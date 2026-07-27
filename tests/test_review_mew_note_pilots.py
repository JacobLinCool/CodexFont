from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.review_mew_note_pilots import (
    PilotReviewError,
    build,
    validate_review,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "families/mew-note-tc/pilots/review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_mew_note_review_build_is_deterministic(tmp_path: Path) -> None:
    first = build(project_root=ROOT, output=tmp_path / "first")
    second = build(project_root=ROOT, output=tmp_path / "second")

    assert _inventory(first) == _inventory(second)
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    assert report["pipeline"] == "mew-note-pilot-raster-review-v1"
    assert len(report["pilots"]) == 2
    assert len(report["proofs"]) == 10
    assert all(
        cell["metrics"]["source"]["edge_contact_ink_pixels"] == 0
        and cell["metrics"]["source"]["small_isolated_component_count"] == 0
        for pilot in report["pilots"]
        for cell in pilot["cells"]
    )


def test_mew_note_review_rejects_bulk_authoring(tmp_path: Path) -> None:
    evidence = build(project_root=ROOT, output=tmp_path / "review")
    review = validate_review(
        review_path=REVIEW_PATH,
        evidence=evidence,
        project_root=ROOT,
    )

    assert review["review_state"] == "REJECT"
    assert review["authorization"]["bulk_authoring_allowed"] is False
    assert review["summary"]["rejected_cells"] == [
        {
            "pilot_id": "mew-note-han-style-pilot",
            "rank": 6,
            "character": "鬱",
        },
        {
            "pilot_id": "mew-note-han-style-pilot",
            "rank": 13,
            "character": "0",
        },
    ]
    assert (
        review["supplementary_scalability_evidence"]["decision"]
        == "ACCEPT_AS_SUPPLEMENTARY_ONLY"
    )
    assert (
        review["supplementary_scalability_evidence"][
            "encoded_coverage_credit"
        ]
        == 0
    )


def test_mew_note_review_rejects_a_stale_proof(tmp_path: Path) -> None:
    evidence = build(project_root=ROOT, output=tmp_path / "review")
    proof = next((evidence / "proof").rglob("*.png"))
    proof.write_bytes(proof.read_bytes() + b"stale")

    with pytest.raises(PilotReviewError, match="stale proof evidence"):
        validate_review(
            review_path=REVIEW_PATH,
            evidence=evidence,
            project_root=ROOT,
        )


def test_mew_note_v1_review_remains_pinned_as_rejected_history() -> None:
    family = json.loads(
        (ROOT / "families/mew-note-tc/family.json").read_text(
            encoding="utf-8"
        )
    )

    history = family["contracts"]["pilot_review_history_v1"]
    assert history["path"] == "families/mew-note-tc/pilots/review.json"
    assert history["sha256"] == _sha256(REVIEW_PATH)
    assert family["authoring"]["pilot_state"] == (
        "pilot-approved-bulk-authoring-allowed"
    )
