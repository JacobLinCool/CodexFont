from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import mew_note_release_approval as approval
from scripts import mew_note_release_deviation as deviation
from scripts import (
    mew_note_post_review_vertical_handedness_correction
    as handedness,
)


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR_SHA256 = (
    "61cf38ff06a3adeb050fdf75ab98c9c52984eeb68f61c97d8d8f0fc6467af819"
)
ROLLED_BACK_SHA256 = (
    "7aee0d83b851eaec12c66b405fd5b788f7fe3bdb7e6cde00438176113f0d3617"
)
ORIENTATION_REVIEW_SHA256 = (
    "d05152f296f07a678c14726085add692d7d14349b31f7babac04b9f1cdf9c633"
)
HANDEDNESS_PREDECESSOR_SHA256 = (
    "bbef5f1b5f5ab050e921afda6f826e49c25dc18aec38197e20492d9a5e579c18"
)


def _valid_61cf_transition() -> tuple[
    dict[str, object],
    dict[str, object],
    list[SimpleNamespace],
    object,
]:
    predecessor_path = (
        ROOT
        / "families/mew-note-tc/approvals/history"
        / f"{PREDECESSOR_SHA256}.approval.json"
    )
    predecessor = approval._read_object(
        predecessor_path,
        label="61cf predecessor fixture",
    )
    release_deviation = deviation.validate_release_deviation(
        project_root=ROOT
    )
    candidate = copy.deepcopy(predecessor)
    candidate["release_deviation"] = approval._pin(
        release_deviation.deviation_path,
        project_root=ROOT,
    )
    candidate["authorization"] = {
        "approver_name": "Codex release reviewer",
        "approved_at": "2026-07-29T13:42:20Z",
        "confirmation": approval.APPROVAL_CONFIRMATION,
    }

    metric_predecessors: dict[tuple[str, str], str] = {}
    for supersedes in predecessor.get("supersedes", []):
        for corrected in supersedes["corrected_batches"]:
            metric_predecessors[
                (
                    corrected["collection_id"],
                    corrected["batch_id"],
                )
            ] = supersedes["release_approval_sha256"]

    orientation_path = (
        ROOT
        / "families/mew-note-tc/sources/imagegen/pipelines/"
        "original-raster-v1/collections/vertical-93/batches/"
        "vertical-0002/"
        "post-review-vertical-orientation-correction.json"
    )
    orientation_sha256 = hashlib.sha256(
        orientation_path.read_bytes()
    ).hexdigest()
    batches: list[SimpleNamespace] = []
    for record in candidate["reviewed_batches"]:
        key = (record["collection_id"], record["batch_id"])
        corrections: list[approval.ApprovedBatchCorrection] = []
        metric_pin = record.get("post_review_correction")
        if metric_pin is not None:
            corrections.append(
                approval.ApprovedBatchCorrection(
                    stage="metric",
                    order=10,
                    approval_field="post_review_correction",
                    reason="release-metric-envelope-rejected",
                    path=ROOT / metric_pin["path"],
                    sha256=metric_pin["sha256"],
                    predecessor_approval_sha256=(
                        metric_predecessors[key]
                    ),
                )
            )
        if key == ("vertical-93", "vertical-0002"):
            record["review"]["sha256"] = ORIENTATION_REVIEW_SHA256
            record["reviewer_name"] = (
                "Codex independent vertical-orientation release reviewer"
            )
            record[
                "post_review_vertical_orientation_correction"
            ] = {
                "path": orientation_path.relative_to(ROOT).as_posix(),
                "sha256": orientation_sha256,
            }
            corrections.append(
                approval.ApprovedBatchCorrection(
                    stage="orientation",
                    order=30,
                    approval_field=(
                        "post_review_vertical_orientation_correction"
                    ),
                    reason="release-vertical-orientation-rejected",
                    path=orientation_path,
                    sha256=orientation_sha256,
                    predecessor_approval_sha256=PREDECESSOR_SHA256,
                )
            )
        batches.append(
            SimpleNamespace(
                collection_id=key[0],
                batch_id=key[1],
                corrections=tuple(corrections),
            )
        )
    candidate["supersedes"] = approval._supersedes_records(
        batches,
        project_root=ROOT,
    )
    return predecessor, candidate, batches, release_deviation


