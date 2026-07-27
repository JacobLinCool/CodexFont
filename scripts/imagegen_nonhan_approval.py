#!/usr/bin/env python3
"""Validate hash-pinned approvals for the non-Han imagegen repertoire.

The frozen repertoire has exactly 206 batches with two deliberately disjoint
admission paths:

* ``nonhan-0001`` through ``nonhan-0205`` are visible raster-outline batches.
  Their approvals pin the schema-v2 source descriptor, raster, identity
  copybook, exact prompt, style reference, vector report, every vector
  artifact, and an explicit per-glyph visual review.
* ``nonhan-0206`` is semantic-only.  It has no raster, copybook, prompt, style
  reference, or vector report.  Its approval pins one semantic evidence
  manifest, an all-empty quadratic font, a blank five-size render proof, and
  an explicit per-glyph review.

This module is a fail-closed admission boundary.  It never creates an approval,
never infers a human decision, never imports another font as a glyph source,
and never reads the authored-source tree.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Mapping, NoReturn, Sequence

import freetype
from fontTools.ttLib import TTFont
from PIL import Image

from scripts import imagegen_font_pipeline as han_pipeline


ROOT = Path(__file__).resolve().parents[1]

APPROVAL_SCHEMA_VERSION = 1
APPROVAL_RECORD_TYPE = "imagegen-nonhan-batch-approval"
VISUAL_REVIEW_RECORD_TYPE = "imagegen-nonhan-glyph-review"
SEMANTIC_RECORD_TYPE = "imagegen-nonhan-semantic-evidence"
VISIBLE_PIPELINE = "imagegen-raster-potrace-quadratic-nonhan-v3"
VISIBLE_SOURCE_TYPE = "imagegen-nonhan-grid-v2"

REPERTOIRE_RELATIVE_PATH = PurePosixPath(
    "sources/imagegen/repertoires/nonhan-3060.json"
)
REPERTOIRE_ID = "clear-hand-tc-nonhan-3060-v1"
REPERTOIRE_SHA256 = (
    "42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4"
)
CANONICAL_SEQUENCE_SHA256 = (
    "906bd2973d9ce2361ac7a2d9bc21078a0a586495a90960b6fbf6d65fa658b135"
)
AUTHORING_SEQUENCE_SHA256 = (
    "c883b20205f9d5cc0d1e873d4470af07264996877eecfd0d464f1da6fd3b1d7b"
)
VISIBLE_AUTHORING_SEQUENCE_SHA256 = (
    "95205bb278895114b496ece6b72aff2d3ee71d54d5fc1cd5caccd0766b1b6638"
)
SEQUENCE_HASH_SERIALIZATION = "ascii-uppercase-codepoint-lines-v1"
TOTAL_GLYPHS = 3060
VISIBLE_GLYPHS = 3043
SEMANTIC_GLYPHS = 17
TOTAL_BATCHES = 206
VISIBLE_BATCHES = 205
SEMANTIC_BATCH_ID = "nonhan-0206"
GRID_CAPACITY = 16
UPM = 1024
VERTICAL_ORIGIN_Y = 880
SMALL_SIZE_PIXELS = (12, 16, 20, 32, 56)
VISUAL_POLARITIES = ("black-on-white", "white-on-black")
GRID_RULE_INTERIOR_PADDING = 2
CU2QU_MAX_ERROR = 2.0
MINIMUM_PROOF_COVERAGE_PIXELS = 2
DEFAULT_PROOF_COVERAGE_DIVISOR = 6
MARK_PROOF_COVERAGE_DIVISOR = 10
SEGMENTATION_INK_FRACTION_LIMITS: Mapping[str, float] = {
    "generic": 0.30,
    "dense-solid": 0.34,
    "edge": 1.0,
}
DENSE_SOLID_GLYPHS: Mapping[int, str] = {
    0x25FC: "BLACK MEDIUM SQUARE",
    0x2617: "BLACK SHOGI PIECE",
}

VISIBLE_REVIEW_CHECKS = (
    "glyph-identity",
    "simple-nonempty-quadratic-outline",
    "exact-horizontal-and-vertical-metrics",
    "profile-invariants",
    "zero-micro-edges-and-thorns",
    "five-size-legibility",
)
SEMANTIC_REVIEW_CHECKS = (
    "empty-quadratic-glyph",
    "exact-semantic-metrics-and-relations",
    "blank-five-size-render",
)
REVIEW_CONFIRMATION = (
    "I_REVIEWED_EVERY_NONHAN_GLYPH_AT_12_16_20_32_56_PX_IN_BOTH_POLARITIES"
)
SEMANTIC_REVIEW_CONFIRMATION = (
    "I_REVIEWED_ALL_17_SEMANTIC_EMPTY_GLYPHS_AND_CONFIRMED_ZERO_INK_AT_"
    "12_16_20_32_56_PX"
)
AUTHORIZATION_CONFIRMATION = (
    "I_AUTHORIZE_THIS_HASH_PINNED_NONHAN_BATCH_FOR_THE_RELEASE_FONT"
)

PROFILE_TRANSFORMS: Mapping[str, str] = {
    "fullwidth": "fullwidth",
    "halfwidth": "halfwidth",
    "proportional": "proportional",
    "tabular-digit": "proportional",
    "nonspacing-mark": "mark",
    "box-drawing": "edge",
    "block-element": "edge",
    "cjk-wide": "fullwidth",
}
PROFILE_IDS = frozenset(PROFILE_TRANSFORMS)

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
CODEPOINT_PATTERN = re.compile(r"U\+[0-9A-F]{4,6}")
BATCH_PATTERN = re.compile(r"nonhan-(?P<number>[0-9]{4})")
RFC3339_UTC_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)

REPERTOIRE_TOP_KEYS = frozenset(
    {
        "schema_version",
        "repertoire_id",
        "normalization",
        "counts",
        "ordering",
        "profile_ids",
        "provenance",
        "sequence_hashes",
        "glyphs",
        "batches",
    }
)
GLYPH_KEYS = frozenset(
    {
        "canonical_rank",
        "authoring_rank",
        "character",
        "codepoint",
        "name",
        "gc",
        "outline_required",
        "profile_id",
        "metrics",
    }
)
DESCRIPTOR_TOP_KEYS = frozenset(
    {
        "schema_version",
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
)
REPORT_TOP_KEYS = frozenset(
    {
        "schema_version",
        "pipeline",
        "approval_state",
        "batch_id",
        "source_type",
        "source_descriptor",
        "source_descriptor_sha256",
        "source_generator",
        "source_generator_call",
        "source_repertoire",
        "source_repertoire_sha256",
        "source_prompt",
        "source_prompt_sha256",
        "source_copybook",
        "source_copybook_sha256",
        "source_style_reference",
        "source_style_reference_sha256",
        "source_raster",
        "source_raster_sha256",
        "source_state",
        "source_review",
        "characters",
        "codepoints",
        "grid",
        "metric_contract",
        "vectorization",
        "font",
        "proofs",
        "glyphs",
        "artifact_sha256",
    }
)
REPORT_GLYPH_KEYS = frozenset(
    {
        "character",
        "codepoint",
        "unicode_name",
        "glyph_name",
        "profile_id",
        "transform_profile",
        "segmentation_profile",
        "metric_policy",
        "row",
        "column",
        "source_box",
        "source_ink_bbox_normalized",
        "source_ink_fraction",
        "source_component_count",
        "source_core_pixel_count",
        "edge_contacts",
        "edge_contact_pixels",
        "vector_edge_contacts",
        "pre_metric_bounds",
        "final_bounds",
        "metrics",
        "mark_class",
        "mark_placement",
        "anchors_candidate",
        "contour_count",
        "point_count",
        "outer_contour_count",
        "counter_count",
        "minimum_control_edge",
        "micro_edge_count",
        "acute_micro_turn_count",
        "quantization_duplicate_points_removed",
        "maximum_quantization_collapse",
        "micro_thorn_points_removed",
        "maximum_micro_thorn_displacement",
        "coincident_flank_control_points_removed",
        "coverage_pixels",
        "source_png",
        "source_png_sha256",
        "svg",
        "svg_sha256",
    }
)


class NonHanApprovalError(RuntimeError):
    """Approval evidence is incomplete, ambiguous, stale, or invalid."""


@dataclass(frozen=True)
class RepertoireGlyph:
    """One exact scalar record from the frozen repertoire."""

    character: str
    codepoint: int
    codepoint_label: str
    canonical_rank: int
    authoring_rank: int
    name: str
    general_category: str
    outline_required: bool
    profile_id: str
    metrics: Mapping[str, Any]
    record: Mapping[str, Any]


@dataclass(frozen=True)
class RepertoireBatch:
    """One exact raster-outline or semantic-empty batch."""

    batch_id: str
    number: int
    batch_kind: str
    design_group: str
    start_authoring_rank: int
    end_authoring_rank: int
    glyphs: tuple[RepertoireGlyph, ...]
    empty_grid_cells: int | None

    @property
    def descriptor_batch_id(self) -> str:
        return f"imagegen-{self.batch_id}"


@dataclass(frozen=True)
class Repertoire:
    """Strictly validated 3,060-scalar, 206-batch repertoire."""

    path: Path
    sha256: str
    repertoire_id: str
    sequence_hashes: Mapping[str, str]
    glyphs: tuple[RepertoireGlyph, ...]
    batches: tuple[RepertoireBatch, ...]

    @property
    def glyph_by_codepoint(self) -> Mapping[int, RepertoireGlyph]:
        return {glyph.codepoint: glyph for glyph in self.glyphs}


@dataclass(frozen=True)
class VisibleEvidence:
    """Validated bytes and report data for one raster-outline batch."""

    descriptor_path: Path
    descriptor_sha256: str
    raster_path: Path
    raster_sha256: str
    copybook_path: Path
    copybook_sha256: str
    prompt_path: Path
    prompt_sha256: str
    style_reference_path: Path
    style_reference_sha256: str
    report_path: Path
    report_sha256: str
    report: Mapping[str, Any]
    proof_references: tuple[Mapping[str, str], ...]


@dataclass(frozen=True)
class SemanticEvidence:
    """Validated empty-glyph font and blank render evidence."""

    manifest_path: Path
    manifest_sha256: str
    font_path: Path
    font_sha256: str
    blank_proof_path: Path
    blank_proof_sha256: str
    manifest: Mapping[str, Any]
    proof_references: tuple[Mapping[str, str], ...]


@dataclass(frozen=True)
class ValidatedApproval:
    """One fully admitted non-Han batch."""

    approval_path: Path
    approval_sha256: str
    repertoire: Repertoire
    batch: RepertoireBatch
    reviewer_name: str
    reviewed_at: str
    approver_name: str
    approved_at: str
    visible_evidence: VisibleEvidence | None
    semantic_evidence: SemanticEvidence | None


def sha256_path(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one regular file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fail(where: str | Path, message: str) -> NoReturn:
    raise NonHanApprovalError(f"{where}: {message}")


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NonHanApprovalError(
            f"{path}: cannot read {label} JSON: {exc}"
        ) from exc
    if not isinstance(value, dict):
        _fail(path, f"{label} must be a JSON object")
    return value


def _exact_keys(
    value: Any,
    expected: Iterable[str],
    *,
    where: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(where, "must be an object")
    expected_set = set(expected)
    actual_set = set(value)
    if actual_set != expected_set:
        _fail(
            where,
            "wrong keys; "
            f"missing={sorted(expected_set - actual_set)}, "
            f"extra={sorted(actual_set - expected_set)}",
        )
    return value


def _nonempty_string(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        _fail(where, "must be non-empty without surrounding whitespace")
    return value


def _lower_sha256(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        _fail(where, "must be a lowercase 64-character SHA-256")
    return value


def _integer(
    value: Any,
    *,
    where: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(where, "must be an integer")
    if minimum is not None and value < minimum:
        _fail(where, f"must be at least {minimum}")
    if maximum is not None and value > maximum:
        _fail(where, f"must be at most {maximum}")
    return value


def _number(value: Any, *, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(where, "must be numeric")
    result = float(value)
    if result != result or result in {float("inf"), float("-inf")}:
        _fail(where, "must be finite")
    return result


def _one_scalar(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or len(value) != 1:
        _fail(where, "must contain exactly one Unicode scalar")
    codepoint = ord(value)
    if 0xD800 <= codepoint <= 0xDFFF:
        _fail(where, "surrogate code points are forbidden")
    return value


def _codepoint(value: Any, *, where: str) -> tuple[int, str]:
    if not isinstance(value, str) or CODEPOINT_PATTERN.fullmatch(value) is None:
        _fail(where, "must use uppercase U+XXXX notation")
    codepoint = int(value[2:], 16)
    if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
        _fail(where, "must identify a Unicode scalar")
    if value != f"U+{codepoint:04X}":
        _fail(where, "must use the shortest canonical uppercase form")
    return codepoint, value


def _canonical_batch_id(value: Any, *, where: str) -> tuple[str, int]:
    if not isinstance(value, str):
        _fail(where, "must be a string")
    match = BATCH_PATTERN.fullmatch(value)
    if match is None:
        _fail(where, "must have canonical form nonhan-NNNN")
    number = int(match.group("number"))
    if not 1 <= number <= TOTAL_BATCHES:
        _fail(where, "batch number must be in 0001..0206")
    return value, number


def _require_rfc3339_utc(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or RFC3339_UTC_PATTERN.fullmatch(value) is None:
        _fail(where, "must be an RFC3339 UTC timestamp without fractions")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise NonHanApprovalError(f"{where}: invalid UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        _fail(where, "timestamp is not canonical")
    return value


def _relative_posix_path(value: Any, *, where: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        _fail(where, "must be a non-empty POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        _fail(where, "must be a normalized project-relative path")
    return path


def _resolve_regular_file(
    project_root: Path,
    relative: PurePosixPath,
    *,
    where: str,
) -> Path:
    root = project_root.resolve()
    path = root.joinpath(*relative.parts)
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        _fail(where, "path escapes project root")
    if path.is_symlink() or not resolved.is_file():
        _fail(where, "must resolve to a regular non-symlink file")
    return resolved


def _reference(
    value: Any,
    *,
    where: str,
    project_root: Path,
    expected_path: PurePosixPath,
) -> tuple[Path, str]:
    reference = _exact_keys(value, {"path", "sha256"}, where=where)
    relative = _relative_posix_path(reference["path"], where=f"{where}.path")
    if relative != expected_path:
        _fail(where, f"path must be {expected_path.as_posix()!r}")
    expected_hash = _lower_sha256(
        reference["sha256"], where=f"{where}.sha256"
    )
    path = _resolve_regular_file(
        project_root, relative, where=f"{where}.path"
    )
    actual_hash = sha256_path(path)
    if actual_hash != expected_hash:
        _fail(where, f"hash mismatch: expected {expected_hash}, got {actual_hash}")
    return path, expected_hash


def _sequence_sha256(codepoints: Iterable[int]) -> str:
    encoded = "".join(f"U+{codepoint:04X}\n" for codepoint in codepoints)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _validate_metrics(value: Any, *, where: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(where, "must be an object")
    required = {"horizontal_advance", "vertical_advance", "side_bearings"}
    allowed = required | {"mark_class"}
    if not required <= set(value) or not set(value) <= allowed:
        _fail(
            where,
            "requires horizontal_advance, vertical_advance, side_bearings; "
            "only mark_class is optional",
        )
    horizontal = value["horizontal_advance"]
    if not isinstance(horizontal, dict):
        _fail(f"{where}.horizontal_advance", "must be an object")
    kind = horizontal.get("kind")
    if kind == "fixed":
        _exact_keys(
            horizontal,
            {"kind", "value"},
            where=f"{where}.horizontal_advance",
        )
        _integer(
            horizontal["value"],
            where=f"{where}.horizontal_advance.value",
            minimum=0,
            maximum=4096,
        )
    elif kind == "reference":
        _exact_keys(
            horizontal,
            {"kind", "codepoint"},
            where=f"{where}.horizontal_advance",
        )
        _codepoint(
            horizontal["codepoint"],
            where=f"{where}.horizontal_advance.codepoint",
        )
    elif kind == "source-proportional":
        _exact_keys(
            horizontal, {"kind"}, where=f"{where}.horizontal_advance"
        )
    else:
        _fail(
            f"{where}.horizontal_advance",
            "kind must be fixed, reference, or source-proportional",
        )
    vertical = _exact_keys(
        value["vertical_advance"],
        {"kind", "value"},
        where=f"{where}.vertical_advance",
    )
    if vertical["kind"] != "fixed":
        _fail(f"{where}.vertical_advance.kind", "must be fixed")
    _integer(
        vertical["value"],
        where=f"{where}.vertical_advance.value",
        minimum=0,
        maximum=4096,
    )
    bearings = _exact_keys(
        value["side_bearings"],
        {"left", "right"},
        where=f"{where}.side_bearings",
    )
    _integer(bearings["left"], where=f"{where}.side_bearings.left")
    _integer(bearings["right"], where=f"{where}.side_bearings.right")
    if "mark_class" in value:
        mark_class = value["mark_class"]
        if (
            not isinstance(mark_class, str)
            or re.fullmatch(r"ccc-(?:0|[1-9][0-9]{0,2})", mark_class) is None
        ):
            _fail(f"{where}.mark_class", "must have canonical form ccc-N")
    return value


def _parse_repertoire_glyph(
    value: Any,
    *,
    index: int,
) -> RepertoireGlyph:
    where = f"repertoire.glyphs[{index}]"
    record = _exact_keys(value, GLYPH_KEYS, where=where)
    character = _one_scalar(record["character"], where=f"{where}.character")
    codepoint, label = _codepoint(
        record["codepoint"], where=f"{where}.codepoint"
    )
    if ord(character) != codepoint:
        _fail(where, "character/codepoint mismatch")
    canonical_rank = _integer(
        record["canonical_rank"],
        where=f"{where}.canonical_rank",
        minimum=1,
        maximum=TOTAL_GLYPHS,
    )
    authoring_rank = _integer(
        record["authoring_rank"],
        where=f"{where}.authoring_rank",
        minimum=1,
        maximum=TOTAL_GLYPHS,
    )
    name = _nonempty_string(record["name"], where=f"{where}.name")
    category = _nonempty_string(record["gc"], where=f"{where}.gc")
    if len(category) != 2:
        _fail(f"{where}.gc", "must be a two-letter general category")
    if not isinstance(record["outline_required"], bool):
        _fail(f"{where}.outline_required", "must be boolean")
    profile_id = record["profile_id"]
    if not isinstance(profile_id, str) or profile_id not in PROFILE_IDS:
        _fail(f"{where}.profile_id", "is not one of the eight frozen profiles")
    metrics = _validate_metrics(record["metrics"], where=f"{where}.metrics")
    return RepertoireGlyph(
        character=character,
        codepoint=codepoint,
        codepoint_label=label,
        canonical_rank=canonical_rank,
        authoring_rank=authoring_rank,
        name=name,
        general_category=category,
        outline_required=record["outline_required"],
        profile_id=profile_id,
        metrics=metrics,
        record=dict(record),
    )


def load_frozen_repertoire(project_root: Path = ROOT) -> Repertoire:
    """Load and fully validate the single canonical 206-batch repertoire."""

    project_root = project_root.resolve()
    path = _resolve_regular_file(
        project_root,
        REPERTOIRE_RELATIVE_PATH,
        where="frozen repertoire",
    )
    digest = sha256_path(path)
    if digest != REPERTOIRE_SHA256:
        _fail(path, f"frozen hash mismatch: expected {REPERTOIRE_SHA256}, got {digest}")
    payload = _read_json_object(path, label="repertoire")
    top = _exact_keys(payload, REPERTOIRE_TOP_KEYS, where=str(path))
    if top["schema_version"] != 1:
        _fail(path, "schema_version must be 1")
    if top["repertoire_id"] != REPERTOIRE_ID:
        _fail(path, f"repertoire_id must be {REPERTOIRE_ID!r}")
    if top["normalization"] != "none":
        _fail(path, "normalization must remain 'none'")
    if top["counts"] != {
        "total": TOTAL_GLYPHS,
        "outline_required": VISIBLE_GLYPHS,
        "semantic_empty": SEMANTIC_GLYPHS,
        "visible_nonspacing_marks": 112,
        "visible_raster_batches": VISIBLE_BATCHES,
        "total_batches": TOTAL_BATCHES,
    }:
        _fail(path, "frozen counts contract changed")
    if (
        not isinstance(top["profile_ids"], list)
        or len(top["profile_ids"]) != len(PROFILE_IDS)
        or set(top["profile_ids"]) != PROFILE_IDS
    ):
        _fail(path, "profile_ids must be the exact eight-profile set")
    sequence_hashes = _exact_keys(
        top["sequence_hashes"],
        {"serialization", "canonical", "authoring", "visible_authoring"},
        where=f"{path}: sequence_hashes",
    )
    if sequence_hashes != {
        "serialization": SEQUENCE_HASH_SERIALIZATION,
        "canonical": CANONICAL_SEQUENCE_SHA256,
        "authoring": AUTHORING_SEQUENCE_SHA256,
        "visible_authoring": VISIBLE_AUTHORING_SEQUENCE_SHA256,
    }:
        _fail(path, "frozen sequence hashes changed")

    raw_glyphs = top["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != TOTAL_GLYPHS:
        _fail(path, f"glyphs must contain exactly {TOTAL_GLYPHS} records")
    glyphs = tuple(
        _parse_repertoire_glyph(value, index=index)
        for index, value in enumerate(raw_glyphs)
    )
    if [glyph.codepoint for glyph in glyphs] != sorted(
        glyph.codepoint for glyph in glyphs
    ):
        _fail(path, "canonical glyph order must be codepoint ascending")
    if [glyph.canonical_rank for glyph in glyphs] != list(
        range(1, TOTAL_GLYPHS + 1)
    ):
        _fail(path, "canonical ranks must be the exact contiguous sequence")
    if sorted(glyph.authoring_rank for glyph in glyphs) != list(
        range(1, TOTAL_GLYPHS + 1)
    ):
        _fail(path, "authoring ranks must be unique and contiguous")
    if len({glyph.codepoint for glyph in glyphs}) != TOTAL_GLYPHS:
        _fail(path, "glyph codepoints must be unique")
    if sum(glyph.outline_required for glyph in glyphs) != VISIBLE_GLYPHS:
        _fail(path, "outline_required count changed")
    if _sequence_sha256(glyph.codepoint for glyph in glyphs) != (
        CANONICAL_SEQUENCE_SHA256
    ):
        _fail(path, "canonical sequence hash does not match glyph records")

    glyph_index = {glyph.codepoint_label: glyph for glyph in glyphs}
    raw_batches = top["batches"]
    if not isinstance(raw_batches, list) or len(raw_batches) != TOTAL_BATCHES:
        _fail(path, f"batches must contain exactly {TOTAL_BATCHES} records")
    batches: list[RepertoireBatch] = []
    flattened_labels: list[str] = []
    for offset, raw_batch in enumerate(raw_batches, start=1):
        where = f"{path}: batches[{offset - 1}]"
        kind = (
            raw_batch.get("batch_kind")
            if isinstance(raw_batch, dict)
            else None
        )
        expected_keys = {
            "batch_id",
            "batch_kind",
            "design_group",
            "start_authoring_rank",
            "end_authoring_rank",
            "glyph_codepoints",
        }
        if kind == "raster-outline":
            expected_keys.add("empty_grid_cells")
        batch_record = _exact_keys(raw_batch, expected_keys, where=where)
        batch_id, number = _canonical_batch_id(
            batch_record["batch_id"], where=f"{where}.batch_id"
        )
        if number != offset:
            _fail(where, "batch IDs must be the exact contiguous 0001..0206 sequence")
        expected_kind = (
            "raster-outline" if number <= VISIBLE_BATCHES else "semantic-empty"
        )
        if kind != expected_kind:
            _fail(where, f"batch_kind must be {expected_kind!r}")
        design_group = _nonempty_string(
            batch_record["design_group"], where=f"{where}.design_group"
        )
        start_rank = _integer(
            batch_record["start_authoring_rank"],
            where=f"{where}.start_authoring_rank",
            minimum=1,
            maximum=TOTAL_GLYPHS,
        )
        end_rank = _integer(
            batch_record["end_authoring_rank"],
            where=f"{where}.end_authoring_rank",
            minimum=start_rank,
            maximum=TOTAL_GLYPHS,
        )
        raw_labels = batch_record["glyph_codepoints"]
        if not isinstance(raw_labels, list) or not raw_labels:
            _fail(f"{where}.glyph_codepoints", "must be a non-empty list")
        labels: list[str] = []
        for label_index, raw_label in enumerate(raw_labels):
            _codepoint(
                raw_label, where=f"{where}.glyph_codepoints[{label_index}]"
            )
            if raw_label not in glyph_index:
                _fail(where, f"unknown repertoire codepoint {raw_label}")
            labels.append(raw_label)
        if len(set(labels)) != len(labels):
            _fail(where, "batch contains duplicate codepoints")
        batch_glyphs = tuple(glyph_index[label] for label in labels)
        expected_ranks = list(range(start_rank, end_rank + 1))
        if [glyph.authoring_rank for glyph in batch_glyphs] != expected_ranks:
            _fail(where, "glyph order does not match authoring rank interval")
        empty_cells: int | None
        if kind == "raster-outline":
            empty_cells = _integer(
                batch_record["empty_grid_cells"],
                where=f"{where}.empty_grid_cells",
                minimum=0,
                maximum=GRID_CAPACITY - 1,
            )
            if len(batch_glyphs) + empty_cells != GRID_CAPACITY:
                _fail(where, "visible glyphs plus empty cells must total 16")
            if any(not glyph.outline_required for glyph in batch_glyphs):
                _fail(where, "visible batch contains a semantic-empty glyph")
        else:
            empty_cells = None
            if batch_id != SEMANTIC_BATCH_ID or len(batch_glyphs) != SEMANTIC_GLYPHS:
                _fail(where, "semantic batch identity/count changed")
            if any(glyph.outline_required for glyph in batch_glyphs):
                _fail(where, "semantic batch contains an outline-required glyph")
        flattened_labels.extend(labels)
        batches.append(
            RepertoireBatch(
                batch_id=batch_id,
                number=number,
                batch_kind=kind,
                design_group=design_group,
                start_authoring_rank=start_rank,
                end_authoring_rank=end_rank,
                glyphs=batch_glyphs,
                empty_grid_cells=empty_cells,
            )
        )
    authoring_glyphs = sorted(glyphs, key=lambda glyph: glyph.authoring_rank)
    if flattened_labels != [glyph.codepoint_label for glyph in authoring_glyphs]:
        _fail(path, "batch plan is not the exact authoring-order partition")
    if _sequence_sha256(glyph.codepoint for glyph in authoring_glyphs) != (
        AUTHORING_SEQUENCE_SHA256
    ):
        _fail(path, "authoring sequence hash does not match batch records")
    visible_authoring = [
        glyph.codepoint for glyph in authoring_glyphs if glyph.outline_required
    ]
    if _sequence_sha256(visible_authoring) != VISIBLE_AUTHORING_SEQUENCE_SHA256:
        _fail(path, "visible authoring sequence hash does not match batch records")
    return Repertoire(
        path=path,
        sha256=digest,
        repertoire_id=REPERTOIRE_ID,
        sequence_hashes=dict(sequence_hashes),
        glyphs=glyphs,
        batches=tuple(batches),
    )


def batch_from_repertoire(
    repertoire: Repertoire, batch_id: str
) -> RepertoireBatch:
    canonical, number = _canonical_batch_id(batch_id, where="batch_id")
    batch = repertoire.batches[number - 1]
    if batch.batch_id != canonical:
        _fail(batch_id, "does not match frozen repertoire")
    return batch


def _approval_repertoire_payload(
    repertoire: Repertoire,
    batch: RepertoireBatch,
) -> dict[str, Any]:
    return {
        "path": REPERTOIRE_RELATIVE_PATH.as_posix(),
        "sha256": repertoire.sha256,
        "repertoire_id": repertoire.repertoire_id,
        "batch_id": batch.batch_id,
        "start_authoring_rank": batch.start_authoring_rank,
        "end_authoring_rank": batch.end_authoring_rank,
        "glyph_codepoints": [
            glyph.codepoint_label for glyph in batch.glyphs
        ],
    }


def _validate_approval_repertoire(
    value: Any,
    *,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    where: str,
) -> None:
    expected = _approval_repertoire_payload(repertoire, batch)
    _exact_keys(value, expected, where=where)
    if value != expected:
        _fail(where, "does not exactly pin the frozen batch")


def _assert_no_authored_reference(value: Any, *, where: str) -> None:
    """Reject descriptor text that attempts to route evidence through authored."""

    if isinstance(value, str):
        normalized = value.replace("\\", "/").lower()
        if "sources/authored" in normalized:
            _fail(where, "authored-source references are forbidden")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_authored_reference(item, where=f"{where}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_no_authored_reference(item, where=f"{where}.{key}")


def _resolve_descriptor_relative(
    descriptor_path: Path,
    raw: Any,
    *,
    project_root: Path,
    where: str,
    expected: PurePosixPath,
) -> Path:
    if not isinstance(raw, str) or "\\" in raw:
        _fail(where, "must be a POSIX path relative to the descriptor")
    relative = PurePosixPath(raw)
    if relative.is_absolute():
        _fail(where, "must be relative to the descriptor")
    candidate = descriptor_path.parent / Path(*relative.parts)
    if candidate.is_symlink():
        _fail(where, "symlink assets are forbidden")
    resolved = candidate.resolve()
    canonical = project_root.resolve().joinpath(*expected.parts).resolve()
    if resolved != canonical:
        _fail(where, f"must resolve to {expected.as_posix()!r}")
    if not resolved.is_file():
        _fail(where, "must resolve to a regular non-symlink file")
    return resolved


def _validate_png(path: Path, *, where: str) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG":
                _fail(where, "must decode as PNG")
            if image.width <= 0 or image.height <= 0:
                _fail(where, "PNG dimensions must be positive")
    except (OSError, ValueError) as exc:
        raise NonHanApprovalError(f"{where}: cannot decode PNG: {exc}") from exc


def _validate_copybook_reference(value: Any, *, where: str) -> None:
    reference = _exact_keys(
        value,
        {
            "role",
            "font_path",
            "font_sha256",
            "font_index",
            "postscript_name",
            "glyph_name",
            "validation",
        },
        where=where,
    )
    if reference["role"] != "identity-reference-only-no-outline-import":
        _fail(where, "copybook reference role changed")
    _nonempty_string(reference["font_path"], where=f"{where}.font_path")
    _lower_sha256(reference["font_sha256"], where=f"{where}.font_sha256")
    _integer(
        reference["font_index"],
        where=f"{where}.font_index",
        minimum=0,
    )
    _nonempty_string(
        reference["postscript_name"], where=f"{where}.postscript_name"
    )
    glyph_name = _nonempty_string(
        reference["glyph_name"], where=f"{where}.glyph_name"
    )
    if glyph_name in {".notdef", ".null", "nonmarkingreturn"}:
        _fail(where, "copybook reference glyph cannot be a notdef/empty control")
    if reference["validation"] != [
        "exact-cmap-hit",
        "non-notdef-glyph-name",
        "non-empty-distinct-outline",
        "non-empty-pillow-raster",
    ]:
        _fail(where, "copybook reference validation list changed")


def _validate_visible_descriptor(
    path: Path,
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
) -> tuple[
    Mapping[str, Any],
    Path,
    str,
    Path,
    str,
    Path,
    str,
    Path,
]:
    if batch.batch_kind != "raster-outline":
        _fail(batch.batch_id, "visible descriptor requested for semantic batch")
    payload = _read_json_object(path, label="source descriptor")
    _assert_no_authored_reference(payload, where=str(path))
    top = _exact_keys(payload, DESCRIPTOR_TOP_KEYS, where=str(path))
    if top["schema_version"] != 2:
        _fail(path, "source descriptor schema_version must be 2")
    if top["batch_id"] != batch.descriptor_batch_id:
        _fail(path, f"batch_id must be {batch.descriptor_batch_id!r}")
    if top["state"] != "generated-unreviewed":
        _fail(path, "state must remain 'generated-unreviewed'")
    if top["generator"] != "built-in-image_gen":
        _fail(path, "generator must remain 'built-in-image_gen'")
    _nonempty_string(top["generator_call"], where=f"{path}: generator_call")

    repertoire_ref = _exact_keys(
        top["repertoire"],
        {"path", "sha256", "repertoire_id", "batch_id"},
        where=f"{path}: repertoire",
    )
    expected_repertoire_relative = PurePosixPath("../repertoires/nonhan-3060.json")
    if repertoire_ref["path"] != expected_repertoire_relative.as_posix():
        _fail(path, "descriptor repertoire path changed")
    resolved_repertoire = (
        path.parent.joinpath(*expected_repertoire_relative.parts).resolve()
    )
    if resolved_repertoire != repertoire.path:
        _fail(path, "descriptor repertoire resolves to the wrong file")
    if repertoire_ref != {
        "path": expected_repertoire_relative.as_posix(),
        "sha256": repertoire.sha256,
        "repertoire_id": repertoire.repertoire_id,
        "batch_id": batch.batch_id,
    }:
        _fail(path, "descriptor repertoire pin changed")

    raster_relative = PurePosixPath(
        f"sources/imagegen/raster/{batch.batch_id}.png"
    )
    raster_path = _resolve_descriptor_relative(
        path,
        top["raster"],
        project_root=project_root,
        where=f"{path}: raster",
        expected=raster_relative,
    )
    raster_sha256 = _lower_sha256(
        top["raster_sha256"], where=f"{path}: raster_sha256"
    )
    if sha256_path(raster_path) != raster_sha256:
        _fail(path, "source raster hash mismatch")
    _validate_png(raster_path, where=f"{path}: raster")

    prompt_relative = PurePosixPath(
        f"sources/imagegen/prompts/{batch.batch_id}.md"
    )
    prompt_path = _resolve_descriptor_relative(
        path,
        top["prompt"],
        project_root=project_root,
        where=f"{path}: prompt",
        expected=prompt_relative,
    )
    if not prompt_path.read_text(encoding="utf-8").strip():
        _fail(prompt_path, "prompt must be non-empty")

    copybook = _exact_keys(
        top["copybook"],
        {"path", "sha256", "role"},
        where=f"{path}: copybook",
    )
    if copybook["role"] != "identity-reference-only-no-outline-import":
        _fail(path, "copybook role changed")
    copybook_relative = PurePosixPath(
        f"sources/imagegen/copybooks/{batch.batch_id}.png"
    )
    copybook_path = _resolve_descriptor_relative(
        path,
        copybook["path"],
        project_root=project_root,
        where=f"{path}: copybook.path",
        expected=copybook_relative,
    )
    copybook_sha256 = _lower_sha256(
        copybook["sha256"], where=f"{path}: copybook.sha256"
    )
    if sha256_path(copybook_path) != copybook_sha256:
        _fail(path, "copybook hash mismatch")
    _validate_png(copybook_path, where=f"{path}: copybook")

    style = _exact_keys(
        top["style_reference"],
        {"path", "sha256", "role"},
        where=f"{path}: style_reference",
    )
    if style["role"] != "style-only":
        _fail(path, "style-reference role changed")
    style_relative = PurePosixPath("sources/imagegen/raster/common-0001.png")
    style_path = _resolve_descriptor_relative(
        path,
        style["path"],
        project_root=project_root,
        where=f"{path}: style_reference.path",
        expected=style_relative,
    )
    style_sha256 = _lower_sha256(
        style["sha256"], where=f"{path}: style_reference.sha256"
    )
    if sha256_path(style_path) != style_sha256:
        _fail(path, "style-reference hash mismatch")
    _validate_png(style_path, where=f"{path}: style_reference")

    grid = _exact_keys(
        top["grid"],
        {"rows", "columns", "glyphs", "empty_grid_cells"},
        where=f"{path}: grid",
    )
    if grid["rows"] != 4 or grid["columns"] != 4:
        _fail(path, "descriptor grid must be exactly 4x4")
    if grid["empty_grid_cells"] != batch.empty_grid_cells:
        _fail(path, "descriptor empty_grid_cells changed")
    raw_glyphs = grid["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != len(batch.glyphs):
        _fail(path, "descriptor glyph count changed")
    seen: set[int] = set()
    for index, (raw, expected) in enumerate(
        zip(raw_glyphs, batch.glyphs, strict=True)
    ):
        where = f"{path}: grid.glyphs[{index}]"
        record = _exact_keys(
            raw, GLYPH_KEYS | {"copybook_reference"}, where=where
        )
        if {key: record[key] for key in GLYPH_KEYS} != expected.record:
            _fail(where, "does not exactly embed the frozen repertoire record")
        if expected.codepoint in seen:
            _fail(where, "duplicate descriptor glyph")
        seen.add(expected.codepoint)
        _validate_copybook_reference(
            record["copybook_reference"],
            where=f"{where}.copybook_reference",
        )
    expected_review = {
        "identity": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }
    if top["review"] != expected_review:
        _fail(path, "all descriptor review gates must remain pending")
    return (
        top,
        raster_path,
        raster_sha256,
        copybook_path,
        copybook_sha256,
        prompt_path,
        sha256_path(prompt_path),
        style_path,
    )


def _artifact_inventory(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            _fail(path, "symlink vector artifacts are forbidden")
        if not path.is_file() or path.name == "report.json":
            continue
        relative = path.relative_to(directory).as_posix()
        result[relative] = sha256_path(path)
    return result


def _artifact_path(
    build_directory: Path,
    raw: Any,
    *,
    where: str,
) -> tuple[Path, str]:
    relative = _relative_posix_path(raw, where=where)
    candidate = build_directory.joinpath(*relative.parts)
    if candidate.is_symlink():
        _fail(where, "symlink artifacts are forbidden")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(build_directory.resolve())
    except ValueError:
        _fail(where, "artifact path escapes vector-build directory")
    if not resolved.is_file():
        _fail(where, "artifact must be a regular non-symlink file")
    return resolved, relative.as_posix()


def _validate_visible_proofs(
    raw_proofs: Any,
    *,
    build_directory: Path,
    artifact_hashes: Mapping[str, str],
    where: str,
) -> tuple[Mapping[str, str], ...]:
    if not isinstance(raw_proofs, list):
        _fail(where, "must be a list")
    small_seen: set[tuple[str, int]] = set()
    singleton_seen: set[str] = set()
    review_refs: list[Mapping[str, str]] = []
    for index, raw in enumerate(raw_proofs):
        proof_where = f"{where}[{index}]"
        if not isinstance(raw, dict):
            _fail(proof_where, "must be an object")
        kind = raw.get("kind")
        if kind == "small-size":
            proof = _exact_keys(
                raw,
                {"kind", "polarity", "size_px", "path", "sha256", "cell_size_px"},
                where=proof_where,
            )
            polarity = proof["polarity"]
            size = proof["size_px"]
            if polarity not in VISUAL_POLARITIES or size not in SMALL_SIZE_PIXELS:
                _fail(proof_where, "unknown small-size proof polarity or size")
            identity = (polarity, size)
            if identity in small_seen:
                _fail(proof_where, "duplicate small-size proof")
            small_seen.add(identity)
            _integer(
                proof["cell_size_px"],
                where=f"{proof_where}.cell_size_px",
                minimum=size,
            )
            review_kind = f"small-size:{polarity}:{size}px"
        elif kind in {"segmented-source", "edge-connect"}:
            proof = _exact_keys(
                raw, {"kind", "path", "sha256"}, where=proof_where
            )
            if kind in singleton_seen:
                _fail(proof_where, f"duplicate {kind} proof")
            singleton_seen.add(kind)
            review_kind = str(kind)
        else:
            _fail(proof_where, "unknown proof kind")
        path, relative = _artifact_path(
            build_directory,
            proof["path"],
            where=f"{proof_where}.path",
        )
        digest = _lower_sha256(
            proof["sha256"], where=f"{proof_where}.sha256"
        )
        if artifact_hashes.get(relative) != digest or sha256_path(path) != digest:
            _fail(proof_where, "proof hash does not match artifact inventory")
        _validate_png(path, where=proof_where)
        if kind == "small-size":
            with Image.open(path) as image:
                extrema = image.convert("L").getextrema()
            if extrema is None or extrema[0] == extrema[1]:
                _fail(proof_where, "visible small-size proof is blank")
        review_refs.append(
            {
                "kind": review_kind,
                "path": (
                    build_directory.relative_to(build_directory.parents[2]).as_posix()
                    + f"/{relative}"
                ),
                "sha256": digest,
            }
        )
    expected_small = {
        (polarity, size)
        for polarity in VISUAL_POLARITIES
        for size in SMALL_SIZE_PIXELS
    }
    if small_seen != expected_small:
        _fail(where, f"missing five-size proof pairs: {sorted(expected_small - small_seen)}")
    if singleton_seen != {"segmented-source", "edge-connect"}:
        _fail(where, "segmented-source and edge-connect proofs are both required")
    return tuple(review_refs)


def _report_metric(
    raw: Any,
    *,
    glyph: RepertoireGlyph,
    final_bounds: tuple[int, int, int, int],
    where: str,
) -> Mapping[str, Any]:
    metric = _exact_keys(
        raw,
        {
            "horizontal_advance",
            "left_side_bearing",
            "right_side_bearing",
            "vertical_advance",
            "vertical_origin_y",
            "top_side_bearing",
            "metric_source",
            "reference_codepoint",
        },
        where=where,
    )
    advance = _integer(
        metric["horizontal_advance"],
        where=f"{where}.horizontal_advance",
        minimum=0,
        maximum=4096,
    )
    left = _integer(
        metric["left_side_bearing"], where=f"{where}.left_side_bearing"
    )
    right = _integer(
        metric["right_side_bearing"], where=f"{where}.right_side_bearing"
    )
    vertical = _integer(
        metric["vertical_advance"],
        where=f"{where}.vertical_advance",
        minimum=0,
        maximum=4096,
    )
    top = _integer(metric["top_side_bearing"], where=f"{where}.top_side_bearing")
    if metric["vertical_origin_y"] != VERTICAL_ORIGIN_Y:
        _fail(where, f"vertical_origin_y must be {VERTICAL_ORIGIN_Y}")
    x_min, _y_min, x_max, y_max = final_bounds
    if left != x_min or right != advance - x_max:
        _fail(where, "reported horizontal bearings do not match final bounds")
    if top != VERTICAL_ORIGIN_Y - y_max:
        _fail(where, "reported top bearing does not match final bounds")

    policy = glyph.metrics
    horizontal = policy["horizontal_advance"]
    kind = horizontal["kind"]
    if metric["metric_source"] != kind:
        _fail(where, "metric_source does not match frozen repertoire policy")
    expected_reference = (
        horizontal["codepoint"] if kind == "reference" else None
    )
    if metric["reference_codepoint"] != expected_reference:
        _fail(where, "reference_codepoint does not match repertoire policy")
    if kind == "fixed" and advance != horizontal["value"]:
        _fail(where, "fixed horizontal advance changed")
    if kind == "source-proportional":
        bearings = policy["side_bearings"]
        if left != bearings["left"] or right != bearings["right"]:
            _fail(where, "source-proportional bearings changed")
        if advance != x_max - x_min + left + right:
            _fail(where, "source-proportional advance is not outline width plus bearings")
    if vertical != policy["vertical_advance"]["value"]:
        _fail(where, "vertical advance changed")
    safety = policy["side_bearings"]
    if kind == "fixed" and glyph.profile_id not in {
        "nonspacing-mark",
        "box-drawing",
        "block-element",
    }:
        if left < safety["left"] or right < safety["right"]:
            _fail(where, "fixed-profile design-safety bearing was violated")
        if glyph.profile_id == "tabular-digit" and abs(left - right) > 1:
            _fail(where, "tabular digit must be centered in its fixed advance")
    return metric


def _four_numbers(value: Any, *, where: str) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4:
        _fail(where, "must contain exactly four integer bounds")
    parsed = [
        _integer(item, where=f"{where}[{index}]")
        for index, item in enumerate(value)
    ]
    return parsed[0], parsed[1], parsed[2], parsed[3]


def _four_finite_numbers(value: Any, *, where: str) -> None:
    if not isinstance(value, list) or len(value) != 4:
        _fail(where, "must contain exactly four finite bounds")
    for index, item in enumerate(value):
        _number(item, where=f"{where}[{index}]")


def _edge_mapping(
    value: Any,
    *,
    where: str,
    boolean: bool,
) -> Mapping[str, Any]:
    mapping = _exact_keys(
        value, {"left", "right", "top", "bottom"}, where=where
    )
    for edge, raw in mapping.items():
        if boolean:
            if not isinstance(raw, bool):
                _fail(f"{where}.{edge}", "must be boolean")
        else:
            _integer(raw, where=f"{where}.{edge}", minimum=0)
    return mapping


def _expected_mark_placement(glyph: RepertoireGlyph) -> str:
    if glyph.codepoint in {0x3099, 0x309A}:
        return "above-right"
    mark_class = glyph.metrics.get("mark_class")
    if not isinstance(mark_class, str) or not mark_class.startswith("ccc-"):
        _fail(glyph.codepoint_label, "nonspacing mark has no canonical CCC class")
    ccc = int(mark_class.removeprefix("ccc-"))
    if ccc == 1:
        return "overlay"
    if ccc == 233:
        return "double-below"
    if ccc == 234:
        return "double-above"
    if ccc in {202, 220, 222, 240}:
        return "below"
    if ccc in {8, 214, 216, 218, 228, 230, 232}:
        return "above"
    _fail(glyph.codepoint_label, f"unsupported mark placement for ccc-{ccc}")


def _validate_report_glyph(
    raw: Any,
    *,
    expected: RepertoireGlyph,
    index: int,
    build_directory: Path,
    artifact_hashes: Mapping[str, str],
    where: str,
) -> tuple[str, Mapping[str, Any]]:
    record = _exact_keys(raw, REPORT_GLYPH_KEYS, where=where)
    if record["character"] != expected.character:
        _fail(where, "character does not match repertoire")
    if record["codepoint"] != expected.codepoint_label:
        _fail(where, "codepoint does not match repertoire")
    if record["unicode_name"] != expected.name:
        _fail(where, "Unicode name does not match repertoire")
    glyph_name = _nonempty_string(
        record["glyph_name"], where=f"{where}.glyph_name"
    )
    if glyph_name in {".notdef", ".null", "nonmarkingreturn"}:
        _fail(where, "visible glyph cannot use an empty/control glyph name")
    if record["profile_id"] != expected.profile_id:
        _fail(where, "profile_id does not match repertoire")
    transform = PROFILE_TRANSFORMS[expected.profile_id]
    if record["transform_profile"] != transform:
        _fail(where, "transform_profile does not match frozen profile mapping")
    expected_segmentation_profile = (
        "edge"
        if transform == "edge"
        else (
            "dense-solid"
            if expected.codepoint in DENSE_SOLID_GLYPHS
            else "generic"
        )
    )
    if record["segmentation_profile"] != expected_segmentation_profile:
        _fail(where, "segmentation_profile does not match exact glyph policy")
    dense_name = DENSE_SOLID_GLYPHS.get(expected.codepoint)
    if dense_name is not None and expected.name != dense_name:
        _fail(where, "dense-solid Unicode identity changed")
    if record["metric_policy"] != expected.metrics:
        _fail(where, "metric_policy does not exactly copy repertoire metrics")
    expected_row, expected_column = divmod(index, 4)
    if record["row"] != expected_row or record["column"] != expected_column:
        _fail(where, "report row/column does not match 4x4 authoring order")
    source_box = _four_numbers(record["source_box"], where=f"{where}.source_box")
    if source_box[0] >= source_box[2] or source_box[1] >= source_box[3]:
        _fail(where, "source_box must have positive width and height")
    _four_finite_numbers(
        record["source_ink_bbox_normalized"],
        where=f"{where}.source_ink_bbox_normalized",
    )
    fraction = _number(
        record["source_ink_fraction"],
        where=f"{where}.source_ink_fraction",
    )
    maximum_fraction = SEGMENTATION_INK_FRACTION_LIMITS[
        expected_segmentation_profile
    ]
    if not 0 < fraction <= maximum_fraction:
        _fail(
            where,
            "source_ink_fraction violates its exact segmentation profile",
        )
    source_component_count = _integer(
        record["source_component_count"],
        where=f"{where}.source_component_count",
        minimum=1,
    )
    _integer(
        record["source_core_pixel_count"],
        where=f"{where}.source_core_pixel_count",
        minimum=1,
    )
    edge_contacts = _edge_mapping(
        record["edge_contacts"],
        where=f"{where}.edge_contacts",
        boolean=True,
    )
    _edge_mapping(
        record["edge_contact_pixels"],
        where=f"{where}.edge_contact_pixels",
        boolean=False,
    )
    vector_edge_contacts_raw = record["vector_edge_contacts"]
    if expected.profile_id in {"box-drawing", "block-element"}:
        if vector_edge_contacts_raw is None:
            _fail(where, "box/block glyph requires vector edge-contact evidence")
        vector_edge_contacts = _edge_mapping(
            vector_edge_contacts_raw,
            where=f"{where}.vector_edge_contacts",
            boolean=True,
        )
    else:
        if vector_edge_contacts_raw is not None:
            _fail(
                where,
                "vector edge-contact evidence is forbidden outside box/block glyphs",
            )
        vector_edge_contacts = None
    _four_finite_numbers(
        record["pre_metric_bounds"], where=f"{where}.pre_metric_bounds"
    )
    final_bounds = _four_numbers(
        record["final_bounds"], where=f"{where}.final_bounds"
    )
    x_min, y_min, x_max, y_max = final_bounds
    if x_min >= x_max or y_min >= y_max:
        _fail(where, "visible final_bounds must be non-empty")
    _report_metric(
        record["metrics"],
        glyph=expected,
        final_bounds=final_bounds,
        where=f"{where}.metrics",
    )

    mark_class = expected.metrics.get("mark_class")
    if expected.profile_id == "nonspacing-mark":
        if transform != "mark":
            _fail(where, "nonspacing mark must use mark transform")
        if record["mark_class"] != mark_class:
            _fail(where, "mark_class does not match repertoire")
        placement = _expected_mark_placement(expected)
        if record["mark_placement"] != placement:
            _fail(where, "mark_placement does not match canonical CCC policy")
        anchors = _exact_keys(
            record["anchors_candidate"],
            {"kind", "class", "canonical_combining_class", "mark_anchor"},
            where=f"{where}.anchors_candidate",
        )
        if anchors["kind"] != "mark" or anchors["class"] != placement:
            _fail(where, "mark anchor classification changed")
        mark_anchor = _exact_keys(
            anchors["mark_anchor"],
            {"x", "y"},
            where=f"{where}.anchors_candidate.mark_anchor",
        )
        if mark_anchor != {"x": 0, "y": 0}:
            _fail(where, "mark anchor must remain at the zero-advance origin")
        if (
            record["metrics"]["horizontal_advance"] != 0
            or record["metrics"]["vertical_advance"] != 0
        ):
            _fail(where, "nonspacing mark advances must both be zero")
    else:
        if record["mark_class"] is not None:
            _fail(where, "mark_class is forbidden outside nonspacing marks")
        if record["mark_placement"] is not None:
            _fail(where, "mark_placement is forbidden outside nonspacing marks")
        if not isinstance(record["anchors_candidate"], dict):
            _fail(where, "visible base glyph requires anchor-candidate evidence")

    if expected.profile_id in {"box-drawing", "block-element"}:
        if transform != "edge":
            _fail(where, "box/block profile must use edge transform")
        metric = record["metrics"]
        if metric["horizontal_advance"] != UPM or metric["vertical_advance"] != UPM:
            _fail(where, "box/block advances must both equal one em")
        edge_limit = {
            "left": x_min <= 8,
            "right": x_max >= UPM - 8,
            "bottom": y_min <= 8,
            "top": y_max >= UPM - 8,
        }
        assert vector_edge_contacts is not None
        if vector_edge_contacts != edge_limit:
            _fail(
                where,
                "vector edge-contact evidence does not match final outline bounds",
            )
        for edge, required in edge_contacts.items():
            if required and not vector_edge_contacts[edge]:
                _fail(where, f"required {edge} edge contact was disconnected")

    geometry: dict[str, int | float] = {}
    for key in (
        "contour_count",
        "point_count",
        "outer_contour_count",
        "minimum_control_edge",
    ):
        numeric = (
            _number(record[key], where=f"{where}.{key}")
            if key == "minimum_control_edge"
            else _integer(record[key], where=f"{where}.{key}", minimum=1)
        )
        if numeric <= 0:
            _fail(where, f"{key} must be positive for a visible outline")
        geometry[key] = numeric
    geometry["counter_count"] = _integer(
        record["counter_count"],
        where=f"{where}.counter_count",
        minimum=0,
    )
    if (
        expected.profile_id in {"box-drawing", "block-element"}
        and geometry["outer_contour_count"] != source_component_count
    ):
        _fail(
            where,
            "edge glyph source-component/vector-outer topology differs",
        )
    for key in (
        "micro_edge_count",
        "acute_micro_turn_count",
        "micro_thorn_points_removed",
    ):
        if record[key] != 0:
            _fail(where, f"{key} must be exactly zero")
    if _number(
        record["maximum_micro_thorn_displacement"],
        where=f"{where}.maximum_micro_thorn_displacement",
    ) != 0:
        _fail(where, "maximum_micro_thorn_displacement must be zero")
    for key in (
        "quantization_duplicate_points_removed",
        "coincident_flank_control_points_removed",
    ):
        _integer(record[key], where=f"{where}.{key}", minimum=0)
    if _number(
        record["maximum_quantization_collapse"],
        where=f"{where}.maximum_quantization_collapse",
    ) < 0:
        _fail(where, "maximum_quantization_collapse cannot be negative")

    coverage = _exact_keys(
        record["coverage_pixels"],
        {str(size) for size in SMALL_SIZE_PIXELS},
        where=f"{where}.coverage_pixels",
    )
    for size in SMALL_SIZE_PIXELS:
        divisor = (
            MARK_PROOF_COVERAGE_DIVISOR
            if expected.profile_id == "nonspacing-mark"
            else DEFAULT_PROOF_COVERAGE_DIVISOR
        )
        minimum = max(MINIMUM_PROOF_COVERAGE_PIXELS, size // divisor)
        _integer(
            coverage[str(size)],
            where=f"{where}.coverage_pixels.{size}",
            minimum=minimum,
        )

    for field, suffix in (("source_png", ".png"), ("svg", ".svg")):
        artifact_path, relative = _artifact_path(
            build_directory,
            record[field],
            where=f"{where}.{field}",
        )
        if not relative.endswith(suffix):
            _fail(where, f"{field} must use {suffix}")
        digest_field = f"{field}_sha256"
        digest = _lower_sha256(
            record[digest_field], where=f"{where}.{digest_field}"
        )
        if artifact_hashes.get(relative) != digest:
            _fail(where, f"{field} is absent from artifact inventory")
        if sha256_path(artifact_path) != digest:
            _fail(where, f"{field} hash mismatch")
    report_relative = f"glyph-report/u{expected.codepoint:04x}.json"
    if report_relative not in artifact_hashes:
        _fail(where, f"missing per-glyph artifact {report_relative}")
    glyph_report_path = build_directory / report_relative
    glyph_report = _read_json_object(glyph_report_path, label="glyph report")
    if glyph_report != dict(record):
        _fail(where, "per-glyph report does not match aggregate report")
    return glyph_name, record


def _font_bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    glyph = font["glyf"][glyph_name]
    glyph.recalcBounds(font["glyf"])
    return (
        int(glyph.xMin),
        int(glyph.yMin),
        int(glyph.xMax),
        int(glyph.yMax),
    )


def _validate_visible_font(
    path: Path,
    *,
    batch: RepertoireBatch,
    report_glyphs: Sequence[Mapping[str, Any]],
) -> None:
    try:
        font = TTFont(
            path,
            lazy=False,
            checkChecksums=2,
            recalcTimestamp=False,
        )
    except Exception as exc:
        raise NonHanApprovalError(f"{path}: cannot open vector font: {exc}") from exc
    try:
        if "glyf" not in font or "CFF " in font or "CFF2" in font:
            _fail(path, "visible font must use quadratic glyf outlines")
        if "hmtx" not in font or "vmtx" not in font:
            _fail(path, "visible font must contain horizontal and vertical metrics")
        expected_names = [str(record["glyph_name"]) for record in report_glyphs]
        if font.getGlyphOrder() != [".notdef", *expected_names]:
            _fail(path, "glyph order is not exactly .notdef plus batch glyphs")
        expected_cmap = {
            glyph.codepoint: name
            for glyph, name in zip(batch.glyphs, expected_names, strict=True)
        }
        if font.getBestCmap() != expected_cmap:
            _fail(path, "cmap is not the exact batch mapping")
        for glyph, record, name in zip(
            batch.glyphs, report_glyphs, expected_names, strict=True
        ):
            built = font["glyf"][name]
            if built.isComposite() or built.numberOfContours <= 0:
                _fail(
                    path,
                    f"{glyph.codepoint_label}: outline must be simple and non-empty",
                )
            bounds = _font_bounds(font, name)
            if bounds != tuple(record["final_bounds"]):
                _fail(path, f"{glyph.codepoint_label}: font/report bounds differ")
            horizontal = record["metrics"]
            expected_hmetric = (
                horizontal["horizontal_advance"],
                horizontal["left_side_bearing"],
            )
            if font["hmtx"].metrics[name] != expected_hmetric:
                _fail(path, f"{glyph.codepoint_label}: horizontal metrics differ")
            expected_vmetric = (
                horizontal["vertical_advance"],
                horizontal["top_side_bearing"],
            )
            if font["vmtx"].metrics[name] != expected_vmetric:
                _fail(path, f"{glyph.codepoint_label}: vertical metrics differ")
            try:
                (
                    contour_count,
                    point_count,
                    outer_count,
                    counter_count,
                    minimum_edge,
                    micro_edges,
                    acute_turns,
                ) = han_pipeline._geometry_quality(built)
            except han_pipeline.ImagegenPipelineError as exc:
                _fail(
                    path,
                    f"{glyph.codepoint_label}: invalid actual outline geometry: {exc}",
                )
            expected_geometry = {
                "contour_count": contour_count,
                "point_count": point_count,
                "outer_contour_count": outer_count,
                "counter_count": counter_count,
                "minimum_control_edge": round(minimum_edge, 6),
                "micro_edge_count": micro_edges,
                "acute_micro_turn_count": acute_turns,
            }
            for key, actual in expected_geometry.items():
                if record[key] != actual:
                    _fail(
                        path,
                        f"{glyph.codepoint_label}: actual {key} differs from report",
                    )
            if (
                glyph.profile_id in {"box-drawing", "block-element"}
                and outer_count != record["source_component_count"]
            ):
                _fail(
                    path,
                    f"{glyph.codepoint_label}: actual edge topology differs "
                    "from source components",
                )
    finally:
        font.close()


def _validate_visible_report(
    path: Path,
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    descriptor_path: Path,
    descriptor_sha256: str,
    raster_path: Path,
    raster_sha256: str,
    descriptor: Mapping[str, Any],
) -> tuple[Mapping[str, Any], tuple[Mapping[str, str], ...]]:
    payload = _read_json_object(path, label="vector report")
    top = _exact_keys(payload, REPORT_TOP_KEYS, where=str(path))
    if top["schema_version"] != 1:
        _fail(path, "vector report schema_version must be 1")
    if top["pipeline"] != VISIBLE_PIPELINE:
        _fail(path, f"pipeline must be {VISIBLE_PIPELINE!r}")
    if top["approval_state"] != "unreviewed":
        _fail(path, "vector report must remain unreviewed")
    if top["batch_id"] != batch.descriptor_batch_id:
        _fail(path, f"batch_id must be {batch.descriptor_batch_id!r}")
    if top["source_type"] != VISIBLE_SOURCE_TYPE:
        _fail(path, f"source_type must be {VISIBLE_SOURCE_TYPE!r}")
    expected_descriptor_relative = PurePosixPath(
        f"sources/imagegen/batches/{batch.batch_id}.source.json"
    )
    if top["source_descriptor"] != expected_descriptor_relative.as_posix():
        _fail(path, "source_descriptor path mismatch")
    if top["source_descriptor_sha256"] != descriptor_sha256:
        _fail(path, "source descriptor hash mismatch")
    if sha256_path(descriptor_path) != descriptor_sha256:
        _fail(path, "source descriptor changed during vector validation")
    if top["source_generator"] != "built-in-image_gen":
        _fail(path, "source_generator changed")
    if top["source_generator_call"] != descriptor["generator_call"]:
        _fail(path, "source_generator_call differs from descriptor")
    expected_repertoire_relative = REPERTOIRE_RELATIVE_PATH.as_posix()
    if (
        top["source_repertoire"] != expected_repertoire_relative
        or top["source_repertoire_sha256"] != repertoire.sha256
    ):
        _fail(path, "source repertoire provenance changed")
    expected_prompt_relative = (
        f"sources/imagegen/prompts/{batch.batch_id}.md"
    )
    prompt_path = project_root / expected_prompt_relative
    if (
        top["source_prompt"] != expected_prompt_relative
        or top["source_prompt_sha256"] != sha256_path(prompt_path)
    ):
        _fail(path, "source prompt provenance changed")
    expected_copybook_relative = (
        f"sources/imagegen/copybooks/{batch.batch_id}.png"
    )
    if (
        top["source_copybook"] != expected_copybook_relative
        or top["source_copybook_sha256"]
        != descriptor["copybook"]["sha256"]
    ):
        _fail(path, "source copybook provenance changed")
    expected_style_relative = "sources/imagegen/raster/common-0001.png"
    if (
        top["source_style_reference"] != expected_style_relative
        or top["source_style_reference_sha256"]
        != descriptor["style_reference"]["sha256"]
    ):
        _fail(path, "source style-reference provenance changed")
    expected_raster_relative = PurePosixPath(
        f"sources/imagegen/raster/{batch.batch_id}.png"
    )
    if top["source_raster"] != expected_raster_relative.as_posix():
        _fail(path, "source_raster path mismatch")
    if top["source_raster_sha256"] != raster_sha256:
        _fail(path, "source raster hash mismatch")
    if sha256_path(raster_path) != raster_sha256:
        _fail(path, "source raster changed during vector validation")
    if top["source_state"] != "generated-unreviewed":
        _fail(path, "source_state must remain generated-unreviewed")
    if top["source_review"] != descriptor["review"]:
        _fail(path, "source_review differs from descriptor")
    expected_characters = [glyph.character for glyph in batch.glyphs]
    expected_codepoints = [glyph.codepoint_label for glyph in batch.glyphs]
    if top["characters"] != expected_characters:
        _fail(path, "character sequence differs from repertoire batch")
    if top["codepoints"] != expected_codepoints:
        _fail(path, "codepoint sequence differs from repertoire batch")

    grid = _exact_keys(
        top["grid"],
        {
            "rows",
            "columns",
            "empty_grid_cells",
            "cell_slots",
            "x_rule_centers",
            "y_rule_centers",
            "x_rule_spans",
            "y_rule_spans",
            "synthesized_coordinates",
        },
        where=f"{path}: grid",
    )
    if grid["rows"] != 4 or grid["columns"] != 4:
        _fail(path, "vector report grid must be exactly 4x4")
    if grid["empty_grid_cells"] != batch.empty_grid_cells:
        _fail(path, "vector report empty-grid count changed")
    if grid["cell_slots"] != [
        *expected_codepoints,
        *(None for _ in range(batch.empty_grid_cells or 0)),
    ]:
        _fail(path, "vector report cell slots changed")
    if grid["synthesized_coordinates"] is not False:
        _fail(path, "grid coordinates may not be synthesized")
    for axis in ("x", "y"):
        centers = grid[f"{axis}_rule_centers"]
        spans = grid[f"{axis}_rule_spans"]
        if not isinstance(centers, list) or len(centers) != 5:
            _fail(path, f"{axis}-axis must report five grid-rule centers")
        if not isinstance(spans, list) or len(spans) != 5:
            _fail(path, f"{axis}-axis must report five grid-rule spans")

    metric_contract = _exact_keys(
        top["metric_contract"],
        {
            "units_per_em",
            "vertical_origin_y",
            "zero_advance_visible_mark_count",
            "spacing_combining_marks",
            "two_em_vertical_advance",
            "profile_transforms",
            "proportional_advance",
        },
        where=f"{path}: metric_contract",
    )
    if (
        metric_contract["units_per_em"] != UPM
        or metric_contract["vertical_origin_y"] != VERTICAL_ORIGIN_Y
        or metric_contract["zero_advance_visible_mark_count"] != 112
        or metric_contract["spacing_combining_marks"] != ["U+302E", "U+302F"]
        or metric_contract["two_em_vertical_advance"] != ["U+3031", "U+3032"]
        or metric_contract["profile_transforms"] != dict(PROFILE_TRANSFORMS)
        or metric_contract["proportional_advance"]
        != "source-outline-width-plus-audited-fixed-side-bearings"
    ):
        _fail(path, "metric contract changed")
    vectorization = _exact_keys(
        top["vectorization"],
        {
            "tool",
            "outline_format",
            "cu2qu_max_error",
            "grid_rules_removed_by_detected_rule_spans",
            "grid_rule_interior_padding_px",
            "segmentation_ink_fraction_limits",
            "dense_solid_codepoints",
            "edge_profile_preserves_border_contacts",
            "small_size_proof_coverage",
        },
        where=f"{path}: vectorization",
    )
    _nonempty_string(vectorization["tool"], where=f"{path}: vectorization.tool")
    coverage_contract = _exact_keys(
        vectorization["small_size_proof_coverage"],
        {
            "minimum_pixels",
            "default_size_divisor",
            "nonspacing_mark_size_divisor",
        },
        where=f"{path}: vectorization.small_size_proof_coverage",
    )
    if (
        vectorization["outline_format"] != "TrueType quadratic glyf"
        or vectorization["cu2qu_max_error"] != CU2QU_MAX_ERROR
        or vectorization["grid_rules_removed_by_detected_rule_spans"] is not True
        or vectorization["grid_rule_interior_padding_px"]
        != GRID_RULE_INTERIOR_PADDING
        or vectorization["segmentation_ink_fraction_limits"]
        != dict(SEGMENTATION_INK_FRACTION_LIMITS)
        or vectorization["dense_solid_codepoints"]
        != [f"U+{value:04X}" for value in DENSE_SOLID_GLYPHS]
        or vectorization["edge_profile_preserves_border_contacts"] is not True
        or coverage_contract
        != {
            "minimum_pixels": MINIMUM_PROOF_COVERAGE_PIXELS,
            "default_size_divisor": DEFAULT_PROOF_COVERAGE_DIVISOR,
            "nonspacing_mark_size_divisor": MARK_PROOF_COVERAGE_DIVISOR,
        }
    ):
        _fail(path, "vectorization invariants changed")

    raw_artifacts = top["artifact_sha256"]
    if not isinstance(raw_artifacts, dict) or not raw_artifacts:
        _fail(path, "artifact_sha256 must be a non-empty object")
    artifact_hashes: dict[str, str] = {}
    for raw_relative, raw_hash in raw_artifacts.items():
        relative = _relative_posix_path(
            raw_relative, where=f"{path}: artifact_sha256 key"
        ).as_posix()
        if relative in artifact_hashes:
            _fail(path, f"duplicate artifact path {relative}")
        artifact_hashes[relative] = _lower_sha256(
            raw_hash, where=f"{path}: artifact_sha256[{relative!r}]"
        )
    actual_inventory = _artifact_inventory(path.parent)
    if artifact_hashes != actual_inventory:
        missing = sorted(set(actual_inventory) - set(artifact_hashes))
        extra = sorted(set(artifact_hashes) - set(actual_inventory))
        changed = sorted(
            key
            for key in set(actual_inventory) & set(artifact_hashes)
            if actual_inventory[key] != artifact_hashes[key]
        )
        _fail(
            path,
            f"artifact inventory mismatch; missing={missing}, extra={extra}, "
            f"changed={changed}",
        )

    proof_refs = _validate_visible_proofs(
        top["proofs"],
        build_directory=path.parent,
        artifact_hashes=artifact_hashes,
        where=f"{path}: proofs",
    )
    raw_glyphs = top["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != len(batch.glyphs):
        _fail(path, "vector report glyph count changed")
    report_glyphs: list[Mapping[str, Any]] = []
    glyph_names: set[str] = set()
    for index, (raw, expected) in enumerate(
        zip(raw_glyphs, batch.glyphs, strict=True)
    ):
        name, record = _validate_report_glyph(
            raw,
            expected=expected,
            index=index,
            build_directory=path.parent,
            artifact_hashes=artifact_hashes,
            where=f"{path}: glyphs[{index}]",
        )
        if name in glyph_names:
            _fail(path, f"duplicate report glyph name {name!r}")
        glyph_names.add(name)
        report_glyphs.append(record)

    font_record = _exact_keys(
        top["font"],
        {
            "units_per_em",
            "ttf",
            "ttf_sha256",
            "otf",
            "otf_sha256",
            "cmap_count",
            "glyph_count",
            "has_vertical_metrics",
        },
        where=f"{path}: font",
    )
    if (
        font_record["units_per_em"] != UPM
        or font_record["cmap_count"] != len(batch.glyphs)
        or font_record["glyph_count"] != len(batch.glyphs) + 1
        or font_record["has_vertical_metrics"] is not True
    ):
        _fail(path, "font summary changed")
    for format_name in ("ttf", "otf"):
        font_path, relative = _artifact_path(
            path.parent,
            font_record[format_name],
            where=f"{path}: font.{format_name}",
        )
        if font_path.suffix.lower() != f".{format_name}":
            _fail(path, f"font.{format_name} extension mismatch")
        digest = _lower_sha256(
            font_record[f"{format_name}_sha256"],
            where=f"{path}: font.{format_name}_sha256",
        )
        if artifact_hashes.get(relative) != digest or sha256_path(font_path) != digest:
            _fail(path, f"font.{format_name} hash mismatch")
        _validate_visible_font(
            font_path, batch=batch, report_glyphs=report_glyphs
        )
    return top, proof_refs


def visible_evidence(
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
) -> VisibleEvidence:
    """Validate every byte needed before a visible review can be recorded."""

    project_root = project_root.resolve()
    if batch.batch_kind != "raster-outline":
        _fail(batch.batch_id, "is not a raster-outline batch")
    descriptor_relative = PurePosixPath(
        f"sources/imagegen/batches/{batch.batch_id}.source.json"
    )
    descriptor_path = _resolve_regular_file(
        project_root, descriptor_relative, where=f"{batch.batch_id}: descriptor"
    )
    descriptor_sha256 = sha256_path(descriptor_path)
    (
        descriptor,
        raster_path,
        raster_sha256,
        copybook_path,
        copybook_sha256,
        prompt_path,
        prompt_sha256,
        style_path,
    ) = _validate_visible_descriptor(
        descriptor_path,
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
    )
    style_sha256 = sha256_path(style_path)
    report_relative = PurePosixPath(
        f"build/imagegen/{batch.descriptor_batch_id}/report.json"
    )
    report_path = _resolve_regular_file(
        project_root, report_relative, where=f"{batch.batch_id}: vector report"
    )
    from scripts.imagegen_derived_artifacts import (
        DerivedArtifactError,
        ensure_materialized,
    )

    try:
        ensure_materialized(report_path, project_root=project_root)
    except DerivedArtifactError as exc:
        _fail(report_path, str(exc))
    report, proof_refs = _validate_visible_report(
        report_path,
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
        descriptor_path=descriptor_path,
        descriptor_sha256=descriptor_sha256,
        raster_path=raster_path,
        raster_sha256=raster_sha256,
        descriptor=descriptor,
    )
    return VisibleEvidence(
        descriptor_path=descriptor_path,
        descriptor_sha256=descriptor_sha256,
        raster_path=raster_path,
        raster_sha256=raster_sha256,
        copybook_path=copybook_path,
        copybook_sha256=copybook_sha256,
        prompt_path=prompt_path,
        prompt_sha256=prompt_sha256,
        style_reference_path=style_path,
        style_reference_sha256=style_sha256,
        report_path=report_path,
        report_sha256=sha256_path(report_path),
        report=report,
        proof_references=proof_refs,
    )


def _metric_from_visible_approval(
    approval: ValidatedApproval,
    *,
    codepoint: int,
) -> int:
    evidence = approval.visible_evidence
    if evidence is None:
        _fail(approval.approval_path, "semantic reference points to a non-visible approval")
    matches = [
        record
        for record in evidence.report["glyphs"]
        if record["codepoint"] == f"U+{codepoint:04X}"
    ]
    if len(matches) != 1:
        _fail(
            approval.approval_path,
            f"must contain exactly one U+{codepoint:04X} metric source",
        )
    return _integer(
        matches[0]["metrics"]["horizontal_advance"],
        where=f"{approval.approval_path}: U+{codepoint:04X} advance",
        minimum=0,
        maximum=4096,
    )


def _validate_semantic_reference_metrics(
    value: Any,
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    where: str,
) -> Mapping[int, int]:
    required_targets = sorted(
        {
            int(glyph.metrics["horizontal_advance"]["codepoint"][2:], 16)
            for glyph in batch.glyphs
            if glyph.metrics["horizontal_advance"]["kind"] == "reference"
        }
    )
    if not isinstance(value, list) or len(value) != len(required_targets):
        _fail(where, "must contain exactly the referenced visible metrics")
    result: dict[int, int] = {}
    for index, (raw, expected_codepoint) in enumerate(
        zip(value, required_targets, strict=True)
    ):
        item_where = f"{where}[{index}]"
        item = _exact_keys(
            raw,
            {"codepoint", "horizontal_advance", "source_approval"},
            where=item_where,
        )
        codepoint, _label = _codepoint(
            item["codepoint"], where=f"{item_where}.codepoint"
        )
        if codepoint != expected_codepoint:
            _fail(item_where, "reference codepoint order/content changed")
        source_batch = next(
            candidate
            for candidate in repertoire.batches[:VISIBLE_BATCHES]
            if any(glyph.codepoint == codepoint for glyph in candidate.glyphs)
        )
        expected_approval_relative = PurePosixPath(
            f"sources/imagegen/approvals/{source_batch.batch_id}.approval.json"
        )
        approval_path, approval_hash = _reference(
            item["source_approval"],
            where=f"{item_where}.source_approval",
            project_root=project_root,
            expected_path=expected_approval_relative,
        )
        source_approval = validate_approval(
            approval_path,
            project_root=project_root,
            repertoire=repertoire,
        )
        if source_approval.batch.batch_id != source_batch.batch_id:
            _fail(item_where, "reference approval batch mismatch")
        if sha256_path(approval_path) != approval_hash:
            _fail(item_where, "reference approval changed during validation")
        actual_advance = _metric_from_visible_approval(
            source_approval, codepoint=codepoint
        )
        declared = _integer(
            item["horizontal_advance"],
            where=f"{item_where}.horizontal_advance",
            minimum=0,
            maximum=4096,
        )
        if declared != actual_advance:
            _fail(item_where, "referenced horizontal advance changed")
        if codepoint in result:
            _fail(item_where, "duplicate reference metric")
        result[codepoint] = declared
    return result


def _resolved_semantic_advance(
    glyph: RepertoireGlyph,
    *,
    references: Mapping[int, int],
    where: str,
) -> int:
    horizontal = glyph.metrics["horizontal_advance"]
    if horizontal["kind"] == "fixed":
        return int(horizontal["value"])
    if horizontal["kind"] == "reference":
        target = int(horizontal["codepoint"][2:], 16)
        if target not in references:
            _fail(where, f"missing resolved reference U+{target:04X}")
        return references[target]
    _fail(where, "semantic-empty glyph cannot use source-proportional advance")


def _validate_semantic_font(
    path: Path,
    *,
    batch: RepertoireBatch,
    glyph_records: Sequence[Mapping[str, Any]],
    references: Mapping[int, int],
) -> None:
    try:
        font = TTFont(
            path,
            lazy=False,
            checkChecksums=2,
            recalcTimestamp=False,
        )
    except Exception as exc:
        raise NonHanApprovalError(f"{path}: cannot open semantic font: {exc}") from exc
    try:
        if "glyf" not in font or "CFF " in font or "CFF2" in font:
            _fail(path, "semantic font must use quadratic glyf outlines")
        if "hmtx" not in font or "vmtx" not in font:
            _fail(path, "semantic font must contain horizontal and vertical metrics")
        glyph_names = [str(record["glyph_name"]) for record in glyph_records]
        if font.getGlyphOrder() != [".notdef", *glyph_names]:
            _fail(path, "semantic glyph order changed")
        expected_cmap = {
            glyph.codepoint: name
            for glyph, name in zip(batch.glyphs, glyph_names, strict=True)
        }
        if font.getBestCmap() != expected_cmap:
            _fail(path, "semantic cmap is not the exact 17-scalar mapping")
        for glyph, raw, glyph_name in zip(
            batch.glyphs, glyph_records, glyph_names, strict=True
        ):
            built = font["glyf"][glyph_name]
            if built.isComposite() or built.numberOfContours != 0:
                _fail(
                    path,
                    f"{glyph.codepoint_label}: semantic glyf must be exactly empty",
                )
            resolved = _resolved_semantic_advance(
                glyph,
                references=references,
                where=f"{path}: {glyph.codepoint_label}",
            )
            if raw["resolved_horizontal_advance"] != resolved:
                _fail(
                    path,
                    f"{glyph.codepoint_label}: manifest resolution changed",
                )
            if font["hmtx"].metrics[glyph_name] != (resolved, 0):
                _fail(
                    path,
                    f"{glyph.codepoint_label}: semantic horizontal metrics changed",
                )
            vertical = glyph.metrics["vertical_advance"]["value"]
            if font["vmtx"].metrics[glyph_name] != (vertical, 0):
                _fail(
                    path,
                    f"{glyph.codepoint_label}: semantic vertical metrics changed",
                )
    finally:
        font.close()


def _validate_blank_proof(path: Path, *, where: str) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG" or image.mode != "L":
                _fail(where, "blank proof must be an 8-bit grayscale PNG")
            if image.size != (320, 64):
                _fail(where, "blank proof must be exactly 320x64 pixels")
            if image.getextrema() != (255, 255):
                _fail(where, "blank proof contains non-background pixels")
            if image.text:
                _fail(where, "blank proof must not carry unpinned text metadata")
    except (OSError, ValueError) as exc:
        raise NonHanApprovalError(
            f"{where}: cannot decode blank proof PNG: {exc}"
        ) from exc


def _validate_font_renders_blank(
    font_path: Path,
    *,
    batch: RepertoireBatch,
) -> None:
    try:
        face = freetype.Face(str(font_path))
    except Exception as exc:
        raise NonHanApprovalError(
            f"{font_path}: FreeType cannot open semantic font: {exc}"
        ) from exc
    flags = (
        freetype.FT_LOAD_RENDER
        | freetype.FT_LOAD_NO_HINTING
        | freetype.FT_LOAD_TARGET_NORMAL
    )
    for size in SMALL_SIZE_PIXELS:
        face.set_pixel_sizes(0, size)
        for glyph in batch.glyphs:
            try:
                face.load_char(glyph.character, flags)
            except Exception as exc:
                raise NonHanApprovalError(
                    f"{font_path}: cannot render {glyph.codepoint_label} "
                    f"at {size}px: {exc}"
                ) from exc
            bitmap = face.glyph.bitmap
            if bitmap.width > 0 and bitmap.rows > 0 and any(bitmap.buffer):
                _fail(
                    font_path,
                    f"{glyph.codepoint_label} produced ink at {size}px",
                )


def semantic_evidence(
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
) -> SemanticEvidence:
    """Validate the semantic-only manifest, empty font, and blank proof."""

    project_root = project_root.resolve()
    if batch.batch_id != SEMANTIC_BATCH_ID or batch.batch_kind != "semantic-empty":
        _fail(batch.batch_id, "is not the canonical semantic-empty batch")
    manifest_relative = PurePosixPath(
        "sources/imagegen/semantic/nonhan-0206.semantic.json"
    )
    manifest_path = _resolve_regular_file(
        project_root,
        manifest_relative,
        where=f"{batch.batch_id}: semantic manifest",
    )
    payload = _read_json_object(manifest_path, label="semantic evidence")
    _assert_no_authored_reference(payload, where=str(manifest_path))
    top = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "batch_id",
            "repertoire",
            "font",
            "blank_render_proof",
            "reference_metrics",
            "glyphs",
        },
        where=str(manifest_path),
    )
    if top["schema_version"] != 1:
        _fail(manifest_path, "semantic schema_version must be 1")
    if top["record_type"] != SEMANTIC_RECORD_TYPE:
        _fail(manifest_path, f"record_type must be {SEMANTIC_RECORD_TYPE!r}")
    if top["batch_id"] != SEMANTIC_BATCH_ID:
        _fail(manifest_path, f"batch_id must be {SEMANTIC_BATCH_ID!r}")
    _validate_approval_repertoire(
        top["repertoire"],
        repertoire=repertoire,
        batch=batch,
        where=f"{manifest_path}: repertoire",
    )
    references = _validate_semantic_reference_metrics(
        top["reference_metrics"],
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
        where=f"{manifest_path}: reference_metrics",
    )

    font_record = _exact_keys(
        top["font"],
        {"path", "sha256", "format"},
        where=f"{manifest_path}: font",
    )
    expected_font_relative = PurePosixPath(
        "build/imagegen/imagegen-nonhan-0206/font/"
        "ClearHandTC-NonHan0206-Semantic.ttf"
    )
    font_path, font_sha256 = _reference(
        {"path": font_record["path"], "sha256": font_record["sha256"]},
        where=f"{manifest_path}: font",
        project_root=project_root,
        expected_path=expected_font_relative,
    )
    if font_record["format"] != "TrueType quadratic glyf":
        _fail(manifest_path, "semantic font format changed")

    proof_record = _exact_keys(
        top["blank_render_proof"],
        {
            "path",
            "sha256",
            "format",
            "mode",
            "size",
            "sizes_px",
            "expected_ink_pixels",
        },
        where=f"{manifest_path}: blank_render_proof",
    )
    expected_proof_relative = PurePosixPath(
        "build/imagegen/imagegen-nonhan-0206/proof/blank-render.png"
    )
    proof_path, proof_sha256 = _reference(
        {"path": proof_record["path"], "sha256": proof_record["sha256"]},
        where=f"{manifest_path}: blank_render_proof",
        project_root=project_root,
        expected_path=expected_proof_relative,
    )
    if proof_record != {
        "path": expected_proof_relative.as_posix(),
        "sha256": proof_sha256,
        "format": "PNG",
        "mode": "L",
        "size": [320, 64],
        "sizes_px": list(SMALL_SIZE_PIXELS),
        "expected_ink_pixels": 0,
    }:
        _fail(manifest_path, "blank-render proof contract changed")
    _validate_blank_proof(
        proof_path, where=f"{manifest_path}: blank_render_proof"
    )

    raw_glyphs = top["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != SEMANTIC_GLYPHS:
        _fail(manifest_path, "semantic glyphs must contain exactly 17 records")
    semantic_records: list[Mapping[str, Any]] = []
    seen: set[int] = set()
    for index, (raw, expected) in enumerate(
        zip(raw_glyphs, batch.glyphs, strict=True)
    ):
        where = f"{manifest_path}: glyphs[{index}]"
        record = _exact_keys(
            raw,
            {
                "authoring_rank",
                "character",
                "codepoint",
                "name",
                "gc",
                "profile_id",
                "metrics",
                "glyph_name",
                "resolved_horizontal_advance",
            },
            where=where,
        )
        expected_identity = {
            "authoring_rank": expected.authoring_rank,
            "character": expected.character,
            "codepoint": expected.codepoint_label,
            "name": expected.name,
            "gc": expected.general_category,
            "profile_id": expected.profile_id,
            "metrics": expected.metrics,
        }
        if {
            key: record[key] for key in expected_identity
        } != expected_identity:
            _fail(where, "does not exactly preserve repertoire identity/metrics")
        if expected.codepoint in seen:
            _fail(where, "duplicate semantic glyph")
        seen.add(expected.codepoint)
        expected_name = f"uni{expected.codepoint:04X}"
        if record["glyph_name"] != expected_name:
            _fail(where, f"glyph_name must be {expected_name!r}")
        resolved = _resolved_semantic_advance(
            expected, references=references, where=where
        )
        if record["resolved_horizontal_advance"] != resolved:
            _fail(where, "resolved horizontal advance changed")
        semantic_records.append(record)
    _validate_semantic_font(
        font_path,
        batch=batch,
        glyph_records=semantic_records,
        references=references,
    )
    _validate_font_renders_blank(font_path, batch=batch)
    return SemanticEvidence(
        manifest_path=manifest_path,
        manifest_sha256=sha256_path(manifest_path),
        font_path=font_path,
        font_sha256=font_sha256,
        blank_proof_path=proof_path,
        blank_proof_sha256=proof_sha256,
        manifest=top,
        proof_references=(
            {
                "kind": "blank-render",
                "path": expected_proof_relative.as_posix(),
                "sha256": proof_sha256,
            },
        ),
    )


def _project_relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise NonHanApprovalError(
            f"{path}: path is outside project root {project_root}"
        ) from exc


def _file_reference(path: Path, project_root: Path) -> dict[str, str]:
    return {
        "path": _project_relative(path, project_root),
        "sha256": sha256_path(path),
    }


def _visible_source_payload(
    evidence: VisibleEvidence,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "descriptor": _file_reference(evidence.descriptor_path, project_root),
        "raster": _file_reference(evidence.raster_path, project_root),
        "copybook": _file_reference(evidence.copybook_path, project_root),
        "prompt": _file_reference(evidence.prompt_path, project_root),
        "style_reference": _file_reference(
            evidence.style_reference_path, project_root
        ),
    }


def _vector_build_payload(
    evidence: VisibleEvidence,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "report": _file_reference(evidence.report_path, project_root),
        "pipeline": VISIBLE_PIPELINE,
        "artifacts_sha256": dict(evidence.report["artifact_sha256"]),
    }


def _semantic_evidence_payload(
    evidence: SemanticEvidence,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "manifest": _file_reference(evidence.manifest_path, project_root),
        "font": _file_reference(evidence.font_path, project_root),
        "blank_render_proof": _file_reference(
            evidence.blank_proof_path, project_root
        ),
    }


def build_visual_review(
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    reviewer_name: str,
    reviewer_role: str,
    reviewed_at: str,
    confirmation: str,
) -> dict[str, Any]:
    """Build a per-glyph PASS record after exact human attestation."""

    reviewer_name = _nonempty_string(
        reviewer_name, where="reviewer_name"
    )
    reviewer_role = _nonempty_string(
        reviewer_role, where="reviewer_role"
    )
    reviewed_at = _require_rfc3339_utc(reviewed_at, where="reviewed_at")
    required_confirmation = (
        REVIEW_CONFIRMATION
        if batch.batch_kind == "raster-outline"
        else SEMANTIC_REVIEW_CONFIRMATION
    )
    if confirmation != required_confirmation:
        _fail(
            batch.batch_id,
            "record-review requires the exact explicit confirmation",
        )
    if batch.batch_kind == "raster-outline":
        evidence = visible_evidence(
            project_root=project_root,
            repertoire=repertoire,
            batch=batch,
        )
        evidence_path = evidence.report_path
        evidence_hash = evidence.report_sha256
        proof_references = evidence.proof_references
        checks = VISIBLE_REVIEW_CHECKS
        polarities: Sequence[str] = VISUAL_POLARITIES
        notes = (
            "PASS: identity, simple outline, exact metrics, profile invariants, "
            "zero micro edges/thorns, and all five sizes were explicitly reviewed."
        )
    else:
        semantic = semantic_evidence(
            project_root=project_root,
            repertoire=repertoire,
            batch=batch,
        )
        evidence_path = semantic.manifest_path
        evidence_hash = semantic.manifest_sha256
        proof_references = semantic.proof_references
        checks = SEMANTIC_REVIEW_CHECKS
        polarities = ()
        notes = (
            "PASS: empty glyf, exact semantic metrics/relations, and zero ink "
            "at all five sizes were explicitly reviewed."
        )
    proofs = [
        {**dict(reference), "decision": "PASS"}
        for reference in proof_references
    ]
    glyphs = [
        {
            "authoring_rank": glyph.authoring_rank,
            "character": glyph.character,
            "codepoint": glyph.codepoint_label,
            "decision": "PASS",
            "notes": notes,
        }
        for glyph in batch.glyphs
    ]
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "record_type": VISUAL_REVIEW_RECORD_TYPE,
        "review_state": "approved",
        "batch_id": batch.batch_id,
        "batch_kind": batch.batch_kind,
        "reviewer": {
            "name": reviewer_name,
            "role": reviewer_role,
        },
        "reviewed_at": reviewed_at,
        "attestation": required_confirmation,
        "evidence": {
            "path": _project_relative(evidence_path, project_root),
            "sha256": evidence_hash,
        },
        "scope": {
            "all_glyphs_reviewed": True,
            "checks": list(checks),
            "sizes_px": list(SMALL_SIZE_PIXELS),
            "polarities": list(polarities),
        },
        "proofs": proofs,
        "glyphs": glyphs,
        "summary": {
            "glyph_count": len(batch.glyphs),
            "pass_count": len(batch.glyphs),
            "reject_count": 0,
            "rejected_codepoints": [],
        },
    }


def _review_path(
    project_root: Path,
    batch: RepertoireBatch,
) -> Path:
    return (
        project_root.resolve()
        / "sources/imagegen/vector-reviews"
        / f"{batch.batch_id}.vector-review.json"
    )


def _validate_visual_review(
    path: Path,
    *,
    project_root: Path,
    batch: RepertoireBatch,
    evidence_path: Path,
    evidence_sha256: str,
    proof_references: Sequence[Mapping[str, str]],
) -> tuple[str, str]:
    payload = _read_json_object(path, label="visual review")
    top = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "review_state",
            "batch_id",
            "batch_kind",
            "reviewer",
            "reviewed_at",
            "attestation",
            "evidence",
            "scope",
            "proofs",
            "glyphs",
            "summary",
        },
        where=str(path),
    )
    if top["schema_version"] != APPROVAL_SCHEMA_VERSION:
        _fail(path, f"schema_version must be {APPROVAL_SCHEMA_VERSION}")
    if top["record_type"] != VISUAL_REVIEW_RECORD_TYPE:
        _fail(path, f"record_type must be {VISUAL_REVIEW_RECORD_TYPE!r}")
    if top["review_state"] != "approved":
        _fail(path, "review_state must be approved")
    if top["batch_id"] != batch.batch_id or top["batch_kind"] != batch.batch_kind:
        _fail(path, "visual review batch identity changed")
    reviewer = _exact_keys(
        top["reviewer"], {"name", "role"}, where=f"{path}: reviewer"
    )
    reviewer_name = _nonempty_string(
        reviewer["name"], where=f"{path}: reviewer.name"
    )
    _nonempty_string(reviewer["role"], where=f"{path}: reviewer.role")
    reviewed_at = _require_rfc3339_utc(
        top["reviewed_at"], where=f"{path}: reviewed_at"
    )
    expected_attestation = (
        REVIEW_CONFIRMATION
        if batch.batch_kind == "raster-outline"
        else SEMANTIC_REVIEW_CONFIRMATION
    )
    if top["attestation"] != expected_attestation:
        _fail(path, "visual-review attestation changed")
    evidence = _exact_keys(
        top["evidence"], {"path", "sha256"}, where=f"{path}: evidence"
    )
    if evidence != {
        "path": _project_relative(evidence_path, project_root),
        "sha256": evidence_sha256,
    }:
        _fail(path, "visual-review evidence pin changed")
    if sha256_path(evidence_path) != evidence_sha256:
        _fail(path, "review evidence changed during validation")
    checks = (
        VISIBLE_REVIEW_CHECKS
        if batch.batch_kind == "raster-outline"
        else SEMANTIC_REVIEW_CHECKS
    )
    polarities = (
        list(VISUAL_POLARITIES)
        if batch.batch_kind == "raster-outline"
        else []
    )
    scope = _exact_keys(
        top["scope"],
        {"all_glyphs_reviewed", "checks", "sizes_px", "polarities"},
        where=f"{path}: scope",
    )
    if scope != {
        "all_glyphs_reviewed": True,
        "checks": list(checks),
        "sizes_px": list(SMALL_SIZE_PIXELS),
        "polarities": polarities,
    }:
        _fail(path, "visual-review scope changed")
    expected_proofs = [
        {**dict(reference), "decision": "PASS"}
        for reference in proof_references
    ]
    if top["proofs"] != expected_proofs:
        _fail(path, "visual-review proof pins changed")
    for index, proof in enumerate(expected_proofs):
        relative = _relative_posix_path(
            proof["path"], where=f"{path}: proofs[{index}].path"
        )
        proof_path = _resolve_regular_file(
            project_root,
            relative,
            where=f"{path}: proofs[{index}].path",
        )
        if sha256_path(proof_path) != proof["sha256"]:
            _fail(path, f"visual-review proof {index} hash mismatch")
    raw_glyphs = top["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != len(batch.glyphs):
        _fail(path, "visual-review glyph count changed")
    seen: set[int] = set()
    for index, (raw, expected) in enumerate(
        zip(raw_glyphs, batch.glyphs, strict=True)
    ):
        where = f"{path}: glyphs[{index}]"
        record = _exact_keys(
            raw,
            {
                "authoring_rank",
                "character",
                "codepoint",
                "decision",
                "notes",
            },
            where=where,
        )
        if record["authoring_rank"] != expected.authoring_rank:
            _fail(where, "authoring_rank changed")
        if (
            record["character"] != expected.character
            or record["codepoint"] != expected.codepoint_label
        ):
            _fail(where, "glyph identity changed")
        if record["decision"] != "PASS":
            _fail(where, "every glyph decision must be PASS")
        _nonempty_string(record["notes"], where=f"{where}.notes")
        if expected.codepoint in seen:
            _fail(where, "duplicate reviewed glyph")
        seen.add(expected.codepoint)
    summary = _exact_keys(
        top["summary"],
        {"glyph_count", "pass_count", "reject_count", "rejected_codepoints"},
        where=f"{path}: summary",
    )
    count = len(batch.glyphs)
    if summary != {
        "glyph_count": count,
        "pass_count": count,
        "reject_count": 0,
        "rejected_codepoints": [],
    }:
        _fail(path, "visual-review summary changed")
    return reviewer_name, reviewed_at


def build_approval(
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    approver_name: str,
    approved_at: str,
    confirmation: str,
) -> dict[str, Any]:
    approver_name = _nonempty_string(
        approver_name, where="approver_name"
    )
    approved_at = _require_rfc3339_utc(approved_at, where="approved_at")
    if confirmation != AUTHORIZATION_CONFIRMATION:
        _fail(
            batch.batch_id,
            "authorize requires the exact explicit release confirmation",
        )
    review_path = _review_path(project_root, batch)
    if not review_path.is_file():
        _fail(batch.batch_id, "visual-review record is missing")
    common: dict[str, Any] = {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "record_type": APPROVAL_RECORD_TYPE,
        "approval_state": "approved",
        "batch_id": batch.batch_id,
        "batch_kind": batch.batch_kind,
        "repertoire": _approval_repertoire_payload(repertoire, batch),
    }
    if batch.batch_kind == "raster-outline":
        visible = visible_evidence(
            project_root=project_root,
            repertoire=repertoire,
            batch=batch,
        )
        common["source"] = _visible_source_payload(
            visible, project_root=project_root
        )
        common["vector_build"] = _vector_build_payload(
            visible, project_root=project_root
        )
    else:
        semantic = semantic_evidence(
            project_root=project_root,
            repertoire=repertoire,
            batch=batch,
        )
        common["semantic_evidence"] = _semantic_evidence_payload(
            semantic, project_root=project_root
        )
    common["visual_review"] = _file_reference(review_path, project_root)
    common["authorization"] = {
        "decision": "APPROVED",
        "approver": approver_name,
        "approved_at": approved_at,
        "attestation": AUTHORIZATION_CONFIRMATION,
    }
    return common


def _validate_approval_source(
    value: Any,
    *,
    evidence: VisibleEvidence,
    project_root: Path,
    where: str,
) -> None:
    expected = _visible_source_payload(evidence, project_root=project_root)
    _exact_keys(value, expected, where=where)
    if value != expected:
        _fail(where, "source evidence pins changed")


def _validate_vector_build_reference(
    value: Any,
    *,
    evidence: VisibleEvidence,
    project_root: Path,
    where: str,
) -> None:
    expected = _vector_build_payload(evidence, project_root=project_root)
    _exact_keys(value, expected, where=where)
    if value != expected:
        _fail(where, "vector-build report/artifact pins changed")


def _validate_semantic_evidence_reference(
    value: Any,
    *,
    evidence: SemanticEvidence,
    project_root: Path,
    where: str,
) -> None:
    expected = _semantic_evidence_payload(evidence, project_root=project_root)
    _exact_keys(value, expected, where=where)
    if value != expected:
        _fail(where, "semantic evidence pins changed")


def validate_approval(
    approval_path: Path,
    *,
    project_root: Path = ROOT,
    repertoire: Repertoire | None = None,
) -> ValidatedApproval:
    """Validate one approval and all transitively referenced evidence."""

    project_root = project_root.resolve()
    repertoire = repertoire or load_frozen_repertoire(project_root)
    if approval_path.is_symlink():
        _fail(approval_path, "approval symlinks are forbidden")
    approval_path = approval_path.resolve()
    expected_parent = project_root / "sources/imagegen/approvals"
    if approval_path.parent != expected_parent:
        _fail(approval_path, f"approval must be directly below {expected_parent}")
    if approval_path.is_symlink() or not approval_path.is_file():
        _fail(approval_path, "approval must be a regular non-symlink file")
    payload = _read_json_object(approval_path, label="approval")
    batch_id, number = _canonical_batch_id(
        payload.get("batch_id"), where=f"{approval_path}: batch_id"
    )
    batch = repertoire.batches[number - 1]
    if batch.batch_id != batch_id:
        _fail(approval_path, "batch_id does not match frozen repertoire")
    if approval_path.name != f"{batch.batch_id}.approval.json":
        _fail(approval_path, "approval filename/batch_id mismatch")
    common_keys = {
        "schema_version",
        "record_type",
        "approval_state",
        "batch_id",
        "batch_kind",
        "repertoire",
        "visual_review",
        "authorization",
    }
    branch_keys = (
        {"source", "vector_build"}
        if batch.batch_kind == "raster-outline"
        else {"semantic_evidence"}
    )
    top = _exact_keys(
        payload, common_keys | branch_keys, where=str(approval_path)
    )
    if top["schema_version"] != APPROVAL_SCHEMA_VERSION:
        _fail(
            approval_path,
            f"schema_version must be {APPROVAL_SCHEMA_VERSION}",
        )
    if top["record_type"] != APPROVAL_RECORD_TYPE:
        _fail(approval_path, f"record_type must be {APPROVAL_RECORD_TYPE!r}")
    if top["approval_state"] != "approved":
        _fail(approval_path, "approval_state must be approved")
    if top["batch_kind"] != batch.batch_kind:
        _fail(approval_path, "batch_kind does not match frozen repertoire")
    _validate_approval_repertoire(
        top["repertoire"],
        repertoire=repertoire,
        batch=batch,
        where=f"{approval_path}: repertoire",
    )

    visible: VisibleEvidence | None = None
    semantic: SemanticEvidence | None = None
    if batch.batch_kind == "raster-outline":
        visible = visible_evidence(
            project_root=project_root,
            repertoire=repertoire,
            batch=batch,
        )
        _validate_approval_source(
            top["source"],
            evidence=visible,
            project_root=project_root,
            where=f"{approval_path}: source",
        )
        _validate_vector_build_reference(
            top["vector_build"],
            evidence=visible,
            project_root=project_root,
            where=f"{approval_path}: vector_build",
        )
        review_evidence_path = visible.report_path
        review_evidence_hash = visible.report_sha256
        proof_references = visible.proof_references
    else:
        semantic = semantic_evidence(
            project_root=project_root,
            repertoire=repertoire,
            batch=batch,
        )
        _validate_semantic_evidence_reference(
            top["semantic_evidence"],
            evidence=semantic,
            project_root=project_root,
            where=f"{approval_path}: semantic_evidence",
        )
        review_evidence_path = semantic.manifest_path
        review_evidence_hash = semantic.manifest_sha256
        proof_references = semantic.proof_references

    expected_review_relative = PurePosixPath(
        f"sources/imagegen/vector-reviews/{batch.batch_id}.vector-review.json"
    )
    review_path, review_hash = _reference(
        top["visual_review"],
        where=f"{approval_path}: visual_review",
        project_root=project_root,
        expected_path=expected_review_relative,
    )
    reviewer_name, reviewed_at = _validate_visual_review(
        review_path,
        project_root=project_root,
        batch=batch,
        evidence_path=review_evidence_path,
        evidence_sha256=review_evidence_hash,
        proof_references=proof_references,
    )
    if sha256_path(review_path) != review_hash:
        _fail(approval_path, "visual review changed during validation")

    authorization = _exact_keys(
        top["authorization"],
        {"decision", "approver", "approved_at", "attestation"},
        where=f"{approval_path}: authorization",
    )
    if authorization["decision"] != "APPROVED":
        _fail(approval_path, "authorization.decision must be APPROVED")
    if authorization["attestation"] != AUTHORIZATION_CONFIRMATION:
        _fail(approval_path, "authorization attestation changed")
    approver_name = _nonempty_string(
        authorization["approver"],
        where=f"{approval_path}: authorization.approver",
    )
    approved_at = _require_rfc3339_utc(
        authorization["approved_at"],
        where=f"{approval_path}: authorization.approved_at",
    )
    if approved_at < reviewed_at:
        _fail(approval_path, "authorization cannot predate visual review")
    return ValidatedApproval(
        approval_path=approval_path,
        approval_sha256=sha256_path(approval_path),
        repertoire=repertoire,
        batch=batch,
        reviewer_name=reviewer_name,
        reviewed_at=reviewed_at,
        approver_name=approver_name,
        approved_at=approved_at,
        visible_evidence=visible,
        semantic_evidence=semantic,
    )


def validate_complete_approval_set(
    approval_paths: Sequence[Path],
    *,
    project_root: Path = ROOT,
) -> tuple[ValidatedApproval, ...]:
    """Require exactly one valid approval for every non-Han batch."""

    if not approval_paths:
        _fail("approval set", "all 206 canonical approval paths are required")
    by_batch: dict[str, Path] = {}
    for path in approval_paths:
        name = path.name
        suffix = ".approval.json"
        if not name.endswith(suffix):
            _fail(path, "approval filename must end in .approval.json")
        batch_id = name.removesuffix(suffix)
        _canonical_batch_id(batch_id, where=str(path))
        if batch_id in by_batch:
            _fail("approval set", f"duplicate approval for {batch_id}")
        by_batch[batch_id] = path
    expected = {f"nonhan-{number:04d}" for number in range(1, TOTAL_BATCHES + 1)}
    actual = set(by_batch)
    if actual != expected:
        _fail(
            "approval set",
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}",
        )
    repertoire = load_frozen_repertoire(project_root)
    return tuple(
        validate_approval(
            by_batch[f"nonhan-{number:04d}"],
            project_root=project_root,
            repertoire=repertoire,
        )
        for number in range(1, TOTAL_BATCHES + 1)
    )


def discover_approval_paths(
    directory: Path,
    *,
    project_root: Path = ROOT,
) -> tuple[Path, ...]:
    directory = directory.resolve()
    expected = project_root.resolve() / "sources/imagegen/approvals"
    if directory != expected:
        _fail(directory, f"approval directory must be exactly {expected}")
    if not directory.is_dir():
        _fail(directory, "approval directory does not exist")
    paths = tuple(
        sorted(
            directory.glob(
                "nonhan-[0-9][0-9][0-9][0-9].approval.json"
            )
        )
    )
    extra = sorted(
        path.name
        for path in directory.glob("nonhan-*.approval.json")
        if path not in paths
    )
    if extra:
        _fail(directory, f"noncanonical approval filenames: {extra}")
    return paths


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root; defaults to this repository",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser(
        "validate", help="validate one non-Han approval"
    )
    validate.add_argument("approval", type=Path)
    complete = subparsers.add_parser(
        "validate-complete", help="validate the exact 206-approval set"
    )
    complete.add_argument(
        "--directory",
        type=Path,
        default=None,
        help="canonical approval directory; defaults below project root",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "validate":
            validate_approval(
                args.approval,
                project_root=args.project_root,
            )
            print(args.approval)
        else:
            directory = args.directory or (
                args.project_root / "sources/imagegen/approvals"
            )
            paths = discover_approval_paths(
                directory, project_root=args.project_root
            )
            validated = validate_complete_approval_set(
                paths, project_root=args.project_root
            )
            print(f"validated {len(validated)} non-Han approvals")
    except NonHanApprovalError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
