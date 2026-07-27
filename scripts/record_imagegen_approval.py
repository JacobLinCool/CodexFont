#!/usr/bin/env python3
"""Record explicit visual reviews and authorizations for imagegen batches.

This is deliberately a two-step recorder:

* ``record-review`` requires an explicit assertion from the reviewer who
  inspected every glyph in the three vector proof sheets; and
* ``authorize`` requires a separate explicit release authorization, discovers
  exactly one all-PASS raster audit, writes the hash-pinned approval, and then
  runs the canonical fail-closed validator.

Neither command infers a visual decision from geometry or test results.
Existing review and approval records are never overwritten.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

from scripts.imagegen_approval import (
    APPROVAL_RECORD_TYPE,
    APPROVAL_SCHEMA_VERSION,
    REPERTOIRE_RELATIVE_PATH,
    ROOT,
    SMALL_SIZE_PIXELS,
    VECTOR_PIPELINE,
    VISUAL_CHECKS,
    VISUAL_POLARITIES,
    VISUAL_PROOF_KINDS,
    VISUAL_REVIEW_RECORD_TYPE,
    ImagegenApprovalError,
    Repertoire,
    RepertoireBatch,
    load_frozen_repertoire,
    sha256_path,
    validate_approval,
)


REVIEW_CONFIRMATION = (
    "I_REVIEWED_EVERY_GLYPH_AT_12_16_20_32_56_PX_IN_BOTH_POLARITIES"
)
AUTHORIZATION_CONFIRMATION = (
    "I_AUTHORIZE_THIS_HASH_PINNED_BATCH_FOR_THE_RELEASE_FONT"
)
BATCH_PATTERN = re.compile(r"common-[0-9]{4}")


class ImagegenApprovalRecorderError(RuntimeError):
    """A requested review or authorization is incomplete or ambiguous."""


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImagegenApprovalRecorderError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ImagegenApprovalRecorderError(f"{path}: {label} must be an object")
    return value


def _require_nonempty(value: str, *, label: str) -> str:
    if value != value.strip() or not value:
        raise ImagegenApprovalRecorderError(
            f"{label} must be non-empty without surrounding whitespace"
        )
    return value


def _require_utc(value: str, *, label: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ImagegenApprovalRecorderError(
            f"{label} must be an RFC3339 UTC timestamp without fractions"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ImagegenApprovalRecorderError(
            f"{label} is not a canonical RFC3339 UTC timestamp"
        )
    return value


def _batch(repertoire: Repertoire, batch_id: str) -> RepertoireBatch:
    if BATCH_PATTERN.fullmatch(batch_id) is None:
        raise ImagegenApprovalRecorderError(
            "batch must have canonical form common-NNNN"
        )
    number = int(batch_id.removeprefix("common-"))
    if not 1 <= number <= len(repertoire.batches):
        raise ImagegenApprovalRecorderError(f"unknown repertoire batch: {batch_id}")
    selected = repertoire.batches[number - 1]
    if selected.batch_id != batch_id:
        raise ImagegenApprovalRecorderError(
            f"frozen repertoire batch mismatch for {batch_id}"
        )
    return selected


def _project_relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise ImagegenApprovalRecorderError(
            f"path escapes project root: {path}"
        ) from exc


def _write_new_json(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ImagegenApprovalRecorderError(
            f"refusing to overwrite existing record: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(encoded)
        stream.flush()
    try:
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _vector_report(
    project_root: Path, batch: RepertoireBatch
) -> tuple[Path, dict[str, Any]]:
    path = (
        project_root
        / "build/imagegen"
        / batch.descriptor_batch_id
        / "report.json"
    )
    payload = _read_json_object(path, label="vector report")
    if payload.get("pipeline") != VECTOR_PIPELINE:
        raise ImagegenApprovalRecorderError(
            f"{path}: pipeline must be {VECTOR_PIPELINE}"
        )
    if payload.get("approval_state") != "unreviewed":
        raise ImagegenApprovalRecorderError(
            f"{path}: vector report must remain unreviewed"
        )
    if payload.get("batch_id") != batch.descriptor_batch_id:
        raise ImagegenApprovalRecorderError(f"{path}: batch_id mismatch")
    if payload.get("characters") != list(batch.characters):
        raise ImagegenApprovalRecorderError(f"{path}: character sequence mismatch")
    return path, payload


def build_visual_review(
    *,
    project_root: Path,
    batch: RepertoireBatch,
    reviewer_name: str,
    reviewer_role: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Build a review payload after the caller explicitly confirms inspection."""

    reviewer_name = _require_nonempty(reviewer_name, label="reviewer name")
    reviewer_role = _require_nonempty(reviewer_role, label="reviewer role")
    reviewed_at = _require_utc(reviewed_at, label="reviewed_at")
    report_path, report = _vector_report(project_root, batch)
    artifact_hashes = report.get("artifact_sha256")
    proofs = report.get("proofs")
    if not isinstance(artifact_hashes, dict) or not isinstance(proofs, dict):
        raise ImagegenApprovalRecorderError(
            f"{report_path}: missing artifact or proof inventory"
        )
    report_key_by_kind = {
        "black-on-white": "black_on_white",
        "white-on-black": "white_on_black",
        "segmented-source": "segmented_source",
    }
    proof_records: list[dict[str, Any]] = []
    for kind in VISUAL_PROOF_KINDS:
        report_key = report_key_by_kind[kind]
        relative = proofs.get(report_key)
        if not isinstance(relative, str):
            raise ImagegenApprovalRecorderError(
                f"{report_path}: missing {report_key} proof"
            )
        digest = artifact_hashes.get(relative)
        if not isinstance(digest, str):
            raise ImagegenApprovalRecorderError(
                f"{report_path}: proof is not hash-pinned: {relative}"
            )
        proof_records.append(
            {
                "kind": kind,
                "path": (
                    f"build/imagegen/{batch.descriptor_batch_id}/{relative}"
                ),
                "sha256": digest,
                "decision": "PASS",
            }
        )
    notes = (
        "Reviewed against the segmented source and all required small-size "
        "proofs in both polarities; all required visual checks passed."
    )
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "record_type": VISUAL_REVIEW_RECORD_TYPE,
        "review_state": "approved",
        "batch_id": batch.batch_id,
        "reviewer": {
            "name": reviewer_name,
            "role": reviewer_role,
        },
        "reviewed_at": reviewed_at,
        "vector_report": {
            "path": _project_relative(report_path, project_root),
            "sha256": sha256_path(report_path),
        },
        "scope": {
            "all_glyphs_reviewed": True,
            "checks": list(VISUAL_CHECKS),
            "sizes_px": list(SMALL_SIZE_PIXELS),
            "polarities": list(VISUAL_POLARITIES),
        },
        "proofs": proof_records,
        "glyphs": [
            {
                "rank": batch.start_rank + offset,
                "character": character,
                "decision": "PASS",
                "notes": notes,
            }
            for offset, character in enumerate(batch.characters)
        ],
        "summary": {
            "glyph_count": len(batch.characters),
            "pass_count": len(batch.characters),
            "reject_count": 0,
            "rejected_characters": [],
        },
    }


