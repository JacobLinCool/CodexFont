from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import unicodedata

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
import numpy as np
from PIL import Image, ImageDraw
import pytest

from scripts import imagegen_nonhan_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
# The isolated pipeline fixture uses the same approved A–P raster as the
# production descriptor. Tests create fresh local provenance and never depend
# on rejected or quarantined artifacts.
PILOT_RASTER_FIXTURE = IMAGEGEN_ROOT / "raster/nonhan-0001.png"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pilot_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    imagegen = project / "sources/imagegen"
    for relative in (
        "batches",
        "copybooks",
        "prompts",
        "raster",
        "repertoires",
    ):
        (imagegen / relative).mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        IMAGEGEN_ROOT / "repertoires/nonhan-3060.json",
        imagegen / "repertoires/nonhan-3060.json",
    )
    shutil.copy2(
        IMAGEGEN_ROOT / "copybooks/nonhan-0001.png",
        imagegen / "copybooks/nonhan-0001.png",
    )
    shutil.copy2(
        IMAGEGEN_ROOT / "prompts/nonhan-0001.md",
        imagegen / "prompts/nonhan-0001.md",
    )
    shutil.copy2(
        IMAGEGEN_ROOT / "raster/common-0001.png",
        imagegen / "raster/common-0001.png",
    )
    raster = imagegen / "raster/nonhan-0001.png"
    shutil.copy2(PILOT_RASTER_FIXTURE, raster)

    draft = json.loads(
        (
            IMAGEGEN_ROOT / "batches/nonhan-0001.draft.json"
        ).read_text(encoding="utf-8")
    )
    draft["state"] = "generated-unreviewed"
    draft["generator_call"] = "call_test_nonhan_0001"
    draft["raster_sha256"] = _sha256(raster)
    descriptor = imagegen / "batches/nonhan-0001.source.json"
    descriptor.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return project, descriptor


def _rewrite_descriptor(
    descriptor: Path,
    mutator: object,
) -> None:
    payload = json.loads(descriptor.read_text(encoding="utf-8"))
    assert callable(mutator)
    mutator(payload)
    descriptor.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _materialized_record(codepoint: int) -> dict[str, object]:
    label = f"U+{codepoint:04X}"
    for draft_path in sorted(
        (IMAGEGEN_ROOT / "batches").glob("nonhan-*.draft.json")
    ):
        payload = json.loads(draft_path.read_text(encoding="utf-8"))
        for record in payload["grid"]["glyphs"]:
            if record["codepoint"] == label:
                return record
    raise AssertionError(f"missing materialized record {label}")


def _rectangle_vector(
    spec: pipeline.GlyphSpec,
    *,
    x_min: int,
    y_min: int,
    x_max: int,
    y_max: int,
    edge_contacts: dict[str, bool] | None = None,
) -> pipeline.VectorizedGlyph:
    pen = TTGlyphPen(None)
    pen.moveTo((x_min, y_min))
    pen.lineTo((x_min, y_max))
    pen.lineTo((x_max, y_max))
    pen.lineTo((x_max, y_min))
    pen.closePath()
    outline = pen.glyph()
    contacts = edge_contacts or {
        "left": False,
        "right": False,
        "top": False,
        "bottom": False,
    }
    cell = pipeline.SegmentedNonHanCell(
        spec=spec,
        row=0,
        column=0,
        source_box=(0, 0, 256, 256),
        source_ink_bbox=(0.25, 0.25, 0.75, 0.75),
        core_component_count=1,
        core_pixel_count=1024,
        ink_fraction=1024 / (256 * 256),
        segmentation_profile=pipeline._segmentation_profile(spec),
        edge_contacts=contacts,
        edge_contact_pixels={edge: int(value) for edge, value in contacts.items()},
        cleaned=Image.new("L", (512, 512), 255),
    )
    return pipeline.VectorizedGlyph(
        spec=spec,
        cell=cell,
        name=pipeline._glyph_name(spec.codepoint),
        outline=outline,
        contour_count=1,
        point_count=4,
        outer_contour_count=1,
        counter_count=0,
        minimum_control_edge=float(min(x_max - x_min, y_max - y_min)),
        quantization_duplicate_points_removed=0,
        maximum_quantization_collapse=0.0,
        micro_thorn_points_removed=0,
        maximum_micro_thorn_displacement=0.0,
        coincident_flank_control_points_removed=0,
        micro_edge_count=0,
        acute_micro_turn_count=0,
        pre_metric_bounds=(
            float(x_min),
            float(y_min),
            float(x_max),
            float(y_max),
        ),
    )


