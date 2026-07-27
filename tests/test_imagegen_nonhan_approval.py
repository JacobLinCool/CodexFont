from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from PIL import Image
import pytest

from scripts import imagegen_nonhan_approval as approval
from scripts import record_imagegen_nonhan_approval as recorder


ROOT = Path(__file__).resolve().parents[1]
REPERTOIRE = ROOT / "sources/imagegen/repertoires/nonhan-3060.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _png(
    path: Path,
    *,
    blank: bool = False,
    size: tuple[int, int] = (64, 64),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("L", size, 255 if blank else 0)
    if not blank:
        image.putpixel((size[0] - 1, size[1] - 1), 255)
    image.save(path, optimize=False)


def _glyph_name(codepoint: int) -> str:
    return f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"


def _empty_glyph():
    return TTGlyphPen(None).glyph()


def _rectangle_glyph(
    bounds: tuple[int, int, int, int],
):
    x_min, y_min, x_max, y_max = bounds
    pen = TTGlyphPen(None)
    pen.moveTo((x_min, y_min))
    pen.lineTo((x_min, y_max))
    pen.lineTo((x_max, y_max))
    pen.lineTo((x_max, y_min))
    pen.closePath()
    return pen.glyph()


def _save_font(
    path: Path,
    *,
    characters: Sequence[str],
    names: Sequence[str],
    outlines: Mapping[str, Any],
    horizontal_metrics: Mapping[str, tuple[int, int]],
    vertical_metrics: Mapping[str, tuple[int, int]],
) -> None:
    glyph_order = [".notdef", *names]
    builder = FontBuilder(approval.UPM, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(
        {
            ord(character): name
            for character, name in zip(characters, names, strict=True)
        }
    )
    builder.setupGlyf({".notdef": _empty_glyph(), **outlines})
    builder.setupHorizontalMetrics(
        {".notdef": (approval.UPM, 0), **horizontal_metrics}
    )
    builder.setupVerticalMetrics(
        {".notdef": (approval.UPM, 0), **vertical_metrics}
    )
    builder.setupHorizontalHeader(ascent=930, descent=-210, lineGap=0)
    builder.setupVerticalHeader(ascent=500, descent=-500, lineGap=0)
    builder.setupNameTable(
        {
            "familyName": "Synthetic NonHan Evidence",
            "styleName": "Regular",
            "uniqueFontIdentifier": "Synthetic NonHan Evidence 1",
            "fullName": "Synthetic NonHan Evidence Regular",
            "psName": "SyntheticNonHanEvidence-Regular",
            "version": "Version 1.0",
        }
    )
    builder.setupOS2(
        sTypoAscender=930,
        sTypoDescender=-210,
        sTypoLineGap=0,
        usWinAscent=1024,
        usWinDescent=210,
    )
    builder.setupPost(keepGlyphNames=True)
    builder.setupMaxp()
    path.parent.mkdir(parents=True, exist_ok=True)
    builder.save(path)


def _project_repertoire(project: Path) -> dict[str, Any]:
    target = project / approval.REPERTOIRE_RELATIVE_PATH.as_posix()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPERTOIRE, target)
    return _read_json(target)


