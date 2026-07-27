from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont
from PIL import Image

from scripts.identity_reference_catalog import _outline_recording
from scripts.materialize_imagegen_nonhan_batches import (
    BATCH_COUNT,
    BATCH_ROOT,
    COPYBOOK_ROOT,
    COPYBOOK_SIDE,
    GRID_CAPACITY,
    IMAGEGEN_ROOT,
    PROMPT_ROOT,
    RASTER_ROOT,
    REPERTOIRE,
    ROOT,
    SEMANTIC_EMPTY_COUNT,
    STYLE_REFERENCE,
    VISIBLE_GLYPH_COUNT,
    MaterializationError,
    load_repertoire,
    prompt_for,
    register,
    sha256,
)

# These eight arrows deliberately replace ambiguous Unicode names with exact
# stroke topology while retaining the codepoint and pinned identity copybook.
EXPLICIT_IDENTITY_DESCRIPTION_OVERRIDES = {
    ("nonhan-0134", index)
    for index in (1, 2, 3, 4, 13, 14, 15, 16)
}


def _manifest_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def test_frozen_repertoire_is_exactly_205_visible_batches() -> None:
    payload, batches = load_repertoire(REPERTOIRE)
    glyphs = [glyph for batch in batches for glyph in batch.glyphs]
    assert len(batches) == BATCH_COUNT == 205
    assert [batch.batch_id for batch in batches] == [
        f"nonhan-{index:04d}" for index in range(1, BATCH_COUNT + 1)
    ]
    assert len(glyphs) == len({glyph.codepoint for glyph in glyphs})
    assert len(glyphs) == VISIBLE_GLYPH_COUNT == 3043
    assert sum(batch.empty_grid_cells for batch in batches) == 237
    assert payload["counts"]["total"] == (
        VISIBLE_GLYPH_COUNT + SEMANTIC_EMPTY_COUNT
    )
    assert payload["counts"]["total_batches"] == BATCH_COUNT + 1
    assert all(batch.profile_ids for batch in batches)
    assert all(
        len(batch.glyphs) + batch.empty_grid_cells == GRID_CAPACITY
        for batch in batches
    )


def test_materialized_artifact_sets_are_complete_and_drafts_are_unregistered() -> None:
    _payload, batches = load_repertoire(REPERTOIRE)
    expected_ids = {batch.batch_id for batch in batches}
    assert {
        path.name.removesuffix(".draft.json")
        for path in BATCH_ROOT.glob("nonhan-*.draft.json")
    } == expected_ids
    assert {
        path.stem for path in COPYBOOK_ROOT.glob("nonhan-*.png")
    } == expected_ids
    assert {
        path.stem for path in PROMPT_ROOT.glob("nonhan-*.md")
    } == expected_ids

    seen: set[int] = set()
    for batch in batches:
        draft_path = BATCH_ROOT / f"{batch.batch_id}.draft.json"
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        assert draft["schema_version"] == 2
        assert draft["batch_id"] == f"imagegen-{batch.batch_id}"
        assert draft["state"] == "awaiting-generation"
        assert draft["generator"] == "built-in-image_gen"
        assert draft["generator_call"] is None
        assert draft["raster"] == f"../raster/{batch.batch_id}.png"
        assert draft["raster_sha256"] is None
        assert draft["prompt"] == f"../prompts/{batch.batch_id}.md"
        assert draft["review"] == {
            "identity": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        }
        assert draft["grid"]["rows"] == draft["grid"]["columns"] == 4
        assert draft["grid"]["empty_grid_cells"] == batch.empty_grid_cells
        records = draft["grid"]["glyphs"]
        assert len(records) == len(batch.glyphs)
        for repertoire_glyph, record in zip(batch.glyphs, records, strict=True):
            for key, value in repertoire_glyph.record.items():
                assert record[key] == value
            assert int(record["codepoint"][2:], 16) == ord(record["character"])
            seen.add(ord(record["character"]))
            reference = record["copybook_reference"]
            assert reference["role"] == (
                "identity-reference-only-no-outline-import"
            )
            assert set(reference["validation"]) == {
                "exact-cmap-hit",
                "non-notdef-glyph-name",
                "non-empty-distinct-outline",
                "non-empty-pillow-raster",
            }
            assert reference["glyph_name"] not in {
                ".notdef",
                ".null",
                "nonmarkingreturn",
            }
            assert "sources/authored" not in reference["font_path"]
            assert sha256(_manifest_path(reference["font_path"])) == reference[
                "font_sha256"
            ]
        assert draft["copybook"] == {
            "path": f"../copybooks/{batch.batch_id}.png",
            "sha256": sha256(COPYBOOK_ROOT / f"{batch.batch_id}.png"),
            "role": "identity-reference-only-no-outline-import",
        }
        assert draft["style_reference"] == {
            "path": "../raster/common-0001.png",
            "sha256": sha256(STYLE_REFERENCE),
            "role": "style-only",
        }
        assert draft["repertoire"]["sha256"] == sha256(REPERTOIRE)
        assert draft["repertoire"]["batch_id"] == batch.batch_id
    assert len(seen) == VISIBLE_GLYPH_COUNT


