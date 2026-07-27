from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import mew_note_batch_evidence as evidence
from scripts import mew_note_post_review_correction as correction
from scripts import mew_note_release_approval as approval


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("nonhan-0048", "U+FFEB", 476, 377),
    ("nonhan-0120", "U+20A9", 553, 381),
)
SUPERSEDED_APPROVAL_SHA256 = (
    "7aee0d83b851eaec12c66b405fd5b788f7fe3bdb7e6cde00438176113f0d3617"
)


@pytest.mark.parametrize(
    ("batch_id", "codepoint", "rejected_width", "corrected_width"),
    CASES,
)
def test_release_metric_correction_preserves_rejection_and_validates_current(
    batch_id: str,
    codepoint: str,
    rejected_width: int,
    corrected_width: int,
) -> None:
    context = evidence.load_context(ROOT)
    paths = context.batch_paths("nonhan-3060", batch_id)
    record = correction.validate_correction(
        context,
        "nonhan-3060",
        batch_id,
        require_new_review=True,
    )
    metric = correction._metric_contract(
        context,
        "nonhan-3060",
        batch_id,
        codepoint,
    )

    assert metric["maximum_ink_width"] == 448
    rejected = record["rejected_release_metric"]
    assert rejected == {
        "bounds": rejected["bounds"],
        "width": rejected_width,
        "maximum_ink_width": 448,
        "decision": "REJECT",
    }
    assert rejected["width"] == rejected["bounds"][2] - rejected["bounds"][0]
    assert record["prior_evidence"]["vector_report"]["sha256"] != (
        record["correction_generation"]["vector_report"]["sha256"]
    )
    assert record["prior_evidence"]["vector_ttf"]["sha256"] != (
        record["correction_generation"]["vector_ttf"]["sha256"]
    )

    current = correction._vector_metric(
        report_path=paths.build / "report.json",
        codepoint=codepoint,
        metric=metric,
        source_sha256=evidence.sha256_path(
            paths.source / "source.json"
        ),
        expect_rejected=False,
    )
    assert current["width"] == corrected_width
    assert current["width"] <= metric["maximum_ink_width"]
    assert current["micro_edge_count"] == 0
    assert current["acute_micro_turn_count"] == 0


@pytest.mark.parametrize(
    ("batch_id", "_codepoint", "_rejected_width", "_corrected_width"),
    CASES,
)
def test_correction_ledger_pins_exact_superseded_review_and_approval(
    batch_id: str,
    _codepoint: str,
    _rejected_width: int,
    _corrected_width: int,
) -> None:
    context = evidence.load_context(ROOT)
    paths = context.batch_paths("nonhan-3060", batch_id)
    protected = (
        paths.source / "history.json",
        paths.source / "source.json",
        paths.source / "raster.png",
        paths.source / "review.json",
        ROOT / approval.APPROVAL_RELATIVE,
    )
    before = {
        path: evidence.sha256_path(path)
        for path in protected
    }

    record = correction.validate_correction(
        context,
        "nonhan-3060",
        batch_id,
        require_new_review=True,
    )
    prior = record["prior_evidence"]
    assert prior["release_approval"]["sha256"] == (
        SUPERSEDED_APPROVAL_SHA256
    )
    assert prior["release_approval"]["retention"] == (
        "hash-only-superseded-after-reapproval"
    )
    assert prior["review"]["sha256"] != evidence.sha256_path(
        paths.source / "review.json"
    )
    assert prior["review"]["retention"] == "hash-only-superseded"
    assert {
        path: evidence.sha256_path(path)
        for path in protected
    } == before
    assert correction.correction_path(
        context, "nonhan-3060", batch_id
    ).is_file()


def test_history_conversion_preserves_every_attempt_and_only_demotes_final() -> None:
    context = evidence.load_context(ROOT)
    history = evidence.validate_history(
        context, "nonhan-3060", "nonhan-0120"
    )

    converted = correction._history_steps(
        context,
        "nonhan-3060",
        "nonhan-0120",
        history,
    )

    assert len(converted) == len(history["steps"])
    assert all(step.disposition == "rejected" for step in converted)
    assert [step.call_id for step in converted] == [
        step["call_id"] for step in history["steps"]
    ]
    assert [step.output_sha256 for step in converted] == [
        step["output"]["sha256"] for step in history["steps"]
    ]
    assert all(step.output_path is None for step in converted)


