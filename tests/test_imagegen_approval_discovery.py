from __future__ import annotations

from pathlib import Path

import pytest

from scripts import imagegen_approval as approval


def test_validate_prefix_summary_flag_is_explicit() -> None:
    args = approval.parse_args(["validate-prefix", "--summary"])
    assert args.command == "validate-prefix"
    assert args.summary is True


def _approval_directory(project_root: Path) -> Path:
    directory = project_root / "sources/imagegen/approvals"
    directory.mkdir(parents=True)
    return directory


def test_discovery_selects_common_approvals_and_allows_peer_families(
    tmp_path: Path,
) -> None:
    directory = _approval_directory(tmp_path)
    for name in (
        "common-0001.approval.json",
        "nonhan-0001.approval.json",
        "vertical-0001.approval.json",
        "moe-common-extension.approval.json",
        "dictionary-salience-extension-1216.approval.json",
    ):
        (directory / name).write_text("{}\n", encoding="utf-8")

    assert approval.discover_approval_paths(
        directory,
        project_root=tmp_path,
    ) == (directory / "common-0001.approval.json",)


def test_discovery_still_rejects_unknown_json(
    tmp_path: Path,
) -> None:
    directory = _approval_directory(tmp_path)
    (directory / "common-0001.approval.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (directory / "vertical-final.approval.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        approval.ImagegenApprovalError,
        match="non-canonical JSON files are forbidden",
    ):
        approval.discover_approval_paths(
            directory,
            project_root=tmp_path,
        )
