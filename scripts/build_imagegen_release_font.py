#!/usr/bin/env python3
"""Build the approved 9,120-codepoint font with 93 vertical alternates.

Every encoded outline comes from an independently approved imagegen raster
batch.  The only contourless encoded glyphs are the 17 Unicode scalars whose
semantics require zero ink; their metrics and evidence are independently
approved.  The unencoded vertical alternates also come from independently
approved imagegen rasters. They inherit their encoded base glyphs' horizontal
and vertical advances while preserving the approved preview placement. No
authored-source tree, fallback font, compatibility outline, or synthetic
visible glyph is accepted by this compiler.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import tempfile
import unicodedata
from typing import Any, Iterable, Mapping, Sequence

import freetype
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
import numpy as np
from PIL import Image
from PIL import ImageDraw
import uharfbuzz as hb

from scripts import imagegen_approval as han_approval
from scripts import imagegen_nonhan_approval as nonhan_approval
from scripts import imagegen_vertical_approval as vertical_approval
from scripts import han_delta_approval
from scripts import moe_common_approval


ROOT = Path(__file__).resolve().parents[1]
APPROVAL_DIRECTORY = ROOT / "sources/imagegen/approvals"
OUTPUT_DIRECTORY = ROOT / "build/imagegen/release-9120"
DIST_RELATIVE_DIRECTORY = Path("dist/clear-hand-tc")
DIST_DIRECTORY = ROOT / DIST_RELATIVE_DIRECTORY

PIPELINE_ID = (
    "imagegen-approved-han6060-nonhan3060-vertical93-release-v4"
)
SOURCE_POLICY = (
    "approved-imagegen-raster-outlines-plus-semantic-empty-and-"
    "approved-unencoded-vertical-alternates-only;"
    "no-authored-sources-no-fallback-font-no-outline-substitution"
)

FONT_FAMILY = "Clear Hand TC"
FONT_STYLE = "Regular"
FONT_FULL_NAME = f"{FONT_FAMILY} {FONT_STYLE}"
FONT_PS_NAME = "ClearHandTC-Regular"
FONT_VERSION = "Version 0.100"
FONT_REVISION = 0.1
FONT_UNIQUE_ID = f"{FONT_FAMILY} 0.100"
FONT_COPYRIGHT = "Copyright 2026 The CodexFont Project Authors"
FONT_LICENSE = (
    "This Font Software is licensed under the SIL Open Font License, "
    "Version 1.1."
)
FONT_LICENSE_URL = "https://openfontlicense.org"
OFL_RELATIVE_PATH = PurePosixPath("OFL.txt")
OFL_SHA256 = "8f5205c5b79e80cdfcbcdea8178383b32b66fd9aa239c3ebe05cef0e891065ec"

UPM = 1024
ASCENDER = 928
DESCENDER = -96
LINE_GAP = 0
VERTICAL_ORIGIN_Y = 880
VERTICAL_CARET_SLOPE_RISE = 0
VERTICAL_CARET_SLOPE_RUN = 1
VERTICAL_CARET_OFFSET = 0
REPRODUCIBLE_HEAD_TIMESTAMP = 2_082_844_800
UNDERLINE_POSITION = -72
UNDERLINE_THICKNESS = 48
STRIKEOUT_POSITION = 300
STRIKEOUT_SIZE = 48

BASE_HAN_COUNT = 3000
MOE_EXTENSION_COUNT = 1844
DICTIONARY_EXTENSION_COUNT = 1216
MOE_COMMON_COUNT = 4808
HAN_COUNT = (
    BASE_HAN_COUNT
    + MOE_EXTENSION_COUNT
    + DICTIONARY_EXTENSION_COUNT
)
NONHAN_COUNT = 3060
VISIBLE_NONHAN_COUNT = 3043
SEMANTIC_EMPTY_COUNT = 17
CMAP_COUNT = HAN_COUNT + NONHAN_COUNT
VERTICAL_ALTERNATE_COUNT = 93
TOTAL_GLYPH_COUNT = 1 + CMAP_COUNT + VERTICAL_ALTERNATE_COUNT

PROOF_SIZES = (12, 16, 20, 24, 32, 36, 56, 72)
PROOF_COLUMNS = 32
MARK_STACK_GAP = 48
MARK_BASE_LOOKUP_CHUNK = 128


class ReleaseFontBuildError(RuntimeError):
    """The release cannot be built without violating an admission invariant."""


@dataclass(frozen=True)
class FontIdentity:
    """Naming and licensing metadata for one compiled family."""

    family: str
    style: str
    full_name: str
    postscript_name: str
    version: str
    revision: float
    unique_id: str
    copyright: str
    license_description: str
    license_url: str


CLEAR_HAND_IDENTITY = FontIdentity(
    family=FONT_FAMILY,
    style=FONT_STYLE,
    full_name=FONT_FULL_NAME,
    postscript_name=FONT_PS_NAME,
    version=FONT_VERSION,
    revision=FONT_REVISION,
    unique_id=FONT_UNIQUE_ID,
    copyright=FONT_COPYRIGHT,
    license_description=FONT_LICENSE,
    license_url=FONT_LICENSE_URL,
)


@dataclass(frozen=True)
class ReleaseGlyph:
    codepoint: int
    name: str
    outline: Glyph
    horizontal_metric: tuple[int, int]
    vertical_metric: tuple[int, int]
    source_collection: str
    source_batch: str
    source_font_sha256: str
    outline_required: bool
    profile_id: str
    mark_placement: str | None

    @property
    def character(self) -> str:
        return chr(self.codepoint)


@dataclass(frozen=True)
class VerticalAlternate:
    base_codepoint: int
    base_name: str
    name: str
    outline: Glyph
    horizontal_metric: tuple[int, int]
    vertical_metric: tuple[int, int]
    preview_horizontal_metric: tuple[int, int]
    preview_vertical_metric: tuple[int, int]
    source_batch: str
    source_font_path: Path
    source_font_sha256: str
    vertical_orientation: str
    tailoring: str | None


@dataclass(frozen=True)
class ReleaseNotdef:
    """The release ``.notdef`` outline and its approved source provenance."""

    outline: Glyph
    source_collection: str
    source_batch: str
    source_font_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _glyph_name(codepoint: int) -> str:
    return (
        f"uni{codepoint:04X}"
        if codepoint <= 0xFFFF
        else f"u{codepoint:05X}"
    )


def _bounds(outline: Glyph) -> tuple[int, int, int, int] | None:
    if (
        getattr(outline, "numberOfContours", 0) <= 0
        or not hasattr(outline, "coordinates")
        or len(outline.coordinates) == 0
    ):
        return None
    xs = [int(point[0]) for point in outline.coordinates]
    ys = [int(point[1]) for point in outline.coordinates]
    return min(xs), min(ys), max(xs), max(ys)


def _outline_signature(outline: Glyph) -> tuple[Any, ...]:
    if outline.isComposite():
        raise ReleaseFontBuildError("composite outline is forbidden")
    contour_count = int(getattr(outline, "numberOfContours", 0))
    coordinates = tuple(
        (int(point[0]), int(point[1]))
        for point in getattr(outline, "coordinates", ())
    )
    end_points = tuple(
        int(value) for value in getattr(outline, "endPtsOfContours", ())
    )
    flags = tuple(int(value) for value in getattr(outline, "flags", ()))
    program = getattr(outline, "program", None)
    instructions = (
        bytes(program.getBytecode())
        if program is not None
        else b""
    )
    return contour_count, coordinates, end_points, flags, instructions


def _project_relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise ReleaseFontBuildError(
            f"approved evidence escapes project root: {path}"
        ) from exc


def _open_validated_font(path: Path) -> TTFont:
    try:
        return TTFont(
            path,
            lazy=False,
            checkChecksums=2,
            recalcTimestamp=False,
        )
    except Exception as exc:
        raise ReleaseFontBuildError(
            f"cannot reopen approved font {path}: {exc}"
        ) from exc


def _han_vertical_metric(outline: Glyph) -> tuple[int, int]:
    bounds = _bounds(outline)
    if bounds is None:
        raise ReleaseFontBuildError("approved Han glyph is unexpectedly empty")
    return UPM, VERTICAL_ORIGIN_Y - bounds[3]


def _extract_han(
    approvals: Sequence[han_approval.ValidatedApproval],
) -> tuple[ReleaseGlyph, ...]:
    glyphs: list[ReleaseGlyph] = []
    seen: set[int] = set()
    for admitted in approvals:
        font = _open_validated_font(admitted.ttf_path)
        try:
            cmap = font.getBestCmap()
            for character in admitted.characters:
                codepoint = ord(character)
                name = _glyph_name(codepoint)
                if codepoint in seen or cmap.get(codepoint) != name:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch.batch_id}: Han cmap/order drift at "
                        f"U+{codepoint:04X}"
                    )
                outline = font["glyf"][name]
                if outline.isComposite() or outline.numberOfContours <= 0:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch.batch_id}: {name} is empty/composite"
                    )
                horizontal = tuple(font["hmtx"].metrics[name])
                if horizontal[0] != UPM:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch.batch_id}: {name} is not fullwidth"
                    )
                glyphs.append(
                    ReleaseGlyph(
                        codepoint=codepoint,
                        name=name,
                        outline=deepcopy(outline),
                        horizontal_metric=(
                            int(horizontal[0]),
                            int(horizontal[1]),
                        ),
                        vertical_metric=_han_vertical_metric(outline),
                        source_collection="common-han-3000",
                        source_batch=admitted.batch.batch_id,
                        source_font_sha256=_sha256(admitted.ttf_path),
                        outline_required=True,
                        profile_id="han-fullwidth",
                        mark_placement=None,
                    )
                )
                seen.add(codepoint)
        finally:
            font.close()
    if len(glyphs) != BASE_HAN_COUNT:
        raise ReleaseFontBuildError(
            f"approved base Han set is {len(glyphs)}, "
            f"expected {BASE_HAN_COUNT}"
        )
    return tuple(glyphs)


def _extract_moe_extension(
    approved: moe_common_approval.ApprovedExtension,
) -> tuple[ReleaseGlyph, ...]:
    glyphs: list[ReleaseGlyph] = []
    seen: set[int] = set()
    for admitted in approved.batches:
        font = _open_validated_font(admitted.ttf_path)
        try:
            cmap = font.getBestCmap()
            for character in admitted.characters:
                codepoint = ord(character)
                name = _glyph_name(codepoint)
                if codepoint in seen or cmap.get(codepoint) != name:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch_id}: MOE extension cmap/order drift "
                        f"at U+{codepoint:04X}"
                    )
                outline = font["glyf"][name]
                if outline.isComposite() or outline.numberOfContours <= 0:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch_id}: {name} is empty/composite"
                    )
                horizontal = tuple(font["hmtx"].metrics[name])
                if horizontal[0] != UPM:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch_id}: {name} is not fullwidth"
                    )
                glyphs.append(
                    ReleaseGlyph(
                        codepoint=codepoint,
                        name=name,
                        outline=deepcopy(outline),
                        horizontal_metric=(
                            int(horizontal[0]),
                            int(horizontal[1]),
                        ),
                        vertical_metric=_han_vertical_metric(outline),
                        source_collection="moe-common-extension-1844",
                        source_batch=admitted.batch_id,
                        source_font_sha256=admitted.ttf_sha256,
                        outline_required=True,
                        profile_id="han-fullwidth",
                        mark_placement=None,
                    )
                )
                seen.add(codepoint)
        finally:
            font.close()
    if len(glyphs) != MOE_EXTENSION_COUNT:
        raise ReleaseFontBuildError(
            f"approved MOE extension is {len(glyphs)}, "
            f"expected {MOE_EXTENSION_COUNT}"
        )
    return tuple(glyphs)


def _extract_dictionary_extension(
    approved: han_delta_approval.ApprovedDelta,
) -> tuple[ReleaseGlyph, ...]:
    """Extract the independently reviewed 1,216-glyph Han delta."""

    glyphs: list[ReleaseGlyph] = []
    seen: set[int] = set()
    for admitted in approved.batches:
        font = _open_validated_font(admitted.ttf_path)
        try:
            cmap = font.getBestCmap()
            for character in admitted.characters:
                codepoint = ord(character)
                name = _glyph_name(codepoint)
                if codepoint in seen or cmap.get(codepoint) != name:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch_id}: dictionary extension "
                        f"cmap/order drift at U+{codepoint:04X}"
                    )
                outline = font["glyf"][name]
                if outline.isComposite() or outline.numberOfContours <= 0:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch_id}: {name} is empty/composite"
                    )
                horizontal = tuple(font["hmtx"].metrics[name])
                if horizontal[0] != UPM:
                    raise ReleaseFontBuildError(
                        f"{admitted.batch_id}: {name} is not fullwidth"
                    )
                glyphs.append(
                    ReleaseGlyph(
                        codepoint=codepoint,
                        name=name,
                        outline=deepcopy(outline),
                        horizontal_metric=(
                            int(horizontal[0]),
                            int(horizontal[1]),
                        ),
                        vertical_metric=_han_vertical_metric(outline),
                        source_collection=(
                            "dictionary-salience-extension-1216"
                        ),
                        source_batch=admitted.batch_id,
                        source_font_sha256=admitted.ttf_sha256,
                        outline_required=True,
                        profile_id="han-fullwidth",
                        mark_placement=None,
                    )
                )
                seen.add(codepoint)
        finally:
            font.close()
    if len(glyphs) != DICTIONARY_EXTENSION_COUNT:
        raise ReleaseFontBuildError(
            f"approved dictionary extension is {len(glyphs)}, "
            f"expected {DICTIONARY_EXTENSION_COUNT}"
        )
    return tuple(glyphs)


def _visible_nonhan_font(
    admitted: nonhan_approval.ValidatedApproval,
) -> tuple[Path, Mapping[str, Mapping[str, Any]]]:
    evidence = admitted.visible_evidence
    if evidence is None:
        raise ReleaseFontBuildError(
            f"{admitted.batch.batch_id}: expected visible evidence"
        )
    report = evidence.report
    relative = report["font"]["ttf"]
    if not isinstance(relative, str):
        raise ReleaseFontBuildError(
            f"{admitted.batch.batch_id}: invalid report font path"
        )
    path = evidence.report_path.parent / relative
    if (
        not path.is_file()
        or _sha256(path) != report["font"]["ttf_sha256"]
    ):
        raise ReleaseFontBuildError(
            f"{admitted.batch.batch_id}: approved TTF hash drift"
        )
    reports = {
        str(record["codepoint"]): record
        for record in report["glyphs"]
    }
    if len(reports) != len(admitted.batch.glyphs):
        raise ReleaseFontBuildError(
            f"{admitted.batch.batch_id}: duplicate report glyphs"
        )
    return path, reports


def _extract_nonhan(
    approvals: Sequence[nonhan_approval.ValidatedApproval],
) -> tuple[ReleaseGlyph, ...]:
    by_codepoint: dict[int, ReleaseGlyph] = {}
    repertoire = approvals[0].repertoire
    for admitted in approvals:
        if admitted.batch.batch_kind == "raster-outline":
            path, report_records = _visible_nonhan_font(admitted)
            font = _open_validated_font(path)
            try:
                cmap = font.getBestCmap()
                for spec in admitted.batch.glyphs:
                    name = _glyph_name(spec.codepoint)
                    record = report_records.get(spec.codepoint_label)
                    if record is None or cmap.get(spec.codepoint) != name:
                        raise ReleaseFontBuildError(
                            f"{admitted.batch.batch_id}: missing "
                            f"{spec.codepoint_label}"
                        )
                    if record["glyph_name"] != name:
                        raise ReleaseFontBuildError(
                            f"{admitted.batch.batch_id}: glyph-name drift for "
                            f"{spec.codepoint_label}"
                        )
                    outline = font["glyf"][name]
                    if outline.isComposite() or outline.numberOfContours <= 0:
                        raise ReleaseFontBuildError(
                            f"{spec.codepoint_label}: visible glyph is empty/composite"
                        )
                    horizontal = tuple(font["hmtx"].metrics[name])
                    vertical = tuple(font["vmtx"].metrics[name])
                    expected_h = (
                        record["metrics"]["horizontal_advance"],
                        record["metrics"]["left_side_bearing"],
                    )
                    expected_v = (
                        record["metrics"]["vertical_advance"],
                        record["metrics"]["top_side_bearing"],
                    )
                    if horizontal != expected_h or vertical != expected_v:
                        raise ReleaseFontBuildError(
                            f"{spec.codepoint_label}: approved metric drift"
                        )
                    if spec.codepoint in by_codepoint:
                        raise ReleaseFontBuildError(
                            f"duplicate non-Han {spec.codepoint_label}"
                        )
                    by_codepoint[spec.codepoint] = ReleaseGlyph(
                        codepoint=spec.codepoint,
                        name=name,
                        outline=deepcopy(outline),
                        horizontal_metric=(
                            int(horizontal[0]),
                            int(horizontal[1]),
                        ),
                        vertical_metric=(
                            int(vertical[0]),
                            int(vertical[1]),
                        ),
                        source_collection="nonhan-3060-visible",
                        source_batch=admitted.batch.batch_id,
                        source_font_sha256=_sha256(path),
                        outline_required=True,
                        profile_id=spec.profile_id,
                        mark_placement=record["mark_placement"],
                    )
            finally:
                font.close()
        else:
            evidence = admitted.semantic_evidence
            if evidence is None:
                raise ReleaseFontBuildError(
                    f"{admitted.batch.batch_id}: missing semantic evidence"
                )
            font = _open_validated_font(evidence.font_path)
            try:
                manifest_records = {
                    str(record["codepoint"]): record
                    for record in evidence.manifest["glyphs"]
                }
                cmap = font.getBestCmap()
                for spec in admitted.batch.glyphs:
                    name = _glyph_name(spec.codepoint)
                    record = manifest_records.get(spec.codepoint_label)
                    if record is None or cmap.get(spec.codepoint) != name:
                        raise ReleaseFontBuildError(
                            f"semantic {spec.codepoint_label} mapping drift"
                        )
                    outline = font["glyf"][name]
                    if outline.isComposite() or outline.numberOfContours != 0:
                        raise ReleaseFontBuildError(
                            f"{spec.codepoint_label}: semantic outline has ink"
                        )
                    horizontal = tuple(font["hmtx"].metrics[name])
                    vertical = tuple(font["vmtx"].metrics[name])
                    if horizontal != (
                        record["resolved_horizontal_advance"],
                        0,
                    ):
                        raise ReleaseFontBuildError(
                            f"{spec.codepoint_label}: semantic hmtx drift"
                        )
                    if vertical != (
                        spec.metrics["vertical_advance"]["value"],
                        0,
                    ):
                        raise ReleaseFontBuildError(
                            f"{spec.codepoint_label}: semantic vmtx drift"
                        )
                    if spec.codepoint in by_codepoint:
                        raise ReleaseFontBuildError(
                            f"duplicate semantic {spec.codepoint_label}"
                        )
                    by_codepoint[spec.codepoint] = ReleaseGlyph(
                        codepoint=spec.codepoint,
                        name=name,
                        outline=deepcopy(outline),
                        horizontal_metric=(
                            int(horizontal[0]),
                            int(horizontal[1]),
                        ),
                        vertical_metric=(
                            int(vertical[0]),
                            int(vertical[1]),
                        ),
                        source_collection="nonhan-3060-semantic-empty",
                        source_batch=admitted.batch.batch_id,
                        source_font_sha256=evidence.font_sha256,
                        outline_required=False,
                        profile_id=spec.profile_id,
                        mark_placement=(
                            "overlay"
                            if spec.profile_id == "nonspacing-mark"
                            else None
                        ),
                    )
            finally:
                font.close()

    expected_codepoints = [glyph.codepoint for glyph in repertoire.glyphs]
    if set(by_codepoint) != set(expected_codepoints):
        missing = sorted(set(expected_codepoints) - set(by_codepoint))
        extra = sorted(set(by_codepoint) - set(expected_codepoints))
        raise ReleaseFontBuildError(
            f"non-Han extraction mismatch: missing={missing}, extra={extra}"
        )
    ordered = tuple(by_codepoint[codepoint] for codepoint in expected_codepoints)
    if len(ordered) != NONHAN_COUNT:
        raise ReleaseFontBuildError(
            f"non-Han extraction is {len(ordered)}, expected {NONHAN_COUNT}"
        )
    return ordered


def _codepoint_from_label(value: Any) -> int:
    if (
        not isinstance(value, str)
        or len(value) not in {6, 7, 8}
        or not value.startswith("U+")
    ):
        raise ReleaseFontBuildError(
            f"invalid vertical base codepoint label: {value!r}"
        )
    try:
        codepoint = int(value[2:], 16)
    except ValueError as exc:
        raise ReleaseFontBuildError(
            f"invalid vertical base codepoint label: {value!r}"
        ) from exc
    if value != f"U+{codepoint:04X}" or not 0 <= codepoint <= 0x10FFFF:
        raise ReleaseFontBuildError(
            f"noncanonical vertical base codepoint label: {value!r}"
        )
    return codepoint


def _validate_vertical_base_policy(
    base: ReleaseGlyph,
    *,
    approved_record: Mapping[str, Any],
) -> None:
    if approved_record.get("base_profile_id") != base.profile_id:
        raise ReleaseFontBuildError(
            f"U+{base.codepoint:04X}: vertical base profile drift"
        )
    policy = approved_record.get("base_metrics")
    if not isinstance(policy, dict):
        raise ReleaseFontBuildError(
            f"U+{base.codepoint:04X}: vertical base metric policy missing"
        )
    horizontal = policy.get("horizontal_advance")
    vertical = policy.get("vertical_advance")
    if not isinstance(horizontal, dict) or not isinstance(vertical, dict):
        raise ReleaseFontBuildError(
            f"U+{base.codepoint:04X}: malformed vertical base metric policy"
        )
    if horizontal.get("kind") == "fixed":
        if horizontal.get("value") != base.horizontal_metric[0]:
            raise ReleaseFontBuildError(
                f"U+{base.codepoint:04X}: horizontal advance policy drift"
            )
    elif horizontal != {"kind": "source-proportional"}:
        raise ReleaseFontBuildError(
            f"U+{base.codepoint:04X}: unsupported horizontal metric policy"
        )
    if (
        vertical.get("kind") != "fixed"
        or vertical.get("value") != base.vertical_metric[0]
    ):
        raise ReleaseFontBuildError(
            f"U+{base.codepoint:04X}: vertical advance policy drift"
        )


def _extract_vertical_alternates(
    approvals: Sequence[Mapping[str, Any]],
    *,
    encoded_glyphs: Sequence[ReleaseGlyph],
    project_root: Path,
) -> tuple[VerticalAlternate, ...]:
    by_codepoint = {glyph.codepoint: glyph for glyph in encoded_glyphs}
    if len(by_codepoint) != len(encoded_glyphs):
        raise ReleaseFontBuildError(
            "encoded repertoire is not unique before vertical extraction"
        )

    alternates: list[VerticalAlternate] = []
    seen_bases: set[int] = set()
    seen_names: set[str] = set()
    for approval in approvals:
        batch_id = approval.get("batch_id")
        if not isinstance(batch_id, str):
            raise ReleaseFontBuildError(
                "vertical approval has no canonical batch identity"
            )
        try:
            build = vertical_approval.validate_build(
                batch_id,
                project_root=project_root,
            )
        except vertical_approval.VerticalApprovalError as exc:
            raise ReleaseFontBuildError(str(exc)) from exc
        approved_records = approval.get("glyphs")
        report_records = build.report.get("glyphs")
        if (
            not isinstance(approved_records, list)
            or not isinstance(report_records, list)
            or len(approved_records) != len(report_records)
        ):
            raise ReleaseFontBuildError(
                f"{batch_id}: vertical approval/report cardinality drift"
            )

        font = _open_validated_font(build.ttf_path)
        try:
            for approved, report in zip(
                approved_records,
                report_records,
                strict=True,
            ):
                if not isinstance(approved, dict) or not isinstance(report, dict):
                    raise ReleaseFontBuildError(
                        f"{batch_id}: malformed vertical glyph record"
                    )
                codepoint = _codepoint_from_label(
                    approved.get("base_codepoint")
                )
                name = approved.get("glyph_name")
                if (
                    not isinstance(name, str)
                    or name != f"{_glyph_name(codepoint)}.vert"
                    or report.get("codepoint")
                    != approved.get("base_codepoint")
                    or report.get("unencoded_glyph_name") != name
                ):
                    raise ReleaseFontBuildError(
                        f"{batch_id}: vertical glyph identity drift at "
                        f"U+{codepoint:04X}"
                    )
                base = by_codepoint.get(codepoint)
                if base is None:
                    raise ReleaseFontBuildError(
                        f"{batch_id}: vertical base U+{codepoint:04X} "
                        "is outside the encoded repertoire"
                    )
                _validate_vertical_base_policy(
                    base,
                    approved_record=approved,
                )
                if codepoint in seen_bases or name in seen_names:
                    raise ReleaseFontBuildError(
                        f"{batch_id}: duplicate vertical alternate {name}"
                    )
                outline = font["glyf"][name]
                if outline.isComposite() or outline.numberOfContours <= 0:
                    raise ReleaseFontBuildError(
                        f"{batch_id}: {name} is empty or composite"
                    )
                vertical_orientation = report.get("vertical_orientation")
                tailoring = report.get("tailoring")
                if (
                    not isinstance(vertical_orientation, str)
                    or (
                        tailoring is not None
                        and not isinstance(tailoring, str)
                    )
                ):
                    raise ReleaseFontBuildError(
                        f"{batch_id}: malformed vertical provenance for {name}"
                    )
                preview_horizontal = tuple(font["hmtx"].metrics[name])
                preview_vertical = tuple(font["vmtx"].metrics[name])
                advance_delta = (
                    base.horizontal_metric[0] - preview_horizontal[0]
                )
                if advance_delta % 2:
                    raise ReleaseFontBuildError(
                        f"{batch_id}: {name} cannot preserve approved "
                        "horizontal placement with an odd advance delta"
                    )
                release_horizontal = (
                    base.horizontal_metric[0],
                    preview_horizontal[1] + advance_delta // 2,
                )
                release_vertical = (
                    base.vertical_metric[0],
                    preview_vertical[1],
                )
                alternates.append(
                    VerticalAlternate(
                        base_codepoint=codepoint,
                        base_name=base.name,
                        name=name,
                        outline=deepcopy(outline),
                        horizontal_metric=release_horizontal,
                        vertical_metric=release_vertical,
                        preview_horizontal_metric=preview_horizontal,
                        preview_vertical_metric=preview_vertical,
                        source_batch=batch_id,
                        source_font_path=build.ttf_path,
                        source_font_sha256=build.ttf_sha256,
                        vertical_orientation=vertical_orientation,
                        tailoring=tailoring,
                    )
                )
                seen_bases.add(codepoint)
                seen_names.add(name)
        finally:
            font.close()

    if len(alternates) != VERTICAL_ALTERNATE_COUNT:
        raise ReleaseFontBuildError(
            f"vertical alternate count is {len(alternates)}, expected "
            f"{VERTICAL_ALTERNATE_COUNT}"
        )
    return tuple(alternates)


def _notdef_from_first_han(
    approvals: Sequence[han_approval.ValidatedApproval],
) -> ReleaseNotdef:
    if not approvals:
        raise ReleaseFontBuildError(
            "cannot source .notdef from an empty Han approval set"
        )
    admitted = approvals[0]
    font = _open_validated_font(admitted.ttf_path)
    try:
        outline = font["glyf"][".notdef"]
        if outline.isComposite() or outline.numberOfContours <= 0:
            raise ReleaseFontBuildError("approved .notdef is empty/composite")
        return ReleaseNotdef(
            outline=deepcopy(outline),
            source_collection="common-han-3000",
            source_batch=admitted.batch.batch_id,
            source_font_sha256=_sha256(admitted.ttf_path),
        )
    finally:
        font.close()


def _latin_base(character: str) -> str | None:
    special = {
        "Æ": "A",
        "æ": "a",
        "Ð": "D",
        "ð": "d",
        "Đ": "D",
        "đ": "d",
        "Ø": "O",
        "ø": "o",
        "Œ": "O",
        "œ": "o",
        "Þ": "P",
        "þ": "p",
        "Ł": "L",
        "ł": "l",
    }
    if character in special:
        return special[character]
    normalized = unicodedata.normalize("NFD", character)
    if normalized and normalized[0] in (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    ):
        return normalized[0]
    return None


def _kerning_feature(glyphs: Sequence[ReleaseGlyph]) -> tuple[str, int]:
    by_base: dict[str, list[str]] = {}
    by_codepoint = {glyph.codepoint: glyph.name for glyph in glyphs}
    for glyph in glyphs:
        base = _latin_base(glyph.character)
        if base is not None:
            by_base.setdefault(base, []).append(glyph.name)

    lines: list[str] = []
    class_name: dict[str, str] = {}
    for base in sorted(by_base):
        name = f"@K_{'U' if base.isupper() else 'L'}_{base.upper()}"
        class_name[base] = name
        lines.append(f"{name} = [{' '.join(by_base[base])}];")

    pairs: tuple[tuple[str, str, int], ...] = (
        ("A", "T", -54), ("A", "V", -76), ("A", "W", -62),
        ("A", "Y", -80), ("A", "v", -44), ("A", "w", -38),
        ("A", "y", -48), ("F", "A", -54), ("F", "a", -36),
        ("F", "e", -34), ("F", "o", -38), ("L", "T", -58),
        ("L", "V", -66), ("L", "W", -52), ("L", "Y", -72),
        ("P", "A", -52), ("P", "a", -28), ("P", "e", -28),
        ("P", "o", -32), ("T", "A", -58), ("T", "a", -66),
        ("T", "e", -66), ("T", "i", -34), ("T", "o", -70),
        ("T", "r", -34), ("T", "u", -54), ("T", "w", -48),
        ("T", "y", -52), ("V", "A", -76), ("V", "a", -54),
        ("V", "e", -54), ("V", "i", -24), ("V", "o", -60),
        ("V", "u", -44), ("W", "A", -62), ("W", "a", -42),
        ("W", "e", -42), ("W", "o", -46), ("Y", "A", -80),
        ("Y", "a", -68), ("Y", "e", -68), ("Y", "i", -38),
        ("Y", "o", -72), ("Y", "u", -56), ("f", "a", -22),
        ("f", "e", -22), ("f", "o", -24), ("r", "v", -18),
        ("r", "w", -16), ("r", "y", -20), ("v", "a", -24),
        ("v", "e", -24), ("v", "o", -28), ("w", "a", -18),
        ("w", "e", -18), ("w", "o", -22), ("y", "a", -24),
        ("y", "e", -24), ("y", "o", -28),
    )
    statements: list[str] = []
    for left, right, value in pairs:
        if left in class_name and right in class_name:
            statements.append(
                f"  pos {class_name[left]} {class_name[right]} {value};"
            )

    punctuation_pairs = (
        ("T", 0x002C, -54), ("T", 0x002E, -54),
        ("V", 0x002C, -46), ("V", 0x002E, -46),
        ("W", 0x002C, -38), ("W", 0x002E, -38),
        ("Y", 0x002C, -58), ("Y", 0x002E, -58),
        ("P", 0x002C, -38), ("P", 0x002E, -38),
        ("F", 0x002C, -34), ("F", 0x002E, -34),
    )
    for left, codepoint, value in punctuation_pairs:
        if left in class_name and codepoint in by_codepoint:
            statements.append(
                f"  pos {class_name[left]} {by_codepoint[codepoint]} {value};"
            )
    if not statements:
        return "", 0
    lines.append("feature kern {")
    lines.extend(statements)
    lines.append("} kern;")
    return "\n".join(lines) + "\n", len(statements)


def _mark_anchor(
    glyph: ReleaseGlyph,
    placement: str,
) -> tuple[int, int]:
    bounds = _bounds(glyph.outline)
    if bounds is None:
        return 0, 0
    x_min, y_min, x_max, y_max = bounds
    center_x = round((x_min + x_max) / 2)
    center_y = round((y_min + y_max) / 2)
    if placement in {"above", "double-above"}:
        return center_x, y_max + MARK_STACK_GAP
    if placement in {"below", "double-below"}:
        return center_x, y_min - MARK_STACK_GAP
    if placement == "overlay":
        return center_x, center_y
    if placement == "above-right":
        return x_max, y_max + MARK_STACK_GAP
    raise ReleaseFontBuildError(f"unsupported mark placement {placement!r}")


def _mark_feature(
    glyphs: Sequence[ReleaseGlyph],
) -> tuple[str, Mapping[str, int]]:
    marks = tuple(
        glyph
        for glyph in glyphs
        if glyph.mark_placement is not None
    )
    by_placement: dict[str, list[ReleaseGlyph]] = {}
    for glyph in marks:
        by_placement.setdefault(glyph.mark_placement or "", []).append(glyph)
        if glyph.horizontal_metric[0] != 0 or glyph.vertical_metric[0] != 0:
            raise ReleaseFontBuildError(
                f"U+{glyph.codepoint:04X}: nonspacing mark advances are not zero"
            )
    bases = tuple(
        glyph
        for glyph in glyphs
        if glyph.outline_required and glyph.mark_placement is None
    )
    if not marks:
        raise ReleaseFontBuildError("release repertoire has no visible marks")

    class_names = {
        placement: f"@MARK_{placement.upper().replace('-', '_')}"
        for placement in sorted(by_placement)
    }
    lines: list[str] = []
    for placement in sorted(by_placement):
        class_id = class_names[placement]
        for glyph in by_placement[placement]:
            lines.append(
                f"markClass {glyph.name} <anchor 0 0> {class_id};"
            )

    base_lookups: list[str] = []
    placements = tuple(sorted(by_placement))
    for start in range(0, len(bases), MARK_BASE_LOOKUP_CHUNK):
        lookup = f"MARK_BASE_{len(base_lookups):03d}"
        base_lookups.append(lookup)
        lines.append(f"lookup {lookup} useExtension {{")
        for base in bases[start : start + MARK_BASE_LOOKUP_CHUNK]:
            pieces = [f"  pos base {base.name}"]
            for placement in placements:
                x, y = _mark_anchor(base, placement)
                pieces.append(
                    f"<anchor {x} {y}> mark {class_names[placement]}"
                )
            lines.append(" ".join(pieces) + ";")
        lines.append(f"}} {lookup};")

    mkmk_lookups: list[str] = []
    for placement in placements:
        lookup = f"MARK_MARK_{placement.upper().replace('-', '_')}"
        mkmk_lookups.append(lookup)
        lines.append(f"lookup {lookup} useExtension {{")
        class_id = class_names[placement]
        for mark in marks:
            x, y = _mark_anchor(mark, placement)
            lines.append(
                f"  pos mark {mark.name} <anchor {x} {y}> mark {class_id};"
            )
        lines.append(f"}} {lookup};")

    lines.append("feature mark {")
    lines.extend(f"  lookup {lookup};" for lookup in base_lookups)
    lines.append("} mark;")
    lines.append("feature mkmk {")
    lines.extend(f"  lookup {lookup};" for lookup in mkmk_lookups)
    lines.append("} mkmk;")
    return "\n".join(lines) + "\n", {
        "mark_glyph_count": len(marks),
        "base_glyph_count": len(bases),
        "placement_class_count": len(placements),
        "mark_to_base_lookups": len(base_lookups),
        "mark_to_mark_lookups": len(mkmk_lookups),
    }


def _vertical_feature(
    alternates: Sequence[VerticalAlternate],
) -> tuple[str, Mapping[str, int]]:
    if not alternates:
        return "", {
            "vertical_substitution_count": 0,
            "vertical_feature_count": 0,
        }
    lines = ["lookup VERTICAL_ALTERNATES {"]
    lines.extend(
        f"  sub {alternate.base_name} by {alternate.name};"
        for alternate in alternates
    )
    lines.extend(
        (
            "} VERTICAL_ALTERNATES;",
            "feature vert {",
            "  lookup VERTICAL_ALTERNATES;",
            "} vert;",
            "feature vrt2 {",
            "  lookup VERTICAL_ALTERNATES;",
            "} vrt2;",
        )
    )
    return "\n".join(lines) + "\n", {
        "vertical_substitution_count": len(alternates),
        "vertical_feature_count": 2,
    }


def _win_extents(
    notdef: Glyph,
    glyphs: Sequence[ReleaseGlyph],
    alternates: Sequence[VerticalAlternate],
) -> tuple[int, int]:
    values: list[int] = []
    for outline in (
        notdef,
        *(glyph.outline for glyph in glyphs),
        *(alternate.outline for alternate in alternates),
    ):
        bounds = _bounds(outline)
        if bounds is not None:
            values.extend((bounds[1], bounds[3]))
    if not values:
        raise ReleaseFontBuildError("release has no visible outline extents")
    return max(960, max(values)), max(112, -min(values))


def _required_outline_ymax(
    glyphs: Sequence[ReleaseGlyph],
    codepoint: int,
) -> int:
    glyph = next(
        (item for item in glyphs if item.codepoint == codepoint),
        None,
    )
    bounds = None if glyph is None else _bounds(glyph.outline)
    if bounds is None:
        raise ReleaseFontBuildError(
            f"U+{codepoint:04X} outline is required for font metadata"
        )
    return bounds[3]


def _font_builder(
    glyphs: Sequence[ReleaseGlyph],
    *,
    notdef: Glyph,
    x_height: int,
    cap_height: int,
    alternates: Sequence[VerticalAlternate] = (),
    identity: FontIdentity = CLEAR_HAND_IDENTITY,
) -> tuple[FontBuilder, Mapping[str, Any]]:
    order = [
        ".notdef",
        *(glyph.name for glyph in glyphs),
        *(alternate.name for alternate in alternates),
    ]
    if len(set(order)) != len(order):
        raise ReleaseFontBuildError("release glyph names are not unique")
    cmap = {glyph.codepoint: glyph.name for glyph in glyphs}
    if len(cmap) != len(glyphs):
        raise ReleaseFontBuildError("release cmap has duplicate codepoints")
    outlines = {".notdef": deepcopy(notdef)}
    outlines.update({glyph.name: deepcopy(glyph.outline) for glyph in glyphs})
    outlines.update(
        {
            alternate.name: deepcopy(alternate.outline)
            for alternate in alternates
        }
    )
    hmetrics = {".notdef": (UPM, 96)}
    hmetrics.update(
        {glyph.name: glyph.horizontal_metric for glyph in glyphs}
    )
    hmetrics.update(
        {
            alternate.name: alternate.horizontal_metric
            for alternate in alternates
        }
    )
    vmetrics = {
        ".notdef": (UPM, VERTICAL_ORIGIN_Y - (_bounds(notdef) or (0, 0, 0, 0))[3])
    }
    vmetrics.update(
        {glyph.name: glyph.vertical_metric for glyph in glyphs}
    )
    vmetrics.update(
        {
            alternate.name: alternate.vertical_metric
            for alternate in alternates
        }
    )
    win_ascent, win_descent = _win_extents(
        notdef,
        glyphs,
        alternates,
    )
    if x_height <= 0 or cap_height <= 0:
        raise ReleaseFontBuildError(
            "x-height and cap-height must be measured positive values"
        )

    builder = FontBuilder(UPM, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(outlines)
    builder.setupHorizontalMetrics(hmetrics)
    builder.setupVerticalMetrics(vmetrics)
    builder.setupHorizontalHeader(
        ascent=ASCENDER,
        descent=DESCENDER,
        lineGap=LINE_GAP,
    )
    builder.setupVerticalHeader(
        ascent=500,
        descent=-500,
        lineGap=0,
        caretSlopeRise=VERTICAL_CARET_SLOPE_RISE,
        caretSlopeRun=VERTICAL_CARET_SLOPE_RUN,
        caretOffset=VERTICAL_CARET_OFFSET,
    )
    builder.setupNameTable(
        {
            "familyName": identity.family,
            "styleName": identity.style,
            "uniqueFontIdentifier": identity.unique_id,
            "fullName": identity.full_name,
            "psName": identity.postscript_name,
            "version": identity.version,
            "copyright": identity.copyright,
            "licenseDescription": identity.license_description,
            "licenseInfoURL": identity.license_url,
        }
    )
    builder.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=LINE_GAP,
        usWinAscent=win_ascent,
        usWinDescent=win_descent,
        achVendID="CDFT",
        usWeightClass=400,
        usWidthClass=5,
        fsSelection=0x0040,
        fsType=0,
        ySubscriptXSize=650,
        ySubscriptYSize=600,
        ySubscriptXOffset=0,
        ySubscriptYOffset=75,
        ySuperscriptXSize=650,
        ySuperscriptYSize=600,
        ySuperscriptXOffset=0,
        ySuperscriptYOffset=350,
        yStrikeoutSize=STRIKEOUT_SIZE,
        yStrikeoutPosition=STRIKEOUT_POSITION,
        sxHeight=x_height,
        sCapHeight=cap_height,
    )
    builder.setupPost(
        keepGlyphNames=True,
        underlinePosition=UNDERLINE_POSITION,
        underlineThickness=UNDERLINE_THICKNESS,
    )
    builder.setupMaxp()

    kern_feature, kern_pairs = _kerning_feature(glyphs)
    mark_feature, mark_summary = _mark_feature(glyphs)
    vertical_feature, vertical_summary = _vertical_feature(alternates)
    feature_text = kern_feature + mark_feature + vertical_feature
    addOpenTypeFeaturesFromString(builder.font, feature_text)
    builder.font["head"].fontRevision = identity.revision
    builder.font["head"].created = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font["head"].modified = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font.recalcTimestamp = False
    return builder, {
        "kern_pair_rules": kern_pairs,
        **dict(mark_summary),
        **dict(vertical_summary),
        "feature_text_sha256": _sha256_text(feature_text),
    }


def _write_sfnt_fonts(
    stage: Path,
    *,
    glyphs: Sequence[ReleaseGlyph],
    alternates: Sequence[VerticalAlternate],
    notdef: Glyph,
    identity: FontIdentity = CLEAR_HAND_IDENTITY,
) -> tuple[Path, Path, Mapping[str, Any]]:
    directory = stage / "font"
    directory.mkdir(parents=True, exist_ok=True)
    ttf = directory / f"{identity.postscript_name}.ttf"
    otf = directory / f"{identity.postscript_name}.otf"
    x_height = _required_outline_ymax(glyphs, ord("x"))
    cap_height = _required_outline_ymax(glyphs, ord("H"))
    builder, summary = _font_builder(
        glyphs,
        alternates=alternates,
        notdef=notdef,
        x_height=x_height,
        cap_height=cap_height,
        identity=identity,
    )
    builder.save(ttf)
    second, second_summary = _font_builder(
        glyphs,
        alternates=alternates,
        notdef=notdef,
        x_height=x_height,
        cap_height=cap_height,
        identity=identity,
    )
    if second_summary != summary:
        raise ReleaseFontBuildError("OpenType feature construction is unstable")
    second.save(otf)
    return ttf, otf, summary


def _name_values(font: TTFont, name_id: int) -> set[str]:
    values: set[str] = set()
    for record in font["name"].names:
        if record.nameID == name_id:
            values.add(record.toUnicode())
    return values


def _gsub_feature_mapping(
    font: TTFont,
    feature_tag: str,
) -> dict[str, str]:
    if "GSUB" not in font:
        raise ReleaseFontBuildError("release GSUB table is missing")
    table = font["GSUB"].table
    if table.FeatureList is None or table.LookupList is None:
        raise ReleaseFontBuildError("release GSUB feature/lookup list is missing")
    records = [
        record
        for record in table.FeatureList.FeatureRecord
        if record.FeatureTag == feature_tag
    ]
    if len(records) != 1:
        raise ReleaseFontBuildError(
            f"GSUB {feature_tag} feature count is {len(records)}, expected 1"
        )
    mapping: dict[str, str] = {}
    lookups = table.LookupList.Lookup
    for lookup_index in records[0].Feature.LookupListIndex:
        if not 0 <= lookup_index < len(lookups):
            raise ReleaseFontBuildError(
                f"GSUB {feature_tag} lookup index is out of range"
            )
        lookup = lookups[lookup_index]
        if lookup.LookupType != 1:
            raise ReleaseFontBuildError(
                f"GSUB {feature_tag} must contain only SingleSubst lookups"
            )
        for subtable in lookup.SubTable:
            subtable_mapping = getattr(subtable, "mapping", None)
            if not isinstance(subtable_mapping, dict):
                raise ReleaseFontBuildError(
                    f"GSUB {feature_tag} SingleSubst mapping is malformed"
                )
            for source, target in subtable_mapping.items():
                previous = mapping.setdefault(source, target)
                if previous != target:
                    raise ReleaseFontBuildError(
                        f"GSUB {feature_tag} has conflicting substitution "
                        f"for {source}"
                    )
    return mapping


def _validate_font(
    path: Path,
    glyphs: Sequence[ReleaseGlyph],
    alternates: Sequence[VerticalAlternate],
    *,
    notdef: Glyph,
    identity: FontIdentity = CLEAR_HAND_IDENTITY,
    expected_total_glyph_count: int = TOTAL_GLYPH_COUNT,
) -> None:
    font = _open_validated_font(path)
    try:
        if "glyf" not in font or "CFF " in font or "CFF2" in font:
            raise ReleaseFontBuildError(
                f"{path}: release must use TrueType quadratic glyf"
            )
        if "vhea" not in font or "vmtx" not in font:
            raise ReleaseFontBuildError(f"{path}: vertical metrics are missing")
        vhea = font["vhea"]
        if (
            vhea.caretSlopeRise != VERTICAL_CARET_SLOPE_RISE
            or vhea.caretSlopeRun != VERTICAL_CARET_SLOPE_RUN
            or vhea.caretOffset != VERTICAL_CARET_OFFSET
        ):
            raise ReleaseFontBuildError(
                f"{path}: vertical caret slope metadata drift"
            )
        expected_order = [
            ".notdef",
            *(glyph.name for glyph in glyphs),
            *(alternate.name for alternate in alternates),
        ]
        if font.getGlyphOrder() != expected_order:
            raise ReleaseFontBuildError(f"{path}: glyph order drift")
        if len(expected_order) != expected_total_glyph_count:
            raise ReleaseFontBuildError(
                f"{path}: total glyph count is {len(expected_order)}, "
                f"expected {expected_total_glyph_count}"
            )
        expected_cmap = {
            glyph.codepoint: glyph.name for glyph in glyphs
        }
        if font.getBestCmap() != expected_cmap:
            raise ReleaseFontBuildError(f"{path}: cmap drift")
        built_notdef = font["glyf"][".notdef"]
        if (
            built_notdef.isComposite()
            or built_notdef.numberOfContours <= 0
            or _outline_signature(built_notdef) != _outline_signature(notdef)
        ):
            raise ReleaseFontBuildError(f"{path}: .notdef outline drift")
        for glyph in glyphs:
            built = font["glyf"][glyph.name]
            expected_contours = glyph.outline.numberOfContours
            if built.isComposite() or built.numberOfContours != expected_contours:
                raise ReleaseFontBuildError(
                    f"{path}: {glyph.name} outline drift"
                )
            if _outline_signature(built) != _outline_signature(glyph.outline):
                raise ReleaseFontBuildError(
                    f"{path}: {glyph.name} compiled outline bytes drift"
                )
            if glyph.outline_required and built.numberOfContours <= 0:
                raise ReleaseFontBuildError(
                    f"{path}: {glyph.name} is unexpectedly empty"
                )
            if not glyph.outline_required and built.numberOfContours != 0:
                raise ReleaseFontBuildError(
                    f"{path}: {glyph.name} semantic glyph has ink"
                )
            if font["hmtx"].metrics[glyph.name] != glyph.horizontal_metric:
                raise ReleaseFontBuildError(
                    f"{path}: {glyph.name} hmtx drift"
                )
            if font["vmtx"].metrics[glyph.name] != glyph.vertical_metric:
                raise ReleaseFontBuildError(
                    f"{path}: {glyph.name} vmtx drift"
                )
        for alternate in alternates:
            built = font["glyf"][alternate.name]
            if (
                built.isComposite()
                or built.numberOfContours
                != alternate.outline.numberOfContours
                or built.numberOfContours <= 0
            ):
                raise ReleaseFontBuildError(
                    f"{path}: {alternate.name} vertical outline drift"
                )
            if _outline_signature(built) != _outline_signature(
                alternate.outline
            ):
                raise ReleaseFontBuildError(
                    f"{path}: {alternate.name} compiled outline bytes drift"
                )
            if (
                font["hmtx"].metrics[alternate.name]
                != alternate.horizontal_metric
                or font["hmtx"].metrics[alternate.name][0]
                != font["hmtx"].metrics[alternate.base_name][0]
            ):
                raise ReleaseFontBuildError(
                    f"{path}: {alternate.name} did not inherit base "
                    "horizontal advance"
                )
            if (
                font["vmtx"].metrics[alternate.name]
                != alternate.vertical_metric
                or font["vmtx"].metrics[alternate.name][0]
                != font["vmtx"].metrics[alternate.base_name][0]
            ):
                raise ReleaseFontBuildError(
                    f"{path}: {alternate.name} did not inherit base "
                    "vertical advance"
                )
        if font["vmtx"].metrics["uni3031"][0] != 2048:
            raise ReleaseFontBuildError(f"{path}: U+3031 vAdvance drift")
        if font["vmtx"].metrics["uni3032"][0] != 2048:
            raise ReleaseFontBuildError(f"{path}: U+3032 vAdvance drift")
        if "GPOS" not in font or "GDEF" not in font:
            raise ReleaseFontBuildError(
                f"{path}: GPOS/GDEF mark and kerning tables are missing"
            )
        feature_tags = {
            record.FeatureTag
            for record in font["GPOS"].table.FeatureList.FeatureRecord
        }
        if not {"kern", "mark", "mkmk"}.issubset(feature_tags):
            raise ReleaseFontBuildError(
                f"{path}: required GPOS features missing: {feature_tags}"
            )
        expected_vertical_mapping = {
            alternate.base_name: alternate.name
            for alternate in alternates
        }
        if len(expected_vertical_mapping) != VERTICAL_ALTERNATE_COUNT:
            raise ReleaseFontBuildError(
                f"{path}: vertical base mapping is not exactly "
                f"{VERTICAL_ALTERNATE_COUNT}"
            )
        for tag in ("vert", "vrt2"):
            actual_mapping = _gsub_feature_mapping(font, tag)
            if actual_mapping != expected_vertical_mapping:
                raise ReleaseFontBuildError(
                    f"{path}: GSUB {tag} substitution mapping drift"
                )
        gdef = font["GDEF"].table.GlyphClassDef
        mark_names = {
            glyph.name
            for glyph in glyphs
            if glyph.mark_placement is not None
        }
        if not mark_names or any(
            gdef.classDefs.get(name) != 3 for name in mark_names
        ):
            raise ReleaseFontBuildError(
                f"{path}: GDEF does not classify all visible marks"
            )
        expected_names = {
            1: {identity.family},
            2: {identity.style},
            3: {identity.unique_id},
            4: {identity.full_name},
            5: {identity.version},
            6: {identity.postscript_name},
            13: {identity.license_description},
            14: {identity.license_url},
        }
        for name_id, expected in expected_names.items():
            if _name_values(font, name_id) != expected:
                raise ReleaseFontBuildError(
                    f"{path}: name ID {name_id} mismatch"
                )
        if font["OS/2"].fsType != 0:
            raise ReleaseFontBuildError(
                f"{path}: embedding permissions are not OFL-compatible"
            )
        if not math.isclose(
            float(font["head"].fontRevision),
            identity.revision,
            abs_tol=1e-5,
        ):
            raise ReleaseFontBuildError(f"{path}: head font revision drift")
        os2 = font["OS/2"]
        if (
            not os2.fsSelection & 0x0040
            or os2.fsSelection & 0x0021
            or os2.usWeightClass != 400
            or os2.usWidthClass != 5
            or os2.yStrikeoutSize != STRIKEOUT_SIZE
            or os2.yStrikeoutPosition != STRIKEOUT_POSITION
            or os2.sxHeight != _required_outline_ymax(glyphs, ord("x"))
            or os2.sCapHeight != _required_outline_ymax(glyphs, ord("H"))
        ):
            raise ReleaseFontBuildError(f"{path}: OS/2 style/height metadata drift")
        post = font["post"]
        if (
            post.underlinePosition != UNDERLINE_POSITION
            or post.underlineThickness != UNDERLINE_THICKNESS
        ):
            raise ReleaseFontBuildError(f"{path}: underline metadata drift")
    finally:
        font.close()


def _vertical_shape_resources(
    path: Path,
) -> tuple[bytes, hb.Font, tuple[str, ...], freetype.Face]:
    data = path.read_bytes()
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    with _open_validated_font(path) as ttfont:
        order = tuple(ttfont.getGlyphOrder())
    return data, font, order, freetype.Face(str(path))


def _vertical_placed_bounds(
    resources: tuple[bytes, hb.Font, tuple[str, ...], freetype.Face],
    *,
    character: str,
    expected_name: str,
) -> tuple[tuple[int, int, int, int], tuple[int, int]]:
    _data, font, order, face = resources
    buffer = hb.Buffer()
    buffer.add_str(character)
    buffer.direction = "ttb"
    buffer.script = "hani"
    buffer.language = "zh-Hant"
    hb.shape(font, buffer, {"vert": True, "vrt2": True})
    if len(buffer.glyph_infos) != 1 or len(buffer.glyph_positions) != 1:
        raise ReleaseFontBuildError(
            f"vertical shaping did not return one glyph for U+{ord(character):04X}"
        )
    glyph_id = int(buffer.glyph_infos[0].codepoint)
    if glyph_id >= len(order) or order[glyph_id] != expected_name:
        actual = order[glyph_id] if glyph_id < len(order) else glyph_id
        raise ReleaseFontBuildError(
            f"vertical shaping U+{ord(character):04X} returned {actual!r}, "
            f"expected {expected_name!r}"
        )
    position = buffer.glyph_positions[0]
    face.load_glyph(
        glyph_id,
        freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING,
    )
    box = face.glyph.outline.get_bbox()
    placed = (
        int(box.xMin) + int(position.x_offset),
        int(box.yMin) + int(position.y_offset),
        int(box.xMax) + int(position.x_offset),
        int(box.yMax) + int(position.y_offset),
    )
    return placed, (int(position.x_advance), int(position.y_advance))


def _validate_vertical_placements(
    release_ttf: Path,
    alternates: Sequence[VerticalAlternate],
) -> Mapping[str, Mapping[str, Any]]:
    release_resources = _vertical_shape_resources(release_ttf)
    preview_resources: dict[
        Path,
        tuple[bytes, hb.Font, tuple[str, ...], freetype.Face],
    ] = {}
    records: dict[str, Mapping[str, Any]] = {}
    for alternate in alternates:
        preview_path = alternate.source_font_path.resolve()
        if _sha256(preview_path) != alternate.source_font_sha256:
            raise ReleaseFontBuildError(
                f"{alternate.name}: approved preview font hash changed"
            )
        if preview_path not in preview_resources:
            preview_resources[preview_path] = _vertical_shape_resources(
                preview_path
            )
        preview = preview_resources[preview_path]
        character = chr(alternate.base_codepoint)
        preview_bounds, preview_advance = _vertical_placed_bounds(
            preview,
            character=character,
            expected_name=alternate.name,
        )
        release_bounds, release_advance = _vertical_placed_bounds(
            release_resources,
            character=character,
            expected_name=alternate.name,
        )
        if release_bounds != preview_bounds:
            raise ReleaseFontBuildError(
                f"{alternate.name}: release placed bounds {release_bounds} "
                f"differ from approved preview {preview_bounds}"
            )
        expected_advance = (0, -alternate.vertical_metric[0])
        if (
            preview_advance != expected_advance
            or release_advance != expected_advance
        ):
            raise ReleaseFontBuildError(
                f"{alternate.name}: vertical shaping advance drift"
            )
        records[alternate.name] = {
            "approved_preview_placed_bounds": list(preview_bounds),
            "release_placed_bounds": list(release_bounds),
            "release_advance": list(release_advance),
        }
    if len(records) != VERTICAL_ALTERNATE_COUNT:
        raise ReleaseFontBuildError(
            "vertical placement validation did not cover all alternates"
        )
    return records


def _write_web_fonts(
    ttf: Path,
    *,
    glyphs: Sequence[ReleaseGlyph],
    alternates: Sequence[VerticalAlternate],
    notdef: Glyph,
    identity: FontIdentity = CLEAR_HAND_IDENTITY,
    expected_total_glyph_count: int = TOTAL_GLYPH_COUNT,
) -> tuple[Path, Path, Path]:
    directory = ttf.parent
    woff = directory / f"{identity.postscript_name}.woff"
    woff2 = directory / f"{identity.postscript_name}.woff2"
    for flavor, destination in (("woff", woff), ("woff2", woff2)):
        font = _open_validated_font(ttf)
        try:
            font.flavor = flavor
            font.recalcTimestamp = False
            font.save(destination, reorderTables=True)
        except Exception as exc:
            raise ReleaseFontBuildError(
                f"cannot create {flavor.upper()}: {exc}"
            ) from exc
        finally:
            font.close()
        _validate_font(
            destination,
            glyphs,
            alternates,
            notdef=notdef,
            identity=identity,
            expected_total_glyph_count=expected_total_glyph_count,
        )
    css = directory / f"{identity.postscript_name}.css"
    css.write_text(
        "@font-face {\n"
        f"  font-family: '{identity.family}';\n"
        "  src: "
        f"url('./{woff2.name}') format('woff2'),\n"
        f"       url('./{woff.name}') format('woff');\n"
        "  font-style: normal;\n"
        "  font-weight: 400;\n"
        "  font-display: swap;\n"
        "}\n",
        encoding="utf-8",
    )
    return woff, woff2, css


def _load_bitmap(
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
        return np.zeros((0, 0), dtype=np.uint8)
    raw = np.asarray(bitmap.buffer, dtype=np.uint8)
    if bitmap.pitch < bitmap.width or raw.size < bitmap.pitch * bitmap.rows:
        raise ReleaseFontBuildError(
            f"U+{ord(character):04X}: unsupported FreeType bitmap layout"
        )
    return raw.reshape(bitmap.rows, bitmap.pitch)[:, : bitmap.width].copy()


def _paste_centered(
    canvas: np.ndarray,
    alpha: np.ndarray,
    *,
    x: int,
    y: int,
    cell: int,
    foreground: int,
) -> None:
    if alpha.size == 0:
        return
    height, width = alpha.shape
    if height > cell or width > cell:
        raise ReleaseFontBuildError(
            f"proof glyph {width}x{height} exceeds {cell}px cell"
        )
    left = x + (cell - width) // 2
    top = y + (cell - height) // 2
    target = canvas[top : top + height, left : left + width]
    if target.shape != alpha.shape:
        raise ReleaseFontBuildError("proof glyph would be cropped")
    if foreground == 0:
        target[:] = np.minimum(target, 255 - alpha)
    else:
        target[:] = np.maximum(target, alpha)


def _render_proofs(
    ttf: Path,
    glyphs: Sequence[ReleaseGlyph],
    directory: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    directory.mkdir(parents=True, exist_ok=True)
    face = freetype.Face(str(ttf))
    columns = PROOF_COLUMNS
    rows = math.ceil(len(glyphs) / columns)
    coverage: dict[str, dict[str, int]] = {
        f"U+{glyph.codepoint:04X}": {} for glyph in glyphs
    }
    proof_records: list[dict[str, Any]] = []
    for size in PROOF_SIZES:
        cell = max(32, size + 16)
        width, height = columns * cell, rows * cell
        black = np.full((height, width), 255, dtype=np.uint8)
        white = np.zeros((height, width), dtype=np.uint8)
        for index, glyph in enumerate(glyphs):
            alpha = _load_bitmap(face, glyph.character, size)
            count = int(np.count_nonzero(alpha))
            if glyph.outline_required and count <= 0:
                raise ReleaseFontBuildError(
                    f"U+{glyph.codepoint:04X}: zero {size}px coverage"
                )
            if not glyph.outline_required and count != 0:
                raise ReleaseFontBuildError(
                    f"U+{glyph.codepoint:04X}: semantic glyph renders ink"
                )
            coverage[f"U+{glyph.codepoint:04X}"][str(size)] = count
            row, column = divmod(index, columns)
            _paste_centered(
                black,
                alpha,
                x=column * cell,
                y=row * cell,
                cell=cell,
                foreground=0,
            )
            _paste_centered(
                white,
                alpha,
                x=column * cell,
                y=row * cell,
                cell=cell,
                foreground=255,
            )
        for polarity, pixels in (
            ("black-on-white", black),
            ("white-on-black", white),
        ):
            path = directory / f"{polarity}-{size}px.png"
            Image.fromarray(pixels, mode="L").save(path, optimize=False)
            proof_records.append(
                {
                    "polarity": polarity,
                    "size_px": size,
                    "path": f"proof/{path.name}",
                    "sha256": _sha256(path),
                    "width_px": width,
                    "height_px": height,
                    "columns": columns,
                    "rows": rows,
                    "cell_size_px": cell,
                    "sequence": (
                        "common-han-rank-then-nonhan-codepoint-row-major"
                    ),
                }
            )
    return proof_records, coverage


def _render_vertical_shaping_proofs(
    ttf: Path,
    alternates: Sequence[VerticalAlternate],
    directory: Path,
) -> list[dict[str, Any]]:
    if len(alternates) != VERTICAL_ALTERNATE_COUNT:
        raise ReleaseFontBuildError(
            "vertical shaping proof requires exactly 93 alternates"
        )
    _data, font, order, face = _vertical_shape_resources(ttf)
    size = 56
    face.set_pixel_sizes(0, size)
    columns = 12
    rows = math.ceil(len(alternates) / columns)
    cell_width = 104
    cell_height = 112
    label_height = 20
    em_left_padding = (cell_width - size) // 2
    width = columns * cell_width
    height = rows * cell_height
    black = Image.new("L", (width, height), 255)
    white = Image.new("L", (width, height), 0)
    black_draw = ImageDraw.Draw(black)
    white_draw = ImageDraw.Draw(white)
    flags = (
        freetype.FT_LOAD_RENDER
        | freetype.FT_LOAD_NO_HINTING
        | freetype.FT_LOAD_TARGET_NORMAL
    )

    for index, alternate in enumerate(alternates):
        character = chr(alternate.base_codepoint)
        buffer = hb.Buffer()
        buffer.add_str(character)
        buffer.direction = "ttb"
        buffer.script = "hani"
        buffer.language = "zh-Hant"
        hb.shape(font, buffer, {"vert": True, "vrt2": True})
        if len(buffer.glyph_infos) != 1 or len(buffer.glyph_positions) != 1:
            raise ReleaseFontBuildError(
                f"{alternate.name}: proof shaping cardinality drift"
            )
        glyph_id = int(buffer.glyph_infos[0].codepoint)
        if glyph_id >= len(order) or order[glyph_id] != alternate.name:
            raise ReleaseFontBuildError(
                f"{alternate.name}: proof did not use approved alternate"
            )
        position = buffer.glyph_positions[0]
        face.load_glyph(glyph_id, flags)
        bitmap = face.glyph.bitmap
        raw = np.asarray(bitmap.buffer, dtype=np.uint8)
        if (
            bitmap.width <= 0
            or bitmap.rows <= 0
            or bitmap.pitch < bitmap.width
            or raw.size < bitmap.pitch * bitmap.rows
        ):
            raise ReleaseFontBuildError(
                f"{alternate.name}: invalid vertical proof bitmap"
            )
        alpha = raw.reshape(bitmap.rows, bitmap.pitch)[:, : bitmap.width]
        alpha_image = Image.fromarray(alpha.copy(), mode="L")

        row, column = divmod(index, columns)
        cell_left = column * cell_width
        cell_top = row * cell_height
        em_left = cell_left + em_left_padding
        em_top = cell_top + label_height
        origin_x = em_left + size // 2
        origin_y = em_top
        x_offset = round(int(position.x_offset) * size / UPM)
        y_offset = round(int(position.y_offset) * size / UPM)
        paste_left = origin_x + x_offset + int(face.glyph.bitmap_left)
        paste_top = origin_y - y_offset - int(face.glyph.bitmap_top)
        if (
            paste_left < cell_left
            or paste_top < cell_top
            or paste_left + bitmap.width > cell_left + cell_width
            or paste_top + bitmap.rows > cell_top + cell_height
        ):
            raise ReleaseFontBuildError(
                f"{alternate.name}: vertical shaping proof would crop glyph"
            )

        label = f"U+{alternate.base_codepoint:04X}"
        black_draw.text((cell_left + 3, cell_top + 3), label, fill=80)
        white_draw.text((cell_left + 3, cell_top + 3), label, fill=175)
        black_draw.rectangle(
            (em_left, em_top, em_left + size, em_top + size),
            outline=210,
        )
        white_draw.rectangle(
            (em_left, em_top, em_left + size, em_top + size),
            outline=45,
        )
        black.paste(
            0,
            (paste_left, paste_top),
            alpha_image,
        )
        white.paste(
            255,
            (paste_left, paste_top),
            alpha_image,
        )

    records: list[dict[str, Any]] = []
    for polarity, image in (
        ("black-on-white", black),
        ("white-on-black", white),
    ):
        path = directory / f"vertical-shaping-{polarity}-{size}px.png"
        image.save(path, optimize=False)
        records.append(
            {
                "kind": "vertical-shaping",
                "polarity": polarity,
                "size_px": size,
                "path": f"proof/{path.name}",
                "sha256": _sha256(path),
                "width_px": width,
                "height_px": height,
                "columns": columns,
                "rows": rows,
                "cell_width_px": cell_width,
                "cell_height_px": cell_height,
                "glyph_count": len(alternates),
                "shaping": "HarfBuzz ttb with vert and vrt2",
                "placement_contract": (
                    "base advances with approved preview placement"
                ),
            }
        )
    return records


def _copy_ofl(stage: Path, project_root: Path) -> Path:
    source = project_root.joinpath(*OFL_RELATIVE_PATH.parts)
    if not source.is_file() or _sha256(source) != OFL_SHA256:
        raise ReleaseFontBuildError("canonical OFL.txt is missing or changed")
    destination = stage / OFL_RELATIVE_PATH.name
    shutil.copyfile(source, destination)
    if _sha256(destination) != OFL_SHA256:
        raise ReleaseFontBuildError("copied OFL hash drift")
    return destination


def _artifact_hashes(stage: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(stage.rglob("*")):
        if path.is_symlink():
            raise ReleaseFontBuildError(
                f"release artifact symlinks are forbidden: {path}"
            )
        if not path.is_file():
            continue
        relative = path.relative_to(stage)
        if relative == Path("report.json"):
            continue
        result[relative.as_posix()] = _sha256(path)
    return result


def _validated_release_destination(
    project_root: Path,
    output_directory: Path,
) -> Path:
    """Return one canonical, non-symlink release destination.

    Release installation is intentionally restricted to the two repository
    locations whose contents are disposable build products.  In particular,
    the approved evidence tree below ``build/imagegen/imagegen-*`` must never
    be accepted as an output destination.
    """

    project_root = project_root.resolve()
    raw_output = output_directory
    if not raw_output.is_absolute():
        raw_output = project_root / raw_output
    lexical_output = Path(os.path.abspath(os.fspath(raw_output)))
    allowed = {
        project_root / DIST_RELATIVE_DIRECTORY,
        project_root / "build/imagegen/release-9120",
    }
    if lexical_output not in allowed:
        choices = ", ".join(sorted(path.as_posix() for path in allowed))
        raise ReleaseFontBuildError(
            f"release output must be exactly one of: {choices}"
        )

    relative = lexical_output.relative_to(project_root)
    cursor = project_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ReleaseFontBuildError(
                f"release output path contains a symlink: {cursor}"
            )
    if lexical_output.exists() and not lexical_output.is_dir():
        raise ReleaseFontBuildError(
            f"release output exists but is not a directory: {lexical_output}"
        )
    return lexical_output


def _unused_backup_path(destination: Path) -> Path:
    for _ in range(128):
        candidate = destination.with_name(
            f".{destination.name}.backup-{secrets.token_hex(16)}"
        )
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
    raise ReleaseFontBuildError(
        f"cannot allocate a release backup path beside {destination}"
    )


def _install_release_directory(stage: Path, destination: Path) -> None:
    """Install ``stage`` and restore the prior release on swap failure."""

    backup: Path | None = None
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise ReleaseFontBuildError(
                f"release destination is not a regular directory: {destination}"
            )
        backup = _unused_backup_path(destination)
        try:
            destination.replace(backup)
        except OSError as exc:
            raise ReleaseFontBuildError(
                f"cannot move the existing release to its backup: {exc}"
            ) from exc

    try:
        stage.replace(destination)
    except OSError as install_error:
        if backup is not None:
            try:
                backup.replace(destination)
            except OSError as rollback_error:
                raise ReleaseFontBuildError(
                    "release install failed and the previous release could not "
                    f"be restored; preserved backup: {backup}; "
                    f"install error: {install_error}; "
                    f"rollback error: {rollback_error}"
                ) from rollback_error
        raise ReleaseFontBuildError(
            f"release install failed; previous release restored: {install_error}"
        ) from install_error

    if backup is not None:
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            raise ReleaseFontBuildError(
                "new release is installed, but its obsolete backup could not "
                f"be removed: {backup}: {exc}"
            ) from exc


def _validate_repertoire_partition(
    han: Sequence[ReleaseGlyph],
    nonhan: Sequence[ReleaseGlyph],
) -> tuple[ReleaseGlyph, ...]:
    han_codepoints = {glyph.codepoint for glyph in han}
    nonhan_codepoints = {glyph.codepoint for glyph in nonhan}
    overlap = han_codepoints & nonhan_codepoints
    if overlap:
        raise ReleaseFontBuildError(
            f"Han/non-Han repertoire overlap: {sorted(overlap)}"
        )
    combined = tuple(han) + tuple(nonhan)
    if len(combined) != CMAP_COUNT:
        raise ReleaseFontBuildError(
            f"release cmap count is {len(combined)}, expected {CMAP_COUNT}"
        )
    visible = sum(glyph.outline_required for glyph in combined)
    empty = len(combined) - visible
    if visible != HAN_COUNT + VISIBLE_NONHAN_COUNT:
        raise ReleaseFontBuildError(
            f"visible glyph count is {visible}, expected "
            f"{HAN_COUNT + VISIBLE_NONHAN_COUNT}"
        )
    if empty != SEMANTIC_EMPTY_COUNT:
        raise ReleaseFontBuildError(
            f"semantic empty count is {empty}, expected {SEMANTIC_EMPTY_COUNT}"
        )
    return combined


def _approval_record(
    admitted: Any,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "batch_id": admitted.batch.batch_id,
        "path": _project_relative(admitted.approval_path, project_root),
        "sha256": admitted.approval_sha256,
        "reviewer": admitted.reviewer_name,
        "reviewed_at": admitted.reviewed_at,
        "approver": admitted.approver_name,
        "approved_at": admitted.approved_at,
    }


def _vertical_approval_record(
    approval: Mapping[str, Any],
    *,
    project_root: Path,
) -> dict[str, Any]:
    batch_id = approval.get("batch_id")
    if not isinstance(batch_id, str):
        raise ReleaseFontBuildError(
            "vertical approval is missing its batch identity"
        )
    try:
        _build, review_path, review = vertical_approval.validate_review(
            batch_id,
            project_root=project_root,
        )
    except vertical_approval.VerticalApprovalError as exc:
        raise ReleaseFontBuildError(str(exc)) from exc
    approval_path = (
        project_root
        / f"sources/imagegen/approvals/{batch_id}.approval.json"
    )
    return {
        "batch_id": batch_id,
        "path": _project_relative(approval_path, project_root),
        "sha256": _sha256(approval_path),
        "reviewer": review["reviewer_name"],
        "reviewed_at": review["reviewed_at"],
        "approver": approval["approver_name"],
        "approved_at": approval["approved_at"],
        "vector_review": _project_relative(review_path, project_root),
        "vector_review_sha256": _sha256(review_path),
    }


def _vertical_repertoire_record(
    *,
    project_root: Path,
) -> dict[str, Any]:
    try:
        build = vertical_approval.validate_build(
            "vertical-0001",
            project_root=project_root,
        )
    except vertical_approval.VerticalApprovalError as exc:
        raise ReleaseFontBuildError(str(exc)) from exc
    relative = build.report.get("source_repertoire")
    digest = build.report.get("source_repertoire_sha256")
    if not isinstance(relative, str) or not isinstance(digest, str):
        raise ReleaseFontBuildError(
            "vertical build has no canonical repertoire provenance"
        )
    path = project_root / relative
    if (
        not path.is_file()
        or _project_relative(path, project_root) != relative
        or _sha256(path) != digest
        or digest != vertical_approval.pipeline.REPERTOIRE_SHA256
    ):
        raise ReleaseFontBuildError("vertical repertoire path/hash drift")
    try:
        repertoire = vertical_approval.pipeline.load_frozen_repertoire(
            path,
            project_root=project_root,
        )
    except vertical_approval.pipeline.VerticalPipelineError as exc:
        raise ReleaseFontBuildError(str(exc)) from exc
    return {
        "path": relative,
        "sha256": digest,
        "repertoire_id": repertoire["repertoire_id"],
        "sequence_sha256": (
            vertical_approval.pipeline.REPERTOIRE_SEQUENCE_SHA256
        ),
        "count": VERTICAL_ALTERNATE_COUNT,
        "encoding": "unencoded-glyphs-reached-by-GSUB",
    }


def _nonhan_repertoire_record(
    repertoire: nonhan_approval.Repertoire,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Return the exact frozen non-Han repertoire and sequence provenance."""

    expected_sequence_hashes = {
        "serialization": nonhan_approval.SEQUENCE_HASH_SERIALIZATION,
        "canonical": nonhan_approval.CANONICAL_SEQUENCE_SHA256,
        "authoring": nonhan_approval.AUTHORING_SEQUENCE_SHA256,
        "visible_authoring": (
            nonhan_approval.VISIBLE_AUTHORING_SEQUENCE_SHA256
        ),
    }
    actual_sequence_hashes = dict(repertoire.sequence_hashes)
    if (
        set(actual_sequence_hashes) != set(expected_sequence_hashes)
        or actual_sequence_hashes != expected_sequence_hashes
    ):
        raise ReleaseFontBuildError(
            "validated non-Han repertoire sequence-hash schema drift"
        )
    if (
        repertoire.repertoire_id != nonhan_approval.REPERTOIRE_ID
        or repertoire.sha256 != nonhan_approval.REPERTOIRE_SHA256
        or len(repertoire.glyphs) != NONHAN_COUNT
    ):
        raise ReleaseFontBuildError(
            "validated non-Han repertoire identity/count drift"
        )
    relative_path = _project_relative(repertoire.path, project_root)
    if (
        relative_path
        != nonhan_approval.REPERTOIRE_RELATIVE_PATH.as_posix()
        or not repertoire.path.is_file()
        or _sha256(repertoire.path) != repertoire.sha256
    ):
        raise ReleaseFontBuildError(
            "validated non-Han repertoire path/hash drift"
        )
    return {
        "path": relative_path,
        "sha256": repertoire.sha256,
        "repertoire_id": repertoire.repertoire_id,
        "count": NONHAN_COUNT,
        "sequence_hashes": {
            **actual_sequence_hashes,
            "serialization_definition": {
                "algorithm": "SHA-256",
                "encoding": "ASCII",
                "record_format": "U+{codepoint:04X}\\n",
                "hexadecimal_case": "uppercase",
                "hexadecimal_width": (
                    "minimum 4 digits; supplementary scalars use 5 or 6 digits"
                ),
                "record_order": "the named repertoire sequence",
                "final_record_terminator": "LF present",
                "byte_order_mark": "none",
            },
        },
    }


