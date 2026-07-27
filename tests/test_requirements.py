from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.requirements import (
    INPUT_PATHS,
    POLICY,
    load_requirements,
    read_codepoint_list,
    read_han_character_list,
    sha256,
    validate,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "inventories/font_requirements.json"


def test_requirement_snapshot_is_independent_and_complete() -> None:
    payload = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    assert validate(REQUIREMENTS) == payload
    codepoints, categories, outline_required = load_requirements(REQUIREMENTS)
    dictionary_text = read_codepoint_list(
        ROOT / "inventories/dictionary_required_codepoints.txt"
    )

    assert payload["schema_version"] == 1
    assert payload["policy"] == POLICY
    assert len(codepoints) == payload["counts"]["all_required"] == 18_071
    assert sum(outline_required.values()) == 18_054
    assert outline_required[0x034F] is False
    assert len(dictionary_text) == 12_306
    assert dictionary_text <= codepoints
    assert sum("dictionary_han" in values for values in categories.values()) == 11_958
    assert sum("taiwan_big5" in values for values in categories.values()) == 13_058


def test_requirement_input_hashes_match_current_sources() -> None:
    payload = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    inputs = payload["inputs"]
    assert set(inputs) == set(INPUT_PATHS)
    for identifier, expected in INPUT_PATHS.items():
        item = inputs[identifier]
        path = Path(item["path"])
        assert path == expected
        assert not path.is_absolute()
        path = ROOT / path
        assert path.is_file()
        assert sha256(path) == item["sha256"]


@pytest.mark.parametrize(
    "content",
    ("", "臺\n\n灣\n", "臺灣\n", "臺\n臺\n", "臺\n灣\n", "A\n"),
)
def test_han_character_list_rejects_noncanonical_input(tmp_path: Path, content: str) -> None:
    path = tmp_path / "han.txt"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        read_han_character_list(path)


def test_han_character_list_accepts_ordered_supplementary_scalars(tmp_path: Path) -> None:
    path = tmp_path / "han.txt"
    path.write_text("臺\n𠀀\n" , encoding="utf-8")
    assert read_han_character_list(path) == {0x81FA, 0x20000}
