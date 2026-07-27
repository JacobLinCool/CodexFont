#!/usr/bin/env python3
"""Verify byte-identical release trees from two independent builds."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_PAIRS = (
    (
        "clear-hand-tc",
        Path("dist/clear-hand-tc"),
        Path("build/imagegen/release-9120"),
    ),
    (
        "mew-note-tc",
        Path("dist/mew-note-tc"),
        Path("build/families/mew-note-tc/release-9088"),
    ),
)


class ReleaseReproducibilityError(RuntimeError):
    """Two release builds are absent, malformed, or not byte-identical."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseReproducibilityError(
                    f"{path}: duplicate JSON key {key!r}"
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicates,
        )
    except ReleaseReproducibilityError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseReproducibilityError(
            f"{path}: cannot read release report"
        ) from error
    if not isinstance(value, dict):
        raise ReleaseReproducibilityError(
            f"{path}: release report must be an object"
        )
    return value


def _canonical_inventory(value: Any, *, report: Path) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise ReleaseReproducibilityError(
            f"{report}: artifact_sha256 must be a non-empty object"
        )
    result: dict[str, str] = {}
    for raw_path, raw_digest in value.items():
        if not isinstance(raw_path, str):
            raise ReleaseReproducibilityError(
                f"{report}: artifact path must be a string"
            )
        relative = Path(raw_path)
        if (
            not raw_path
            or relative.is_absolute()
            or relative.as_posix() != raw_path
            or any(part in {"", ".", ".."} for part in relative.parts)
            or raw_path == "report.json"
        ):
            raise ReleaseReproducibilityError(
                f"{report}: invalid artifact path {raw_path!r}"
            )
        if (
            not isinstance(raw_digest, str)
            or len(raw_digest) != 64
            or raw_digest != raw_digest.lower()
            or any(character not in "0123456789abcdef" for character in raw_digest)
        ):
            raise ReleaseReproducibilityError(
                f"{report}: invalid SHA-256 for {raw_path}"
            )
        result[raw_path] = raw_digest
    return result


def snapshot_release_tree(directory: Path) -> dict[str, str]:
    """Return a verified complete file inventory, including report.json."""

    directory = Path(directory)
    try:
        root_mode = directory.lstat().st_mode
    except OSError as error:
        raise ReleaseReproducibilityError(
            f"release directory is missing: {directory}"
        ) from error
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise ReleaseReproducibilityError(
            f"release root must be a real directory: {directory}"
        )

    actual: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ReleaseReproducibilityError(
                f"{directory}: symlink is forbidden: {relative}"
            )
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ReleaseReproducibilityError(
                f"{directory}: non-regular artifact: {relative}"
            )
        actual[relative] = _sha256(path)

    report_path = directory / "report.json"
    if "report.json" not in actual:
        raise ReleaseReproducibilityError(
            f"{directory}: report.json is missing"
        )
    report = _read_object(report_path)
    declared = _canonical_inventory(
        report.get("artifact_sha256"),
        report=report_path,
    )
    artifacts = {
        path: digest
        for path, digest in actual.items()
        if path != "report.json"
    }
    if declared != artifacts:
        raise ReleaseReproducibilityError(
            f"{directory}: report artifact inventory does not match the tree"
        )
    return actual


def compare_release_trees(
    first: Path,
    second: Path,
    *,
    family_id: str,
) -> dict[str, Any]:
    """Require the same paths and bytes in two independently built trees."""

    left = snapshot_release_tree(first)
    right = snapshot_release_tree(second)
    if left != right:
        left_paths = set(left)
        right_paths = set(right)
        missing = sorted(left_paths - right_paths)
        extra = sorted(right_paths - left_paths)
        changed = sorted(
            path
            for path in left_paths & right_paths
            if left[path] != right[path]
        )
        raise ReleaseReproducibilityError(
            f"{family_id}: release trees differ; "
            f"missing={missing}, extra={extra}, changed={changed}"
        )
    manifest = "\n".join(
        f"{path}\0{digest}" for path, digest in sorted(left.items())
    ).encode("utf-8")
    return {
        "family_id": family_id,
        "artifact_count_including_report": len(left),
        "tree_sha256": hashlib.sha256(manifest).hexdigest(),
    }


def verify_all(project_root: Path = ROOT) -> list[dict[str, Any]]:
    project_root = Path(project_root).resolve(strict=True)
    return [
        compare_release_trees(
            project_root / first,
            project_root / second,
            family_id=family_id,
        )
        for family_id, first, second in RELEASE_PAIRS
    ]


def main() -> int:
    print(
        json.dumps(
            {
                "schema_version": 1,
                "reproducible": True,
                "families": verify_all(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
