from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ROOT = ROOT / "families/mew-note-tc"
FAMILY_PATH = FAMILY_ROOT / "family.json"
BRIEF_PATH = FAMILY_ROOT / "design-brief.json"
COLLECTIONS_PATH = FAMILY_ROOT / "collections.json"
AUTHORING_PATH = FAMILY_ROOT / "authoring.json"
PIPELINE_PATH = FAMILY_ROOT / "pipeline.json"
MOTIF_PATH = FAMILY_ROOT / "motif-contract.json"
PROVENANCE_PATH = FAMILY_ROOT / "pilots/provenance-v2.json"
REVIEW_PATH = FAMILY_ROOT / "pilots/review-v2.json"
V1_PROVENANCE_PATH = FAMILY_ROOT / "pilots/provenance.json"
V1_REVIEW_PATH = FAMILY_ROOT / "pilots/review.json"
BRIEF_VALIDATOR = (
    ROOT
    / ".agents/skills/design-font-family/scripts/validate_design_brief.py"
)


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _brief_validator():
    spec = importlib.util.spec_from_file_location(
        "mew_note_design_brief_validator",
        BRIEF_VALIDATOR,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _collection(payload: dict[str, Any], identifier: str) -> dict[str, Any]:
    matches = [
        item
        for item in payload["collections"]
        if item["id"] == identifier
    ]
    assert len(matches) == 1
    return matches[0]


def _codepoint_lines(codepoints: list[int]) -> bytes:
    return "".join(
        f"U+{codepoint:04X}\n" for codepoint in codepoints
    ).encode("ascii")


def test_mew_note_brief_is_valid_and_identity_is_frozen() -> None:
    brief = _object(BRIEF_PATH)
    _brief_validator().validate(brief)

    assert brief["project_id"] == "mew-note-tc"
    assert brief["family"] == {
        "name": "Mew Note TC",
        "style": "Regular",
        "version": "1.000",
    }
    assert brief["design_contract"]["authoring_mode"] == (
        "original-raster-first"
    )
    assert brief["design_contract"]["units_per_em"] == 1024
    assert brief["design_contract"]["required_features"] == [
        "kern",
        "mark",
        "mkmk",
        "vert",
        "vrt2",
    ]
    assert brief["licensing"] == {
        "source_license": "OFL-1.1",
        "release_license": "OFL-1.1",
    }
    assert all(
        reference["outline_import_allowed"] is False
        for reference in brief["references"]
    )


def test_mew_note_family_manifest_pins_every_contract() -> None:
    family = _object(FAMILY_PATH)
    assert set(family) == {
        "schema_version",
        "record_type",
        "family_id",
        "names",
        "release_identity",
        "contracts",
        "workspace",
        "authoring",
        "release_target",
        "licensing",
        "stop_conditions",
    }
    assert family["schema_version"] == 1
    assert family["record_type"] == "codexfont-family-contract"
    assert family["family_id"] == "mew-note-tc"
    assert family["names"]["postscript_name"] == "MewNoteTC-Regular"
    assert family["release_identity"] == {
        "product_status": "0.1 Preview",
        "opentype_version": "1.000",
        "font_revision": 1.0,
        "license": "OFL-1.1",
    }

    expected_contract_paths = {
        "design_brief": BRIEF_PATH,
        "collections": COLLECTIONS_PATH,
        "authoring": AUTHORING_PATH,
        "motif": MOTIF_PATH,
        "pilot_provenance": PROVENANCE_PATH,
        "pilot_review": REVIEW_PATH,
        "pilot_provenance_history_v1": V1_PROVENANCE_PATH,
        "pilot_review_history_v1": V1_REVIEW_PATH,
    }
    for key, path in expected_contract_paths.items():
        reference = family["contracts"][key]
        assert ROOT / reference["path"] == path
        assert reference["sha256"] == _sha256(path)

    assert family["workspace"]["source_root"].startswith(
        "families/mew-note-tc/"
    )
    assert family["workspace"]["release_root"] == "dist/mew-note-tc"
    assert family["authoring"]["pilot_state"] == (
        "pilot-approved-bulk-authoring-allowed"
    )
    assert family["authoring"]["bulk_authoring_allowed"] is True
    assert family["authoring"]["active_pilot_ids"] == [
        "mew-note-han-style-pilot-v2",
        "mew-note-nonhan-style-pilot",
    ]
    assert family["authoring"]["detached_cat_contour_allowed"] is False
    assert family["authoring"]["tail_terminal_allowed"] is True
    assert family["authoring"]["maximum_tail_terminals_per_glyph"] == 1
    assert family["authoring"]["neutral_safety_allowed"] is True
    assert all(
        family["authoring"][key] is False
        for key in (
            "clear_hand_raster_reuse_allowed",
            "clear_hand_outline_reuse_allowed",
            "clear_hand_review_reuse_allowed",
            "clear_hand_approval_reuse_allowed",
        )
    )
    license_reference = family["licensing"]
    assert license_reference["identifier"] == "OFL-1.1"
    assert license_reference["sha256"] == _sha256(
        ROOT / license_reference["path"]
    )


def test_mew_note_han_6060_sequence_is_deterministic_and_unique() -> None:
    collections = _object(COLLECTIONS_PATH)
    han = _collection(collections, "han-6060")
    base, extension, additional = han["ordered_segments"]

    for reference in (base, extension):
        path = ROOT / reference["path"]
        assert reference["sha256"] == _sha256(path)
        payload = _object(path)
        assert len(payload["characters"]) == reference["count"]

    base_codepoints = [
        record["codepoint"]
        for record in _object(ROOT / base["path"])["characters"]
    ]
    extension_codepoints = [
        record["codepoint"]
        for record in _object(ROOT / extension["path"])["characters"]
    ]
    existing = set(base_codepoints) | set(extension_codepoints)
    assert len(base_codepoints) == 3000
    assert len(extension_codepoints) == 1844
    assert len(existing) == 4844

    inventory_path = ROOT / additional["input_path"]
    requirements_path = ROOT / additional["requirements_path"]
    assert additional["input_sha256"] == _sha256(inventory_path)
    assert additional["requirements_sha256"] == _sha256(
        requirements_path
    )
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    requirements = _object(requirements_path)
    required = {
        record["codepoint_decimal"]
        for record in requirements["requirements"]
    }
    candidates = [
        record
        for record in inventory
        if record["codepoint_decimal"] in required
        and record["codepoint_decimal"] not in existing
    ]
    candidates.sort(
        key=lambda record: (
            -record["occurrence_count"],
            record["codepoint_decimal"],
        )
    )
    additional_codepoints = [
        record["codepoint_decimal"]
        for record in candidates[: additional["count"]]
    ]
    assert len(additional_codepoints) == 1216
    assert len(set(additional_codepoints)) == 1216
    assert (
        hashlib.sha256(_codepoint_lines(additional_codepoints)).hexdigest()
        == additional["sequence_sha256"]
    )

    combined = base_codepoints + extension_codepoints + additional_codepoints
    assert len(combined) == han["encoded_count"] == 6060
    assert len(set(combined)) == 6060
    assert (
        hashlib.sha256(_codepoint_lines(combined)).hexdigest()
        == han["sequence_sha256"]
    )
    characters = "".join(chr(codepoint) for codepoint in combined)
    assert hashlib.sha256(characters.encode("utf-8")).hexdigest() == (
        han["characters_sha256"]
    )
    assert (
        han["common_han_required"]
        + han["existing_uncommon_han"]
        + han["additional_uncommon_han"]
        == 6060
    )
    family_repertoire = han["family_repertoire"]
    family_repertoire_path = ROOT / family_repertoire["path"]
    assert family_repertoire["sha256"] == _sha256(
        family_repertoire_path
    )
    assert family_repertoire_path.is_relative_to(FAMILY_ROOT)
    projected = _object(family_repertoire_path)
    assert projected["family_id"] == "mew-note-tc"
    assert projected["pipeline_id"] == "original-raster-v1"
    assert projected["counts"]["encoded"] == 6060
    assert [
        record["codepoint"] for record in projected["glyphs"]
    ] == combined


def test_mew_note_collections_lock_9120_and_all_189_kana() -> None:
    collections = _object(COLLECTIONS_PATH)
    milestone = collections["milestone"]
    assert milestone == {
        "product_status": "0.1 Preview",
        "requirements_path": "inventories/font_requirements.json",
        "requirements_sha256": (
            "658c5e7070e6875dac4392b988357107b662467cd976863d053df046d9b65a6a"
        ),
        "requirements_count": 18071,
        "cmap_target": 9120,
        "coverage_percent": 50.4676,
        "strictly_exceeds_half": True,
        "visible_encoded_target": 9103,
        "semantic_empty_target": 17,
        "unencoded_vertical_alternates_target": 93,
        "glyph_order_target_including_notdef": 9214,
    }
    assert milestone["cmap_target"] / milestone["requirements_count"] > 0.5
    assert milestone["cmap_target"] == 6060 + 3060
    assert milestone["visible_encoded_target"] == 6060 + 3043
    assert milestone["glyph_order_target_including_notdef"] == (
        1 + 9120 + 93
    )
    requirements = ROOT / milestone["requirements_path"]
    assert milestone["requirements_sha256"] == _sha256(requirements)

    nonhan = _collection(collections, "nonhan-3060")
    nonhan_reference = nonhan["family_repertoire"]
    nonhan_path = ROOT / nonhan_reference["path"]
    assert nonhan_reference["sha256"] == _sha256(nonhan_path)
    assert nonhan_path.is_relative_to(FAMILY_ROOT)
    repertoire = _object(nonhan_path)
    assert repertoire["family_id"] == "mew-note-tc"
    assert repertoire["pipeline_id"] == "original-raster-v1"
    assert repertoire["counts"]["encoded"] == nonhan["encoded_count"] == 3060
    assert (
        repertoire["counts"]["visible"]
        == nonhan["visible_count"]
        == 3043
    )
    assert (
        repertoire["counts"]["semantic_empty"]
        == nonhan["semantic_empty_count"]
        == 17
    )
    codepoints = {
        int(record["codepoint"].removeprefix("U+"), 16)
        for record in repertoire["glyphs"]
    }
    hiragana = {
        codepoint for codepoint in codepoints if 0x3041 <= codepoint <= 0x309F
    }
    katakana = {
        codepoint for codepoint in codepoints if 0x30A0 <= codepoint <= 0x30FF
    }
    subsets = {
        subset["id"]: subset for subset in nonhan["required_subsets"]
    }
    assert len(hiragana) == subsets["hiragana"]["count"] == 93
    assert len(katakana) == subsets["katakana"]["count"] == 96
    assert not hiragana & katakana
    assert (
        len(hiragana | katakana)
        == subsets["kana-total"]["count"]
        == 189
    )

    vertical = _collection(collections, "vertical-93")
    vertical_reference = vertical["family_repertoire"]
    vertical_path = ROOT / vertical_reference["path"]
    assert vertical_reference["sha256"] == _sha256(vertical_path)
    assert vertical_path.is_relative_to(FAMILY_ROOT)
    vertical_repertoire = _object(vertical_path)
    assert (
        vertical_repertoire["counts"]["visible"]
        == vertical["visible_count"]
        == 93
    )
    assert len(vertical_repertoire["alternates"]) == 93
    assert vertical["required_features"] == ["vert", "vrt2"]

    partition = collections["partition_contract"]
    assert partition["encoded_overlap_count"] == 0
    assert partition["fallback_counts_as_coverage"] is False
    assert partition["clear_hand_glyph_evidence_reusable"] is False
    assert (
        partition["every_visible_glyph_requires_mew_note_raster_review_and_approval"]
        is True
    )


def test_mew_note_motif_is_one_attached_tail_or_a_safe_terminal() -> None:
    motif = _object(MOTIF_PATH)
    assert motif["family_id"] == "mew-note-tc"
    rules = motif["global_rules"]
    assert rules["detached_decorative_contours_allowed"] is False
    assert (
        rules["source_topology_extra_decorative_components_allowed"] is False
    )
    assert rules["maximum_motif_sites_per_glyph"] == 1

    motif_classes = {
        item["id"]: item for item in motif["motif_classes"]
    }
    assert set(motif_classes) == {
        "tail-terminal",
        "soft-terminal",
        "neutral-safety",
    }
    assert all(item["detached"] is False for item in motif_classes.values())
    tail_geometry = motif_classes["tail-terminal"]["geometry"]
    assert tail_geometry["must_extend_existing_final_stroke"] is True
    assert tail_geometry["must_share_final_stroke_contour"] is True
    assert tail_geometry["self_intersection_allowed"] is False
    assert (
        motif_classes["neutral-safety"]["geometry"][
            "decorative_component_count"
        ]
        == 0
    )
    assignment = motif["assignment_policy"]
    assert assignment["neutral_safety_allowed"] is True
    assert assignment["semantic_empty_class"] == "neutral-safety"
    assert "combining-marks" in assignment["neutral_safety_required_groups"]
    assert "box-drawing" in assignment["neutral_safety_required_groups"]
    tail_assignment = assignment["tail_assignment"]
    assert tail_assignment == {
        "repertoire_maximum_ratio": 0.35,
        "readable_text_minimum_sample_glyphs": 40,
        "readable_text_ratio": {
            "minimum": 0.15,
            "maximum": 0.35,
        },
        "maximum_consecutive_tail_glyphs": 2,
        "tail_on_every_glyph_forbidden": True,
    }

    failures = {
        item["id"]: item for item in motif["pilot_failures"]
    }
    assert failures["floating-cat-hat"]["decision"] == "REJECT"
    assert motif["geometry_gates"]["detached_cat_contour_decision"] == (
        "REJECT"
    )
    assert motif["geometry_gates"]["max_micro_edge_count"] == 0
    assert motif["geometry_gates"]["max_acute_micro_turn_count"] == 0
    assert (
        motif["geometry_gates"][
            "tail_must_preserve_identity_and_stroke_topology"
        ]
        is True
    )

    brief = _object(BRIEF_PATH)
    assert motif["review_gates"]["proof_sizes_px"] == (
        brief["acceptance"]["proof_sizes_px"]
    )
    assert motif["review_gates"]["proof_polarities"] == (
        brief["acceptance"]["proof_polarities"]
    )


def test_mew_note_frozen_pilots_are_style_only_and_hash_pinned() -> None:
    provenance = _object(V1_PROVENANCE_PATH)
    assert provenance["family_id"] == "mew-note-tc"
    assert provenance["pilot_state"] == (
        "pilot-source-frozen-review-pending"
    )
    assert provenance["scope"] == {
        "purpose": (
            "Freeze the accepted cat-tail style direction before full "
            "technical review"
        ),
        "style_gate_only": True,
        "encoded_coverage_credit": 0,
        "release_approval": False,
        "bulk_authoring_allowed": False,
    }
    assert provenance["prompt_policy"]["original_prompt_status"] == (
        "original_prompt_unavailable"
    )
    assert (
        provenance["prompt_policy"]["reproduction_prompt_is_original"]
        is False
    )

    expected = {
        "mew-note-han-style-pilot": {
            "call_id": "call_teu5UsMfvk3Mh2rqBGq6NSka",
            "characters": list("永貓手寫龍鬱國愛AaGg08あア"),
            "raster_sha256": (
                "9cce5322a07df04f6e4c0e90e4f98fac020d18fb6994dc5be28e38c8c73182e4"
            ),
            "copybook_sha256": (
                "0fa1995e5555fe70c878a70379250935565a943de41696a0e8555e85436bd4ba"
            ),
        },
        "mew-note-nonhan-style-pilot": {
            "call_id": "call_cERLz0MZYKcyzTt5Fty6hX50",
            "characters": [
                "I",
                "l",
                "1",
                "|",
                "O",
                "o",
                "0",
                "Q",
                "c",
                "e",
                "r",
                "v",
                "ㄅ",
                "ㄆ",
                "°",
                "?",
            ],
            "raster_sha256": (
                "eb755d5fb065798812ddc15619025ab79b290d06fc89626ba845b6580e882f41"
            ),
            "copybook_sha256": (
                "e845e50c5b6cbb6a02e585e243b53a1c69363354dcb60748f67d8208d7edb510"
            ),
        },
    }
    pilots = {pilot["id"]: pilot for pilot in provenance["pilots"]}
    assert set(pilots) == set(expected)
    for identifier, contract in expected.items():
        pilot = pilots[identifier]
        generator = pilot["generator"]
        assert generator["call_id"] == contract["call_id"]
        assert generator["original_prompt_status"] == (
            "original_prompt_unavailable"
        )
        assert isinstance(generator["reproduction_prompt"], str)
        assert "attached" in generator["reproduction_prompt"]
        assert pilot["grid"]["rows"] == 4
        assert pilot["grid"]["columns"] == 4
        assert pilot["grid"]["cell_order"] == contract["characters"]

        raster = pilot["artifacts"]["raster"]
        copybook = pilot["artifacts"]["identity_copybook"]
        assert raster["sha256"] == contract["raster_sha256"]
        assert copybook["sha256"] == contract["copybook_sha256"]
        assert raster["sha256"] == _sha256(ROOT / raster["path"])
        assert copybook["sha256"] == _sha256(ROOT / copybook["path"])
        assert (raster["width"], raster["height"], raster["mode"]) == (
            1254,
            1254,
            "RGB",
        )
        assert (
            copybook["width"],
            copybook["height"],
            copybook["mode"],
        ) == (1600, 1600, "L")
        assert copybook["role"] == (
            "identity-reference-only-no-outline-import"
        )
        assert pilot["manual_decision"]["style_direction"] == "ACCEPTED"
        assert pilot["manual_decision"]["technical_review_state"] == (
            "pending"
        )
        assert pilot["manual_decision"]["release_admission_state"] == (
            "not-admitted"
        )