def test_zero_advance_visible_mark_contract_is_exact() -> None:
    expected = {
        *range(0x0300, 0x0358),
        *range(0x035D, 0x0370),
        *range(0x302A, 0x302E),
        0x3099,
        0x309A,
    }
    expected.remove(0x034F)
    assert pipeline.ZERO_ADVANCE_VISIBLE_MARKS == expected
    assert len(expected) == 112
    assert {0x302E, 0x302F}.isdisjoint(expected)

    for codepoint in sorted(expected):
        policy = pipeline._metrics_policy(
            {
                "horizontal_advance": {"kind": "fixed", "value": 0},
                "vertical_advance": {"kind": "fixed", "value": 0},
                "side_bearings": {"left": 0, "right": 0},
                "mark_class": f"ccc-{unicodedata.combining(chr(codepoint))}",
            },
            codepoint=codepoint,
            profile_id="nonspacing-mark",
            transform_profile="mark",
            where=f"U+{codepoint:04X}.metrics",
        )
        assert policy.horizontal_advance.value == 0
        assert policy.vertical_advance == 0


def test_small_size_coverage_contract_is_profile_aware() -> None:
    assert pipeline.MINIMUM_PROOF_COVERAGE_PIXELS == 2
    assert pipeline.DEFAULT_PROOF_COVERAGE_DIVISOR == 6
    assert pipeline.MARK_PROOF_COVERAGE_DIVISOR == 10
    assert [
        max(
            pipeline.MINIMUM_PROOF_COVERAGE_PIXELS,
            size // pipeline.DEFAULT_PROOF_COVERAGE_DIVISOR,
        )
        for size in pipeline.SMALL_SIZE_PIXELS
    ] == [2, 2, 3, 5, 9]
    assert [
        max(
            pipeline.MINIMUM_PROOF_COVERAGE_PIXELS,
            size // pipeline.MARK_PROOF_COVERAGE_DIVISOR,
        )
        for size in pipeline.SMALL_SIZE_PIXELS
    ] == [2, 2, 2, 3, 5]
    assert pipeline.GRID_RULE_INTERIOR_PADDING == 2


def test_runtime_has_no_rejected_or_authored_source_path() -> None:
    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    assert "rejected" not in source
    assert "sources/authored" not in source


def test_spacing_hangul_tone_marks_are_positive_advance() -> None:
    for codepoint in sorted(pipeline.SPACING_COMBINING_MARKS):
        policy = pipeline._metrics_policy(
            {
                "horizontal_advance": {"kind": "fixed", "value": 1024},
                "vertical_advance": {"kind": "fixed", "value": 1024},
                "side_bearings": {"left": 32, "right": 32},
            },
            codepoint=codepoint,
            profile_id="cjk-wide",
            transform_profile="fullwidth",
            where=f"U+{codepoint:04X}.metrics",
        )
        assert policy.horizontal_advance.value == 1024

        with pytest.raises(
            pipeline.NonHanPipelineError,
            match="is not one of the 112 visible nonspacing marks",
        ):
            pipeline._metrics_policy(
                {
                    "horizontal_advance": {"kind": "fixed", "value": 0},
                    "vertical_advance": {"kind": "fixed", "value": 0},
                    "side_bearings": {"left": 0, "right": 0},
                    "mark_class": f"ccc-{unicodedata.combining(chr(codepoint))}",
                },
                codepoint=codepoint,
                profile_id="nonspacing-mark",
                transform_profile="mark",
                where=f"U+{codepoint:04X}.metrics",
            )


