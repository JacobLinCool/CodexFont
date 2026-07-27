#!/usr/bin/env python3
"""Record a vertical vector review or release authorization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from scripts import imagegen_vertical_approval as approval


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=approval.ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("record-review")
    review.add_argument("--batch", required=True)
    review.add_argument("--reviewer-name", required=True)
    review.add_argument("--reviewer-role", required=True)
    review.add_argument("--reviewed-at", required=True)
    review.add_argument("--confirmation", required=True)

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--batch", required=True)
    authorize.add_argument("--approver-name", required=True)
    authorize.add_argument("--approved-at", required=True)
    authorize.add_argument("--confirmation", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "record-review":
        output = approval.record_review(
            args.batch,
            reviewer_name=args.reviewer_name,
            reviewer_role=args.reviewer_role,
            reviewed_at=args.reviewed_at,
            confirmation=args.confirmation,
            project_root=args.project_root,
        )
    else:
        output = approval.authorize(
            args.batch,
            approver_name=args.approver_name,
            approved_at=args.approved_at,
            confirmation=args.confirmation,
            project_root=args.project_root,
        )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