def _valid_bbef_handedness_transition() -> tuple[
    dict[str, object],
    dict[str, object],
    list[SimpleNamespace],
    object,
]:
    predecessor_path = (
        ROOT
        / "families/mew-note-tc/approvals/history"
        / f"{HANDEDNESS_PREDECESSOR_SHA256}.approval.json"
    )
    predecessor = approval._read_object(
        predecessor_path,
        label="bbef handedness predecessor fixture",
    )
    release_deviation = deviation.validate_release_deviation(
        project_root=ROOT
    )
    candidate = copy.deepcopy(predecessor)
    candidate["authorization"] = {
        "approver_name": "Codex release reviewer",
        "approved_at": "2026-07-29T15:00:00Z",
        "confirmation": approval.APPROVAL_CONFIRMATION,
    }

    supersession_by_batch_field: dict[
        tuple[str, str, str], tuple[str, str]
    ] = {}
    for supersedes in predecessor.get("supersedes", []):
        for corrected in supersedes["corrected_batches"]:
            fields = set(corrected) - {"collection_id", "batch_id"}
            assert len(fields) == 1
            field = next(iter(fields))
            supersession_by_batch_field[
                (
                    corrected["collection_id"],
                    corrected["batch_id"],
                    field,
                )
            ] = (
                supersedes["release_approval_sha256"],
                supersedes["reason"],
            )

    spec_by_field = {
        spec.approval_field: spec
        for spec in approval.CORRECTION_TRANSITION_SPECS
    }
    review_path = (
        ROOT
        / "families/mew-note-tc/sources/imagegen/pipelines/"
        "original-raster-v1/collections/vertical-93/batches/"
        "vertical-0002/review.json"
    )
    handedness_path = review_path.with_name(handedness.RECORD_NAME)
    handedness_sha256 = hashlib.sha256(
        handedness_path.read_bytes()
    ).hexdigest()
    review = approval._read_object(
        review_path,
        label="handedness replacement review",
    )

    batches: list[SimpleNamespace] = []
    for record in candidate["reviewed_batches"]:
        key = (record["collection_id"], record["batch_id"])
        corrections: list[approval.ApprovedBatchCorrection] = []
        for field, spec in spec_by_field.items():
            pin = record.get(field)
            if pin is None:
                continue
            predecessor_sha256, reason = (
                supersession_by_batch_field[
                    (key[0], key[1], field)
                ]
            )
            corrections.append(
                approval.ApprovedBatchCorrection(
                    stage=spec.stage,
                    order=spec.order,
                    approval_field=field,
                    reason=reason,
                    path=ROOT / pin["path"],
                    sha256=pin["sha256"],
                    predecessor_approval_sha256=predecessor_sha256,
                )
            )
        if key == (
            handedness.COLLECTION_ID,
            handedness.BATCH_ID,
        ):
            record["review"] = {
                "path": review_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(
                    review_path.read_bytes()
                ).hexdigest(),
            }
            record["reviewer_name"] = review["reviewer"]["name"]
            record[handedness.APPROVAL_FIELD] = {
                "path": handedness_path.relative_to(ROOT).as_posix(),
                "sha256": handedness_sha256,
            }
            corrections.append(
                approval.ApprovedBatchCorrection(
                    stage="handedness",
                    order=40,
                    approval_field=handedness.APPROVAL_FIELD,
                    reason=handedness.REASON,
                    path=handedness_path,
                    sha256=handedness_sha256,
                    predecessor_approval_sha256=(
                        HANDEDNESS_PREDECESSOR_SHA256
                    ),
                )
            )
        batches.append(
            SimpleNamespace(
                collection_id=key[0],
                batch_id=key[1],
                corrections=tuple(corrections),
            )
        )
    candidate["supersedes"] = approval._supersedes_records(
        batches,
        project_root=ROOT,
    )
    return predecessor, candidate, batches, release_deviation


def test_valid_61cf_deviation_orientation_transition() -> None:
    predecessor, candidate, batches, release_deviation = (
        _valid_61cf_transition()
    )

    approval._validate_linear_transition(
        predecessor,
        candidate,
        predecessor_sha256=PREDECESSOR_SHA256,
        batches=batches,
        release_deviation=release_deviation,
        project_root=ROOT,
    )