def test_vertical_kana_repeat_marks_keep_two_em_vadvance() -> None:
    for codepoint in sorted(pipeline.TWO_EM_VERTICAL_ADVANCE):
        policy = pipeline._metrics_policy(
            {
                "horizontal_advance": {"kind": "fixed", "value": 1024},
                "vertical_advance": {"kind": "fixed", "value": 2048},
                "side_bearings": {"left": 32, "right": 32},
            },
            codepoint=codepoint,
            profile_id="cjk-wide",
            transform_profile="fullwidth",
            where=f"U+{codepoint:04X}.metrics",
        )
        assert policy.vertical_advance == 2048

        with pytest.raises(
            pipeline.NonHanPipelineError,
            match="requires vertical advance 2048",
        ):
            pipeline._metrics_policy(
                {
                    "horizontal_advance": {"kind": "fixed", "value": 1024},
                    "vertical_advance": {"kind": "fixed", "value": 1024},
                    "side_bearings": {"left": 32, "right": 32},
                },
                codepoint=codepoint,
                profile_id="cjk-wide",
                transform_profile="fullwidth",
                where=f"U+{codepoint:04X}.metrics",
            )


def test_profile_metric_contracts_fail_closed() -> None:
    proportional = pipeline._metrics_policy(
        {
            "horizontal_advance": {"kind": "source-proportional"},
            "vertical_advance": {"kind": "fixed", "value": 1024},
            "side_bearings": {"left": 48, "right": 48},
        },
        codepoint=ord("A"),
        profile_id="proportional",
        transform_profile="proportional",
        where="A.metrics",
    )
    assert proportional.left_side_bearing == 48
    assert proportional.right_side_bearing == 48

    with pytest.raises(
        pipeline.NonHanPipelineError,
        match="policy bearings 48/48",
    ):
        pipeline._metrics_policy(
            {
                "horizontal_advance": {"kind": "source-proportional"},
                "vertical_advance": {"kind": "fixed", "value": 1024},
                "side_bearings": {"left": 0, "right": 0},
            },
            codepoint=ord("A"),
            profile_id="proportional",
            transform_profile="proportional",
            where="A.metrics",
        )

    for digit in "0123456789":
        policy = pipeline._metrics_policy(
            {
                "horizontal_advance": {"kind": "fixed", "value": 620},
                "vertical_advance": {"kind": "fixed", "value": 1024},
                "side_bearings": {"left": 56, "right": 56},
            },
            codepoint=ord(digit),
            profile_id="tabular-digit",
            transform_profile="proportional",
            where=f"{digit}.metrics",
        )
        assert policy.horizontal_advance.value == 620


def test_mark_resolution_builds_zero_hmtx_and_vmtx_with_ccc_anchor(
    tmp_path: Path,
) -> None:
    spec = pipeline._glyph_spec(
        _materialized_record(0x0300),
        where="U+0300 fixture",
    )
    glyph = _rectangle_vector(
        spec,
        x_min=260,
        y_min=620,
        x_max=460,
        y_max=780,
    )
    pipeline._resolve_advances([glyph])
    assert glyph.horizontal_advance == 0
    assert glyph.vertical_advance == 0
    assert pipeline._glyph_bounds(glyph.outline) == (-100, 0, 100, 160)
    assert glyph.left_side_bearing == glyph.right_side_bearing == -100
    assert glyph.mark_class == "above"
    assert glyph.anchors_candidate == {
        "kind": "mark",
        "class": "above",
        "canonical_combining_class": 230,
        "mark_anchor": {"x": 0, "y": 0},
    }

    ttf, otf = pipeline._build_fonts(
        [glyph],
        batch_id="imagegen-nonhan-9999",
        directory=tmp_path / "font",
    )
    pipeline._validate_fonts((ttf, otf), [glyph])
    for font_path in (ttf, otf):
        font = TTFont(font_path, lazy=False, checkChecksums=2)
        try:
            assert font["hmtx"].metrics[glyph.name] == (0, -100)
            assert font["vmtx"].metrics[glyph.name][0] == 0
        finally:
            font.close()
    face = pipeline.freetype.Face(str(ttf))
    assert np.count_nonzero(pipeline._rendered_alpha(face, spec.character, 16)) >= 2


