from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tomllib

import freetype
from fontTools.ttLib import TTFont
import pytest
import uharfbuzz as hb

from scripts import build_imagegen_release_font as release


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist/clear-hand-tc"
REPORT = DIST / "report.json"
HAN_REPERTOIRE = ROOT / "sources/imagegen/repertoires/common-3000.json"
MOE_EXTENSION_REPERTOIRE = (
    ROOT / "sources/imagegen/repertoires/moe-common-extension-1844.json"
)
DICTIONARY_EXTENSION_REPERTOIRE = (
    ROOT
    / "sources/imagegen/repertoires/dictionary-salience-extension-1216.json"
)
NONHAN_REPERTOIRE = (
    ROOT / "sources/imagegen/repertoires/nonhan-3060.json"
)
VERTICAL_REPERTOIRE = (
    ROOT / "sources/imagegen/repertoires/vertical-93.json"
)
ARTIFACTS = {
    "ttf": DIST / "font/ClearHandTC-Regular.ttf",
    "otf": DIST / "font/ClearHandTC-Regular.otf",
    "woff": DIST / "font/ClearHandTC-Regular.woff",
    "woff2": DIST / "font/ClearHandTC-Regular.woff2",
}


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _glyph_name(character: str) -> str:
    codepoint = ord(character)
    return (
        f"uni{codepoint:04X}"
        if codepoint <= 0xFFFF
        else f"u{codepoint:05X}"
    )


def _expected_release() -> tuple[
    dict[int, str],
    list[str],
    dict[str, bool],
    list[dict[str, object]],
]:
    han = _load(HAN_REPERTOIRE)["characters"]
    extension = _load(MOE_EXTENSION_REPERTOIRE)["characters"]
    dictionary_extension = _load(
        DICTIONARY_EXTENSION_REPERTOIRE
    )["characters"]
    nonhan = _load(NONHAN_REPERTOIRE)["glyphs"]
    vertical = _load(VERTICAL_REPERTOIRE)["alternates"]
    assert isinstance(han, list)
    assert isinstance(extension, list)
    assert isinstance(dictionary_extension, list)
    assert isinstance(nonhan, list)
    assert isinstance(vertical, list)

    encoded = [row["character"] for row in han]
    encoded.extend(row["character"] for row in extension)
    encoded.extend(row["character"] for row in dictionary_extension)
    encoded.extend(row["character"] for row in nonhan)
    cmap = {ord(character): _glyph_name(character) for character in encoded}
    outline_required = {
        _glyph_name(row["character"]): True for row in han
    }
    outline_required.update(
        {
            _glyph_name(row["character"]): True
            for row in extension
        }
    )
    outline_required.update(
        {
            _glyph_name(row["character"]): True
            for row in dictionary_extension
        }
    )
    outline_required.update(
        {
            _glyph_name(row["character"]): row["outline_required"]
            for row in nonhan
        }
    )
    order = [
        ".notdef",
        *cmap.values(),
        *[row["glyph_name"] for row in vertical],
    ]
    return cmap, order, outline_required, vertical


def _outline_digest(font: TTFont) -> str:
    digest = hashlib.sha256()
    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(glyf[name].compile(glyf))
        digest.update(b"\0")
    return digest.hexdigest()


def _shape(
    path: Path,
    text: str,
    *,
    direction: str = "ltr",
    features: dict[str, bool] | None = None,
) -> tuple[list[str], list[object]]:
    data = path.read_bytes()
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.direction = direction
    buffer.guess_segment_properties()
    hb.shape(font, buffer, features or {})
    with TTFont(path, recalcTimestamp=False) as ttfont:
        order = ttfont.getGlyphOrder()
    return [order[info.codepoint] for info in buffer.glyph_infos], list(
        buffer.glyph_positions
    )


def _vertical_placed_bounds(
    path: Path,
    character: str,
    expected_name: str,
) -> tuple[tuple[int, int, int, int], tuple[int, int]]:
    names, positions = _shape(
        path,
        character,
        direction="ttb",
        features={"vert": True, "vrt2": True},
    )
    assert names == [expected_name]
    position = positions[0]
    face = freetype.Face(str(path))
    glyph_id = face.get_name_index(expected_name.encode("ascii"))
    assert glyph_id > 0
    face.load_glyph(
        glyph_id,
        freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING,
    )
    box = face.glyph.outline.get_bbox()
    return (
        (
            int(box.xMin) + int(position.x_offset),
            int(box.yMin) + int(position.y_offset),
            int(box.xMax) + int(position.x_offset),
            int(box.yMax) + int(position.y_offset),
        ),
        (int(position.x_advance), int(position.y_advance)),
    )


