#!/usr/bin/env python3
"""Build one image-generated vertical-alternate batch.

The six source sheets contain 93 independently authored, unencoded ``.vert``
outlines.  This builder validates each sheet against the frozen Unicode 17.0
vertical repertoire, then reuses the audited non-Han raster segmentation,
Potrace/cu2qu conversion, and zero-thorn geometry gates.  Its preview fonts
temporarily cmap each base scalar to the corresponding alternate solely for
proof rendering; the release compiler imports the approved outlines as
unencoded glyphs and constructs ``vert``/``vrt2`` substitutions.
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

from fontTools.ttLib import TTFont
from PIL import Image

from scripts import imagegen_font_pipeline as han_pipeline
from scripts import imagegen_nonhan_pipeline as nonhan


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
DEFAULT_DESCRIPTOR = IMAGEGEN_ROOT / "batches/vertical-0001.source.json"
DEFAULT_OUTPUT_ROOT = ROOT / "build/imagegen"
VERTICAL_REPERTOIRE = IMAGEGEN_ROOT / "repertoires/vertical-93.json"

PIPELINE_ID = "imagegen-raster-potrace-quadratic-vertical-v1"
SOURCE_TYPE = "imagegen-vertical-alternate"
REPERTOIRE_ID = "clear-hand-tc-vertical-alternates-93-uax50-17.0-v1"
REPERTOIRE_SHA256 = (
    "5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786"
)
REPERTOIRE_SEQUENCE_SHA256 = (
    "ae69a6532e9acd58527ed9a1f287a093757847a6938c608112314d8e6c674945"
)
NONHAN_REPERTOIRE_SHA256 = (
    "42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4"
)
SOURCE_BATCH_PATTERN = re.compile(r"imagegen-(vertical-[0-9]{4})")
BASE_BATCH_PATTERN = re.compile(r"vertical-[0-9]{4}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
ROWS = 4
COLUMNS = 4
CAPACITY = ROWS * COLUMNS
VERTICAL_PROOF_COVERAGE_DIVISOR = 10

TOP_LEVEL_FIELDS = {
    "schema_version",
    "source_type",
    "batch_id",
    "state",
    "generator",
    "generator_call",
    "repertoire",
    "raster",
    "raster_sha256",
    "prompt",
    "copybook",
    "style_reference",
    "grid",
    "review",
}
ALTERNATE_FIELDS = {
    "rank",
    "base_character",
    "base_codepoint",
    "unicode_name",
    "vertical_orientation",
    "tailoring",
    "glyph_name",
    "base_profile_id",
    "base_metrics",
    "copybook_reference",
}
REFERENCE_FIELDS = {
    "role",
    "font_path",
    "font_sha256",
    "font_index",
    "postscript_name",
    "base_glyph_id",
    "vertical_glyph_id",
    "used_glyph_id",
    "reference_vert_substitution",
    "reference_rotation_for_identity_only",
}
REPERTOIRE_FIELDS = {
    "schema_version",
    "repertoire_id",
    "source",
    "total",
    "sequence_sha256",
    "alternates",
    "batches",
}
REPERTOIRE_ALTERNATE_FIELDS = ALTERNATE_FIELDS - {"copybook_reference"}
REPERTOIRE_BATCH_FIELDS = {
    "batch_id",
    "start_rank",
    "end_rank",
    "base_codepoints",
    "empty_grid_cells",
}
REPERTOIRE_SOURCE = {
    "unicode_version": "17.0.0",
    "vertical_orientation_url": (
        "https://www.unicode.org/Public/17.0.0/ucd/"
        "VerticalOrientation.txt"
    ),
    "vertical_orientation_sha256": (
        "dcef09c3fb24d356b042569c328ec341efc5b53447700d799f2fb4834c3cd3cd"
    ),
    "nonhan_repertoire": "sources/imagegen/repertoires/nonhan-3060.json",
    "nonhan_repertoire_sha256": NONHAN_REPERTOIRE_SHA256,
    "policy": (
        "all encoded non-Han Tu/Tr scalars plus ten reviewed "
        "Taiwan/CJK project-tailored forms"
    ),
}
PREVIEW_METRICS: Mapping[str, Any] = {
    "horizontal_advance": {"kind": "fixed", "value": nonhan.UPM},
    "vertical_advance": {"kind": "fixed", "value": nonhan.UPM},
    "side_bearings": {"left": 32, "right": 32},
}


class VerticalPipelineError(RuntimeError):
    """A vertical source or generated artifact violated the strict contract."""


@dataclass(frozen=True)
class VerticalDescriptor:
    path: Path
    project_root: Path
    batch_id: str
    base_batch_id: str
    raster_path: Path
    raster_sha256: str
    generator_call: str
    repertoire_path: Path
    repertoire_sha256: str
    prompt_path: Path
    prompt_sha256: str
    copybook_path: Path
    copybook_sha256: str
    style_reference_path: Path
    style_reference_sha256: str
    alternates: tuple[Mapping[str, Any], ...]
    glyphs: tuple[nonhan.GlyphSpec, ...]
    cell_slots: tuple[nonhan.GlyphSpec | None, ...]
    empty_grid_cells: int
    review: Mapping[str, str]
    source_sha256: str


def _fail(where: object, message: str) -> None:
    raise VerticalPipelineError(f"{where}: {message}")


def _object(value: Any, *, where: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(where, "expected a JSON object")
    return value


def _read_object(path: Path) -> dict[str, Any]:
    try:
        return _object(
            json.loads(path.read_text(encoding="utf-8")),
            where=path,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise VerticalPipelineError(f"{path}: cannot read JSON: {exc}") from exc


def _resolve_asset(
    descriptor_path: Path,
    value: Any,
    *,
    expected: str,
    allowed_root: Path,
    where: str,
) -> Path:
    if value != expected:
        _fail(descriptor_path, f"{where} path must be {expected!r}")
    path = (descriptor_path.parent / value).resolve()
    if not nonhan._is_relative_to(path, allowed_root.resolve()) or not path.is_file():
        _fail(descriptor_path, f"{where} is missing or escapes its allowed root")
    return path


def _hashed_asset(
    descriptor_path: Path,
    value: Any,
    *,
    expected_path: str,
    expected_role: str,
    allowed_root: Path,
    where: str,
) -> tuple[Path, str]:
    record = _object(value, where=f"{descriptor_path}: {where}")
    if set(record) != {"path", "sha256", "role"}:
        _fail(descriptor_path, f"{where} fields are not exact")
    if record["role"] != expected_role:
        _fail(descriptor_path, f"{where} role changed")
    path = _resolve_asset(
        descriptor_path,
        record["path"],
        expected=expected_path,
        allowed_root=allowed_root,
        where=where,
    )
    digest = record["sha256"]
    if (
        not isinstance(digest, str)
        or SHA256_PATTERN.fullmatch(digest) is None
        or nonhan._sha256(path) != digest
    ):
        _fail(descriptor_path, f"{where} hash mismatch")
    return path, digest


def _validate_repertoire_payload(
    repertoire: Mapping[str, Any],
    *,
    where: object,
) -> Mapping[str, Any]:
    if set(repertoire) != REPERTOIRE_FIELDS:
        _fail(where, "vertical repertoire fields are not exact")
    if (
        repertoire["schema_version"] != 1
        or repertoire["repertoire_id"] != REPERTOIRE_ID
        or repertoire["source"] != REPERTOIRE_SOURCE
        or repertoire["total"] != 93
    ):
        _fail(where, "vertical repertoire identity changed")
    alternates = repertoire["alternates"]
    batches = repertoire["batches"]
    if (
        not isinstance(alternates, list)
        or len(alternates) != 93
        or not isinstance(batches, list)
        or len(batches) != 6
    ):
        _fail(where, "vertical repertoire cardinality changed")

    codepoints: list[str] = []
    characters: list[str] = []
    glyph_names: set[str] = set()
    for rank, raw in enumerate(alternates, start=1):
        record = _object(raw, where=f"{where}: alternate {rank}")
        if set(record) != REPERTOIRE_ALTERNATE_FIELDS:
            _fail(where, f"vertical alternate {rank} fields are not exact")
        character = nonhan._one_scalar(
            record["base_character"],
            where=f"{where}: alternate {rank}.base_character",
        )
        codepoint = nonhan._codepoint(
            record["base_codepoint"],
            where=f"{where}: alternate {rank}.base_codepoint",
        )
        label = f"U+{codepoint:04X}"
        glyph_name = (
            f"uni{codepoint:04X}.vert"
            if codepoint <= 0xFFFF
            else f"u{codepoint:05X}.vert"
        )
        if (
            record["rank"] != rank
            or ord(character) != codepoint
            or record["glyph_name"] != glyph_name
            or not isinstance(record["unicode_name"], str)
            or not record["unicode_name"]
            or record["vertical_orientation"] not in {"Tu", "Tr", "Tailored"}
            or record["base_profile_id"]
            not in nonhan.REPERTOIRE_PROFILE_TRANSFORMS
            or glyph_name in glyph_names
            or label in codepoints
        ):
            _fail(where, f"vertical alternate {rank} identity changed")
        tailoring = record["tailoring"]
        if (
            (record["vertical_orientation"] == "Tailored")
            and (not isinstance(tailoring, str) or not tailoring)
        ) or (
            record["vertical_orientation"] != "Tailored"
            and tailoring is not None
        ):
            _fail(where, f"vertical alternate {rank} tailoring changed")
        metrics = record["base_metrics"]
        if not isinstance(metrics, dict) or set(metrics) != {
            "horizontal_advance",
            "vertical_advance",
            "side_bearings",
        }:
            _fail(where, f"vertical alternate {rank} base metrics changed")
        horizontal = metrics["horizontal_advance"]
        vertical = metrics["vertical_advance"]
        bearings = metrics["side_bearings"]
        if (
            not isinstance(horizontal, dict)
            or horizontal.get("kind") not in {"fixed", "source-proportional"}
            or set(horizontal)
            != (
                {"kind", "value"}
                if horizontal.get("kind") == "fixed"
                else {"kind"}
            )
            or (
                horizontal.get("kind") == "fixed"
                and (
                    isinstance(horizontal.get("value"), bool)
                    or not isinstance(horizontal.get("value"), int)
                    or horizontal["value"] <= 0
                )
            )
            or not isinstance(vertical, dict)
            or set(vertical) != {"kind", "value"}
            or vertical.get("kind") != "fixed"
            or isinstance(vertical.get("value"), bool)
            or not isinstance(vertical.get("value"), int)
            or vertical["value"] <= 0
            or not isinstance(bearings, dict)
            or set(bearings) != {"left", "right"}
            or any(
                isinstance(bearings.get(side), bool)
                or not isinstance(bearings.get(side), int)
                or bearings[side] < 0
                for side in ("left", "right")
            )
        ):
            _fail(where, f"vertical alternate {rank} base metrics are invalid")
        glyph_names.add(glyph_name)
        codepoints.append(label)
        characters.append(character)

    sequence = hashlib.sha256("".join(characters).encode("utf-8")).hexdigest()
    if (
        repertoire["sequence_sha256"] != REPERTOIRE_SEQUENCE_SHA256
        or sequence != REPERTOIRE_SEQUENCE_SHA256
    ):
        _fail(where, "vertical repertoire sequence hash changed")

    for index, raw in enumerate(batches):
        batch = _object(raw, where=f"{where}: batch {index + 1}")
        if set(batch) != REPERTOIRE_BATCH_FIELDS:
            _fail(where, f"vertical batch {index + 1} fields are not exact")
        start = index * CAPACITY
        end = min(start + CAPACITY, len(alternates))
        expected_labels = codepoints[start:end]
        expected_id = f"vertical-{index + 1:04d}"
        if (
            batch["batch_id"] != expected_id
            or batch["start_rank"] != start + 1
            or batch["end_rank"] != end
            or batch["base_codepoints"] != expected_labels
            or batch["empty_grid_cells"] != CAPACITY - len(expected_labels)
        ):
            _fail(where, f"vertical batch {expected_id} slice changed")
    return repertoire


def load_frozen_repertoire(
    path: Path = VERTICAL_REPERTOIRE,
    *,
    project_root: Path = ROOT,
) -> Mapping[str, Any]:
    project_root = project_root.resolve()
    expected = (
        project_root / "sources/imagegen/repertoires/vertical-93.json"
    ).resolve()
    path = path.resolve()
    if path != expected or not path.is_file():
        _fail(path, "vertical repertoire path is not canonical")
    if nonhan._sha256(path) != REPERTOIRE_SHA256:
        _fail(path, "vertical repertoire file hash changed")
    return _validate_repertoire_payload(
        _read_object(path),
        where=path,
    )


def _expected_batch(
    repertoire: Mapping[str, Any],
    base_batch_id: str,
) -> tuple[Mapping[str, Any], ...]:
    matches = [
        batch
        for batch in repertoire["batches"]
        if isinstance(batch, dict) and batch.get("batch_id") == base_batch_id
    ]
    if len(matches) != 1:
        raise VerticalPipelineError(
            f"vertical repertoire has no unique batch {base_batch_id}"
        )
    batch = matches[0]
    start = int(batch["start_rank"]) - 1
    end = int(batch["end_rank"])
    records = repertoire["alternates"][start:end]
    if not records or len(records) + int(batch["empty_grid_cells"]) != CAPACITY:
        raise VerticalPipelineError(
            f"vertical repertoire batch {base_batch_id} cardinality changed"
        )
    return tuple(records)


def _preview_spec(record: Mapping[str, Any]) -> nonhan.GlyphSpec:
    character = nonhan._one_scalar(
        record["base_character"],
        where=f"{record.get('base_codepoint')}.base_character",
    )
    codepoint = nonhan._codepoint(
        record["base_codepoint"],
        where=f"{record.get('base_codepoint')}.base_codepoint",
    )
    if ord(character) != codepoint:
        raise VerticalPipelineError(
            f"U+{codepoint:04X}: base character/codepoint mismatch"
        )
    metrics = nonhan.GlyphMetricsPolicy(
        horizontal_advance=nonhan.HorizontalAdvance(
            kind="fixed",
            value=nonhan.UPM,
        ),
        vertical_advance=nonhan.UPM,
        left_side_bearing=32,
        right_side_bearing=32,
        mark_class=None,
    )
    return nonhan.GlyphSpec(
        character=character,
        codepoint=codepoint,
        codepoint_label=f"U+{codepoint:04X}",
        unicode_name=str(record["unicode_name"]),
        profile_id="cjk-wide",
        transform_profile="fullwidth",
        metrics=metrics,
        source_record={"metrics": PREVIEW_METRICS},
    )


def load_source_descriptor(
    path: Path = DEFAULT_DESCRIPTOR,
    *,
    project_root: Path = ROOT,
) -> VerticalDescriptor:
    path = path.resolve()
    project_root = project_root.resolve()
    imagegen_root = project_root / "sources/imagegen"
    payload = _read_object(path)
    if set(payload) != TOP_LEVEL_FIELDS:
        _fail(path, f"top-level fields must be exactly {sorted(TOP_LEVEL_FIELDS)}")
    if payload["schema_version"] != 1 or payload["source_type"] != SOURCE_TYPE:
        _fail(path, "schema/source type changed")
    if payload["state"] != "generated-unreviewed":
        _fail(path, "state must be generated-unreviewed")
    if payload["generator"] != "built-in-image_gen":
        _fail(path, "generator must be built-in_image_gen")
    generator_call = payload["generator_call"]
    if (
        not isinstance(generator_call, str)
        or not generator_call
        or generator_call.startswith("<")
        or generator_call != generator_call.strip()
    ):
        _fail(path, "generator_call is not exact provenance")

    batch_id = payload["batch_id"]
    match = (
        SOURCE_BATCH_PATTERN.fullmatch(batch_id)
        if isinstance(batch_id, str)
        else None
    )
    if match is None:
        _fail(path, "invalid vertical source batch ID")
    base_batch_id = match.group(1)
    if path.name != f"{base_batch_id}.source.json":
        _fail(path, "descriptor filename/batch mismatch")

    repertoire_record = _object(payload["repertoire"], where=f"{path}: repertoire")
    if set(repertoire_record) != {"path", "sha256", "repertoire_id", "batch_id"}:
        _fail(path, "repertoire fields are not exact")
    if (
        repertoire_record["repertoire_id"] != REPERTOIRE_ID
        or repertoire_record["batch_id"] != base_batch_id
    ):
        _fail(path, "repertoire identity/batch changed")
    repertoire_path = _resolve_asset(
        path,
        repertoire_record["path"],
        expected="../repertoires/vertical-93.json",
        allowed_root=imagegen_root / "repertoires",
        where="repertoire",
    )
    repertoire_hash = repertoire_record["sha256"]
    if (
        not isinstance(repertoire_hash, str)
        or SHA256_PATTERN.fullmatch(repertoire_hash) is None
        or nonhan._sha256(repertoire_path) != repertoire_hash
    ):
        _fail(path, "repertoire hash mismatch")
    repertoire = load_frozen_repertoire(
        repertoire_path,
        project_root=project_root,
    )
    expected_records = _expected_batch(repertoire, base_batch_id)

    grid = _object(payload["grid"], where=f"{path}: grid")
    if set(grid) != {"rows", "columns", "alternates", "empty_grid_cells"}:
        _fail(path, "grid fields are not exact")
    if grid["rows"] != ROWS or grid["columns"] != COLUMNS:
        _fail(path, "grid must be exactly 4x4")
    empty = grid["empty_grid_cells"]
    if not isinstance(empty, int) or isinstance(empty, bool) or not 0 <= empty < CAPACITY:
        _fail(path, "empty_grid_cells is invalid")
    actual_records = grid["alternates"]
    if not isinstance(actual_records, list) or len(actual_records) + empty != CAPACITY:
        _fail(path, "alternate/empty cell cardinality mismatch")
    if len(actual_records) != len(expected_records):
        _fail(path, "source/repertoire alternate count mismatch")

    alternates: list[Mapping[str, Any]] = []
    glyphs: list[nonhan.GlyphSpec] = []
    seen_names: set[str] = set()
    for index, (actual_value, expected) in enumerate(
        zip(actual_records, expected_records, strict=True),
        start=1,
    ):
        actual = _object(actual_value, where=f"{path}: alternate {index}")
        if set(actual) != ALTERNATE_FIELDS:
            _fail(path, f"alternate {index} fields are not exact")
        reference = _object(
            actual["copybook_reference"],
            where=f"{path}: alternate {index} copybook reference",
        )
        if set(reference) != REFERENCE_FIELDS:
            _fail(path, f"alternate {index} reference fields are not exact")
        if reference["role"] != "identity-reference-only-no-outline-import":
            _fail(path, f"alternate {index} reference role changed")
        reference_hash = reference["font_sha256"]
        if (
            not isinstance(reference_hash, str)
            or SHA256_PATTERN.fullmatch(reference_hash) is None
        ):
            _fail(path, f"alternate {index} reference hash is invalid")
        without_reference = {
            key: value
            for key, value in actual.items()
            if key != "copybook_reference"
        }
        if without_reference != expected:
            _fail(path, f"alternate {index} drifted from frozen repertoire")
        glyph_name = actual["glyph_name"]
        if (
            not isinstance(glyph_name, str)
            or glyph_name != f"uni{int(actual['base_codepoint'][2:], 16):04X}.vert"
            or glyph_name in seen_names
        ):
            _fail(path, f"alternate {index} glyph name is invalid or duplicate")
        seen_names.add(glyph_name)
        alternates.append(actual)
        glyphs.append(_preview_spec(actual))

    expected_empty = CAPACITY - len(expected_records)
    if empty != expected_empty:
        _fail(path, "empty cell count drifted from repertoire")

    raster_path = _resolve_asset(
        path,
        payload["raster"],
        expected=f"../raster/{base_batch_id}.png",
        allowed_root=imagegen_root / "raster",
        where="raster",
    )
    raster_hash = payload["raster_sha256"]
    if (
        not isinstance(raster_hash, str)
        or SHA256_PATTERN.fullmatch(raster_hash) is None
        or nonhan._sha256(raster_path) != raster_hash
    ):
        _fail(path, "raster hash mismatch")
    prompt_path = _resolve_asset(
        path,
        payload["prompt"],
        expected=f"../prompts/{base_batch_id}.md",
        allowed_root=imagegen_root / "prompts",
        where="prompt",
    )
    copybook_path, copybook_hash = _hashed_asset(
        path,
        payload["copybook"],
        expected_path=f"../copybooks/{base_batch_id}.png",
        expected_role="identity-reference-only-no-outline-import",
        allowed_root=imagegen_root / "copybooks",
        where="copybook",
    )
    style_path, style_hash = _hashed_asset(
        path,
        payload["style_reference"],
        expected_path="../raster/common-0001.png",
        expected_role="style-only",
        allowed_root=imagegen_root / "raster",
        where="style reference",
    )
    review = payload["review"]
    if review != {
        "identity": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }:
        _fail(path, "source review must remain entirely pending")

    return VerticalDescriptor(
        path=path,
        project_root=project_root,
        batch_id=batch_id,
        base_batch_id=base_batch_id,
        raster_path=raster_path,
        raster_sha256=raster_hash,
        generator_call=generator_call,
        repertoire_path=repertoire_path,
        repertoire_sha256=repertoire_hash,
        prompt_path=prompt_path,
        prompt_sha256=nonhan._sha256(prompt_path),
        copybook_path=copybook_path,
        copybook_sha256=copybook_hash,
        style_reference_path=style_path,
        style_reference_sha256=style_hash,
        alternates=tuple(alternates),
        glyphs=tuple(glyphs),
        cell_slots=(*glyphs, *(None for _ in range(empty))),
        empty_grid_cells=empty,
        review={str(key): str(value) for key, value in review.items()},
        source_sha256=nonhan._sha256(path),
    )


def _build_fonts(
    glyphs: Sequence[nonhan.VectorizedGlyph],
    *,
    base_batch_id: str,
    directory: Path,
) -> tuple[Path, Path]:
    number = base_batch_id.removeprefix("vertical-")
    family = f"Clear Hand TC Vertical {number} Unreviewed"
    ps_name = f"ClearHandTC-Vertical{number}-Unreviewed"
    directory.mkdir(parents=True, exist_ok=True)
    ttf = directory / f"{ps_name}.ttf"
    otf = directory / f"{ps_name}.otf"
    nonhan._font_builder(glyphs, family=family, ps_name=ps_name).save(ttf)
    nonhan._font_builder(glyphs, family=family, ps_name=ps_name).save(otf)
    nonhan._validate_fonts((ttf, otf), glyphs)
    return ttf, otf


def _vertical_glyph_report(
    glyph: nonhan.VectorizedGlyph,
    alternate: Mapping[str, Any],
    *,
    coverage: Mapping[str, Mapping[str, int]],
    source_png: Path,
    svg: Path,
) -> dict[str, Any]:
    record = nonhan._glyph_report(
        glyph,
        coverage=coverage,
        source_png=source_png,
        svg=svg,
    )
    record["unencoded_glyph_name"] = alternate["glyph_name"]
    record["vertical_orientation"] = alternate["vertical_orientation"]
    record["tailoring"] = alternate["tailoring"]
    record["base_profile_id"] = alternate["base_profile_id"]
    record["base_metrics"] = alternate["base_metrics"]
    record["preview_metrics_only"] = record.pop("metric_policy")
    return record


def build_batch(
    descriptor_path: Path = DEFAULT_DESCRIPTOR,
    *,
    project_root: Path = ROOT,
    output_root: Path | None = None,
    potrace_executable: str | Path | None = None,
) -> Path:
    descriptor = load_source_descriptor(
        descriptor_path,
        project_root=project_root,
    )
    output_root = (
        descriptor.project_root / "build/imagegen"
        if output_root is None
        else output_root.resolve()
    )
    output_root.mkdir(parents=True, exist_ok=True)
    try:
        potrace, potrace_version = han_pipeline._resolve_potrace(
            potrace_executable
        )
    except han_pipeline.ImagegenPipelineError as exc:
        raise VerticalPipelineError(str(exc)) from exc
    try:
        source_image = Image.open(descriptor.raster_path)
        source_image.load()
    except (OSError, ValueError) as exc:
        raise VerticalPipelineError(
            f"{descriptor.raster_path}: cannot decode PNG: {exc}"
        ) from exc
    if source_image.format != "PNG":
        raise VerticalPipelineError("source raster must decode as PNG")
    try:
        detection = han_pipeline.detect_grid(source_image)
        cells = nonhan.segment_cells(
            source_image,
            detection,
            descriptor.cell_slots,
        )
    except (han_pipeline.ImagegenPipelineError, nonhan.NonHanPipelineError) as exc:
        raise VerticalPipelineError(str(exc)) from exc

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{descriptor.batch_id}-",
            dir=output_root,
        )
    )
    final_directory = output_root / descriptor.batch_id
    try:
        png_directory = stage / "png"
        svg_directory = stage / "svg"
        trace_directory = stage / ".trace"
        glyph_report_directory = stage / "glyph-report"
        font_directory = stage / "font"
        proof_directory = stage / "proof"
        for directory in (
            png_directory,
            svg_directory,
            trace_directory,
            glyph_report_directory,
            proof_directory,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        vectorized: list[nonhan.VectorizedGlyph] = []
        paths_by_codepoint: dict[int, tuple[Path, Path]] = {}
        for cell, alternate in zip(
            cells,
            descriptor.alternates,
            strict=True,
        ):
            stem = f"u{cell.spec.codepoint:04x}-vert"
            source_png = png_directory / f"{stem}-source.png"
            trace_bitmap = trace_directory / f"{stem}.pgm"
            svg_path = svg_directory / f"{stem}.svg"
            cell.cleaned.save(source_png, optimize=False)
            bridge = han_pipeline.SegmentedCell(
                character=cell.spec.character,
                codepoint=cell.spec.codepoint,
                row=cell.row,
                column=cell.column,
                source_box=cell.source_box,
                source_ink_bbox=cell.source_ink_bbox,
                core_component_count=cell.core_component_count,
                core_pixel_count=cell.core_pixel_count,
                cleaned=cell.cleaned,
            )
            try:
                han_pipeline._trace_cell(
                    bridge,
                    potrace=potrace,
                    bitmap_path=trace_bitmap,
                    svg_path=svg_path,
                )
                glyph = nonhan._vectorize(cell, svg_path)
            except (
                han_pipeline.ImagegenPipelineError,
                nonhan.NonHanPipelineError,
            ) as exc:
                raise VerticalPipelineError(str(exc)) from exc
            glyph.name = str(alternate["glyph_name"])
            vectorized.append(glyph)
            paths_by_codepoint[cell.spec.codepoint] = (
                source_png,
                svg_path,
            )
        try:
            nonhan._resolve_advances(vectorized)
            ttf_path, otf_path = _build_fonts(
                vectorized,
                base_batch_id=descriptor.base_batch_id,
                directory=font_directory,
            )
            proof_records, coverage = nonhan._write_size_proofs(
                ttf_path,
                vectorized,
                directory=proof_directory,
                coverage_divisor_override=VERTICAL_PROOF_COVERAGE_DIVISOR,
            )
        except nonhan.NonHanPipelineError as exc:
            raise VerticalPipelineError(str(exc)) from exc

        source_proof = nonhan._write_source_proof(
            cells,
            output=proof_directory / "segmented-source.png",
        )
        edge_proof = nonhan._write_edge_proof(
            cells,
            font_path=ttf_path,
            output=proof_directory / "edge-connect.png",
        )
        glyph_records: list[dict[str, Any]] = []
        for glyph, alternate in zip(
            vectorized,
            descriptor.alternates,
            strict=True,
        ):
            source_png, svg_path = paths_by_codepoint[glyph.spec.codepoint]
            record = _vertical_glyph_report(
                glyph,
                alternate,
                coverage=coverage,
                source_png=source_png,
                svg=svg_path,
            )
            glyph_records.append(record)
            (glyph_report_directory / f"u{glyph.spec.codepoint:04x}-vert.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
        shutil.rmtree(trace_directory)

        report: dict[str, Any] = {
            "schema_version": 1,
            "pipeline": PIPELINE_ID,
            "approval_state": "unreviewed",
            "batch_id": descriptor.batch_id,
            "source_type": SOURCE_TYPE,
            "source_descriptor": str(
                descriptor.path.relative_to(descriptor.project_root)
            ),
            "source_descriptor_sha256": descriptor.source_sha256,
            "source_generator": "built-in-image_gen",
            "source_generator_call": descriptor.generator_call,
            "source_repertoire": str(
                descriptor.repertoire_path.relative_to(descriptor.project_root)
            ),
            "source_repertoire_sha256": descriptor.repertoire_sha256,
            "source_prompt": str(
                descriptor.prompt_path.relative_to(descriptor.project_root)
            ),
            "source_prompt_sha256": descriptor.prompt_sha256,
            "source_copybook": str(
                descriptor.copybook_path.relative_to(descriptor.project_root)
            ),
            "source_copybook_sha256": descriptor.copybook_sha256,
            "source_style_reference": str(
                descriptor.style_reference_path.relative_to(
                    descriptor.project_root
                )
            ),
            "source_style_reference_sha256": (
                descriptor.style_reference_sha256
            ),
            "source_raster": str(
                descriptor.raster_path.relative_to(descriptor.project_root)
            ),
            "source_raster_sha256": descriptor.raster_sha256,
            "source_state": "generated-unreviewed",
            "source_review": dict(descriptor.review),
            "base_codepoints": [
                glyph.spec.codepoint_label for glyph in vectorized
            ],
            "unencoded_glyph_names": [
                glyph.name for glyph in vectorized
            ],
            "grid": {
                "rows": ROWS,
                "columns": COLUMNS,
                "empty_grid_cells": descriptor.empty_grid_cells,
                "cell_slots": [
                    *[glyph.spec.codepoint_label for glyph in vectorized],
                    *[None for _ in range(descriptor.empty_grid_cells)],
                ],
                "x_rule_centers": list(detection.x.centers),
                "y_rule_centers": list(detection.y.centers),
                "x_rule_spans": [list(value) for value in detection.x.groups],
                "y_rule_spans": [list(value) for value in detection.y.groups],
                "synthesized_coordinates": False,
            },
            "vectorization": {
                "tool": potrace_version,
                "outline_format": "TrueType quadratic glyf",
                "cu2qu_max_error": han_pipeline.CU2QU_MAX_ERROR,
                "grid_rules_removed_by_detected_rule_spans": True,
                "grid_rule_interior_padding_px": (
                    nonhan.GRID_RULE_INTERIOR_PADDING
                ),
                "proof_coverage_divisor": (
                    VERTICAL_PROOF_COVERAGE_DIVISOR
                ),
                "minimum_proof_coverage_pixels": (
                    nonhan.MINIMUM_PROOF_COVERAGE_PIXELS
                ),
                "preview_transform": "fullwidth",
                "release_metrics": (
                    "base-advances-with-approved-preview-placement"
                ),
            },
            "font": {
                "ttf": f"font/{ttf_path.name}",
                "ttf_sha256": nonhan._sha256(ttf_path),
                "otf": f"font/{otf_path.name}",
                "otf_sha256": nonhan._sha256(otf_path),
                "temporary_preview_cmap_count": len(vectorized),
                "glyph_count": len(vectorized) + 1,
                "release_alternates_are_unencoded": True,
            },
            "proofs": [
                *proof_records,
                {
                    "kind": "segmented-source",
                    "path": f"proof/{source_proof.name}",
                    "sha256": nonhan._sha256(source_proof),
                },
                {
                    "kind": "edge-connect",
                    "path": f"proof/{edge_proof.name}",
                    "sha256": nonhan._sha256(edge_proof),
                },
            ],
            "glyphs": glyph_records,
        }
        report["artifact_sha256"] = nonhan._artifact_hashes(stage)
        report_path = stage / "report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        nonhan._validate_fonts((ttf_path, otf_path), vectorized)
        if report["artifact_sha256"] != nonhan._artifact_hashes(stage):
            raise VerticalPipelineError(
                "artifact inventory changed after report materialization"
            )
        nonhan._install_build_directory(stage, final_directory)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return final_directory


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor", type=Path, default=DEFAULT_DESCRIPTOR)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--potrace", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = build_batch(
        args.descriptor,
        project_root=args.project_root,
        output_root=args.output_root,
        potrace_executable=args.potrace,
    )
    print(output)
    print(output / "report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
