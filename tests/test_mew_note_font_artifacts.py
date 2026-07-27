from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image
import pytest

from scripts import build_imagegen_release_font as shared
from scripts import build_mew_note_release_font as mew


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist/mew-note-tc"
ARTIFACTS = {
    "ttf": DIST / "font/MewNoteTC-Regular.ttf",
    "otf": DIST / "font/MewNoteTC-Regular.otf",
    "woff": DIST / "font/MewNoteTC-Regular.woff",
    "woff2": DIST / "font/MewNoteTC-Regular.woff2",
}


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _glyph_name(codepoint: int) -> str:
    return (
        f"uni{codepoint:04X}"
        if codepoint <= 0xFFFF
        else f"u{codepoint:05X}"
    )


def _expected() -> tuple[dict[int, str], list[str], set[int]]:
    han = _load(mew.HAN_REPERTOIRE)
    nonhan = _load(mew.NONHAN_REPERTOIRE)
    vertical = _load(mew.VERTICAL_REPERTOIRE)
    withheld = {
        int(codepoint[2:], 16)
        for batch in han["batches"]
        if ("han-6060", batch["batch_id"])
        in mew.approval.WITHHELD_BATCHES
        for codepoint in batch["codepoints"]
    }
    codepoints = [
        int(record["codepoint"])
        for record in han["glyphs"]
        if int(record["codepoint"]) not in withheld
    ]
    codepoints.extend(
        int(record["codepoint"][2:], 16)
        for record in sorted(
            nonhan["glyphs"],
            key=lambda record: int(record["canonical_rank"]),
        )
    )
    cmap = {codepoint: _glyph_name(codepoint) for codepoint in codepoints}
    order = [
        ".notdef",
        *cmap.values(),
        *[
            record["glyph_name"]
            for record in vertical["alternates"]
        ],
    ]
    return cmap, order, withheld


def _outline_digest(font: TTFont) -> str:
    glyf = font["glyf"]
    digest = hashlib.sha256()
    for name in font.getGlyphOrder():
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(glyf[name].compile(glyf))
        digest.update(b"\0")
    return digest.hexdigest()