def discover_raster_audit(
    *, project_root: Path, batch: RepertoireBatch
) -> Path:
    """Return the unique canonical audit report containing ``batch``."""

    matches: list[Path] = []
    for path in sorted(
        (project_root / "reports").glob(
            "imagegen-common-[0-9][0-9][0-9][0-9]-"
            "[0-9][0-9][0-9][0-9]-audit.json"
        )
    ):
        payload = _read_json_object(path, label="raster audit")
        raw_batches = payload.get("batches")
        if not isinstance(raw_batches, list):
            continue
        if any(
            isinstance(item, dict) and item.get("batch_id") == batch.batch_id
            for item in raw_batches
        ):
            matches.append(path)
    if len(matches) != 1:
        raise ImagegenApprovalRecorderError(
            f"{batch.batch_id}: expected exactly one raster audit, found "
            f"{len(matches)}: {[str(path) for path in matches]}"
        )
    return matches[0]


def build_approval(
    *,
    project_root: Path,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    raster_audit_path: Path,
    approver_name: str,
    approved_at: str,
) -> dict[str, Any]:
    """Build the exact hash-pinned approval payload for one reviewed batch."""

    approver_name = _require_nonempty(approver_name, label="approver name")
    approved_at = _require_utc(approved_at, label="approved_at")
    descriptor_path = (
        project_root
        / "sources/imagegen/batches"
        / f"{batch.batch_id}.source.json"
    )
    raster_path = (
        project_root / "sources/imagegen/raster" / f"{batch.batch_id}.png"
    )
    vector_report_path, _ = _vector_report(project_root, batch)
    visual_review_path = (
        project_root
        / "sources/imagegen/vector-reviews"
        / f"{batch.batch_id}.vector-review.json"
    )
    required = (
        descriptor_path,
        raster_path,
        raster_audit_path,
        vector_report_path,
        visual_review_path,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ImagegenApprovalRecorderError(
            f"{batch.batch_id}: missing approval evidence: {missing}"
        )
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "record_type": APPROVAL_RECORD_TYPE,
        "approval_state": "approved",
        "batch_id": batch.batch_id,
        "repertoire": {
            "path": REPERTOIRE_RELATIVE_PATH.as_posix(),
            "sha256": repertoire.sha256,
            "repertoire_id": repertoire.repertoire_id,
            "sequence_sha256": repertoire.sequence_sha256,
            "start_rank": batch.start_rank,
            "end_rank": batch.end_rank,
            "characters": "".join(batch.characters),
        },
        "source": {
            "descriptor": _project_relative(descriptor_path, project_root),
            "descriptor_sha256": sha256_path(descriptor_path),
            "raster": _project_relative(raster_path, project_root),
            "raster_sha256": sha256_path(raster_path),
        },
        "raster_audit": {
            "report": _project_relative(raster_audit_path, project_root),
            "report_sha256": sha256_path(raster_audit_path),
        },
        "vector_build": {
            "report": _project_relative(vector_report_path, project_root),
            "report_sha256": sha256_path(vector_report_path),
            "pipeline": VECTOR_PIPELINE,
        },
        "vector_visual_review": {
            "record": _project_relative(visual_review_path, project_root),
            "record_sha256": sha256_path(visual_review_path),
        },
        "authorization": {
            "decision": "APPROVED",
            "approver": approver_name,
            "approved_at": approved_at,
        },
    }


