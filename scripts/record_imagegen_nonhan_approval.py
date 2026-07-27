#!/usr/bin/env python3
"""Record explicit non-Han per-glyph reviews and release authorizations.

Review and authorization are intentionally separate writes:

* ``record-review`` accepts only the exact batch-kind-specific human
  attestation, validates all current evidence, and writes one per-glyph PASS
  record.
* ``authorize`` accepts only the exact release attestation, revalidates all
  evidence and the prior review, writes one hash-pinned approval, then invokes
  the canonical validator.

Neither command infers a review decision.  Neither command overwrites an
existing review or approval.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

from scripts.imagegen_nonhan_approval import (
    AUTHORIZATION_CONFIRMATION,
    REVIEW_CONFIRMATION,
    ROOT,
    SEMANTIC_REVIEW_CONFIRMATION,
    NonHanApprovalError,
    batch_from_repertoire,
    build_approval,
    build_visual_review,
    load_frozen_repertoire,
    validate_approval,
)


class NonHanApprovalRecorderError(RuntimeError):
    """The requested human record cannot be created without guessing."""


def _write_new_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically create a JSON record while refusing every overwrite race."""

    if path.exists() or path.is_symlink():
        raise NonHanApprovalRecorderError(
            f"refusing to overwrite existing record: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise NonHanApprovalRecorderError(
                f"refusing to overwrite existing record: {path}"
            ) from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def record_review(
    *,
    project_root: Path = ROOT,
    batch_id: str,
    reviewer_name: str,
    reviewer_role: str,
    reviewed_at: str,
    confirmation: str,
) -> Path:
    """Validate evidence and create one explicit per-glyph PASS record."""

    project_root = project_root.resolve()
    repertoire = load_frozen_repertoire(project_root)
    batch = batch_from_repertoire(repertoire, batch_id)
    payload = build_visual_review(
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
        reviewer_name=reviewer_name,
        reviewer_role=reviewer_role,
        reviewed_at=reviewed_at,
        confirmation=confirmation,
    )
    path = (
        project_root
        / "sources/imagegen/vector-reviews"
        / f"{batch.batch_id}.vector-review.json"
    )
    _write_new_json(path, payload)
    return path


def authorize(
    *,
    project_root: Path = ROOT,
    batch_id: str,
    approver_name: str,
    approved_at: str,
    confirmation: str,
) -> Path:
    """Create and canonically validate a distinct release authorization."""

    project_root = project_root.resolve()
    repertoire = load_frozen_repertoire(project_root)
    batch = batch_from_repertoire(repertoire, batch_id)
    payload = build_approval(
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
        approver_name=approver_name,
        approved_at=approved_at,
        confirmation=confirmation,
    )
    path = (
        project_root
        / "sources/imagegen/approvals"
        / f"{batch.batch_id}.approval.json"
    )
    _write_new_json(path, payload)
    try:
        validate_approval(
            path,
            project_root=project_root,
            repertoire=repertoire,
        )
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root; defaults to this repository",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser(
        "record-review", help="write one explicit per-glyph PASS review"
    )
    review.add_argument("--batch", required=True)
    review.add_argument("--reviewer-name", required=True)
    review.add_argument("--reviewer-role", required=True)
    review.add_argument("--reviewed-at", required=True)
    review.add_argument(
        "--confirmation",
        required=True,
        help=(
            "visible: "
            f"{REVIEW_CONFIRMATION}; semantic: {SEMANTIC_REVIEW_CONFIRMATION}"
        ),
    )

    approval = subparsers.add_parser(
        "authorize", help="write and validate a separate release authorization"
    )
    approval.add_argument("--batch", required=True)
    approval.add_argument("--approver-name", required=True)
    approval.add_argument("--approved-at", required=True)
    approval.add_argument(
        "--confirmation",
        required=True,
        help=AUTHORIZATION_CONFIRMATION,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "record-review":
            path = record_review(
                project_root=args.project_root,
                batch_id=args.batch,
                reviewer_name=args.reviewer_name,
                reviewer_role=args.reviewer_role,
                reviewed_at=args.reviewed_at,
                confirmation=args.confirmation,
            )
        else:
            path = authorize(
                project_root=args.project_root,
                batch_id=args.batch,
                approver_name=args.approver_name,
                approved_at=args.approved_at,
                confirmation=args.confirmation,
            )
    except (NonHanApprovalRecorderError, NonHanApprovalError) as exc:
        raise SystemExit(str(exc)) from exc
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
