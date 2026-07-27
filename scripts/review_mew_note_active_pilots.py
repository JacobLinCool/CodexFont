#!/usr/bin/env python3
"""Build and validate the active Mew Note TC pilot review.

The active pilot IDs come only from the frozen provenance contract. Historical
pilots are excluded from authorization but remain hash-pinned by that contract.
Raster measurements and proof rendering use the immutable v1 review engine,
whose exact bytes are also pinned as an input.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageOps

from scripts import review_mew_note_pilots as engine


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ROOT = ROOT / "families/mew-note-tc"
PROVENANCE_PATH = FAMILY_ROOT / "pilots/provenance-v2.json"
MOTIF_PATH = FAMILY_ROOT / "motif-contract.json"
REVIEW_PATH = FAMILY_ROOT / "pilots/review-v2.json"
REVIEW_ENGINE_PATH = ROOT / "scripts/review_mew_note_pilots.py"
DEFAULT_OUTPUT = ROOT / "build/pilots/mew-note-active-review-v2"

ROWS = 4
COLUMNS = 4
PROOF_SIZES = (16, 20, 32, 72)
CHECK_KEYS = (
    "identity",
    "grid_clearance",
    "cropping",
    "spikes",
    "isolated_ink",
    "motif_assignment",
    "tail_attachment",
    "confusable_distinction",
    "legibility_16px",
    "legibility_20px",
    "legibility_32px",
    "legibility_72px",
)
CHECK_DECISIONS = frozenset({"PASS", "REJECT", "NOT_APPLICABLE"})
MOTIF_CLASSES = frozenset(
    {"tail-terminal", "soft-terminal", "neutral-safety"}
)
CONFUSABLE_REVIEW_CELLS = {
    ("mew-note-han-style-pilot-v2", 13),
    ("mew-note-nonhan-style-pilot", 1),
    ("mew-note-nonhan-style-pilot", 2),
    ("mew-note-nonhan-style-pilot", 3),
    ("mew-note-nonhan-style-pilot", 4),
    ("mew-note-nonhan-style-pilot", 5),
    ("mew-note-nonhan-style-pilot", 6),
    ("mew-note-nonhan-style-pilot", 7),
    ("mew-note-nonhan-style-pilot", 8),
}


class ActivePilotReviewError(engine.PilotReviewError):
    """Active pilot evidence or review violates the frozen v2 contract."""


@dataclass(frozen=True)
class ActivePilot:
    pilot: engine.Pilot
    expected_motif_classes: tuple[str, ...]
    expected_tail_terminal_ranks: tuple[int, ...]


@dataclass(frozen=True)
class ConfusableReference:
    character: str
    codepoint: str
    rank: int
    image: Image.Image
    descriptor_path: Path
    raster_path: Path


@dataclass(frozen=True)
class ActiveContext:
    provenance: Mapping[str, Any]
    active_pilot_ids: tuple[str, ...]
    pilots: tuple[ActivePilot, ...]
    zero_confusables: tuple[ConfusableReference, ...]


def _relative_reference(
    project_root: Path,
    raw: Any,
    *,
    allowed_root: Path,
    where: str,
) -> Path:
    value = engine._exact_keys(raw, {"path", "sha256"}, where=where)
    return engine._require_relative_file(
        project_root,
        value["path"],
        value["sha256"],
        allowed_root=allowed_root,
        where=where,
    )


def _load_confusable_references(
    project_root: Path,
    provenance: Mapping[str, Any],
) -> tuple[ConfusableReference, ...]:
    contract = engine._exact_keys(
        provenance.get("review_identity_references"),
        {"role", "zero_confusables"},
        where="review_identity_references",
    )
    if contract["role"] != "identity-reference-only-no-outline-import":
        raise ActivePilotReviewError("confusable reference role is invalid")
    raw_references = contract["zero_confusables"]
    if not isinstance(raw_references, list) or len(raw_references) != 2:
        raise ActivePilotReviewError("exactly two zero confusables are required")
    expected = (("Ø", "U+00D8", 11), ("∅", "U+2205", 6))
    references: list[ConfusableReference] = []
    for index, (raw, identity) in enumerate(zip(raw_references, expected)):
        value = engine._exact_keys(
            raw,
            {
                "character",
                "codepoint",
                "rank",
                "descriptor",
                "raster",
            },
            where=f"review_identity_references.zero_confusables[{index}]",
        )
        if (
            value["character"],
            value["codepoint"],
            value["rank"],
        ) != identity:
            raise ActivePilotReviewError("zero confusable identity changed")
        descriptor_path = _relative_reference(
            project_root,
            value["descriptor"],
            allowed_root=project_root / "sources/imagegen/batches",
            where=f"zero_confusables[{index}].descriptor",
        )
        descriptor = engine._read_object(
            descriptor_path,
            label="confusable source descriptor",
        )
        glyphs = descriptor.get("grid", {}).get("glyphs")
        rank = value["rank"]
        if (
            not isinstance(glyphs, list)
            or len(glyphs) != ROWS * COLUMNS
            or glyphs[rank - 1].get("character") != value["character"]
            or glyphs[rank - 1].get("codepoint") != value["codepoint"]
        ):
            raise ActivePilotReviewError("confusable descriptor rank changed")
        raster_metadata = engine._exact_keys(
            value["raster"],
            {"path", "sha256", "width", "height", "mode"},
            where=f"zero_confusables[{index}].raster",
        )
        raster_path = _relative_reference(
            project_root,
            {
                "path": raster_metadata["path"],
                "sha256": raster_metadata["sha256"],
            },
            allowed_root=project_root / "sources/imagegen/raster",
            where=f"zero_confusables[{index}].raster",
        )
        try:
            raster = Image.open(raster_path)
            raster.load()
        except (OSError, ValueError) as exc:
            raise ActivePilotReviewError(
                f"zero_confusables[{index}].raster cannot decode: {exc}"
            ) from exc
        if (
            raster.format != "PNG"
            or (raster.width, raster.height, raster.mode)
            != (
                raster_metadata["width"],
                raster_metadata["height"],
                raster_metadata["mode"],
            )
        ):
            raise ActivePilotReviewError(
                f"zero_confusables[{index}].raster metadata changed"
            )
        descriptor_raster = (descriptor_path.parent / descriptor["raster"]).resolve()
        if descriptor_raster != raster_path:
            raise ActivePilotReviewError(
                "confusable descriptor and raster reference differ"
            )
        grid = engine._detect_grid(
            raster,
            where=f"zero_confusables[{index}].raster",
        )
        row, column = divmod(rank - 1, COLUMNS)
        references.append(
            ConfusableReference(
                character=value["character"],
                codepoint=value["codepoint"],
                rank=rank,
                image=engine._cell_image(
                    raster,
                    grid,
                    row=row,
                    column=column,
                ),
                descriptor_path=descriptor_path,
                raster_path=raster_path,
            )
        )
    return tuple(references)


def _validate_pilot_generator(
    project_root: Path,
    raw: Mapping[str, Any],
    *,
    pilot_id: str,
) -> None:
    generator = raw.get("generator")
    if not isinstance(generator, dict):
        raise ActivePilotReviewError(f"{pilot_id}: generator must be an object")
    expected_policy = {
        "identity_and_style_only": True,
        "outline_import_allowed": False,
        "raster_reuse_allowed": False,
    }
    if pilot_id == "mew-note-han-style-pilot-v2":
        engine._exact_keys(
            generator,
            {"name", "prompt_record", "calls", "reference_policy"},
            where=f"{pilot_id}.generator",
        )
        if (
            generator["name"] != "built-in-image_gen"
            or generator["reference_policy"] != expected_policy
        ):
            raise ActivePilotReviewError(
                f"{pilot_id}: generator policy is invalid"
            )
        prompt_path = _relative_reference(
            project_root,
            generator["prompt_record"],
            allowed_root=project_root / "families/mew-note-tc/pilots",
            where=f"{pilot_id}.generator.prompt_record",
        )
        calls = generator["calls"]
        expected_calls = [
            {
                "stage": "generation",
                "call_id": "exec-29882601-d6c0-44c5-861a-dcc73bc8885b",
                "result_sha256": (
                    "bb5c9b7e0220feb45c7190871f9d99b85937f24df9470a29d"
                    "3f688b87cd47c15"
                ),
                "result_retention": "generator-result-not-retained",
            },
            {
                "stage": "zero-correction",
                "call_id": "exec-a37b11cd-92cb-4449-9ed3-4d3c0ea5124e",
                "parent_result_sha256": (
                    "bb5c9b7e0220feb45c7190871f9d99b85937f24df9470a29d"
                    "3f688b87cd47c15"
                ),
                "result_sha256": (
                    "b6ae4ac12a769e979b86df7af1a3d7f4a824ea79ba67bf7b4"
                    "3802c3fc49eff82"
                ),
                "result_retention": "canonical-lossless-raster",
            },
        ]
        if calls != expected_calls:
            raise ActivePilotReviewError(
                f"{pilot_id}: exact two-step call record changed"
            )
        prompt = prompt_path.read_text(encoding="utf-8")
        required_prompt_evidence = (
            "## Generation",
            "## Zero correction",
            expected_calls[0]["call_id"],
            expected_calls[0]["result_sha256"],
            expected_calls[1]["call_id"],
            expected_calls[1]["result_sha256"],
        )
        if any(value not in prompt for value in required_prompt_evidence):
            raise ActivePilotReviewError(
                f"{pilot_id}: prompt record is incomplete"
            )
        artifacts = engine._exact_keys(
            raw.get("artifacts"),
            {
                "raster",
                "identity_copybook",
                "style_reference",
                "zero_identity_reference",
            },
            where=f"{pilot_id}.artifacts",
        )
        if artifacts["raster"].get("sha256") != calls[1]["result_sha256"]:
            raise ActivePilotReviewError(
                f"{pilot_id}: final call and raster hashes differ"
            )
        for key, role in (
            (
                "style_reference",
                "style-reference-only-no-raster-or-outline-reuse",
            ),
            (
                "zero_identity_reference",
                "identity-reference-only-no-raster-or-outline-reuse",
            ),
        ):
            reference = engine._exact_keys(
                artifacts[key],
                {"path", "sha256", "role"},
                where=f"{pilot_id}.artifacts.{key}",
            )
            if reference["role"] != role:
                raise ActivePilotReviewError(
                    f"{pilot_id}: {key} role is invalid"
                )
            _relative_reference(
                project_root,
                {
                    "path": reference["path"],
                    "sha256": reference["sha256"],
                },
                allowed_root=project_root / "families/mew-note-tc/pilots",
                where=f"{pilot_id}.artifacts.{key}",
            )
        return

    engine._exact_keys(
        generator,
        {"name", "source_provenance", "reference_policy"},
        where=f"{pilot_id}.generator",
    )
    if (
        generator["name"] != "built-in-image_gen"
        or generator["reference_policy"] != expected_policy
    ):
        raise ActivePilotReviewError(f"{pilot_id}: generator policy is invalid")
    source = engine._exact_keys(
        generator["source_provenance"],
        {"path", "sha256", "pilot_id"},
        where=f"{pilot_id}.generator.source_provenance",
    )
    if source["pilot_id"] != pilot_id:
        raise ActivePilotReviewError(
            f"{pilot_id}: source provenance pilot ID changed"
        )
    source_path = _relative_reference(
        project_root,
        {"path": source["path"], "sha256": source["sha256"]},
        allowed_root=project_root / "families/mew-note-tc/pilots",
        where=f"{pilot_id}.generator.source_provenance",
    )
    source_provenance = engine._read_object(
        source_path,
        label="historical pilot provenance",
    )
    matches = [
        item
        for item in source_provenance.get("pilots", [])
        if isinstance(item, dict) and item.get("id") == pilot_id
    ]
    if len(matches) != 1:
        raise ActivePilotReviewError(
            f"{pilot_id}: source provenance record is unavailable"
        )
    engine._exact_keys(
        raw.get("artifacts"),
        {"raster", "identity_copybook"},
        where=f"{pilot_id}.artifacts",
    )


def load_active_context(project_root: Path = ROOT) -> ActiveContext:
    """Load only the provenance-declared active pilots."""

    project_root = project_root.resolve()
    provenance_path = (
        project_root / "families/mew-note-tc/pilots/provenance-v2.json"
    )
    provenance = engine._read_object(
        provenance_path,
        label="active pilot provenance",
    )
    engine._exact_keys(
        provenance,
        {
            "schema_version",
            "record_type",
            "family_id",
            "source_state",
            "active_pilot_ids",
            "scope",
            "historical_pilots",
            "review_identity_references",
            "pilots",
            "stop_conditions",
        },
        where=str(provenance_path),
    )
    if (
        provenance["schema_version"] != 2
        or provenance["record_type"]
        != "mew-note-tc-active-style-pilot-provenance"
        or provenance["family_id"] != "mew-note-tc"
        or provenance["source_state"] != "pilot-source-frozen"
    ):
        raise ActivePilotReviewError("active provenance identity is invalid")
    if provenance["scope"] != {
        "style_gate_only": True,
        "encoded_coverage_credit": 0,
        "release_approval": False,
        "bulk_authoring_authority": False,
    }:
        raise ActivePilotReviewError("active provenance scope is invalid")

    raw_active_ids = provenance["active_pilot_ids"]
    if (
        not isinstance(raw_active_ids, list)
        or len(raw_active_ids) != 2
        or len(set(raw_active_ids)) != 2
        or any(not isinstance(value, str) or not value for value in raw_active_ids)
    ):
        raise ActivePilotReviewError("active_pilot_ids must name two pilots")
    active_ids = tuple(raw_active_ids)

    historical = provenance["historical_pilots"]
    if not isinstance(historical, list) or len(historical) != 1:
        raise ActivePilotReviewError("one rejected historical pilot is required")
    history = engine._exact_keys(
        historical[0],
        {
            "id",
            "status",
            "provenance",
            "review",
            "decision",
            "rejected_cells",
        },
        where="historical_pilots[0]",
    )
    if (
        history.get("id") != "mew-note-han-style-pilot"
        or history.get("status") != "rejected-historical-pilot"
        or history.get("decision") != "REJECT"
        or history["id"] in active_ids
    ):
        raise ActivePilotReviewError("v1 history is not isolated from active IDs")
    _relative_reference(
        project_root,
        history.get("provenance"),
        allowed_root=project_root / "families/mew-note-tc/pilots",
        where="historical_pilots[0].provenance",
    )
    _relative_reference(
        project_root,
        history.get("review"),
        allowed_root=project_root / "families/mew-note-tc/pilots",
        where="historical_pilots[0].review",
    )

    raw_pilots = provenance["pilots"]
    if not isinstance(raw_pilots, list) or [
        item.get("id") for item in raw_pilots if isinstance(item, dict)
    ] != list(active_ids):
        raise ActivePilotReviewError(
            "pilots must match active_pilot_ids in exact order"
        )
    active_pilots: list[ActivePilot] = []
    for pilot_index, raw in enumerate(raw_pilots):
        if not isinstance(raw, dict):
            raise ActivePilotReviewError(f"pilots[{pilot_index}] must be an object")
        engine._exact_keys(
            raw,
            {
                "id",
                "generator",
                "grid",
                "motif_assignment",
                "artifacts",
                "manual_decision",
            },
            where=f"pilots[{pilot_index}]",
        )
        pilot_id = raw["id"]
        _validate_pilot_generator(
            project_root,
            raw,
            pilot_id=pilot_id,
        )
        if raw.get("manual_decision") != {
            "style_direction": "ACCEPTED_FOR_TECHNICAL_REVIEW",
            "technical_review_state": "pending",
            "release_admission_state": "not-admitted",
        }:
            raise ActivePilotReviewError(
                f"{pilot_id}: source cannot self-approve technical review"
            )
        grid_contract = raw.get("grid")
        if (
            not isinstance(grid_contract, dict)
            or grid_contract.get("rows") != ROWS
            or grid_contract.get("columns") != COLUMNS
            or not isinstance(grid_contract.get("cell_order"), list)
            or len(grid_contract["cell_order"]) != ROWS * COLUMNS
            or any(
                not isinstance(character, str) or len(character) != 1
                for character in grid_contract["cell_order"]
            )
        ):
            raise ActivePilotReviewError(f"{pilot_id}: invalid grid contract")
        motif = engine._exact_keys(
            raw.get("motif_assignment"),
            {"expected_tail_terminal_ranks", "expected_classes"},
            where=f"{pilot_id}.motif_assignment",
        )
        expected_classes = motif["expected_classes"]
        expected_tails = motif["expected_tail_terminal_ranks"]
        if (
            not isinstance(expected_classes, list)
            or len(expected_classes) != ROWS * COLUMNS
            or any(value not in MOTIF_CLASSES for value in expected_classes)
            or not isinstance(expected_tails, list)
            or expected_tails
            != [
                rank
                for rank, value in enumerate(expected_classes, start=1)
                if value == "tail-terminal"
            ]
        ):
            raise ActivePilotReviewError(f"{pilot_id}: motif assignment changed")
        artifacts = raw.get("artifacts")
        if not isinstance(artifacts, dict):
            raise ActivePilotReviewError(f"{pilot_id}: artifacts must be an object")
        raster_path, raster = engine._artifact_image(
            project_root,
            artifacts["raster"],
            where=f"{pilot_id}.raster",
        )
        copybook_path, copybook = engine._artifact_image(
            project_root,
            artifacts["identity_copybook"],
            where=f"{pilot_id}.identity_copybook",
        )
        if (
            artifacts["identity_copybook"].get("role")
            != "identity-reference-only-no-outline-import"
        ):
            raise ActivePilotReviewError(
                f"{pilot_id}: identity copybook role is invalid"
            )
        raster_grid = engine._detect_grid(
            raster,
            where=f"{pilot_id}.raster",
        )
        copybook_grid = engine._detect_grid(
            copybook,
            where=f"{pilot_id}.identity_copybook",
        )
        cells: list[engine.Cell] = []
        for rank, character in enumerate(grid_contract["cell_order"], start=1):
            row, column = divmod(rank - 1, COLUMNS)
            source = engine._cell_image(
                raster,
                raster_grid,
                row=row,
                column=column,
            )
            identity_copybook = engine._cell_image(
                copybook,
                copybook_grid,
                row=row,
                column=column,
            )
            cells.append(
                engine.Cell(
                    character=character,
                    rank=rank,
                    row=row,
                    column=column,
                    source=source,
                    copybook=identity_copybook,
                    metrics={
                        "source": engine._ink_metrics(source),
                        "copybook": engine._ink_metrics(identity_copybook),
                    },
                )
            )
        active_pilots.append(
            ActivePilot(
                pilot=engine.Pilot(
                    pilot_id=pilot_id,
                    raster_path=raster_path,
                    copybook_path=copybook_path,
                    characters=tuple(grid_contract["cell_order"]),
                    raster=raster,
                    copybook=copybook,
                    raster_grid=raster_grid,
                    copybook_grid=copybook_grid,
                    cells=tuple(cells),
                ),
                expected_motif_classes=tuple(expected_classes),
                expected_tail_terminal_ranks=tuple(expected_tails),
            )
        )
    return ActiveContext(
        provenance=provenance,
        active_pilot_ids=active_ids,
        pilots=tuple(active_pilots),
        zero_confusables=_load_confusable_references(
            project_root,
            provenance,
        ),
    )


def _write_confusable_proof(
    sources: tuple[tuple[str, Image.Image], ...],
    *,
    size: int,
    output: Path,
) -> Path:
    panel_width, panel_height = 200, 320
    sheet = Image.new(
        "L",
        (panel_width * len(sources), panel_height),
        color=255,
    )
    for index, (label, source) in enumerate(sources):
        panel = Image.new("L", (panel_width, panel_height), color=255)
        draw = ImageDraw.Draw(panel)
        draw.text((8, 4), label, fill=0)
        actual = engine._fit(source, size)
        zoom = actual.resize((128, 128), Image.Resampling.NEAREST)
        inverse = ImageOps.invert(actual)
        inverse_zoom = inverse.resize((128, 128), Image.Resampling.NEAREST)
        panel.paste(actual, (8, 24))
        panel.paste(zoom, (56, 24))
        panel.paste(inverse, (8, 176))
        panel.paste(inverse_zoom, (56, 176))
        sheet.paste(panel, (index * panel_width, 0))
    sheet.save(output)
    return output


def build(
    *,
    project_root: Path = ROOT,
    output: Path = DEFAULT_OUTPUT,
) -> Path:
    """Build deterministic evidence for the provenance-declared active pilots."""

    project_root = project_root.resolve()
    output = engine._safe_output(project_root, output)
    context = load_active_context(project_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent)
    )
    try:
        pilot_records: list[dict[str, Any]] = []
        proof_records: list[dict[str, str]] = []
        for active in context.pilots:
            pilot = active.pilot
            proof_directory = stage / "proof" / pilot.pilot_id
            proof_directory.mkdir(parents=True)
            segmented = engine._write_segmented_proof(
                pilot,
                proof_directory / "segmented-source-vs-copybook.png",
            )
            proof_records.append(
                {
                    "pilot_id": pilot.pilot_id,
                    "kind": "segmented-source-vs-copybook",
                    "path": segmented.relative_to(stage).as_posix(),
                    "sha256": engine._sha256(segmented),
                }
            )
            for size in PROOF_SIZES:
                proof = engine._write_readability_proof(
                    pilot,
                    size=size,
                    output=proof_directory / f"readability-{size}px.png",
                )
                proof_records.append(
                    {
                        "pilot_id": pilot.pilot_id,
                        "kind": f"readability-{size}px",
                        "path": proof.relative_to(stage).as_posix(),
                        "sha256": engine._sha256(proof),
                    }
                )
            pilot_records.append(
                {
                    "pilot_id": pilot.pilot_id,
                    "expected_motif_classes": list(
                        active.expected_motif_classes
                    ),
                    "expected_tail_terminal_ranks": list(
                        active.expected_tail_terminal_ranks
                    ),
                    "raster": {
                        "path": pilot.raster_path.relative_to(
                            project_root
                        ).as_posix(),
                        "sha256": engine._sha256(pilot.raster_path),
                    },
                    "identity_copybook": {
                        "path": pilot.copybook_path.relative_to(
                            project_root
                        ).as_posix(),
                        "sha256": engine._sha256(pilot.copybook_path),
                    },
                    "raster_grid": {
                        "x_rule_centers": list(pilot.raster_grid.x_centers),
                        "y_rule_centers": list(pilot.raster_grid.y_centers),
                    },
                    "copybook_grid": {
                        "x_rule_centers": list(pilot.copybook_grid.x_centers),
                        "y_rule_centers": list(pilot.copybook_grid.y_centers),
                    },
                    "cells": [
                        {
                            "rank": cell.rank,
                            "character": cell.character,
                            "codepoint": f"U+{ord(cell.character):04X}",
                            "row": cell.row,
                            "column": cell.column,
                            "metrics": cell.metrics,
                        }
                        for cell in pilot.cells
                    ],
                }
            )

        pilots_by_id = {
            active.pilot.pilot_id: active for active in context.pilots
        }
        han_zero = pilots_by_id[
            "mew-note-han-style-pilot-v2"
        ].pilot.cells[12].source
        nonhan = pilots_by_id["mew-note-nonhan-style-pilot"].pilot.cells
        confusable_sources = (
            ("U+0030 v2", han_zero),
            ("U+004F O", nonhan[4].source),
            ("U+0051 Q", nonhan[7].source),
            (
                context.zero_confusables[0].codepoint,
                context.zero_confusables[0].image,
            ),
            (
                context.zero_confusables[1].codepoint,
                context.zero_confusables[1].image,
            ),
        )
        confusable_directory = stage / "proof/confusable-zero"
        confusable_directory.mkdir(parents=True)
        for size in PROOF_SIZES:
            proof = _write_confusable_proof(
                confusable_sources,
                size=size,
                output=confusable_directory
                / f"zero-vs-o-q-o-stroke-empty-set-{size}px.png",
            )
            proof_records.append(
                {
                    "pilot_id": "cross-pilot-zero-confusables",
                    "kind": f"confusable-readability-{size}px",
                    "path": proof.relative_to(stage).as_posix(),
                    "sha256": engine._sha256(proof),
                }
            )

        report = {
            "schema_version": 2,
            "pipeline": "mew-note-active-pilot-raster-review-v2",
            "approval_state": "unreviewed",
            "family_id": "mew-note-tc",
            "active_pilot_ids": list(context.active_pilot_ids),
            "inputs": {
                "active_provenance": {
                    "path": (
                        "families/mew-note-tc/pilots/provenance-v2.json"
                    ),
                    "sha256": engine._sha256(
                        project_root
                        / "families/mew-note-tc/pilots/provenance-v2.json"
                    ),
                },
                "motif_contract": {
                    "path": "families/mew-note-tc/motif-contract.json",
                    "sha256": engine._sha256(
                        project_root
                        / "families/mew-note-tc/motif-contract.json"
                    ),
                },
                "review_script": {
                    "path": "scripts/review_mew_note_active_pilots.py",
                    "sha256": engine._sha256(
                        project_root
                        / "scripts/review_mew_note_active_pilots.py"
                    ),
                },
                "review_engine": {
                    "path": "scripts/review_mew_note_pilots.py",
                    "sha256": engine._sha256(
                        project_root / "scripts/review_mew_note_pilots.py"
                    ),
                },
            },
            "measurement_contract": {
                "rows": ROWS,
                "columns": COLUMNS,
                "proof_sizes_px": list(PROOF_SIZES),
                "proof_polarities": [
                    "black-on-white",
                    "white-on-black",
                ],
                "grid_pixel_ceiling": engine.GRID_PIXEL_CEILING,
                "grid_min_coverage": engine.GRID_MIN_COVERAGE,
                "ink_pixel_ceiling": engine.INK_PIXEL_CEILING,
                "edge_band_pixels": engine.EDGE_BAND_PIXELS,
                "small_component_minimum_pixels": (
                    engine.SMALL_COMPONENT_MINIMUM_PIXELS
                ),
            },
            "pilots": pilot_records,
            "zero_confusable_references": [
                {
                    "character": reference.character,
                    "codepoint": reference.codepoint,
                    "rank": reference.rank,
                    "descriptor": {
                        "path": reference.descriptor_path.relative_to(
                            project_root
                        ).as_posix(),
                        "sha256": engine._sha256(reference.descriptor_path),
                    },
                    "raster": {
                        "path": reference.raster_path.relative_to(
                            project_root
                        ).as_posix(),
                        "sha256": engine._sha256(reference.raster_path),
                    },
                    "role": "identity-reference-only-no-outline-import",
                }
                for reference in context.zero_confusables
            ],
            "proofs": proof_records,
            "review_policy": (
                "Measurements never self-approve identity, motif assignment, "
                "tail attachment, confusable distinction, spikes, or legibility"
            ),
        }
        report_path = stage / "report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return output


def _validate_input_reference(
    project_root: Path,
    raw: Any,
    *,
    expected_path: str,
    where: str,
) -> Path:
    value = engine._exact_keys(raw, {"path", "sha256"}, where=where)
    if value["path"] != expected_path:
        raise ActivePilotReviewError(f"{where}.path must be {expected_path}")
    return engine._require_relative_file(
        project_root,
        value["path"],
        value["sha256"],
        allowed_root=project_root,
        where=where,
    )


def validate_review(
    *,
    review_path: Path = REVIEW_PATH,
    evidence: Path = DEFAULT_OUTPUT,
    project_root: Path = ROOT,
    require_supplementary_evidence: bool = False,
) -> dict[str, Any]:
    """Validate an independent review of all provenance-declared active cells."""

    project_root = project_root.resolve()
    context = load_active_context(project_root)
    review_path = review_path.resolve()
    review = engine._read_object(review_path, label="active pilot review")
    top = engine._exact_keys(
        review,
        {
            "schema_version",
            "record_type",
            "family_id",
            "review_state",
            "reviewer",
            "reviewed_on",
            "scope",
            "active_pilot_ids",
            "inputs",
            "evidence",
            "pilots",
            "summary",
            "authorization",
            "supplementary_scalability_evidence",
        },
        where=str(review_path),
    )
    if (
        top["schema_version"] != 2
        or top["record_type"]
        != "mew-note-tc-active-pilot-technical-review"
        or top["family_id"] != "mew-note-tc"
        or top["review_state"] not in {"ACCEPT", "REJECT"}
        or top["active_pilot_ids"] != list(context.active_pilot_ids)
    ):
        raise ActivePilotReviewError("active review identity/state is invalid")
    reviewer = engine._exact_keys(
        top["reviewer"],
        {"name", "role", "independent_from_generator"},
        where="reviewer",
    )
    if (
        not isinstance(reviewer["name"], str)
        or not reviewer["name"].strip()
        or reviewer["role"] != "independent-active-pilot-technical-review"
        or reviewer["independent_from_generator"] is not True
    ):
        raise ActivePilotReviewError("active reviewer contract is invalid")
    if top["reviewed_on"] != "2026-07-29":
        raise ActivePilotReviewError("reviewed_on must pin the review date")
    if top["scope"] != {
        "active_pilot_gate_only": True,
        "historical_pilots_authoritative": False,
        "encoded_coverage_credit": 0,
        "bulk_authoring_decision": True,
    }:
        raise ActivePilotReviewError("active review scope is invalid")

    inputs = engine._exact_keys(
        top["inputs"],
        {
            "active_provenance",
            "motif_contract",
            "review_script",
            "review_engine",
        },
        where="inputs",
    )
    for key, path in (
        (
            "active_provenance",
            "families/mew-note-tc/pilots/provenance-v2.json",
        ),
        ("motif_contract", "families/mew-note-tc/motif-contract.json"),
        ("review_script", "scripts/review_mew_note_active_pilots.py"),
        ("review_engine", "scripts/review_mew_note_pilots.py"),
    ):
        _validate_input_reference(
            project_root,
            inputs[key],
            expected_path=path,
            where=f"inputs.{key}",
        )

    evidence = evidence.resolve()
    report_path = evidence / "report.json"
    report = engine._read_object(
        report_path,
        label="rebuilt active pilot report",
    )
    if (
        report.get("schema_version") != 2
        or report.get("pipeline")
        != "mew-note-active-pilot-raster-review-v2"
        or report.get("approval_state") != "unreviewed"
        or report.get("family_id") != "mew-note-tc"
        or report.get("active_pilot_ids") != list(context.active_pilot_ids)
        or report.get("inputs") != inputs
    ):
        raise ActivePilotReviewError("rebuilt active report identity changed")
    evidence_contract = engine._exact_keys(
        top["evidence"],
        {"report", "proofs"},
        where="evidence",
    )
    if evidence_contract["report"] != {
        "path": "build/pilots/mew-note-active-review-v2/report.json",
        "sha256": engine._sha256(report_path),
    }:
        raise ActivePilotReviewError("review does not pin the active report")
    expected_proofs = {
        item["path"]: item["sha256"] for item in report["proofs"]
    }
    raw_proofs = evidence_contract["proofs"]
    if not isinstance(raw_proofs, list):
        raise ActivePilotReviewError("evidence.proofs must be an array")
    if len(raw_proofs) != len(expected_proofs):
        raise ActivePilotReviewError("active proof inventory length changed")
    actual_proofs: dict[str, str] = {}
    prefix = "build/pilots/mew-note-active-review-v2/"
    for index, raw in enumerate(raw_proofs):
        value = engine._exact_keys(
            raw,
            {"path", "sha256"},
            where=f"evidence.proofs[{index}]",
        )
        path = value["path"]
        if not isinstance(path, str) or not path.startswith(prefix):
            raise ActivePilotReviewError("proof path is outside active evidence")
        relative = path.removeprefix(prefix)
        proof_path = evidence / relative
        if (
            not proof_path.is_file()
            or engine._sha256(proof_path) != value["sha256"]
        ):
            raise ActivePilotReviewError(f"stale active proof: {path}")
        actual_proofs[relative] = value["sha256"]
    if actual_proofs != expected_proofs:
        raise ActivePilotReviewError("active proof inventory changed")

    contracts = {
        active.pilot.pilot_id: active for active in context.pilots
    }
    report_metrics = {
        pilot["pilot_id"]: {
            cell["rank"]: cell["metrics"] for cell in pilot["cells"]
        }
        for pilot in report["pilots"]
    }
    raw_pilots = top["pilots"]
    if not isinstance(raw_pilots, list) or [
        item.get("pilot_id") for item in raw_pilots if isinstance(item, dict)
    ] != list(context.active_pilot_ids):
        raise ActivePilotReviewError(
            "review pilots must match active_pilot_ids in order"
        )
    decisions: list[tuple[str, int, str, str]] = []
    for pilot_index, raw_pilot in enumerate(raw_pilots):
        pilot_review = engine._exact_keys(
            raw_pilot,
            {
                "pilot_id",
                "decision",
                "observed_tail_terminal_ranks",
                "cells",
            },
            where=f"pilots[{pilot_index}]",
        )
        pilot_id = pilot_review["pilot_id"]
        contract = contracts[pilot_id]
        observed_tails = pilot_review["observed_tail_terminal_ranks"]
        if (
            not isinstance(observed_tails, list)
            or observed_tails != sorted(set(observed_tails))
            or any(
                not isinstance(rank, int) or not 1 <= rank <= 16
                for rank in observed_tails
            )
        ):
            raise ActivePilotReviewError(
                f"{pilot_id}: observed tail ranks are invalid"
            )
        raw_cells = pilot_review["cells"]
        if not isinstance(raw_cells, list) or len(raw_cells) != 16:
            raise ActivePilotReviewError(
                f"{pilot_id}: all 16 cells require review"
            )
        pilot_decisions: list[str] = []
        for cell_index, raw_cell in enumerate(raw_cells):
            cell = engine._exact_keys(
                raw_cell,
                {
                    "rank",
                    "character",
                    "motif_class",
                    "checks",
                    "decision",
                    "notes",
                },
                where=f"{pilot_id}.cells[{cell_index}]",
            )
            rank = cell_index + 1
            character = contract.pilot.characters[cell_index]
            if cell["rank"] != rank or cell["character"] != character:
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} identity/order changed"
                )
            expected_motif = contract.expected_motif_classes[cell_index]
            if cell["motif_class"] not in MOTIF_CLASSES:
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} motif class is invalid"
                )
            checks = engine._exact_keys(
                cell["checks"],
                set(CHECK_KEYS),
                where=f"{pilot_id}.cells[{rank}].checks",
            )
            if any(value not in CHECK_DECISIONS for value in checks.values()):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} has an invalid check"
                )
            if any(
                checks[key] == "NOT_APPLICABLE"
                for key in CHECK_KEYS
                if key not in {"tail_attachment", "confusable_distinction"}
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} skips a mandatory check"
                )
            if (
                checks["motif_assignment"] == "PASS"
                and cell["motif_class"] != expected_motif
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} passes the wrong motif class"
                )
            if (
                cell["motif_class"] == "tail-terminal"
                and checks["tail_attachment"] == "NOT_APPLICABLE"
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} needs tail attachment review"
                )
            if (
                cell["motif_class"] != "tail-terminal"
                and checks["tail_attachment"] != "NOT_APPLICABLE"
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} tail attachment must be N/A"
                )
            needs_confusable = (pilot_id, rank) in CONFUSABLE_REVIEW_CELLS
            if needs_confusable == (
                checks["confusable_distinction"] == "NOT_APPLICABLE"
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} confusable decision is invalid"
                )
            metrics = report_metrics[pilot_id][rank]["source"]
            if (
                checks["grid_clearance"] == "PASS"
                and metrics["edge_contact_ink_pixels"] != 0
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} passes with edge ink"
                )
            if (
                checks["isolated_ink"] == "PASS"
                and metrics["small_isolated_component_count"] != 0
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} passes with a small ink island"
                )
            has_reject = "REJECT" in checks.values()
            expected_decision = "REJECT" if has_reject else "ACCEPT"
            if cell["decision"] != expected_decision:
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} decision/checks disagree"
                )
            if (
                not isinstance(cell["notes"], str)
                or not cell["notes"].strip()
            ):
                raise ActivePilotReviewError(
                    f"{pilot_id}: cell {rank} needs notes"
                )
            pilot_decisions.append(cell["decision"])
            decisions.append((pilot_id, rank, character, cell["decision"]))
        expected_pilot_decision = (
            "ACCEPT" if set(pilot_decisions) == {"ACCEPT"} else "REJECT"
        )
        observed_from_cells = [
            cell_index + 1
            for cell_index, cell in enumerate(raw_cells)
            if cell["motif_class"] == "tail-terminal"
        ]
        if observed_tails != observed_from_cells:
            raise ActivePilotReviewError(
                f"{pilot_id}: observed tail ranks and cell records differ"
            )
        if pilot_review["decision"] != expected_pilot_decision:
            raise ActivePilotReviewError(
                f"{pilot_id}: aggregate decision is invalid"
            )
        expected_tails = list(contract.expected_tail_terminal_ranks)
        if (
            pilot_review["decision"] == "ACCEPT"
            and observed_tails != expected_tails
        ):
            raise ActivePilotReviewError(
                f"{pilot_id}: accepted pilot tail assignment differs"
            )

    rejected = [
        {
            "pilot_id": pilot_id,
            "rank": rank,
            "character": character,
        }
        for pilot_id, rank, character, decision in decisions
        if decision == "REJECT"
    ]
    summary = engine._exact_keys(
        top["summary"],
        {
            "active_pilot_count",
            "active_cell_count",
            "accepted_cell_count",
            "rejected_cell_count",
            "rejected_cells",
            "historical_rejected_pilot_count",
        },
        where="summary",
    )
    expected_summary = {
        "active_pilot_count": len(context.active_pilot_ids),
        "active_cell_count": len(decisions),
        "accepted_cell_count": len(decisions) - len(rejected),
        "rejected_cell_count": len(rejected),
        "rejected_cells": rejected,
        "historical_rejected_pilot_count": 1,
    }
    if summary != expected_summary:
        raise ActivePilotReviewError("active review summary is invalid")
    expected_state = "ACCEPT" if not rejected else "REJECT"
    if top["review_state"] != expected_state:
        raise ActivePilotReviewError("active review state is invalid")
    expected_authorization = {
        "bulk_authoring_allowed": not rejected,
        "reason": (
            "All 32 cells in the two active pilots passed independent review"
            if not rejected
            else "At least one active pilot cell failed independent review"
        ),
    }
    if top["authorization"] != expected_authorization:
        raise ActivePilotReviewError("active authorization is invalid")
    engine._validate_supplementary_evidence(
        project_root,
        top["supplementary_scalability_evidence"],
        required=require_supplementary_evidence,
    )
    return review


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    validate_parser = subparsers.add_parser("validate-review")
    validate_parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    validate_parser.add_argument("--evidence", type=Path, default=DEFAULT_OUTPUT)
    validate_parser.add_argument(
        "--require-supplementary-evidence",
        action="store_true",
    )
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    if arguments.command == "build":
        output = arguments.output
        if not output.is_absolute():
            output = project_root / output
        built = build(project_root=project_root, output=output)
        print(f"built active Mew Note pilot evidence: {built}")
        return 0
    review_path = arguments.review
    if not review_path.is_absolute():
        review_path = project_root / review_path
    evidence = arguments.evidence
    if not evidence.is_absolute():
        evidence = project_root / evidence
    review = validate_review(
        review_path=review_path,
        evidence=evidence,
        project_root=project_root,
        require_supplementary_evidence=(
            arguments.require_supplementary_evidence
        ),
    )
    print(
        "validated active Mew Note pilot review: "
        f"{review['review_state']}; "
        f"bulk={review['authorization']['bulk_authoring_allowed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