def test_batch_install_restores_prior_build_when_swap_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "canonical"
    destination.mkdir()
    (destination / "state.txt").write_text("old\n", encoding="utf-8")
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "state.txt").write_text("new\n", encoding="utf-8")
    original_replace = Path.replace

    def injected_replace(self: Path, target: Path) -> Path:
        if self == stage and Path(target) == destination:
            raise OSError("injected install failure")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", injected_replace)
    with pytest.raises(
        pipeline.NonHanPipelineError,
        match="prior build restored",
    ):
        pipeline._install_build_directory(stage, destination)
    assert (destination / "state.txt").read_text(encoding="utf-8") == "old\n"
    assert (stage / "state.txt").read_text(encoding="utf-8") == "new\n"
    assert not list(tmp_path.glob(".canonical.backup-*"))


def test_tabular_digit_resolution_keeps_shared_620_advance() -> None:
    glyphs = []
    for offset, character in enumerate("0123456789"):
        spec = pipeline._glyph_spec(
            _materialized_record(ord(character)),
            where=f"{character} fixture",
        )
        width = 260 + offset * 20
        glyphs.append(
            _rectangle_vector(
                spec,
                x_min=120,
                y_min=80,
                x_max=120 + width,
                y_max=800,
            )
        )
    pipeline._resolve_advances(glyphs)
    assert {glyph.horizontal_advance for glyph in glyphs} == {620}
    assert all((glyph.left_side_bearing or 0) >= 56 for glyph in glyphs)
    assert all((glyph.right_side_bearing or 0) >= 56 for glyph in glyphs)


def test_edge_profiles_use_connectivity_instead_of_generic_ink_cap() -> None:
    solid = Image.new("L", (256, 256), 0)
    (
        _cleaned,
        bbox,
        _component_count,
        _pixels,
        fraction,
        contacts,
        contact_pixels,
    ) = pipeline._clean_cell(solid, segmentation_profile="edge")
    assert fraction == 1.0
    assert bbox == (0.0, 0.0, 1.0, 1.0)
    assert contacts == {
        "left": True,
        "right": True,
        "top": True,
        "bottom": True,
    }
    assert all(value > 0 for value in contact_pixels.values())

    with pytest.raises(
        pipeline.NonHanPipelineError,
        match="generic.*profile limits",
    ):
        pipeline._clean_cell(solid, segmentation_profile="generic")

    horizontal = Image.new("L", (256, 256), 255)
    ImageDraw.Draw(horizontal).rectangle((0, 120, 255, 136), fill=0)
    *_, horizontal_contacts, _counts = pipeline._clean_cell(
        horizontal,
        segmentation_profile="edge",
    )
    assert horizontal_contacts["left"]
    assert horizontal_contacts["right"]

    left_only = Image.new("L", (256, 256), 255)
    ImageDraw.Draw(left_only).rectangle((0, 80, 20, 176), fill=0)
    *_, left_contacts, _counts = pipeline._clean_cell(
        left_only,
        segmentation_profile="edge",
        minimum_edge_contacts=1,
    )
    assert left_contacts == {
        "left": True,
        "right": False,
        "top": False,
        "bottom": False,
    }
    with pytest.raises(
        pipeline.NonHanPipelineError,
        match="at least 2 cell edges",
    ):
        pipeline._clean_cell(left_only, segmentation_profile="edge")

    with pytest.raises(
        pipeline.NonHanPipelineError,
        match="minimum contact count",
    ):
        pipeline._clean_cell(
            horizontal,
            segmentation_profile="edge",
            minimum_edge_contacts=3,
        )


