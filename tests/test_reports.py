from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist/clear-hand-tc"
REPORT = DIST / "report.json"
PROOF_SIZES = (12, 16, 20, 24, 32, 36, 56, 72)
COVERAGE_REPORT = ROOT / "reports/coverage.json"
REQUIREMENTS = ROOT / "inventories/font_requirements.json"
COMMON_REPERTOIRE = ROOT / "sources/imagegen/repertoires/common-3000.json"
MOE_EXTENSION_REPERTOIRE = (
    ROOT / "sources/imagegen/repertoires/moe-common-extension-1844.json"
)
DICTIONARY_EXTENSION_REPERTOIRE = (
    ROOT
    / "sources/imagegen/repertoires/dictionary-salience-extension-1216.json"
)
NONHAN_REPERTOIRE = ROOT / "sources/imagegen/repertoires/nonhan-3060.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_report() -> dict[str, object]:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _coverage_scope(required: set[int], valid: set[int]) -> dict[str, object]:
    present = required & valid
    return {
        "required": len(required),
        "valid": len(present),
        "missing": len(required - present),
        "coverage_percent": round(
            len(present) / len(required) * 100.0,
            6,
        ),
    }


def test_repository_coverage_report_matches_frozen_9120_repertoires() -> None:
    report = json.loads(COVERAGE_REPORT.read_text(encoding="utf-8"))
    requirements = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    common = json.loads(COMMON_REPERTOIRE.read_text(encoding="utf-8"))
    extension = json.loads(
        MOE_EXTENSION_REPERTOIRE.read_text(encoding="utf-8")
    )
    dictionary_extension = json.loads(
        DICTIONARY_EXTENSION_REPERTOIRE.read_text(encoding="utf-8")
    )
    nonhan = json.loads(NONHAN_REPERTOIRE.read_text(encoding="utf-8"))

    valid = {int(record["codepoint"]) for record in common["characters"]}
    valid.update(
        int(record["codepoint"]) for record in extension["characters"]
    )
    valid.update(
        int(record["codepoint"])
        for record in dictionary_extension["characters"]
    )
    valid.update(
        int(record["codepoint"].removeprefix("U+"), 16)
        for record in nonhan["glyphs"]
    )
    categories = {
        int(record["codepoint_decimal"]): set(record["categories"])
        for record in requirements["requirements"]
    }
    required = set(categories)
    latin_letters = set(range(ord("A"), ord("Z") + 1)) | set(
        range(ord("a"), ord("z") + 1)
    )
    digits = set(range(ord("0"), ord("9") + 1))
    scopes = {
        "dictionary_han": {
            codepoint
            for codepoint, values in categories.items()
            if "dictionary_han" in values
        },
        "dictionary_text": {
            codepoint
            for codepoint, values in categories.items()
            if "dictionary_text" in values
        },
        "all": required,
        "latin_letters": latin_letters & required,
        "digits": digits & required,
        "symbols": {
            codepoint
            for codepoint in required
            if unicodedata.category(chr(codepoint))[0] in {"P", "S"}
        },
    }

    assert len(valid) == 9120
    assert valid <= required
    assert report["_metadata"] == {
        "schema_version": 2,
        "release_version": "0.1",
        "release_scope": "0.1 Preview with 9,120 encoded codepoints",
        "denominator": "inventories/font_requirements.json",
        "valid_set": (
            "sources/imagegen/repertoires/common-3000.json union "
            "sources/imagegen/repertoires/"
            "moe-common-extension-1844.json union "
            "sources/imagegen/repertoires/"
            "dictionary-salience-extension-1216.json union "
            "sources/imagegen/repertoires/nonhan-3060.json"
        ),
        "full_prompt_requirement_complete": False,
        "full_prompt_required": 18071,
        "full_prompt_covered": 9120,
        "full_prompt_missing": 8951,
    }
    assert {
        name: report[name]
        for name in scopes
    } == {
        name: _coverage_scope(codepoints, valid)
        for name, codepoints in scopes.items()
    }


