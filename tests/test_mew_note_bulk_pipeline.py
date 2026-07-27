from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import font_family_context
from scripts import mew_note_bulk_pipeline as bulk


ROOT = Path(__file__).resolve().parents[1]
FAMILY_PATH = ROOT / bulk.FAMILY_PATH
PIPELINE_PATH = ROOT / bulk.PIPELINE_PATH
PLAN_PATH = ROOT / bulk.PLAN_PATH


def _object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _context() -> font_family_context.FamilyContext:
    return font_family_context.load_family_context(
        project_root=ROOT,
        family_contract_path=FAMILY_PATH,
        pipeline_contract_path=PIPELINE_PATH,
    )


def _rehash_batch(batch: dict) -> None:
    batch["batch_contract_sha256"] = bulk._batch_contract_hash(batch)


def test_family_local_repertoires_are_deterministic_identity_projections() -> None:
    actual_han = _object(ROOT / bulk.HAN_PATH)
    actual_nonhan = _object(ROOT / bulk.NONHAN_PATH)
    actual_vertical = _object(ROOT / bulk.VERTICAL_PATH)

    assert bulk.build_han_repertoire(ROOT) == actual_han
    assert bulk.build_nonhan_repertoire(ROOT) == actual_nonhan
    assert bulk.build_vertical_repertoire(ROOT) == actual_vertical
    for payload in (actual_han, actual_nonhan, actual_vertical):
        assert payload["record_type"] == bulk.REPERTOIRE_RECORD_TYPE
        assert payload["family_id"] == "mew-note-tc"
        assert payload["pipeline_id"] == "original-raster-v1"
        serialized = json.dumps(payload, ensure_ascii=False)
        assert "sources/imagegen/raster/" not in serialized
        assert "sources/imagegen/vector-reviews/" not in serialized
        assert "sources/imagegen/approvals/" not in serialized


def test_context_binds_family_pipeline_authoring_and_each_collection() -> None:
    context = _context()
    assert context.family_id == "mew-note-tc"
    assert context.pipeline_id == "original-raster-v1"
    assert context.source_root == (
        ROOT / "families/mew-note-tc/sources/imagegen"
    )
    assert context.build_root == ROOT / "build/families/mew-note-tc"
    assert context.cache_root == ROOT / "cache/families/mew-note-tc"
    assert context.release_root == ROOT / "dist/mew-note-tc"

    for collection_id in ("han-6060", "nonhan-3060", "vertical-93"):
        binding = context.evidence_binding(collection_id)
        assert binding["family_id"] == "mew-note-tc"
        assert binding["pipeline_id"] == "original-raster-v1"
        assert binding["family_contract"]["sha256"] == hashlib.sha256(
            FAMILY_PATH.read_bytes()
        ).hexdigest()
        assert binding["pipeline_contract"]["sha256"] == hashlib.sha256(
            PIPELINE_PATH.read_bytes()
        ).hexdigest()
        assert binding["authoring_contract"]["sha256"] == hashlib.sha256(
            (ROOT / bulk.AUTHORING_PATH).read_bytes()
        ).hexdigest()


def test_plan_is_byte_deterministic_complete_and_strictly_over_half() -> None:
    context = _context()
    committed = _object(PLAN_PATH)
    rebuilt = bulk.build_plan(context)
    assert rebuilt == committed
    bulk.validate_plan_payload(committed, context=context)

    assert committed["targets"] == {
        "requirements_denominator": 18071,
        "encoded_han": 6060,
        "encoded_nonhan": 3060,
        "encoded_total": 9120,
        "visible_encoded": 9103,
        "semantic_empty": 17,
        "unencoded_vertical": 93,
        "coverage_percent": 50.4676,
        "hiragana": 93,
        "katakana": 96,
        "kana_total": 189,
    }
    assert 9120 / 18071 > 0.5
    assert committed["batch_counts"] == {
        "han": 379,
        "nonhan_visible": 205,
        "nonhan_semantic_empty": 1,
        "vertical": 6,
        "total": 591,
        "visible_raster": 590,
    }


def test_all_kana_and_common_japanese_marks_are_frozen() -> None:
    repertoire = _object(ROOT / bulk.NONHAN_PATH)
    codepoints = {
        int(record["codepoint"][2:], 16)
        for record in repertoire["glyphs"]
    }
    hiragana = {
        codepoint for codepoint in codepoints if 0x3041 <= codepoint <= 0x309F
    }
    katakana = {
        codepoint for codepoint in codepoints if 0x30A0 <= codepoint <= 0x30FF
    }
    assert len(hiragana) == 93
    assert len(katakana) == 96
    assert len(hiragana | katakana) == 189
    assert {
        0x3001,
        0x3002,
        0x300C,
        0x300D,
        0x3099,
        0x309A,
        0x309D,
        0x309E,
        0x30FB,
        0x30FC,
        0x30FD,
        0x30FE,
    } <= codepoints


