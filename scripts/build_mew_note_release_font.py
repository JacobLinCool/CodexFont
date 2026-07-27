#!/usr/bin/env python3
"""Compile the approved 9,088-codepoint Mew Note TC preview.

Every visible outline comes from a reviewed family-local imagegen raster.
Only the 17 Unicode semantic-empty scalars receive programmatic empty glyphs.
Metrics, OpenType features, web formats, and vertical substitutions are
derived deterministically from the frozen family repertoires. Two 16-glyph
Han batches withheld by the release approval are not compiled.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unicodedata
from typing import Any, Mapping, Sequence

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
import uharfbuzz as hb

from scripts import build_imagegen_release_font as engine
from scripts import mew_note_release_approval as approval


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "build/families/mew-note-tc/release-9088"
DIST_DIRECTORY = ROOT / "dist/mew-note-tc"
OFL_PATH = ROOT / "OFL.txt"
HAN_REPERTOIRE = (
    ROOT
    / "families/mew-note-tc/sources/imagegen/repertoires/han-6060.json"
)
NONHAN_REPERTOIRE = (
    ROOT
    / "families/mew-note-tc/sources/imagegen/repertoires/nonhan-3060.json"
)
VERTICAL_REPERTOIRE = (
    ROOT
    / "families/mew-note-tc/sources/imagegen/repertoires/vertical-93.json"
)

IDENTITY = engine.FontIdentity(
    family="Mew Note TC",
    style="Regular",
    full_name="Mew Note TC Regular",
    postscript_name="MewNoteTC-Regular",
    version="Version 1.000",
    revision=1.0,
    unique_id="Mew Note TC 1.000",
    copyright="Copyright 2026 The CodexFont Project Authors",
    license_description=engine.FONT_LICENSE,
    license_url=engine.FONT_LICENSE_URL,
)
PIPELINE_ID = (
    "mew-note-tc-approved-imagegen-han6028-nonhan3060-"
    "vertical93-release-v1"
)
SOURCE_POLICY = (
    "approved-family-local-imagegen-raster-outlines-plus-"
    "semantic-empty-glyphs-only;no-clear-hand-outline-reuse;"
    "no-fallback-font-no-outline-substitution"
)
PLANNED_HAN_COUNT = 6_060
HAN_COUNT = 6_028
NONHAN_COUNT = 3_060
CMAP_COUNT = 9_088
VISIBLE_COUNT = 9_071
SEMANTIC_EMPTY_COUNT = 17
VERTICAL_COUNT = 93
TOTAL_GLYPH_COUNT = 1 + CMAP_COUNT + VERTICAL_COUNT
PROOF_SIZES = engine.PROOF_SIZES


class MewNoteReleaseBuildError(RuntimeError):
    """The Mew Note release cannot be compiled without contract drift."""


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteReleaseBuildError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MewNoteReleaseBuildError(f"{path}: {label} must be an object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _codepoint(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("U+"):
        raise MewNoteReleaseBuildError(f"invalid codepoint label {value!r}")
    try:
        result = int(value[2:], 16)
    except ValueError as exc:
        raise MewNoteReleaseBuildError(
            f"invalid codepoint label {value!r}"
        ) from exc
    if value != f"U+{result:04X}":
        raise MewNoteReleaseBuildError(
            f"noncanonical codepoint label {value!r}"
        )
    return result


def _bounds(glyph: Glyph) -> tuple[int, int, int, int]:
    result = engine._bounds(glyph)
    if result is None:
        raise MewNoteReleaseBuildError("visible glyph has no bounds")
    return result


def _shift(glyph: Glyph, *, x: int = 0, y: int = 0) -> None:
    if not x and not y:
        return
    glyph.coordinates = GlyphCoordinates(
        [
            (int(point[0]) + x, int(point[1]) + y)
            for point in glyph.coordinates
        ]
    )


def _mark_placement(character: str) -> str:
    codepoint = ord(character)
    if codepoint in {0x3099, 0x309A}:
        return "above-right"
    ccc = unicodedata.combining(character)
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
    raise MewNoteReleaseBuildError(
        f"U+{codepoint:04X}: unsupported combining class {ccc}"
    )


def _position_visible_nonhan(
    outline: Glyph,
    record: Mapping[str, Any],
) -> tuple[Glyph, tuple[int, int], tuple[int, int], str | None]:
    """Apply the frozen non-Han metric policy without changing stroke shape."""

    result = deepcopy(outline)
    character = str(record["character"])
    codepoint = _codepoint(str(record["codepoint"]))
    metrics = record["metrics"]
    horizontal = metrics["horizontal_advance"]
    vertical = metrics["vertical_advance"]
    bearings = metrics["side_bearings"]
    profile_id = str(record["profile_id"])
    x_min, _y_min, x_max, y_max = _bounds(result)
    ink_width = x_max - x_min
    mark_placement: str | None = None
    kind = horizontal["kind"]
    if kind == "source-proportional":
        left = int(bearings["left"])
        right = int(bearings["right"])
        advance = ink_width + left + right
        _shift(result, x=left - x_min)
    elif kind == "fixed":
        advance = int(horizontal["value"])
        if profile_id == "nonspacing-mark":
            center_x = round((x_min + x_max) / 2)
            placement = _mark_placement(character)
            if placement in {"above", "above-right", "double-above"}:
                y_shift = -_bounds(result)[1]
            elif placement in {"below", "double-below"}:
                y_shift = -_bounds(result)[3]
            else:
                _xm, y_min, _xx, y_max_before = _bounds(result)
                y_shift = -round((y_min + y_max_before) / 2)
            _shift(result, x=-center_x, y=y_shift)
            mark_placement = placement
        else:
            left = int(bearings["left"])
            right = int(bearings["right"])
            available = advance - left - right
            if ink_width > available:
                raise MewNoteReleaseBuildError(
                    f"U+{codepoint:04X}: imagegen ink width {ink_width} "
                    f"exceeds frozen metric envelope {available}; "
                    "regenerate the source glyph narrower"
                )
            _shift(
                result,
                x=left + (available - ink_width) // 2 - x_min,
            )
    else:
        raise MewNoteReleaseBuildError(
            f"U+{codepoint:04X}: visible glyph has unsupported "
            f"advance policy {kind!r}"
        )
    final_x_min, _final_y_min, final_x_max, final_y_max = _bounds(result)
    if profile_id != "nonspacing-mark" and (
        final_x_min < 0 or final_x_max > advance
    ):
        raise MewNoteReleaseBuildError(
            f"U+{codepoint:04X}: positioned outline escapes its advance"
        )
    vertical_advance = int(vertical["value"])
    return (
        result,
        (advance, final_x_min),
        (
            vertical_advance,
            engine.VERTICAL_ORIGIN_Y - final_y_max,
        ),
        mark_placement,
    )


def _load_source_outlines(
    admitted: approval.ApprovedMewNoteRelease,
) -> tuple[
    dict[int, tuple[Glyph, approval.ApprovedVisibleBatch]],
    dict[int, tuple[Glyph, approval.ApprovedVisibleBatch, Mapping[str, Any]]],
]:
    encoded: dict[
        int, tuple[Glyph, approval.ApprovedVisibleBatch]
    ] = {}
    vertical: dict[
        int,
        tuple[
            Glyph,
            approval.ApprovedVisibleBatch,
            Mapping[str, Any],
        ],
    ] = {}
    for batch in admitted.visible_batches:
        with TTFont(
            batch.ttf_path,
            lazy=False,
            checkChecksums=2,
            recalcTimestamp=False,
        ) as font:
            cmap = font.getBestCmap()
            for entry in batch.entries:
                codepoint = _codepoint(str(entry["codepoint"]))
                source_name = engine._glyph_name(codepoint)
                if cmap.get(codepoint) != source_name:
                    raise MewNoteReleaseBuildError(
                        f"{batch.collection_id}/{batch.batch_id}: "
                        f"missing U+{codepoint:04X}"
                    )
                outline = font["glyf"][source_name]
                if outline.isComposite() or outline.numberOfContours <= 0:
                    raise MewNoteReleaseBuildError(
                        f"{batch.collection_id}/{batch.batch_id}: "
                        f"{source_name} is empty or composite"
                    )
                if batch.collection_id == "vertical-93":
                    if codepoint in vertical:
                        raise MewNoteReleaseBuildError(
                            f"duplicate vertical U+{codepoint:04X}"
                        )
                    vertical[codepoint] = (
                        deepcopy(outline),
                        batch,
                        entry,
                    )
                else:
                    if codepoint in encoded:
                        raise MewNoteReleaseBuildError(
                            f"duplicate encoded U+{codepoint:04X}"
                        )
                    encoded[codepoint] = (deepcopy(outline), batch)
    if len(encoded) != VISIBLE_COUNT or len(vertical) != VERTICAL_COUNT:
        raise MewNoteReleaseBuildError(
            f"source outline inventory is encoded={len(encoded)}, "
            f"vertical={len(vertical)}"
        )
    return encoded, vertical


def _empty_outline() -> Glyph:
    return TTGlyphPen(None).glyph()


def _build_encoded_glyphs(
    admitted: approval.ApprovedMewNoteRelease,
    outlines: Mapping[
        int, tuple[Glyph, approval.ApprovedVisibleBatch]
    ],
) -> tuple[engine.ReleaseGlyph, ...]:
    han = _read_object(HAN_REPERTOIRE, label="Mew Note Han repertoire")
    nonhan = _read_object(
        NONHAN_REPERTOIRE, label="Mew Note non-Han repertoire"
    )
    han_records = han.get("glyphs")
    nonhan_records = nonhan.get("glyphs")
    if (
        not isinstance(han_records, list)
        or len(han_records) != PLANNED_HAN_COUNT
        or not isinstance(nonhan_records, list)
        or len(nonhan_records) != NONHAN_COUNT
    ):
        raise MewNoteReleaseBuildError("family repertoire count drift")
    withheld_han = {
        _codepoint(str(entry["codepoint"]))
        for entry in admitted.withheld_entries
    }
    planned_han_codepoints = {
        int(record["codepoint"]) for record in han_records
    }
    if (
        len(withheld_han) != PLANNED_HAN_COUNT - HAN_COUNT
        or not withheld_han <= planned_han_codepoints
    ):
        raise MewNoteReleaseBuildError(
            "withheld Han repertoire count drift"
        )

    glyphs: list[engine.ReleaseGlyph] = []
    by_codepoint: dict[int, engine.ReleaseGlyph] = {}
    for record in han_records:
        codepoint = int(record["codepoint"])
        if record["character"] != chr(codepoint):
            raise MewNoteReleaseBuildError(
                f"Han identity drift at U+{codepoint:04X}"
            )
        if codepoint in withheld_han:
            continue
        source = outlines.get(codepoint)
        if source is None:
            raise MewNoteReleaseBuildError(
                f"missing reviewed Han U+{codepoint:04X}"
            )
        outline, batch = source
        bounds = _bounds(outline)
        glyph = engine.ReleaseGlyph(
            codepoint=codepoint,
            name=engine._glyph_name(codepoint),
            outline=outline,
            # Family-local Han evidence is compiled on the shared 1,024-unit
            # grid, so its TrueType left side bearing is exactly xMin.
            # Reopening every source font here would add 6,060 needless file
            # reads without providing independent information.
            horizontal_metric=(engine.UPM, bounds[0]),
            vertical_metric=(
                engine.UPM,
                engine.VERTICAL_ORIGIN_Y - bounds[3],
            ),
            source_collection="mew-note-han-6060",
            source_batch=batch.batch_id,
            source_font_sha256=batch.ttf_sha256,
            outline_required=True,
            profile_id="han-fullwidth",
            mark_placement=None,
        )
        glyphs.append(glyph)
        by_codepoint[codepoint] = glyph

    canonical_nonhan = sorted(
        nonhan_records, key=lambda record: int(record["canonical_rank"])
    )
    unresolved_empty: list[Mapping[str, Any]] = []
    for record in canonical_nonhan:
        codepoint = _codepoint(str(record["codepoint"]))
        if record["character"] != chr(codepoint):
            raise MewNoteReleaseBuildError(
                f"non-Han identity drift at U+{codepoint:04X}"
            )
        outline_required = bool(record["outline_required"])
        if not outline_required:
            unresolved_empty.append(record)
            continue
        source = outlines.get(codepoint)
        if source is None:
            raise MewNoteReleaseBuildError(
                f"missing reviewed non-Han U+{codepoint:04X}"
            )
        outline, batch = source
        (
            positioned,
            horizontal_metric,
            vertical_metric,
            mark_placement,
        ) = _position_visible_nonhan(outline, record)
        glyph = engine.ReleaseGlyph(
            codepoint=codepoint,
            name=engine._glyph_name(codepoint),
            outline=positioned,
            horizontal_metric=horizontal_metric,
            vertical_metric=vertical_metric,
            source_collection="mew-note-nonhan-3060-visible",
            source_batch=batch.batch_id,
            source_font_sha256=batch.ttf_sha256,
            outline_required=True,
            profile_id=str(record["profile_id"]),
            mark_placement=mark_placement,
        )
        by_codepoint[codepoint] = glyph

    for record in unresolved_empty:
        codepoint = _codepoint(str(record["codepoint"]))
        policy = record["metrics"]["horizontal_advance"]
        if policy["kind"] == "fixed":
            advance = int(policy["value"])
        elif policy["kind"] == "reference":
            reference = _codepoint(str(policy["codepoint"]))
            resolved = by_codepoint.get(reference)
            if resolved is None:
                raise MewNoteReleaseBuildError(
                    f"U+{codepoint:04X}: unresolved advance reference "
                    f"U+{reference:04X}"
                )
            advance = resolved.horizontal_metric[0]
        else:
            raise MewNoteReleaseBuildError(
                f"U+{codepoint:04X}: semantic glyph cannot be "
                "source-proportional"
            )
        glyph = engine.ReleaseGlyph(
            codepoint=codepoint,
            name=engine._glyph_name(codepoint),
            outline=_empty_outline(),
            horizontal_metric=(advance, 0),
            vertical_metric=(
                int(record["metrics"]["vertical_advance"]["value"]),
                0,
            ),
            source_collection="mew-note-nonhan-3060-semantic-empty",
            source_batch="nonhan-0206",
            source_font_sha256=admitted.plan_sha256,
            outline_required=False,
            profile_id=str(record["profile_id"]),
            mark_placement=(
                "overlay"
                if record["profile_id"] == "nonspacing-mark"
                else None
            ),
        )
        by_codepoint[codepoint] = glyph

    glyphs.extend(
        by_codepoint[_codepoint(str(record["codepoint"]))]
        for record in canonical_nonhan
    )
    if (
        len(glyphs) != CMAP_COUNT
        or len({glyph.codepoint for glyph in glyphs}) != CMAP_COUNT
        or sum(glyph.outline_required for glyph in glyphs) != VISIBLE_COUNT
    ):
        raise MewNoteReleaseBuildError(
            "compiled encoded repertoire partition drift"
        )
    return tuple(glyphs)


def _center_outline(
    outline: Glyph,
    *,
    advance: int,
) -> tuple[Glyph, int]:
    result = deepcopy(outline)
    x_min, _y_min, x_max, _y_max = _bounds(result)
    width = x_max - x_min
    if width > advance:
        raise MewNoteReleaseBuildError(
            f"vertical imagegen ink width {width} exceeds base advance "
            f"{advance}"
        )
    _shift(result, x=(advance - width) // 2 - x_min)
    return result, _bounds(result)[0]


def _build_vertical_alternates(
    glyphs: Sequence[engine.ReleaseGlyph],
    vertical_sources: Mapping[
        int,
        tuple[
            Glyph,
            approval.ApprovedVisibleBatch,
            Mapping[str, Any],
        ],
    ],
) -> tuple[engine.VerticalAlternate, ...]:
    repertoire = _read_object(
        VERTICAL_REPERTOIRE,
        label="Mew Note vertical repertoire",
    )
    records = repertoire.get("alternates")
    if not isinstance(records, list) or len(records) != VERTICAL_COUNT:
        raise MewNoteReleaseBuildError("vertical repertoire count drift")
    by_codepoint = {glyph.codepoint: glyph for glyph in glyphs}
    alternates: list[engine.VerticalAlternate] = []
    for record in records:
        codepoint = _codepoint(str(record["base_codepoint"]))
        source = vertical_sources.get(codepoint)
        base = by_codepoint.get(codepoint)
        if source is None or base is None:
            raise MewNoteReleaseBuildError(
                f"vertical base/source missing for U+{codepoint:04X}"
            )
        outline, batch, entry = source
        expected_name = f"{base.name}.vert"
        if (
            record["glyph_name"] != expected_name
            or entry.get("glyph_name") != expected_name
        ):
            raise MewNoteReleaseBuildError(
                f"vertical glyph identity drift for U+{codepoint:04X}"
            )
        positioned, lsb = _center_outline(
            outline,
            advance=base.horizontal_metric[0],
        )
        y_max = _bounds(positioned)[3]
        alternates.append(
            engine.VerticalAlternate(
                base_codepoint=codepoint,
                base_name=base.name,
                name=expected_name,
                outline=positioned,
                horizontal_metric=(
                    base.horizontal_metric[0],
                    lsb,
                ),
                vertical_metric=(
                    base.vertical_metric[0],
                    engine.VERTICAL_ORIGIN_Y - y_max,
                ),
                preview_horizontal_metric=(
                    engine.UPM,
                    _bounds(outline)[0],
                ),
                preview_vertical_metric=(
                    engine.UPM,
                    engine.VERTICAL_ORIGIN_Y - _bounds(outline)[3],
                ),
                source_batch=batch.batch_id,
                source_font_path=batch.ttf_path,
                source_font_sha256=batch.ttf_sha256,
                vertical_orientation=str(
                    record["vertical_orientation"]
                ),
                tailoring=record["tailoring"],
            )
        )
    return tuple(alternates)


def _notdef(
    admitted: approval.ApprovedMewNoteRelease,
) -> tuple[Glyph, approval.ApprovedVisibleBatch]:
    first = next(
        batch
        for batch in admitted.visible_batches
        if batch.collection_id == "han-6060"
    )
    with TTFont(
        first.ttf_path,
        lazy=False,
        checkChecksums=2,
    ) as font:
        outline = font["glyf"][".notdef"]
        if outline.isComposite() or outline.numberOfContours <= 0:
            raise MewNoteReleaseBuildError(
                "first reviewed Mew Note .notdef is empty or composite"
            )
        return deepcopy(outline), first


def _coverage_digest(
    glyphs: Sequence[engine.ReleaseGlyph],
    coverage: Mapping[str, Mapping[str, int]],
) -> str:
    expected_labels = {
        f"U+{glyph.codepoint:04X}"
        for glyph in glyphs
    }
    if set(coverage) != expected_labels:
        raise MewNoteReleaseBuildError(
            "final proof coverage inventory drift"
        )
    digest = hashlib.sha256()
    for glyph in glyphs:
        label = f"U+{glyph.codepoint:04X}"
        counts = coverage[label]
        if set(counts) != {str(size) for size in PROOF_SIZES}:
            raise MewNoteReleaseBuildError(
                f"{label}: final proof size inventory drift"
            )
        for size in PROOF_SIZES:
            count = int(counts[str(size)])
            if glyph.outline_required and count <= 0:
                raise MewNoteReleaseBuildError(
                    f"{label}: zero coverage at {size}px"
                )
            if not glyph.outline_required and count != 0:
                raise MewNoteReleaseBuildError(
                    f"{label}: semantic-empty glyph renders ink"
                )
            digest.update(
                f"{label}\t{size}\t{count}\n".encode("ascii")
            )
    return digest.hexdigest()


def _validate_vertical_shaping(
    ttf: Path,
    alternates: Sequence[engine.VerticalAlternate],
) -> str:
    data = ttf.read_bytes()
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    with TTFont(ttf, lazy=False, checkChecksums=2) as ttfont:
        order = ttfont.getGlyphOrder()
    digest = hashlib.sha256()
    for alternate in alternates:
        buffer = hb.Buffer()
        buffer.add_str(chr(alternate.base_codepoint))
        buffer.direction = "ttb"
        buffer.script = "hani"
        buffer.language = "zh-Hant"
        hb.shape(font, buffer, {"vert": True, "vrt2": True})
        if len(buffer.glyph_infos) != 1:
            raise MewNoteReleaseBuildError(
                f"{alternate.name}: vertical shaping cardinality drift"
            )
        glyph_id = int(buffer.glyph_infos[0].codepoint)
        if glyph_id >= len(order) or order[glyph_id] != alternate.name:
            raise MewNoteReleaseBuildError(
                f"{alternate.name}: vertical shaping substitution drift"
            )
        position = buffer.glyph_positions[0]
        if (
            int(position.x_advance) != 0
            or int(position.y_advance)
            != -alternate.vertical_metric[0]
        ):
            raise MewNoteReleaseBuildError(
                f"{alternate.name}: vertical shaping advance drift"
            )
        digest.update(
            (
                f"{alternate.base_codepoint:06X}\t{alternate.name}\t"
                f"{position.x_advance}\t{position.y_advance}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _allowed_destination(
    project_root: Path,
    output: Path,
) -> Path:
    project_root = project_root.resolve()
    if not output.is_absolute():
        output = project_root / output
    lexical = Path(os.path.abspath(os.fspath(output)))
    allowed = {
        project_root / "build/families/mew-note-tc/release-9088",
        project_root / "dist/mew-note-tc",
    }
    if lexical not in allowed:
        raise MewNoteReleaseBuildError(
            "Mew Note release output must be exactly build/families/"
            "mew-note-tc/release-9088 or dist/mew-note-tc"
        )
    cursor = project_root
    for part in lexical.relative_to(project_root).parts:
        cursor /= part
        if cursor.is_symlink():
            raise MewNoteReleaseBuildError(
                f"release output path contains symlink: {cursor}"
            )
    return lexical


def _artifact_hashes(stage: Path) -> dict[str, str]:
    return {
        path.relative_to(stage).as_posix(): _sha256(path)
        for path in sorted(stage.rglob("*"))
        if path.is_file() and path.name != "report.json"
    }


def build_release(
    *,
    project_root: Path = ROOT,
    output_directory: Path = OUTPUT_DIRECTORY,
) -> Path:
    """Validate all review evidence and atomically compile Mew Note TC."""

    project_root = project_root.resolve()
    output_directory = _allowed_destination(
        project_root, output_directory
    )
    try:
        admitted = approval.validate_approval(
            project_root=project_root
        )
    except approval.MewNoteReleaseApprovalError as exc:
        raise MewNoteReleaseBuildError(str(exc)) from exc
    outlines, vertical_sources = _load_source_outlines(admitted)
    glyphs = _build_encoded_glyphs(admitted, outlines)
    alternates = _build_vertical_alternates(
        glyphs, vertical_sources
    )
    notdef, notdef_source = _notdef(admitted)

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{output_directory.name}-",
            dir=output_directory.parent,
        )
    )
    try:
        ttf, otf, feature_summary = engine._write_sfnt_fonts(
            stage,
            glyphs=glyphs,
            alternates=alternates,
            notdef=notdef,
            identity=IDENTITY,
        )
        for path in (ttf, otf):
            engine._validate_font(
                path,
                glyphs,
                alternates,
                notdef=notdef,
                identity=IDENTITY,
                expected_total_glyph_count=TOTAL_GLYPH_COUNT,
            )
        woff, woff2, css = engine._write_web_fonts(
            ttf,
            glyphs=glyphs,
            alternates=alternates,
            notdef=notdef,
            identity=IDENTITY,
            expected_total_glyph_count=TOTAL_GLYPH_COUNT,
        )
        proof_records, coverage = engine._render_proofs(
            ttf,
            glyphs,
            stage / "proof",
        )
        for record in proof_records:
            record["sequence"] = "mew-note-release-glyph-order-row-major"
        vertical_proofs = engine._render_vertical_shaping_proofs(
            ttf,
            alternates,
            stage / "proof",
        )
        for record in vertical_proofs:
            record["placement_contract"] = (
                "base advances with centered family-local vertical outline"
            )
        proof_records.extend(vertical_proofs)
        coverage_sha256 = _coverage_digest(glyphs, coverage)
        vertical_sha256 = _validate_vertical_shaping(
            ttf, alternates
        )
        ofl = stage / "OFL.txt"
        shutil.copyfile(project_root / "OFL.txt", ofl)
        if _sha256(ofl) != engine.OFL_SHA256:
            raise MewNoteReleaseBuildError("OFL hash drift")
        glyph_records = [
            {
                "glyph_order_index": index,
                "character": glyph.character,
                "codepoint": f"U+{glyph.codepoint:04X}",
                "glyph_name": glyph.name,
                "outline_required": glyph.outline_required,
                "profile_id": glyph.profile_id,
                "mark_placement": glyph.mark_placement,
                "horizontal_advance": glyph.horizontal_metric[0],
                "left_side_bearing": glyph.horizontal_metric[1],
                "vertical_advance": glyph.vertical_metric[0],
                "top_side_bearing": glyph.vertical_metric[1],
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
                "base_character": chr(item.base_codepoint),
                "base_codepoint": f"U+{item.base_codepoint:04X}",
                "base_glyph_name": item.base_name,
                "glyph_name": item.name,
                "encoded": False,
                "horizontal_advance": item.horizontal_metric[0],
                "left_side_bearing": item.horizontal_metric[1],
                "vertical_advance": item.vertical_metric[0],
                "top_side_bearing": item.vertical_metric[1],
                "vertical_orientation": item.vertical_orientation,
                "tailoring": item.tailoring,
                "source_batch": item.source_batch,
                "source_font_sha256": item.source_font_sha256,
            }
            for index, item in enumerate(alternates, start=1)
        ]
        report: dict[str, Any] = {
            "schema_version": 1,
            "pipeline": PIPELINE_ID,
            "source_policy": SOURCE_POLICY,
            "approval_state": "approved-9088-plus-vertical93",
            "family": {
                "family": IDENTITY.family,
                "style": IDENTITY.style,
                "postscript_name": IDENTITY.postscript_name,
                "version": IDENTITY.version,
                "head_font_revision": IDENTITY.revision,
            },
            "coverage": {
                "requirements_denominator": 18_071,
                "cmap_count": CMAP_COUNT,
                "coverage_percent": round(
                    CMAP_COUNT / 18_071 * 100, 4
                ),
                "han": HAN_COUNT,
                "planned_han": PLANNED_HAN_COUNT,
                "nonhan": NONHAN_COUNT,
                "visible": VISIBLE_COUNT,
                "semantic_empty": SEMANTIC_EMPTY_COUNT,
                "hiragana": sum(
                    0x3041 <= glyph.codepoint <= 0x309F
                    for glyph in glyphs
                ),
                "katakana": sum(
                    0x30A0 <= glyph.codepoint <= 0x30FF
                    for glyph in glyphs
                ),
                "unencoded_vertical_alternates": VERTICAL_COUNT,
                "total_glyph_count_including_notdef": TOTAL_GLYPH_COUNT,
                "small_size_audit_sha256": coverage_sha256,
                "vertical_shaping_audit_sha256": vertical_sha256,
            },
            "repertoires": {
                "han": {
                    "path": HAN_REPERTOIRE.relative_to(
                        project_root
                    ).as_posix(),
                    "sha256": _sha256(HAN_REPERTOIRE),
                },
                "nonhan": {
                    "path": NONHAN_REPERTOIRE.relative_to(
                        project_root
                    ).as_posix(),
                    "sha256": _sha256(NONHAN_REPERTOIRE),
                },
                "vertical": {
                    "path": VERTICAL_REPERTOIRE.relative_to(
                        project_root
                    ).as_posix(),
                    "sha256": _sha256(VERTICAL_REPERTOIRE),
                },
            },
            "approval": {
                "path": admitted.approval_path.relative_to(
                    project_root
                ).as_posix(),
                "sha256": admitted.approval_sha256,
                "release_deviation": {
                    "path": admitted.release_deviation_path.relative_to(
                        project_root
                    ).as_posix(),
                    "sha256": admitted.release_deviation_sha256,
                },
                "approver": admitted.approver_name,
                "approved_at": admitted.approved_at,
                "reviewed_visible_batches": len(
                    admitted.visible_batches
                ),
                "withheld_batches": len(approval.WITHHELD_BATCHES),
                "withheld_codepoints": [
                    str(entry["codepoint"])
                    for entry in admitted.withheld_entries
                ],
            },
            "notdef": {
                "source_collection": notdef_source.collection_id,
                "source_batch": notdef_source.batch_id,
                "source_font_sha256": notdef_source.ttf_sha256,
            },
            "font": {
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
            "proofs": proof_records,
            "license": {
                "identifier": "OFL-1.1",
                "path": ofl.name,
                "sha256": _sha256(ofl),
            },
            "qa": {
                "proof_sizes_px": list(PROOF_SIZES),
                "proof_polarities": [
                    "black-on-white",
                    "white-on-black",
                ],
                "vertical_shaping_proof_size_px": 56,
                "all_visible_glyphs_nonempty_at_all_sizes": True,
                "all_semantic_empty_glyphs_zero_ink": True,
                "all_outlines_simple": True,
                "all_technical_reviews_validated": True,
                "cmap_unique": True,
                "vert_substitutions_exact": True,
                "vrt2_substitutions_exact": True,
                "woff_validated": True,
                "woff2_validated": True,
                "clear_hand_outlines_read": False,
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
                allow_nan=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if report["artifact_sha256"] != _artifact_hashes(stage):
            raise MewNoteReleaseBuildError(
                "release artifact inventory changed after report creation"
            )
        engine._install_release_directory(stage, output_directory)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return output_directory


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    output = args.output or (
        project_root / "build/families/mew-note-tc/release-9088"
    )
    result = build_release(
        project_root=project_root,
        output_directory=output,
    )
    print(result)
    print(result / "report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