def test_transition_registry_orders_handedness_after_orientation() -> None:
    approval._validate_transition_spec_registry()

    assert [
        (spec.stage, spec.order, spec.approval_field)
        for spec in approval.CORRECTION_TRANSITION_SPECS
    ] == [
        ("metric", 10, "post_review_correction"),
        (
            "orientation",
            30,
            "post_review_vertical_orientation_correction",
        ),
        (
            "handedness",
            40,
            handedness.APPROVAL_FIELD,
        ),
    ]
    assert approval.DEVIATION_TRANSITION_ORDER == 20


def test_nested_handedness_predecessor_schema_is_exact() -> None:
    spec = next(
        spec
        for spec in approval.CORRECTION_TRANSITION_SPECS
        if spec.stage == "handedness"
    )
    record_path = (
        ROOT
        / "families/mew-note-tc/sources/imagegen/pipelines/"
        "original-raster-v1/collections/vertical-93/batches/"
        "vertical-0002"
        / handedness.RECORD_NAME
    )
    record = approval._read_object(
        record_path,
        label="handedness correction",
    )

    assert approval._correction_predecessor_sha256(
        spec,
        record,
        project_root=ROOT,
    ) == HANDEDNESS_PREDECESSOR_SHA256

    shallow = {
        "prior_evidence": {
            "release_approval": {
                "canonical_overwrite_target": record[
                    "prior_evidence"
                ]["release_approval"]["canonical_overwrite_target"]
            }
        }
    }
    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="key drift",
    ):
        approval._correction_predecessor_sha256(
            spec,
            shallow,
            project_root=ROOT,
        )

    mismatched = copy.deepcopy(record)
    mismatched["prior_evidence"]["release_approval"][
        "immutable_snapshot"
    ]["sha256"] = "0" * 64
    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="nested predecessor approval schema drift",
    ):
        approval._correction_predecessor_sha256(
            spec,
            mismatched,
            project_root=ROOT,
        )


def test_valid_bbef_handedness_linear_delta() -> None:
    predecessor, candidate, batches, release_deviation = (
        _valid_bbef_handedness_transition()
    )

    approval._validate_linear_transition(
        predecessor,
        candidate,
        predecessor_sha256=HANDEDNESS_PREDECESSOR_SHA256,
        batches=batches,
        release_deviation=release_deviation,
        project_root=ROOT,
    )
    assert approval._latest_transition_predecessor_sha256(
        batches,
        release_deviation=release_deviation,
    ) == HANDEDNESS_PREDECESSOR_SHA256


def test_handedness_reapproval_supersedes_exact_bbef_predecessor() -> None:
    _predecessor, candidate, _batches, _deviation = (
        _valid_bbef_handedness_transition()
    )
    matching = [
        item
        for item in candidate["supersedes"]
        if item["release_approval_sha256"]
        == HANDEDNESS_PREDECESSOR_SHA256
    ]

    assert matching == [
        {
            "release_approval_sha256": (
                HANDEDNESS_PREDECESSOR_SHA256
            ),
            "reason": handedness.REASON,
            "corrected_batches": [
                {
                    "collection_id": handedness.COLLECTION_ID,
                    "batch_id": handedness.BATCH_ID,
                    handedness.APPROVAL_FIELD: {
                        "path": (
                            "families/mew-note-tc/sources/imagegen/"
                            "pipelines/original-raster-v1/collections/"
                            "vertical-93/batches/vertical-0002/"
                            f"{handedness.RECORD_NAME}"
                        ),
                        "sha256": hashlib.sha256(
                            (
                                ROOT
                                / "families/mew-note-tc/sources/"
                                "imagegen/pipelines/original-raster-v1/"
                                "collections/vertical-93/batches/"
                                "vertical-0002"
                                / handedness.RECORD_NAME
                            ).read_bytes()
                        ).hexdigest(),
                    },
                }
            ],
        }
    ]


def test_rollback_to_7aee_cannot_cross_release_generations() -> None:
    predecessor, candidate, batches, release_deviation = (
        _valid_61cf_transition()
    )

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="latest transition predecessor",
    ):
        approval._validate_linear_transition(
            predecessor,
            candidate,
            predecessor_sha256=ROLLED_BACK_SHA256,
            batches=batches,
            release_deviation=release_deviation,
            project_root=ROOT,
        )


