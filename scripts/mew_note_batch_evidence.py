#!/usr/bin/env python3
"""Materialize, register, and build one Mew Note TC raster batch.

Every operation starts from the hash-pinned family context and frozen batch
plan.  Identity copybooks are rendered from exact cmap hits in explicitly
pinned external fonts.  Generator attempts are recorded as an immutable
chain: rejected outputs are hash-only, while the one accepted output is copied
to the family-local canonical raster path.  No Clear Hand raster, outline,
review, approval, or build artifact is accepted.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw

from scripts.font_family_context import (
    FamilyContext,
    FamilyContextError,
    canonical_json_sha256,
    sha256_path,
)
from scripts.identity_reference_catalog import (
    IdentityReferenceCatalogError,
    load_reference_faces,
    pillow_font,
    select_references,
)
from scripts import imagegen_font_pipeline
from scripts import mew_note_bulk_pipeline


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ID = "mew-note-tc"
PIPELINE_ID = "original-raster-v1"
CONTRACT_PATH = Path("families/mew-note-tc/batch-evidence-contract.json")
PLAN_PATH = mew_note_bulk_pipeline.PLAN_PATH
SCHEMA_VERSION = 1
CONTRACT_RECORD_TYPE = "mew-note-tc-batch-evidence-contract"
DRAFT_RECORD_TYPE = "mew-note-tc-batch-draft"
HISTORY_RECORD_TYPE = "mew-note-tc-generation-history"
SOURCE_RECORD_TYPE = "mew-note-tc-generated-source"
REVIEW_RECORD_TYPE = "mew-note-tc-batch-technical-review"
GENERATOR = "built-in-image_gen"
GRID_ROWS = 4
GRID_COLUMNS = 4
GRID_CAPACITY = 16
COPYBOOK_SIDE = 1600
COPYBOOK_CELL = COPYBOOK_SIDE // GRID_COLUMNS
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
CALL_ID_PATTERN = re.compile(
    r"(?:exec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}|call_[0-9A-Za-z]{24})"
)
OPERATIONS = frozenset({"generate", "correction"})
DISPOSITIONS = frozenset({"rejected", "accepted"})
INPUT_ROLES = frozenset(
    {"style-reference", "identity-copybook", "parent-output"}
)


class MewNoteBatchError(RuntimeError):
    """A Mew Note TC batch artifact is incomplete, stale, or unsafe."""


@dataclass(frozen=True)
class CatalogGlyph:
    character: str
    codepoint: int
    codepoint_label: str


@dataclass(frozen=True)
class GenerationInput:
    role: str
    sha256: str
    path: Path | None
    retention: str


@dataclass(frozen=True)
class GenerationStep:
    operation: str
    disposition: str
    call_id: str
    prompt_path: Path
    inputs: tuple[GenerationInput, ...]
    output_sha256: str
    output_path: Path | None
    parent_output_sha256: str | None = None


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write(path, _json_bytes(value))


def _atomic_copy(source: Path, target: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise MewNoteBatchError(f"accepted raster is not a regular file: {source}")
    _atomic_write(target, source.read_bytes())


def _object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteBatchError(f"{path}: cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise MewNoteBatchError(f"{path}: {label} must be a JSON object")
    return value


def _regular_file(path: Path, *, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise MewNoteBatchError(f"{label} must be a regular file: {path}")


def _digest(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise MewNoteBatchError(f"{label} must be a lowercase SHA-256")
    return value


def _canonical_relative(value: Any, *, label: str) -> Path:
    if not isinstance(value, str):
        raise MewNoteBatchError(f"{label} must be a relative path string")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or not pure.parts
        or "." in pure.parts
        or ".." in pure.parts
        or pure.as_posix() != value
    ):
        raise MewNoteBatchError(
            f"{label} must be a canonical project-relative POSIX path"
        )
    return Path(*pure.parts)


def _project_relative(path: Path, *, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise MewNoteBatchError(f"path escapes project root: {path}") from exc


def _pin(path: Path, *, project_root: Path) -> dict[str, str]:
    _regular_file(path, label="pinned file")
    return {
        "path": _project_relative(path, project_root=project_root),
        "sha256": sha256_path(path),
    }


def _contract_reference(
    contract: Mapping[str, Any],
    key: str,
    *,
    project_root: Path,
) -> Path:
    value = contract.get(key)
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise MewNoteBatchError(f"contract.{key} must pin path and sha256")
    relative = _canonical_relative(value["path"], label=f"contract.{key}.path")
    expected = _digest(value["sha256"], label=f"contract.{key}.sha256")
    path = project_root / relative
    _regular_file(path, label=f"contract.{key}")
    if sha256_path(path) != expected:
        raise MewNoteBatchError(f"contract.{key} SHA-256 mismatch")
    return path


def load_contract(
    context: FamilyContext,
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    path = context.project_root / CONTRACT_PATH if path is None else path
    payload = _object(path, label="batch evidence contract")
    expected_keys = {
        "schema_version",
        "record_type",
        "family_id",
        "pipeline_id",
        "family_contract",
        "pipeline_contract",
        "authoring_contract",
        "collection_contract",
        "batch_plan",
        "implementation",
        "vector_pipeline",
        "identity_reference_fonts",
        "style_references",
        "grid",
        "prompt_execution_adapter",
        "history_policy",
        "vector_policy",
        "stop_conditions",
    }
    if set(payload) != expected_keys:
        raise MewNoteBatchError("batch evidence contract key set changed")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("record_type") != CONTRACT_RECORD_TYPE
        or payload.get("family_id") != FAMILY_ID
        or payload.get("pipeline_id") != PIPELINE_ID
    ):
        raise MewNoteBatchError("batch evidence contract identity mismatch")
    expected_context = {
        "family_contract": context.family_contract.evidence_record(),
        "pipeline_contract": context.pipeline_contract.evidence_record(),
        "authoring_contract": context.authoring_contract.evidence_record(),
        "collection_contract": context.collection_contract.evidence_record(),
    }
    for key, expected in expected_context.items():
        if payload.get(key) != expected:
            raise MewNoteBatchError(f"batch evidence {key} pin mismatch")
        _contract_reference(payload, key, project_root=context.project_root)
    for key in (
        "batch_plan",
        "implementation",
        "vector_pipeline",
    ):
        _contract_reference(payload, key, project_root=context.project_root)
    styles = payload["style_references"]
    if not isinstance(styles, list) or not styles:
        raise MewNoteBatchError("style reference list is empty")
    style_paths: set[str] = set()
    for index, item in enumerate(styles):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise MewNoteBatchError(
                f"style reference {index} must pin path and sha256"
            )
        style_path = str(item["path"])
        if style_path in style_paths:
            raise MewNoteBatchError("duplicate style reference")
        style_paths.add(style_path)
        reference = {
            "style_reference": item,
        }
        _contract_reference(
            reference,
            "style_reference",
            project_root=context.project_root,
        )
    fonts = payload["identity_reference_fonts"]
    if not isinstance(fonts, list) or not fonts:
        raise MewNoteBatchError("identity reference font list is empty")
    seen: set[str] = set()
    for index, item in enumerate(fonts):
        if not isinstance(item, dict) or set(item) != {
            "path",
            "sha256",
            "role",
            "binary_committed",
        }:
            raise MewNoteBatchError(
                f"identity reference font {index} has an invalid key set"
            )
        font_path = str(item["path"])
        if font_path in seen:
            raise MewNoteBatchError("duplicate identity reference font")
        seen.add(font_path)
        path_value = Path(font_path).expanduser().resolve()
        _regular_file(path_value, label=f"identity reference font {index}")
        if sha256_path(path_value) != _digest(
            item["sha256"],
            label=f"identity reference font {index} hash",
        ):
            raise MewNoteBatchError(
                f"identity reference font {index} hash mismatch"
            )
        try:
            path_value.relative_to(context.project_root)
        except ValueError:
            pass
        else:
            raise MewNoteBatchError(
                "identity reference binaries must remain outside the project"
            )
        if (
            item["role"] != "identity-reference-only-no-outline-import"
            or item["binary_committed"] is not False
        ):
            raise MewNoteBatchError("identity reference role changed")
    if payload["grid"] != {
        "rows": GRID_ROWS,
        "columns": GRID_COLUMNS,
        "capacity": GRID_CAPACITY,
        "copybook_side_px": COPYBOOK_SIDE,
        "order": "row-major",
    }:
        raise MewNoteBatchError("batch evidence grid contract changed")
    adapter = payload["prompt_execution_adapter"]
    if (
        adapter.get("intended_prompt_is_immutable") is not True
        or adapter.get("actual_tool_prompt_is_separate") is not True
        or adapter.get("tool_grid_rules") != (
            "exactly-five-horizontal-and-five-vertical-thin-neutral-gray-rules"
        )
        or adapter.get("glyph_ink_or_identity_change_allowed") is not False
    ):
        raise MewNoteBatchError("prompt execution adapter is unsafe")
    history = payload["history_policy"]
    if history != {
        "generator": GENERATOR,
        "rejected_outputs": "hash-only",
        "accepted_output": "one-canonical-lossless-raster",
        "actual_prompt_required_per_call": True,
        "parent_hash_chain_required": True,
        "generated_raster_self_approval_allowed": False,
    }:
        raise MewNoteBatchError("history policy changed")
    vector = payload["vector_policy"]
    if (
        vector.get("family_local_raster_root_required") is not True
        or vector.get("family_local_build_root_required") is not True
        or vector.get("max_micro_edge_count") != 0
        or vector.get("max_acute_micro_turn_count") != 0
        or vector.get("clear_hand_font_identity_allowed") is not False
    ):
        raise MewNoteBatchError("vector policy changed")
    return payload


def load_context(project_root: Path = ROOT) -> FamilyContext:
    try:
        context = mew_note_bulk_pipeline.load_context(project_root)
        mew_note_bulk_pipeline.validate_authoring_contract(context)
    except (FamilyContextError, mew_note_bulk_pipeline.MewNoteBulkError) as exc:
        raise MewNoteBatchError(str(exc)) from exc
    load_contract(context)
    return context


def _load_plan(context: FamilyContext) -> dict[str, Any]:
    contract = load_contract(context)
    path = _contract_reference(
        contract,
        "batch_plan",
        project_root=context.project_root,
    )
    payload = _object(path, label="frozen batch plan")
    try:
        mew_note_bulk_pipeline.validate_plan_payload(payload, context=context)
    except mew_note_bulk_pipeline.MewNoteBulkError as exc:
        raise MewNoteBatchError(str(exc)) from exc
    return payload


def frozen_batch(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in _load_plan(context)["batches"]
        if item["collection_id"] == collection_id
        and item["batch_id"] == batch_id
    ]
    if len(matches) != 1:
        raise MewNoteBatchError(
            f"{collection_id}/{batch_id}: not one frozen plan batch"
        )
    batch = matches[0]
    if batch["materialization_kind"] != "visible-raster":
        raise MewNoteBatchError(
            f"{collection_id}/{batch_id}: not a visible-raster batch"
        )
    if batch["family_context"] != context.evidence_binding(collection_id):
        raise MewNoteBatchError(
            f"{collection_id}/{batch_id}: family context mismatch"
        )
    return batch


def _batch_root(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Path:
    return context.batch_paths(collection_id, batch_id).source


def _reference_catalog(
    contract: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
) -> tuple[dict[int, dict[str, Any]], tuple[Path, ...]]:
    glyphs = tuple(
        CatalogGlyph(
            character=str(entry["character"]),
            codepoint=int(str(entry["codepoint"])[2:], 16),
            codepoint_label=str(entry["codepoint"]),
        )
        for entry in entries
    )
    paths = tuple(
        Path(str(item["path"])).expanduser().resolve()
        for item in contract["identity_reference_fonts"]
    )
    try:
        faces = load_reference_faces(
            (glyph.codepoint for glyph in glyphs),
            paths,
        )
        selected = select_references(glyphs, faces)
    except IdentityReferenceCatalogError as exc:
        raise MewNoteBatchError(str(exc)) from exc
    return selected, paths


def _render_copybook(
    entries: Sequence[Mapping[str, Any]],
    references: Mapping[int, Mapping[str, Any]],
) -> Image.Image:
    image = Image.new("L", (COPYBOOK_SIDE, COPYBOOK_SIDE), 255)
    draw = ImageDraw.Draw(image)
    for coordinate in (0, 400, 800, 1200, 1599):
        draw.line((coordinate, 0, coordinate, 1599), fill=218, width=1)
        draw.line((0, coordinate, 1599, coordinate), fill=218, width=1)
    for index, entry in enumerate(entries):
        character = str(entry["character"])
        codepoint = ord(character)
        reference = references[codepoint]
        font = pillow_font(
            str(reference["font_path"]),
            int(reference["font_index"]),
            238,
        )
        left = (index % GRID_COLUMNS) * COPYBOOK_CELL
        top = (index // GRID_COLUMNS) * COPYBOOK_CELL
        bbox = draw.textbbox((0, 0), character, font=font)
        ink_width = bbox[2] - bbox[0]
        ink_height = bbox[3] - bbox[1]
        x = left + (COPYBOOK_CELL - ink_width) / 2 - bbox[0]
        y = top + (COPYBOOK_CELL - ink_height) / 2 - bbox[1]
        draw.text((x, y), character, font=font, fill=0)
    return image


def _actual_initial_prompt(batch: Mapping[str, Any]) -> str:
    rows = [
        "".join(
            str(entry["character"])
            for entry in batch["entries"][start : start + GRID_COLUMNS]
        )
        for start in range(0, len(batch["entries"]), GRID_COLUMNS)
    ]
    cells = "\n".join(
        f"Cell {int(entry['cell']):02d}: {entry['codepoint']} "
        f"{entry['character']} — {entry['motif_class']}"
        for entry in batch["entries"]
    )
    tail_cells = ", ".join(
        str(value) for value in batch["tail_terminal_cells"]
    )
    style_count = len(batch["style_references"])
    if style_count == 1:
        input_images = (
            "Input images: Image 1 is the approved Mew Note TC v2 style "
            "pilot (style rhythm only); Image 2 is an identity-only copybook "
            "(code point identity only).\n"
        )
        style_images = "Image 1"
    elif style_count == 2:
        input_images = (
            "Input images: Images 1 and 2 are the approved Mew Note TC Han "
            "and non-Han style pilots (style rhythm only); Image 3 is an "
            "identity-only copybook (code point identity only).\n"
        )
        style_images = "Images 1 and 2"
    else:
        raise MewNoteBatchError(
            "visible batches require one or two style references"
        )
    return "".join(
        (
        "Use case: logo-brand\n"
        "Asset type: original typeface source glyph sheet\n"
        f"Primary request: create one new Mew Note TC sheet for "
        f"{batch['collection_id']}/{batch['batch_id']}.\n",
        input_images,
        "Scene/backdrop: pure white square background with exactly five "
        "horizontal and five vertical thin neutral-gray rules forming a "
        "4 by 4 grid, including all four outer border rules. No other "
        "background marks.\n"
        "Style/medium: original upright rounded gel-pen handwriting, black "
        "ink, low contrast, soft human terminals, consistent with ",
        style_images,
        " "
        "without copying any raster or outline.\n"
        "Composition/framing: one centered glyph per cell, row-major, "
        "generous padding, no contact with grid rules.\n"
        "Exact row-major rows (verbatim):\n",
        "\n".join(rows),
        "\nExact cells (verbatim):\n",
        cells,
        "\n"
        f"Tail-terminal cells only: {tail_cells}. In each listed cell, use "
        "at most one restrained curl continuing an existing final stroke "
        "in the same connected contour. All other cells must have no cat "
        "tail.\n"
        "Constraints: preserve every Traditional Chinese character exactly; "
        "do not simplify, substitute, translate, normalize, label, number, "
        "caption, shade, or decorate. No detached ears, hats, faces, "
        "whiskers, paws, silhouettes, floating marks, spikes, sharp thorns, "
        "self-intersections, shadows, paper texture, signatures, or "
        "watermarks. The identity copybook must never be traced, transformed, "
        "pasted, or reused as an outline. Render only the 16 requested "
        "glyphs and the neutral-gray grid.\n",
        )
    )


def materialize_batch(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    contract = load_contract(context)
    batch = frozen_batch(context, collection_id, batch_id)
    root = _batch_root(context, collection_id, batch_id)
    root.mkdir(parents=True, exist_ok=True)
    prompt_path = root / "prompt.md"
    template = (
        context.project_root
        / context.authoring_payload["prompt_template"]["path"]
    ).read_text(encoding="utf-8")
    intended = mew_note_bulk_pipeline._render_prompt(
        template,
        collection_id=collection_id,
        batch_id=batch_id,
        entries=batch["entries"],
        style_references=batch["style_references"],
    )
    if hashlib.sha256(intended.encode("utf-8")).hexdigest() != (
        batch["prompt_sha256"]
    ):
        raise MewNoteBatchError("intended prompt does not match frozen plan")
    _atomic_write(prompt_path, intended.encode("utf-8"))

    references, configured_paths = _reference_catalog(
        contract,
        batch["entries"],
    )
    copybook_path = root / "identity-copybook.png"
    image = _render_copybook(batch["entries"], references)
    with tempfile.NamedTemporaryFile(
        suffix=".png",
        dir=root,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
    try:
        image.save(temporary, format="PNG", optimize=False)
        _atomic_copy(temporary, copybook_path)
    finally:
        temporary.unlink(missing_ok=True)

    tool_prompt_path = root / "tool-step-0001.txt"
    _atomic_write(
        tool_prompt_path,
        _actual_initial_prompt(batch).encode("utf-8"),
    )
    catalog_by_path = {
        str(Path(str(item["path"])).expanduser().resolve()): item
        for item in contract["identity_reference_fonts"]
    }
    identities: list[dict[str, Any]] = []
    for entry in batch["entries"]:
        codepoint = ord(str(entry["character"]))
        reference = references[codepoint]
        configured = catalog_by_path[str(reference["font_path"])]
        identities.append(
            {
                "cell": int(entry["cell"]),
                "character": str(entry["character"]),
                "codepoint": str(entry["codepoint"]),
                "role": "identity-reference-only-no-outline-import",
                "external_font": {
                    "path": str(reference["font_path"]),
                    "sha256": str(reference["font_sha256"]),
                    "face_index": int(reference["font_index"]),
                    "postscript_name": str(reference["postscript_name"]),
                    "glyph_name": str(reference["glyph_name"]),
                    "binary_committed": False,
                    "validation": list(reference["validation"]),
                },
            }
        )
    draft: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": DRAFT_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "collection_id": collection_id,
        "batch_id": batch_id,
        "family_context": context.evidence_binding(collection_id),
        "batch_evidence_contract": _pin(
            context.project_root / CONTRACT_PATH,
            project_root=context.project_root,
        ),
        "batch_plan": _pin(
            context.project_root / PLAN_PATH,
            project_root=context.project_root,
        ),
        "batch_contract_sha256": batch["batch_contract_sha256"],
        "entries": batch["entries"],
        "tail_terminal_cells": batch["tail_terminal_cells"],
        "intended_prompt": _pin(
            prompt_path,
            project_root=context.project_root,
        ),
        "actual_initial_tool_prompt": _pin(
            tool_prompt_path,
            project_root=context.project_root,
        ),
        "identity_copybook": {
            **_pin(copybook_path, project_root=context.project_root),
            "width": COPYBOOK_SIDE,
            "height": COPYBOOK_SIDE,
            "mode": "L",
            "role": "identity-reference-only-no-outline-import",
            "glyphs": identities,
            "configured_external_font_count": len(configured_paths),
        },
        "style_references": batch["style_references"],
        "planned_raster": {
            "path": _project_relative(root / "raster.png", project_root=context.project_root),
            "state": "not-generated",
        },
        "state": "materialized-awaiting-generation",
    }
    draft["draft_sha256"] = canonical_json_sha256(
        {key: value for key, value in draft.items() if key != "draft_sha256"}
    )
    _atomic_json(root / "draft.json", draft)
    return validate_draft(context, collection_id, batch_id)


def validate_draft(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    contract = load_contract(context)
    batch = frozen_batch(context, collection_id, batch_id)
    root = _batch_root(context, collection_id, batch_id)
    path = root / "draft.json"
    payload = _object(path, label="batch draft")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("record_type") != DRAFT_RECORD_TYPE
        or payload.get("family_id") != FAMILY_ID
        or payload.get("pipeline_id") != PIPELINE_ID
        or payload.get("collection_id") != collection_id
        or payload.get("batch_id") != batch_id
        or payload.get("family_context")
        != context.evidence_binding(collection_id)
        or payload.get("batch_contract_sha256")
        != batch["batch_contract_sha256"]
        or payload.get("entries") != batch["entries"]
        or payload.get("tail_terminal_cells")
        != batch["tail_terminal_cells"]
        or payload.get("state") != "materialized-awaiting-generation"
    ):
        raise MewNoteBatchError("batch draft identity or binding mismatch")
    expected_hash = canonical_json_sha256(
        {key: value for key, value in payload.items() if key != "draft_sha256"}
    )
    if payload.get("draft_sha256") != expected_hash:
        raise MewNoteBatchError("batch draft canonical hash mismatch")
    for key in (
        "batch_evidence_contract",
        "batch_plan",
        "intended_prompt",
        "actual_initial_tool_prompt",
    ):
        reference = payload[key]
        file_path = context.project_root / _canonical_relative(
            reference["path"],
            label=f"draft.{key}.path",
        )
        _regular_file(file_path, label=f"draft.{key}")
        if sha256_path(file_path) != _digest(
            reference["sha256"],
            label=f"draft.{key}.sha256",
        ):
            raise MewNoteBatchError(f"draft.{key} hash mismatch")
    copybook = payload["identity_copybook"]
    copybook_path = context.project_root / _canonical_relative(
        copybook["path"],
        label="draft.identity_copybook.path",
    )
    _regular_file(copybook_path, label="identity copybook")
    if sha256_path(copybook_path) != copybook["sha256"]:
        raise MewNoteBatchError("identity copybook hash mismatch")
    if copybook_path != root / "identity-copybook.png":
        raise MewNoteBatchError("identity copybook path is not canonical")
    if (
        copybook.get("role")
        != "identity-reference-only-no-outline-import"
        or copybook.get("width") != COPYBOOK_SIDE
        or copybook.get("height") != COPYBOOK_SIDE
        or copybook.get("mode") != "L"
        or len(copybook.get("glyphs", [])) != len(batch["entries"])
    ):
        raise MewNoteBatchError("identity copybook role or count changed")
    expected_references, configured_paths = _reference_catalog(
        contract,
        batch["entries"],
    )
    if copybook.get("configured_external_font_count") != len(
        configured_paths
    ):
        raise MewNoteBatchError("identity copybook font count changed")
    for expected_entry, glyph in zip(
        batch["entries"],
        copybook["glyphs"],
        strict=True,
    ):
        codepoint = ord(str(expected_entry["character"]))
        selected = expected_references[codepoint]
        external = glyph.get("external_font")
        expected_external = {
            "path": str(selected["font_path"]),
            "sha256": str(selected["font_sha256"]),
            "face_index": int(selected["font_index"]),
            "postscript_name": str(selected["postscript_name"]),
            "glyph_name": str(selected["glyph_name"]),
            "binary_committed": False,
            "validation": list(selected["validation"]),
        }
        if glyph != {
            "cell": int(expected_entry["cell"]),
            "character": str(expected_entry["character"]),
            "codepoint": str(expected_entry["codepoint"]),
            "role": "identity-reference-only-no-outline-import",
            "external_font": expected_external,
        }:
            raise MewNoteBatchError(
                f"identity copybook provenance mismatch at cell "
                f"{expected_entry['cell']}"
            )
        if external != expected_external:
            raise MewNoteBatchError("identity copybook external font mismatch")
    if payload.get("planned_raster") != {
        "path": _project_relative(
            root / "raster.png",
            project_root=context.project_root,
        ),
        "state": "not-generated",
    }:
        raise MewNoteBatchError("draft planned raster path changed")
    return payload


def _generation_input_payload(
    value: GenerationInput,
    *,
    context: FamilyContext,
    root: Path,
) -> dict[str, Any]:
    if value.role not in INPUT_ROLES:
        raise MewNoteBatchError(f"unsupported input role: {value.role}")
    digest = _digest(value.sha256, label="generation input hash")
    if value.role == "parent-output":
        if value.retention != "hash-only-rejected" or value.path is not None:
            raise MewNoteBatchError(
                "parent output input must be hash-only and pathless"
            )
        path_value = None
    else:
        if value.retention != "retained-reference" or value.path is None:
            raise MewNoteBatchError(
                "style/copybook input must be a retained reference"
            )
        _regular_file(value.path, label="generation input")
        if sha256_path(value.path) != digest:
            raise MewNoteBatchError("generation input hash mismatch")
        path_value = _project_relative(
            value.path,
            project_root=context.project_root,
        )
        if value.role == "identity-copybook" and value.path != (
            root / "identity-copybook.png"
        ):
            raise MewNoteBatchError("wrong identity copybook input")
        if (
            value.role == "style-reference"
            and "families/mew-note-tc" not in path_value
        ):
            raise MewNoteBatchError("style reference crosses family boundary")
    return {
        "role": value.role,
        "retention": value.retention,
        "path": path_value,
        "sha256": digest,
    }


def register_history(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
    *,
    steps: Sequence[GenerationStep],
) -> dict[str, Any]:
    draft = validate_draft(context, collection_id, batch_id)
    batch = frozen_batch(context, collection_id, batch_id)
    root = _batch_root(context, collection_id, batch_id)
    if not steps:
        raise MewNoteBatchError("generation history cannot be empty")
    expected_parent: str | None = None
    accepted_count = 0
    step_payloads: list[dict[str, Any]] = []
    for sequence, step in enumerate(steps, start=1):
        if step.operation not in OPERATIONS:
            raise MewNoteBatchError("generation operation is invalid")
        if step.disposition not in DISPOSITIONS:
            raise MewNoteBatchError("generation disposition is invalid")
        if CALL_ID_PATTERN.fullmatch(step.call_id) is None:
            raise MewNoteBatchError("generation call ID is invalid")
        expected_prompt = root / f"tool-step-{sequence:04d}.txt"
        if step.prompt_path.resolve() != expected_prompt.resolve():
            raise MewNoteBatchError("actual tool prompt path is not canonical")
        _regular_file(step.prompt_path, label="actual tool prompt")
        if sequence == 1:
            if (
                step.operation != "generate"
                or step.parent_output_sha256 is not None
                or any(value.role == "parent-output" for value in step.inputs)
            ):
                raise MewNoteBatchError("first generation step is invalid")
        else:
            if (
                step.operation != "correction"
                or step.parent_output_sha256 != expected_parent
                or sum(value.role == "parent-output" for value in step.inputs)
                != 1
                or next(
                    value.sha256
                    for value in step.inputs
                    if value.role == "parent-output"
                )
                != expected_parent
            ):
                raise MewNoteBatchError("correction parent hash chain is invalid")
        input_payloads = [
            _generation_input_payload(
                value,
                context=context,
                root=root,
            )
            for value in step.inputs
        ]
        expected_style_inputs = [
            {
                "role": "style-reference",
                "retention": "retained-reference",
                "path": str(reference["path"]),
                "sha256": str(reference["sha256"]),
            }
            for reference in batch["style_references"]
        ]
        expected_copybook_input = {
            "role": "identity-copybook",
            "retention": "retained-reference",
            "path": draft["identity_copybook"]["path"],
            "sha256": draft["identity_copybook"]["sha256"],
        }
        expected_inputs = (
            ([] if sequence == 1 else [{
                "role": "parent-output",
                "retention": "hash-only-rejected",
                "path": None,
                "sha256": expected_parent,
            }])
            + expected_style_inputs
            + [expected_copybook_input]
        )
        if input_payloads != expected_inputs:
            raise MewNoteBatchError(
                "generation inputs do not match the frozen batch references"
            )
        if sum(item["role"] == "identity-copybook" for item in input_payloads) != 1:
            raise MewNoteBatchError("each call must include one identity copybook")
        if sum(
            item["role"] == "style-reference" for item in input_payloads
        ) != len(expected_style_inputs):
            raise MewNoteBatchError(
                "each call must include every frozen style reference"
            )
        output_hash = _digest(step.output_sha256, label="output hash")
        if step.disposition == "rejected":
            if step.output_path is not None:
                raise MewNoteBatchError("rejected output must be hash-only")
            output_path = None
            output_retention = "hash-only-rejected"
        else:
            accepted_count += 1
            if sequence != len(steps) or step.output_path is None:
                raise MewNoteBatchError(
                    "accepted output must be the final retained step"
                )
            _regular_file(step.output_path, label="accepted generated output")
            if sha256_path(step.output_path) != output_hash:
                raise MewNoteBatchError("accepted output hash mismatch")
            canonical_raster = root / "raster.png"
            _atomic_copy(step.output_path, canonical_raster)
            if sha256_path(canonical_raster) != output_hash:
                raise MewNoteBatchError("canonical raster copy hash mismatch")
            output_path = _project_relative(
                canonical_raster,
                project_root=context.project_root,
            )
            output_retention = "retained-final"
        step_payloads.append(
            {
                "sequence": sequence,
                "operation": step.operation,
                "disposition": step.disposition,
                "call_id": step.call_id,
                "actual_tool_prompt": _pin(
                    step.prompt_path,
                    project_root=context.project_root,
                ),
                "inputs": input_payloads,
                "parent_output_sha256": step.parent_output_sha256,
                "output": {
                    "retention": output_retention,
                    "path": output_path,
                    "sha256": output_hash,
                },
            }
        )
        expected_parent = output_hash
    if accepted_count != 1:
        raise MewNoteBatchError("history must have exactly one accepted output")
    history: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": HISTORY_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "collection_id": collection_id,
        "batch_id": batch_id,
        "family_context": context.evidence_binding(collection_id),
        "batch_contract_sha256": batch["batch_contract_sha256"],
        "generator": GENERATOR,
        "intended_materialization": {
            "draft": _pin(
                root / "draft.json",
                project_root=context.project_root,
            ),
            "prompt": draft["intended_prompt"],
            "identity_copybook": {
                "path": draft["identity_copybook"]["path"],
                "sha256": draft["identity_copybook"]["sha256"],
                "role": draft["identity_copybook"]["role"],
            },
        },
        "steps": step_payloads,
        "accepted_final": {
            "call_id": step_payloads[-1]["call_id"],
            "raster": step_payloads[-1]["output"],
        },
        "state": "generated-unreviewed",
    }
    history["history_sha256"] = canonical_json_sha256(
        {key: value for key, value in history.items() if key != "history_sha256"}
    )
    history_path = root / "history.json"
    _atomic_json(history_path, history)
    source = {
        "schema_version": SCHEMA_VERSION,
        "record_type": SOURCE_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "collection_id": collection_id,
        "batch_id": batch_id,
        "state": "generated-unreviewed",
        "family_context": context.evidence_binding(collection_id),
        "batch_contract_sha256": batch["batch_contract_sha256"],
        "generation_history": _pin(
            history_path,
            project_root=context.project_root,
        ),
        "raster": "raster.png",
        "raster_sha256": step_payloads[-1]["output"]["sha256"],
        "grid": {
            "rows": GRID_ROWS,
            "columns": GRID_COLUMNS,
            "characters": [
                str(entry["character"]) for entry in batch["entries"]
            ],
            "empty_grid_cells": GRID_CAPACITY - len(batch["entries"]),
        },
        "motif_assignments": [
            {
                "cell": int(entry["cell"]),
                "codepoint": str(entry["codepoint"]),
                "motif_class": str(entry["motif_class"]),
            }
            for entry in batch["entries"]
        ],
        "review": {
            "topology": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }
    _atomic_json(root / "source.json", source)
    return validate_source(context, collection_id, batch_id)


def validate_history(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    batch = frozen_batch(context, collection_id, batch_id)
    root = _batch_root(context, collection_id, batch_id)
    payload = _object(root / "history.json", label="generation history")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("record_type") != HISTORY_RECORD_TYPE
        or payload.get("family_id") != FAMILY_ID
        or payload.get("pipeline_id") != PIPELINE_ID
        or payload.get("collection_id") != collection_id
        or payload.get("batch_id") != batch_id
        or payload.get("family_context")
        != context.evidence_binding(collection_id)
        or payload.get("batch_contract_sha256")
        != batch["batch_contract_sha256"]
        or payload.get("generator") != GENERATOR
        or payload.get("state") != "generated-unreviewed"
    ):
        raise MewNoteBatchError("generation history binding mismatch")
    expected = canonical_json_sha256(
        {key: value for key, value in payload.items() if key != "history_sha256"}
    )
    if payload.get("history_sha256") != expected:
        raise MewNoteBatchError("generation history canonical hash mismatch")
    draft = validate_draft(context, collection_id, batch_id)
    intended = payload.get("intended_materialization")
    if intended != {
        "draft": _pin(
            root / "draft.json",
            project_root=context.project_root,
        ),
        "prompt": draft["intended_prompt"],
        "identity_copybook": {
            "path": draft["identity_copybook"]["path"],
            "sha256": draft["identity_copybook"]["sha256"],
            "role": draft["identity_copybook"]["role"],
        },
    }:
        raise MewNoteBatchError("history intended materialization mismatch")
    load_contract(context)
    expected_copybook_input = {
        "role": "identity-copybook",
        "retention": "retained-reference",
        "path": draft["identity_copybook"]["path"],
        "sha256": draft["identity_copybook"]["sha256"],
    }
    expected_style_inputs = [
        {
            "role": "style-reference",
            "retention": "retained-reference",
            "path": str(reference["path"]),
            "sha256": str(reference["sha256"]),
        }
        for reference in batch["style_references"]
    ]
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise MewNoteBatchError("generation history steps are missing")
    expected_parent = None
    accepted = 0
    for sequence, step in enumerate(steps, start=1):
        if (
            not isinstance(step, dict)
            or step.get("sequence") != sequence
            or CALL_ID_PATTERN.fullmatch(str(step.get("call_id"))) is None
        ):
            raise MewNoteBatchError("generation history step identity invalid")
        prompt = step["actual_tool_prompt"]
        prompt_path = context.project_root / _canonical_relative(
            prompt["path"],
            label="history tool prompt path",
        )
        if prompt_path != root / f"tool-step-{sequence:04d}.txt":
            raise MewNoteBatchError("history tool prompt is not canonical")
        _regular_file(prompt_path, label="history tool prompt")
        if sha256_path(prompt_path) != prompt["sha256"]:
            raise MewNoteBatchError("history tool prompt hash mismatch")
        if sequence == 1:
            if (
                step["operation"] != "generate"
                or step["parent_output_sha256"] is not None
            ):
                raise MewNoteBatchError("initial history step invalid")
            expected_inputs = [
                *expected_style_inputs,
                expected_copybook_input,
            ]
        elif (
            step["operation"] != "correction"
            or step["parent_output_sha256"] != expected_parent
        ):
            raise MewNoteBatchError("history parent chain mismatch")
        else:
            expected_inputs = [
                {
                    "role": "parent-output",
                    "retention": "hash-only-rejected",
                    "path": None,
                    "sha256": expected_parent,
                },
                *expected_style_inputs,
                expected_copybook_input,
            ]
        if step.get("inputs") != expected_inputs:
            raise MewNoteBatchError("history input image chain mismatch")
        output = step["output"]
        expected_parent = _digest(output["sha256"], label="history output")
        if step["disposition"] == "rejected":
            if output != {
                "retention": "hash-only-rejected",
                "path": None,
                "sha256": expected_parent,
            }:
                raise MewNoteBatchError("rejected history output is retained")
        elif step["disposition"] == "accepted":
            accepted += 1
            if (
                sequence != len(steps)
                or output["retention"] != "retained-final"
                or output["path"]
                != _project_relative(
                    root / "raster.png",
                    project_root=context.project_root,
                )
            ):
                raise MewNoteBatchError("accepted history output is invalid")
            if sha256_path(root / "raster.png") != expected_parent:
                raise MewNoteBatchError("accepted raster hash drifted")
        else:
            raise MewNoteBatchError("history disposition invalid")
    if accepted != 1:
        raise MewNoteBatchError("history does not have one accepted step")
    if payload.get("accepted_final") != {
        "call_id": steps[-1]["call_id"],
        "raster": steps[-1]["output"],
    }:
        raise MewNoteBatchError("history accepted-final summary mismatch")
    return payload


def validate_source(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    history = validate_history(context, collection_id, batch_id)
    batch = frozen_batch(context, collection_id, batch_id)
    root = _batch_root(context, collection_id, batch_id)
    path = root / "source.json"
    payload = _object(path, label="generated source")
    expected_keys = {
        "schema_version",
        "record_type",
        "family_id",
        "pipeline_id",
        "collection_id",
        "batch_id",
        "state",
        "family_context",
        "batch_contract_sha256",
        "generation_history",
        "raster",
        "raster_sha256",
        "grid",
        "motif_assignments",
        "review",
    }
    if set(payload) != expected_keys:
        raise MewNoteBatchError("generated source key set changed")
    if (
        payload["schema_version"] != SCHEMA_VERSION
        or payload["record_type"] != SOURCE_RECORD_TYPE
        or payload["family_id"] != FAMILY_ID
        or payload["pipeline_id"] != PIPELINE_ID
        or payload["collection_id"] != collection_id
        or payload["batch_id"] != batch_id
        or payload["state"] != "generated-unreviewed"
        or payload["family_context"] != context.evidence_binding(collection_id)
        or payload["batch_contract_sha256"]
        != batch["batch_contract_sha256"]
        or payload["raster"] != "raster.png"
        or payload["raster_sha256"]
        != history["accepted_final"]["raster"]["sha256"]
        or payload["review"]
        != {
            "topology": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        }
    ):
        raise MewNoteBatchError("generated source binding mismatch")
    history_pin = payload["generation_history"]
    if (
        history_pin["path"]
        != _project_relative(
            root / "history.json",
            project_root=context.project_root,
        )
        or history_pin["sha256"] != sha256_path(root / "history.json")
    ):
        raise MewNoteBatchError("generated source history pin mismatch")
    expected_grid = {
        "rows": GRID_ROWS,
        "columns": GRID_COLUMNS,
        "characters": [
            str(entry["character"]) for entry in batch["entries"]
        ],
        "empty_grid_cells": GRID_CAPACITY - len(batch["entries"]),
    }
    if payload["grid"] != expected_grid:
        raise MewNoteBatchError("generated source grid mismatch")
    if sha256_path(root / "raster.png") != payload["raster_sha256"]:
        raise MewNoteBatchError("generated source raster hash mismatch")
    return payload


def build_vector_batch(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    validate_source(context, collection_id, batch_id)
    paths = context.batch_paths(collection_id, batch_id)
    final = imagegen_font_pipeline.build_batch(
        paths.source / "source.json",
        output_root=paths.build.parent,
        allowed_raster_root=paths.source,
        family_name_prefix="Mew Note TC",
        postscript_name_prefix="MewNoteTC",
    )
    if final != paths.build:
        raise MewNoteBatchError("vector build escaped the family batch root")
    report_path = final / "report.json"
    report = _object(report_path, label="vector report")
    glyphs = report.get("glyphs")
    if (
        report.get("pipeline") != "imagegen-raster-potrace-quadratic-v2"
        or report.get("approval_state") != "unreviewed"
        or report.get("batch_id") != batch_id
        or report.get("source_descriptor_sha256")
        != sha256_path(paths.source / "source.json")
        or report.get("font", {}).get("cmap_count")
        != len(frozen_batch(context, collection_id, batch_id)["entries"])
        or not isinstance(glyphs, list)
        or any(record.get("micro_edge_count") != 0 for record in glyphs)
        or any(
            record.get("acute_micro_turn_count") != 0
            for record in glyphs
        )
    ):
        raise MewNoteBatchError("vector report does not pass strict gates")
    return {
        "report": _pin(report_path, project_root=context.project_root),
        "black_on_white": _pin(
            final / report["proofs"]["black_on_white"],
            project_root=context.project_root,
        ),
        "white_on_black": _pin(
            final / report["proofs"]["white_on_black"],
            project_root=context.project_root,
        ),
        "segmented_source": _pin(
            final / report["proofs"]["segmented_source"],
            project_root=context.project_root,
        ),
        "glyph_count": len(glyphs),
        "micro_edge_count": sum(
            int(record["micro_edge_count"]) for record in glyphs
        ),
        "acute_micro_turn_count": sum(
            int(record["acute_micro_turn_count"]) for record in glyphs
        ),
    }


def record_review(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
    *,
    cells: Sequence[Mapping[str, Any]],
    reviewer: str,
) -> dict[str, Any]:
    evidence = build_vector_batch(context, collection_id, batch_id)
    batch = frozen_batch(context, collection_id, batch_id)
    if len(cells) != len(batch["entries"]):
        raise MewNoteBatchError("review must contain one decision per cell")
    normalized: list[dict[str, Any]] = []
    for expected, actual in zip(batch["entries"], cells, strict=True):
        required = {
            "cell",
            "character",
            "codepoint",
            "identity",
            "topology",
            "motif_assignment",
            "tail_attachment",
            "grid_clearance",
            "spikes",
            "legibility_16px",
            "decision",
            "notes",
        }
        if not isinstance(actual, dict) or set(actual) != required:
            raise MewNoteBatchError("review cell key set changed")
        if (
            actual["cell"] != expected["cell"]
            or actual["character"] != expected["character"]
            or actual["codepoint"] != expected["codepoint"]
            or actual["decision"] != "ACCEPT"
            or any(
                actual[key] != "PASS"
                for key in (
                    "identity",
                    "topology",
                    "motif_assignment",
                    "grid_clearance",
                    "spikes",
                    "legibility_16px",
                )
            )
            or actual["tail_attachment"]
            != (
                "PASS"
                if expected["motif_class"] == "tail-terminal"
                else "NOT_APPLICABLE"
            )
            or not isinstance(actual["notes"], str)
            or not actual["notes"].strip()
        ):
            raise MewNoteBatchError("review cell did not pass exact gates")
        normalized.append(dict(actual))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "record_type": REVIEW_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "collection_id": collection_id,
        "batch_id": batch_id,
        "family_context": context.evidence_binding(collection_id),
        "batch_contract_sha256": batch["batch_contract_sha256"],
        "source": _pin(
            _batch_root(context, collection_id, batch_id) / "source.json",
            project_root=context.project_root,
        ),
        "evidence": evidence,
        "reviewer": {
            "name": reviewer,
            "role": "independent-raster-vector-technical-review",
            "independent_from_generator": True,
        },
        "cells": normalized,
        "decision": "ACCEPT",
        "release_approval": False,
    }
    path = _batch_root(context, collection_id, batch_id) / "review.json"
    _atomic_json(path, payload)
    return payload


def _result(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    root = _batch_root(context, collection_id, batch_id)
    files = {}
    for name in (
        "prompt.md",
        "identity-copybook.png",
        "draft.json",
        "tool-step-0001.txt",
        "history.json",
        "source.json",
        "raster.png",
        "review.json",
    ):
        path = root / name
        if path.is_file():
            files[name] = sha256_path(path)
    return {
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "collection_id": collection_id,
        "batch_id": batch_id,
        "files": files,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--collection-id", required=True)
    parser.add_argument("--batch-id", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("materialize")
    subparsers.add_parser("validate-draft")
    subparsers.add_parser("validate-source")
    subparsers.add_parser("build")
    subparsers.add_parser("status")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    context = load_context(args.project_root)
    if args.command == "materialize":
        materialize_batch(context, args.collection_id, args.batch_id)
    elif args.command == "validate-draft":
        validate_draft(context, args.collection_id, args.batch_id)
    elif args.command == "validate-source":
        validate_source(context, args.collection_id, args.batch_id)
    elif args.command == "build":
        build_vector_batch(context, args.collection_id, args.batch_id)
    print(
        json.dumps(
            _result(context, args.collection_id, args.batch_id),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