def test_edge_targets_are_unicode_semantic_and_normalize_authored_ink() -> None:
    for codepoint in range(0x2500, 0x25A0):
        spec = pipeline._glyph_spec(
            _materialized_record(codepoint),
            where=f"U+{codepoint:04X} fixture",
        )
        x_target, y_target, required = pipeline._edge_target_bounds(spec)
        assert any(required.values())
        assert x_target is not None or y_target is not None
        normalized = pipeline._normalize_edge_points(
            [(400.0, 420.0), (600.0, 620.0)],
            spec=spec,
        )
        xs = [point[0] for point in normalized]
        ys = [point[1] for point in normalized]
        if x_target is None:
            assert min(xs) == pytest.approx(412.0)
            assert max(xs) == pytest.approx(612.0)
        else:
            assert (min(xs), max(xs)) == pytest.approx(x_target)
        if y_target is None:
            assert min(ys) == pytest.approx(412.0)
            assert max(ys) == pytest.approx(612.0)
        else:
            assert (min(ys), max(ys)) == pytest.approx(y_target)

    expected = {
        0x2570: ((512.0, 1024.0), (512.0, 1024.0)),
        0x2571: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2572: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2573: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2574: ((0.0, 512.0), None),
        0x2575: (None, (512.0, 1024.0)),
        0x2576: ((512.0, 1024.0), None),
        0x2577: (None, (0.0, 512.0)),
        0x2578: ((0.0, 512.0), None),
        0x2579: (None, (512.0, 1024.0)),
        0x257A: ((512.0, 1024.0), None),
        0x257B: (None, (0.0, 512.0)),
        0x257C: ((0.0, 1024.0), None),
        0x257D: (None, (0.0, 1024.0)),
        0x257E: ((0.0, 1024.0), None),
        0x257F: (None, (0.0, 1024.0)),
        0x2580: ((0.0, 1024.0), (512.0, 1024.0)),
        0x2581: ((0.0, 1024.0), (0.0, 128.0)),
        0x2582: ((0.0, 1024.0), (0.0, 256.0)),
        0x2583: ((0.0, 1024.0), (0.0, 384.0)),
        0x2584: ((0.0, 1024.0), (0.0, 512.0)),
        0x2585: ((0.0, 1024.0), (0.0, 640.0)),
        0x2586: ((0.0, 1024.0), (0.0, 768.0)),
        0x2587: ((0.0, 1024.0), (0.0, 896.0)),
        0x2588: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2589: ((0.0, 896.0), (0.0, 1024.0)),
        0x258A: ((0.0, 768.0), (0.0, 1024.0)),
        0x258B: ((0.0, 640.0), (0.0, 1024.0)),
        0x258C: ((0.0, 512.0), (0.0, 1024.0)),
        0x258D: ((0.0, 384.0), (0.0, 1024.0)),
        0x258E: ((0.0, 256.0), (0.0, 1024.0)),
        0x258F: ((0.0, 128.0), (0.0, 1024.0)),
        0x2590: ((512.0, 1024.0), (0.0, 1024.0)),
        0x2591: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2592: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2593: ((0.0, 1024.0), (0.0, 1024.0)),
        0x2594: ((0.0, 1024.0), (896.0, 1024.0)),
        0x2595: ((896.0, 1024.0), (0.0, 1024.0)),
        0x2596: ((0.0, 512.0), (0.0, 512.0)),
        0x2597: ((512.0, 1024.0), (0.0, 512.0)),
        0x2598: ((0.0, 512.0), (512.0, 1024.0)),
        0x2599: ((0.0, 1024.0), (0.0, 1024.0)),
        0x259A: ((0.0, 1024.0), (0.0, 1024.0)),
        0x259B: ((0.0, 1024.0), (0.0, 1024.0)),
        0x259C: ((0.0, 1024.0), (0.0, 1024.0)),
        0x259D: ((512.0, 1024.0), (512.0, 1024.0)),
        0x259E: ((0.0, 1024.0), (0.0, 1024.0)),
        0x259F: ((0.0, 1024.0), (0.0, 1024.0)),
    }
    for codepoint, targets in expected.items():
        spec = pipeline._glyph_spec(
            _materialized_record(codepoint),
            where=f"U+{codepoint:04X} fixture",
        )
        assert pipeline._edge_target_bounds(spec)[:2] == targets


