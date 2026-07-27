#!/usr/bin/env python3
"""Build and validate the independent Mew Note TC pilot review evidence.

The tool recomputes source hashes, detects the four-by-four grids from pixels,
segments every cell, measures clipping and small isolated ink, and renders
deterministic 16/20/32/72 px proofs. It never infers visual approval. Identity,
tail attachment, spike quality, and legibility remain explicit reviewer
decisions in the separately hash-pinned review record.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ROOT = ROOT / "families/mew-note-tc"
PROVENANCE_PATH = FAMILY_ROOT / "pilots/provenance.json"
MOTIF_PATH = FAMILY_ROOT / "motif-contract.json"
REVIEW_PATH = FAMILY_ROOT / "pilots/review.json"
DEFAULT_OUTPUT = ROOT / "build/pilots/mew-note-review"

ROWS = 4
COLUMNS = 4
PROOF_SIZES = (16, 20, 32, 72)
GRID_PIXEL_CEILING = 245
GRID_MIN_COVERAGE = 0.75
INK_PIXEL_CEILING = 192
EDGE_BAND_PIXELS = 3
SMALL_COMPONENT_MINIMUM_PIXELS = 8
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

CHECK_KEYS = (
    "identity",
    "grid_clearance",
    "cropping",
    "spikes",
    "isolated_ink",
    "tail_attachment",
    "legibility_16px",
    "legibility_20px",
    "legibility_32px",
    "legibility_72px",
)
CHECK_DECISIONS = frozenset({"PASS", "REJECT", "NOT_APPLICABLE"})


class PilotReviewError(RuntimeError):
    """Pilot evidence or a reviewer decision violates the frozen contract."""


@dataclass(frozen=True)
class Grid:
    x_groups: tuple[tuple[int, int], ...]
    y_groups: tuple[tuple[int, int], ...]

    @property
    def x_centers(self) -> tuple[int, ...]:
        return tuple((start + end) // 2 for start, end in self.x_groups)

    @property
    def y_centers(self) -> tuple[int, ...]:
        return tuple((start + end) // 2 for start, end in self.y_groups)


@dataclass(frozen=True)
class Cell:
    character: str
    rank: int
    row: int
    column: int
    source: Image.Image
    copybook: Image.Image
    metrics: Mapping[str, Any]


@dataclass(frozen=True)
class Pilot:
    pilot_id: str
    raster_path: Path
    copybook_path: Path
    characters: tuple[str, ...]
    raster: Image.Image
    copybook: Image.Image
    raster_grid: Grid
    copybook_grid: Grid
    cells: tuple[Cell, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PilotReviewError(f"{path}: cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotReviewError(f"{path}: {label} must be an object")
    return value


def _exact_keys(
    value: Any,
    expected: set[str],
    *,
    where: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PilotReviewError(f"{where}: expected an object")
    actual = set(value)
    if actual != expected:
        raise PilotReviewError(
            f"{where}: fields differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    return value


def _require_relative_file(
    project_root: Path,
    raw_path: Any,
    raw_sha256: Any,
    *,
    allowed_root: Path,
    where: str,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise PilotReviewError(f"{where}.path must be nonempty text")
    if not isinstance(raw_sha256, str) or SHA256_PATTERN.fullmatch(
        raw_sha256
    ) is None:
        raise PilotReviewError(f"{where}.sha256 must be lowercase SHA-256")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise PilotReviewError(f"{where}.path must be a safe relative path")
    path = (project_root / relative).resolve()
    allowed = allowed_root.resolve()
    try:
        path.relative_to(allowed)
    except ValueError as exc:
        raise PilotReviewError(f"{where}.path escapes {allowed}") from exc
    if not path.is_file():
        raise PilotReviewError(f"{where}.path does not exist: {path}")
    digest = _sha256(path)
    if digest != raw_sha256:
        raise PilotReviewError(
            f"{where}.sha256 mismatch: expected {raw_sha256}, got {digest}"
        )
    return path


def _groups(indices: Sequence[int]) -> tuple[tuple[int, int], ...]:
    result: list[list[int]] = []
    for index in indices:
        if not result or index != result[-1][-1] + 1:
            result.append([index])
        else:
            result[-1].append(index)
    return tuple((group[0], group[-1]) for group in result)


def _detect_grid(image: Image.Image, *, where: str) -> Grid:
    gray = np.asarray(image.convert("L"), dtype=np.uint8)
    vertical_coverage = (gray < GRID_PIXEL_CEILING).mean(axis=0)
    horizontal_coverage = (gray < GRID_PIXEL_CEILING).mean(axis=1)
    x_groups = _groups(
        np.flatnonzero(vertical_coverage >= GRID_MIN_COVERAGE).tolist()
    )
    y_groups = _groups(
        np.flatnonzero(horizontal_coverage >= GRID_MIN_COVERAGE).tolist()
    )
    if len(x_groups) != COLUMNS + 1 or len(y_groups) != ROWS + 1:
        raise PilotReviewError(
            f"{where}: expected five detected rules per axis, got "
            f"x={len(x_groups)}, y={len(y_groups)}"
        )
    if any(end - start + 1 > 4 for start, end in (*x_groups, *y_groups)):
        raise PilotReviewError(f"{where}: a detected grid rule is too wide")
    if any(
        later[0] - earlier[1] < 100
        for groups in (x_groups, y_groups)
        for earlier, later in zip(groups, groups[1:])
    ):
        raise PilotReviewError(f"{where}: detected grid cells are implausibly small")
    return Grid(x_groups=x_groups, y_groups=y_groups)


def _cell_image(
    image: Image.Image,
    grid: Grid,
    *,
    row: int,
    column: int,
) -> Image.Image:
    left = grid.x_groups[column][1] + 1
    right = grid.x_groups[column + 1][0]
    top = grid.y_groups[row][1] + 1
    bottom = grid.y_groups[row + 1][0]
    if right <= left or bottom <= top:
        raise PilotReviewError("grid segmentation produced an empty cell")
    return image.crop((left, top, right, bottom)).convert("L")


def _ink_metrics(image: Image.Image) -> dict[str, Any]:
    gray = np.asarray(image.convert("L"), dtype=np.uint8)
    ink = gray < INK_PIXEL_CEILING
    ys, xs = np.nonzero(ink)
    if not len(xs):
        raise PilotReviewError("segmented visible pilot cell contains no ink")
    labels, count = ndimage.label(
        ink,
        structure=np.ones((3, 3), dtype=np.uint8),
    )
    component_areas = np.bincount(labels.ravel())[1:]
    small_limit = max(
        SMALL_COMPONENT_MINIMUM_PIXELS,
        int(round(ink.size * 0.0001)),
    )
    edge = np.zeros_like(ink)
    edge[:EDGE_BAND_PIXELS, :] = True
    edge[-EDGE_BAND_PIXELS:, :] = True
    edge[:, :EDGE_BAND_PIXELS] = True
    edge[:, -EDGE_BAND_PIXELS:] = True
    height, width = ink.shape
    bbox = [
        int(xs.min()),
        int(ys.min()),
        int(xs.max()) + 1,
        int(ys.max()) + 1,
    ]
    clearance = {
        "left": bbox[0],
        "top": bbox[1],
        "right": width - bbox[2],
        "bottom": height - bbox[3],
    }
    return {
        "cell_width": width,
        "cell_height": height,
        "ink_pixel_count": int(ink.sum()),
        "ink_bbox": bbox,
        "clearance_pixels": clearance,
        "edge_band_pixels": EDGE_BAND_PIXELS,
        "edge_contact_ink_pixels": int((ink & edge).sum()),
        "component_count": int(count),
        "minimum_component_pixels": int(component_areas.min()),
        "small_component_limit_pixels": small_limit,
        "small_isolated_component_count": int(
            (component_areas < small_limit).sum()
        ),
    }


def _artifact_image(
    project_root: Path,
    artifact: Mapping[str, Any],
    *,
    where: str,
) -> tuple[Path, Image.Image]:
    path = _require_relative_file(
        project_root,
        artifact.get("path"),
        artifact.get("sha256"),
        allowed_root=project_root / "families/mew-note-tc/pilots",
        where=where,
    )
    try:
        image = Image.open(path)
        image.load()
    except (OSError, ValueError) as exc:
        raise PilotReviewError(f"{where}: cannot decode PNG: {exc}") from exc
    if image.format != "PNG":
        raise PilotReviewError(f"{where}: artifact must decode as PNG")
    expected = (
        artifact.get("width"),
        artifact.get("height"),
        artifact.get("mode"),
    )
    actual = (image.width, image.height, image.mode)
    if actual != expected:
        raise PilotReviewError(
            f"{where}: image metadata differs; expected={expected}, got={actual}"
        )
    return path, image


def load_pilots(project_root: Path = ROOT) -> tuple[Pilot, ...]:
    project_root = project_root.resolve()
    provenance_path = project_root / "families/mew-note-tc/pilots/provenance.json"
    provenance = _read_object(provenance_path, label="pilot provenance")
    if (
        provenance.get("schema_version") != 1
        or provenance.get("record_type")
        != "mew-note-tc-style-pilot-provenance"
        or provenance.get("family_id") != "mew-note-tc"
        or provenance.get("pilot_state")
        != "pilot-source-frozen-review-pending"
    ):
        raise PilotReviewError(f"{provenance_path}: unexpected pilot contract")
    raw_pilots = provenance.get("pilots")
    if not isinstance(raw_pilots, list) or len(raw_pilots) != 2:
        raise PilotReviewError("pilot provenance must contain exactly two pilots")

    pilots: list[Pilot] = []
    for pilot_index, raw in enumerate(raw_pilots):
        if not isinstance(raw, dict):
            raise PilotReviewError(f"pilots[{pilot_index}] must be an object")
        pilot_id = raw.get("id")
        if pilot_id not in {
            "mew-note-han-style-pilot",
            "mew-note-nonhan-style-pilot",
        }:
            raise PilotReviewError(f"pilots[{pilot_index}].id is invalid")
        grid = raw.get("grid")
        if (
            not isinstance(grid, dict)
            or grid.get("rows") != ROWS
            or grid.get("columns") != COLUMNS
            or not isinstance(grid.get("cell_order"), list)
            or len(grid["cell_order"]) != ROWS * COLUMNS
            or any(
                not isinstance(character, str) or len(character) != 1
                for character in grid["cell_order"]
            )
        ):
            raise PilotReviewError(f"{pilot_id}: invalid four-by-four cell order")
        artifacts = raw.get("artifacts")
        if not isinstance(artifacts, dict):
            raise PilotReviewError(f"{pilot_id}.artifacts must be an object")
        raster_path, raster = _artifact_image(
            project_root,
            artifacts["raster"],
            where=f"{pilot_id}.raster",
        )
        copybook_path, copybook = _artifact_image(
            project_root,
            artifacts["identity_copybook"],
            where=f"{pilot_id}.identity_copybook",
        )
        raster_grid = _detect_grid(raster, where=f"{pilot_id}.raster")
        copybook_grid = _detect_grid(
            copybook,
            where=f"{pilot_id}.identity_copybook",
        )
        cells: list[Cell] = []
        for rank, character in enumerate(grid["cell_order"], start=1):
            row, column = divmod(rank - 1, COLUMNS)
            source_cell = _cell_image(
                raster,
                raster_grid,
                row=row,
                column=column,
            )
            copybook_cell = _cell_image(
                copybook,
                copybook_grid,
                row=row,
                column=column,
            )
            cells.append(
                Cell(
                    character=character,
                    rank=rank,
                    row=row,
                    column=column,
                    source=source_cell,
                    copybook=copybook_cell,
                    metrics={
                        "source": _ink_metrics(source_cell),
                        "copybook": _ink_metrics(copybook_cell),
                    },
                )
            )
        pilots.append(
            Pilot(
                pilot_id=pilot_id,
                raster_path=raster_path,
                copybook_path=copybook_path,
                characters=tuple(grid["cell_order"]),
                raster=raster,
                copybook=copybook,
                raster_grid=raster_grid,
                copybook_grid=copybook_grid,
                cells=tuple(cells),
            )
        )
    if len({pilot.pilot_id for pilot in pilots}) != len(pilots):
        raise PilotReviewError("pilot provenance contains duplicate IDs")
    return tuple(pilots)


def _fit(image: Image.Image, size: int) -> Image.Image:
    canvas = Image.new("L", (size, size), color=255)
    source = image.convert("L")
    ratio = min(size / source.width, size / source.height)
    width = max(1, int(round(source.width * ratio)))
    height = max(1, int(round(source.height * ratio)))
    resized = source.resize((width, height), Image.Resampling.LANCZOS)
    canvas.paste(resized, ((size - width) // 2, (size - height) // 2))
    return canvas


def _proof_panel(
    cell: Cell,
    *,
    size: int,
) -> Image.Image:
    panel = Image.new("L", (240, 584), color=255)
    draw = ImageDraw.Draw(panel)
    label = f"{cell.rank:02d} U+{ord(cell.character):04X}"
    draw.text((8, 4), label, fill=0)
    for section, source in enumerate((cell.source, cell.copybook)):
        actual = _fit(source, size)
        zoom = actual.resize((128, 128), Image.Resampling.NEAREST)
        inverted = ImageOps.invert(actual)
        inverted_zoom = inverted.resize((128, 128), Image.Resampling.NEAREST)
        base_y = 24 + section * 280
        panel.paste(actual, (8, base_y))
        panel.paste(zoom, (64, base_y))
        dark_box = Image.new("L", (size, size), color=0)
        dark_box.paste(inverted, (0, 0))
        panel.paste(dark_box, (8, base_y + 144))
        panel.paste(inverted_zoom, (64, base_y + 144))
    return panel


def _write_readability_proof(
    pilot: Pilot,
    *,
    size: int,
    output: Path,
) -> Path:
    panel_width, panel_height = 240, 584
    sheet = Image.new(
        "L",
        (panel_width * COLUMNS, panel_height * ROWS),
        color=255,
    )
    for cell in pilot.cells:
        sheet.paste(
            _proof_panel(cell, size=size),
            (cell.column * panel_width, cell.row * panel_height),
        )
    sheet.save(output)
    return output


def _write_segmented_proof(pilot: Pilot, output: Path) -> Path:
    panel_width, panel_height = 320, 176
    sheet = Image.new(
        "L",
        (panel_width * COLUMNS, panel_height * ROWS),
        color=255,
    )
    for cell in pilot.cells:
        panel = Image.new("L", (panel_width, panel_height), color=255)
        draw = ImageDraw.Draw(panel)
        draw.text(
            (4, 4),
            f"{cell.rank:02d} U+{ord(cell.character):04X}",
            fill=0,
        )
        panel.paste(_fit(cell.source, 144), (4, 24))
        panel.paste(_fit(cell.copybook, 144), (168, 24))
        sheet.paste(
            panel,
            (cell.column * panel_width, cell.row * panel_height),
        )
    sheet.save(output)
    return output


def _safe_output(project_root: Path, output: Path) -> Path:
    output = output.resolve()
    project_root = project_root.resolve()
    if output == project_root or project_root.is_relative_to(output):
        raise PilotReviewError("output must not be the project root or its parent")
    for forbidden in (
        project_root / ".git",
        project_root / "dist",
        project_root / "families",
        project_root / "sources",
    ):
        forbidden = forbidden.resolve()
        if output == forbidden or output.is_relative_to(forbidden):
            raise PilotReviewError(f"output must not be below {forbidden}")
    return output


def build(
    *,
    project_root: Path = ROOT,
    output: Path = DEFAULT_OUTPUT,
) -> Path:
    """Build deterministic pilot measurements and review proofs."""

    project_root = project_root.resolve()
    output = _safe_output(project_root, output)
    pilots = load_pilots(project_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent)
    )
    try:
        pilot_records: list[dict[str, Any]] = []
        proof_records: list[dict[str, str]] = []
        for pilot in pilots:
            proof_directory = stage / "proof" / pilot.pilot_id
            proof_directory.mkdir(parents=True)
            segmented = _write_segmented_proof(
                pilot,
                proof_directory / "segmented-source-vs-copybook.png",
            )
            proof_records.append(
                {
                    "pilot_id": pilot.pilot_id,
                    "kind": "segmented-source-vs-copybook",
                    "path": segmented.relative_to(stage).as_posix(),
                    "sha256": _sha256(segmented),
                }
            )
            for size in PROOF_SIZES:
                proof = _write_readability_proof(
                    pilot,
                    size=size,
                    output=proof_directory / f"readability-{size}px.png",
                )
                proof_records.append(
                    {
                        "pilot_id": pilot.pilot_id,
                        "kind": f"readability-{size}px",
                        "path": proof.relative_to(stage).as_posix(),
                        "sha256": _sha256(proof),
                    }
                )
            pilot_records.append(
                {
                    "pilot_id": pilot.pilot_id,
                    "raster": {
                        "path": pilot.raster_path.relative_to(
                            project_root
                        ).as_posix(),
                        "sha256": _sha256(pilot.raster_path),
                    },
                    "identity_copybook": {
                        "path": pilot.copybook_path.relative_to(
                            project_root
                        ).as_posix(),
                        "sha256": _sha256(pilot.copybook_path),
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

        report = {
            "schema_version": 1,
            "pipeline": "mew-note-pilot-raster-review-v1",
            "approval_state": "unreviewed",
            "family_id": "mew-note-tc",
            "inputs": {
                "provenance": {
                    "path": "families/mew-note-tc/pilots/provenance.json",
                    "sha256": _sha256(
                        project_root
                        / "families/mew-note-tc/pilots/provenance.json"
                    ),
                },
                "motif_contract": {
                    "path": "families/mew-note-tc/motif-contract.json",
                    "sha256": _sha256(
                        project_root
                        / "families/mew-note-tc/motif-contract.json"
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
                "grid_pixel_ceiling": GRID_PIXEL_CEILING,
                "grid_min_coverage": GRID_MIN_COVERAGE,
                "ink_pixel_ceiling": INK_PIXEL_CEILING,
                "edge_band_pixels": EDGE_BAND_PIXELS,
                "small_component_minimum_pixels": (
                    SMALL_COMPONENT_MINIMUM_PIXELS
                ),
            },
            "pilots": pilot_records,
            "proofs": proof_records,
            "review_policy": (
                "Automated measurements do not decide identity, spikes, tail "
                "attachment, or legibility; an independent review is required"
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


def _validate_reference(
    project_root: Path,
    raw: Any,
    *,
    expected_path: str,
    where: str,
) -> Path:
    value = _exact_keys(raw, {"path", "sha256"}, where=where)
    if value["path"] != expected_path:
        raise PilotReviewError(f"{where}.path must be {expected_path}")
    return _require_relative_file(
        project_root,
        value["path"],
        value["sha256"],
        allowed_root=project_root,
        where=where,
    )


def _validate_build_only_reference(
    project_root: Path,
    raw: Any,
    *,
    expected_path: str,
    where: str,
    required: bool,
) -> Path | None:
    value = _exact_keys(raw, {"path", "sha256"}, where=where)
    if value["path"] != expected_path:
        raise PilotReviewError(f"{where}.path must be {expected_path}")
    if (
        not isinstance(value["sha256"], str)
        or SHA256_PATTERN.fullmatch(value["sha256"]) is None
    ):
        raise PilotReviewError(f"{where}.sha256 must be lowercase SHA-256")
    relative = Path(value["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise PilotReviewError(f"{where}.path must be a safe relative path")
    path = (project_root / relative).resolve()
    build_root = (project_root / "build/pilots").resolve()
    try:
        path.relative_to(build_root)
    except ValueError as exc:
        raise PilotReviewError(f"{where}.path escapes {build_root}") from exc
    if not path.is_file():
        if required:
            raise PilotReviewError(f"{where}.path is not available: {path}")
        return None
    if _sha256(path) != value["sha256"]:
        raise PilotReviewError(f"{where}.sha256 does not match {path}")
    return path


def _validate_supplementary_evidence(
    project_root: Path,
    raw: Any,
    *,
    required: bool,
) -> None:
    supplementary = _exact_keys(
        raw,
        {
            "evidence_id",
            "role",
            "artifact_retention",
            "canonical_source",
            "encoded_coverage_credit",
            "source_raster",
            "vector_report",
            "proofs",
            "characters",
            "tail_terminal_ranks",
            "checks",
            "decision",
            "notes",
        },
        where="supplementary_scalability_evidence",
    )
    characters = list("的一人不為第回之子有也三名作以二")
    if supplementary["evidence_id"] != "mew-note-technical-han-0001":
        raise PilotReviewError("supplementary evidence ID is invalid")
    if supplementary["role"] != "supplementary-build-only-scalability-evidence":
        raise PilotReviewError("supplementary evidence role is invalid")
    if supplementary["artifact_retention"] != "build-only-not-committed":
        raise PilotReviewError("supplementary retention policy is invalid")
    if supplementary["canonical_source"] is not False:
        raise PilotReviewError("supplementary raster must not be canonical source")
    if supplementary["encoded_coverage_credit"] != 0:
        raise PilotReviewError("supplementary evidence must not receive coverage")
    if supplementary["characters"] != characters:
        raise PilotReviewError("supplementary character order changed")
    if supplementary["tail_terminal_ranks"] != [4, 6, 11, 14, 16]:
        raise PilotReviewError("supplementary tail assignment changed")
    checks = _exact_keys(
        supplementary["checks"],
        {
            "identity",
            "exact_tail_assignment",
            "grid_clearance",
            "cropping",
            "spikes",
            "isolated_ink",
            "small_size_legibility",
        },
        where="supplementary_scalability_evidence.checks",
    )
    if set(checks.values()) != {"PASS"}:
        raise PilotReviewError("supplementary review contains a failed check")
    if supplementary["decision"] != "ACCEPT_AS_SUPPLEMENTARY_ONLY":
        raise PilotReviewError("supplementary decision is invalid")
    if (
        not isinstance(supplementary["notes"], str)
        or not supplementary["notes"].strip()
    ):
        raise PilotReviewError("supplementary evidence needs reviewer notes")

    source_path = _validate_build_only_reference(
        project_root,
        supplementary["source_raster"],
        expected_path="build/pilots/mew-note-technical-han-0001-fresh.png",
        where="supplementary_scalability_evidence.source_raster",
        required=required,
    )
    report_path = _validate_build_only_reference(
        project_root,
        supplementary["vector_report"],
        expected_path=(
            "build/pilots/mew-vector/mew-note-technical-han-0001/report.json"
        ),
        where="supplementary_scalability_evidence.vector_report",
        required=required,
    )
    raw_proofs = supplementary["proofs"]
    if not isinstance(raw_proofs, list) or len(raw_proofs) != 3:
        raise PilotReviewError("supplementary evidence must pin three proofs")
    expected_proof_paths = {
        (
            "build/pilots/mew-vector/mew-note-technical-han-0001/proof/"
            "segmented-source-contact.png"
        ),
        (
            "build/pilots/mew-vector/mew-note-technical-han-0001/proof/"
            "small-sizes-black-on-white.png"
        ),
        (
            "build/pilots/mew-vector/mew-note-technical-han-0001/proof/"
            "small-sizes-white-on-black.png"
        ),
    }
    proof_paths: set[str] = set()
    available_proofs: list[Path | None] = []
    for index, reference in enumerate(raw_proofs):
        value = _exact_keys(
            reference,
            {"path", "sha256"},
            where=f"supplementary_scalability_evidence.proofs[{index}]",
        )
        if value["path"] not in expected_proof_paths:
            raise PilotReviewError("unexpected supplementary proof path")
        available_proofs.append(
            _validate_build_only_reference(
                project_root,
                value,
                expected_path=value["path"],
                where=f"supplementary_scalability_evidence.proofs[{index}]",
                required=required,
            )
        )
        proof_paths.add(value["path"])
    if proof_paths != expected_proof_paths:
        raise PilotReviewError("supplementary proof inventory is incomplete")

    available = (
        source_path is not None,
        report_path is not None,
        *(path is not None for path in available_proofs),
    )
    if any(available) and not all(available):
        raise PilotReviewError("supplementary build evidence availability differs")
    if report_path is None:
        return
    report = _read_object(report_path, label="supplementary vector report")
    if (
        report.get("schema_version") != 1
        or report.get("pipeline") != "imagegen-raster-potrace-quadratic-v2"
        or report.get("batch_id") != supplementary["evidence_id"]
        or report.get("source_raster_sha256")
        != supplementary["source_raster"]["sha256"]
        or report.get("characters") != characters
        or report.get("font", {}).get("cmap_count") != 16
    ):
        raise PilotReviewError("supplementary vector report identity changed")
    glyphs = report.get("glyphs")
    if not isinstance(glyphs, list) or len(glyphs) != 16:
        raise PilotReviewError("supplementary vector report lacks 16 glyphs")
    for index, glyph in enumerate(glyphs):
        if (
            glyph.get("character") != characters[index]
            or glyph.get("micro_edge_count") != 0
            or glyph.get("acute_micro_turn_count") != 0
        ):
            raise PilotReviewError(
                "supplementary glyph order or geometry checks changed"
            )


def validate_review(
    *,
    review_path: Path = REVIEW_PATH,
    evidence: Path = DEFAULT_OUTPUT,
    project_root: Path = ROOT,
    require_supplementary_evidence: bool = False,
) -> dict[str, Any]:
    """Validate a human review against rebuilt evidence and frozen inputs."""

    project_root = project_root.resolve()
    review_path = review_path.resolve()
    review = _read_object(review_path, label="pilot review")
    top = _exact_keys(
        review,
        {
            "schema_version",
            "record_type",
            "family_id",
            "review_state",
            "reviewer",
            "reviewed_on",
            "scope",
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
        top["schema_version"] != 1
        or top["record_type"] != "mew-note-tc-pilot-technical-review"
        or top["family_id"] != "mew-note-tc"
        or top["review_state"] not in {"ACCEPT", "REJECT"}
    ):
        raise PilotReviewError(f"{review_path}: invalid review identity/state")

    reviewer = _exact_keys(
        top["reviewer"],
        {"name", "role", "independent_from_generator"},
        where="reviewer",
    )
    if (
        not isinstance(reviewer["name"], str)
        or not reviewer["name"]
        or reviewer["role"] != "independent-pilot-technical-review"
        or reviewer["independent_from_generator"] is not True
    ):
        raise PilotReviewError("reviewer contract is invalid")
    if top["reviewed_on"] != "2026-07-29":
        raise PilotReviewError("reviewed_on must pin the review date")
    if top["scope"] != {
        "style_gate_only": True,
        "encoded_coverage_credit": 0,
        "bulk_authoring_decision": True,
    }:
        raise PilotReviewError("review scope is invalid")

    inputs = _exact_keys(
        top["inputs"],
        {"provenance", "motif_contract", "review_script"},
        where="inputs",
    )
    _validate_reference(
        project_root,
        inputs["provenance"],
        expected_path="families/mew-note-tc/pilots/provenance.json",
        where="inputs.provenance",
    )
    _validate_reference(
        project_root,
        inputs["motif_contract"],
        expected_path="families/mew-note-tc/motif-contract.json",
        where="inputs.motif_contract",
    )
    _validate_reference(
        project_root,
        inputs["review_script"],
        expected_path="scripts/review_mew_note_pilots.py",
        where="inputs.review_script",
    )

    evidence = evidence.resolve()
    report_path = evidence / "report.json"
    report = _read_object(report_path, label="rebuilt pilot report")
    if (
        report.get("schema_version") != 1
        or report.get("pipeline") != "mew-note-pilot-raster-review-v1"
        or report.get("approval_state") != "unreviewed"
        or report.get("family_id") != "mew-note-tc"
        or report.get("inputs")
        != {
            "provenance": inputs["provenance"],
            "motif_contract": inputs["motif_contract"],
        }
    ):
        raise PilotReviewError("rebuilt pilot report identity/input changed")
    evidence_contract = _exact_keys(
        top["evidence"],
        {"report", "proofs"},
        where="evidence",
    )
    if evidence_contract["report"] != {
        "path": "build/pilots/mew-note-review/report.json",
        "sha256": _sha256(report_path),
    }:
        raise PilotReviewError("review does not pin the rebuilt report")
    expected_proofs = {
        item["path"]: item["sha256"] for item in report["proofs"]
    }
    raw_proofs = evidence_contract["proofs"]
    if not isinstance(raw_proofs, list):
        raise PilotReviewError("evidence.proofs must be an array")
    review_proofs: dict[str, str] = {}
    for index, raw in enumerate(raw_proofs):
        proof = _exact_keys(
            raw,
            {"path", "sha256"},
            where=f"evidence.proofs[{index}]",
        )
        relative = proof["path"]
        canonical_prefix = "build/pilots/mew-note-review/"
        if not isinstance(relative, str) or not relative.startswith(
            canonical_prefix
        ):
            raise PilotReviewError("proof path is outside canonical evidence")
        report_relative = relative.removeprefix(canonical_prefix)
        proof_path = evidence / report_relative
        if not proof_path.is_file() or _sha256(proof_path) != proof["sha256"]:
            raise PilotReviewError(f"stale proof evidence: {relative}")
        review_proofs[report_relative] = proof["sha256"]
    if review_proofs != expected_proofs:
        raise PilotReviewError("review proof inventory is incomplete or changed")

    provenance = _read_object(
        project_root / "families/mew-note-tc/pilots/provenance.json",
        label="pilot provenance",
    )
    expected_characters = {
        item["id"]: tuple(item["grid"]["cell_order"])
        for item in provenance["pilots"]
    }
    report_metrics = {
        pilot["pilot_id"]: {
            cell["rank"]: cell["metrics"] for cell in pilot["cells"]
        }
        for pilot in report["pilots"]
    }
    raw_pilot_reviews = top["pilots"]
    if not isinstance(raw_pilot_reviews, list) or len(raw_pilot_reviews) != 2:
        raise PilotReviewError("review must cover exactly two pilots")
    decisions: list[tuple[str, int, str, str]] = []
    seen_pilots: set[str] = set()
    for pilot_index, raw_pilot in enumerate(raw_pilot_reviews):
        pilot_review = _exact_keys(
            raw_pilot,
            {"pilot_id", "decision", "cells"},
            where=f"pilots[{pilot_index}]",
        )
        pilot_id = pilot_review["pilot_id"]
        if pilot_id not in expected_characters or pilot_id in seen_pilots:
            raise PilotReviewError(f"invalid or duplicate pilot review: {pilot_id}")
        seen_pilots.add(pilot_id)
        if pilot_review["decision"] not in {"ACCEPT", "REJECT"}:
            raise PilotReviewError(f"{pilot_id}: invalid decision")
        raw_cells = pilot_review["cells"]
        if not isinstance(raw_cells, list) or len(raw_cells) != 16:
            raise PilotReviewError(f"{pilot_id}: review must cover 16 cells")
        for cell_index, raw_cell in enumerate(raw_cells):
            cell = _exact_keys(
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
            character = expected_characters[pilot_id][cell_index]
            if cell["rank"] != rank or cell["character"] != character:
                raise PilotReviewError(
                    f"{pilot_id}: cell {rank} identity/order changed"
                )
            if cell["motif_class"] not in {
                "tail-terminal",
                "soft-terminal",
                "neutral-safety",
            }:
                raise PilotReviewError(f"{pilot_id}: invalid motif class")
            checks = _exact_keys(
                cell["checks"],
                set(CHECK_KEYS),
                where=f"{pilot_id}.cells[{rank}].checks",
            )
            if any(value not in CHECK_DECISIONS for value in checks.values()):
                raise PilotReviewError(
                    f"{pilot_id}: cell {rank} has an invalid check decision"
                )
            if (
                cell["motif_class"] == "tail-terminal"
                and checks["tail_attachment"] == "NOT_APPLICABLE"
            ):
                raise PilotReviewError(
                    f"{pilot_id}: tail cell {rank} needs an attachment decision"
                )
            if (
                cell["motif_class"] != "tail-terminal"
                and checks["tail_attachment"] != "NOT_APPLICABLE"
            ):
                raise PilotReviewError(
                    f"{pilot_id}: non-tail cell {rank} attachment must be N/A"
                )
            metrics = report_metrics[pilot_id][rank]["source"]
            if (
                checks["grid_clearance"] == "PASS"
                and metrics["edge_contact_ink_pixels"] != 0
            ):
                raise PilotReviewError(
                    f"{pilot_id}: cell {rank} passes grid clearance with edge ink"
                )
            if (
                checks["isolated_ink"] == "PASS"
                and metrics["small_isolated_component_count"] != 0
            ):
                raise PilotReviewError(
                    f"{pilot_id}: cell {rank} passes with a small ink island"
                )
            if cell["decision"] not in {"ACCEPT", "REJECT"}:
                raise PilotReviewError(f"{pilot_id}: cell {rank} decision invalid")
            has_reject = "REJECT" in checks.values()
            if (cell["decision"] == "REJECT") != has_reject:
                raise PilotReviewError(
                    f"{pilot_id}: cell {rank} decision/checks disagree"
                )
            if not isinstance(cell["notes"], str) or not cell["notes"].strip():
                raise PilotReviewError(f"{pilot_id}: cell {rank} needs notes")
            decisions.append((pilot_id, rank, character, cell["decision"]))
        cell_states = [
            decision for pid, _, _, decision in decisions if pid == pilot_id
        ]
        expected_pilot_decision = (
            "ACCEPT" if set(cell_states) == {"ACCEPT"} else "REJECT"
        )
        if pilot_review["decision"] != expected_pilot_decision:
            raise PilotReviewError(f"{pilot_id}: aggregate decision is wrong")

    rejected = [
        {
            "pilot_id": pilot_id,
            "rank": rank,
            "character": character,
        }
        for pilot_id, rank, character, decision in decisions
        if decision == "REJECT"
    ]
    summary = _exact_keys(
        top["summary"],
        {
            "pilot_count",
            "cell_count",
            "accepted_cell_count",
            "rejected_cell_count",
            "rejected_cells",
        },
        where="summary",
    )
    if summary != {
        "pilot_count": 2,
        "cell_count": 32,
        "accepted_cell_count": 32 - len(rejected),
        "rejected_cell_count": len(rejected),
        "rejected_cells": rejected,
    }:
        raise PilotReviewError("review summary does not match cell decisions")
    expected_state = "ACCEPT" if not rejected else "REJECT"
    if top["review_state"] != expected_state:
        raise PilotReviewError("review_state does not match rejected cells")
    expected_authorization = {
        "bulk_authoring_allowed": not rejected,
        "reason": (
            "All 32 pilot cells passed the independent technical review"
            if not rejected
            else "At least one pilot cell failed the independent technical review"
        ),
    }
    if top["authorization"] != expected_authorization:
        raise PilotReviewError("authorization does not match the review result")
    _validate_supplementary_evidence(
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
        help="require the intentionally uncommitted supplementary build proof",
    )
    arguments = parser.parse_args()

    project_root = arguments.project_root.resolve()
    if arguments.command == "build":
        output = arguments.output
        if not output.is_absolute():
            output = project_root / output
        built = build(project_root=project_root, output=output)
        print(f"built Mew Note pilot review evidence: {built}")
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
        "validated Mew Note pilot review: "
        f"{review['review_state']}; "
        f"bulk={review['authorization']['bulk_authoring_allowed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