def test_missing_orientation_ledger_cannot_admit_modified_review() -> None:
    predecessor, candidate, batches, release_deviation = (
        _valid_61cf_transition()
    )
    for batch in batches:
        if (
            batch.collection_id,
            batch.batch_id,
        ) == ("vertical-93", "vertical-0002"):
            batch.corrections = tuple(
                correction
                for correction in batch.corrections
                if correction.stage != "orientation"
            )

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="changed without current correction provenance",
    ):
        approval._validate_linear_transition(
            predecessor,
            candidate,
            predecessor_sha256=PREDECESSOR_SHA256,
            batches=batches,
            release_deviation=release_deviation,
            project_root=ROOT,
        )


def test_unsanctioned_batch_delta_fails_closed() -> None:
    predecessor, candidate, batches, release_deviation = (
        _valid_61cf_transition()
    )
    candidate["reviewed_batches"][0]["review"]["sha256"] = "0" * 64

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="changed without current correction provenance",
    ):
        approval._validate_linear_transition(
            predecessor,
            candidate,
            predecessor_sha256=PREDECESSOR_SHA256,
            batches=batches,
            release_deviation=release_deviation,
            project_root=ROOT,
        )


def test_missing_canonical_approval_is_never_created(
    tmp_path: Path,
) -> None:
    path = tmp_path / "approval.json"
    validator_called = False

    def validate() -> None:
        nonlocal validator_called
        validator_called = True

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="missing",
    ):
        approval._install_validated_approval(
            path,
            {"new": True},
            trusted_root=tmp_path,
            required_predecessor_sha256="0" * 64,
            validate_transition=lambda _payload, _sha256: None,
            validate=validate,
        )
    assert not path.exists()
    assert validator_called is False


def test_symlinked_canonical_approval_is_rejected(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.json"
    target.write_text('{"decision":"APPROVED"}\n', encoding="utf-8")
    canonical = tmp_path / approval.APPROVAL_RELATIVE
    canonical.parent.mkdir(parents=True)
    canonical.symlink_to(target)

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="regular non-symlink",
    ):
        approval.validate_approval(project_root=tmp_path)


def test_symlinked_approval_parent_is_rejected(
    tmp_path: Path,
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(real, target_is_directory=True)
    path = link / "approval.json"
    path.write_text('{"old":true}\n', encoding="utf-8")

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="parent must be a non-symlink directory",
    ):
        approval._required_predecessor_bytes(
            path,
            trusted_root=tmp_path,
            required_predecessor_sha256=hashlib.sha256(
                path.read_bytes()
            ).hexdigest(),
        )


class _InventoryContext:
    def __init__(self, root: Path) -> None:
        self.project_root = root
        self.source_root = root / "sources"
        self.pipeline_id = "original-raster-v1"

    def batch_paths(
        self,
        collection_id: str,
        batch_id: str,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            source=(
                self.source_root
                / "pipelines"
                / self.pipeline_id
                / "collections"
                / collection_id
                / "batches"
                / batch_id
            )
        )


def test_foreign_orientation_ledger_is_rejected(
    tmp_path: Path,
) -> None:
    context = _InventoryContext(tmp_path)
    foreign = (
        context.batch_paths("nonhan-3060", "nonhan-0001").source
        / "post-review-vertical-orientation-correction.json"
    )
    foreign.parent.mkdir(parents=True)
    foreign.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="outside its canonical batch",
    ):
        approval._validate_correction_ledger_inventory(context)


def test_outer_correction_parse_rejects_duplicate_keys(
    tmp_path: Path,
) -> None:
    context = _InventoryContext(tmp_path)
    canonical = (
        context.batch_paths("vertical-93", "vertical-0002").source
        / "post-review-vertical-orientation-correction.json"
    )
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        '{"reason":"a","reason":"b"}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="duplicate JSON object key",
    ):
        approval._validate_correction_ledger_inventory(context)


def test_deviation_cannot_expand_into_plan_scope() -> None:
    predecessor, candidate, batches, release_deviation = (
        _valid_61cf_transition()
    )
    candidate["plan"]["encoded_count"] += 1

    with pytest.raises(
        approval.MewNoteReleaseApprovalError,
        match="immutable plan",
    ):
        approval._validate_linear_transition(
            predecessor,
            candidate,
            predecessor_sha256=PREDECESSOR_SHA256,
            batches=batches,
            release_deviation=release_deviation,
            project_root=ROOT,
        )
