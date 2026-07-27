from __future__ import annotations

from array import array
import copy
import hashlib
import json
from pathlib import Path

import freetype
import numpy as np
from PIL import Image, ImageDraw
import pytest
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates

from scripts import imagegen_font_pipeline as pipeline


PILOT_CHARACTERS = tuple("的一是不了人我在有他這為之大來以")
EXPECTED_X_RULES = (28, 327, 626, 925, 1224)
EXPECTED_Y_RULES = (28, 327, 628, 926, 1225)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _signed_area(points: list[tuple[int, int]]) -> float:
    return 0.5 * sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])
    )


@pytest.fixture(scope="module")
def pilot_build(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    output_root = tmp_path_factory.mktemp("imagegen-pilot")
    output = pipeline.build_batch(
        pipeline.DEFAULT_DESCRIPTOR, output_root=output_root
    )
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    return output, report


def test_pilot_descriptor_is_unreviewed_and_hash_pinned() -> None:
    descriptor = pipeline.load_source_descriptor()
    assert descriptor.characters == PILOT_CHARACTERS
    assert descriptor.state == "generated-unreviewed"
    assert descriptor.review == {
        "topology": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }
    assert pipeline._sha256(descriptor.raster_path) == descriptor.raster_sha256


def test_formal_descriptor_uses_the_same_data_driven_contract() -> None:
    descriptor = pipeline.load_source_descriptor(
        pipeline.IMAGEGEN_ROOT / "batches/common-0001.source.json"
    )
    assert descriptor.batch_id == "imagegen-common-0001"
    assert descriptor.characters == tuple("的一人不為第回之子有也三名作以二")
    assert len(descriptor.characters) == 16


def test_descriptor_rejects_hash_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual_sha256 = pipeline._sha256

    def wrong_raster_hash(path: Path) -> str:
        if path.suffix.lower() == ".png":
            return "0" * 64
        return actual_sha256(path)

    monkeypatch.setattr(pipeline, "_sha256", wrong_raster_hash)
    with pytest.raises(pipeline.ImagegenPipelineError, match="hash mismatch"):
        pipeline.load_source_descriptor()


def test_descriptor_rejects_duplicate_character(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.loads(
        pipeline.DEFAULT_DESCRIPTOR.read_text(encoding="utf-8")
    )
    payload = copy.deepcopy(payload)
    payload["grid"]["characters"][1] = payload["grid"]["characters"][0]
    monkeypatch.setattr(pipeline, "_read_json_object", lambda _: payload)
    with pytest.raises(pipeline.ImagegenPipelineError, match="duplicates"):
        pipeline.load_source_descriptor()


def test_han_pipeline_accepts_ideographic_number_zero() -> None:
    assert pipeline._one_unicode_scalar(
        "\u3007",
        where="test",
    ) == "\u3007"


@pytest.mark.parametrize("character", ["A", "\u0301", "7", "。", "★", "あ", "ア"])
def test_pipeline_accepts_visible_unicode_glyph_scalars(character: str) -> None:
    assert pipeline._one_unicode_scalar(character, where="test") == character


@pytest.mark.parametrize("character", [" ", "\n", "\u200b"])
def test_pipeline_rejects_separators_and_controls(character: str) -> None:
    with pytest.raises(
        pipeline.ImagegenPipelineError,
        match="not a visible Unicode glyph scalar",
    ):
        pipeline._one_unicode_scalar(character, where="test")


def test_grid_detection_uses_pixel_evidence_at_exact_rule_centres() -> None:
    image = Image.open(
        pipeline.IMAGEGEN_ROOT / "raster/pilot-common-0001.png"
    )
    grid = pipeline.detect_grid(image)
    assert grid.x.centers == EXPECTED_X_RULES
    assert grid.y.centers == EXPECTED_Y_RULES
    assert all(value >= pipeline.GRID_MIN_COVERAGE for value in grid.x.center_coverages)
    assert all(value >= pipeline.GRID_MIN_COVERAGE for value in grid.y.center_coverages)


def test_grid_detection_has_no_equal_spacing_fallback() -> None:
    source = Image.open(
        pipeline.IMAGEGEN_ROOT / "raster/pilot-common-0001.png"
    ).convert("RGB")
    damaged = source.copy()
    draw = ImageDraw.Draw(damaged)
    # Remove one full evidence-bearing rule while leaving the other four and
    # every glyph untouched.  A coordinate-guessing implementation would
    # still return a grid; the production detector must refuse.
    draw.rectangle((620, 0, 632, damaged.height - 1), fill=(255, 255, 255))
    with pytest.raises(
        pipeline.ImagegenPipelineError, match="expected exactly 5 vertical"
    ):
        pipeline.detect_grid(damaged)


def test_grid_detection_bridges_only_one_missing_scanline_inside_a_rule() -> None:
    image = Image.new("RGB", (1254, 1254), "white")
    draw = ImageDraw.Draw(image)
    rules = (20, 323, 626, 929, 1232)
    for coordinate in rules:
        draw.rectangle(
            (coordinate - 1, 0, coordinate + 1, 1253),
            fill=(220, 220, 220),
        )
        draw.rectangle(
            (0, coordinate - 1, 1253, coordinate + 1),
            fill=(220, 220, 220),
        )
    draw.rectangle(
        (0, rules[-1] - 2, 1253, rules[-1] + 2),
        fill=(220, 220, 220),
    )
    # Split the final horizontal rule into two independently evidenced spans
    # separated by exactly one missing scanline.  They remain one rule because
    # the combined span is narrower than GRID_MAX_RULE_WIDTH.
    draw.line((0, rules[-1], 1253, rules[-1]), fill="white", width=1)
    grid = pipeline.detect_grid(image)
    # Uniform three-pixel rules have equal darkness, so the documented
    # lower-coordinate tie-break selects the first row/column.
    assert grid.x.centers == tuple(value - 1 for value in rules)
    assert grid.y.centers[:4] == tuple(value - 1 for value in rules[:4])
    assert grid.y.groups[-1] == (rules[-1] - 2, rules[-1] + 2)

    # Two missing scanlines are outside the audited tolerance and must not be
    # interpreted as a single grid rule.
    damaged = image.copy()
    damaged_draw = ImageDraw.Draw(damaged)
    damaged_draw.line(
        (0, rules[-1] - 1, 1253, rules[-1] - 1),
        fill="white",
        width=1,
    )
    with pytest.raises(
        pipeline.ImagegenPipelineError,
        match="expected exactly 5 horizontal",
    ):
        pipeline.detect_grid(damaged)


def test_trailing_empty_cells_are_explicit_and_fail_closed() -> None:
    source = Image.open(
        pipeline.IMAGEGEN_ROOT / "raster/pilot-common-0001.png"
    ).convert("RGB")
    grid = pipeline.detect_grid(source)
    slots: tuple[str | None, ...] = (*PILOT_CHARACTERS[:-1], None)
    with pytest.raises(
        pipeline.ImagegenPipelineError, match="declared empty cell"
    ):
        pipeline.segment_cells(source, grid, slots)

    blanked = source.copy()
    draw = ImageDraw.Draw(blanked)
    draw.rectangle(
        (
            grid.x.centers[3] + 5,
            grid.y.centers[3] + 5,
            grid.x.centers[4] - 5,
            grid.y.centers[4] - 5,
        ),
        fill=(255, 255, 255),
    )
    cells = pipeline.segment_cells(blanked, pipeline.detect_grid(blanked), slots)
    assert len(cells) == 15
    assert tuple(cell.character for cell in cells) == PILOT_CHARACTERS[:-1]


def test_segmentation_removes_rules_but_keeps_antialias(
    pilot_build: tuple[Path, dict],
) -> None:
    output, _ = pilot_build
    source_pngs = sorted((output / "png").glob("*-source.png"))
    assert len(source_pngs) == 16
    for path in source_pngs:
        pixels = np.asarray(Image.open(path).convert("L"), dtype=np.uint8)
        assert pixels.shape == (
            pipeline.CELL_RASTER_SIZE,
            pipeline.CELL_RASTER_SIZE,
        )
        assert np.all(pixels[:5, :] == 255)
        assert np.all(pixels[-5:, :] == 255)
        assert np.all(pixels[:, :5] == 255)
        assert np.all(pixels[:, -5:] == 255)
        assert np.any(pixels <= pipeline.INK_CORE_CEILING)
        assert np.count_nonzero((pixels > 0) & (pixels < 255)) > 100


def test_outputs_are_complete_and_explicitly_unreviewed(
    pilot_build: tuple[Path, dict],
) -> None:
    output, report = pilot_build
    assert report["approval_state"] == "unreviewed"
    assert report["source_review"] == {
        "topology": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }
    assert report["grid"]["synthesized_coordinates"] is False
    assert report["grid"]["x_rule_centers"] == list(EXPECTED_X_RULES)
    assert report["grid"]["y_rule_centers"] == list(EXPECTED_Y_RULES)
    assert report["characters"] == list(PILOT_CHARACTERS)
    assert len(list((output / "svg").glob("*.svg"))) == 16
    assert len(list((output / "glyph-report").glob("*.json"))) == 16
    assert len(list((output / "png").glob("*-proof.png"))) == 16
    for name in (
        "small-sizes-black-on-white.png",
        "small-sizes-white-on-black.png",
        "segmented-source-contact.png",
    ):
        proof = output / "proof" / name
        assert proof.is_file()
        assert proof.stat().st_size > 1_000


def test_cmap_metrics_and_quadratic_outline_flavour(
    pilot_build: tuple[Path, dict],
) -> None:
    output, report = pilot_build
    expected_cmap = {
        ord(character): f"uni{ord(character):04X}"
        for character in PILOT_CHARACTERS
    }
    for key in ("ttf", "otf"):
        path = output / report["font"][key]
        font = TTFont(path, recalcTimestamp=False)
        assert font.getBestCmap() == expected_cmap
        assert "glyf" in font
        assert "CFF " not in font and "CFF2" not in font
        assert font.getGlyphOrder() == [".notdef", *expected_cmap.values()]
        for glyph_name in expected_cmap.values():
            glyph = font["glyf"][glyph_name]
            assert not glyph.isComposite()
            assert glyph.numberOfContours > 0
            assert font["hmtx"].metrics[glyph_name][0] == pipeline.ADVANCE
            # TrueType flags are on/off-curve quadratic point flags; a cubic
            # segment cannot exist in a glyf outline.
            assert all((flag & ~0x7F) == 0 for flag in glyph.flags)
        font.close()


def test_true_type_winding_and_counters_are_preserved(
    pilot_build: tuple[Path, dict],
) -> None:
    output, report = pilot_build
    font = TTFont(output / report["font"]["ttf"], recalcTimestamp=False)
    glyph_set = font["glyf"]
    counter_characters: set[str] = set()
    for character in PILOT_CHARACTERS:
        glyph = glyph_set[f"uni{ord(character):04X}"]
        coordinates, end_points, _ = glyph.getCoordinates(glyph_set)
        areas: list[float] = []
        start = 0
        for end in end_points:
            contour = [
                (int(coordinates[index][0]), int(coordinates[index][1]))
                for index in range(start, end + 1)
            ]
            assert len(contour) >= 4
            assert all(a != b for a, b in zip(contour, contour[1:] + contour[:1]))
            areas.append(_signed_area(contour))
            start = end + 1
        assert areas
        assert max(areas, key=abs) < 0  # clockwise outer contour
        if any(area > 0 for area in areas):
            counter_characters.add(character)
    # These closed handwritten structures visibly require white counters.
    assert {"的", "是", "這", "為"} <= counter_characters
    font.close()


def test_no_zero_length_edges_micro_thorns_or_excess_nodes(
    pilot_build: tuple[Path, dict],
) -> None:
    _, report = pilot_build
    for glyph in report["glyphs"]:
        assert glyph["minimum_control_edge"] >= 1.0
        assert glyph["micro_edge_count"] == 0
        assert glyph["acute_micro_turn_count"] == 0
        assert glyph["point_count"] <= 260
        assert glyph["maximum_position_delta"] <= pipeline.MAX_BBOX_EDGE_DELTA


def test_mixed_on_off_quantization_duplicate_is_canonicalized() -> None:
    glyph = Glyph()
    glyph.numberOfContours = 1
    glyph.coordinates = GlyphCoordinates(
        [(0, 0), (0, 40), (40, 80), (80, 40), (40, 0), (40, 0)]
    )
    glyph.flags = array("B", [1, 1, 1, 1, 0, 1])
    glyph.endPtsOfContours = [5]
    unrounded = [
        (0.0, 0.0),
        (0.0, 40.0),
        (40.0, 80.0),
        (80.0, 40.0),
        (39.7, 0.1),
        (40.2, -0.1),
    ]

    removed, maximum_collapse = (
        pipeline._canonicalize_quantized_on_off_duplicates(
            glyph, unrounded
        )
    )

    assert removed == 1
    assert 0 < maximum_collapse < 1
    assert list(glyph.coordinates) == [
        (0, 0),
        (0, 40),
        (40, 80),
        (80, 40),
        (40, 0),
    ]
    assert list(glyph.flags) == [1, 1, 1, 1, 1]
    pipeline._geometry_quality(glyph)


def test_same_type_quantization_duplicate_remains_fail_closed() -> None:
    glyph = Glyph()
    glyph.numberOfContours = 1
    glyph.coordinates = GlyphCoordinates(
        [(0, 0), (40, 0), (40, 0), (80, 40), (40, 80), (0, 40)]
    )
    glyph.flags = array("B", [1, 1, 1, 1, 1, 1])
    glyph.endPtsOfContours = [5]
    unrounded = [
        (0.0, 0.0),
        (39.7, 0.1),
        (40.2, -0.1),
        (80.0, 40.0),
        (40.0, 80.0),
        (0.0, 40.0),
    ]

    with pytest.raises(
        pipeline.ImagegenPipelineError,
        match="same-type duplicate pair",
    ):
        pipeline._canonicalize_quantized_on_off_duplicates(
            glyph, unrounded
        )


def test_position_audit_uses_exact_quadratic_not_control_bounds() -> None:
    pen = pipeline.TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.qCurveTo((50, 100), (100, 0))
    pen.lineTo((100, -20))
    pen.lineTo((0, -20))
    pen.closePath()
    glyph = pen.glyph()

    assert pipeline._glyph_bbox(glyph) == (0, -20, 100, 100)
    assert pipeline._glyph_outline_bbox(glyph) == (0.0, -20.0, 100.0, 50.0)


def test_acute_micro_thorn_becomes_bounded_implied_point() -> None:
    glyph = Glyph()
    glyph.numberOfContours = 1
    glyph.coordinates = GlyphCoordinates(
        [(0, 0), (0, 40), (40, 80), (80, 40), (40, 0), (40, 4), (40, 3)]
    )
    glyph.flags = array("B", [1, 1, 1, 1, 0, 1, 0])
    glyph.endPtsOfContours = [6]

    removed, maximum_displacement, coincident_flanks_removed = (
        pipeline._remove_acute_implied_point_thorns(glyph)
    )

    assert removed == 1
    assert coincident_flanks_removed == 0
    assert 0 < maximum_displacement <= (
        pipeline.MICRO_THORN_MAX_IMPLIED_DISPLACEMENT
    )
    assert list(glyph.coordinates) == [
        (0, 0),
        (0, 40),
        (40, 80),
        (80, 40),
        (40, 0),
        (40, 3),
    ]
    assert list(glyph.flags) == [1, 1, 1, 1, 0, 0]
    quality = pipeline._geometry_quality(glyph)
    assert quality[-1] == 0


def test_coincident_flank_micro_thorn_collapses_to_one_control() -> None:
    glyph = Glyph()
    glyph.numberOfContours = 1
    glyph.coordinates = GlyphCoordinates(
        [
            (0, 0),
            (0, 40),
            (40, 80),
            (80, 40),
            (60, 4),
            (40, 0),
            (39, 0),
            (40, 0),
            (20, 4),
        ]
    )
    glyph.flags = array("B", [1, 1, 1, 1, 1, 0, 1, 0, 1])
    glyph.endPtsOfContours = [8]

    removed, displacement, coincident_flanks_removed = (
        pipeline._remove_acute_implied_point_thorns(glyph)
    )

    assert removed == 1
    assert displacement == 1
    assert coincident_flanks_removed == 1
    assert list(glyph.coordinates).count((40, 0)) == 1
    assert all(
        first != second
        for first, second in zip(
            list(glyph.coordinates),
            [*list(glyph.coordinates)[1:], list(glyph.coordinates)[0]],
        )
    )
    quality = pipeline._geometry_quality(glyph)
    assert quality[-1] == 0


@pytest.mark.parametrize(
    ("batch_id", "known_canonicalized_character"),
    [
        ("common-0003", "來"),
        ("common-0004", "後"),
        ("common-0005", "等"),
        ("common-0006", "法"),
    ],
)
def test_formal_batches_canonicalize_only_audited_quantization_pairs(
    batch_id: str,
    known_canonicalized_character: str,
    tmp_path: Path,
) -> None:
    output = pipeline.build_batch(
        pipeline.IMAGEGEN_ROOT / f"batches/{batch_id}.source.json",
        output_root=tmp_path,
    )
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    records = {
        record["character"]: record for record in report["glyphs"]
    }
    assert (
        records[known_canonicalized_character][
            "quantization_duplicate_points_removed"
        ]
        >= 1
    )
    for record in records.values():
        assert record["maximum_quantization_collapse"] <= 2**0.5
        assert record["maximum_micro_thorn_displacement"] <= (
            pipeline.MICRO_THORN_MAX_IMPLIED_DISPLACEMENT
        )
        assert record["minimum_control_edge"] >= 1
        assert record["micro_edge_count"] == 0
        assert record["acute_micro_turn_count"] == 0


def test_formal_batch_with_control_overshoot_passes_exact_position_audit(
    tmp_path: Path,
) -> None:
    output = pipeline.build_batch(
        pipeline.IMAGEGEN_ROOT / "batches/common-0008.source.json",
        output_root=tmp_path,
    )
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["pipeline"] == "imagegen-raster-potrace-quadratic-v2"
    clear = next(
        record for record in report["glyphs"] if record["character"] == "清"
    )
    assert clear["maximum_position_delta"] <= pipeline.MAX_BBOX_EDGE_DELTA


def test_formal_batch_collapses_only_bounded_coincident_flank_thorn(
    tmp_path: Path,
) -> None:
    output = pipeline.build_batch(
        pipeline.IMAGEGEN_ROOT / "batches/common-0021.source.json",
        output_root=tmp_path,
    )
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    falling = next(
        record for record in report["glyphs"] if record["character"] == "落"
    )
    assert falling["micro_thorn_points_removed"] == 1
    assert falling["coincident_flank_control_points_removed"] == 1
    assert falling["maximum_micro_thorn_displacement"] == 1
    assert falling["acute_micro_turn_count"] == 0


def test_black_and_white_small_size_freetype_rendering(
    pilot_build: tuple[Path, dict],
) -> None:
    output, report = pilot_build
    ttf_path = output / report["font"]["ttf"]
    otf_path = output / report["font"]["otf"]
    ttf_face = freetype.Face(str(ttf_path))
    otf_face = freetype.Face(str(otf_path))
    for character in PILOT_CHARACTERS:
        for size in (12, 16, 20, 32, 56):
            ttf_alpha, _, _, ttf_advance = pipeline._load_rendered_glyph(
                ttf_face, character, size
            )
            otf_alpha, _, _, otf_advance = pipeline._load_rendered_glyph(
                otf_face, character, size
            )
            assert ttf_advance == otf_advance > 0
            assert np.array_equal(ttf_alpha, otf_alpha)
            assert np.count_nonzero(ttf_alpha) >= max(2, size // 6)


def test_reproducible_byte_for_byte(
    pilot_build: tuple[Path, dict],
    tmp_path: Path,
) -> None:
    first_output, first_report = pilot_build
    second_output = pipeline.build_batch(
        pipeline.DEFAULT_DESCRIPTOR, output_root=tmp_path / "second"
    )
    assert _file_hashes(first_output) == _file_hashes(second_output)
    second_report = json.loads(
        (second_output / "report.json").read_text(encoding="utf-8")
    )
    assert first_report == second_report