def _batch_payload(
    repertoire: Mapping[str, Any],
    batch_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    batch = next(
        item for item in repertoire["batches"] if item["batch_id"] == batch_id
    )
    index = {item["codepoint"]: item for item in repertoire["glyphs"]}
    glyphs = [index[label] for label in batch["glyph_codepoints"]]
    return batch, glyphs


def _visible_bounds_and_metrics(
    glyph: Mapping[str, Any],
) -> tuple[tuple[int, int, int, int], int, int, int, int]:
    profile = glyph["profile_id"]
    policy = glyph["metrics"]
    vertical = policy["vertical_advance"]["value"]
    if profile == "nonspacing-mark":
        bounds = (-100, 0, 100, 200)
        return bounds, 0, -100, -100, vertical
    if profile in {"box-drawing", "block-element"}:
        bounds = (0, 0, 1024, 1024)
        return bounds, 1024, 0, 0, vertical
    horizontal = policy["horizontal_advance"]
    left = policy["side_bearings"]["left"]
    right = policy["side_bearings"]["right"]
    if horizontal["kind"] == "source-proportional":
        bounds = (left, 0, left + 200, 800)
        advance = left + 200 + right
        return bounds, advance, left, right, vertical
    assert horizontal["kind"] == "fixed"
    advance = horizontal["value"]
    bounds = (left, 0, advance - right, 800)
    return bounds, advance, left, right, vertical


def _artifact_inventory(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): _sha256(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != "report.json"
    }


def _prepare_visible_batch(project: Path, batch_id: str) -> Path:
    repertoire = _project_repertoire(project)
    batch, glyphs = _batch_payload(repertoire, batch_id)
    assert batch["batch_kind"] == "raster-outline"
    imagegen = project / "sources/imagegen"
    raster = imagegen / f"raster/{batch_id}.png"
    copybook = imagegen / f"copybooks/{batch_id}.png"
    style = imagegen / "raster/common-0001.png"
    prompt = imagegen / f"prompts/{batch_id}.md"
    _png(raster)
    _png(copybook)
    if not style.exists():
        _png(style)
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text(f"Exact synthetic prompt for {batch_id}.\n", encoding="utf-8")

    reference = {
        "role": "identity-reference-only-no-outline-import",
        "font_path": "fixtures/reference.ttf",
        "font_sha256": "a" * 64,
        "font_index": 0,
        "postscript_name": "SyntheticReference",
        "glyph_name": "referenceGlyph",
        "validation": [
            "exact-cmap-hit",
            "non-notdef-glyph-name",
            "non-empty-distinct-outline",
            "non-empty-pillow-raster",
        ],
    }
    descriptor = {
        "schema_version": 2,
        "batch_id": f"imagegen-{batch_id}",
        "state": "generated-unreviewed",
        "generator": "built-in-image_gen",
        "generator_call": f"call_synthetic_{batch_id}",
        "repertoire": {
            "path": "../repertoires/nonhan-3060.json",
            "sha256": _sha256(
                project / approval.REPERTOIRE_RELATIVE_PATH.as_posix()
            ),
            "repertoire_id": approval.REPERTOIRE_ID,
            "batch_id": batch_id,
        },
        "raster": f"../raster/{batch_id}.png",
        "raster_sha256": _sha256(raster),
        "prompt": f"../prompts/{batch_id}.md",
        "copybook": {
            "path": f"../copybooks/{batch_id}.png",
            "sha256": _sha256(copybook),
            "role": "identity-reference-only-no-outline-import",
        },
        "style_reference": {
            "path": "../raster/common-0001.png",
            "sha256": _sha256(style),
            "role": "style-only",
        },
        "grid": {
            "rows": 4,
            "columns": 4,
            "glyphs": [
                {**glyph, "copybook_reference": dict(reference)}
                for glyph in glyphs
            ],
            "empty_grid_cells": batch["empty_grid_cells"],
        },
        "review": {
            "identity": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }
    descriptor_path = imagegen / f"batches/{batch_id}.source.json"
    _write_json(descriptor_path, descriptor)

    build = project / f"build/imagegen/imagegen-{batch_id}"
    for relative in ("png", "svg", "glyph-report", "font", "proof"):
        (build / relative).mkdir(parents=True, exist_ok=True)
    report_glyphs: list[dict[str, Any]] = []
    outlines: dict[str, Any] = {}
    hmetrics: dict[str, tuple[int, int]] = {}
    vmetrics: dict[str, tuple[int, int]] = {}
    for index, glyph in enumerate(glyphs):
        codepoint = int(glyph["codepoint"][2:], 16)
        name = _glyph_name(codepoint)
        bounds, advance, left, right, vertical = _visible_bounds_and_metrics(
            glyph
        )
        outlines[name] = _rectangle_glyph(bounds)
        top = approval.VERTICAL_ORIGIN_Y - bounds[3]
        hmetrics[name] = (advance, left)
        vmetrics[name] = (vertical, top)
        source_png = build / f"png/u{codepoint:04x}-source.png"
        svg = build / f"svg/u{codepoint:04x}.svg"
        _png(source_png)
        svg.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"/>\n", encoding="utf-8")
        profile = glyph["profile_id"]
        mark_class = glyph["metrics"].get("mark_class")
        if profile == "nonspacing-mark":
            placement = approval._expected_mark_placement(
                approval.RepertoireGlyph(
                    character=glyph["character"],
                    codepoint=codepoint,
                    codepoint_label=glyph["codepoint"],
                    canonical_rank=glyph["canonical_rank"],
                    authoring_rank=glyph["authoring_rank"],
                    name=glyph["name"],
                    general_category=glyph["gc"],
                    outline_required=True,
                    profile_id=profile,
                    metrics=glyph["metrics"],
                    record=glyph,
                )
            )
            anchors: Mapping[str, Any] = {
                "kind": "mark",
                "class": placement,
                "canonical_combining_class": int(mark_class.split("-")[1]),
                "mark_anchor": {"x": 0, "y": 0},
            }
        else:
            placement = None
            anchors = {
                "kind": "base",
                "top": {"x": 0, "y": 900},
                "bottom": {"x": 0, "y": -100},
                "overlay": {"x": 0, "y": 400},
                "above_right": {"x": advance, "y": 900},
                "ideographic_left": {"x": 0, "y": 400},
            }
        edge = profile in {"box-drawing", "block-element"}
        report_glyph = {
            "character": glyph["character"],
            "codepoint": glyph["codepoint"],
            "unicode_name": glyph["name"],
            "glyph_name": name,
            "profile_id": profile,
            "transform_profile": approval.PROFILE_TRANSFORMS[profile],
            "segmentation_profile": "edge" if edge else "generic",
            "metric_policy": glyph["metrics"],
            "row": index // 4,
            "column": index % 4,
            "source_box": [0, 0, 64, 64],
            "source_ink_bbox_normalized": [0.1, 0.1, 0.9, 0.9],
            "source_ink_fraction": 0.25,
            "source_component_count": 1,
            "source_core_pixel_count": 64,
            "edge_contacts": {
                "left": edge,
                "right": edge,
                "top": edge,
                "bottom": edge,
            },
            "edge_contact_pixels": {
                "left": 4 if edge else 0,
                "right": 4 if edge else 0,
                "top": 4 if edge else 0,
                "bottom": 4 if edge else 0,
            },
            "vector_edge_contacts": (
                {
                    "left": True,
                    "right": True,
                    "top": True,
                    "bottom": True,
                }
                if edge
                else None
            ),
            "pre_metric_bounds": [float(value) for value in bounds],
            "final_bounds": list(bounds),
            "metrics": {
                "horizontal_advance": advance,
                "left_side_bearing": left,
                "right_side_bearing": right,
                "vertical_advance": vertical,
                "vertical_origin_y": approval.VERTICAL_ORIGIN_Y,
                "top_side_bearing": top,
                "metric_source": glyph["metrics"]["horizontal_advance"]["kind"],
                "reference_codepoint": (
                    glyph["metrics"]["horizontal_advance"].get("codepoint")
                ),
            },
            "mark_class": mark_class,
            "mark_placement": placement,
            "anchors_candidate": anchors,
            "contour_count": 1,
            "point_count": 4,
            "outer_contour_count": 1,
            "counter_count": 0,
            "minimum_control_edge": float(
                min(bounds[2] - bounds[0], bounds[3] - bounds[1])
            ),
            "quantization_duplicate_points_removed": 0,
            "maximum_quantization_collapse": 0.0,
            "micro_thorn_points_removed": 0,
            "maximum_micro_thorn_displacement": 0.0,
            "coincident_flank_control_points_removed": 0,
            "micro_edge_count": 0,
            "acute_micro_turn_count": 0,
            "coverage_pixels": {
                str(size): max(
                    approval.MINIMUM_PROOF_COVERAGE_PIXELS,
                    size
                    // (
                        approval.MARK_PROOF_COVERAGE_DIVISOR
                        if profile == "nonspacing-mark"
                        else approval.DEFAULT_PROOF_COVERAGE_DIVISOR
                    ),
                )
                for size in approval.SMALL_SIZE_PIXELS
            },
            "source_png": f"png/{source_png.name}",
            "source_png_sha256": _sha256(source_png),
            "svg": f"svg/{svg.name}",
            "svg_sha256": _sha256(svg),
        }
        report_glyphs.append(report_glyph)
        _write_json(
            build / f"glyph-report/u{codepoint:04x}.json",
            report_glyph,
        )

    ttf = build / f"font/Synthetic-{batch_id}.ttf"
    otf = build / f"font/Synthetic-{batch_id}.otf"
    _save_font(
        ttf,
        characters=[glyph["character"] for glyph in glyphs],
        names=[record["glyph_name"] for record in report_glyphs],
        outlines=outlines,
        horizontal_metrics=hmetrics,
        vertical_metrics=vmetrics,
    )
    shutil.copy2(ttf, otf)

    proofs: list[dict[str, Any]] = []
    for size in approval.SMALL_SIZE_PIXELS:
        for polarity in approval.VISUAL_POLARITIES:
            proof = build / f"proof/{polarity}-{size}px.png"
            _png(proof)
            proofs.append(
                {
                    "kind": "small-size",
                    "polarity": polarity,
                    "size_px": size,
                    "path": f"proof/{proof.name}",
                    "sha256": _sha256(proof),
                    "cell_size_px": max(36, size + 24),
                }
            )
    for kind, filename in (
        ("segmented-source", "segmented-source-contact.png"),
        ("edge-connect", "edge-connect.png"),
    ):
        proof = build / f"proof/{filename}"
        _png(proof)
        proofs.append(
            {
                "kind": kind,
                "path": f"proof/{filename}",
                "sha256": _sha256(proof),
            }
        )
    report = {
        "schema_version": 1,
        "pipeline": approval.VISIBLE_PIPELINE,
        "approval_state": "unreviewed",
        "batch_id": f"imagegen-{batch_id}",
        "source_type": approval.VISIBLE_SOURCE_TYPE,
        "source_descriptor": f"sources/imagegen/batches/{batch_id}.source.json",
        "source_descriptor_sha256": _sha256(descriptor_path),
        "source_generator": "built-in-image_gen",
        "source_generator_call": descriptor["generator_call"],
        "source_repertoire": approval.REPERTOIRE_RELATIVE_PATH.as_posix(),
        "source_repertoire_sha256": descriptor["repertoire"]["sha256"],
        "source_prompt": f"sources/imagegen/prompts/{batch_id}.md",
        "source_prompt_sha256": _sha256(prompt),
        "source_copybook": f"sources/imagegen/copybooks/{batch_id}.png",
        "source_copybook_sha256": _sha256(copybook),
        "source_style_reference": "sources/imagegen/raster/common-0001.png",
        "source_style_reference_sha256": _sha256(style),
        "source_raster": f"sources/imagegen/raster/{batch_id}.png",
        "source_raster_sha256": _sha256(raster),
        "source_state": "generated-unreviewed",
        "source_review": descriptor["review"],
        "characters": [glyph["character"] for glyph in glyphs],
        "codepoints": [glyph["codepoint"] for glyph in glyphs],
        "grid": {
            "rows": 4,
            "columns": 4,
            "empty_grid_cells": batch["empty_grid_cells"],
            "cell_slots": [
                *[glyph["codepoint"] for glyph in glyphs],
                *(None for _ in range(batch["empty_grid_cells"])),
            ],
            "x_rule_centers": [0, 1, 2, 3, 4],
            "y_rule_centers": [0, 1, 2, 3, 4],
            "x_rule_spans": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]],
            "y_rule_spans": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]],
            "synthesized_coordinates": False,
        },
        "metric_contract": {
            "units_per_em": approval.UPM,
            "vertical_origin_y": approval.VERTICAL_ORIGIN_Y,
            "zero_advance_visible_mark_count": 112,
            "spacing_combining_marks": ["U+302E", "U+302F"],
            "two_em_vertical_advance": ["U+3031", "U+3032"],
            "profile_transforms": dict(approval.PROFILE_TRANSFORMS),
            "proportional_advance": (
                "source-outline-width-plus-audited-fixed-side-bearings"
            ),
        },
        "vectorization": {
            "tool": "synthetic-potrace-1",
            "outline_format": "TrueType quadratic glyf",
            "cu2qu_max_error": 2.0,
            "grid_rules_removed_by_detected_rule_spans": True,
            "grid_rule_interior_padding_px": 2,
            "segmentation_ink_fraction_limits": dict(
                approval.SEGMENTATION_INK_FRACTION_LIMITS
            ),
            "dense_solid_codepoints": [
                f"U+{value:04X}" for value in approval.DENSE_SOLID_GLYPHS
            ],
            "edge_profile_preserves_border_contacts": True,
            "small_size_proof_coverage": {
                "minimum_pixels": 2,
                "default_size_divisor": 6,
                "nonspacing_mark_size_divisor": 10,
            },
        },
        "font": {
            "units_per_em": approval.UPM,
            "ttf": f"font/{ttf.name}",
            "ttf_sha256": _sha256(ttf),
            "otf": f"font/{otf.name}",
            "otf_sha256": _sha256(otf),
            "cmap_count": len(glyphs),
            "glyph_count": len(glyphs) + 1,
            "has_vertical_metrics": True,
        },
        "proofs": proofs,
        "glyphs": report_glyphs,
        "artifact_sha256": _artifact_inventory(build),
    }
    report_path = build / "report.json"
    _write_json(report_path, report)
    return report_path


