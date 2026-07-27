from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import mew_note_release_approval as approval


ROOT = Path(__file__).resolve().parents[1]


def test_release_approval_objects_reject_unknown_and_missing_keys() -> None:
    expected = {"approver_name", "approved_at", "confirmation"}
    canonical = {
        "approver_name": "Codex release reviewer",
        "approved_at": "2026-07-29T13:22:35Z",
        "confirmation": approval.APPROVAL_CONFIRMATION,
    }

    assert approval._exact_object_keys(
        canonical,
        expected,
        label="authorization",
    ) == canonical

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match=r"unknown=\['unexpected'\]",
    ):
        approval._exact_object_keys(
            {**canonical, "unexpected": True},
            expected,
            label="authorization",
        )

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match=r"missing=\['confirmation'\]",
    ):
        approval._exact_object_keys(
            {
                key: value
                for key, value in canonical.items()
                if key != "confirmation"
            },
            expected,
            label="authorization",
        )


def test_release_approval_json_rejects_duplicate_keys(
    tmp_path: Path,
) -> None:
    path = tmp_path / "approval.json"
    path.write_text(
        '{"decision":"APPROVED","decision":"APPROVED"}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="duplicate JSON object key 'decision'",
    ):
        approval._read_object(path, label="approval")


def test_vertical_orientation_correction_has_distinct_supersession() -> None:
    path = (
        ROOT
        / "families/mew-note-tc/sources/imagegen/pipelines/"
        "original-raster-v1/collections/vertical-93/batches/"
        "vertical-0002/"
        "post-review-vertical-orientation-correction.json"
    )
    predecessor = (
        "61cf38ff06a3adeb050fdf75ab98c9c52984eeb68f61c97d8d8f0fc6467af819"
    )
    transition = approval.ApprovedBatchCorrection(
        stage="orientation",
        order=30,
        approval_field=(
            "post_review_vertical_orientation_correction"
        ),
        reason="release-vertical-orientation-rejected",
        path=path,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        predecessor_approval_sha256=predecessor,
    )
    batch = type(
        "Batch",
        (),
        {
            "collection_id": "vertical-93",
            "batch_id": "vertical-0002",
            "corrections": (transition,),
        },
    )()

    records = approval._supersedes_records(
        [batch],
        project_root=ROOT,
    )

    assert records == [
        {
            "release_approval_sha256": predecessor,
            "reason": "release-vertical-orientation-rejected",
            "corrected_batches": [
                {
                    "collection_id": "vertical-93",
                    "batch_id": "vertical-0002",
                    "post_review_vertical_orientation_correction": {
                        "path": path.relative_to(ROOT).as_posix(),
                        "sha256": hashlib.sha256(
                            path.read_bytes()
                        ).hexdigest(),
                    },
                }
            ],
        }
    ]