def test_motif_assignment_is_attached_tail_only_and_ratio_bounded() -> None:
    plan = _object(PLAN_PATH)
    summary = plan["motif_summary"]
    assert 0.15 <= summary["tail_ratio"] <= 0.35
    assert summary["detached_contours_allowed"] is False
    assert summary["spikes_allowed"] is False
    assert sum(summary["counts"].values()) == 9196
    assert summary["counts"]["tail-terminal"] == 1816

    consecutive = 0
    maximum = 0
    for batch in plan["batches"]:
        for entry in batch["entries"]:
            if entry["motif_class"] == "tail-terminal":
                consecutive += 1
                maximum = max(maximum, consecutive)
            else:
                consecutive = 0
            if batch["collection_id"] == "vertical-93":
                assert entry["motif_class"] == "neutral-safety"
            if batch["materialization_kind"] == "semantic-empty":
                assert entry["motif_class"] == "neutral-safety"
    assert maximum <= 2

    authoring = _object(ROOT / bulk.AUTHORING_PATH)
    assert authoring["motif_assignment"]["detached_contours_allowed"] is False
    assert authoring["motif_assignment"]["spikes_allowed"] is False
    assert (
        authoring["motif_assignment"]["maximum_tail_terminals_per_glyph"]
        == 1
    )


def test_every_visible_batch_has_family_specific_planned_artifacts() -> None:
    plan = _object(PLAN_PATH)
    family_prefix = (
        "families/mew-note-tc/sources/imagegen/pipelines/"
        "original-raster-v1/collections/"
    )
    for batch in plan["batches"]:
        artifacts = batch["artifacts"]
        if batch["materialization_kind"] == "visible-raster":
            for key in (
                "prompt",
                "identity_copybook",
                "draft",
                "raster",
            ):
                assert artifacts[key].startswith(family_prefix)
            assert isinstance(batch["prompt_sha256"], str)
            assert len(batch["prompt_sha256"]) == 64
        else:
            assert artifacts["prompt"] is None
            assert artifacts["identity_copybook"] is None
            assert artifacts["raster"] is None
            assert artifacts["draft"].startswith(family_prefix)
        assert artifacts["build_root"].startswith(
            "build/families/mew-note-tc/"
        )
        assert artifacts["cache_root"].startswith(
            "cache/families/mew-note-tc/"
        )
        assert artifacts["release_root"].startswith("dist/mew-note-tc/")
        assert "clear-hand-tc" not in json.dumps(artifacts)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("family_id", "clear-hand-tc"),
        ("pipeline_id", "clear-hand-original-raster-v1"),
    ],
)
def test_plan_rejects_cross_family_and_cross_pipeline_bindings(
    field: str,
    replacement: str,
) -> None:
    context = _context()
    plan = _object(PLAN_PATH)
    tampered = deepcopy(plan)
    tampered["batches"][0]["family_context"][field] = replacement
    _rehash_batch(tampered["batches"][0])

    with pytest.raises(bulk.MewNoteBulkError, match="context mismatch"):
        bulk.validate_plan_payload(tampered, context=context)


def test_plan_rejects_cross_collection_binding() -> None:
    context = _context()
    plan = _object(PLAN_PATH)
    tampered = deepcopy(plan)
    tampered["batches"][0]["family_context"] = context.evidence_binding(
        "nonhan-3060"
    )
    _rehash_batch(tampered["batches"][0])

    with pytest.raises(bulk.MewNoteBulkError, match="context mismatch"):
        bulk.validate_plan_payload(tampered, context=context)


def test_plan_rejects_detached_or_spiky_motif_contract() -> None:
    context = _context()
    plan = _object(PLAN_PATH)
    detached = deepcopy(plan)
    detached["motif_summary"]["detached_contours_allowed"] = True
    with pytest.raises(bulk.MewNoteBulkError, match="motif summary mismatch"):
        bulk.validate_plan_payload(detached, context=context)

    spiky = deepcopy(plan)
    spiky["motif_summary"]["spikes_allowed"] = True
    with pytest.raises(bulk.MewNoteBulkError, match="motif summary mismatch"):
        bulk.validate_plan_payload(spiky, context=context)