def _record_and_authorize_visible(
    project: Path,
    batch_id: str,
) -> Path:
    recorder.record_review(
        project_root=project,
        batch_id=batch_id,
        reviewer_name="Synthetic Reviewer",
        reviewer_role="Glyph QA",
        reviewed_at="2026-07-26T01:00:00Z",
        confirmation=approval.REVIEW_CONFIRMATION,
    )
    return recorder.authorize(
        project_root=project,
        batch_id=batch_id,
        approver_name="Synthetic Approver",
        approved_at="2026-07-26T02:00:00Z",
        confirmation=approval.AUTHORIZATION_CONFIRMATION,
    )


def _prepare_semantic_batch(project: Path) -> Path:
    _project_repertoire(project)
    for batch_id in ("nonhan-0005", "nonhan-0006"):
        _prepare_visible_batch(project, batch_id)
        _record_and_authorize_visible(project, batch_id)
    repertoire = approval.load_frozen_repertoire(project)
    batch = repertoire.batches[-1]
    source_by_codepoint = {
        0x0030: project
        / "sources/imagegen/approvals/nonhan-0005.approval.json",
        0x002E: project
        / "sources/imagegen/approvals/nonhan-0006.approval.json",
    }
    resolved_references: dict[int, int] = {}
    reference_records: list[dict[str, Any]] = []
    for codepoint in sorted(source_by_codepoint):
        source = source_by_codepoint[codepoint]
        validated = approval.validate_approval(source, project_root=project)
        value = approval._metric_from_visible_approval(
            validated, codepoint=codepoint
        )
        resolved_references[codepoint] = value
        reference_records.append(
            {
                "codepoint": f"U+{codepoint:04X}",
                "horizontal_advance": value,
                "source_approval": {
                    "path": source.relative_to(project).as_posix(),
                    "sha256": _sha256(source),
                },
            }
        )

    font_path = (
        project
        / "build/imagegen/imagegen-nonhan-0206/font/"
        "ClearHandTC-NonHan0206-Semantic.ttf"
    )
    glyph_names = [_glyph_name(glyph.codepoint) for glyph in batch.glyphs]
    resolved_advances: dict[int, int] = {}
    hmetrics: dict[str, tuple[int, int]] = {}
    vmetrics: dict[str, tuple[int, int]] = {}
    outlines: dict[str, Any] = {}
    for glyph, name in zip(batch.glyphs, glyph_names, strict=True):
        horizontal = glyph.metrics["horizontal_advance"]
        resolved = (
            horizontal["value"]
            if horizontal["kind"] == "fixed"
            else resolved_references[int(horizontal["codepoint"][2:], 16)]
        )
        resolved_advances[glyph.codepoint] = resolved
        hmetrics[name] = (resolved, 0)
        vmetrics[name] = (glyph.metrics["vertical_advance"]["value"], 0)
        outlines[name] = _empty_glyph()
    _save_font(
        font_path,
        characters=[glyph.character for glyph in batch.glyphs],
        names=glyph_names,
        outlines=outlines,
        horizontal_metrics=hmetrics,
        vertical_metrics=vmetrics,
    )
    proof_path = (
        project
        / "build/imagegen/imagegen-nonhan-0206/proof/blank-render.png"
    )
    _png(proof_path, blank=True, size=(320, 64))
    manifest = {
        "schema_version": 1,
        "record_type": approval.SEMANTIC_RECORD_TYPE,
        "batch_id": approval.SEMANTIC_BATCH_ID,
        "repertoire": approval._approval_repertoire_payload(
            repertoire, batch
        ),
        "font": {
            "path": font_path.relative_to(project).as_posix(),
            "sha256": _sha256(font_path),
            "format": "TrueType quadratic glyf",
        },
        "blank_render_proof": {
            "path": proof_path.relative_to(project).as_posix(),
            "sha256": _sha256(proof_path),
            "format": "PNG",
            "mode": "L",
            "size": [320, 64],
            "sizes_px": list(approval.SMALL_SIZE_PIXELS),
            "expected_ink_pixels": 0,
        },
        "reference_metrics": reference_records,
        "glyphs": [
            {
                "authoring_rank": glyph.authoring_rank,
                "character": glyph.character,
                "codepoint": glyph.codepoint_label,
                "name": glyph.name,
                "gc": glyph.general_category,
                "profile_id": glyph.profile_id,
                "metrics": glyph.metrics,
                "glyph_name": name,
                "resolved_horizontal_advance": resolved_advances[glyph.codepoint],
            }
            for glyph, name in zip(batch.glyphs, glyph_names, strict=True)
        ],
    }
    manifest_path = (
        project
        / "sources/imagegen/semantic/nonhan-0206.semantic.json"
    )
    _write_json(manifest_path, manifest)
    return manifest_path


