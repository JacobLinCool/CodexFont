from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import han_delta_repertoire as delta


ROOT = Path(__file__).resolve().parents[1]
REPERTOIRE = (
    ROOT
    / "sources/imagegen/repertoires/"
    "dictionary-salience-extension-1216.json"
)
EXISTING_REPERTOIRES = (
    ROOT / "sources/imagegen/repertoires/common-3000.json",
    ROOT
    / "sources/imagegen/repertoires/"
    "moe-common-extension-1844.json",
    ROOT / "sources/imagegen/repertoires/nonhan-3060.json",
)


def _existing_codepoints() -> set[int]:
    result: set[int] = set()
    for path in EXISTING_REPERTOIRES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload.get("characters", []):
            result.add(int(record["codepoint"]))
        for record in payload.get("glyphs", []):
            result.add(
                int(record["codepoint"].removeprefix("U+"), 16)
            )
    return result


def test_frozen_clear_hand_delta_is_exact_and_disjoint() -> None:
    repertoire = delta.load_repertoire(
        REPERTOIRE,
        project_root=ROOT,
    )
    codepoints = {ord(character) for character in repertoire.characters}
    existing = _existing_codepoints()

    assert repertoire.family_id == "clear-hand-tc"
    assert (
        repertoire.repertoire_id
        == "clear-hand-tc-dictionary-salience-extension-1216-v1"
    )
    assert repertoire.batch_prefix == "dict-han"
    assert len(repertoire.characters) == 1216
    assert len(repertoire.batches) == 76
    assert all(
        len(batch.characters) == 16
        and batch.empty_grid_cells == 0
        for batch in repertoire.batches
    )
    assert codepoints.isdisjoint(existing)
    assert len(existing) == 7904
    assert len(existing | codepoints) == 9120
    assert (
        repertoire.sequence_sha256
        == "3b28f33b80e7675ccdba24d0e678b305"
        "81f4eb55fd7418ab1447f10a889267d7"
    )
    assert (
        repertoire.payload["provenance"]["codepoint_lines_sha256"]
        == "0e9a74e906fcd637f9de06056dd867ead"
        "9e72e39085d2e3d9ef5235392483e98"
    )
    assert repertoire.batches[0].batch_id == "dict-han-0001"
    assert repertoire.batches[-1].batch_id == "dict-han-0076"


def test_builder_reproduces_frozen_payload_exactly() -> None:
    frozen = json.loads(REPERTOIRE.read_text(encoding="utf-8"))
    rebuilt = delta.build_dictionary_salience_delta_payload(
        project_root=ROOT,
        family_id="clear-hand-tc",
        repertoire_id=(
            "clear-hand-tc-dictionary-salience-extension-1216-v1"
        ),
        batch_prefix="dict-han",
        total_count=1216,
        inventory_relative=Path("inventories/han_characters.csv"),
        requirements_relative=Path(
            "inventories/font_requirements.json"
        ),
        excluded_repertoire_relatives=(
            Path(
                "sources/imagegen/repertoires/common-3000.json"
            ),
            Path(
                "sources/imagegen/repertoires/"
                "moe-common-extension-1844.json"
            ),
            Path(
                "sources/imagegen/repertoires/nonhan-3060.json"
            ),
        ),
        authority_source="教育部重編國語辭典修訂本 2015",
        authority_jurisdiction="Taiwan",
        authority_role=(
            "Clear Hand TC dictionary-salience coverage extension"
        ),
    )
    assert rebuilt == frozen


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["characters"][0].update(
            {"character": "一"}
        ),
        lambda value: value["batches"][0].update(
            {"characters": value["batches"][0]["characters"][::-1]}
        ),
        lambda value: value["provenance"].update(
            {"sequence_sha256": "0" * 64}
        ),
        lambda value: value["selection"].update(
            {"ordering": ["codepoint ASC"]}
        ),
    ],
)
def test_validator_rejects_repertoire_drift(mutate) -> None:
    payload = json.loads(REPERTOIRE.read_text(encoding="utf-8"))
    tampered = deepcopy(payload)
    mutate(tampered)
    with pytest.raises(
        delta.HanDeltaRepertoireError,
        match="does not equal the recomputed",
    ):
        delta.validate_payload(tampered, project_root=ROOT)