def test_release_approval_overwrite_requires_exact_correction_predecessor(
    tmp_path: Path,
) -> None:
    path = tmp_path / "approval.json"
    path.write_text('{"old":true}\n', encoding="utf-8")
    old_sha256 = evidence.sha256_path(path)

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="latest transition predecessor",
    ):
        approval._required_predecessor_bytes(
            path,
            trusted_root=tmp_path,
            required_predecessor_sha256="0" * 64,
        )
    assert path.read_text(encoding="utf-8") == '{"old":true}\n'

    assert approval._required_predecessor_bytes(
        path,
        trusted_root=tmp_path,
        required_predecessor_sha256=old_sha256,
    ) == b'{"old":true}\n'


def test_release_approval_validation_failure_atomically_restores_predecessor(
    tmp_path: Path,
) -> None:
    path = tmp_path / "approval.json"
    predecessor = b'{"old":true}\n'
    path.write_bytes(predecessor)
    old_sha256 = evidence.sha256_path(path)

    def reject_new_approval() -> None:
        assert path.read_text(encoding="utf-8") == (
            '{\n  "new": true\n}\n'
        )
        raise RuntimeError("post-write validation failed")

    with pytest.raises(
        RuntimeError,
        match="post-write validation failed",
    ):
        approval._install_validated_approval(
            path,
            {"new": True},
            trusted_root=tmp_path,
            required_predecessor_sha256=old_sha256,
            validate_transition=lambda _payload, _sha256: None,
            validate=reject_new_approval,
        )

    assert path.read_bytes() == predecessor
    assert path.with_name(f".{path.name}.lock").is_file()


def test_successful_validated_approval_install_releases_lock(
    tmp_path: Path,
) -> None:
    path = tmp_path / "approval.json"
    path.write_text('{"old":true}\n', encoding="utf-8")
    old_sha256 = evidence.sha256_path(path)
    validated = False

    def validate() -> None:
        nonlocal validated
        assert path.read_text(encoding="utf-8") == (
            '{\n  "new": true\n}\n'
        )
        validated = True

    approval._install_validated_approval(
        path,
        {"new": True},
        trusted_root=tmp_path,
        required_predecessor_sha256=old_sha256,
        validate_transition=lambda _payload, _sha256: None,
        validate=validate,
    )

    assert validated is True
    assert not path.with_name(f".{path.name}.lock").exists()


def test_release_approval_lock_rejects_concurrent_overwrite(
    tmp_path: Path,
) -> None:
    path = tmp_path / "approval.json"
    predecessor = b'{"old":true}\n'
    path.write_bytes(predecessor)
    validator_called = False

    def validate() -> None:
        nonlocal validator_called
        validator_called = True

    with approval._approval_lock(path):
        with pytest.raises(
            approval.MewNoteReleaseApprovalError,
            match="install lock already exists",
        ):
            approval._install_validated_approval(
                path,
                {"new": True},
                trusted_root=tmp_path,
                required_predecessor_sha256=evidence.sha256_path(path),
                validate_transition=lambda _payload, _sha256: None,
                validate=validate,
            )

    assert path.read_bytes() == predecessor
    assert validator_called is False
    assert not path.with_name(f".{path.name}.lock").exists()


def test_multiple_corrected_batches_share_one_superseded_approval() -> None:
    prior = "a" * 64
    batches = [
        SimpleNamespace(
            collection_id="nonhan-3060",
            batch_id=batch_id,
            corrections=(
                approval.ApprovedBatchCorrection(
                    stage="metric",
                    order=10,
                    approval_field="post_review_correction",
                    reason=correction.REASON,
                    path=ROOT
                    / "families/mew-note-tc/sources/imagegen/"
                    "pipelines/original-raster-v1/collections/"
                    "nonhan-3060/batches"
                    / batch_id
                    / correction.RECORD_NAME,
                    sha256=digest,
                    predecessor_approval_sha256=prior,
                ),
            ),
        )
        for batch_id, digest in (
            ("nonhan-0048", "b" * 64),
            ("nonhan-0120", "c" * 64),
        )
    ]

    records = approval._supersedes_records(
        batches,
        project_root=ROOT,
    )

    assert len(records) == 1
    assert records[0]["release_approval_sha256"] == prior
    assert [
        item["batch_id"]
        for item in records[0]["corrected_batches"]
    ] == ["nonhan-0048", "nonhan-0120"]