def _notdef_report_record(notdef: ReleaseNotdef) -> dict[str, Any]:
    """Return the exact release-report record for glyph-order entry zero."""

    if (
        notdef.source_batch != "common-0001"
        or notdef.source_collection != "common-han-3000"
        or len(notdef.source_font_sha256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in notdef.source_font_sha256
        )
    ):
        raise ReleaseFontBuildError(".notdef source provenance is malformed")
    return {
        "glyph_order_index": 0,
        "glyph_name": ".notdef",
        "encoded": False,
        "source_collection": notdef.source_collection,
        "source_batch": notdef.source_batch,
        "source_font_sha256": notdef.source_font_sha256,
    }


def _characters_sha256_serialization() -> dict[str, str]:
    """Describe the exact bytes hashed by ``coverage.characters_sha256``."""

    return {
        "algorithm": "SHA-256",
        "scope": (
            "encoded glyphs in release glyph order; .notdef and unencoded "
            "vertical alternates excluded"
        ),
        "serialization": (
            "raw Unicode scalar values concatenated without separators or "
            "a final terminator"
        ),
        "normalization": "none",
        "encoding": "UTF-8",
        "byte_order_mark": "none",
    }


def build_release_font(
    *,
    project_root: Path = ROOT,
    output_directory: Path = OUTPUT_DIRECTORY,
) -> Path:
    """Validate all approvals and atomically build the 9,120-codepoint release."""

    project_root = project_root.resolve()
    output_directory = _validated_release_destination(
        project_root,
        output_directory,
    )

    approval_directory = project_root / "sources/imagegen/approvals"
    han_paths = han_approval.discover_approval_paths(
        approval_directory,
        project_root=project_root,
    )
    han_admitted = han_approval.validate_approval_prefix(
        han_paths,
        project_root=project_root,
    )
    if len(han_admitted) != 188:
        raise ReleaseFontBuildError(
            f"common-Han approval set has {len(han_admitted)} batches, expected 188"
        )
    try:
        moe_extension_admitted = moe_common_approval.validate_approval(
            project_root=project_root,
        )
    except moe_common_approval.MoeCommonApprovalError as exc:
        raise ReleaseFontBuildError(str(exc)) from exc
    try:
        dictionary_extension_admitted = (
            han_delta_approval.validate_approval(
                project_root=project_root,
            )
        )
    except han_delta_approval.HanDeltaApprovalError as exc:
        raise ReleaseFontBuildError(str(exc)) from exc
    nonhan_paths = nonhan_approval.discover_approval_paths(
        approval_directory,
        project_root=project_root,
    )
    nonhan_admitted = nonhan_approval.validate_complete_approval_set(
        nonhan_paths,
        project_root=project_root,
    )
    try:
        vertical_admitted = vertical_approval.load_complete_approvals(
            project_root=project_root,
        )
    except vertical_approval.VerticalApprovalError as exc:
        raise ReleaseFontBuildError(str(exc)) from exc

    base_han_glyphs = _extract_han(han_admitted)
    extension_glyphs = _extract_moe_extension(moe_extension_admitted)
    dictionary_glyphs = _extract_dictionary_extension(
        dictionary_extension_admitted
    )
    base_codepoints = {glyph.codepoint for glyph in base_han_glyphs}
    extension_codepoints = {glyph.codepoint for glyph in extension_glyphs}
    dictionary_codepoints = {
        glyph.codepoint for glyph in dictionary_glyphs
    }
    if (
        base_codepoints & extension_codepoints
        or base_codepoints & dictionary_codepoints
        or extension_codepoints & dictionary_codepoints
    ):
        raise ReleaseFontBuildError(
            "approved Han repertoire segments overlap"
        )
    han_glyphs = (
        base_han_glyphs
        + extension_glyphs
        + dictionary_glyphs
    )
    nonhan_glyphs = _extract_nonhan(nonhan_admitted)
    glyphs = _validate_repertoire_partition(han_glyphs, nonhan_glyphs)
    alternates = _extract_vertical_alternates(
        vertical_admitted,
        encoded_glyphs=glyphs,
        project_root=project_root,
    )
    vertical_repertoire = _vertical_repertoire_record(
        project_root=project_root,
    )
    notdef = _notdef_from_first_han(han_admitted)

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{output_directory.name}-",
            dir=output_directory.parent,
        )
    )
    try:
        ttf, otf, feature_summary = _write_sfnt_fonts(
            stage,
            glyphs=glyphs,
            alternates=alternates,
            notdef=notdef.outline,
        )
        _validate_font(
            ttf,
            glyphs,
            alternates,
            notdef=notdef.outline,
        )
        _validate_font(
            otf,
            glyphs,
            alternates,
            notdef=notdef.outline,
        )
        vertical_placement = _validate_vertical_placements(
            ttf,
            alternates,
        )
        woff, woff2, css = _write_web_fonts(
            ttf,
            glyphs=glyphs,
            alternates=alternates,
            notdef=notdef.outline,
        )
        proof_records, coverage = _render_proofs(
            ttf,
            glyphs,
            stage / "proof",
        )
        proof_records.extend(
            _render_vertical_shaping_proofs(
                ttf,
                alternates,
                stage / "proof",
            )
        )
        ofl = _copy_ofl(stage, project_root)

        glyph_records = [
            {
                "glyph_order_index": index,
                "character": glyph.character,
                "codepoint": f"U+{glyph.codepoint:04X}",
                "unicode_name": unicodedata.name(
                    glyph.character, "<UNNAMED>"
                ),
                "glyph_name": glyph.name,
                "outline_required": glyph.outline_required,
                "horizontal_advance": glyph.horizontal_metric[0],
                "left_side_bearing": glyph.horizontal_metric[1],
                "vertical_advance": glyph.vertical_metric[0],
                "top_side_bearing": glyph.vertical_metric[1],
                "profile_id": glyph.profile_id,
                "mark_placement": glyph.mark_placement,
                "source_collection": glyph.source_collection,
                "source_batch": glyph.source_batch,
                "source_font_sha256": glyph.source_font_sha256,
                "coverage_pixels": coverage[
                    f"U+{glyph.codepoint:04X}"
                ],
            }
            for index, glyph in enumerate(glyphs, start=1)
        ]
        vertical_records = [
            {
                "glyph_order_index": CMAP_COUNT + index,
                "base_character": chr(alternate.base_codepoint),
                "base_codepoint": f"U+{alternate.base_codepoint:04X}",
                "base_glyph_name": alternate.base_name,
                "glyph_name": alternate.name,
                "encoded": False,
                "horizontal_advance": alternate.horizontal_metric[0],
                "left_side_bearing": alternate.horizontal_metric[1],
                "vertical_advance": alternate.vertical_metric[0],
                "top_side_bearing": alternate.vertical_metric[1],
                "metric_policy": (
                    "base-advances-with-approved-preview-placement"
                ),
                "preview_horizontal_advance": (
                    alternate.preview_horizontal_metric[0]
                ),
                "preview_left_side_bearing": (
                    alternate.preview_horizontal_metric[1]
                ),
                "preview_vertical_advance": (
                    alternate.preview_vertical_metric[0]
                ),
                "preview_top_side_bearing": (
                    alternate.preview_vertical_metric[1]
                ),
                **vertical_placement[alternate.name],
                "vertical_orientation": alternate.vertical_orientation,
                "tailoring": alternate.tailoring,
                "source_collection": "vertical-alternates-93",
                "source_batch": alternate.source_batch,
                "source_font_sha256": alternate.source_font_sha256,
            }
            for index, alternate in enumerate(alternates, start=1)
        ]
        report: dict[str, Any] = {
            "schema_version": 1,
            "pipeline": PIPELINE_ID,
            "source_policy": SOURCE_POLICY,
            "approval_state": "fully-approved-9120-plus-vertical93",
            "repertoires": {
                "base_han": {
                    "path": _project_relative(
                        han_admitted[0].repertoire.path, project_root
                    ),
                    "sha256": han_admitted[0].repertoire.sha256,
                    "repertoire_id": (
                        han_admitted[0].repertoire.repertoire_id
                    ),
                    "sequence_sha256": (
                        han_admitted[0].repertoire.sequence_sha256
                    ),
                    "count": BASE_HAN_COUNT,
                },
                "moe_common_extension": {
                    "path": _project_relative(
                        moe_extension_admitted.repertoire_path,
                        project_root,
                    ),
                    "sha256": (
                        moe_extension_admitted.repertoire_sha256
                    ),
                    "repertoire_id": (
                        moe_extension_admitted.repertoire_id
                    ),
                    "sequence_sha256": (
                        moe_extension_admitted.sequence_sha256
                    ),
                    "count": MOE_EXTENSION_COUNT,
                },
                "dictionary_salience_extension": {
                    "path": _project_relative(
                        dictionary_extension_admitted.repertoire.path,
                        project_root,
                    ),
                    "sha256": (
                        dictionary_extension_admitted.repertoire.sha256
                    ),
                    "repertoire_id": (
                        dictionary_extension_admitted
                        .repertoire.repertoire_id
                    ),
                    "sequence_sha256": (
                        dictionary_extension_admitted
                        .repertoire.sequence_sha256
                    ),
                    "count": DICTIONARY_EXTENSION_COUNT,
                },
                "nonhan": _nonhan_repertoire_record(
                    nonhan_admitted[0].repertoire,
                    project_root=project_root,
                ),
                "vertical_alternates": vertical_repertoire,
            },
            "coverage": {
                "cmap_count": CMAP_COUNT,
                "total_glyph_count_including_notdef": TOTAL_GLYPH_COUNT,
                "common_han": HAN_COUNT,
                "moe_common": MOE_COMMON_COUNT,
                "moe_common_complete": True,
                "dictionary_salience_extension": (
                    DICTIONARY_EXTENSION_COUNT
                ),
                "nonhan_total": NONHAN_COUNT,
                "nonhan_visible": VISIBLE_NONHAN_COUNT,
                "semantic_empty": SEMANTIC_EMPTY_COUNT,
                "hiragana": sum(
                    0x3041 <= glyph.codepoint <= 0x309F
                    for glyph in glyphs
                ),
                "katakana": sum(
                    0x30A0 <= glyph.codepoint <= 0x30FF
                    for glyph in glyphs
                ),
                "visible_total": HAN_COUNT + VISIBLE_NONHAN_COUNT,
                "unencoded_vertical_alternates": (
                    VERTICAL_ALTERNATE_COUNT
                ),
                "vertical_substitution_bases": (
                    VERTICAL_ALTERNATE_COUNT
                ),
                "glyph_order": (
                    ".notdef; base Han frozen rank 1..3000; "
                    "MOE common extension rank 1..1844; "
                    "dictionary-salience extension rank 1..1216; "
                    "non-Han ascending codepoint; approved unencoded "
                    "vertical alternates rank 1..93"
                ),
                "characters_sha256": _sha256_text(
                    "".join(glyph.character for glyph in glyphs)
                ),
                "characters_sha256_serialization": (
                    _characters_sha256_serialization()
                ),
            },
            "notdef": _notdef_report_record(notdef),
            "font": {
                "family": FONT_FAMILY,
                "style": FONT_STYLE,
                "postscript_name": FONT_PS_NAME,
                "version": FONT_VERSION,
                "head_font_revision": FONT_REVISION,
                "weight_class": 400,
                "width_class": 5,
                "fs_selection": 0x0040,
                "units_per_em": UPM,
                "ascender": ASCENDER,
                "descender": DESCENDER,
                "line_gap": LINE_GAP,
                "vertical_caret_slope_rise": VERTICAL_CARET_SLOPE_RISE,
                "vertical_caret_slope_run": VERTICAL_CARET_SLOPE_RUN,
                "vertical_caret_offset": VERTICAL_CARET_OFFSET,
                "x_height": _required_outline_ymax(glyphs, ord("x")),
                "cap_height": _required_outline_ymax(glyphs, ord("H")),
                "underline_position": UNDERLINE_POSITION,
                "underline_thickness": UNDERLINE_THICKNESS,
                "strikeout_position": STRIKEOUT_POSITION,
                "strikeout_size": STRIKEOUT_SIZE,
                "outline_format": "TrueType quadratic glyf",
                "ttf": f"font/{ttf.name}",
                "ttf_sha256": _sha256(ttf),
                "otf": f"font/{otf.name}",
                "otf_sha256": _sha256(otf),
                "woff": f"font/{woff.name}",
                "woff_sha256": _sha256(woff),
                "woff2": f"font/{woff2.name}",
                "woff2_sha256": _sha256(woff2),
                "css": f"font/{css.name}",
                "css_sha256": _sha256(css),
            },
            "opentype": dict(feature_summary),
            "license": {
                "identifier": "OFL-1.1",
                "path": ofl.name,
                "sha256": _sha256(ofl),
                "metadata": FONT_LICENSE,
                "url": FONT_LICENSE_URL,
                "fsType": 0,
            },
            "approvals": {
                "common_han": [
                    _approval_record(item, project_root=project_root)
                    for item in han_admitted
                ],
                "moe_common_extension": {
                    "path": _project_relative(
                        moe_extension_admitted.approval_path,
                        project_root,
                    ),
                    "sha256": moe_extension_admitted.approval_sha256,
                    "reviewer": moe_extension_admitted.reviewer_name,
                    "reviewed_at": moe_extension_admitted.reviewed_at,
                    "approver": moe_extension_admitted.approver_name,
                    "approved_at": moe_extension_admitted.approved_at,
                    "batch_count": len(moe_extension_admitted.batches),
                    "character_count": len(
                        moe_extension_admitted.characters
                    ),
                },
                "dictionary_salience_extension": {
                    "path": _project_relative(
                        dictionary_extension_admitted.approval_path,
                        project_root,
                    ),
                    "sha256": (
                        dictionary_extension_admitted.approval_sha256
                    ),
                    "review_path": _project_relative(
                        dictionary_extension_admitted.review_path,
                        project_root,
                    ),
                    "review_sha256": (
                        dictionary_extension_admitted.review_sha256
                    ),
                    "reviewer": (
                        dictionary_extension_admitted.reviewer_name
                    ),
                    "reviewer_role": (
                        dictionary_extension_admitted.reviewer_role
                    ),
                    "reviewed_at": (
                        dictionary_extension_admitted.reviewed_at
                    ),
                    "approver": (
                        dictionary_extension_admitted.approver_name
                    ),
                    "approved_at": (
                        dictionary_extension_admitted.approved_at
                    ),
                    "batch_count": len(
                        dictionary_extension_admitted.batches
                    ),
                    "character_count": len(
                        dictionary_extension_admitted.characters
                    ),
                },
                "nonhan": [
                    _approval_record(item, project_root=project_root)
                    for item in nonhan_admitted
                ],
                "vertical_alternates": [
                    _vertical_approval_record(
                        item,
                        project_root=project_root,
                    )
                    for item in vertical_admitted
                ],
            },
            "proofs": proof_records,
            "qa": {
                "proof_sizes_px": list(PROOF_SIZES),
                "proof_polarities": [
                    "black-on-white",
                    "white-on-black",
                ],
                "all_visible_glyphs_nonempty": True,
                "all_semantic_glyphs_zero_ink": True,
                "all_outlines_simple": True,
                "cmap_unique": True,
                "horizontal_metrics_present": True,
                "vertical_metrics_present": True,
                "vertical_alternates_unencoded": True,
                "vert_substitutions_exact": True,
                "vrt2_substitutions_exact": True,
                "vertical_alternates_inherit_base_advances": True,
                "vertical_alternates_preserve_approved_preview_placement": True,
                "woff_validated": True,
                "woff2_validated": True,
                "authored_sources_read": False,
                "fallback_fonts_read": False,
            },
            "glyphs": glyph_records,
            "vertical_alternates": vertical_records,
        }
        report["artifact_sha256"] = _artifact_hashes(stage)
        report_path = stage / "report.json"
        report_path.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        for path in (ttf, otf, woff, woff2):
            _validate_font(
                path,
                glyphs,
                alternates,
                notdef=notdef.outline,
            )
        if report["artifact_sha256"] != _artifact_hashes(stage):
            raise ReleaseFontBuildError(
                "release artifact inventory changed after report creation"
            )
        _install_release_directory(stage, output_directory)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return output_directory


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root containing approvals and OFL.txt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output directory; defaults to build/imagegen/release-9120",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    output = args.output or (
        project_root / "build/imagegen/release-9120"
    )
    if not output.is_absolute():
        output = project_root / output
    result = build_release_font(
        project_root=project_root,
        output_directory=output,
    )
    print(result)
    print(result / "report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