def _dist_inventory(directory: Path) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        assert not path.is_symlink()
        if not path.is_file() or path == directory / "report.json":
            continue
        inventory[path.relative_to(directory).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return inventory


def _quadrant_outline_occupancy(
    font: TTFont,
    glyph_name: str,
) -> dict[str, int]:
    coordinates, _end_points, _flags = font["glyf"][
        glyph_name
    ].getCoordinates(font["glyf"])
    xs = [x for x, _y in coordinates]
    ys = [y for _x, y in coordinates]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    width = x_max - x_min
    height = y_max - y_min
    assert width > 0 and height > 0
    return {
        "upper_left": sum(
            x <= x_min + 0.3 * width
            and y >= y_min + 0.55 * height
            for x, y in coordinates
        ),
        "upper_right": sum(
            x >= x_min + 0.7 * width
            and y >= y_min + 0.55 * height
            for x, y in coordinates
        ),
        "lower_left": sum(
            x <= x_min + 0.3 * width
            and y <= y_min + 0.45 * height
            for x, y in coordinates
        ),
        "lower_right": sum(
            x >= x_min + 0.7 * width
            and y <= y_min + 0.45 * height
            for x, y in coordinates
        ),
    }


def test_mew_note_report_pins_complete_dist_artifact_inventory() -> None:
    report = _load(DIST / "report.json")
    declared = report["artifact_sha256"]
    assert isinstance(declared, dict)
    assert "report.json" not in declared
    assert declared == _dist_inventory(DIST)


def test_mew_note_formats_have_exact_preview_repertoire() -> None:
    expected_cmap, expected_order, withheld = _expected()
    assert len(expected_cmap) == mew.CMAP_COUNT == 9_088
    assert len(expected_order) == mew.TOTAL_GLYPH_COUNT == 9_182
    assert len(withheld) == 32

    signatures = []
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
            assert font["name"].getDebugName(1) == "Mew Note TC"
            assert font["name"].getDebugName(6) == "MewNoteTC-Regular"
            assert font["name"].getDebugName(5) == "Version 1.000"
            assert font["head"].fontRevision == pytest.approx(1.0)
            assert font["head"].unitsPerEm == 1024
            assert font["OS/2"].fsType == 0
            assert "SIL Open Font License" in (
                font["name"].getDebugName(13) or ""
            )
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


def test_mew_note_horizontal_em_dash_and_quotes_keep_horizontal_forms() -> None:
    with TTFont(ARTIFACTS["ttf"], recalcTimestamp=False) as font:
        cmap = font.getBestCmap()
        vertical = shared._gsub_feature_mapping(font, "vert")

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


def test_mew_note_compiled_vertical_quotes_keep_correct_handedness() -> None:
    with TTFont(ARTIFACTS["ttf"], recalcTimestamp=False) as font:
        cmap = font.getBestCmap()
        vertical = shared._gsub_feature_mapping(font, "vert")
        occupancy = {
            codepoint: _quadrant_outline_occupancy(
                font,
                vertical[cmap[codepoint]],
            )
            for codepoint in (0x300C, 0x300D, 0x300E, 0x300F)
        }

    # Opening quotes are top-right corners: ink spans the top and descends
    # only on the right. Closing quotes are bottom-left corners: the short
    # vertical arm rises on the left and the bottom arm extends right.
    for codepoint in (0x300C, 0x300E):
        assert occupancy[codepoint]["upper_left"] > 0
        assert occupancy[codepoint]["upper_right"] > 0
        assert occupancy[codepoint]["lower_left"] == 0
        assert occupancy[codepoint]["lower_right"] > 0
    for codepoint in (0x300D, 0x300F):
        assert occupancy[codepoint]["upper_left"] > 0
        assert occupancy[codepoint]["upper_right"] == 0
        assert occupancy[codepoint]["lower_left"] > 0
        assert occupancy[codepoint]["lower_right"] > 0


def test_mew_note_common_han_kana_vertical_and_report_are_complete() -> None:
    expected_cmap, _expected_order, withheld = _expected()
    with (ROOT / "inventories/moe-common-4808.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        common_han = {
            int(row["Unicode"], 16)
            for row in csv.DictReader(stream)
        }
    assert len(common_han) == 4_808
    assert common_han <= expected_cmap.keys()
    assert withheld.isdisjoint(common_han)
    assert sum(0x3041 <= value <= 0x309F for value in expected_cmap) == 93
    assert sum(0x30A0 <= value <= 0x30FF for value in expected_cmap) == 96

    report = _load(DIST / "report.json")
    coverage = report["coverage"]
    assert coverage == {
        **coverage,
        "requirements_denominator": 18_071,
        "cmap_count": 9_088,
        "han": 6_028,
        "planned_han": 6_060,
        "nonhan": 3_060,
        "visible": 9_071,
        "semantic_empty": 17,
        "hiragana": 93,
        "katakana": 96,
        "unencoded_vertical_alternates": 93,
        "total_glyph_count_including_notdef": 9_182,
    }
    assert report["approval"]["withheld_batches"] == 2
    deviation_path = (
        ROOT
        / "families/mew-note-tc/release-deviations/"
        "0.1-preview-9088.release-deviation.json"
    )
    assert report["approval"]["release_deviation"] == {
        "path": deviation_path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(
            deviation_path.read_bytes()
        ).hexdigest(),
    }
    assert {
        int(value[2:], 16)
        for value in report["approval"]["withheld_codepoints"]
    } == withheld
    assert report["qa"] == {
        **report["qa"],
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
    }

    with TTFont(ARTIFACTS["ttf"], recalcTimestamp=False) as font:
        expected_vertical = {
            record["base_glyph_name"]: record["glyph_name"]
            for record in report["vertical_alternates"]
        }
        assert len(expected_vertical) == 93
        assert shared._gsub_feature_mapping(
            font, "vert"
        ) == expected_vertical
        assert shared._gsub_feature_mapping(
            font, "vrt2"
        ) == expected_vertical


def test_mew_note_release_keeps_only_complete_final_proofs() -> None:
    report = _load(DIST / "report.json")
    proofs = report["proofs"]
    regular = [
        record for record in proofs
        if record.get("kind") is None
    ]
    vertical = [
        record for record in proofs
        if record.get("kind") == "vertical-shaping"
    ]
    polarities = {"black-on-white", "white-on-black"}
    expected_regular = {
        (polarity, size)
        for polarity in polarities
        for size in shared.PROOF_SIZES
    }

    assert {
        (record["polarity"], record["size_px"])
        for record in regular
    } == expected_regular
    assert {
        (record["polarity"], record["size_px"])
        for record in vertical
    } == {
        (polarity, 56)
        for polarity in polarities
    }
    assert len(proofs) == len(expected_regular) + 2
    assert report["qa"]["proof_sizes_px"] == list(shared.PROOF_SIZES)
    assert report["qa"]["proof_polarities"] == sorted(polarities)
    assert report["qa"]["vertical_shaping_proof_size_px"] == 56

    for record in proofs:
        path = DIST / record["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        with Image.open(path) as image:
            assert image.mode == "L"
            assert image.size == (
                record["width_px"],
                record["height_px"],
            )

    expected_sizes = {str(size) for size in shared.PROOF_SIZES}
    assert all(
        set(record["coverage_pixels"]) == expected_sizes
        for record in report["glyphs"]
    )