def test_edge_vectorization_rejects_source_component_bridge(
    tmp_path: Path,
) -> None:
    spec = pipeline._glyph_spec(
        _materialized_record(0x259A),
        where="U+259A fixture",
    )
    _x_target, _y_target, required = pipeline._edge_target_bounds(spec)
    cell = pipeline.SegmentedNonHanCell(
        spec=spec,
        row=0,
        column=0,
        source_box=(0, 0, 256, 256),
        source_ink_bbox=(0.2, 0.2, 0.8, 0.8),
        core_component_count=2,
        core_pixel_count=2048,
        ink_fraction=2048 / (256 * 256),
        segmentation_profile="edge",
        edge_contacts=required,
        edge_contact_pixels={edge: 0 for edge in required},
        cleaned=Image.new("L", (512, 512), 255),
    )
    svg = tmp_path / "bridged.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 512 512">
<g transform="translate(0.000000,512.000000) scale(0.100000,-0.100000)">
<path d="M1000 1000 L4000 1000 L4000 4000 L1000 4000 Z"/>
</g>
</svg>
""",
        encoding="utf-8",
    )

    with pytest.raises(
        pipeline.NonHanPipelineError,
        match=(
            r"U\+259A: vectorization changed source connected-component "
            r"topology \(2 source components, 1 vector outer contours\)"
        ),
    ):
        pipeline._vectorize(cell, svg)


def test_dense_solid_profile_is_exact_and_does_not_relax_generic_limit() -> None:
    dense = Image.new("L", (256, 256), 255)
    ImageDraw.Draw(dense).rectangle((57, 57, 198, 198), fill=0)
    with pytest.raises(
        pipeline.NonHanPipelineError,
        match="generic profile limits",
    ):
        pipeline._clean_cell(dense, segmentation_profile="generic")
    *_values, fraction, _contacts, _counts = pipeline._clean_cell(
        dense,
        segmentation_profile="dense-solid",
    )
    assert pipeline.GENERIC_MAX_INK_FRACTION < fraction
    assert fraction <= pipeline.DENSE_SOLID_MAX_INK_FRACTION
    assert pipeline.DENSE_SOLID_GLYPHS == {
        0x25FC: "BLACK MEDIUM SQUARE",
        0x2617: "BLACK SHOGI PIECE",
    }


def test_generic_profile_requires_clear_border_and_antialiasing() -> None:
    centered = Image.new("L", (256, 256), 255)
    ImageDraw.Draw(centered).ellipse((72, 40, 184, 216), fill=0)
    cleaned, *_rest, contacts, _counts = pipeline._clean_cell(
        centered,
        segmentation_profile="generic",
    )
    pixels = np.asarray(cleaned)
    assert np.any((pixels > 0) & (pixels < 255))
    assert not any(contacts.values())

    touching = Image.new("L", (256, 256), 255)
    ImageDraw.Draw(touching).rectangle((0, 80, 30, 176), fill=0)
    with pytest.raises(pipeline.NonHanPipelineError, match="touches the cell border"):
        pipeline._clean_cell(touching, segmentation_profile="generic")


def test_descriptor_v2_is_hash_pinned_to_repertoire_and_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, descriptor_path = _pilot_project(tmp_path)
    opened: set[Path] = set()
    original_open = Path.open

    def tracked_open(path: Path, *args: object, **kwargs: object):
        opened.add(path.resolve())
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracked_open)
    descriptor = pipeline.load_source_descriptor(
        descriptor_path,
        project_root=project,
    )
    assert descriptor.batch_id == "imagegen-nonhan-0001"
    assert descriptor.generator_call == "call_test_nonhan_0001"
    assert [glyph.character for glyph in descriptor.glyphs] == list("ABCDEFGHIJKLMNOP")
    assert {glyph.profile_id for glyph in descriptor.glyphs} == {"proportional"}
    assert all(path.is_relative_to(project) for path in opened)


def test_all_3043_materialized_records_are_accepted_without_inference() -> None:
    records = []
    placements: Counter[str] = Counter()
    draft_paths = sorted(
        (IMAGEGEN_ROOT / "batches").glob("nonhan-*.draft.json")
    )
    assert len(draft_paths) == 205
    for draft_path in draft_paths:
        payload = json.loads(draft_path.read_text(encoding="utf-8"))
        assert payload["repertoire"]["sha256"] == _sha256(
            IMAGEGEN_ROOT / "repertoires/nonhan-3060.json"
        )
        for index, raw_record in enumerate(payload["grid"]["glyphs"]):
            spec = pipeline._glyph_spec(
                raw_record,
                where=f"{draft_path.name}.grid.glyphs[{index}]",
            )
            records.append(spec)
            if spec.transform_profile == "mark":
                placements[pipeline._mark_class(spec)] += 1
    assert len(records) == 3043
    assert len({record.codepoint for record in records}) == 3043
    assert Counter(record.profile_id for record in records) == {
        "proportional": 1876,
        "tabular-digit": 10,
        "cjk-wide": 382,
        "nonspacing-mark": 112,
        "fullwidth": 494,
        "halfwidth": 9,
        "box-drawing": 128,
        "block-element": 32,
    }
    assert placements == {
        "above": 56,
        "below": 43,
        "overlay": 5,
        "double-above": 4,
        "double-below": 2,
        "above-right": 2,
    }


def test_descriptor_rejects_unknown_profiles_and_hash_drift(
    tmp_path: Path,
) -> None:
    project, descriptor_path = _pilot_project(tmp_path)
    _rewrite_descriptor(
        descriptor_path,
        lambda payload: payload["grid"]["glyphs"][0].__setitem__(
            "profile_id", "unknown-profile"
        ),
    )
    with pytest.raises(pipeline.NonHanPipelineError, match="unsupported profile"):
        pipeline.load_source_descriptor(descriptor_path, project_root=project)

    project_2, descriptor_path_2 = _pilot_project(tmp_path / "second")
    _rewrite_descriptor(
        descriptor_path_2,
        lambda payload: payload.__setitem__("raster_sha256", "0" * 64),
    )
    with pytest.raises(pipeline.NonHanPipelineError, match="raster hash mismatch"):
        pipeline.load_source_descriptor(descriptor_path_2, project_root=project_2)


def test_real_ap_pilot_build_is_reproducible_and_auditable(
    tmp_path: Path,
) -> None:
    project, descriptor_path = _pilot_project(tmp_path)
    potrace = shutil.which("potrace")
    assert potrace is not None

    first = pipeline.build_batch(
        descriptor_path,
        project_root=project,
        output_root=tmp_path / "build-one",
        potrace_executable=potrace,
    )
    second = pipeline.build_batch(
        descriptor_path,
        project_root=project,
        output_root=tmp_path / "build-two",
        potrace_executable=potrace,
    )
    assert first.name == second.name == "imagegen-nonhan-0001"

    first_report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    second_report = json.loads((second / "report.json").read_text(encoding="utf-8"))
    assert first_report == second_report
    assert first_report["pipeline"] == (
        "imagegen-raster-potrace-quadratic-nonhan-v3"
    )
    assert first_report["batch_id"] == "imagegen-nonhan-0001"
    assert first_report["approval_state"] == "unreviewed"
    assert first_report["source_generator"] == "built-in-image_gen"
    assert first_report["source_generator_call"] == "call_test_nonhan_0001"
    assert first_report["codepoints"] == [
        f"U+{codepoint:04X}" for codepoint in range(ord("A"), ord("P") + 1)
    ]
    assert first_report["metric_contract"]["profile_transforms"] == {
        "fullwidth": "fullwidth",
        "halfwidth": "halfwidth",
        "proportional": "proportional",
        "tabular-digit": "proportional",
        "nonspacing-mark": "mark",
        "box-drawing": "edge",
        "block-element": "edge",
        "cjk-wide": "fullwidth",
    }
    assert first_report["vectorization"]["small_size_proof_coverage"] == {
        "minimum_pixels": 2,
        "default_size_divisor": 6,
        "nonspacing_mark_size_divisor": 10,
    }
    assert first_report["vectorization"]["grid_rule_interior_padding_px"] == 2
    assert first_report["vectorization"][
        "segmentation_ink_fraction_limits"
    ] == {
        "generic": 0.30,
        "dense-solid": 0.34,
        "edge": 1.0,
    }
    assert first_report["vectorization"]["dense_solid_codepoints"] == [
        "U+25FC",
        "U+2617",
    ]

    small_size_proofs = [
        record
        for record in first_report["proofs"]
        if record["kind"] == "small-size"
    ]
    assert {
        (record["size_px"], record["polarity"])
        for record in small_size_proofs
    } == {
        (size, polarity)
        for size in pipeline.SMALL_SIZE_PIXELS
        for polarity in ("black-on-white", "white-on-black")
    }
    assert {record["kind"] for record in first_report["proofs"]} >= {
        "segmented-source",
        "edge-connect",
    }

    for glyph in first_report["glyphs"]:
        assert glyph["profile_id"] == "proportional"
        assert glyph["metric_policy"]["horizontal_advance"] == {
            "kind": "source-proportional"
        }
        assert glyph["metrics"]["left_side_bearing"] == 48
        assert glyph["metrics"]["right_side_bearing"] == 48
        assert glyph["metrics"]["horizontal_advance"] > 96
        assert glyph["metrics"]["vertical_advance"] == 1024
        assert glyph["anchors_candidate"]["kind"] == "base"
        assert glyph["micro_edge_count"] == 0
        assert glyph["acute_micro_turn_count"] == 0
        assert glyph["micro_thorn_points_removed"] == 0
        assert set(glyph["coverage_pixels"]) == {
            str(size) for size in pipeline.SMALL_SIZE_PIXELS
        }

    for relative, expected_hash in first_report["artifact_sha256"].items():
        artifact = first / relative
        assert artifact.is_file()
        assert _sha256(artifact) == expected_hash

    for font_key in ("ttf", "otf"):
        font_path = first / first_report["font"][font_key]
        font = TTFont(font_path, lazy=False, checkChecksums=2)
        try:
            assert font.getBestCmap() == {
                codepoint: f"uni{codepoint:04X}"
                for codepoint in range(ord("A"), ord("P") + 1)
            }
            assert "vhea" in font and "vmtx" in font
            for glyph in first_report["glyphs"]:
                name = glyph["glyph_name"]
                metrics = glyph["metrics"]
                assert font["hmtx"].metrics[name] == (
                    metrics["horizontal_advance"],
                    metrics["left_side_bearing"],
                )
                assert font["vmtx"].metrics[name] == (
                    metrics["vertical_advance"],
                    metrics["top_side_bearing"],
                )
        finally:
            font.close()