def test_release_report_declares_complete_9120_admission_set() -> None:
    report = _load_report()
    approvals = report["approvals"]
    coverage = report["coverage"]
    repertoires = report["repertoires"]
    glyphs = report["glyphs"]
    vertical = report["vertical_alternates"]

    assert isinstance(approvals, dict)
    assert [record["batch_id"] for record in approvals["common_han"]] == [
        f"common-{index:04d}" for index in range(1, 189)
    ]
    assert approvals["moe_common_extension"]["batch_count"] == 116
    assert approvals["moe_common_extension"]["character_count"] == 1844
    assert approvals["dictionary_salience_extension"]["batch_count"] == 76
    assert (
        approvals["dictionary_salience_extension"]["character_count"]
        == 1216
    )
    assert [record["batch_id"] for record in approvals["nonhan"]] == [
        f"nonhan-{index:04d}" for index in range(1, 207)
    ]
    assert [
        record["batch_id"]
        for record in approvals["vertical_alternates"]
    ] == [f"vertical-{index:04d}" for index in range(1, 7)]

    expected_coverage = {
        "cmap_count": 9120,
        "common_han": 6060,
        "dictionary_salience_extension": 1216,
        "moe_common": 4808,
        "moe_common_complete": True,
        "nonhan_total": 3060,
        "nonhan_visible": 3043,
        "semantic_empty": 17,
        "hiragana": 93,
        "katakana": 96,
        "visible_total": 9103,
        "unencoded_vertical_alternates": 93,
        "vertical_substitution_bases": 93,
        "total_glyph_count_including_notdef": 9214,
    }
    for key, expected in expected_coverage.items():
        assert coverage[key] == expected
    assert repertoires["base_han"]["count"] == 3000
    assert repertoires["moe_common_extension"]["count"] == 1844
    assert repertoires["dictionary_salience_extension"]["count"] == 1216
    assert repertoires["nonhan"]["count"] == 3060
    assert repertoires["vertical_alternates"]["count"] == 93

    assert isinstance(glyphs, list) and len(glyphs) == 9120
    assert isinstance(vertical, list) and len(vertical) == 93
    assert [glyph["glyph_order_index"] for glyph in glyphs] == list(
        range(1, 9121)
    )
    assert [
        glyph["glyph_order_index"] for glyph in vertical
    ] == list(range(9121, 9214))
    assert len({glyph["codepoint"] for glyph in glyphs}) == 9120
    assert len({glyph["glyph_name"] for glyph in glyphs}) == 9120
    assert all(record["encoded"] is False for record in vertical)


def test_release_artifact_paths_and_hashes_match_dist_exactly() -> None:
    report = _load_report()
    font = report["font"]
    license_record = report["license"]
    proofs = report["proofs"]
    declared_hashes = report["artifact_sha256"]

    assert isinstance(font, dict)
    assert isinstance(license_record, dict)
    assert isinstance(proofs, list)
    assert isinstance(declared_hashes, dict)

    artifact_records = {
        font["ttf"]: font["ttf_sha256"],
        font["otf"]: font["otf_sha256"],
        font["woff"]: font["woff_sha256"],
        font["woff2"]: font["woff2_sha256"],
        font["css"]: font["css_sha256"],
        license_record["path"]: license_record["sha256"],
    }

    expected_proof_paths = {
        f"proof/{polarity}-{size}px.png"
        for size in PROOF_SIZES
        for polarity in ("black-on-white", "white-on-black")
    }
    expected_vertical_proof_paths = {
        f"proof/vertical-shaping-{polarity}-56px.png"
        for polarity in ("black-on-white", "white-on-black")
    }
    regular_proofs = [
        proof for proof in proofs if proof.get("kind") != "vertical-shaping"
    ]
    vertical_proofs = [
        proof for proof in proofs if proof.get("kind") == "vertical-shaping"
    ]
    assert len(regular_proofs) == 2 * len(PROOF_SIZES)
    assert len(vertical_proofs) == 2
    assert {proof["path"] for proof in proofs} == (
        expected_proof_paths | expected_vertical_proof_paths
    )
    assert {
        (proof["size_px"], proof["polarity"]) for proof in regular_proofs
    } == {
        (size, polarity)
        for size in PROOF_SIZES
        for polarity in ("black-on-white", "white-on-black")
    }
    artifact_records.update(
        {proof["path"]: proof["sha256"] for proof in proofs}
    )

    assert set(artifact_records) == {
        "font/ClearHandTC-Regular.ttf",
        "font/ClearHandTC-Regular.otf",
        "font/ClearHandTC-Regular.woff",
        "font/ClearHandTC-Regular.woff2",
        "font/ClearHandTC-Regular.css",
        "OFL.txt",
        *expected_proof_paths,
        *expected_vertical_proof_paths,
    }
    assert declared_hashes == artifact_records

    actual_files = {
        path.relative_to(DIST).as_posix()
        for path in DIST.rglob("*")
        if path.is_file() and path != REPORT
    }
    assert actual_files == set(artifact_records)
    for relative_path, expected_sha256 in artifact_records.items():
        artifact = DIST / relative_path
        assert _sha256(artifact) == expected_sha256, relative_path