def test_copybooks_are_unlabeled_four_by_four_identity_references() -> None:
    _payload, batches = load_repertoire(REPERTOIRE)
    for batch in batches:
        path = COPYBOOK_ROOT / f"{batch.batch_id}.png"
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (COPYBOOK_SIDE, COPYBOOK_SIDE)
            assert image.mode == "L"
            assert not image.text
            cell_side = COPYBOOK_SIDE // 4
            for index in range(GRID_CAPACITY):
                row, column = divmod(index, 4)
                crop = image.crop(
                    (
                        column * cell_side + 8,
                        row * cell_side + 8,
                        (column + 1) * cell_side - 8,
                        (row + 1) * cell_side - 8,
                    )
                )
                if index < len(batch.glyphs):
                    assert crop.getextrema()[0] == 0
                else:
                    assert crop.getextrema() == (255, 255)


def test_every_copybook_reference_is_an_exact_non_tofu_cmap_glyph() -> None:
    face_cache: dict[tuple[Path, int], TTFont] = {}
    try:
        for draft_path in sorted(BATCH_ROOT.glob("nonhan-*.draft.json")):
            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            for record in draft["grid"]["glyphs"]:
                codepoint = int(record["codepoint"][2:], 16)
                reference = record["copybook_reference"]
                path = _manifest_path(reference["font_path"]).resolve()
                key = (path, int(reference["font_index"]))
                if key not in face_cache:
                    face_cache[key] = TTFont(
                        path, fontNumber=key[1], lazy=True
                    )
                font = face_cache[key]
                cmap = font.getBestCmap()
                assert cmap is not None
                glyph_name = reference["glyph_name"]
                assert cmap.get(codepoint) == glyph_name
                recording = _outline_recording(font, glyph_name)
                assert recording
                if ".notdef" in font.getGlyphOrder():
                    assert recording != _outline_recording(font, ".notdef")
    finally:
        for font in face_cache.values():
            font.close()


def test_prompts_pin_both_reference_roles_and_forbid_reference_labels() -> None:
    _payload, batches = load_repertoire(REPERTOIRE)
    for batch in batches:
        prompt = (PROMPT_ROOT / f"{batch.batch_id}.md").read_text(encoding="utf-8")
        normalized = " ".join(prompt.split())
        assert "## Exact tool prompt" in prompt
        assert "Generator call: `<PENDING: filled only by register>`" in prompt
        assert "Raster SHA-256: `<PENDING: filled only by register>`" in prompt
        assert "STYLE ONLY" in prompt
        assert "IDENTITY\n   REFERENCE ONLY" in prompt
        assert (
            "Do not trace, reproduce, or import its printed outlines"
            in normalized
        )
        assert "Do not include any U+XXXX label" in prompt
        assert f"Design group: `{batch.design_group}`" in prompt
        assert (
            f"Metric/design profiles: `{', '.join(batch.profile_ids)}`"
            in prompt
        )
        for index, glyph in enumerate(batch.glyphs, start=1):
            canonical_identity = (
                f"Cell {index:02d}: `{glyph.codepoint_label}` "
                f"{glyph.unicode_name}"
            )
            if (
                batch.batch_id,
                index,
            ) in EXPLICIT_IDENTITY_DESCRIPTION_OVERRIDES:
                assert (
                    f"Cell {index:02d}: `{glyph.codepoint_label}` — "
                    "use Image 2 for identity —"
                ) in prompt
            else:
                assert canonical_identity in prompt
        if "box-drawing" in batch.profile_ids:
            assert "separator" in normalized
        if "block-element" in batch.profile_ids:
            assert "boundary" in normalized
            assert "separator" in normalized


