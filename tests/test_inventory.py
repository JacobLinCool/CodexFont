from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path

from scripts.inventory import make_records, read_verified_codepoints


ROOT = Path(__file__).resolve().parents[1]


def records() -> list[dict[str, str]]:
    with (ROOT / "inventories/han_characters.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_inventory_counts_and_planes() -> None:
    rows = records()
    assert len(rows) == 11_958
    assert sum(int(row["occurrence_count"]) for row in rows) == 5_268_037
    assert sum(int(row["codepoint"][2:], 16) > 0xFFFF for row in rows) == 327
    assert sum(
        0xF0000 <= int(row["codepoint"][2:], 16) <= 0xFFFFD
        for row in rows
    ) == 111
    assert len({row["codepoint"] for row in rows}) == len(rows)


def release_codepoints() -> set[int]:
    return read_verified_codepoints(
        ROOT / "dist/clear-hand-tc/report.json"
    )


def test_han_inventory_status_is_the_pinned_pre_delta_baseline() -> None:
    rows = records()
    verified = release_codepoints()
    inventory_codepoints = {int(row["codepoint"][2:], 16) for row in rows}
    release_han = verified & inventory_codepoints
    baseline_designed = {
        int(row["codepoint"][2:], 16)
        for row in rows
        if row["glyph_designed"] == "True"
    }
    baseline_checked = {
        int(row["codepoint"][2:], 16)
        for row in rows
        if row["quality_checked"] == "True"
    }
    repertoire_path = (
        ROOT
        / "sources/imagegen/repertoires/"
        "dictionary-salience-extension-1216.json"
    )
    repertoire = json.loads(repertoire_path.read_text(encoding="utf-8"))
    delta = {
        int(record["codepoint"])
        for record in repertoire["characters"]
    }
    inventory_path = ROOT / "inventories/han_characters.csv"

    assert baseline_designed == baseline_checked
    assert len(baseline_designed) == 4_844
    assert baseline_designed < release_han
    assert release_han - baseline_designed == delta
    assert len(delta) == repertoire["total_count"] == 1_216
    assert repertoire["provenance"]["existing_encoded_union_count"] == 7_904
    assert repertoire["provenance"]["inventory"]["sha256"] == (
        hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    )
    assert len(verified) == 9_120
    assert len(release_han) == 6_060
    assert len(verified - inventory_codepoints) == 3_060
    assert inventory_codepoints - release_han


def test_immutable_han_list_matches_status_joined_inventory() -> None:
    characters = (ROOT / "inventories/han_characters.txt").read_text(encoding="utf-8").splitlines()
    rows = records()
    assert len(characters) == len(set(characters)) == 11_958
    assert characters == [row["character"] for row in rows]


def test_status_join_cannot_change_the_immutable_han_denominator() -> None:
    counts = collections.Counter({"臺": 3, "灣": 2})
    provenance = {
        "臺": collections.Counter({"entries.key": 3}),
        "灣": collections.Counter({"entries.readings[].gloss": 2}),
    }
    pending = make_records(counts, provenance, set())
    verified = make_records(counts, provenance, {ord("臺"), ord("灣")})

    assert [record.character for record in pending] == [record.character for record in verified]
    assert not any(record.quality_checked for record in pending)
    assert all(record.quality_checked for record in verified)


def test_audit_is_utf8_and_has_no_json_failures() -> None:
    audit = json.loads((ROOT / "reports/database_audit.json").read_text(encoding="utf-8"))
    assert audit["encoding"] == "UTF-8"
    assert audit["json_error_count"] == 0
    assert {table["name"] for table in audit["schema"]} == {"entries", "meta"}
    assert "entries.readings[].gloss" in audit["scanned_logical_fields"]
    assert audit["dictionary_text_unique_codepoints"] == 12_307
    assert len(audit["excluded_format_or_control_codepoints"]) == 1
    assert audit["excluded_format_or_control_codepoints"][0]["codepoint"] == "U+FEFF"


def test_rejected_legacy_ext_f_composition_is_not_marked_finished() -> None:
    record = next(row for row in records() if row["codepoint"] == "U+2D8C3")
    assert record["glyph_designed"] == "False"
    assert record["quality_checked"] == "False"
