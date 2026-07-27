#!/usr/bin/env python3
"""Build one reviewed-metrics non-Han imagegen batch.

This is deliberately independent from the frozen common-Han pipeline.  It
reuses only the pixel-evidenced grid detector and the audited
Potrace/cu2qu/outline-cleanup primitives.  The v2 descriptor carries complete
repertoire records and an explicit metric contract for every visible glyph;
the builder never reads the legacy authored-source tree or imports an existing font.

The pipeline is a batch/vector proof stage, not the final family merger.
Outputs remain ``Unreviewed`` and are written below
``build/imagegen/imagegen-nonhan-NNNN``.  A later approval gate may copy only
hash-pinned outlines, metrics, profiles, and anchor candidates into the formal
family.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import tempfile
import unicodedata
from typing import Any, Mapping, Sequence

import freetype
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path.parser import parse_path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from scripts import imagegen_font_pipeline as han_pipeline


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
DEFAULT_DESCRIPTOR = IMAGEGEN_ROOT / "batches/nonhan-0001.source.json"
DEFAULT_OUTPUT_ROOT = ROOT / "build/imagegen"

PIPELINE_ID = "imagegen-raster-potrace-quadratic-nonhan-v3"
SOURCE_TYPE = "imagegen-nonhan-grid-v2"
SCHEMA_VERSION = 2
ROWS = 4
COLUMNS = 4
GRID_CAPACITY = ROWS * COLUMNS
UPM = 1024
VERTICAL_ORIGIN_Y = 880
ASCENDER = 930
DESCENDER = -210
LINE_GAP = 0
REPRODUCIBLE_HEAD_TIMESTAMP = 2_082_844_800
SMALL_SIZE_PIXELS = (12, 16, 20, 32, 56)
DEFAULT_PROOF_COVERAGE_DIVISOR = 6
MARK_PROOF_COVERAGE_DIVISOR = 10
MINIMUM_PROOF_COVERAGE_PIXELS = 2

GENERIC_FONT_X_MIN = 32
GENERIC_FONT_X_MAX = 992
GENERIC_FONT_Y_MIN = -40
GENERIC_FONT_Y_MAX = 920
HALFWIDTH_X_MIN = 32
HALFWIDTH_X_MAX = 480
MARK_STACK_GAP = 24

GENERIC_MAX_INK_FRACTION = 0.30
DENSE_SOLID_MAX_INK_FRACTION = 0.34
EDGE_MAX_INK_FRACTION = 1.0
EDGE_CONTACT_BAND = 4
EDGE_FONT_TOLERANCE = 8
SOURCE_BORDER_CLEARANCE = 2
GRID_RULE_INTERIOR_PADDING = 2

BATCH_ID_PATTERN = re.compile(r"nonhan-[0-9]{4}")
SOURCE_BATCH_ID_PATTERN = re.compile(r"imagegen-(nonhan-[0-9]{4})")
CODEPOINT_PATTERN = re.compile(r"U\+[0-9A-F]{4,6}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
CCC_MARK_CLASS_PATTERN = re.compile(r"ccc-(0|[1-9][0-9]{0,2})")

# Exactly the visible nonspacing-mark requirement.  U+034F is semantic-empty
# and therefore never enters this raster pipeline.  U+302E/U+302F are spacing
# combining marks (Mc) and intentionally are not members of this set.
ZERO_ADVANCE_VISIBLE_MARKS = frozenset(
    (
        *(codepoint for codepoint in range(0x0300, 0x0358) if codepoint != 0x034F),
        *range(0x035D, 0x0370),
        *range(0x302A, 0x302E),
        0x3099,
        0x309A,
    )
)
if len(ZERO_ADVANCE_VISIBLE_MARKS) != 112:
    raise RuntimeError("zero-advance visible-mark contract must contain 112 scalars")

SPACING_COMBINING_MARKS = frozenset({0x302E, 0x302F})
TWO_EM_VERTICAL_ADVANCE = frozenset({0x3031, 0x3032})

# These two Unicode identities are deliberately solid and occupy slightly
# more than the generic 30% source-ink ceiling. This is an exact semantic
# profile, not a fallback: all other non-edge glyphs retain the generic cap.
DENSE_SOLID_GLYPHS: Mapping[int, str] = {
    0x25FC: "BLACK MEDIUM SQUARE",
    0x2617: "BLACK SHOGI PIECE",
}
SEGMENTATION_INK_FRACTION_LIMITS: Mapping[str, float] = {
    "generic": GENERIC_MAX_INK_FRACTION,
    "dense-solid": DENSE_SOLID_MAX_INK_FRACTION,
    "edge": EDGE_MAX_INK_FRACTION,
}

# A repertoire profile names design semantics; the transform profile controls
# only raster-to-font coordinate mapping.  The report exposes exactly the eight
# frozen repertoire profiles.  Additional named aliases remain explicit for
# direct schema-level validation and never appear as an inferred fallback.
REPERTOIRE_PROFILE_TRANSFORMS: Mapping[str, str] = {
    "fullwidth": "fullwidth",
    "cjk-wide": "fullwidth",
    "proportional": "proportional",
    "tabular-digit": "proportional",
    "halfwidth": "halfwidth",
    "nonspacing-mark": "mark",
    "box-drawing": "edge",
    "block-element": "edge",
}
PROFILE_TRANSFORMS: Mapping[str, str] = {
    **REPERTOIRE_PROFILE_TRANSFORMS,
    "generic-cjk": "fullwidth",
    "kana": "fullwidth",
    "bopomofo": "fullwidth",
    "cjk-punctuation": "fullwidth",
    "generic-symbol": "fullwidth",
    "latin": "proportional",
    "greek": "proportional",
    "ipa": "proportional",
}

PROFILE_SIDE_BEARINGS: Mapping[str, tuple[int, int]] = {
    "fullwidth": (32, 32),
    "cjk-wide": (32, 32),
    "generic-cjk": (32, 32),
    "kana": (32, 32),
    "bopomofo": (32, 32),
    "cjk-punctuation": (32, 32),
    "generic-symbol": (32, 32),
    "halfwidth": (32, 32),
    "proportional": (48, 48),
    "latin": (48, 48),
    "greek": (48, 48),
    "ipa": (48, 48),
    "tabular-digit": (56, 56),
    "nonspacing-mark": (0, 0),
    "box-drawing": (0, 0),
    "block-element": (0, 0),
}
FIXED_PROFILE_ADVANCES: Mapping[str, int] = {
    "fullwidth": UPM,
    "cjk-wide": UPM,
    "generic-cjk": UPM,
    "kana": UPM,
    "bopomofo": UPM,
    "cjk-punctuation": UPM,
    "generic-symbol": UPM,
    "halfwidth": UPM // 2,
    "tabular-digit": 620,
    "nonspacing-mark": 0,
    "box-drawing": UPM,
    "block-element": UPM,
}
COPYBOOK_VALIDATIONS = (
    "exact-cmap-hit",
    "non-notdef-glyph-name",
    "non-empty-distinct-outline",
    "non-empty-pillow-raster",
)
DESCRIPTOR_GLYPH_FIELDS = {
    "canonical_rank",
    "authoring_rank",
    "character",
    "codepoint",
    "name",
    "gc",
    "outline_required",
    "profile_id",
    "metrics",
    "copybook_reference",
}


class NonHanPipelineError(RuntimeError):
    """A v3 descriptor or generated artifact violated the fail-closed contract."""


@dataclass(frozen=True)
class HorizontalAdvance:
    kind: str
    value: int | None = None
    reference_codepoint: int | None = None


@dataclass(frozen=True)
class GlyphMetricsPolicy:
    horizontal_advance: HorizontalAdvance
    vertical_advance: int
    left_side_bearing: int | None
    right_side_bearing: int | None
    mark_class: str | None


@dataclass(frozen=True)
class GlyphSpec:
    character: str
    codepoint: int
    codepoint_label: str
    unicode_name: str
    profile_id: str
    transform_profile: str
    metrics: GlyphMetricsPolicy
    source_record: Mapping[str, Any]


@dataclass(frozen=True)
class SourceDescriptor:
    path: Path
    project_root: Path
    batch_id: str
    state: str
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
    glyphs: tuple[GlyphSpec, ...]
    cell_slots: tuple[GlyphSpec | None, ...]
    empty_grid_cells: int
    review: Mapping[str, str]
    source_sha256: str


@dataclass(frozen=True)
class SegmentedNonHanCell:
    spec: GlyphSpec
    row: int
    column: int
    source_box: tuple[int, int, int, int]
    source_ink_bbox: tuple[float, float, float, float]
    core_component_count: int
    core_pixel_count: int
    ink_fraction: float
    segmentation_profile: str
    edge_contacts: Mapping[str, bool]
    edge_contact_pixels: Mapping[str, int]
    cleaned: Image.Image


@dataclass
class VectorizedGlyph:
    spec: GlyphSpec
    cell: SegmentedNonHanCell
    name: str
    outline: Glyph
    contour_count: int
    point_count: int
    outer_contour_count: int
    counter_count: int
    minimum_control_edge: float
    quantization_duplicate_points_removed: int
    maximum_quantization_collapse: float
    micro_thorn_points_removed: int
    maximum_micro_thorn_displacement: float
    coincident_flank_control_points_removed: int
    micro_edge_count: int
    acute_micro_turn_count: int
    pre_metric_bounds: tuple[float, float, float, float]
    horizontal_advance: int | None = None
    left_side_bearing: int | None = None
    right_side_bearing: int | None = None
    vertical_advance: int | None = None
    top_side_bearing: int | None = None
    mark_class: str | None = None
    anchors_candidate: Mapping[str, Any] | None = None
    vector_edge_contacts: Mapping[str, bool] | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NonHanPipelineError(f"{path}: cannot read JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise NonHanPipelineError(f"{path}: expected a JSON object")
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _one_scalar(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or len(value) != 1:
        raise NonHanPipelineError(f"{where}: expected exactly one Unicode scalar")
    codepoint = ord(value)
    if 0xD800 <= codepoint <= 0xDFFF:
        raise NonHanPipelineError(f"{where}: surrogate scalars are forbidden")
    return value


def _integer(
    value: Any,
    *,
    where: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise NonHanPipelineError(f"{where}: expected an integer")
    if not minimum <= value <= maximum:
        raise NonHanPipelineError(
            f"{where}: expected {minimum}..{maximum}, got {value}"
        )
    return value


def _codepoint(value: Any, *, where: str) -> int:
    if not isinstance(value, str) or CODEPOINT_PATTERN.fullmatch(value) is None:
        raise NonHanPipelineError(
            f"{where}: expected uppercase U+XXXX codepoint notation"
        )
    codepoint = int(value[2:], 16)
    if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
        raise NonHanPipelineError(f"{where}: invalid Unicode scalar")
    if value != f"U+{codepoint:04X}":
        raise NonHanPipelineError(f"{where}: codepoint notation is not canonical")
    return codepoint


def _horizontal_advance(value: Any, *, where: str) -> HorizontalAdvance:
    if not isinstance(value, dict):
        raise NonHanPipelineError(f"{where}: expected an object")
    kind = value.get("kind")
    if kind == "fixed":
        if set(value) != {"kind", "value"}:
            raise NonHanPipelineError(f"{where}: fixed advance fields are not exact")
        return HorizontalAdvance(
            kind=kind,
            value=_integer(
                value["value"], where=f"{where}.value", minimum=0, maximum=4096
            ),
        )
    if kind == "reference":
        if set(value) != {"kind", "codepoint"}:
            raise NonHanPipelineError(
                f"{where}: reference advance fields are not exact"
            )
        return HorizontalAdvance(
            kind=kind,
            reference_codepoint=_codepoint(
                value["codepoint"], where=f"{where}.codepoint"
            ),
        )
    if kind == "source-proportional":
        if set(value) != {"kind"}:
            raise NonHanPipelineError(
                f"{where}: source-proportional fields are not exact"
            )
        return HorizontalAdvance(kind=kind)
    raise NonHanPipelineError(
        f"{where}: kind must be fixed, reference, or source-proportional"
    )


def _metrics_policy(
    value: Any,
    *,
    codepoint: int,
    profile_id: str,
    transform_profile: str,
    where: str,
) -> GlyphMetricsPolicy:
    if not isinstance(value, dict):
        raise NonHanPipelineError(f"{where}: expected an object")
    required = {"horizontal_advance", "vertical_advance", "side_bearings"}
    allowed = required | {"mark_class"}
    if not required <= set(value) or not set(value) <= allowed:
        raise NonHanPipelineError(
            f"{where}: required fields are horizontal_advance, "
            "vertical_advance, side_bearings; only mark_class is optional"
        )
    horizontal = _horizontal_advance(
        value["horizontal_advance"], where=f"{where}.horizontal_advance"
    )
    vertical_raw = value["vertical_advance"]
    if (
        not isinstance(vertical_raw, dict)
        or set(vertical_raw) != {"kind", "value"}
        or vertical_raw.get("kind") != "fixed"
    ):
        raise NonHanPipelineError(
            f"{where}.vertical_advance: only an exact fixed value is accepted"
        )
    vertical = _integer(
        vertical_raw["value"],
        where=f"{where}.vertical_advance.value",
        minimum=0,
        maximum=4096,
    )

    side_bearings = value["side_bearings"]
    if not isinstance(side_bearings, dict) or set(side_bearings) != {
        "left",
        "right",
    }:
        raise NonHanPipelineError(
            f"{where}.side_bearings: expected exact fixed left/right values"
        )
    left = _integer(
        side_bearings["left"],
        where=f"{where}.side_bearings.left",
        minimum=-512,
        maximum=1024,
    )
    right = _integer(
        side_bearings["right"],
        where=f"{where}.side_bearings.right",
        minimum=-512,
        maximum=1024,
    )

    mark_class = value.get("mark_class")
    if (
        mark_class is not None
        and (
            not isinstance(mark_class, str)
            or CCC_MARK_CLASS_PATTERN.fullmatch(mark_class) is None
        )
    ):
        raise NonHanPipelineError(
            f"{where}.mark_class: expected canonical ccc-N notation"
        )

    is_zero_mark = codepoint in ZERO_ADVANCE_VISIBLE_MARKS
    if is_zero_mark:
        if transform_profile != "mark":
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: zero-advance visible mark must use "
                "profile_id 'nonspacing-mark'"
            )
        if horizontal.kind != "fixed" or horizontal.value != 0 or vertical != 0:
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: nonspacing marks require fixed horizontal "
                "and vertical advance 0"
            )
        if (left, right) != (0, 0):
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: nonspacing marks require zero policy bearings"
            )
        expected_mark_class = f"ccc-{unicodedata.combining(chr(codepoint))}"
        if mark_class != expected_mark_class:
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: mark_class must be {expected_mark_class!r}"
            )
    elif transform_profile == "mark":
        raise NonHanPipelineError(
            f"U+{codepoint:04X}: is not one of the 112 visible nonspacing marks"
        )
    elif mark_class is not None:
        raise NonHanPipelineError(
            f"U+{codepoint:04X}: mark_class is only valid for nonspacing marks"
        )

    if codepoint == 0x034F:
        raise NonHanPipelineError(
            "U+034F is semantic-empty and must not enter the raster pipeline"
        )
    if codepoint in SPACING_COMBINING_MARKS:
        if horizontal.kind != "fixed" or horizontal.value != UPM:
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: spacing Hangul tone mark must advance {UPM}"
            )
        if transform_profile == "mark":
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: spacing Hangul tone mark is not a GDEF mark"
            )

    if horizontal.kind == "source-proportional":
        if profile_id not in {"proportional", "latin", "greek", "ipa"}:
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: source-proportional requires an audited "
                "proportional profile"
            )

    expected_bearings = PROFILE_SIDE_BEARINGS.get(profile_id)
    if expected_bearings is not None and (left, right) != expected_bearings:
        raise NonHanPipelineError(
            f"U+{codepoint:04X}: {profile_id} requires policy bearings "
            f"{expected_bearings[0]}/{expected_bearings[1]}"
        )
    expected_advance = FIXED_PROFILE_ADVANCES.get(profile_id)
    if expected_advance is not None:
        if (
            horizontal.kind != "fixed"
            or horizontal.value != expected_advance
        ):
            raise NonHanPipelineError(
                f"U+{codepoint:04X}: {profile_id} requires fixed advance "
                f"{expected_advance}"
            )
    if codepoint in TWO_EM_VERTICAL_ADVANCE:
        expected_vertical = UPM * 2
    else:
        expected_vertical = 0 if transform_profile == "mark" else UPM
    if vertical != expected_vertical:
        raise NonHanPipelineError(
            f"U+{codepoint:04X}: {profile_id} requires vertical advance "
            f"{expected_vertical}"
        )

    return GlyphMetricsPolicy(
        horizontal_advance=horizontal,
        vertical_advance=vertical,
        left_side_bearing=left,
        right_side_bearing=right,
        mark_class=str(mark_class) if mark_class is not None else None,
    )


def _glyph_spec(value: Any, *, where: str) -> GlyphSpec:
    if not isinstance(value, dict):
        raise NonHanPipelineError(f"{where}: expected a repertoire glyph object")
    if set(value) != DESCRIPTOR_GLYPH_FIELDS:
        raise NonHanPipelineError(
            f"{where}: glyph fields must be exactly "
            f"{sorted(DESCRIPTOR_GLYPH_FIELDS)}"
        )
    character = _one_scalar(value["character"], where=f"{where}.character")
    codepoint = _codepoint(value["codepoint"], where=f"{where}.codepoint")
    if ord(character) != codepoint:
        raise NonHanPipelineError(f"{where}: character/codepoint mismatch")
    unicode_name = value["name"]
    if not isinstance(unicode_name, str) or not unicode_name:
        raise NonHanPipelineError(f"{where}.name: expected nonempty text")
    # Unicode database versions can differ on newly assigned characters.  For
    # assigned scalars known to this runtime, however, a wrong identity is fatal.
    runtime_name = unicodedata.name(character, None)
    if runtime_name is not None and unicode_name != runtime_name:
        raise NonHanPipelineError(
            f"{where}.name: expected {runtime_name!r}, got {unicode_name!r}"
        )
    if value["gc"] != unicodedata.category(character):
        raise NonHanPipelineError(f"{where}.gc: Unicode general-category mismatch")
    _integer(
        value["canonical_rank"],
        where=f"{where}.canonical_rank",
        minimum=1,
        maximum=3060,
    )
    _integer(
        value["authoring_rank"],
        where=f"{where}.authoring_rank",
        minimum=1,
        maximum=3060,
    )
    if value["outline_required"] is not True:
        raise NonHanPipelineError(
            f"{where}: only visible outline-required records enter this pipeline"
        )
    profile_id = value["profile_id"]
    if not isinstance(profile_id, str) or profile_id not in PROFILE_TRANSFORMS:
        raise NonHanPipelineError(
            f"{where}.profile_id: unsupported profile {profile_id!r}"
        )
    transform_profile = PROFILE_TRANSFORMS[profile_id]
    metrics = _metrics_policy(
        value["metrics"],
        codepoint=codepoint,
        profile_id=profile_id,
        transform_profile=transform_profile,
        where=f"{where}.metrics",
    )
    reference = value["copybook_reference"]
    expected_reference_fields = {
        "role",
        "font_path",
        "font_sha256",
        "font_index",
        "postscript_name",
        "glyph_name",
        "validation",
    }
    if (
        not isinstance(reference, dict)
        or set(reference) != expected_reference_fields
        or reference.get("role")
        != "identity-reference-only-no-outline-import"
        or reference.get("validation") != list(COPYBOOK_VALIDATIONS)
    ):
        raise NonHanPipelineError(
            f"{where}.copybook_reference: reference evidence is not exact"
        )
    for field in ("font_path", "postscript_name", "glyph_name"):
        if not isinstance(reference[field], str) or not reference[field]:
            raise NonHanPipelineError(
                f"{where}.copybook_reference.{field}: expected nonempty text"
            )
    if (
        not isinstance(reference["font_sha256"], str)
        or SHA256_PATTERN.fullmatch(reference["font_sha256"]) is None
    ):
        raise NonHanPipelineError(
            f"{where}.copybook_reference.font_sha256: invalid SHA-256"
        )
    _integer(
        reference["font_index"],
        where=f"{where}.copybook_reference.font_index",
        minimum=0,
        maximum=65535,
    )
    return GlyphSpec(
        character=character,
        codepoint=codepoint,
        codepoint_label=f"U+{codepoint:04X}",
        unicode_name=unicode_name,
        profile_id=profile_id,
        transform_profile=transform_profile,
        metrics=metrics,
        source_record=dict(value),
    )


def load_source_descriptor(
    path: Path = DEFAULT_DESCRIPTOR,
    *,
    project_root: Path = ROOT,
) -> SourceDescriptor:
    """Load and strictly validate one embedded-repertoire descriptor v2."""

    project_root = project_root.resolve()
    path = path.resolve()
    imagegen_root = (project_root / "sources/imagegen").resolve()
    allowed_batch_root = imagegen_root / "batches"
    if not _is_relative_to(path, allowed_batch_root.resolve()):
        raise NonHanPipelineError(
            f"{path}: descriptor must remain below {allowed_batch_root}"
        )
    payload = _read_object(path)
    expected_top = {
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
    if set(payload) != expected_top:
        raise NonHanPipelineError(
            f"{path}: descriptor fields must be exactly {sorted(expected_top)}"
        )
    if payload["schema_version"] != SCHEMA_VERSION:
        raise NonHanPipelineError(
            f"{path}: schema_version must be {SCHEMA_VERSION}"
        )
    batch_id = payload["batch_id"]
    if not isinstance(batch_id, str):
        raise NonHanPipelineError(f"{path}: batch_id must be text")
    batch_match = SOURCE_BATCH_ID_PATTERN.fullmatch(batch_id)
    if batch_match is None:
        raise NonHanPipelineError(
            f"{path}: batch_id must match {SOURCE_BATCH_ID_PATTERN.pattern}"
        )
    repertoire_batch_id = batch_match.group(1)
    if path.name != f"{repertoire_batch_id}.source.json":
        raise NonHanPipelineError(f"{path}: descriptor filename/batch_id mismatch")
    if payload["state"] != "generated-unreviewed":
        raise NonHanPipelineError(
            f"{path}: state must remain 'generated-unreviewed'"
        )
    if payload["generator"] != "built-in-image_gen":
        raise NonHanPipelineError(
            f"{path}: generator must be 'built-in-image_gen'"
        )
    generator_call = payload["generator_call"]
    if (
        not isinstance(generator_call, str)
        or not generator_call
        or generator_call != generator_call.strip()
        or generator_call.startswith("<")
    ):
        raise NonHanPipelineError(
            f"{path}: generator_call must be non-placeholder provenance"
        )

    def exact_asset(
        value: Any,
        *,
        expected_manifest_path: str,
        allowed_root: Path,
        where: str,
    ) -> Path:
        if value != expected_manifest_path:
            raise NonHanPipelineError(
                f"{where}: expected {expected_manifest_path!r}"
            )
        manifest_path = PurePosixPath(value)
        if manifest_path.is_absolute() or "\\" in value:
            raise NonHanPipelineError(f"{where}: expected a relative POSIX path")
        resolved = path.parent.joinpath(*manifest_path.parts).resolve()
        if not _is_relative_to(resolved, allowed_root.resolve()):
            raise NonHanPipelineError(
                f"{where}: asset must remain below {allowed_root}"
            )
        if not resolved.is_file():
            raise NonHanPipelineError(f"{where}: asset does not exist")
        return resolved

    repertoire_record = payload["repertoire"]
    expected_repertoire_fields = {
        "path",
        "sha256",
        "repertoire_id",
        "batch_id",
    }
    if (
        not isinstance(repertoire_record, dict)
        or set(repertoire_record) != expected_repertoire_fields
        or repertoire_record.get("repertoire_id")
        != "clear-hand-tc-nonhan-3060-v1"
        or repertoire_record.get("batch_id") != repertoire_batch_id
    ):
        raise NonHanPipelineError(f"{path}: repertoire provenance is not exact")
    repertoire_hash = repertoire_record["sha256"]
    if (
        not isinstance(repertoire_hash, str)
        or SHA256_PATTERN.fullmatch(repertoire_hash) is None
    ):
        raise NonHanPipelineError(f"{path}: repertoire SHA-256 is invalid")
    repertoire_path = exact_asset(
        repertoire_record["path"],
        expected_manifest_path="../repertoires/nonhan-3060.json",
        allowed_root=imagegen_root / "repertoires",
        where=f"{path}: repertoire.path",
    )
    if _sha256(repertoire_path) != repertoire_hash:
        raise NonHanPipelineError(f"{path}: repertoire hash mismatch")
    repertoire_payload = _read_object(repertoire_path)
    if (
        repertoire_payload.get("schema_version") != 1
        or repertoire_payload.get("repertoire_id")
        != repertoire_record["repertoire_id"]
    ):
        raise NonHanPipelineError(f"{path}: repertoire identity mismatch")

    grid = payload["grid"]
    if not isinstance(grid, dict) or set(grid) != {
        "rows",
        "columns",
        "glyphs",
        "empty_grid_cells",
    }:
        raise NonHanPipelineError(f"{path}: grid fields are not exact")
    if grid["rows"] != ROWS or grid["columns"] != COLUMNS:
        raise NonHanPipelineError(f"{path}: only a {ROWS}x{COLUMNS} grid is accepted")
    empty_count = _integer(
        grid["empty_grid_cells"],
        where=f"{path}: grid.empty_grid_cells",
        minimum=0,
        maximum=GRID_CAPACITY - 1,
    )
    raw_glyphs = grid["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) + empty_count != GRID_CAPACITY:
        raise NonHanPipelineError(
            f"{path}: glyph records plus trailing empty cells must total {GRID_CAPACITY}"
        )
    glyphs = tuple(
        _glyph_spec(value, where=f"{path}: grid.glyphs[{index}]")
        for index, value in enumerate(raw_glyphs)
    )
    codepoints = [glyph.codepoint for glyph in glyphs]
    if len(set(codepoints)) != len(codepoints):
        raise NonHanPipelineError(f"{path}: duplicate codepoint in batch")
    tabular_values = {
        glyph.metrics.horizontal_advance.value
        for glyph in glyphs
        if glyph.profile_id == "tabular-digit"
    }
    if len(tabular_values) > 1:
        raise NonHanPipelineError(
            f"{path}: tabular-digit records must share one fixed advance"
        )
    for glyph in glyphs:
        reference = glyph.metrics.horizontal_advance.reference_codepoint
        if reference is not None and reference not in set(codepoints):
            raise NonHanPipelineError(
                f"{path}: {glyph.codepoint_label} advance reference "
                f"U+{reference:04X} is outside this hash-pinned batch"
            )

    repertoire_glyph_rows = repertoire_payload.get("glyphs")
    repertoire_batches = repertoire_payload.get("batches")
    if not isinstance(repertoire_glyph_rows, list) or not isinstance(
        repertoire_batches, list
    ):
        raise NonHanPipelineError(f"{path}: repertoire arrays are missing")
    repertoire_index = {
        row.get("codepoint"): row
        for row in repertoire_glyph_rows
        if isinstance(row, dict) and isinstance(row.get("codepoint"), str)
    }
    repertoire_batch = next(
        (
            row
            for row in repertoire_batches
            if isinstance(row, dict)
            and row.get("batch_id") == repertoire_batch_id
        ),
        None,
    )
    codepoint_labels = [glyph.codepoint_label for glyph in glyphs]
    if (
        repertoire_batch is None
        or repertoire_batch.get("batch_kind") != "raster-outline"
        or repertoire_batch.get("glyph_codepoints") != codepoint_labels
        or repertoire_batch.get("empty_grid_cells") != empty_count
    ):
        raise NonHanPipelineError(
            f"{path}: grid order does not match its hash-pinned repertoire batch"
        )
    for raw_glyph, glyph in zip(raw_glyphs, glyphs, strict=True):
        embedded_repertoire_record = dict(raw_glyph)
        embedded_repertoire_record.pop("copybook_reference")
        if repertoire_index.get(glyph.codepoint_label) != embedded_repertoire_record:
            raise NonHanPipelineError(
                f"{path}: embedded record for {glyph.codepoint_label} "
                "does not match the hash-pinned repertoire"
            )

    raster_value = payload["raster"]
    raster_hash = payload["raster_sha256"]
    if not isinstance(raster_hash, str) or SHA256_PATTERN.fullmatch(raster_hash) is None:
        raise NonHanPipelineError(f"{path}: raster_sha256 must be lowercase SHA-256")
    raster_path = exact_asset(
        raster_value,
        expected_manifest_path=f"../raster/{repertoire_batch_id}.png",
        allowed_root=imagegen_root / "raster",
        where=f"{path}: raster",
    )
    actual_hash = _sha256(raster_path)
    if actual_hash != raster_hash:
        raise NonHanPipelineError(
            f"{path}: raster hash mismatch: expected {raster_hash}, got {actual_hash}"
        )

    prompt_path = exact_asset(
        payload["prompt"],
        expected_manifest_path=f"../prompts/{repertoire_batch_id}.md",
        allowed_root=imagegen_root / "prompts",
        where=f"{path}: prompt",
    )

    def hashed_asset_record(
        value: Any,
        *,
        expected_path: str,
        expected_role: str,
        allowed_root: Path,
        where: str,
    ) -> tuple[Path, str]:
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "sha256", "role"}
            or value.get("role") != expected_role
            or not isinstance(value.get("sha256"), str)
            or SHA256_PATTERN.fullmatch(value["sha256"]) is None
        ):
            raise NonHanPipelineError(f"{where}: hash-pinned asset is not exact")
        asset = exact_asset(
            value["path"],
            expected_manifest_path=expected_path,
            allowed_root=allowed_root,
            where=f"{where}.path",
        )
        if _sha256(asset) != value["sha256"]:
            raise NonHanPipelineError(f"{where}: asset hash mismatch")
        return asset, value["sha256"]

    copybook_path, copybook_hash = hashed_asset_record(
        payload["copybook"],
        expected_path=f"../copybooks/{repertoire_batch_id}.png",
        expected_role="identity-reference-only-no-outline-import",
        allowed_root=imagegen_root / "copybooks",
        where=f"{path}: copybook",
    )
    style_reference_path, style_reference_hash = hashed_asset_record(
        payload["style_reference"],
        expected_path="../raster/common-0001.png",
        expected_role="style-only",
        allowed_root=imagegen_root / "raster",
        where=f"{path}: style_reference",
    )

    review = payload["review"]
    if not isinstance(review, dict) or review != {
        "identity": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }:
        raise NonHanPipelineError(
            f"{path}: source review must contain pending identity/raster/vector"
        )
    return SourceDescriptor(
        path=path,
        project_root=project_root,
        batch_id=batch_id,
        state="generated-unreviewed",
        raster_path=raster_path,
        raster_sha256=raster_hash,
        generator_call=generator_call,
        repertoire_path=repertoire_path,
        repertoire_sha256=repertoire_hash,
        prompt_path=prompt_path,
        prompt_sha256=_sha256(prompt_path),
        copybook_path=copybook_path,
        copybook_sha256=copybook_hash,
        style_reference_path=style_reference_path,
        style_reference_sha256=style_reference_hash,
        glyphs=glyphs,
        cell_slots=(*glyphs, *(None for _ in range(empty_count))),
        empty_grid_cells=empty_count,
        review={str(key): str(value) for key, value in review.items()},
        source_sha256=_sha256(path),
    )


def _normalized_ink_bbox(mask: np.ndarray) -> tuple[float, float, float, float]:
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        raise NonHanPipelineError("segmented cell contains no ink")
    height, width = mask.shape
    return (
        float(xs.min()) / width,
        1.0 - float(ys.max() + 1) / height,
        float(xs.max() + 1) / width,
        1.0 - float(ys.min()) / height,
    )


def _edge_counts(mask: np.ndarray, *, band: int = EDGE_CONTACT_BAND) -> dict[str, int]:
    band = min(band, max(1, min(mask.shape) // 8))
    return {
        "left": int(np.count_nonzero(mask[:, :band])),
        "right": int(np.count_nonzero(mask[:, -band:])),
        "top": int(np.count_nonzero(mask[:band, :])),
        "bottom": int(np.count_nonzero(mask[-band:, :])),
    }


def _clean_cell(
    crop: Image.Image,
    *,
    segmentation_profile: str,
    minimum_edge_contacts: int = 2,
) -> tuple[
    Image.Image,
    tuple[float, float, float, float],
    int,
    int,
    float,
    dict[str, bool],
    dict[str, int],
]:
    """Segment one rule-free cell interior under its declared profile."""

    if segmentation_profile not in SEGMENTATION_INK_FRACTION_LIMITS:
        raise NonHanPipelineError(
            f"unsupported segmentation profile {segmentation_profile!r}"
        )
    gray = np.asarray(crop.convert("L"), dtype=np.uint8).copy()
    if min(gray.shape) < 128:
        raise NonHanPipelineError("grid cell is too small for reliable segmentation")
    core = gray <= han_pipeline.INK_CORE_CEILING
    labels, label_count = ndimage.label(
        core, structure=np.ones((3, 3), dtype=np.uint8)
    )
    if label_count == 0:
        raise NonHanPipelineError("segmented cell contains no dark ink core")
    areas = np.bincount(labels.ravel())
    accepted_labels = np.flatnonzero(
        areas >= han_pipeline.INK_MIN_COMPONENT_AREA
    )
    accepted_labels = accepted_labels[accepted_labels != 0]
    if accepted_labels.size == 0:
        raise NonHanPipelineError(
            "segmented cell contains only sub-threshold raster speckles"
        )
    kept_core = np.isin(labels, accepted_labels)
    core_pixels = int(kept_core.sum())
    fraction = core_pixels / kept_core.size
    maximum = SEGMENTATION_INK_FRACTION_LIMITS[segmentation_profile]
    if not han_pipeline.INK_MIN_CELL_FRACTION <= fraction <= maximum:
        raise NonHanPipelineError(
            f"segmented ink fraction {fraction:.6f} is outside "
            f"{segmentation_profile} profile limits"
        )

    raw_edge_counts = _edge_counts(kept_core)
    contacts = {edge: count > 0 for edge, count in raw_edge_counts.items()}
    if segmentation_profile == "edge":
        if minimum_edge_contacts not in {0, 1, 2}:
            raise NonHanPipelineError(
                "edge profile minimum contact count must be 0, 1, or 2"
            )
        if sum(contacts.values()) < minimum_edge_contacts:
            raise NonHanPipelineError(
                "edge-profile source must connect to at least "
                f"{minimum_edge_contacts} cell "
                f"{'edge' if minimum_edge_contacts == 1 else 'edges'}"
            )
    else:
        clear = SOURCE_BORDER_CLEARANCE
        if (
            np.any(kept_core[:clear, :])
            or np.any(kept_core[-clear:, :])
            or np.any(kept_core[:, :clear])
            or np.any(kept_core[:, -clear:])
        ):
            raise NonHanPipelineError(
                "non-edge source touches the cell border; grid contamination "
                "or a wrong profile is likely"
            )

    support = ndimage.binary_dilation(
        kept_core, iterations=han_pipeline.INK_SUPPORT_DILATION
    )
    support &= gray <= han_pipeline.INK_SUPPORT_CEILING
    if segmentation_profile != "edge":
        clear = SOURCE_BORDER_CLEARANCE
        if (
            np.any(support[:clear, :])
            or np.any(support[-clear:, :])
            or np.any(support[:, :clear])
            or np.any(support[:, -clear:])
        ):
            raise NonHanPipelineError(
                "non-edge antialiased support touches the cell border"
            )
    cleaned = np.full_like(gray, 255)
    cleaned[support] = gray[support]
    resized = Image.fromarray(cleaned, mode="L").resize(
        (han_pipeline.CELL_RASTER_SIZE, han_pipeline.CELL_RASTER_SIZE),
        Image.Resampling.LANCZOS,
    )
    resized_array = np.asarray(resized, dtype=np.uint8)
    resized_core = resized_array <= han_pipeline.INK_CORE_CEILING
    resized_support = ndimage.binary_dilation(resized_core, iterations=5)
    final_array = np.full_like(resized_array, 255)
    final_array[resized_support] = resized_array[resized_support]
    if segmentation_profile != "edge":
        midtones = int(((final_array > 0) & (final_array < 255)).sum())
        if midtones == 0:
            raise NonHanPipelineError(
                "segmentation destroyed all source antialiasing"
            )
    final_core = final_array <= han_pipeline.INK_CORE_CEILING
    final_edge_counts = _edge_counts(final_core)
    final_contacts = {
        edge: count > 0 for edge, count in final_edge_counts.items()
    }
    if segmentation_profile == "edge" and any(
        contacts[edge] and not final_contacts[edge] for edge in contacts
    ):
        raise NonHanPipelineError(
            "resizing disconnected a declared box/block edge"
        )
    return (
        Image.fromarray(final_array, mode="L"),
        _normalized_ink_bbox(final_core),
        int(accepted_labels.size),
        core_pixels,
        fraction,
        final_contacts,
        final_edge_counts,
    )


def _content_box(
    detection: han_pipeline.GridDetection,
    *,
    row: int,
    column: int,
) -> tuple[int, int, int, int]:
    # The detected span contains the independently evidenced neutral-grey
    # centre of each rule.  Generator antialiasing can extend a darker fringe
    # one or two pixels into the cell without satisfying the neutral-coverage
    # test.  Remove that audited fringe as part of the grid, before any glyph
    # segmentation, so it can never become an outline or a false border touch.
    pad = GRID_RULE_INTERIOR_PADDING
    left = detection.x.groups[column][1] + 1 + pad
    right = detection.x.groups[column + 1][0] - pad
    top = detection.y.groups[row][1] + 1 + pad
    bottom = detection.y.groups[row + 1][0] - pad
    if right - left < 128 or bottom - top < 128:
        raise NonHanPipelineError("detected rule-free cell has implausible dimensions")
    return left, top, right, bottom


def _segmentation_profile(spec: GlyphSpec) -> str:
    if spec.transform_profile == "edge":
        return "edge"
    expected_name = DENSE_SOLID_GLYPHS.get(spec.codepoint)
    if expected_name is not None:
        if (
            spec.unicode_name != expected_name
            or spec.transform_profile != "proportional"
        ):
            raise NonHanPipelineError(
                f"{spec.codepoint_label}: dense-solid identity/profile drift"
            )
        return "dense-solid"
    return "generic"


def _edge_target_bounds(
    spec: GlyphSpec,
) -> tuple[
    tuple[float, float] | None,
    tuple[float, float] | None,
    dict[str, bool],
]:
    """Return semantic x/y bounds and required contacts for edge glyphs.

    Image-generated source ink defines the authored topology and stroke
    character. Unicode identity defines only the functional em-boundary
    placement required for box drawing and block elements. This separation
    avoids asking a raster model to perform exact font-metric placement while
    still forbidding any synthetic replacement outline. In particular, a
    source bbox is segmentation/layout evidence rather than identity: a
    symmetric U+2574–U+257B single arm remains admissible when its
    antialiased source ink crosses the cell midpoint. Its Unicode name selects
    the exact named half-em here.
    """

    if spec.transform_profile != "edge":
        raise NonHanPipelineError(
            f"{spec.codepoint_label}: edge targets require the edge transform"
        )
    if spec.profile_id == "box-drawing":
        if not 0x2500 <= spec.codepoint <= 0x257F:
            raise NonHanPipelineError(
                f"{spec.codepoint_label}: box-drawing scalar is out of range"
            )
        words = set(spec.unicode_name.split())
        if "DIAGONAL" in words:
            left = right = top = bottom = True
        else:
            left = "LEFT" in words or "HORIZONTAL" in words
            right = "RIGHT" in words or "HORIZONTAL" in words
            top = "UP" in words or "VERTICAL" in words
            bottom = "DOWN" in words or "VERTICAL" in words
        if not any((left, right, top, bottom)):
            raise NonHanPipelineError(
                f"{spec.codepoint_label}: box-drawing name has no direction"
            )
        x_target = (
            (0.0, float(UPM))
            if left and right
            else (0.0, UPM / 2)
            if left
            else (UPM / 2, float(UPM))
            if right
            else None
        )
        y_target = (
            (0.0, float(UPM))
            if bottom and top
            else (0.0, UPM / 2)
            if bottom
            else (UPM / 2, float(UPM))
            if top
            else None
        )
    elif spec.profile_id == "block-element":
        if not 0x2580 <= spec.codepoint <= 0x259F:
            raise NonHanPipelineError(
                f"{spec.codepoint_label}: block-element scalar is out of range"
            )
        codepoint = spec.codepoint
        if codepoint == 0x2580:
            x_target, y_target = (0.0, float(UPM)), (UPM / 2, float(UPM))
        elif 0x2581 <= codepoint <= 0x2587:
            height = (codepoint - 0x2580) * UPM / 8
            x_target, y_target = (0.0, float(UPM)), (0.0, height)
        elif codepoint == 0x2588:
            x_target = y_target = (0.0, float(UPM))
        elif 0x2589 <= codepoint <= 0x258F:
            width = (0x2590 - codepoint) * UPM / 8
            x_target, y_target = (0.0, width), (0.0, float(UPM))
        elif codepoint == 0x2590:
            x_target, y_target = (UPM / 2, float(UPM)), (0.0, float(UPM))
        elif 0x2591 <= codepoint <= 0x2593:
            x_target = y_target = (0.0, float(UPM))
        elif codepoint == 0x2594:
            x_target, y_target = (0.0, float(UPM)), (
                7 * UPM / 8,
                float(UPM),
            )
        elif codepoint == 0x2595:
            x_target, y_target = (
                7 * UPM / 8,
                float(UPM),
            ), (0.0, float(UPM))
        else:
            words = set(spec.unicode_name.split())
            left = "LEFT" in words
            right = "RIGHT" in words
            top = "UPPER" in words
            bottom = "LOWER" in words
            if not any((left, right)) or not any((top, bottom)):
                raise NonHanPipelineError(
                    f"{spec.codepoint_label}: quadrant identity is malformed"
                )
            x_target = (
                (0.0, float(UPM))
                if left and right
                else (0.0, UPM / 2)
                if left
                else (UPM / 2, float(UPM))
            )
            y_target = (
                (0.0, float(UPM))
                if bottom and top
                else (0.0, UPM / 2)
                if bottom
                else (UPM / 2, float(UPM))
            )
        assert x_target is not None and y_target is not None
        left = x_target[0] == 0
        right = x_target[1] == UPM
        bottom = y_target[0] == 0
        top = y_target[1] == UPM
    else:
        raise NonHanPipelineError(
            f"{spec.codepoint_label}: unsupported edge profile "
            f"{spec.profile_id!r}"
        )
    required = {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
    }
    return x_target, y_target, required


def _normalize_edge_points(
    points: Sequence[tuple[float, float]],
    *,
    spec: GlyphSpec,
) -> list[tuple[float, float]]:
    """Normalize authored edge ink to its Unicode-defined em placement."""

    if not points:
        raise NonHanPipelineError(
            f"{spec.codepoint_label}: edge outline has no points"
        )
    x_target, y_target, _required = _edge_target_bounds(spec)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min >= x_max or y_min >= y_max:
        raise NonHanPipelineError(
            f"{spec.codepoint_label}: edge outline bounds are degenerate"
        )

    def axis(
        value: float,
        source_min: float,
        source_max: float,
        target: tuple[float, float] | None,
    ) -> float:
        if target is None:
            return value + UPM / 2 - (source_min + source_max) / 2
        target_min, target_max = target
        return target_min + (
            (value - source_min)
            * (target_max - target_min)
            / (source_max - source_min)
        )

    return [
        (
            axis(x, x_min, x_max, x_target),
            axis(y, y_min, y_max, y_target),
        )
        for x, y in points
    ]


def segment_cells(
    image: Image.Image,
    detection: han_pipeline.GridDetection,
    slots: Sequence[GlyphSpec | None],
) -> tuple[SegmentedNonHanCell, ...]:
    if len(slots) != GRID_CAPACITY:
        raise NonHanPipelineError("descriptor/cell cardinality mismatch")
    cells: list[SegmentedNonHanCell] = []
    for row in range(ROWS):
        for column in range(COLUMNS):
            source_box = _content_box(detection, row=row, column=column)
            crop = image.crop(source_box)
            spec = slots[row * COLUMNS + column]
            if spec is None:
                gray = np.asarray(crop.convert("L"), dtype=np.uint8)
                labels, count = ndimage.label(
                    gray <= han_pipeline.INK_CORE_CEILING,
                    structure=np.ones((3, 3), dtype=np.uint8),
                )
                areas = np.bincount(labels.ravel()) if count else np.asarray([0])
                if count and np.any(
                    areas[1:] >= han_pipeline.INK_MIN_COMPONENT_AREA
                ):
                    raise NonHanPipelineError(
                        f"declared empty cell at row {row}, column {column} "
                        "contains visible ink"
                    )
                continue
            segmentation_profile = _segmentation_profile(spec)
            (
                cleaned,
                bbox,
                component_count,
                core_pixels,
                ink_fraction,
                contacts,
                contact_pixels,
            ) = _clean_cell(
                crop,
                segmentation_profile=segmentation_profile,
                minimum_edge_contacts=0,
            )
            if segmentation_profile == "edge":
                _x_target, _y_target, required_contacts = (
                    _edge_target_bounds(spec)
                )
                unexpected_contacts = {
                    edge
                    for edge, touched in contacts.items()
                    if touched and not required_contacts[edge]
                }
                if unexpected_contacts:
                    raise NonHanPipelineError(
                        f"{spec.codepoint_label}: source touches unexpected "
                        f"cell edges {sorted(unexpected_contacts)}"
                    )
                contacts = required_contacts
            cells.append(
                SegmentedNonHanCell(
                    spec=spec,
                    row=row,
                    column=column,
                    source_box=source_box,
                    source_ink_bbox=bbox,
                    core_component_count=component_count,
                    core_pixel_count=core_pixels,
                    ink_fraction=ink_fraction,
                    segmentation_profile=segmentation_profile,
                    edge_contacts=contacts,
                    edge_contact_pixels=contact_pixels,
                    cleaned=cleaned,
                )
            )
    return tuple(cells)


def _glyph_name(codepoint: int) -> str:
    return f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"


def _glyph_bounds(glyph: Glyph) -> tuple[int, int, int, int]:
    if glyph.numberOfContours <= 0 or not hasattr(glyph, "coordinates"):
        raise NonHanPipelineError("visible outline has no coordinates")
    xs = [int(point[0]) for point in glyph.coordinates]
    ys = [int(point[1]) for point in glyph.coordinates]
    if not xs:
        raise NonHanPipelineError("visible outline has no coordinates")
    return min(xs), min(ys), max(xs), max(ys)


def _shift_outline(glyph: Glyph, *, x: int = 0, y: int = 0) -> None:
    if not x and not y:
        return
    glyph.coordinates = GlyphCoordinates(
        [
            (int(point[0]) + x, int(point[1]) + y)
            for point in glyph.coordinates
        ]
    )


def _mark_class(spec: GlyphSpec) -> str:
    if spec.codepoint in {0x3099, 0x309A}:
        return "above-right"
    ccc = unicodedata.combining(spec.character)
    expected = f"ccc-{ccc}"
    if spec.metrics.mark_class != expected:
        raise NonHanPipelineError(
            f"{spec.codepoint_label}: descriptor mark class drifted from {expected}"
        )
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
    raise NonHanPipelineError(
        f"{spec.codepoint_label}: canonical combining class {ccc} has no "
        "audited above/below/overlay mapping"
    )


def _transform_for_profile(profile: str) -> tuple[float, float, float, float]:
    trace_extent = (
        han_pipeline.CELL_RASTER_SIZE
        * han_pipeline.TRACE_SUPERSAMPLE
        * han_pipeline.POTRACE_UNIT
    )
    if profile == "halfwidth":
        x_min, x_max = HALFWIDTH_X_MIN, HALFWIDTH_X_MAX
        y_min, y_max = GENERIC_FONT_Y_MIN, GENERIC_FONT_Y_MAX
    elif profile == "edge":
        x_min, x_max = 0, UPM
        y_min, y_max = 0, UPM
    else:
        x_min, x_max = GENERIC_FONT_X_MIN, GENERIC_FONT_X_MAX
        y_min, y_max = GENERIC_FONT_Y_MIN, GENERIC_FONT_Y_MAX
    return (
        (x_max - x_min) / trace_extent,
        (y_max - y_min) / trace_extent,
        float(x_min),
        float(y_min),
    )


def _vectorize(cell: SegmentedNonHanCell, svg_path: Path) -> VectorizedGlyph:
    path_data = han_pipeline._svg_path_data(svg_path)
    scale_x, scale_y, offset_x, offset_y = _transform_for_profile(
        cell.spec.transform_profile
    )
    pen = TTGlyphPen(None)
    converter = Cu2QuPen(
        pen,
        han_pipeline.CU2QU_MAX_ERROR,
        reverse_direction=True,
        all_quadratic=True,
    )
    transformed = TransformPen(
        converter,
        (scale_x, 0.0, 0.0, scale_y, offset_x, offset_y),
    )
    try:
        parse_path(path_data, transformed)
    except Exception as exc:
        raise NonHanPipelineError(
            f"{cell.spec.codepoint_label}: SVG to quadratic conversion failed: {exc}"
        ) from exc
    if cell.spec.transform_profile == "edge":
        pen.points = _normalize_edge_points(
            [
                (float(point[0]), float(point[1]))
                for point in pen.points
            ],
            spec=cell.spec,
        )
    raw_coordinates = tuple(
        (float(point[0]), float(point[1])) for point in pen.points
    )
    outline = pen.glyph()
    try:
        duplicate_count, maximum_collapse = (
            han_pipeline._canonicalize_quantized_on_off_duplicates(
                outline, raw_coordinates
            )
        )
        (
            thorn_count,
            maximum_thorn_displacement,
            coincident_flanks,
        ) = han_pipeline._remove_acute_implied_point_thorns(outline)
        if thorn_count:
            raise NonHanPipelineError(
                f"{cell.spec.codepoint_label}: vectorization required removal "
                f"of {thorn_count} micro-thorn points"
            )
        (
            contour_count,
            point_count,
            outer_count,
            counter_count,
            minimum_edge,
            micro_edges,
            acute_turns,
        ) = han_pipeline._geometry_quality(outline)
    except han_pipeline.ImagegenPipelineError as exc:
        raise NonHanPipelineError(
            f"{cell.spec.codepoint_label}: {exc}"
        ) from exc
    if (
        cell.spec.transform_profile == "edge"
        and outer_count != cell.core_component_count
    ):
        raise NonHanPipelineError(
            f"{cell.spec.codepoint_label}: vectorization changed source "
            "connected-component topology "
            f"({cell.core_component_count} source components, "
            f"{outer_count} vector outer contours)"
        )
    if micro_edges or acute_turns:
        raise NonHanPipelineError(
            f"{cell.spec.codepoint_label}: unsafe outline survived cleanup"
        )
    try:
        bounds = tuple(
            float(value) for value in han_pipeline._glyph_outline_bbox(outline)
        )
    except han_pipeline.ImagegenPipelineError as exc:
        raise NonHanPipelineError(
            f"{cell.spec.codepoint_label}: {exc}"
        ) from exc
    return VectorizedGlyph(
        spec=cell.spec,
        cell=cell,
        name=_glyph_name(cell.spec.codepoint),
        outline=outline,
        contour_count=contour_count,
        point_count=point_count,
        outer_contour_count=outer_count,
        counter_count=counter_count,
        minimum_control_edge=minimum_edge,
        quantization_duplicate_points_removed=duplicate_count,
        maximum_quantization_collapse=maximum_collapse,
        micro_thorn_points_removed=thorn_count,
        maximum_micro_thorn_displacement=maximum_thorn_displacement,
        coincident_flank_control_points_removed=coincident_flanks,
        micro_edge_count=micro_edges,
        acute_micro_turn_count=acute_turns,
        pre_metric_bounds=bounds,
    )


def _resolve_advances(glyphs: Sequence[VectorizedGlyph]) -> None:
    by_codepoint = {glyph.spec.codepoint: glyph for glyph in glyphs}
    resolving: set[int] = set()

    def resolve(glyph: VectorizedGlyph) -> int:
        if glyph.horizontal_advance is not None:
            return glyph.horizontal_advance
        codepoint = glyph.spec.codepoint
        if codepoint in resolving:
            raise NonHanPipelineError(
                f"{glyph.spec.codepoint_label}: cyclic advance reference"
            )
        resolving.add(codepoint)
        policy = glyph.spec.metrics.horizontal_advance
        x_min, _y_min, x_max, _y_max = _glyph_bounds(glyph.outline)
        ink_width = x_max - x_min
        if policy.kind == "source-proportional":
            left = glyph.spec.metrics.left_side_bearing
            right = glyph.spec.metrics.right_side_bearing
            if left is None or right is None:
                raise NonHanPipelineError(
                    f"{glyph.spec.codepoint_label}: missing audited bearings"
                )
            advance = ink_width + left + right
            if advance <= 0:
                raise NonHanPipelineError(
                    f"{glyph.spec.codepoint_label}: proportional advance is not positive"
                )
            _shift_outline(glyph.outline, x=left - x_min)
        elif policy.kind == "fixed":
            assert policy.value is not None
            advance = policy.value
            if glyph.spec.transform_profile == "mark":
                mark_class = _mark_class(glyph.spec)
                center_x = round((x_min + x_max) / 2)
                if mark_class in {"above", "above-right", "double-above"}:
                    y_shift = -_glyph_bounds(glyph.outline)[1]
                elif mark_class in {"below", "double-below"}:
                    y_shift = -_glyph_bounds(glyph.outline)[3]
                else:
                    _xm, y_min, _xx, y_max = _glyph_bounds(glyph.outline)
                    y_shift = -round((y_min + y_max) / 2)
                _shift_outline(glyph.outline, x=-center_x, y=y_shift)
                glyph.mark_class = mark_class
            elif glyph.spec.transform_profile == "proportional":
                left = glyph.spec.metrics.left_side_bearing
                right = glyph.spec.metrics.right_side_bearing
                assert left is not None and right is not None
                available_ink_width = advance - left - right
                if ink_width > available_ink_width:
                    raise NonHanPipelineError(
                        f"{glyph.spec.codepoint_label}: source ink width {ink_width} "
                        f"exceeds the audited fixed-metric envelope "
                        f"{available_ink_width}"
                    )
                _shift_outline(
                    glyph.outline,
                    x=left + (available_ink_width - ink_width) // 2 - x_min,
                )
        else:
            assert policy.reference_codepoint is not None
            reference = by_codepoint[policy.reference_codepoint]
            advance = resolve(reference)
            if ink_width > advance:
                raise NonHanPipelineError(
                    f"{glyph.spec.codepoint_label}: source ink width exceeds "
                    f"referenced advance {advance}"
                )
            _shift_outline(
                glyph.outline,
                x=(advance - ink_width) // 2 - x_min,
            )
        resolving.remove(codepoint)
        if not 0 <= advance <= 4096:
            raise NonHanPipelineError(
                f"{glyph.spec.codepoint_label}: resolved advance is out of range"
            )
        glyph.horizontal_advance = advance
        return advance

    for glyph in glyphs:
        resolve(glyph)

    for glyph in glyphs:
        x_min, _y_min, x_max, y_max = _glyph_bounds(glyph.outline)
        advance = glyph.horizontal_advance
        assert advance is not None
        glyph.left_side_bearing = x_min
        glyph.right_side_bearing = advance - x_max
        glyph.vertical_advance = glyph.spec.metrics.vertical_advance
        glyph.top_side_bearing = VERTICAL_ORIGIN_Y - y_max
        if glyph.spec.transform_profile not in {"mark"}:
            if x_min < 0 or x_max > advance:
                raise NonHanPipelineError(
                    f"{glyph.spec.codepoint_label}: outline {x_min}..{x_max} "
                    f"clips advance {advance}"
                )
        if glyph.spec.transform_profile == "edge":
            vector_contacts = {
                "left": x_min <= EDGE_FONT_TOLERANCE,
                "right": x_max >= UPM - EDGE_FONT_TOLERANCE,
                "bottom": _glyph_bounds(glyph.outline)[1] <= EDGE_FONT_TOLERANCE,
                "top": y_max >= UPM - EDGE_FONT_TOLERANCE,
            }
            glyph.vector_edge_contacts = vector_contacts
            for edge, required in glyph.cell.edge_contacts.items():
                if required and not vector_contacts[edge]:
                    raise NonHanPipelineError(
                        f"{glyph.spec.codepoint_label}: vectorization disconnected "
                        f"the {edge} edge"
                    )
        glyph.anchors_candidate = _anchor_candidates(glyph)


def _anchor_candidates(glyph: VectorizedGlyph) -> Mapping[str, Any]:
    x_min, y_min, x_max, y_max = _glyph_bounds(glyph.outline)
    if glyph.spec.transform_profile == "mark":
        return {
            "kind": "mark",
            "class": glyph.mark_class,
            "canonical_combining_class": unicodedata.combining(
                glyph.spec.character
            ),
            "mark_anchor": {"x": 0, "y": 0},
        }
    center_x = round((x_min + x_max) / 2)
    center_y = round((y_min + y_max) / 2)
    return {
        "kind": "base",
        "top": {"x": center_x, "y": min(ASCENDER, y_max + MARK_STACK_GAP)},
        "bottom": {
            "x": center_x,
            "y": max(DESCENDER, y_min - MARK_STACK_GAP),
        },
        "overlay": {"x": center_x, "y": center_y},
        "above_right": {
            "x": min(glyph.horizontal_advance or UPM, x_max),
            "y": min(ASCENDER, y_max + MARK_STACK_GAP),
        },
        "ideographic_left": {
            "x": x_min - MARK_STACK_GAP,
            "y": center_y,
        },
    }


def _notdef_glyph() -> Glyph:
    pen = TTGlyphPen(None)
    pen.moveTo((96, 0))
    pen.lineTo((928, 0))
    pen.lineTo((928, 896))
    pen.lineTo((96, 896))
    pen.closePath()
    pen.moveTo((176, 80))
    pen.lineTo((176, 816))
    pen.lineTo((848, 816))
    pen.lineTo((848, 80))
    pen.closePath()
    return pen.glyph()


def _font_builder(
    glyphs: Sequence[VectorizedGlyph],
    *,
    family: str,
    ps_name: str,
) -> FontBuilder:
    glyph_order = [".notdef", *(glyph.name for glyph in glyphs)]
    outlines = {".notdef": _notdef_glyph()}
    outlines.update({glyph.name: glyph.outline for glyph in glyphs})
    cmap = {glyph.spec.codepoint: glyph.name for glyph in glyphs}
    hmetrics = {".notdef": (UPM, 96)}
    hmetrics.update(
        {
            glyph.name: (
                int(glyph.horizontal_advance or 0),
                int(glyph.left_side_bearing or 0),
            )
            for glyph in glyphs
        }
    )
    vmetrics = {
        ".notdef": (UPM, VERTICAL_ORIGIN_Y - _glyph_bounds(outlines[".notdef"])[3])
    }
    vmetrics.update(
        {
            glyph.name: (
                int(glyph.vertical_advance or 0),
                int(glyph.top_side_bearing or 0),
            )
            for glyph in glyphs
        }
    )
    y_values = [
        int(point[1])
        for outline in outlines.values()
        if getattr(outline, "numberOfContours", 0) > 0
        for point in outline.coordinates
    ]
    win_ascent = max(ASCENDER, max(y_values))
    win_descent = max(-DESCENDER, -min(y_values))

    builder = FontBuilder(UPM, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(outlines)
    builder.setupHorizontalMetrics(hmetrics)
    builder.setupVerticalMetrics(vmetrics)
    builder.setupHorizontalHeader(
        ascent=ASCENDER,
        descent=DESCENDER,
        lineGap=LINE_GAP,
    )
    builder.setupVerticalHeader(ascent=500, descent=-500, lineGap=0)
    builder.setupNameTable(
        {
            "familyName": family,
            "styleName": "Regular",
            "uniqueFontIdentifier": f"{family} 0.1 unreviewed",
            "fullName": f"{family} Regular",
            "psName": ps_name,
            "version": "Version 0.1",
            "copyright": "Copyright 2026 The CodexFont Project Authors",
            "licenseDescription": (
                "This unreviewed Font Software is licensed under the SIL Open "
                "Font License, Version 1.1."
            ),
            "licenseInfoURL": "https://openfontlicense.org",
        }
    )
    builder.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=LINE_GAP,
        usWinAscent=win_ascent,
        usWinDescent=win_descent,
        achVendID="CDFT",
        fsType=0,
    )
    builder.setupPost(keepGlyphNames=True)
    builder.setupMaxp()
    builder.font["head"].created = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font["head"].modified = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font.recalcTimestamp = False
    return builder


def _font_names(batch_id: str) -> tuple[str, str]:
    match = SOURCE_BATCH_ID_PATTERN.fullmatch(batch_id)
    if match is None:
        raise NonHanPipelineError(f"invalid source batch id {batch_id!r}")
    number = match.group(1).removeprefix("nonhan-")
    return (
        f"Clear Hand TC NonHan {number} Unreviewed",
        f"ClearHandTC-NonHan{number}-Unreviewed",
    )


def _build_fonts(
    glyphs: Sequence[VectorizedGlyph],
    *,
    batch_id: str,
    directory: Path,
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    family, ps_name = _font_names(batch_id)
    ttf = directory / f"{ps_name}.ttf"
    otf = directory / f"{ps_name}.otf"
    _font_builder(glyphs, family=family, ps_name=ps_name).save(ttf)
    _font_builder(glyphs, family=family, ps_name=ps_name).save(otf)
    return ttf, otf


def _validate_fonts(
    paths: Sequence[Path],
    glyphs: Sequence[VectorizedGlyph],
) -> None:
    expected_order = [".notdef", *(glyph.name for glyph in glyphs)]
    expected_cmap = {glyph.spec.codepoint: glyph.name for glyph in glyphs}
    expected_hmetrics = {
        glyph.name: (
            int(glyph.horizontal_advance or 0),
            int(glyph.left_side_bearing or 0),
        )
        for glyph in glyphs
    }
    expected_vmetrics = {
        glyph.name: (
            int(glyph.vertical_advance or 0),
            int(glyph.top_side_bearing or 0),
        )
        for glyph in glyphs
    }
    for path in paths:
        try:
            font = TTFont(
                path,
                lazy=False,
                checkChecksums=2,
                recalcTimestamp=False,
            )
        except Exception as exc:
            raise NonHanPipelineError(f"{path}: cannot reopen font: {exc}") from exc
        try:
            if "glyf" not in font or "CFF " in font or "CFF2" in font:
                raise NonHanPipelineError(f"{path}: must use quadratic glyf outlines")
            if font.getGlyphOrder() != expected_order:
                raise NonHanPipelineError(f"{path}: glyph order mismatch")
            if font.getBestCmap() != expected_cmap:
                raise NonHanPipelineError(f"{path}: cmap mismatch")
            if "vhea" not in font or "vmtx" not in font:
                raise NonHanPipelineError(f"{path}: vertical metrics are missing")
            for glyph in glyphs:
                built = font["glyf"][glyph.name]
                if built.isComposite() or built.numberOfContours <= 0:
                    raise NonHanPipelineError(
                        f"{path}: {glyph.name} is empty or composite"
                    )
                if font["hmtx"].metrics[glyph.name] != expected_hmetrics[glyph.name]:
                    raise NonHanPipelineError(
                        f"{path}: {glyph.name} horizontal metric drift"
                    )
                if font["vmtx"].metrics[glyph.name] != expected_vmetrics[glyph.name]:
                    raise NonHanPipelineError(
                        f"{path}: {glyph.name} vertical metric drift"
                    )
        finally:
            font.close()


def _rendered_alpha(
    face: freetype.Face,
    character: str,
    size: int,
) -> np.ndarray:
    face.set_pixel_sizes(0, size)
    flags = (
        freetype.FT_LOAD_RENDER
        | freetype.FT_LOAD_NO_HINTING
        | freetype.FT_LOAD_TARGET_NORMAL
    )
    face.load_char(character, flags)
    bitmap = face.glyph.bitmap
    if bitmap.width <= 0 or bitmap.rows <= 0:
        raise NonHanPipelineError(
            f"U+{ord(character):04X}: blank at {size}px"
        )
    raw = np.asarray(bitmap.buffer, dtype=np.uint8)
    if bitmap.pitch < bitmap.width or raw.size < bitmap.pitch * bitmap.rows:
        raise NonHanPipelineError("unexpected FreeType bitmap layout")
    alpha = raw.reshape(bitmap.rows, bitmap.pitch)[:, : bitmap.width].copy()
    if int(alpha.max()) == 0:
        raise NonHanPipelineError(
            f"U+{ord(character):04X}: zero raster coverage at {size}px"
        )
    return alpha


def _paste_centered(
    canvas: np.ndarray,
    alpha: np.ndarray,
    *,
    cell_left: int,
    cell_top: int,
    cell_size: int,
    foreground: int,
) -> None:
    height, width = alpha.shape
    if height > cell_size or width > cell_size:
        raise NonHanPipelineError(
            f"proof glyph {width}x{height} exceeds {cell_size}px cell"
        )
    left = cell_left + (cell_size - width) // 2
    top = cell_top + (cell_size - height) // 2
    target = canvas[top : top + height, left : left + width]
    if foreground == 0:
        target[:] = np.minimum(target, 255 - alpha)
    else:
        target[:] = np.maximum(target, alpha)


def _write_size_proofs(
    font_path: Path,
    glyphs: Sequence[VectorizedGlyph],
    *,
    directory: Path,
    coverage_divisor_override: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    if (
        coverage_divisor_override is not None
        and coverage_divisor_override < 1
    ):
        raise NonHanPipelineError(
            "proof coverage divisor override must be positive"
        )
    directory.mkdir(parents=True, exist_ok=True)
    face = freetype.Face(str(font_path))
    coverage = {glyph.spec.codepoint_label: {} for glyph in glyphs}
    proof_records: list[dict[str, Any]] = []
    for size in SMALL_SIZE_PIXELS:
        cell_size = max(36, size + 24)
        width = COLUMNS * cell_size
        height = ROWS * cell_size
        black = np.full((height, width), 255, dtype=np.uint8)
        white = np.zeros((height, width), dtype=np.uint8)
        for glyph in glyphs:
            alpha = _rendered_alpha(face, glyph.spec.character, size)
            count = int(np.count_nonzero(alpha))
            divisor = coverage_divisor_override or (
                MARK_PROOF_COVERAGE_DIVISOR
                if glyph.spec.profile_id == "nonspacing-mark"
                else DEFAULT_PROOF_COVERAGE_DIVISOR
            )
            minimum_coverage = max(
                MINIMUM_PROOF_COVERAGE_PIXELS,
                size // divisor,
            )
            if count < minimum_coverage:
                raise NonHanPipelineError(
                    f"{glyph.spec.codepoint_label}: insufficient {size}px "
                    f"coverage ({count} < {minimum_coverage})"
                )
            coverage[glyph.spec.codepoint_label][str(size)] = count
            left = glyph.cell.column * cell_size
            top = glyph.cell.row * cell_size
            _paste_centered(
                black,
                alpha,
                cell_left=left,
                cell_top=top,
                cell_size=cell_size,
                foreground=0,
            )
            _paste_centered(
                white,
                alpha,
                cell_left=left,
                cell_top=top,
                cell_size=cell_size,
                foreground=255,
            )
        for polarity, pixels in (
            ("black-on-white", black),
            ("white-on-black", white),
        ):
            output = directory / f"{polarity}-{size}px.png"
            Image.fromarray(pixels, mode="L").save(output, optimize=False)
            proof_records.append(
                {
                    "kind": "small-size",
                    "polarity": polarity,
                    "size_px": size,
                    "path": f"proof/{output.name}",
                    "sha256": _sha256(output),
                    "cell_size_px": cell_size,
                }
            )
    return proof_records, coverage


def _write_source_proof(
    cells: Sequence[SegmentedNonHanCell],
    *,
    output: Path,
) -> Path:
    cell_size = 128
    sheet = Image.new("L", (COLUMNS * cell_size, ROWS * cell_size), color=255)
    for cell in cells:
        thumb = cell.cleaned.resize(
            (cell_size, cell_size), Image.Resampling.LANCZOS
        )
        sheet.paste(thumb, (cell.column * cell_size, cell.row * cell_size))
    sheet.save(output, optimize=False)
    return output


def _write_edge_proof(
    cells: Sequence[SegmentedNonHanCell],
    *,
    font_path: Path,
    output: Path,
) -> Path:
    cell_size = 144
    em_pixels = 128
    sheet = Image.new("RGB", (COLUMNS * cell_size, ROWS * cell_size), "white")
    draw = ImageDraw.Draw(sheet)
    face = freetype.Face(str(font_path))
    face.set_pixel_sizes(0, em_pixels)
    flags = (
        freetype.FT_LOAD_RENDER
        | freetype.FT_LOAD_NO_HINTING
        | freetype.FT_LOAD_TARGET_NORMAL
    )
    for cell in cells:
        left = cell.column * cell_size
        top = cell.row * cell_size
        face.load_char(cell.spec.character, flags)
        bitmap = face.glyph.bitmap
        raw = np.asarray(bitmap.buffer, dtype=np.uint8)
        if (
            bitmap.width <= 0
            or bitmap.rows <= 0
            or bitmap.pitch < bitmap.width
            or raw.size < bitmap.pitch * bitmap.rows
        ):
            raise NonHanPipelineError(
                f"{cell.spec.codepoint_label}: invalid edge-proof bitmap"
            )
        alpha = raw.reshape(bitmap.rows, bitmap.pitch)[:, : bitmap.width]
        glyph_left = left + 8 + int(face.glyph.bitmap_left)
        glyph_top = top + 8 + em_pixels - int(face.glyph.bitmap_top)
        inner_left, inner_top = left + 8, top + 8
        inner_right = inner_left + em_pixels
        inner_bottom = inner_top + em_pixels
        paste_left = max(glyph_left, inner_left)
        paste_top = max(glyph_top, inner_top)
        paste_right = min(glyph_left + bitmap.width, inner_right)
        paste_bottom = min(glyph_top + bitmap.rows, inner_bottom)
        if paste_left >= paste_right or paste_top >= paste_bottom:
            raise NonHanPipelineError(
                f"{cell.spec.codepoint_label}: edge-proof bitmap misses em"
            )
        alpha_crop = alpha[
            paste_top - glyph_top : paste_bottom - glyph_top,
            paste_left - glyph_left : paste_right - glyph_left,
        ]
        ink = Image.fromarray(255 - alpha_crop, mode="L").convert("RGB")
        sheet.paste(ink, (paste_left, paste_top))
        edge_profile = cell.spec.transform_profile == "edge"
        contacts = cell.edge_contacts
        colors = {
            edge: (
                "#159447"
                if edge_profile and contacts[edge]
                else "#c7ccd1"
            )
            for edge in ("left", "right", "top", "bottom")
        }
        draw.line((left + 4, top + 4, left + 4, top + cell_size - 5), fill=colors["left"], width=4)
        draw.line((left + cell_size - 5, top + 4, left + cell_size - 5, top + cell_size - 5), fill=colors["right"], width=4)
        draw.line((left + 4, top + 4, left + cell_size - 5, top + 4), fill=colors["top"], width=4)
        draw.line((left + 4, top + cell_size - 5, left + cell_size - 5, top + cell_size - 5), fill=colors["bottom"], width=4)
    sheet.save(output, optimize=False)
    return output


def _artifact_hashes(stage: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(stage.rglob("*")):
        if path.is_symlink():
            raise NonHanPipelineError(f"symlink artifact is forbidden: {path}")
        if not path.is_file() or path.name == "report.json":
            continue
        if path.suffix == ".pgm":
            raise NonHanPipelineError(f"temporary trace artifact leaked: {path}")
        result[path.relative_to(stage).as_posix()] = _sha256(path)
    return result


def _unused_backup_path(destination: Path) -> Path:
    for _ in range(128):
        candidate = destination.with_name(
            f".{destination.name}.backup-{secrets.token_hex(16)}"
        )
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
    raise NonHanPipelineError(
        f"cannot allocate a batch-build backup beside {destination}"
    )


def _install_build_directory(stage: Path, destination: Path) -> None:
    """Atomically install a batch build and restore the prior build on failure."""

    backup: Path | None = None
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise NonHanPipelineError(
                f"batch-build destination is not a regular directory: {destination}"
            )
        backup = _unused_backup_path(destination)
        try:
            destination.replace(backup)
        except OSError as exc:
            raise NonHanPipelineError(
                f"cannot move the prior batch build to backup: {exc}"
            ) from exc
    try:
        stage.replace(destination)
    except OSError as install_error:
        if backup is not None:
            try:
                backup.replace(destination)
            except OSError as rollback_error:
                raise NonHanPipelineError(
                    "batch-build install failed and rollback also failed; "
                    f"preserved backup: {backup}; install error: {install_error}; "
                    f"rollback error: {rollback_error}"
                ) from rollback_error
        raise NonHanPipelineError(
            f"batch-build install failed; prior build restored: {install_error}"
        ) from install_error
    if backup is not None:
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            raise NonHanPipelineError(
                f"new batch build installed but obsolete backup remains: "
                f"{backup}: {exc}"
            ) from exc


def _round_bounds(bounds: Sequence[float]) -> list[float]:
    return [round(float(value), 6) for value in bounds]


def _glyph_report(
    glyph: VectorizedGlyph,
    *,
    coverage: Mapping[str, Mapping[str, int]],
    source_png: Path,
    svg: Path,
) -> dict[str, Any]:
    x_min, y_min, x_max, y_max = _glyph_bounds(glyph.outline)
    assert glyph.horizontal_advance is not None
    assert glyph.left_side_bearing is not None
    assert glyph.right_side_bearing is not None
    assert glyph.vertical_advance is not None
    assert glyph.top_side_bearing is not None
    return {
        "character": glyph.spec.character,
        "codepoint": glyph.spec.codepoint_label,
        "unicode_name": glyph.spec.unicode_name,
        "glyph_name": glyph.name,
        "profile_id": glyph.spec.profile_id,
        "transform_profile": glyph.spec.transform_profile,
        "segmentation_profile": glyph.cell.segmentation_profile,
        "metric_policy": glyph.spec.source_record["metrics"],
        "row": glyph.cell.row,
        "column": glyph.cell.column,
        "source_box": list(glyph.cell.source_box),
        "source_ink_bbox_normalized": _round_bounds(
            glyph.cell.source_ink_bbox
        ),
        "source_ink_fraction": round(glyph.cell.ink_fraction, 8),
        "source_component_count": glyph.cell.core_component_count,
        "source_core_pixel_count": glyph.cell.core_pixel_count,
        "edge_contacts": dict(glyph.cell.edge_contacts),
        "edge_contact_pixels": dict(glyph.cell.edge_contact_pixels),
        "vector_edge_contacts": (
            None
            if glyph.vector_edge_contacts is None
            else dict(glyph.vector_edge_contacts)
        ),
        "pre_metric_bounds": _round_bounds(glyph.pre_metric_bounds),
        "final_bounds": [x_min, y_min, x_max, y_max],
        "metrics": {
            "horizontal_advance": glyph.horizontal_advance,
            "left_side_bearing": glyph.left_side_bearing,
            "right_side_bearing": glyph.right_side_bearing,
            "vertical_advance": glyph.vertical_advance,
            "vertical_origin_y": VERTICAL_ORIGIN_Y,
            "top_side_bearing": glyph.top_side_bearing,
            "metric_source": glyph.spec.metrics.horizontal_advance.kind,
            "reference_codepoint": (
                None
                if glyph.spec.metrics.horizontal_advance.reference_codepoint is None
                else f"U+{glyph.spec.metrics.horizontal_advance.reference_codepoint:04X}"
            ),
        },
        "mark_class": glyph.spec.metrics.mark_class,
        "mark_placement": glyph.mark_class,
        "anchors_candidate": glyph.anchors_candidate,
        "contour_count": glyph.contour_count,
        "point_count": glyph.point_count,
        "outer_contour_count": glyph.outer_contour_count,
        "counter_count": glyph.counter_count,
        "minimum_control_edge": round(glyph.minimum_control_edge, 6),
        "quantization_duplicate_points_removed": (
            glyph.quantization_duplicate_points_removed
        ),
        "maximum_quantization_collapse": round(
            glyph.maximum_quantization_collapse, 6
        ),
        "micro_thorn_points_removed": glyph.micro_thorn_points_removed,
        "maximum_micro_thorn_displacement": round(
            glyph.maximum_micro_thorn_displacement, 6
        ),
        "coincident_flank_control_points_removed": (
            glyph.coincident_flank_control_points_removed
        ),
        "micro_edge_count": glyph.micro_edge_count,
        "acute_micro_turn_count": glyph.acute_micro_turn_count,
        "coverage_pixels": dict(coverage[glyph.spec.codepoint_label]),
        "source_png": f"png/{source_png.name}",
        "source_png_sha256": _sha256(source_png),
        "svg": f"svg/{svg.name}",
        "svg_sha256": _sha256(svg),
    }


def build_batch(
    descriptor_path: Path = DEFAULT_DESCRIPTOR,
    *,
    project_root: Path = ROOT,
    output_root: Path | None = None,
    potrace_executable: str | Path | None = None,
) -> Path:
    """Build one unreviewed non-Han batch and return its final directory."""

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
        raise NonHanPipelineError(str(exc)) from exc
    try:
        source_image = Image.open(descriptor.raster_path)
        source_image.load()
    except (OSError, ValueError) as exc:
        raise NonHanPipelineError(
            f"{descriptor.raster_path}: cannot decode source PNG: {exc}"
        ) from exc
    if source_image.format != "PNG":
        raise NonHanPipelineError("source raster must decode as PNG")
    try:
        detection = han_pipeline.detect_grid(source_image)
    except han_pipeline.ImagegenPipelineError as exc:
        raise NonHanPipelineError(str(exc)) from exc
    cells = segment_cells(source_image, detection, descriptor.cell_slots)

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".imagegen-{descriptor.batch_id}-",
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

        vectorized: list[VectorizedGlyph] = []
        paths_by_codepoint: dict[int, tuple[Path, Path]] = {}
        for cell in cells:
            stem = f"u{cell.spec.codepoint:04x}"
            source_png = png_directory / f"{stem}-source.png"
            trace_bitmap = trace_directory / f"{stem}.pgm"
            svg_path = svg_directory / f"{stem}.svg"
            cell.cleaned.save(source_png, optimize=False)
            bridge_cell = han_pipeline.SegmentedCell(
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
                    bridge_cell,
                    potrace=potrace,
                    bitmap_path=trace_bitmap,
                    svg_path=svg_path,
                )
            except han_pipeline.ImagegenPipelineError as exc:
                raise NonHanPipelineError(str(exc)) from exc
            vectorized.append(_vectorize(cell, svg_path))
            paths_by_codepoint[cell.spec.codepoint] = (source_png, svg_path)
        _resolve_advances(vectorized)

        ttf_path, otf_path = _build_fonts(
            vectorized,
            batch_id=descriptor.batch_id,
            directory=font_directory,
        )
        _validate_fonts((ttf_path, otf_path), vectorized)
        proof_records, coverage = _write_size_proofs(
            ttf_path,
            vectorized,
            directory=proof_directory,
        )
        source_proof = _write_source_proof(
            cells,
            output=proof_directory / "segmented-source-contact.png",
        )
        edge_proof = _write_edge_proof(
            cells,
            font_path=ttf_path,
            output=proof_directory / "edge-connect.png",
        )

        glyph_records = []
        for glyph in vectorized:
            source_png, svg_path = paths_by_codepoint[glyph.spec.codepoint]
            record = _glyph_report(
                glyph,
                coverage=coverage,
                source_png=source_png,
                svg=svg_path,
            )
            glyph_records.append(record)
            report_path = glyph_report_directory / (
                f"u{glyph.spec.codepoint:04x}.json"
            )
            report_path.write_text(
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
            "source_state": descriptor.state,
            "source_review": dict(descriptor.review),
            "characters": [glyph.spec.character for glyph in vectorized],
            "codepoints": [glyph.spec.codepoint_label for glyph in vectorized],
            "grid": {
                "rows": ROWS,
                "columns": COLUMNS,
                "empty_grid_cells": descriptor.empty_grid_cells,
                "cell_slots": [
                    None if spec is None else spec.codepoint_label
                    for spec in descriptor.cell_slots
                ],
                "x_rule_centers": list(detection.x.centers),
                "y_rule_centers": list(detection.y.centers),
                "x_rule_spans": [list(value) for value in detection.x.groups],
                "y_rule_spans": [list(value) for value in detection.y.groups],
                "synthesized_coordinates": False,
            },
            "metric_contract": {
                "units_per_em": UPM,
                "vertical_origin_y": VERTICAL_ORIGIN_Y,
                "zero_advance_visible_mark_count": len(
                    ZERO_ADVANCE_VISIBLE_MARKS
                ),
                "spacing_combining_marks": [
                    f"U+{value:04X}" for value in sorted(SPACING_COMBINING_MARKS)
                ],
                "two_em_vertical_advance": [
                    f"U+{value:04X}"
                    for value in sorted(TWO_EM_VERTICAL_ADVANCE)
                ],
                "profile_transforms": dict(REPERTOIRE_PROFILE_TRANSFORMS),
                "proportional_advance": (
                    "source-outline-width-plus-audited-fixed-side-bearings"
                ),
            },
            "vectorization": {
                "tool": potrace_version,
                "outline_format": "TrueType quadratic glyf",
                "cu2qu_max_error": han_pipeline.CU2QU_MAX_ERROR,
                "grid_rules_removed_by_detected_rule_spans": True,
                "grid_rule_interior_padding_px": GRID_RULE_INTERIOR_PADDING,
                "segmentation_ink_fraction_limits": dict(
                    SEGMENTATION_INK_FRACTION_LIMITS
                ),
                "dense_solid_codepoints": [
                    f"U+{value:04X}" for value in DENSE_SOLID_GLYPHS
                ],
                "edge_profile_preserves_border_contacts": True,
                "small_size_proof_coverage": {
                    "minimum_pixels": MINIMUM_PROOF_COVERAGE_PIXELS,
                    "default_size_divisor": DEFAULT_PROOF_COVERAGE_DIVISOR,
                    "nonspacing_mark_size_divisor": (
                        MARK_PROOF_COVERAGE_DIVISOR
                    ),
                },
            },
            "font": {
                "units_per_em": UPM,
                "ttf": f"font/{ttf_path.name}",
                "ttf_sha256": _sha256(ttf_path),
                "otf": f"font/{otf_path.name}",
                "otf_sha256": _sha256(otf_path),
                "cmap_count": len(vectorized),
                "glyph_count": len(vectorized) + 1,
                "has_vertical_metrics": True,
            },
            "proofs": [
                *proof_records,
                {
                    "kind": "segmented-source",
                    "path": f"proof/{source_proof.name}",
                    "sha256": _sha256(source_proof),
                },
                {
                    "kind": "edge-connect",
                    "path": f"proof/{edge_proof.name}",
                    "sha256": _sha256(edge_proof),
                },
            ],
            "glyphs": glyph_records,
        }
        report["artifact_sha256"] = _artifact_hashes(stage)
        report_path = stage / "report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        _validate_fonts((ttf_path, otf_path), vectorized)
        if report["artifact_sha256"] != _artifact_hashes(stage):
            raise NonHanPipelineError(
                "artifact inventory changed after report materialization"
            )
        _install_build_directory(stage, final_directory)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return final_directory


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--descriptor",
        type=Path,
        default=DEFAULT_DESCRIPTOR,
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
    )
    parser.add_argument(
        "--potrace",
        type=Path,
    )
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