def test_canonical_edge_prompts_separate_authored_topology_from_metrics() -> None:
    _payload, batches = load_repertoire(REPERTOIRE)
    by_id = {batch.batch_id: batch for batch in batches}
    for batch_id in ("nonhan-0202", "nonhan-0203"):
        batch = by_id[batch_id]
        copybook = COPYBOOK_ROOT / f"{batch_id}.png"
        prompt = prompt_for(
            batch,
            repertoire_path=REPERTOIRE,
            repertoire_sha256=sha256(REPERTOIRE),
            copybook_path=copybook,
            copybook_sha256=sha256(copybook),
            style_sha256=sha256(STYLE_REFERENCE),
        )
        normalized = " ".join(prompt.split())
        assert "Keep all black source ink well away from separators" in normalized
        assert "standard vector metric normalization" in normalized
        assert "generated raster must supply the original topology" in normalized
    prompt_0202 = prompt_for(
        by_id["nonhan-0202"],
        repertoire_path=REPERTOIRE,
        repertoire_sha256=sha256(REPERTOIRE),
        copybook_path=COPYBOOK_ROOT / "nonhan-0202.png",
        copybook_sha256=sha256(COPYBOOK_ROOT / "nonhan-0202.png"),
        style_sha256=sha256(STYLE_REFERENCE),
    )
    normalized_0202 = " ".join(prompt_0202.split())
    assert "absolute raster bounding box is segmentation and layout evidence" in (
        normalized_0202
    )
    assert "not Unicode identity and not a release metric" in normalized_0202
    assert "`_edge_target_bounds`" in prompt_0202


def test_register_atomically_pins_raster_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    batch_id = "nonhan-0001"
    imagegen_root = tmp_path / "sources/imagegen"
    for relative in ("batches", "copybooks", "prompts", "raster", "repertoires"):
        (imagegen_root / relative).mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPERTOIRE, imagegen_root / "repertoires/nonhan-3060.json")
    shutil.copy2(
        BATCH_ROOT / f"{batch_id}.draft.json",
        imagegen_root / f"batches/{batch_id}.draft.json",
    )
    shutil.copy2(
        COPYBOOK_ROOT / f"{batch_id}.png",
        imagegen_root / f"copybooks/{batch_id}.png",
    )
    shutil.copy2(
        PROMPT_ROOT / f"{batch_id}.md",
        imagegen_root / f"prompts/{batch_id}.md",
    )
    shutil.copy2(STYLE_REFERENCE, imagegen_root / "raster/common-0001.png")
    raster = imagegen_root / f"raster/{batch_id}.png"
    Image.new("RGB", (1024, 1024), "white").save(raster)

    output = register(
        batch_id=batch_id,
        generator_call="call_test_nonhan_0001",
        imagegen_root=imagegen_root,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["state"] == "generated-unreviewed"
    assert payload["generator_call"] == "call_test_nonhan_0001"
    assert payload["raster_sha256"] == sha256(raster)
    assert set(payload["review"].values()) == {"pending"}

    with pytest.raises(MaterializationError, match="refusing to overwrite"):
        register(
            batch_id=batch_id,
            generator_call="call_different",
            imagegen_root=imagegen_root,
        )


def test_register_rejects_noncanonical_raster_path(tmp_path: Path) -> None:
    wrong = tmp_path / "nonhan-0001.png"
    Image.new("RGB", (1024, 1024), "white").save(wrong)
    with pytest.raises(MaterializationError, match="raster must be exactly"):
        register(
            batch_id="nonhan-0001",
            generator_call="call_test",
            raster=wrong,
            imagegen_root=IMAGEGEN_ROOT,
        )