def test_all_release_artifacts_cover_exact_9120_plus_vertical_93() -> None:
    expected_cmap, expected_order, required, vertical = _expected_release()
    assert len(expected_cmap) == 9120
    assert len(expected_order) == 9214
    assert len(vertical) == 93
    assert sum(0x3041 <= value <= 0x309F for value in expected_cmap) == 93
    assert sum(0x30A0 <= value <= 0x30FF for value in expected_cmap) == 96

    for path in ARTIFACTS.values():
        with TTFont(
            path,
            lazy=False,
            checkChecksums=2,
            recalcTimestamp=False,
        ) as font:
            assert font.getBestCmap() == expected_cmap
            assert font.getGlyphOrder() == expected_order
            assert "glyf" in font and "CFF " not in font and "CFF2" not in font
            assert font["glyf"][".notdef"].numberOfContours > 0

            for name, must_have_outline in required.items():
                glyph = font["glyf"][name]
                assert not glyph.isComposite()
                assert (glyph.numberOfContours > 0) is must_have_outline

            cmap_names = set(expected_cmap.values())
            for row in vertical:
                alternate = row["glyph_name"]
                base = _glyph_name(row["base_character"])
                glyph = font["glyf"][alternate]
                assert alternate not in cmap_names
                assert not glyph.isComposite()
                assert glyph.numberOfContours > 0
                assert font["hmtx"].metrics[alternate][0] == (
                    font["hmtx"].metrics[base][0]
                )
                assert font["vmtx"].metrics[alternate][0] == (
                    font["vmtx"].metrics[base][0]
                )

            expected_substitutions = {
                _glyph_name(row["base_character"]): row["glyph_name"]
                for row in vertical
            }
            assert release._gsub_feature_mapping(
                font, "vert"
            ) == expected_substitutions
            assert release._gsub_feature_mapping(
                font, "vrt2"
            ) == expected_substitutions


def test_release_vertical_placement_matches_every_approved_preview() -> None:
    report = _load(REPORT)
    records = report["vertical_alternates"]
    assert isinstance(records, list) and len(records) == 93
    for index, record in enumerate(records):
        assert isinstance(record, dict)
        batch_number = index // 16 + 1
        preview = (
            ROOT
            / f"build/imagegen/imagegen-vertical-{batch_number:04d}/font/"
            f"ClearHandTC-Vertical{batch_number:04d}-Unreviewed.ttf"
        )
        character = record["base_character"]
        name = record["glyph_name"]
        preview_bounds, preview_advance = _vertical_placed_bounds(
            preview,
            character,
            name,
        )
        release_bounds, release_advance = _vertical_placed_bounds(
            ARTIFACTS["ttf"],
            character,
            name,
        )
        assert release_bounds == preview_bounds
        assert release_advance == preview_advance
        assert record["metric_policy"] == (
            "base-advances-with-approved-preview-placement"
        )
        assert record["approved_preview_placed_bounds"] == list(
            preview_bounds
        )
        assert record["release_placed_bounds"] == list(release_bounds)
        assert record["release_advance"] == list(release_advance)
    vertical_proofs = [
        proof
        for proof in report["proofs"]
        if proof.get("kind") == "vertical-shaping"
    ]
    assert {
        (proof["polarity"], proof["size_px"], proof["glyph_count"])
        for proof in vertical_proofs
    } == {
        ("black-on-white", 56, 93),
        ("white-on-black", 56, 93),
    }


def test_release_formats_have_identical_canonical_font_tables() -> None:
    signatures = []
    for path in ARTIFACTS.values():
        with TTFont(path, recalcTimestamp=False) as font:
            signatures.append(
                (
                    tuple(font.getBestCmap().items()),
                    tuple(font.getGlyphOrder()),
                    tuple(font["hmtx"].metrics.items()),
                    tuple(font["vmtx"].metrics.items()),
                    _outline_digest(font),
                    font.getTableData("GSUB"),
                    font.getTableData("GPOS"),
                    font.getTableData("GDEF"),
                )
            )
    assert signatures[0] == signatures[1] == signatures[2] == signatures[3]


def test_horizontal_em_dash_and_corner_quotes_keep_horizontal_forms() -> None:
    with TTFont(ARTIFACTS["ttf"], recalcTimestamp=False) as font:
        cmap = font.getBestCmap()
        vertical = release._gsub_feature_mapping(font, "vert")

        em_dash = font["glyf"][cmap[0x2014]]
        vertical_em_dash = font["glyf"][vertical[cmap[0x2014]]]
        assert em_dash.xMax - em_dash.xMin > em_dash.yMax - em_dash.yMin
        assert (
            vertical_em_dash.yMax - vertical_em_dash.yMin
            > vertical_em_dash.xMax - vertical_em_dash.xMin
        )

        for codepoint in (0x300C, 0x300D):
            horizontal_quote = font["glyf"][cmap[codepoint]]
            vertical_quote = font["glyf"][vertical[cmap[codepoint]]]
            assert (
                horizontal_quote.yMax - horizontal_quote.yMin
                > horizontal_quote.xMax - horizontal_quote.xMin
            )
            assert (
                vertical_quote.xMax - vertical_quote.xMin
                > vertical_quote.yMax - vertical_quote.yMin
            )