def test_repertoire_is_exactly_205_visible_plus_one_semantic_batch(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    _project_repertoire(project)
    repertoire = approval.load_frozen_repertoire(project)
    assert len(repertoire.glyphs) == 3060
    assert len(repertoire.batches) == 206
    assert [batch.batch_id for batch in repertoire.batches] == [
        f"nonhan-{number:04d}" for number in range(1, 207)
    ]
    assert {
        batch.batch_kind for batch in repertoire.batches[:205]
    } == {"raster-outline"}
    semantic = repertoire.batches[-1]
    assert semantic.batch_id == "nonhan-0206"
    assert semantic.batch_kind == "semantic-empty"
    assert len(semantic.glyphs) == 17
    assert all(not glyph.outline_required for glyph in semantic.glyphs)


def test_visible_review_and_authorization_pin_every_evidence_class(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report_path = _prepare_visible_batch(project, "nonhan-0001")
    review_path = recorder.record_review(
        project_root=project,
        batch_id="nonhan-0001",
        reviewer_name="Synthetic Reviewer",
        reviewer_role="Glyph QA",
        reviewed_at="2026-07-26T01:00:00Z",
        confirmation=approval.REVIEW_CONFIRMATION,
    )
    review = _read_json(review_path)
    assert len(review["glyphs"]) == 16
    assert {record["decision"] for record in review["glyphs"]} == {"PASS"}
    approval_path = recorder.authorize(
        project_root=project,
        batch_id="nonhan-0001",
        approver_name="Synthetic Approver",
        approved_at="2026-07-26T02:00:00Z",
        confirmation=approval.AUTHORIZATION_CONFIRMATION,
    )
    validated = approval.validate_approval(
        approval_path, project_root=project
    )
    assert validated.batch.batch_id == "nonhan-0001"
    assert validated.visible_evidence is not None
    assert validated.semantic_evidence is None
    payload = _read_json(approval_path)
    assert set(payload["source"]) == {
        "descriptor",
        "raster",
        "copybook",
        "prompt",
        "style_reference",
    }
    report = _read_json(report_path)
    assert payload["vector_build"]["artifacts_sha256"] == report[
        "artifact_sha256"
    ]


def test_review_requires_exact_confirmation_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    _prepare_visible_batch(project, "nonhan-0001")
    kwargs = {
        "project_root": project,
        "batch_id": "nonhan-0001",
        "reviewer_name": "Synthetic Reviewer",
        "reviewer_role": "Glyph QA",
        "reviewed_at": "2026-07-26T01:00:00Z",
    }
    with pytest.raises(
        approval.NonHanApprovalError, match="exact explicit confirmation"
    ):
        recorder.record_review(**kwargs, confirmation="yes")
    path = recorder.record_review(
        **kwargs, confirmation=approval.REVIEW_CONFIRMATION
    )
    before = path.read_bytes()
    with pytest.raises(
        recorder.NonHanApprovalRecorderError, match="refusing to overwrite"
    ):
        recorder.record_review(
            **kwargs, confirmation=approval.REVIEW_CONFIRMATION
        )
    assert path.read_bytes() == before


@pytest.mark.parametrize("tamper", ["prompt", "vector-artifact"])
def test_hash_tamper_is_rejected(
    tmp_path: Path,
    tamper: str,
) -> None:
    project = tmp_path / "project"
    _prepare_visible_batch(project, "nonhan-0001")
    approval_path = _record_and_authorize_visible(project, "nonhan-0001")
    if tamper == "prompt":
        target = project / "sources/imagegen/prompts/nonhan-0001.md"
        target.write_text("tampered prompt\n", encoding="utf-8")
    else:
        target = (
            project
            / "build/imagegen/imagegen-nonhan-0001/svg/u0041.svg"
        )
        target.write_text("<svg><!-- tampered --></svg>\n", encoding="utf-8")
    with pytest.raises(approval.NonHanApprovalError, match="hash|inventory"):
        approval.validate_approval(approval_path, project_root=project)


def test_unknown_approval_key_is_rejected(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    _prepare_visible_batch(project, "nonhan-0001")
    approval_path = _record_and_authorize_visible(project, "nonhan-0001")
    payload = _read_json(approval_path)
    payload["fallback"] = True
    _write_json(approval_path, payload)
    with pytest.raises(approval.NonHanApprovalError, match="wrong keys"):
        approval.validate_approval(approval_path, project_root=project)


def test_duplicate_report_glyph_is_rejected_before_review(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report_path = _prepare_visible_batch(project, "nonhan-0001")
    report = _read_json(report_path)
    report["glyphs"][-1] = dict(report["glyphs"][0])
    _write_json(report_path, report)
    with pytest.raises(
        approval.NonHanApprovalError,
        match="character does not match|duplicate",
    ):
        recorder.record_review(
            project_root=project,
            batch_id="nonhan-0001",
            reviewer_name="Synthetic Reviewer",
            reviewer_role="Glyph QA",
            reviewed_at="2026-07-26T01:00:00Z",
            confirmation=approval.REVIEW_CONFIRMATION,
        )


def test_edge_topology_mismatch_is_rejected_before_review(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report_path = _prepare_visible_batch(project, "nonhan-0195")
    report = _read_json(report_path)
    report["glyphs"][0]["source_component_count"] = 2
    _write_json(report_path, report)
    with pytest.raises(
        approval.NonHanApprovalError,
        match="source-component/vector-outer topology differs",
    ):
        recorder.record_review(
            project_root=project,
            batch_id="nonhan-0195",
            reviewer_name="Synthetic Reviewer",
            reviewer_role="Glyph QA",
            reviewed_at="2026-07-26T01:00:00Z",
            confirmation=approval.REVIEW_CONFIRMATION,
        )


def test_forged_edge_geometry_report_is_recomputed_from_font(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report_path = _prepare_visible_batch(project, "nonhan-0195")
    report = _read_json(report_path)
    forged = report["glyphs"][0]
    forged["source_component_count"] = 2
    forged["outer_contour_count"] = 2
    codepoint = forged["codepoint"].removeprefix("U+").lower()
    glyph_report_path = (
        project
        / f"build/imagegen/imagegen-nonhan-0195/glyph-report/u{codepoint}.json"
    )
    _write_json(glyph_report_path, forged)
    relative = glyph_report_path.relative_to(
        project / "build/imagegen/imagegen-nonhan-0195"
    ).as_posix()
    report["artifact_sha256"][relative] = _sha256(glyph_report_path)
    _write_json(report_path, report)
    with pytest.raises(
        approval.NonHanApprovalError,
        match="actual outer_contour_count differs from report",
    ):
        recorder.record_review(
            project_root=project,
            batch_id="nonhan-0195",
            reviewer_name="Synthetic Reviewer",
            reviewer_role="Glyph QA",
            reviewed_at="2026-07-26T01:00:00Z",
            confirmation=approval.REVIEW_CONFIRMATION,
        )


def test_missing_five_size_proof_is_rejected_before_review(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    report_path = _prepare_visible_batch(project, "nonhan-0001")
    report = _read_json(report_path)
    report["proofs"] = report["proofs"][1:]
    _write_json(report_path, report)
    with pytest.raises(approval.NonHanApprovalError, match="missing five-size"):
        recorder.record_review(
            project_root=project,
            batch_id="nonhan-0001",
            reviewer_name="Synthetic Reviewer",
            reviewer_role="Glyph QA",
            reviewed_at="2026-07-26T01:00:00Z",
            confirmation=approval.REVIEW_CONFIRMATION,
        )


def test_complete_set_rejects_duplicate_and_missing_batches(
    tmp_path: Path,
) -> None:
    approval_dir = tmp_path / "project/sources/imagegen/approvals"
    one = approval_dir / "nonhan-0001.approval.json"
    with pytest.raises(approval.NonHanApprovalError, match="duplicate"):
        approval.validate_complete_approval_set(
            [one, one], project_root=tmp_path / "project"
        )
    with pytest.raises(approval.NonHanApprovalError, match="missing="):
        approval.validate_complete_approval_set(
            [one], project_root=tmp_path / "project"
        )


def test_semantic_batch_pins_empty_font_relations_without_raster(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    _prepare_semantic_batch(project)
    review_path = recorder.record_review(
        project_root=project,
        batch_id="nonhan-0206",
        reviewer_name="Semantic Reviewer",
        reviewer_role="Metrics QA",
        reviewed_at="2026-07-26T03:00:00Z",
        confirmation=approval.SEMANTIC_REVIEW_CONFIRMATION,
    )
    review = _read_json(review_path)
    assert len(review["glyphs"]) == 17
    assert {record["decision"] for record in review["glyphs"]} == {"PASS"}
    approval_path = recorder.authorize(
        project_root=project,
        batch_id="nonhan-0206",
        approver_name="Semantic Approver",
        approved_at="2026-07-26T04:00:00Z",
        confirmation=approval.AUTHORIZATION_CONFIRMATION,
    )
    payload = _read_json(approval_path)
    assert payload["batch_kind"] == "semantic-empty"
    assert "semantic_evidence" in payload
    assert "source" not in payload
    assert "vector_build" not in payload
    assert "raster" not in json.dumps(payload)
    validated = approval.validate_approval(
        approval_path, project_root=project
    )
    assert validated.visible_evidence is None
    assert validated.semantic_evidence is not None


@pytest.mark.parametrize("tamper", ["nonempty-glyf", "inked-proof"])
def test_semantic_empty_evidence_fails_closed(
    tmp_path: Path,
    tamper: str,
) -> None:
    project = tmp_path / "project"
    manifest_path = _prepare_semantic_batch(project)
    manifest = _read_json(manifest_path)
    if tamper == "nonempty-glyf":
        font_path = project / manifest["font"]["path"]
        font = TTFont(font_path)
        try:
            name = manifest["glyphs"][0]["glyph_name"]
            font["glyf"][name] = _rectangle_glyph((0, 0, 100, 100))
            font.save(font_path)
        finally:
            font.close()
        manifest["font"]["sha256"] = _sha256(font_path)
        expected_error = "semantic glyf must be exactly empty"
    else:
        proof_path = project / manifest["blank_render_proof"]["path"]
        image = Image.open(proof_path)
        try:
            image.putpixel((0, 0), 0)
            image.save(proof_path, optimize=False)
        finally:
            image.close()
        manifest["blank_render_proof"]["sha256"] = _sha256(proof_path)
        expected_error = "contains non-background pixels"
    _write_json(manifest_path, manifest)
    repertoire = approval.load_frozen_repertoire(project)
    with pytest.raises(approval.NonHanApprovalError, match=expected_error):
        approval.semantic_evidence(
            project_root=project,
            repertoire=repertoire,
            batch=repertoire.batches[-1],
        )
