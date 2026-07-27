from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil

from fontTools.ttLib import TTFont
import numpy as np
from PIL import Image
import pytest

from scripts import imagegen_vertical_pipeline as pipeline


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_edge_proof_uses_preview_font(
    directory: Path,
    report: dict[str, object],
) -> None:
    font = report["font"]
    glyphs = report["glyphs"]
    assert isinstance(font, dict)
    assert isinstance(glyphs, list)
    face = pipeline.nonhan.freetype.Face(str(directory / font["ttf"]))
    em_pixels = 128
    face.set_pixel_sizes(0, em_pixels)
    flags = (
        pipeline.nonhan.freetype.FT_LOAD_RENDER
        | pipeline.nonhan.freetype.FT_LOAD_NO_HINTING
        | pipeline.nonhan.freetype.FT_LOAD_TARGET_NORMAL
    )
    proof = np.asarray(
        Image.open(directory / "proof/edge-connect.png").convert("RGB")
    )
    for glyph in glyphs:
        assert isinstance(glyph, dict)
        face.load_char(str(glyph["character"]), flags)
        bitmap = face.glyph.bitmap
        alpha = np.asarray(bitmap.buffer, dtype=np.uint8).reshape(
            bitmap.rows,
            bitmap.pitch,
        )[:, : bitmap.width]
        expected = np.full((em_pixels, em_pixels), 255, dtype=np.uint8)
        glyph_left = int(face.glyph.bitmap_left)
        glyph_top = em_pixels - int(face.glyph.bitmap_top)
        paste_left = max(glyph_left, 0)
        paste_top = max(glyph_top, 0)
        paste_right = min(glyph_left + bitmap.width, em_pixels)
        paste_bottom = min(glyph_top + bitmap.rows, em_pixels)
        assert paste_left < paste_right and paste_top < paste_bottom
        expected[
            paste_top:paste_bottom,
            paste_left:paste_right,
        ] = 255 - alpha[
            paste_top - glyph_top : paste_bottom - glyph_top,
            paste_left - glyph_left : paste_right - glyph_left,
        ]
        cell_left = int(glyph["column"]) * 144 + 8
        cell_top = int(glyph["row"]) * 144 + 8
        actual = proof[
            cell_top : cell_top + em_pixels,
            cell_left : cell_left + em_pixels,
        ]
        assert all(
            np.array_equal(actual[:, :, channel], expected)
            for channel in range(3)
        )


def test_all_six_vertical_descriptors_cover_exactly_93_alternates() -> None:
    descriptors = [
        pipeline.load_source_descriptor(
            pipeline.IMAGEGEN_ROOT
            / f"batches/vertical-{number:04d}.source.json"
        )
        for number in range(1, 7)
    ]
    assert [len(item.glyphs) for item in descriptors] == [16, 16, 16, 16, 16, 13]
    assert sum(len(item.glyphs) for item in descriptors) == 93
    assert sum(item.empty_grid_cells for item in descriptors) == 3
    names = [
        alternate["glyph_name"]
        for descriptor in descriptors
        for alternate in descriptor.alternates
    ]
    codepoints = [
        glyph.codepoint
        for descriptor in descriptors
        for glyph in descriptor.glyphs
    ]
    assert len(names) == len(set(names)) == 93
    assert len(codepoints) == len(set(codepoints)) == 93
    assert all(name.endswith(".vert") for name in names)
    assert all(len(item.cell_slots) == pipeline.CAPACITY for item in descriptors)


def test_vertical_descriptor_rejects_raster_hash_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        pipeline.IMAGEGEN_ROOT / "batches/vertical-0001.source.json"
    ).resolve()
    actual_read = pipeline._read_object

    def drifted_read(path: Path) -> dict[str, object]:
        value = actual_read(path)
        if path.resolve() == source:
            value = copy.deepcopy(value)
            value["raster_sha256"] = "0" * 64
        return value

    monkeypatch.setattr(pipeline, "_read_object", drifted_read)
    with pytest.raises(pipeline.VerticalPipelineError, match="raster hash mismatch"):
        pipeline.load_source_descriptor(source)


def test_vertical_descriptor_rejects_repertoire_identity_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repertoire = pipeline.VERTICAL_REPERTOIRE.resolve()
    actual_read = pipeline._read_object

    def drifted_read(path: Path) -> dict[str, object]:
        value = actual_read(path)
        if path.resolve() == repertoire:
            value = copy.deepcopy(value)
            value["total"] = 92
        return value

    monkeypatch.setattr(pipeline, "_read_object", drifted_read)
    with pytest.raises(
        pipeline.VerticalPipelineError,
        match="repertoire identity changed",
    ):
        pipeline.load_source_descriptor(
            pipeline.IMAGEGEN_ROOT
            / "batches/vertical-0001.source.json"
        )


