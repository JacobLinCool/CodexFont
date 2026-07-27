from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from scripts.materialize_imagegen_vertical_batches import (
    CAPACITY,
    COPYBOOK_SIZE,
    IMAGEGEN,
    REPERTOIRE_ID,
    STYLE_REFERENCE,
    VERTICAL_REPERTOIRE,
    VerticalMaterializationError,
    _alternate_records,
    _sha256,
    build_repertoire,
    register,
)


def test_vertical_repertoire_is_exact_and_stable() -> None:
    records = _alternate_records()
    assert len(records) == 93
    assert len({row["base_codepoint"] for row in records}) == 93
    assert sum(row["vertical_orientation"] in {"Tu", "Tr"} for row in records) == 83
    assert sum(row["vertical_orientation"] == "Tailored" for row in records) == 10
    assert [row["rank"] for row in records] == list(range(1, 94))
    assert all(row["glyph_name"].endswith(".vert") for row in records)

    path = build_repertoire()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["repertoire_id"] == REPERTOIRE_ID
    assert payload["total"] == 93
    assert len(payload["alternates"]) == 93
    assert len(payload["batches"]) == 6
    assert sum(batch["empty_grid_cells"] for batch in payload["batches"]) == 3
    assert all(
        batch["end_rank"] - batch["start_rank"] + 1
        + batch["empty_grid_cells"]
        == CAPACITY
        for batch in payload["batches"]
    )


def test_materialized_vertical_copybooks_are_black_ink_on_white() -> None:
    payload = json.loads(VERTICAL_REPERTOIRE.read_text(encoding="utf-8"))
    for batch in payload["batches"]:
        path = IMAGEGEN / "copybooks" / f"{batch['batch_id']}.png"
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.mode == "L"
            assert image.size == (COPYBOOK_SIZE, COPYBOOK_SIZE)
            assert not image.text
            cell = COPYBOOK_SIZE // 4
            occupied = batch["end_rank"] - batch["start_rank"] + 1
            for index in range(CAPACITY):
                row, column = divmod(index, 4)
                crop = image.crop(
                    (
                        column * cell + 20,
                        row * cell + 20,
                        (column + 1) * cell - 20,
                        (row + 1) * cell - 20,
                    )
                )
                if index < occupied:
                    lo, hi = crop.getextrema()
                    assert lo == 0
                    assert hi == 255
                    # A polarity regression creates a large black rectangle.
                    black = sum(value < 32 for value in crop.getdata())
                    assert black < crop.width * crop.height // 4
                else:
                    assert crop.getextrema() == (255, 255)


def test_vertical_drafts_pin_copybooks_style_and_repertoire() -> None:
    payload = json.loads(VERTICAL_REPERTOIRE.read_text(encoding="utf-8"))
    assert payload["total"] == 93
    for batch in payload["batches"]:
        batch_id = batch["batch_id"]
        draft_path = IMAGEGEN / "batches" / f"{batch_id}.draft.json"
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        assert draft["source_type"] == "imagegen-vertical-alternate"
        assert draft["batch_id"] == f"imagegen-{batch_id}"
        assert draft["state"] == "awaiting-generation"
        assert draft["generator"] == "built-in-image_gen"
        assert draft["grid"]["rows"] == draft["grid"]["columns"] == 4
        assert draft["grid"]["empty_grid_cells"] == batch["empty_grid_cells"]
        assert draft["repertoire"]["sha256"] == _sha256(VERTICAL_REPERTOIRE)
        assert draft["copybook"]["sha256"] == _sha256(
            IMAGEGEN / "copybooks" / f"{batch_id}.png"
        )
        assert draft["style_reference"]["sha256"] == _sha256(STYLE_REFERENCE)
        assert all(
            item["copybook_reference"]["role"]
            == "identity-reference-only-no-outline-import"
            for item in draft["grid"]["alternates"]
        )


