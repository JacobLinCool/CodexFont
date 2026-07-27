from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.review_mew_note_active_pilots import (
    ActivePilotReviewError,
    build,
    load_active_context,
    validate_review,
)


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ROOT = ROOT / "families/mew-note-tc"
PROVENANCE_PATH = FAMILY_ROOT / "pilots/provenance-v2.json"
REVIEW_PATH = FAMILY_ROOT / "pilots/review-v2.json"
V1_PROVENANCE_PATH = FAMILY_ROOT / "pilots/provenance.json"
V1_REVIEW_PATH = FAMILY_ROOT / "pilots/review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_active_provenance_names_only_v2_han_and_existing_nonhan() -> None:
    context = load_active_context(ROOT)
    provenance = context.provenance

    assert context.active_pilot_ids == (
        "mew-note-han-style-pilot-v2",
        "mew-note-nonhan-style-pilot",
    )
    assert [active.pilot.pilot_id for active in context.pilots] == list(
        context.active_pilot_ids
    )
    assert provenance["scope"]["encoded_coverage_credit"] == 0
    history = provenance["historical_pilots"][0]
    assert history["status"] == "rejected-historical-pilot"
    assert history["decision"] == "REJECT"
    assert history["provenance"]["sha256"] == _sha256(V1_PROVENANCE_PATH)
    assert history["review"]["sha256"] == _sha256(V1_REVIEW_PATH)


def test_v2_generation_and_exact_tail_contract_are_frozen() -> None:
    context = load_active_context(ROOT)
    han = context.pilots[0]
    provenance = context.provenance
    raw_han = provenance["pilots"][0]

    assert han.pilot.characters == tuple("永貓手寫龍鬱國愛AaGg08あア")
    assert han.expected_tail_terminal_ranks == (2, 4, 8, 10, 12)
    assert [
        rank
        for rank, motif_class in enumerate(
            han.expected_motif_classes,
            start=1,
        )
        if motif_class == "tail-terminal"
    ] == [2, 4, 8, 10, 12]
    calls = raw_han["generator"]["calls"]
    assert [call["stage"] for call in calls] == [
        "generation",
        "zero-correction",
    ]
    assert calls[1]["parent_result_sha256"] == calls[0]["result_sha256"]
    assert calls[1]["result_sha256"] == _sha256(han.pilot.raster_path)
    prompt = ROOT / raw_han["generator"]["prompt_record"]["path"]
    assert raw_han["generator"]["prompt_record"]["sha256"] == _sha256(
        prompt
    )


def test_active_review_build_is_deterministic(tmp_path: Path) -> None:
    first = build(project_root=ROOT, output=tmp_path / "first")
    second = build(project_root=ROOT, output=tmp_path / "second")

    assert _inventory(first) == _inventory(second)
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    assert report["active_pilot_ids"] == [
        "mew-note-han-style-pilot-v2",
        "mew-note-nonhan-style-pilot",
    ]
    assert len(report["proofs"]) == 14
    assert len(report["zero_confusable_references"]) == 2
    assert {
        reference["codepoint"]
        for reference in report["zero_confusable_references"]
    } == {"U+00D8", "U+2205"}
    assert all(
        cell["metrics"]["source"]["edge_contact_ink_pixels"] == 0
        and cell["metrics"]["source"]["small_isolated_component_count"] == 0
        for pilot in report["pilots"]
        for cell in pilot["cells"]
    )


def test_active_review_accepts_all_32_cells_and_authorizes_bulk(
    tmp_path: Path,
) -> None:
    evidence = build(project_root=ROOT, output=tmp_path / "review")
    review = validate_review(
        review_path=REVIEW_PATH,
        evidence=evidence,
        project_root=ROOT,
    )

    assert review["review_state"] == "ACCEPT"
    assert review["summary"] == {
        "active_pilot_count": 2,
        "active_cell_count": 32,
        "accepted_cell_count": 32,
        "rejected_cell_count": 0,
        "rejected_cells": [],
        "historical_rejected_pilot_count": 1,
    }
    assert review["authorization"]["bulk_authoring_allowed"] is True
    assert review["pilots"][0]["observed_tail_terminal_ranks"] == [
        2,
        4,
        8,
        10,
        12,
    ]
    assert review["pilots"][1]["observed_tail_terminal_ranks"] == []
    assert (
        review["pilots"][0]["cells"][5]["checks"]["legibility_16px"]
        == "PASS"
    )
    assert (
        review["pilots"][0]["cells"][12]["checks"][
            "confusable_distinction"
        ]
        == "PASS"
    )
    assert (
        review["supplementary_scalability_evidence"][
            "encoded_coverage_credit"
        ]
        == 0
    )


def test_active_review_rejects_stale_proof(tmp_path: Path) -> None:
    evidence = build(project_root=ROOT, output=tmp_path / "review")
    proof = next((evidence / "proof").rglob("*.png"))
    proof.write_bytes(proof.read_bytes() + b"stale")

    with pytest.raises(ActivePilotReviewError, match="stale active proof"):
        validate_review(
            review_path=REVIEW_PATH,
            evidence=evidence,
            project_root=ROOT,
        )


def test_family_opens_bulk_only_for_the_accepted_active_review() -> None:
    family = json.loads(
        (FAMILY_ROOT / "family.json").read_text(encoding="utf-8")
    )
    authoring = family["authoring"]

    assert authoring["pilot_state"] == (
        "pilot-approved-bulk-authoring-allowed"
    )
    assert authoring["bulk_authoring_allowed"] is True
    assert authoring["active_pilot_ids"] == [
        "mew-note-han-style-pilot-v2",
        "mew-note-nonhan-style-pilot",
    ]
    for key, path in (
        ("pilot_provenance", PROVENANCE_PATH),
        ("pilot_review", REVIEW_PATH),
        ("pilot_provenance_history_v1", V1_PROVENANCE_PATH),
        ("pilot_review_history_v1", V1_REVIEW_PATH),
    ):
        reference = family["contracts"][key]
        assert ROOT / reference["path"] == path
        assert reference["sha256"] == _sha256(path)