def test_release_names_metrics_license_and_report() -> None:
    report = _load(REPORT)
    coverage = report["coverage"]
    font_record = report["font"]
    assert isinstance(coverage, dict) and isinstance(font_record, dict)
    assert coverage["cmap_count"] == 9120
    assert coverage["total_glyph_count_including_notdef"] == 9214
    assert coverage["unencoded_vertical_alternates"] == 93
    assert report["source_policy"] == release.SOURCE_POLICY
    assert font_record["version"] == "Version 0.100"
    assert font_record["head_font_revision"] == 0.1
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert project["project"]["version"] == "0.1.0"

    for path in ARTIFACTS.values():
        with TTFont(path, recalcTimestamp=False) as font:
            assert font["name"].getDebugName(1) == "Clear Hand TC"
            assert font["name"].getDebugName(6) == "ClearHandTC-Regular"
            assert font["name"].getDebugName(5) == "Version 0.100"
            assert font["head"].fontRevision == pytest.approx(0.1, abs=1e-5)
            assert font["head"].unitsPerEm == 1024
            assert font["OS/2"].fsType == 0
            assert font["OS/2"].fsSelection & 0x0040
            assert not font["OS/2"].fsSelection & 0x0021
            assert font["OS/2"].sxHeight == font_record["x_height"]
            assert font["OS/2"].sCapHeight == font_record["cap_height"]
            assert font["OS/2"].yStrikeoutPosition == (
                font_record["strikeout_position"]
            )
            assert font["OS/2"].yStrikeoutSize == (
                font_record["strikeout_size"]
            )
            assert font["post"].underlinePosition == (
                font_record["underline_position"]
            )
            assert font["post"].underlineThickness == (
                font_record["underline_thickness"]
            )
            assert (
                font["vhea"].caretSlopeRise,
                font["vhea"].caretSlopeRun,
                font["vhea"].caretOffset,
            ) == (
                font_record["vertical_caret_slope_rise"],
                font_record["vertical_caret_slope_run"],
                font_record["vertical_caret_offset"],
            ) == (0, 1, 0)
            assert (
                font["hhea"].ascent,
                font["hhea"].descent,
                font["hhea"].lineGap,
            ) == (
                font["OS/2"].sTypoAscender,
                font["OS/2"].sTypoDescender,
                font["OS/2"].sTypoLineGap,
            )
            assert "SIL Open Font License" in (
                font["name"].getDebugName(13) or ""
            )

    css = (DIST / str(font_record["css"])).read_text(encoding="utf-8")
    assert "ClearHandTC-Regular.woff2" in css
    assert "ClearHandTC-Regular.woff" in css
    assert "font-family: 'Clear Hand TC'" in css


def test_true_harfbuzz_shapes_vertical_marks_and_kerning() -> None:
    path = ARTIFACTS["ttf"]
    vertical = _load(VERTICAL_REPERTOIRE)["alternates"]
    assert isinstance(vertical, list)
    bases = "".join(row["base_character"] for row in vertical)
    expected_alternates = [row["glyph_name"] for row in vertical]
    names, positions = _shape(
        path,
        bases,
        direction="ttb",
        features={"vert": True, "vrt2": True},
    )
    assert names == expected_alternates
    assert all(position.y_advance < 0 for position in positions)

    mark_names, mark_positions = _shape(
        path,
        # U+0078 has no precomposed acute form, so HarfBuzz keeps all three
        # glyphs visible and this exercises both mark and mkmk positioning.
        "x\u0301\u0304",
        features={"ccmp": False, "mark": True, "mkmk": True},
    )
    assert mark_names == ["uni0078", "uni0301", "uni0304"]
    assert mark_positions[0].x_advance > 0
    assert mark_positions[1].x_advance == mark_positions[2].x_advance == 0
    assert (
        mark_positions[1].x_offset,
        mark_positions[1].y_offset,
    ) != (0, 0)
    assert (
        mark_positions[2].x_offset,
        mark_positions[2].y_offset,
    ) != (
        mark_positions[1].x_offset,
        mark_positions[1].y_offset,
    )

    _, kern_off = _shape(path, "AV", features={"kern": False})
    _, kern_on = _shape(path, "AV", features={"kern": True})
    assert sum(item.x_advance for item in kern_on) < sum(
        item.x_advance for item in kern_off
    )


def test_release_cmap_is_unique_and_semantic_empty_is_intentional() -> None:
    expected_cmap, _, required, _ = _expected_release()
    with TTFont(ARTIFACTS["ttf"], recalcTimestamp=False) as font:
        cmap = font.getBestCmap()
        names = list(cmap.values())
        assert len(cmap) == len(names) == len(set(names)) == 9120
        assert cmap == expected_cmap
        assert ".notdef" not in names
        empty_names = {
            name for name, must_have_outline in required.items()
            if not must_have_outline
        }
        assert len(empty_names) == 17
        assert all(
            font["glyf"][name].numberOfContours == 0
            for name in empty_names
        )