def record_review(args: argparse.Namespace) -> Path:
    if args.confirmation != REVIEW_CONFIRMATION:
        raise ImagegenApprovalRecorderError(
            "record-review requires the exact explicit inspection confirmation"
        )
    project_root = args.project_root.resolve()
    repertoire = load_frozen_repertoire(project_root)
    batch = _batch(repertoire, args.batch)
    payload = build_visual_review(
        project_root=project_root,
        batch=batch,
        reviewer_name=args.reviewer_name,
        reviewer_role=args.reviewer_role,
        reviewed_at=args.reviewed_at,
    )
    path = (
        project_root
        / "sources/imagegen/vector-reviews"
        / f"{batch.batch_id}.vector-review.json"
    )
    _write_new_json(path, payload)
    return path


def authorize(args: argparse.Namespace) -> Path:
    if args.confirmation != AUTHORIZATION_CONFIRMATION:
        raise ImagegenApprovalRecorderError(
            "authorize requires the exact explicit release confirmation"
        )
    project_root = args.project_root.resolve()
    repertoire = load_frozen_repertoire(project_root)
    batch = _batch(repertoire, args.batch)
    audit_path = discover_raster_audit(
        project_root=project_root, batch=batch
    )
    payload = build_approval(
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
        raster_audit_path=audit_path,
        approver_name=args.approver_name,
        approved_at=args.approved_at,
    )
    path = (
        project_root
        / "sources/imagegen/approvals"
        / f"{batch.batch_id}.approval.json"
    )
    _write_new_json(path, payload)
    try:
        validate_approval(path, project_root=project_root, repertoire=repertoire)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record explicit imagegen vector reviews and authorizations."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root; defaults to this repository",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser(
        "record-review", help="write one explicit per-glyph vector review"
    )
    review.add_argument("--batch", required=True)
    review.add_argument("--reviewer-name", required=True)
    review.add_argument("--reviewer-role", required=True)
    review.add_argument("--reviewed-at", required=True)
    review.add_argument("--confirmation", required=True)

    approval = subparsers.add_parser(
        "authorize", help="write and canonically validate one release approval"
    )
    approval.add_argument("--batch", required=True)
    approval.add_argument("--approver-name", required=True)
    approval.add_argument("--approved-at", required=True)
    approval.add_argument("--confirmation", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        path = (
            record_review(args)
            if args.command == "record-review"
            else authorize(args)
        )
    except (ImagegenApprovalRecorderError, ImagegenApprovalError) as exc:
        raise SystemExit(str(exc)) from exc
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
