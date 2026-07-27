#!/usr/bin/env python3
"""Authorize and validate the Mew Note TC 0.1 preview.

Generation evidence is immutable and remains governed by
``mew_note_batch_evidence.py``. This independent module validates every
admitted source/review/vector chain and the one 17-codepoint semantic-empty
batch without changing generation evidence. Two atomic Han batches are
withheld because their frozen identity catalog cannot prove one scalar in
each; the approval records those exclusions explicitly.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any, Callable, Iterator, Mapping, Sequence

from fontTools.ttLib import TTFont

from scripts.font_family_context import FamilyContext, sha256_path
from scripts import mew_note_batch_evidence as evidence
from scripts import mew_note_bulk_pipeline as bulk
from scripts import mew_note_history_amendment as amendment
from scripts import mew_note_post_review_correction as correction
from scripts import (
    mew_note_post_review_vertical_orientation_correction
    as orientation_correction
)
from scripts import (
    mew_note_post_review_vertical_handedness_correction
    as handedness_correction
)
from scripts import mew_note_release_deviation as deviation


ROOT = Path(__file__).resolve().parents[1]
APPROVAL_RELATIVE = Path(
    "families/mew-note-tc/approvals/"
    "original-raster-v1-preview.approval.json"
)
APPROVAL_HISTORY_RELATIVE = Path(
    "families/mew-note-tc/approvals/history"
)
PLAN_RELATIVE = bulk.PLAN_PATH
FAMILY_ID = "mew-note-tc"
PIPELINE_ID = "original-raster-v1"
PLANNED_VISIBLE_BATCH_COUNT = 590
PLANNED_ENCODED_COUNT = 9_120
WITHHELD_BATCHES: Mapping[tuple[str, str], str] = {
    ("han-6060", "han-0304"): "U+25CD1",
    ("han-6060", "han-0319"): "U+3473",
}
VISIBLE_BATCH_COUNT = 588
ENCODED_COUNT = 9_088
HAN_COUNT = 6_028
NONHAN_COUNT = 3_060
SEMANTIC_EMPTY_COUNT = 17
VERTICAL_COUNT = 93
APPROVAL_CONFIRMATION = (
    "I_AUTHORIZE_ALL_REVIEWED_MEW_NOTE_GLYPHS_FOR_0_1_PREVIEW"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


class MewNoteReleaseApprovalError(RuntimeError):
    """The Mew Note release review chain is incomplete or has drifted."""


@dataclass(frozen=True)
class ReleaseCorrectionSpec:
    """One ordered, batch-local release correction transition."""

    stage: str
    order: int
    approval_field: str
    record_name: str
    reason: str
    predecessor_schema: str
    prior_evidence_keys: frozenset[str]
    canonical_targets: frozenset[tuple[str, str]] | None
    validate_record: Callable[
        [FamilyContext, str, str], Mapping[str, Any]
    ]


@dataclass(frozen=True)
class ApprovedBatchCorrection:
    """One validated correction ledger attached to an admitted batch."""

    stage: str
    order: int
    approval_field: str
    reason: str
    path: Path
    sha256: str
    predecessor_approval_sha256: str


@dataclass(frozen=True)
class TransitionAuditContext:
    """The exact predecessor and active stage for one reapproval."""

    latest_order: int
    predecessor_approval_sha256: str
    predecessor_approval: Mapping[str, Any]


def _validate_metric_correction(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Mapping[str, Any]:
    try:
        return correction.validate_correction(
            context,
            collection_id,
            batch_id,
            require_new_review=True,
        )
    except correction.MewNotePostReviewCorrectionError as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc


def _validate_orientation_correction(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Mapping[str, Any]:
    if (collection_id, batch_id) != (
        orientation_correction.COLLECTION_ID,
        orientation_correction.BATCH_ID,
    ):
        raise MewNoteReleaseApprovalError(
            "vertical-orientation correction ledger is only valid at "
            "vertical-93/vertical-0002"
        )
    try:
        return orientation_correction.validate_correction(
            context,
            require_new_review=True,
            require_reapproval=False,
        )
    except (
        orientation_correction.MewNoteVerticalOrientationCorrectionError
    ) as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc


def _validate_handedness_correction(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Mapping[str, Any]:
    if (collection_id, batch_id) != (
        handedness_correction.COLLECTION_ID,
        handedness_correction.BATCH_ID,
    ):
        raise MewNoteReleaseApprovalError(
            "vertical-handedness correction ledger is only valid at "
            "vertical-93/vertical-0002"
        )
    try:
        return handedness_correction.validate_correction(
            context,
            require_new_review=True,
            require_reapproval=False,
        )
    except (
        handedness_correction.MewNoteVerticalHandednessCorrectionError
    ) as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc


FLAT_PREDECESSOR_SCHEMA = "flat-canonical-hash"
SNAPSHOT_PREDECESSOR_SCHEMA = "immutable-snapshot-canonical-target"


# Ordered extension point for future release corrections. A new correction
# appends one spec with a strictly larger order; the generic approval and
# supersession code below needs no new per-correction branches.
CORRECTION_TRANSITION_SPECS: tuple[ReleaseCorrectionSpec, ...] = (
    ReleaseCorrectionSpec(
        stage="metric",
        order=10,
        approval_field="post_review_correction",
        record_name=correction.RECORD_NAME,
        reason=correction.REASON,
        predecessor_schema=FLAT_PREDECESSOR_SCHEMA,
        prior_evidence_keys=frozenset(
            {
                "history",
                "source",
                "raster",
                "review",
                "release_approval",
                "vector_report",
                "vector_ttf",
            }
        ),
        canonical_targets=None,
        validate_record=_validate_metric_correction,
    ),
    ReleaseCorrectionSpec(
        stage="orientation",
        order=30,
        approval_field=(
            "post_review_vertical_orientation_correction"
        ),
        record_name=orientation_correction.RECORD_NAME,
        reason=orientation_correction.REASON,
        predecessor_schema=FLAT_PREDECESSOR_SCHEMA,
        prior_evidence_keys=frozenset(
            {
                "history",
                "source",
                "raster",
                "review",
                "release_approval",
                "build",
            }
        ),
        canonical_targets=frozenset(
            {
                (
                    orientation_correction.COLLECTION_ID,
                    orientation_correction.BATCH_ID,
                )
            }
        ),
        validate_record=_validate_orientation_correction,
    ),
    ReleaseCorrectionSpec(
        stage="handedness",
        order=40,
        approval_field=handedness_correction.APPROVAL_FIELD,
        record_name=handedness_correction.RECORD_NAME,
        reason=handedness_correction.REASON,
        predecessor_schema=SNAPSHOT_PREDECESSOR_SCHEMA,
        prior_evidence_keys=frozenset(
            {
                "vertical_orientation_correction",
                "history",
                "source",
                "raster",
                "review",
                "release_approval",
                "build",
            }
        ),
        canonical_targets=frozenset(
            {
                (
                    handedness_correction.COLLECTION_ID,
                    handedness_correction.BATCH_ID,
                )
            }
        ),
        validate_record=_validate_handedness_correction,
    ),
)
DEVIATION_TRANSITION_ORDER = 20


def _validate_transition_spec_registry() -> None:
    orders = [spec.order for spec in CORRECTION_TRANSITION_SPECS]
    stages = [spec.stage for spec in CORRECTION_TRANSITION_SPECS]
    fields = [
        spec.approval_field for spec in CORRECTION_TRANSITION_SPECS
    ]
    record_names = [
        spec.record_name for spec in CORRECTION_TRANSITION_SPECS
    ]
    if (
        orders != sorted(orders)
        or len(set(orders)) != len(orders)
        or DEVIATION_TRANSITION_ORDER in orders
        or len(set(stages)) != len(stages)
        or len(set(fields)) != len(fields)
        or len(set(record_names)) != len(record_names)
        or any(
            spec.predecessor_schema
            not in {
                FLAT_PREDECESSOR_SCHEMA,
                SNAPSHOT_PREDECESSOR_SCHEMA,
            }
            for spec in CORRECTION_TRANSITION_SPECS
        )
        or any(
            "release_approval" not in spec.prior_evidence_keys
            for spec in CORRECTION_TRANSITION_SPECS
        )
    ):
        raise MewNoteReleaseApprovalError(
            "release correction transition registry is not strictly "
            "ordered and unique"
        )


@dataclass(frozen=True)
class ApprovedVisibleBatch:
    """One visible batch admitted through an independent technical review."""

    collection_id: str
    batch_id: str
    entries: tuple[Mapping[str, Any], ...]
    review_path: Path
    review_sha256: str
    source_path: Path
    source_sha256: str
    raster_path: Path
    raster_sha256: str
    report_path: Path
    report_sha256: str
    ttf_path: Path
    ttf_sha256: str
    amendments_path: Path | None
    amendments_sha256: str | None
    corrections: tuple[ApprovedBatchCorrection, ...]
    reviewer_name: str


@dataclass(frozen=True)
class ApprovedMewNoteRelease:
    """The complete Mew Note TC release admission set."""

    approval_path: Path
    approval_sha256: str
    release_deviation_path: Path
    release_deviation_sha256: str
    plan_path: Path
    plan_sha256: str
    approver_name: str
    approved_at: str
    visible_batches: tuple[ApprovedVisibleBatch, ...]
    withheld_entries: tuple[Mapping[str, Any], ...]
    semantic_empty_entries: tuple[Mapping[str, Any], ...]

    @property
    def encoded_entries(self) -> tuple[Mapping[str, Any], ...]:
        visible = tuple(
            entry
            for batch in self.visible_batches
            if batch.collection_id in {"han-6060", "nonhan-3060"}
            for entry in batch.entries
        )
        return visible + self.semantic_empty_entries

    @property
    def vertical_batches(self) -> tuple[ApprovedVisibleBatch, ...]:
        return tuple(
            batch
            for batch in self.visible_batches
            if batch.collection_id == "vertical-93"
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise MewNoteReleaseApprovalError(
                f"duplicate JSON object key {key!r}"
            )
        value[key] = item
    return value


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise MewNoteReleaseApprovalError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    return _decode_object(data, label=f"{path}: {label}")


def _decode_object(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except MewNoteReleaseApprovalError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteReleaseApprovalError(
            f"{label}: cannot decode JSON object: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MewNoteReleaseApprovalError(
            f"{label}: must be an object"
        )
    return value


def _exact_object_keys(
    value: Any,
    expected: set[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise MewNoteReleaseApprovalError(
            f"{label}: expected an object"
        )
    actual = set(value)
    if actual != expected:
        raise MewNoteReleaseApprovalError(
            f"{label}: key drift; "
            f"unknown={sorted(actual - expected)}, "
            f"missing={sorted(expected - actual)}"
        )
    return value


def _regular_file(path: Path, *, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MewNoteReleaseApprovalError(
            f"{label}: missing {path}"
        ) from exc
    if path.is_symlink() or not resolved.is_file():
        raise MewNoteReleaseApprovalError(
            f"{label}: expected a regular non-symlink file"
        )
    return resolved


def _safe_existing_regular_file(
    path: Path,
    *,
    trusted_root: Path,
    label: str,
) -> Path:
    """Require an existing regular file below non-symlink directories."""

    root = trusted_root.resolve(strict=True)
    candidate = _lexical_absolute(path)
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise MewNoteReleaseApprovalError(
            f"{label}: path escapes trusted root"
        ) from exc
    cursor = root
    try:
        root_mode = cursor.lstat().st_mode
    except OSError as exc:
        raise MewNoteReleaseApprovalError(
            f"{label}: cannot inspect trusted root {root}"
        ) from exc
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise MewNoteReleaseApprovalError(
            f"{label}: trusted root must be a non-symlink directory"
        )
    for part in relative.parts[:-1]:
        cursor = cursor / part
        try:
            mode = cursor.lstat().st_mode
        except OSError as exc:
            raise MewNoteReleaseApprovalError(
                f"{label}: missing parent directory {cursor}"
            ) from exc
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise MewNoteReleaseApprovalError(
                f"{label}: parent must be a non-symlink directory: "
                f"{cursor}"
            )
    try:
        mode = candidate.lstat().st_mode
    except OSError as exc:
        raise MewNoteReleaseApprovalError(
            f"{label}: missing {candidate}"
        ) from exc
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise MewNoteReleaseApprovalError(
            f"{label}: expected a regular non-symlink file"
        )
    return candidate


def _relative(path: Path, *, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError as exc:
        raise MewNoteReleaseApprovalError(
            f"path escapes repository: {path}"
        ) from exc


def _pin(path: Path, *, project_root: Path) -> dict[str, str]:
    path = _regular_file(path, label="pinned evidence")
    return {
        "path": _relative(path, project_root=project_root),
        "sha256": sha256_path(path),
    }


def _timestamp(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise MewNoteReleaseApprovalError(
            f"{label}: invalid UTC timestamp"
        )
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise MewNoteReleaseApprovalError(
            f"{label}: invalid UTC timestamp"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise MewNoteReleaseApprovalError(
            f"{label}: noncanonical UTC timestamp"
        )
    return value


def _person(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise MewNoteReleaseApprovalError(f"{label}: invalid person name")
    return value


def _sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or SHA256_PATTERN.fullmatch(value) is None
    ):
        raise MewNoteReleaseApprovalError(
            f"{label}: invalid SHA-256"
        )
    return value


def _load_plan(
    project_root: Path,
) -> tuple[FamilyContext, Path, dict[str, Any]]:
    try:
        context = bulk.load_context(project_root)
    except bulk.MewNoteBulkError as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc
    plan_path = _regular_file(
        project_root / PLAN_RELATIVE,
        label="Mew Note batch plan",
    )
    plan = _read_object(plan_path, label="Mew Note batch plan")
    try:
        bulk.validate_plan_payload(plan, context=context)
    except bulk.MewNoteBulkError as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc
    return context, plan_path, plan


def _batch_root(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Path:
    paths = context.batch_paths(collection_id, batch_id)
    return paths.source


def _lexical_absolute(path: Path) -> Path:
    """Normalize ``.``/``..`` without following the final symlink."""

    return Path(os.path.abspath(path))


def _validate_correction_ledger_inventory(
    context: FamilyContext,
) -> None:
    """Reject misplaced ledgers and duplicate-key JSON before delegation."""

    _validate_transition_spec_registry()
    collections_root = (
        context.source_root
        / "pipelines"
        / context.pipeline_id
        / "collections"
    )
    for spec in CORRECTION_TRANSITION_SPECS:
        found = tuple(
            sorted(
                collections_root.glob(
                    f"*/batches/*/{spec.record_name}"
                )
            )
        )
        if spec.canonical_targets is not None:
            expected = {
                _lexical_absolute(
                    context.batch_paths(
                        collection_id, batch_id
                    ).source
                    / spec.record_name
                )
                for collection_id, batch_id in spec.canonical_targets
            }
            foreign = [
                path
                for path in found
                if _lexical_absolute(path) not in expected
            ]
            if foreign:
                raise MewNoteReleaseApprovalError(
                    f"{spec.stage} correction ledger is outside its "
                    f"canonical batch: {foreign[0]}"
                )
        for path in found:
            regular = _regular_file(
                path,
                label=f"{spec.stage} correction ledger",
            )
            _read_object(
                regular,
                label=f"{spec.stage} correction ledger",
            )


def _correction_predecessor_sha256(
    spec: ReleaseCorrectionSpec,
    record: Mapping[str, Any],
    *,
    project_root: Path,
) -> str:
    """Extract one predecessor only from a fully specified exact schema."""

    try:
        prior = _exact_object_keys(
            record["prior_evidence"],
            set(spec.prior_evidence_keys),
            label=f"{spec.stage} prior evidence",
        )
        release_approval = prior["release_approval"]
    except KeyError as exc:
        raise MewNoteReleaseApprovalError(
            f"{spec.stage} correction lacks release-approval provenance"
        ) from exc

    if spec.predecessor_schema == FLAT_PREDECESSOR_SCHEMA:
        flat = _exact_object_keys(
            release_approval,
            {"path", "sha256", "retention"},
            label=f"{spec.stage} predecessor approval",
        )
        digest = _sha256(
            flat.get("sha256"),
            label=f"{spec.stage} predecessor approval hash",
        )
        if (
            flat.get("path") != APPROVAL_RELATIVE.as_posix()
            or flat.get("retention")
            != "hash-only-superseded-after-reapproval"
        ):
            raise MewNoteReleaseApprovalError(
                f"{spec.stage} predecessor approval schema drift"
            )
        return digest

    if spec.predecessor_schema != SNAPSHOT_PREDECESSOR_SCHEMA:
        raise MewNoteReleaseApprovalError(
            f"{spec.stage} predecessor schema is unsupported"
        )
    nested = _exact_object_keys(
        release_approval,
        {"immutable_snapshot", "canonical_overwrite_target"},
        label=f"{spec.stage} predecessor approval",
    )
    snapshot = _exact_object_keys(
        nested.get("immutable_snapshot"),
        {"path", "sha256", "retention"},
        label=f"{spec.stage} immutable predecessor snapshot",
    )
    canonical = _exact_object_keys(
        nested.get("canonical_overwrite_target"),
        {"path", "sha256", "retention"},
        label=f"{spec.stage} canonical overwrite target",
    )
    digest = _sha256(
        canonical.get("sha256"),
        label=f"{spec.stage} canonical overwrite target hash",
    )
    expected_snapshot_relative = (
        APPROVAL_HISTORY_RELATIVE / f"{digest}.approval.json"
    ).as_posix()
    if (
        canonical.get("path") != APPROVAL_RELATIVE.as_posix()
        or canonical.get("retention") != "canonical-overwrite-target"
        or snapshot.get("path") != expected_snapshot_relative
        or snapshot.get("sha256") != digest
        or snapshot.get("retention")
        != "immutable-release-approval-snapshot"
    ):
        raise MewNoteReleaseApprovalError(
            f"{spec.stage} nested predecessor approval schema drift"
        )
    snapshot_path = _safe_existing_regular_file(
        project_root / expected_snapshot_relative,
        trusted_root=project_root,
        label=f"{spec.stage} immutable predecessor snapshot",
    )
    if sha256_path(snapshot_path) != digest:
        raise MewNoteReleaseApprovalError(
            f"{snapshot_path}: immutable predecessor snapshot hash drift"
        )
    _read_object(
        snapshot_path,
        label=f"{spec.stage} immutable predecessor snapshot",
    )
    return digest


def _validate_historical_correction_admission(
    predecessor_approval: Mapping[str, Any],
    *,
    spec: ReleaseCorrectionSpec,
    collection_id: str,
    batch_id: str,
    path: Path,
    ledger_predecessor_sha256: str,
    project_root: Path,
) -> None:
    """Prove an older correction was admitted by the exact predecessor."""

    pin = _pin(path, project_root=project_root)
    reviewed = predecessor_approval.get("reviewed_batches")
    matching_reviewed = [
        item
        for item in reviewed
        if isinstance(item, dict)
        and item.get("collection_id") == collection_id
        and item.get("batch_id") == batch_id
    ] if isinstance(reviewed, list) else []
    if (
        len(matching_reviewed) != 1
        or matching_reviewed[0].get(spec.approval_field) != pin
    ):
        raise MewNoteReleaseApprovalError(
            f"{collection_id}/{batch_id}: predecessor approval does not "
            f"admit the exact historical {spec.stage} ledger"
        )

    supersedes = predecessor_approval.get("supersedes")
    matching_supersedes = [
        item
        for item in supersedes
        if isinstance(item, dict)
        and item.get("release_approval_sha256")
        == ledger_predecessor_sha256
        and item.get("reason") == spec.reason
    ] if isinstance(supersedes, list) else []
    expected_batch = {
        "collection_id": collection_id,
        "batch_id": batch_id,
        spec.approval_field: pin,
    }
    if (
        len(matching_supersedes) != 1
        or not isinstance(
            matching_supersedes[0].get("corrected_batches"),
            list,
        )
        or matching_supersedes[0]["corrected_batches"].count(
            expected_batch
        )
        != 1
    ):
        raise MewNoteReleaseApprovalError(
            f"{collection_id}/{batch_id}: predecessor approval lacks "
            f"exact historical {spec.stage} supersession"
        )


def _discover_transition_audit(
    context: FamilyContext,
    *,
    release_deviation: Any,
) -> TransitionAuditContext:
    """Validate active ledgers and bind older ones to the exact predecessor."""

    stages: list[tuple[int, str]] = [
        (
            DEVIATION_TRANSITION_ORDER,
            _sha256(
                release_deviation.required_overwrite_predecessor_sha256,
                label="release-deviation predecessor",
            ),
        )
    ]
    collections_root = (
        context.source_root
        / "pipelines"
        / context.pipeline_id
        / "collections"
    )
    discovered: list[
        tuple[
            ReleaseCorrectionSpec,
            Path,
            Mapping[str, Any],
            str,
            str,
            str,
        ]
    ] = []
    for spec in CORRECTION_TRANSITION_SPECS:
        for path in sorted(
            collections_root.glob(
                f"*/batches/*/{spec.record_name}"
            )
        ):
            ledger = _read_object(
                _regular_file(
                    path,
                    label=f"{spec.stage} correction ledger",
                ),
                label=f"{spec.stage} correction ledger",
            )
            try:
                collection_id = str(ledger["collection_id"])
                batch_id = str(ledger["batch_id"])
            except KeyError as exc:
                raise MewNoteReleaseApprovalError(
                    f"{path}: missing correction batch identity"
                ) from exc
            if _lexical_absolute(path) != _lexical_absolute(
                context.batch_paths(
                    collection_id,
                    batch_id,
                ).source
                / spec.record_name
            ):
                raise MewNoteReleaseApprovalError(
                    f"{path}: correction batch path/identity mismatch"
                )
            predecessor = _correction_predecessor_sha256(
                spec,
                ledger,
                project_root=context.project_root,
            )
            stages.append((spec.order, predecessor))
            discovered.append(
                (
                    spec,
                    path,
                    ledger,
                    collection_id,
                    batch_id,
                    predecessor,
                )
            )
    latest_order = max(order for order, _digest in stages)
    latest = {
        digest for order, digest in stages if order == latest_order
    }
    if len(latest) != 1:
        raise MewNoteReleaseApprovalError(
            "latest correction stage names multiple approval predecessors"
        )
    predecessor_sha256 = next(iter(latest))
    predecessor_approval = _predecessor_snapshot(
        project_root=context.project_root,
        predecessor_sha256=predecessor_sha256,
    )
    for (
        spec,
        path,
        _ledger,
        collection_id,
        batch_id,
        ledger_predecessor,
    ) in discovered:
        if spec.order == latest_order:
            validated = spec.validate_record(
                context,
                collection_id,
                batch_id,
            )
            validated_predecessor = _correction_predecessor_sha256(
                spec,
                validated,
                project_root=context.project_root,
            )
            if validated_predecessor != predecessor_sha256:
                raise MewNoteReleaseApprovalError(
                    f"{path}: active correction names the wrong "
                    "approval predecessor"
                )
        else:
            _validate_historical_correction_admission(
                predecessor_approval,
                spec=spec,
                collection_id=collection_id,
                batch_id=batch_id,
                path=path,
                ledger_predecessor_sha256=ledger_predecessor,
                project_root=context.project_root,
            )
    return TransitionAuditContext(
        latest_order=latest_order,
        predecessor_approval_sha256=predecessor_sha256,
        predecessor_approval=predecessor_approval,
    )


def _validated_batch_corrections(
    context: FamilyContext,
    collection_id: str,
    batch_id: str,
    root: Path,
    *,
    transition_audit: TransitionAuditContext,
) -> tuple[ApprovedBatchCorrection, ...]:
    """Validate every ledger attached to one batch in transition order."""

    result: list[ApprovedBatchCorrection] = []
    for spec in CORRECTION_TRANSITION_SPECS:
        path = root / spec.record_name
        if not path.exists():
            continue
        if (
            spec.canonical_targets is not None
            and (collection_id, batch_id)
            not in spec.canonical_targets
        ):
            raise MewNoteReleaseApprovalError(
                f"{spec.stage} correction ledger is outside its "
                "canonical batch"
            )
        path = _regular_file(
            path,
            label=f"{spec.stage} correction ledger",
        )
        # The correction modules are self-pinned and intentionally untouched.
        # Parse here first so their legacy JSON readers cannot accept
        # duplicate object keys.
        _read_object(path, label=f"{spec.stage} correction ledger")
        if spec.order == transition_audit.latest_order:
            record = spec.validate_record(
                context,
                collection_id,
                batch_id,
            )
        else:
            record = _read_object(
                path,
                label=f"historical {spec.stage} correction ledger",
            )
        predecessor = _correction_predecessor_sha256(
            spec,
            record,
            project_root=context.project_root,
        )
        if spec.order == transition_audit.latest_order:
            if (
                predecessor
                != transition_audit.predecessor_approval_sha256
            ):
                raise MewNoteReleaseApprovalError(
                    f"{path}: active correction names the wrong "
                    "approval predecessor"
                )
        else:
            _validate_historical_correction_admission(
                transition_audit.predecessor_approval,
                spec=spec,
                collection_id=collection_id,
                batch_id=batch_id,
                path=path,
                ledger_predecessor_sha256=predecessor,
                project_root=context.project_root,
            )
        result.append(
            ApprovedBatchCorrection(
                stage=spec.stage,
                order=spec.order,
                approval_field=spec.approval_field,
                reason=spec.reason,
                path=path,
                sha256=sha256_path(path),
                predecessor_approval_sha256=predecessor,
            )
        )
    return tuple(result)


def _glyph_name(codepoint: int) -> str:
    return (
        f"uni{codepoint:04X}"
        if codepoint <= 0xFFFF
        else f"u{codepoint:05X}"
    )


def _vector_evidence(
    context: FamilyContext,
    batch: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    Path,
    str,
    Path,
    str,
]:
    collection_id = str(batch["collection_id"])
    batch_id = str(batch["batch_id"])
    paths = context.batch_paths(collection_id, batch_id)
    report_path = _regular_file(
        paths.build / "report.json",
        label=f"{collection_id}/{batch_id} vector report",
    )
    report = _read_object(report_path, label="vector report")
    entries = batch["entries"]
    source_path = paths.source / "source.json"
    raster_path = paths.source / "raster.png"
    expected_characters = [str(entry["character"]) for entry in entries]
    if (
        report.get("schema_version") != 1
        or report.get("pipeline")
        != "imagegen-raster-potrace-quadratic-v2"
        or report.get("approval_state") != "unreviewed"
        or report.get("batch_id") != batch_id
        or report.get("source_descriptor_sha256")
        != sha256_path(source_path)
        or report.get("source_raster_sha256")
        != sha256_path(raster_path)
        or report.get("characters") != expected_characters
    ):
        raise MewNoteReleaseApprovalError(
            f"{report_path}: vector identity drift"
        )
    glyphs = report.get("glyphs")
    coverage = report.get("small_size_coverage_pixels")
    if (
        not isinstance(glyphs, list)
        or len(glyphs) != len(entries)
        or not isinstance(coverage, dict)
    ):
        raise MewNoteReleaseApprovalError(
            f"{report_path}: vector QA is incomplete"
        )
    for entry, glyph in zip(entries, glyphs, strict=True):
        codepoint = str(entry["codepoint"])
        pixels = coverage.get(codepoint)
        if (
            not isinstance(glyph, dict)
            or glyph.get("character") != entry["character"]
            or glyph.get("codepoint") != codepoint
            or glyph.get("micro_edge_count") != 0
            or glyph.get("acute_micro_turn_count") != 0
            or glyph.get("contour_count", 0) <= 0
            or glyph.get("point_count", 0) <= 0
            or not isinstance(pixels, dict)
            or set(pixels) != {"12", "16", "20", "32", "56"}
            or any(
                not isinstance(value, int) or value <= 0
                for value in pixels.values()
            )
        ):
            raise MewNoteReleaseApprovalError(
                f"{report_path}: {codepoint} failed vector QA"
            )
    font_record = report.get("font")
    if (
        not isinstance(font_record, dict)
        or font_record.get("cmap_count") != len(entries)
        or not isinstance(font_record.get("ttf"), str)
    ):
        raise MewNoteReleaseApprovalError(
            f"{report_path}: vector font record drift"
        )
    ttf_path = _regular_file(
        paths.build / str(font_record["ttf"]),
        label=f"{collection_id}/{batch_id} vector TTF",
    )
    ttf_sha256 = sha256_path(ttf_path)
    if ttf_sha256 != font_record.get("ttf_sha256"):
        raise MewNoteReleaseApprovalError(f"{ttf_path}: TTF hash drift")
    expected_cmap = {
        int(str(entry["codepoint"])[2:], 16): _glyph_name(
            int(str(entry["codepoint"])[2:], 16)
        )
        for entry in entries
    }
    with TTFont(ttf_path, lazy=False, checkChecksums=2) as font:
        if font.getBestCmap() != expected_cmap:
            raise MewNoteReleaseApprovalError(f"{ttf_path}: cmap drift")
        for glyph_name in expected_cmap.values():
            outline = font["glyf"][glyph_name]
            if outline.isComposite() or outline.numberOfContours <= 0:
                raise MewNoteReleaseApprovalError(
                    f"{ttf_path}: {glyph_name} is empty or composite"
                )
    proofs = report.get("proofs")
    if not isinstance(proofs, dict) or set(proofs) != {
        "black_on_white",
        "white_on_black",
        "segmented_source",
    }:
        raise MewNoteReleaseApprovalError(
            f"{report_path}: proof inventory drift"
        )
    proof_pins: dict[str, dict[str, str]] = {}
    for key in ("black_on_white", "white_on_black", "segmented_source"):
        relative = proofs[key]
        if not isinstance(relative, str):
            raise MewNoteReleaseApprovalError(
                f"{report_path}: invalid {key} proof path"
            )
        proof_pins[key] = _pin(
            paths.build / relative,
            project_root=context.project_root,
        )
    return (
        {
            "report": _pin(
                report_path, project_root=context.project_root
            ),
            "black_on_white": proof_pins["black_on_white"],
            "white_on_black": proof_pins["white_on_black"],
            "segmented_source": proof_pins["segmented_source"],
            "glyph_count": len(glyphs),
            "micro_edge_count": 0,
            "acute_micro_turn_count": 0,
        },
        report_path,
        sha256_path(report_path),
        ttf_path,
        ttf_sha256,
    )


def _validate_cells(
    batch: Mapping[str, Any],
    value: Any,
) -> None:
    if not isinstance(value, list) or len(value) != len(batch["entries"]):
        raise MewNoteReleaseApprovalError(
            f"{batch['batch_id']}: review cell count drift"
        )
    required = {
        "cell",
        "character",
        "codepoint",
        "identity",
        "topology",
        "motif_assignment",
        "tail_attachment",
        "grid_clearance",
        "spikes",
        "legibility_16px",
        "decision",
        "notes",
    }
    for expected, actual in zip(batch["entries"], value, strict=True):
        if (
            not isinstance(actual, dict)
            or set(actual) != required
            or actual["cell"] != expected["cell"]
            or actual["character"] != expected["character"]
            or actual["codepoint"] != expected["codepoint"]
            or actual["decision"] != "ACCEPT"
            or any(
                actual[key] != "PASS"
                for key in (
                    "identity",
                    "topology",
                    "motif_assignment",
                    "grid_clearance",
                    "spikes",
                    "legibility_16px",
                )
            )
            or actual["tail_attachment"]
            != (
                "PASS"
                if expected["motif_class"] == "tail-terminal"
                else "NOT_APPLICABLE"
            )
            or not isinstance(actual["notes"], str)
            or not actual["notes"].strip()
        ):
            raise MewNoteReleaseApprovalError(
                f"{batch['batch_id']}: technical review gate failed"
            )


def validate_batch_review(
    context: FamilyContext,
    batch: Mapping[str, Any],
    *,
    transition_audit: TransitionAuditContext,
) -> ApprovedVisibleBatch:
    """Validate one family-local technical review without mutating evidence."""

    collection_id = str(batch["collection_id"])
    batch_id = str(batch["batch_id"])
    if batch.get("materialization_kind") != "visible-raster":
        raise MewNoteReleaseApprovalError(
            f"{collection_id}/{batch_id}: expected a visible batch"
        )
    try:
        generated_evidence = evidence.build_vector_batch(
            context,
            collection_id,
            batch_id,
        )
    except evidence.MewNoteBatchError as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc
    root = _batch_root(context, collection_id, batch_id)
    corrections = _validated_batch_corrections(
        context,
        collection_id,
        batch_id,
        root,
        transition_audit=transition_audit,
    )
    amendments_path = root / "amendments.json"
    if amendments_path.exists():
        try:
            amendment.validate_amendments(
                context,
                collection_id,
                batch_id,
            )
        except amendment.MewNoteAmendmentError as exc:
            raise MewNoteReleaseApprovalError(str(exc)) from exc
        amendments_sha256: str | None = sha256_path(amendments_path)
    else:
        amendments_path = None
        amendments_sha256 = None
    source_path = root / "source.json"
    raster_path = root / "raster.png"
    source = _read_object(source_path, label="generated source")
    review_path = _regular_file(
        root / "review.json",
        label=f"{collection_id}/{batch_id} technical review",
    )
    review = _read_object(review_path, label="technical review")
    expected_keys = {
        "schema_version",
        "record_type",
        "family_id",
        "pipeline_id",
        "collection_id",
        "batch_id",
        "family_context",
        "batch_contract_sha256",
        "source",
        "evidence",
        "reviewer",
        "cells",
        "decision",
        "release_approval",
    }
    if (
        set(review) != expected_keys
        or review.get("schema_version") != 1
        or review.get("record_type")
        != evidence.REVIEW_RECORD_TYPE
        or review.get("family_id") != FAMILY_ID
        or review.get("pipeline_id") != PIPELINE_ID
        or review.get("collection_id") != collection_id
        or review.get("batch_id") != batch_id
        or review.get("family_context")
        != context.evidence_binding(collection_id)
        or review.get("batch_contract_sha256")
        != batch["batch_contract_sha256"]
        or review.get("decision") != "ACCEPT"
        or review.get("release_approval") is not False
        or review.get("source")
        != _pin(source_path, project_root=context.project_root)
        or source.get("raster_sha256") != sha256_path(raster_path)
    ):
        raise MewNoteReleaseApprovalError(
            f"{review_path}: technical review identity drift"
        )
    (
        vector_evidence,
        report_path,
        report_sha256,
        ttf_path,
        ttf_sha256,
    ) = _vector_evidence(context, batch)
    if generated_evidence != vector_evidence:
        raise MewNoteReleaseApprovalError(
            f"{review_path}: deterministic vector rebuild drift"
        )
    if review.get("evidence") != vector_evidence:
        raise MewNoteReleaseApprovalError(
            f"{review_path}: vector/proof evidence drift"
        )
    reviewer = review.get("reviewer")
    if (
        not isinstance(reviewer, dict)
        or set(reviewer) != {
            "name",
            "role",
            "independent_from_generator",
        }
        or reviewer.get("role")
        != "independent-raster-vector-technical-review"
        or reviewer.get("independent_from_generator") is not True
    ):
        raise MewNoteReleaseApprovalError(
            f"{review_path}: invalid independent reviewer"
        )
    reviewer_name = _person(
        reviewer.get("name"), label="reviewer.name"
    )
    _validate_cells(batch, review.get("cells"))
    return ApprovedVisibleBatch(
        collection_id=collection_id,
        batch_id=batch_id,
        entries=tuple(dict(entry) for entry in batch["entries"]),
        review_path=review_path,
        review_sha256=sha256_path(review_path),
        source_path=source_path,
        source_sha256=sha256_path(source_path),
        raster_path=raster_path,
        raster_sha256=sha256_path(raster_path),
        report_path=report_path,
        report_sha256=report_sha256,
        ttf_path=ttf_path,
        ttf_sha256=ttf_sha256,
        amendments_path=amendments_path,
        amendments_sha256=amendments_sha256,
        corrections=corrections,
        reviewer_name=reviewer_name,
    )


def _approval_review_record(
    batch: ApprovedVisibleBatch,
    *,
    project_root: Path,
) -> dict[str, Any]:
    result = {
        "collection_id": batch.collection_id,
        "batch_id": batch.batch_id,
        "review": {
            "path": _relative(
                batch.review_path, project_root=project_root
            ),
            "sha256": batch.review_sha256,
        },
        "reviewer_name": batch.reviewer_name,
        "amendments": (
            None
            if batch.amendments_path is None
            else {
                "path": _relative(
                    batch.amendments_path,
                    project_root=project_root,
                ),
                "sha256": batch.amendments_sha256,
            }
        ),
        "character_count": len(batch.entries),
    }
    for transition in batch.corrections:
        result[transition.approval_field] = {
            "path": _relative(
                transition.path,
                project_root=project_root,
            ),
            "sha256": transition.sha256,
        }
    return result


def _supersedes_records(
    batches: Sequence[ApprovedVisibleBatch],
    *,
    project_root: Path,
) -> list[dict[str, Any]]:
    """Group corrected batches by the exact approval they supersede."""

    groups: dict[
        tuple[str, str],
        list[
            tuple[
                ApprovedVisibleBatch,
                ApprovedBatchCorrection,
            ]
        ],
    ] = {}
    for batch in batches:
        for transition in batch.corrections:
            digest = _sha256(
                transition.predecessor_approval_sha256,
                label="superseded release approval hash",
            )
            _sha256(
                transition.sha256,
                label=f"{transition.approval_field} hash",
            )
            groups.setdefault((digest, transition.reason), []).append(
                (batch, transition)
            )
    return [
        {
            "release_approval_sha256": digest,
            "reason": reason,
            "corrected_batches": [
                {
                    "collection_id": batch.collection_id,
                    "batch_id": batch.batch_id,
                    transition.approval_field: {
                        "path": _relative(
                            transition.path,
                            project_root=project_root,
                        ),
                        "sha256": transition.sha256,
                    },
                }
                for batch, transition in grouped
            ],
        }
        for (digest, reason), grouped in sorted(groups.items())
    ]


def _latest_transition_predecessor_sha256(
    batches: Sequence[ApprovedVisibleBatch],
    *,
    release_deviation: Any,
) -> str:
    """Return the sole predecessor authorized by the latest active stage."""

    _validate_transition_spec_registry()
    stages: list[tuple[int, str, str]] = [
        (
            DEVIATION_TRANSITION_ORDER,
            "deviation",
            _sha256(
                release_deviation.required_overwrite_predecessor_sha256,
                label="release-deviation predecessor",
            ),
        )
    ]
    for batch in batches:
        for transition in batch.corrections:
            stages.append(
                (
                    transition.order,
                    transition.stage,
                    transition.predecessor_approval_sha256,
                )
            )
    latest_order = max(order for order, _stage, _digest in stages)
    latest = {
        digest
        for order, _stage, digest in stages
        if order == latest_order
    }
    if len(latest) != 1:
        raise MewNoteReleaseApprovalError(
            "latest correction stage names multiple approval predecessors"
        )
    return next(iter(latest))


def _supersedes_key(value: Mapping[str, Any]) -> tuple[str, str]:
    try:
        digest = _sha256(
            value["release_approval_sha256"],
            label="supersedes.release_approval_sha256",
        )
        reason = value["reason"]
    except (KeyError, TypeError) as exc:
        raise MewNoteReleaseApprovalError(
            "invalid supersedes record"
        ) from exc
    if not isinstance(reason, str) or not reason:
        raise MewNoteReleaseApprovalError(
            "invalid supersedes reason"
        )
    return digest, reason


def _validate_linear_transition(
    predecessor: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    predecessor_sha256: str,
    batches: Sequence[ApprovedVisibleBatch],
    release_deviation: Any,
    project_root: Path,
) -> None:
    """Allow only the exact delta proven by current transition ledgers."""

    predecessor_sha256 = _sha256(
        predecessor_sha256,
        label="installed predecessor approval hash",
    )
    expected_predecessor = _latest_transition_predecessor_sha256(
        batches,
        release_deviation=release_deviation,
    )
    if predecessor_sha256 != expected_predecessor:
        raise MewNoteReleaseApprovalError(
            "canonical approval is not the latest transition predecessor; "
            f"expected {expected_predecessor}, got {predecessor_sha256}"
        )

    immutable_fields = (
        "schema_version",
        "record_type",
        "decision",
        "family_id",
        "pipeline_id",
        "release",
        "plan",
        "withheld_batches",
        "semantic_empty",
    )
    for field in immutable_fields:
        if predecessor.get(field) != candidate.get(field):
            raise MewNoteReleaseApprovalError(
                f"approval transition changed immutable {field}"
            )

    expected_top_keys = set(predecessor)
    deviation_is_current = (
        release_deviation.required_overwrite_predecessor_sha256
        == predecessor_sha256
    )
    expected_deviation = _pin(
        release_deviation.deviation_path,
        project_root=project_root,
    )
    if "release_deviation" in predecessor:
        if predecessor["release_deviation"] != expected_deviation:
            raise MewNoteReleaseApprovalError(
                "predecessor release-deviation pin drift"
            )
        if candidate.get("release_deviation") != predecessor[
            "release_deviation"
        ]:
            raise MewNoteReleaseApprovalError(
                "approval transition changed existing release-deviation pin"
            )
    elif deviation_is_current:
        expected_top_keys.add("release_deviation")
        if candidate.get("release_deviation") != expected_deviation:
            raise MewNoteReleaseApprovalError(
                "release-deviation transition pin drift"
            )
    elif "release_deviation" in candidate:
        raise MewNoteReleaseApprovalError(
            "release-deviation pin added outside its transition"
        )

    predecessor_reviewed = predecessor.get("reviewed_batches")
    candidate_reviewed = candidate.get("reviewed_batches")
    if (
        not isinstance(predecessor_reviewed, list)
        or not isinstance(candidate_reviewed, list)
        or len(predecessor_reviewed) != len(candidate_reviewed)
        or len(candidate_reviewed) != len(batches)
    ):
        raise MewNoteReleaseApprovalError(
            "approval transition reviewed-batch inventory drift"
        )
    current_by_batch: dict[
        tuple[str, str], tuple[ApprovedBatchCorrection, ...]
    ] = {}
    for batch in batches:
        current = tuple(
            transition
            for transition in batch.corrections
            if transition.predecessor_approval_sha256
            == predecessor_sha256
        )
        if current:
            current_by_batch[
                (batch.collection_id, batch.batch_id)
            ] = current

    used: set[tuple[str, str]] = set()
    for old, new, batch in zip(
        predecessor_reviewed,
        candidate_reviewed,
        batches,
        strict=True,
    ):
        if not isinstance(old, dict) or not isinstance(new, dict):
            raise MewNoteReleaseApprovalError(
                "approval transition batch record must be an object"
            )
        key = (batch.collection_id, batch.batch_id)
        if (
            old.get("collection_id"),
            old.get("batch_id"),
        ) != key or (
            new.get("collection_id"),
            new.get("batch_id"),
        ) != key:
            raise MewNoteReleaseApprovalError(
                "approval transition reordered or replaced a reviewed batch"
            )
        transitions = current_by_batch.get(key, ())
        if not transitions:
            if new != old:
                raise MewNoteReleaseApprovalError(
                    f"{key[0]}/{key[1]} changed without current "
                    "correction provenance"
                )
            continue

        expected = dict(old)
        old_review = _exact_object_keys(
            old.get("review"),
            {"path", "sha256"},
            label=f"{key[0]}/{key[1]} predecessor review pin",
        )
        new_review = _exact_object_keys(
            new.get("review"),
            {"path", "sha256"},
            label=f"{key[0]}/{key[1]} candidate review pin",
        )
        if (
            new_review.get("path") != old_review.get("path")
            or new_review.get("sha256") == old_review.get("sha256")
        ):
            raise MewNoteReleaseApprovalError(
                f"{key[0]}/{key[1]} correction must replace the exact "
                "review at the same path"
            )
        expected["review"] = dict(new_review)
        expected["reviewer_name"] = new.get("reviewer_name")
        for transition in transitions:
            if transition.approval_field in old:
                raise MewNoteReleaseApprovalError(
                    f"{key[0]}/{key[1]} repeats an already admitted "
                    f"{transition.stage} transition"
                )
            expected[transition.approval_field] = {
                "path": _relative(
                    transition.path,
                    project_root=project_root,
                ),
                "sha256": transition.sha256,
            }
        if new != expected:
            raise MewNoteReleaseApprovalError(
                f"{key[0]}/{key[1]} correction changed fields outside "
                "its review and ledger pins"
            )
        used.add(key)
    if used != set(current_by_batch):
        raise MewNoteReleaseApprovalError(
            "current correction transition did not change exactly its "
            "declared reviewed batches"
        )

    expected_all_supersedes = _supersedes_records(
        batches,
        project_root=project_root,
    )
    actual_supersedes = candidate.get("supersedes", [])
    old_supersedes = predecessor.get("supersedes", [])
    if (
        not isinstance(actual_supersedes, list)
        or not isinstance(old_supersedes, list)
        or actual_supersedes != expected_all_supersedes
    ):
        raise MewNoteReleaseApprovalError(
            "candidate supersedes records are not exact"
        )
    old_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for item in old_supersedes:
        if not isinstance(item, dict):
            raise MewNoteReleaseApprovalError(
                "predecessor supersedes record must be an object"
            )
        key = _supersedes_key(item)
        if key in old_by_key:
            raise MewNoteReleaseApprovalError(
                "duplicate predecessor supersedes transition"
            )
        old_by_key[key] = item
    actual_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for item in actual_supersedes:
        if not isinstance(item, dict):
            raise MewNoteReleaseApprovalError(
                "candidate supersedes record must be an object"
            )
        key = _supersedes_key(item)
        if key in actual_by_key:
            raise MewNoteReleaseApprovalError(
                "duplicate candidate supersedes transition"
            )
        actual_by_key[key] = item
    for key, old in old_by_key.items():
        if actual_by_key.get(key) != old:
            raise MewNoteReleaseApprovalError(
                "approval transition changed old supersedes provenance"
            )
    added = set(actual_by_key) - set(old_by_key)
    expected_added = {
        key
        for key in actual_by_key
        if key[0] == predecessor_sha256
    }
    if added != expected_added:
        raise MewNoteReleaseApprovalError(
            "new supersedes records do not exactly name the current "
            "predecessor"
        )

    if actual_supersedes:
        expected_top_keys.add("supersedes")
    elif "supersedes" in expected_top_keys:
        expected_top_keys.remove("supersedes")
    if set(candidate) != expected_top_keys:
        raise MewNoteReleaseApprovalError(
            "approval transition changed fields outside authorization, "
            "deviation, reviewed batches, and supersedes"
        )
    # Authorization is the sole freely replaceable top-level scope. Its
    # schema and values are validated independently by validate_approval().


def _semantic_record(
    batch: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        batch.get("collection_id") != "nonhan-3060"
        or batch.get("batch_id") != "nonhan-0206"
        or batch.get("materialization_kind") != "semantic-empty"
        or len(batch.get("entries", ())) != SEMANTIC_EMPTY_COUNT
        or any(
            entry.get("motif_class") != "neutral-safety"
            for entry in batch["entries"]
        )
    ):
        raise MewNoteReleaseApprovalError(
            "semantic-empty batch identity drift"
        )
    return {
        "collection_id": "nonhan-3060",
        "batch_id": "nonhan-0206",
        "batch_contract_sha256": batch["batch_contract_sha256"],
        "codepoints": [
            entry["codepoint"] for entry in batch["entries"]
        ],
        "character_count": SEMANTIC_EMPTY_COUNT,
        "outline_policy": "semantic-empty-zero-ink",
    }


def _withheld_record(batch: Mapping[str, Any]) -> dict[str, Any]:
    key = (str(batch.get("collection_id")), str(batch.get("batch_id")))
    missing_codepoint = WITHHELD_BATCHES.get(key)
    entries = batch.get("entries")
    if (
        missing_codepoint is None
        or batch.get("materialization_kind") != "visible-raster"
        or not isinstance(entries, list)
        or len(entries) != 16
        or missing_codepoint
        not in {str(entry.get("codepoint")) for entry in entries}
    ):
        raise MewNoteReleaseApprovalError(
            f"{key[0]}/{key[1]}: withheld batch identity drift"
        )
    return {
        "collection_id": key[0],
        "batch_id": key[1],
        "batch_contract_sha256": batch["batch_contract_sha256"],
        "missing_identity_codepoint": missing_codepoint,
        "codepoints": [entry["codepoint"] for entry in entries],
        "character_count": len(entries),
        "reason": "missing-exact-cmap-in-frozen-identity-reference-catalog",
        "policy": "withhold-the-atomic-16-glyph-batch",
    }


def _atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _approval_lock(path: Path) -> Iterator[None]:
    """Hold a fail-closed, same-directory lock for one approval install."""

    lock_path = path.with_name(f".{path.name}.lock")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except FileExistsError as exc:
        raise MewNoteReleaseApprovalError(
            f"approval install lock already exists: {lock_path}"
        ) from exc
    except OSError as exc:
        raise MewNoteReleaseApprovalError(
            f"cannot acquire approval install lock {lock_path}: {exc}"
        ) from exc
    completed = False
    try:
        os.write(
            descriptor,
            f"pid={os.getpid()}\n".encode("ascii"),
        )
        os.fsync(descriptor)
        yield
        completed = True
    finally:
        os.close(descriptor)
        if completed:
            try:
                lock_path.unlink()
            except FileNotFoundError as exc:
                raise MewNoteReleaseApprovalError(
                    f"approval install lock disappeared: {lock_path}"
                ) from exc


def _encode_approval(
    payload: Mapping[str, Any],
) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    ).encode("utf-8")


def _required_predecessor_bytes(
    path: Path,
    *,
    trusted_root: Path,
    required_predecessor_sha256: str,
) -> bytes:
    required = _sha256(
        required_predecessor_sha256,
        label="required approval predecessor",
    )
    canonical = _safe_existing_regular_file(
        path,
        trusted_root=trusted_root,
        label="current release approval",
    )
    current = canonical.read_bytes()
    actual = hashlib.sha256(current).hexdigest()
    if actual != required:
        raise MewNoteReleaseApprovalError(
            "canonical approval is not the latest transition predecessor; "
            f"expected {required}, got {actual}"
        )
    _decode_object(current, label="current release approval")
    return current


def _predecessor_snapshot(
    *,
    project_root: Path,
    predecessor_sha256: str,
) -> dict[str, Any]:
    """Load the immutable exact predecessor used for transition auditing."""

    digest = _sha256(
        predecessor_sha256,
        label="approval predecessor snapshot hash",
    )
    path = (
        project_root
        / APPROVAL_HISTORY_RELATIVE
        / f"{digest}.approval.json"
    )
    path = _safe_existing_regular_file(
        path,
        trusted_root=project_root,
        label="approval predecessor snapshot",
    )
    if sha256_path(path) != digest:
        raise MewNoteReleaseApprovalError(
            f"{path}: predecessor snapshot SHA-256 drift"
        )
    return _read_object(path, label="approval predecessor snapshot")


def _install_validated_approval(
    path: Path,
    payload: Mapping[str, Any],
    *,
    trusted_root: Path,
    required_predecessor_sha256: str,
    validate_transition: Callable[
        [Mapping[str, Any], str], None
    ],
    validate: Callable[[], Any],
) -> None:
    """Replace exactly one predecessor and validate under an exclusive lock."""

    # Fail before creating a lock or doing expensive post-write work if the
    # canonical approval is missing, symlinked, or from another generation.
    _required_predecessor_bytes(
        path,
        trusted_root=trusted_root,
        required_predecessor_sha256=required_predecessor_sha256,
    )
    with _approval_lock(path):
        predecessor = _required_predecessor_bytes(
            path,
            trusted_root=trusted_root,
            required_predecessor_sha256=required_predecessor_sha256,
        )
        predecessor_sha256 = hashlib.sha256(predecessor).hexdigest()
        predecessor_payload = _decode_object(
            predecessor,
            label="current release approval",
        )
        validate_transition(
            predecessor_payload,
            predecessor_sha256,
        )
        encoded = _encode_approval(payload)
        if encoded == predecessor:
            raise MewNoteReleaseApprovalError(
                "release transition payload is byte-identical to predecessor"
            )
        _atomic_write(path, encoded)
        try:
            validate()
        except BaseException:
            _atomic_write(path, predecessor)
            raise


def record_approval(
    *,
    project_root: Path,
    approver_name: str,
    approved_at: str,
    confirmation: str,
) -> Path:
    """Authorize all exact reviewed batches for the preview release."""

    if confirmation != APPROVAL_CONFIRMATION:
        raise MewNoteReleaseApprovalError(
            "explicit release authorization is required"
        )
    project_root = project_root.resolve()
    approver_name = _person(approver_name, label="approver_name")
    approved_at = _timestamp(approved_at, label="approved_at")
    try:
        release_deviation = deviation.validate_release_deviation(
            project_root=project_root
        )
    except deviation.MewNoteReleaseDeviationError as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc
    context, plan_path, plan = _load_plan(project_root)
    _validate_correction_ledger_inventory(context)
    transition_audit = _discover_transition_audit(
        context,
        release_deviation=release_deviation,
    )
    output = project_root / APPROVAL_RELATIVE
    _required_predecessor_bytes(
        output,
        trusted_root=project_root,
        required_predecessor_sha256=(
            transition_audit.predecessor_approval_sha256
        ),
    )
    full_visible_plan = [
        batch
        for batch in plan["batches"]
        if batch["materialization_kind"] == "visible-raster"
    ]
    withheld_plan = [
        batch
        for batch in full_visible_plan
        if (str(batch["collection_id"]), str(batch["batch_id"]))
        in WITHHELD_BATCHES
    ]
    admitted_plan = [
        batch
        for batch in full_visible_plan
        if (str(batch["collection_id"]), str(batch["batch_id"]))
        not in WITHHELD_BATCHES
    ]
    visible = [
        validate_batch_review(
            context,
            batch,
            transition_audit=transition_audit,
        )
        for batch in admitted_plan
    ]
    semantic_batches = [
        batch
        for batch in plan["batches"]
        if batch["materialization_kind"] == "semantic-empty"
    ]
    if (
        len(full_visible_plan) != PLANNED_VISIBLE_BATCH_COUNT
        or len(withheld_plan) != len(WITHHELD_BATCHES)
        or len(visible) != VISIBLE_BATCH_COUNT
        or len(semantic_batches) != 1
    ):
        raise MewNoteReleaseApprovalError(
            "release batch partition is incomplete"
        )
    payload = {
        "schema_version": 1,
        "record_type": "mew-note-tc-collection-release-approval",
        "decision": "APPROVED",
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "release": "0.1 Preview",
        "release_deviation": _pin(
            release_deviation.deviation_path,
            project_root=project_root,
        ),
        "plan": {
            **_pin(plan_path, project_root=project_root),
            "planned_visible_batch_count": PLANNED_VISIBLE_BATCH_COUNT,
            "admitted_visible_batch_count": VISIBLE_BATCH_COUNT,
            "planned_encoded_count": PLANNED_ENCODED_COUNT,
            "encoded_count": ENCODED_COUNT,
            "vertical_count": VERTICAL_COUNT,
        },
        "authorization": {
            "approver_name": approver_name,
            "approved_at": approved_at,
            "confirmation": APPROVAL_CONFIRMATION,
        },
        "reviewed_batches": [
            _approval_review_record(
                batch, project_root=project_root
            )
            for batch in visible
        ],
        "withheld_batches": [
            _withheld_record(batch) for batch in withheld_plan
        ],
        "semantic_empty": _semantic_record(semantic_batches[0]),
    }
    supersedes = _supersedes_records(
        visible, project_root=project_root
    )
    if supersedes:
        payload["supersedes"] = supersedes
    required_predecessor = _latest_transition_predecessor_sha256(
        visible,
        release_deviation=release_deviation,
    )
    if (
        required_predecessor
        != transition_audit.predecessor_approval_sha256
    ):
        raise MewNoteReleaseApprovalError(
            "validated transition predecessor differs from preflight"
        )
    _install_validated_approval(
        output,
        payload,
        trusted_root=project_root,
        required_predecessor_sha256=required_predecessor,
        validate_transition=lambda predecessor, predecessor_sha256: (
            _validate_linear_transition(
                predecessor,
                payload,
                predecessor_sha256=predecessor_sha256,
                batches=visible,
                release_deviation=release_deviation,
                project_root=project_root,
            )
        ),
        validate=lambda: validate_approval(
            project_root=project_root,
            approval_path=output,
        ),
    )
    return output


def validate_approval(
    *,
    project_root: Path = ROOT,
    approval_path: Path | None = None,
) -> ApprovedMewNoteRelease:
    """Validate the collection authorization and every admitted review."""

    project_root = project_root.resolve()
    expected_path = _lexical_absolute(
        project_root / APPROVAL_RELATIVE
    )
    approval_path = _lexical_absolute(
        approval_path or expected_path
    )
    if approval_path != expected_path:
        raise MewNoteReleaseApprovalError(
            "Mew Note approval path is not canonical"
        )
    approval_path = _safe_existing_regular_file(
        approval_path,
        trusted_root=project_root,
        label="canonical Mew Note release approval",
    )
    approval = _read_object(
        approval_path, label="Mew Note release approval"
    )
    required_keys = {
        "schema_version",
        "record_type",
        "decision",
        "family_id",
        "pipeline_id",
        "release",
        "release_deviation",
        "plan",
        "authorization",
        "reviewed_batches",
        "withheld_batches",
        "semantic_empty",
    }
    _exact_object_keys(
        approval,
        required_keys
        | ({"supersedes"} if "supersedes" in approval else set()),
        label=f"{approval_path}: approval",
    )
    if (
        approval.get("schema_version") != 1
        or approval.get("record_type")
        != "mew-note-tc-collection-release-approval"
        or approval.get("decision") != "APPROVED"
        or approval.get("family_id") != FAMILY_ID
        or approval.get("pipeline_id") != PIPELINE_ID
        or approval.get("release") != "0.1 Preview"
    ):
        raise MewNoteReleaseApprovalError(
            f"{approval_path}: approval identity drift"
        )
    try:
        release_deviation = deviation.validate_release_deviation(
            project_root=project_root
        )
    except deviation.MewNoteReleaseDeviationError as exc:
        raise MewNoteReleaseApprovalError(str(exc)) from exc
    if approval.get("release_deviation") != _pin(
        release_deviation.deviation_path,
        project_root=project_root,
    ):
        raise MewNoteReleaseApprovalError(
            f"{approval_path}: release deviation pin drift"
        )
    context, plan_path, plan = _load_plan(project_root)
    _validate_correction_ledger_inventory(context)
    transition_audit = _discover_transition_audit(
        context,
        release_deviation=release_deviation,
    )
    expected_plan = {
        **_pin(plan_path, project_root=project_root),
        "planned_visible_batch_count": PLANNED_VISIBLE_BATCH_COUNT,
        "admitted_visible_batch_count": VISIBLE_BATCH_COUNT,
        "planned_encoded_count": PLANNED_ENCODED_COUNT,
        "encoded_count": ENCODED_COUNT,
        "vertical_count": VERTICAL_COUNT,
    }
    if approval.get("plan") != expected_plan:
        raise MewNoteReleaseApprovalError(
            f"{approval_path}: plan pin drift"
        )
    authorization = _exact_object_keys(
        approval.get("authorization"),
        {"approver_name", "approved_at", "confirmation"},
        label=f"{approval_path}: authorization",
    )
    if (
        authorization.get("confirmation") != APPROVAL_CONFIRMATION
    ):
        raise MewNoteReleaseApprovalError(
            f"{approval_path}: authorization drift"
        )
    approver_name = _person(
        authorization.get("approver_name"), label="approver_name"
    )
    approved_at = _timestamp(
        authorization.get("approved_at"), label="approved_at"
    )
    full_visible_plan = [
        batch
        for batch in plan["batches"]
        if batch["materialization_kind"] == "visible-raster"
    ]
    withheld_plan = [
        batch
        for batch in full_visible_plan
        if (str(batch["collection_id"]), str(batch["batch_id"]))
        in WITHHELD_BATCHES
    ]
    visible_plan = [
        batch
        for batch in full_visible_plan
        if (str(batch["collection_id"]), str(batch["batch_id"]))
        not in WITHHELD_BATCHES
    ]
    semantic_plan = [
        batch
        for batch in plan["batches"]
        if batch["materialization_kind"] == "semantic-empty"
    ]
    reviewed = approval.get("reviewed_batches")
    if (
        not isinstance(reviewed, list)
        or len(reviewed) != VISIBLE_BATCH_COUNT
        or len(full_visible_plan) != PLANNED_VISIBLE_BATCH_COUNT
        or len(withheld_plan) != len(WITHHELD_BATCHES)
        or len(visible_plan) != VISIBLE_BATCH_COUNT
        or len(semantic_plan) != 1
    ):
        raise MewNoteReleaseApprovalError(
            "reviewed batch inventory is incomplete"
        )
    admitted: list[ApprovedVisibleBatch] = []
    for plan_batch, pinned in zip(visible_plan, reviewed, strict=True):
        batch = validate_batch_review(
            context,
            plan_batch,
            transition_audit=transition_audit,
        )
        expected = _approval_review_record(
            batch, project_root=project_root
        )
        if pinned != expected:
            raise MewNoteReleaseApprovalError(
                f"{batch.collection_id}/{batch.batch_id}: "
                "approval review pin drift"
            )
        admitted.append(batch)
    expected_supersedes = _supersedes_records(
        admitted, project_root=project_root
    )
    if expected_supersedes:
        if approval.get("supersedes") != expected_supersedes:
            raise MewNoteReleaseApprovalError(
                "superseded approval provenance drift"
            )
    elif "supersedes" in approval:
        raise MewNoteReleaseApprovalError(
            "unexpected superseded approval provenance"
        )
    expected_withheld = [
        _withheld_record(batch) for batch in withheld_plan
    ]
    if approval.get("withheld_batches") != expected_withheld:
        raise MewNoteReleaseApprovalError(
            "withheld batch inventory drift"
        )
    if approval.get("semantic_empty") != _semantic_record(
        semantic_plan[0]
    ):
        raise MewNoteReleaseApprovalError(
            "semantic-empty approval pin drift"
        )
    transition_predecessor_sha256 = (
        _latest_transition_predecessor_sha256(
            admitted,
            release_deviation=release_deviation,
        )
    )
    if (
        transition_predecessor_sha256
        != transition_audit.predecessor_approval_sha256
    ):
        raise MewNoteReleaseApprovalError(
            "validated transition predecessor differs from audit"
        )
    _validate_linear_transition(
        transition_audit.predecessor_approval,
        approval,
        predecessor_sha256=transition_predecessor_sha256,
        batches=admitted,
        release_deviation=release_deviation,
        project_root=project_root,
    )
    result = ApprovedMewNoteRelease(
        approval_path=approval_path,
        approval_sha256=sha256_path(approval_path),
        release_deviation_path=release_deviation.deviation_path,
        release_deviation_sha256=release_deviation.deviation_sha256,
        plan_path=plan_path,
        plan_sha256=sha256_path(plan_path),
        approver_name=approver_name,
        approved_at=approved_at,
        visible_batches=tuple(admitted),
        withheld_entries=tuple(
            dict(entry)
            for batch in withheld_plan
            for entry in batch["entries"]
        ),
        semantic_empty_entries=tuple(
            dict(entry) for entry in semantic_plan[0]["entries"]
        ),
    )
    encoded_entries = result.encoded_entries
    encoded_codepoints = [
        str(entry["codepoint"]) for entry in encoded_entries
    ]
    if (
        len(encoded_entries) != ENCODED_COUNT
        or len(set(encoded_codepoints)) != ENCODED_COUNT
        or len(result.withheld_entries)
        != PLANNED_ENCODED_COUNT - ENCODED_COUNT
        or len(result.vertical_batches) != 6
        or sum(
            len(batch.entries) for batch in result.vertical_batches
        )
        != VERTICAL_COUNT
    ):
        raise MewNoteReleaseApprovalError(
            "validated release repertoire count drift"
        )
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    record = subparsers.add_parser("record")
    record.add_argument("--approver", required=True)
    record.add_argument("--approved-at", required=True)
    record.add_argument("--confirmation", required=True)
    subparsers.add_parser("validate")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    if args.command == "record":
        print(
            record_approval(
                project_root=project_root,
                approver_name=args.approver,
                approved_at=args.approved_at,
                confirmation=args.confirmation,
            )
        )
    else:
        approved = validate_approval(project_root=project_root)
        print(
            f"validated {len(approved.visible_batches)} reviewed batches, "
            f"{len(approved.encoded_entries)} encoded codepoints, and "
            f"{sum(len(batch.entries) for batch in approved.vertical_batches)} "
            "vertical alternates"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