def test_vertical_prompts_require_original_unencoded_alternates() -> None:
    payload = json.loads(VERTICAL_REPERTOIRE.read_text(encoding="utf-8"))
    for batch in payload["batches"]:
        batch_id = batch["batch_id"]
        prompt = (IMAGEGEN / "prompts" / f"{batch_id}.md").read_text(
            encoding="utf-8"
        )
        assert "## Exact tool prompt" in prompt
        assert "STYLE ONLY" in prompt
        assert "IDENTITY REFERENCE ONLY" in prompt
        assert "not mechanically rotated copies" in prompt
        assert "Never trace or import its printed outlines" in prompt
        assert "must use the TOP/BOTTOM vertical form" in prompt
        assert "`〈` must become `∧` and `〉` must become `∨`" in prompt
        assert "Never retain a sideways" in prompt
        for codepoint in batch["base_codepoints"]:
            assert f"`{codepoint}`" in prompt
    quotation_prompt = (
        IMAGEGEN / "prompts" / "vertical-0003.md"
    ).read_text(encoding="utf-8")
    assert quotation_prompt.count("exactly two short quote strokes total") == 3
    assert "do not add a third stroke" in quotation_prompt
    first_prompt = (
        IMAGEGEN / "prompts" / "vertical-0001.md"
    ).read_text(encoding="utf-8")
    assert "one straight vertical half-line only" in first_prompt
    second_prompt = (
        IMAGEGEN / "prompts" / "vertical-0002.md"
    ).read_text(encoding="utf-8")
    assert "draw a `┐` silhouette" in second_prompt
    assert "draw a `└` silhouette" in second_prompt
    assert "draw two nested `┐` strokes only" in second_prompt
    assert "draw two nested `└` strokes only" in second_prompt
    assert "top trapezoid bracket opening downward" in second_prompt
    assert "bottom trapezoid bracket opening upward" in second_prompt
    assert "outlined top tortoise-shell form opening downward" in second_prompt
    assert "outlined bottom tortoise-shell form opening upward" in second_prompt
    fifth_prompt = (
        IMAGEGEN / "prompts" / "vertical-0005.md"
    ).read_text(encoding="utf-8")
    assert "straight vertical line for the vertical prolonged-sound" in fifth_prompt
    assert "keep Bopomofo I as one straight horizontal line" in fifth_prompt
    assert "one slender vertical wavy rule" in fifth_prompt
    assert "top parenthesis arc opening downward" in fifth_prompt
    assert "bottom parenthesis arc opening upward" in fifth_prompt
    sixth_prompt = (
        IMAGEGEN / "prompts" / "vertical-0006.md"
    ).read_text(encoding="utf-8")
    assert "two round dots aligned horizontally" in sixth_prompt
    assert "comma-like mark on the left and the round dot on the right" in sixth_prompt
    assert "Cell 01 must be `•  •` from left to right" in sixth_prompt
    assert "Never arrange either cell as a top/bottom vertical stack" in sixth_prompt
    assert "three-sided top square bracket" in sixth_prompt
    assert "three-sided bottom square bracket" in sixth_prompt
    assert "one vertical S-shaped tilde" in sixth_prompt
    assert "outlined top white-parenthesis" in sixth_prompt
    assert "outlined bottom white-parenthesis" in sixth_prompt


def test_register_pins_raster_and_refuses_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imagegen = tmp_path / "sources/imagegen"
    for relative in ("batches", "raster"):
        (imagegen / relative).mkdir(parents=True, exist_ok=True)
    batch_id = "vertical-0001"
    shutil.copy2(
        IMAGEGEN / "batches" / f"{batch_id}.draft.json",
        imagegen / "batches" / f"{batch_id}.draft.json",
    )
    raster = imagegen / "raster" / f"{batch_id}.png"
    Image.new("RGB", (1024, 1024), "white").save(raster)
    monkeypatch.setattr(
        "scripts.materialize_imagegen_vertical_batches.IMAGEGEN",
        imagegen,
    )

    output = register(batch_id, "call_test_vertical_0001")
    source = json.loads(output.read_text(encoding="utf-8"))
    assert source["state"] == "generated-unreviewed"
    assert source["generator_call"] == "call_test_vertical_0001"
    assert source["raster_sha256"] == _sha256(raster)

    with pytest.raises(
        VerticalMaterializationError,
        match="refusing to overwrite",
    ):
        register(batch_id, "call_test_vertical_0001_again")