@pytest.mark.parametrize(
    ("tamper", "message"),
    (
        ("sequence", "sequence hash changed"),
        ("batch-slice", "batch vertical-0001 slice changed"),
        ("missing-alternate", "cardinality changed"),
        ("extra-alternate", "cardinality changed"),
    ),
)
def test_vertical_repertoire_validator_fails_closed(
    tamper: str,
    message: str,
) -> None:
    repertoire = pipeline._read_object(pipeline.VERTICAL_REPERTOIRE)
    value = copy.deepcopy(repertoire)
    if tamper == "sequence":
        value["sequence_sha256"] = "0" * 64
    elif tamper == "batch-slice":
        value["batches"][0]["base_codepoints"][0] = "U+FFFF"
    elif tamper == "missing-alternate":
        value["alternates"].pop()
    else:
        value["alternates"].append(copy.deepcopy(value["alternates"][-1]))
    with pytest.raises(pipeline.VerticalPipelineError, match=message):
        pipeline._validate_repertoire_payload(
            value,
            where="synthetic vertical repertoire",
        )


def test_vertical_batch_with_trailing_blanks_is_reproducible(
    tmp_path: Path,
) -> None:
    source = (
        pipeline.IMAGEGEN_ROOT / "batches/vertical-0006.source.json"
    )
    potrace = shutil.which("potrace")
    assert potrace is not None
    first = pipeline.build_batch(
        source,
        output_root=tmp_path / "first",
        potrace_executable=potrace,
    )
    second = pipeline.build_batch(
        source,
        output_root=tmp_path / "second",
        potrace_executable=potrace,
    )
    first_report = json.loads(
        (first / "report.json").read_text(encoding="utf-8")
    )
    second_report = json.loads(
        (second / "report.json").read_text(encoding="utf-8")
    )
    assert first_report == second_report
    assert first_report["pipeline"] == pipeline.PIPELINE_ID
    assert first_report["batch_id"] == "imagegen-vertical-0006"
    assert first_report["approval_state"] == "unreviewed"
    assert first_report["grid"]["empty_grid_cells"] == 3
    assert first_report["grid"]["cell_slots"][-3:] == [None, None, None]
    assert len(first_report["glyphs"]) == 13
    assert first_report["font"]["release_alternates_are_unencoded"] is True
    assert first_report["vectorization"] == {
        "tool": first_report["vectorization"]["tool"],
        "outline_format": "TrueType quadratic glyf",
        "cu2qu_max_error": 2.0,
        "grid_rules_removed_by_detected_rule_spans": True,
        "grid_rule_interior_padding_px": 2,
        "proof_coverage_divisor": 10,
        "minimum_proof_coverage_pixels": 2,
        "preview_transform": "fullwidth",
        "release_metrics": (
            "base-advances-with-approved-preview-placement"
        ),
    }
    assert {
        (record["size_px"], record["polarity"])
        for record in first_report["proofs"]
        if record["kind"] == "small-size"
    } == {
        (size, polarity)
        for size in pipeline.nonhan.SMALL_SIZE_PIXELS
        for polarity in ("black-on-white", "white-on-black")
    }
    for glyph in first_report["glyphs"]:
        assert glyph["unencoded_glyph_name"].endswith(".vert")
        assert glyph["glyph_name"] == glyph["unencoded_glyph_name"]
        assert glyph["micro_edge_count"] == 0
        assert glyph["acute_micro_turn_count"] == 0
        assert glyph["micro_thorn_points_removed"] == 0
        assert set(glyph["coverage_pixels"]) == {
            str(size) for size in pipeline.nonhan.SMALL_SIZE_PIXELS
        }

    for relative, digest in first_report["artifact_sha256"].items():
        artifact = first / relative
        assert artifact.is_file()
        assert _sha256(artifact) == digest

    _assert_edge_proof_uses_preview_font(first, first_report)

    font = TTFont(
        first / first_report["font"]["ttf"],
        lazy=False,
        checkChecksums=2,
    )
    try:
        assert font.getBestCmap() == {
            int(codepoint[2:], 16): glyph_name
            for codepoint, glyph_name in zip(
                first_report["base_codepoints"],
                first_report["unencoded_glyph_names"],
                strict=True,
            )
        }
        assert font.getGlyphOrder() == [
            ".notdef",
            *first_report["unencoded_glyph_names"],
        ]
        assert "vhea" in font and "vmtx" in font
        for glyph_name in first_report["unencoded_glyph_names"]:
            glyph = font["glyf"][glyph_name]
            assert not glyph.isComposite()
            assert glyph.numberOfContours > 0
    finally:
        font.close()
