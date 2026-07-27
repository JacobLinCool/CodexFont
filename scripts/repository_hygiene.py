#!/usr/bin/env python3
"""Audit the repository for superseded experiments and orphaned proof files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
AUDIT_GLOB = "imagegen-common-*-audit.json"
REDUNDANT_AUDIT_GLOB = "imagegen-common-*-audit.md"
EVIDENCE_ROOTS = (
    Path("reports/proofs"),
    Path("build/imagegen-audit"),
)
FORBIDDEN_PATHS = (
    Path("tmp"),
    Path("sources/upstream"),
    Path("sources/authored"),
    Path("sources/original"),
    Path("sources/manual"),
    Path("sources/gaiji"),
    Path("sources/glyphwiki"),
    Path("sources/imagegen/rejected"),
    Path("build/authored"),
    Path("build/original"),
    Path("build/imagegen/approved"),
    Path("build/imagegen/rejected"),
    Path("build/imagegen/imagegen-pilot-common-0001"),
    Path("reports/rejected"),
    Path("specimens"),
    Path("output/playwright"),
    Path("dist/font"),
    Path("dist/proof"),
    Path("dist/OFL.txt"),
    Path("dist/report.json"),
)
FORBIDDEN_SCRIPT_PREFIXES = (
    "_tmp_",
    "authored_",
    "canonical_",
    "gesture_",
)
FORBIDDEN_SCRIPT_NAMES = frozenset(
    {
        "build_authored_font.py",
        "build_common_3000_repertoire.py",
        "build_font.py",
        "build_imagegen_approved_font.py",
        "build_imagegen_nonhan_repertoire.py",
        "careful_pen.py",
        "compile_authored_manifest.py",
        "compile_authored_special_manifest.py",
        "flowing_pen.py",
        "gaiji.py",
        "hardpen.py",
        "match_glyphwiki.py",
        "non_han_manifest.py",
        "package_authored_font.py",
        "proof_combining_mark_integration.py",
        "qa_authored_font.py",
        "qa_font.py",
        "render_original_probe.py",
        "render_spur_comparison.py",
        "specimens.py",
        "style_previews.py",
        "vendor_glyphwiki.py",
    }
)
REGENERABLE_BUILD_PARTS = frozenset({"font", "glyph-report", "png", "svg"})
SEMANTIC_EVIDENCE_FONT = Path(
    "build/imagegen/imagegen-nonhan-0206/font/"
    "ClearHandTC-NonHan0206-Semantic.ttf"
)
FONT_BINARY_SUFFIXES = frozenset(
    {".ttf", ".otf", ".woff", ".woff2", ".ttc", ".dfont"}
)
ALLOWED_FONT_BINARY_ROOTS = (
    Path("dist/clear-hand-tc/font"),
    Path("dist/mew-note-tc/font"),
)
DIST_FAMILY_DIRECTORIES = (
    Path("clear-hand-tc"),
    Path("mew-note-tc"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def referenced_evidence(root: Path = ROOT) -> set[Path]:
    """Return proof artifacts pinned by the active Han raster audits."""

    references: set[Path] = set()
    reports = sorted((root / "reports").glob(AUDIT_GLOB))
    if len(reports) != 48:
        raise ValueError(f"expected 48 active Han audit reports, found {len(reports)}")
    prefixes = tuple(f"{path.as_posix()}/" for path in EVIDENCE_ROOTS)
    for report in reports:
        payload = json.loads(report.read_text(encoding="utf-8"))
        for value in _walk_strings(payload):
            normalized = value.removeprefix("./")
            if normalized.startswith(prefixes) and Path(normalized).suffix:
                references.add(Path(normalized))
    return references


def evidence_files(root: Path = ROOT) -> set[Path]:
    return {
        path.relative_to(root)
        for directory in EVIDENCE_ROOTS
        for path in (root / directory).rglob("*")
        if path.is_file()
    }


def redundant_audit_documents(root: Path = ROOT) -> list[Path]:
    return sorted(
        path.relative_to(root)
        for path in (root / "reports").glob(REDUNDANT_AUDIT_GLOB)
        if path.is_file()
    )


def forbidden_paths(root: Path = ROOT) -> list[Path]:
    found = [path for relative in FORBIDDEN_PATHS if (path := root / relative).exists()]
    script_directory = root / "scripts"
    for path in script_directory.glob("*.py"):
        if path.name in FORBIDDEN_SCRIPT_NAMES or path.name.startswith(
            FORBIDDEN_SCRIPT_PREFIXES
        ):
            found.append(path)
    return sorted(path.relative_to(root) for path in found)


def _git_paths(root: Path, *arguments: str) -> list[Path]:
    if not (root / ".git").exists():
        return []
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 1 and arguments[:1] == ("grep",):
        return []
    completed.check_returncode()
    return [
        Path(line)
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def tracked_regenerable_files(root: Path = ROOT) -> list[Path]:
    found: list[Path] = []
    for path in _git_paths(root, "ls-files", "build/imagegen"):
        parts = path.parts
        if (
            len(parts) >= 4
            and parts[2].startswith("imagegen-")
            and parts[3] in REGENERABLE_BUILD_PARTS
            and path != SEMANTIC_EVIDENCE_FONT
        ):
            found.append(path)
        elif (
            len(parts) == 3
            and parts[2].startswith("common-")
            and "small-sizes" in parts[2]
        ):
            found.append(path)
        elif len(parts) >= 3 and parts[2] == "release-9120":
            found.append(path)
    return sorted(found)


def _is_original_raster(path: Path) -> bool:
    if (
        len(path.parts) == 4
        and path.parts[:3] == ("sources", "imagegen", "raster")
        and path.suffix.lower() == ".png"
    ):
        return True
    parts = path.parts
    if len(parts) < 4 or parts[0] != "families":
        return False
    if (
        len(parts) == 4
        and parts[2] == "pilots"
        and parts[3].endswith("-raster.png")
    ):
        return True
    if (
        len(parts) == 6
        and parts[2:5] == ("sources", "imagegen", "raster")
        and path.suffix.lower() == ".png"
    ):
        return True
    return (
        len(parts) >= 11
        and parts[2:5] == ("sources", "imagegen", "pipelines")
        and parts[6] == "collections"
        and parts[8] == "batches"
        and parts[-2].startswith(
            (
                "han-",
                "nonhan-",
                "vertical-",
            )
        )
        and (
            parts[-1] == "raster.png"
            or parts[-1].endswith("-raw-candidate.png")
        )
    )


def lfs_pointer_files(root: Path = ROOT) -> set[Path]:
    return set(
        _git_paths(
            root,
            "grep",
            "--cached",
            "-l",
            "-e",
            "^version https://git-lfs.github.com/spec/v1$",
        )
    )


def unexpected_lfs_files(root: Path = ROOT) -> list[Path]:
    return sorted(
        path
        for path in lfs_pointer_files(root)
        if not _is_original_raster(path)
    )


def original_rasters_missing_lfs(root: Path = ROOT) -> list[Path]:
    """Require every tracked irreplaceable raster to be an LFS pointer."""

    pointers = lfs_pointer_files(root)
    return sorted(
        path
        for path in _git_paths(root, "ls-files")
        if _is_original_raster(path) and path not in pointers
    )


def unexpected_font_binaries(root: Path = ROOT) -> list[Path]:
    found: list[Path] = []
    for path in _git_paths(root, "ls-files"):
        if path.suffix.lower() not in FONT_BINARY_SUFFIXES:
            continue
        if path == SEMANTIC_EVIDENCE_FONT:
            continue
        if not any(
            path.is_relative_to(directory)
            for directory in ALLOWED_FONT_BINARY_ROOTS
        ):
            found.append(path)
    return sorted(found)


def unexpected_dist_entries(root: Path = ROOT) -> list[Path]:
    """Return entries outside the two namespaced release directories."""

    dist = root / "dist"
    if not dist.exists():
        return []
    if dist.is_symlink() or not dist.is_dir():
        return [Path("dist")]
    allowed = {path.name for path in DIST_FAMILY_DIRECTORIES}
    return sorted(
        path.relative_to(root)
        for path in dist.iterdir()
        if (
            path.name not in allowed
            or path.is_symlink()
            or not path.is_dir()
        )
    )


def _release_artifact_inventory(
    directory: Path,
) -> tuple[dict[str, str], list[str]]:
    inventory: dict[str, str] = {}
    issues: list[str] = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            issues.append(f"{directory}: symlink is forbidden: {relative}")
            continue
        if not path.is_file() or relative == "report.json":
            continue
        inventory[relative] = sha256(path)
    return inventory, issues


def release_inventory_issues(root: Path = ROOT) -> list[str]:
    """Validate every release report against its complete artifact tree."""

    issues: list[str] = []
    dist = root / "dist"
    if dist.is_symlink() or not dist.is_dir():
        return ["dist: release directory is missing or is not a real directory"]

    for family in DIST_FAMILY_DIRECTORIES:
        directory = dist / family
        label = directory.relative_to(root).as_posix()
        if directory.is_symlink() or not directory.is_dir():
            issues.append(
                f"{label}: family release is missing or is not a real directory"
            )
            continue

        actual, inventory_issues = _release_artifact_inventory(directory)
        issues.extend(inventory_issues)
        report_path = directory / "report.json"
        if report_path.is_symlink() or not report_path.is_file():
            issues.append(f"{label}: report.json is missing or is not a regular file")
            continue
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            issues.append(f"{label}/report.json: cannot read valid JSON: {error}")
            continue
        if not isinstance(report, dict):
            issues.append(f"{label}/report.json: root must be an object")
            continue
        declared = report.get("artifact_sha256")
        if not isinstance(declared, dict) or not declared:
            issues.append(
                f"{label}/report.json: artifact_sha256 must be a non-empty object"
            )
            continue

        normalized: dict[str, str] = {}
        malformed = False
        for raw_path, raw_digest in declared.items():
            if not isinstance(raw_path, str) or not raw_path:
                malformed = True
                continue
            relative = Path(raw_path)
            if (
                relative.is_absolute()
                or relative.as_posix() != raw_path
                or any(part in ("", ".", "..") for part in relative.parts)
                or raw_path == "report.json"
            ):
                malformed = True
                continue
            if (
                not isinstance(raw_digest, str)
                or len(raw_digest) != 64
                or raw_digest != raw_digest.lower()
                or any(character not in "0123456789abcdef" for character in raw_digest)
            ):
                malformed = True
                continue
            normalized[raw_path] = raw_digest
        if malformed or len(normalized) != len(declared):
            issues.append(
                f"{label}/report.json: artifact_sha256 contains malformed entries"
            )

        missing = sorted(set(actual) - set(normalized))
        extra = sorted(set(normalized) - set(actual))
        mismatched = sorted(
            path
            for path in set(actual) & set(normalized)
            if actual[path] != normalized[path]
        )
        if missing or extra or mismatched:
            issues.append(
                f"{label}/report.json: artifact inventory mismatch; "
                f"missing={missing}, extra={extra}, hash_mismatch={mismatched}"
            )
    return issues


def audit(root: Path = ROOT) -> dict[str, object]:
    references = referenced_evidence(root)
    files = evidence_files(root)
    missing = sorted(references - files)
    orphaned = sorted(files - references)
    digest_mismatches: list[Path] = []
    for report in sorted((root / "reports").glob(AUDIT_GLOB)):
        payload = json.loads(report.read_text(encoding="utf-8"))
        for value in _walk_records(payload):
            path = value.get("path")
            expected = value.get("sha256")
            if not isinstance(path, str) or not isinstance(expected, str):
                continue
            relative = Path(path.removeprefix("./"))
            if relative not in references or not (root / relative).is_file():
                continue
            if sha256(root / relative) != expected:
                digest_mismatches.append(relative)
    return {
        "active_audit_reports": 48,
        "referenced_evidence_files": len(references),
        "evidence_files": len(files),
        "missing_evidence": [path.as_posix() for path in missing],
        "orphaned_evidence": [path.as_posix() for path in orphaned],
        "redundant_audit_documents": [
            path.as_posix() for path in redundant_audit_documents(root)
        ],
        "digest_mismatches": [
            path.as_posix() for path in sorted(set(digest_mismatches))
        ],
        "forbidden_paths": [
            path.as_posix() for path in forbidden_paths(root)
        ],
        "tracked_regenerable_files": [
            path.as_posix() for path in tracked_regenerable_files(root)
        ],
        "unexpected_lfs_files": [
            path.as_posix() for path in unexpected_lfs_files(root)
        ],
        "original_rasters_missing_lfs": [
            path.as_posix()
            for path in original_rasters_missing_lfs(root)
        ],
        "unexpected_font_binaries": [
            path.as_posix() for path in unexpected_font_binaries(root)
        ],
        "unexpected_dist_entries": [
            path.as_posix() for path in unexpected_dist_entries(root)
        ],
        "release_inventory_issues": release_inventory_issues(root),
    }


def _walk_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_records(item)


def prune_orphaned_evidence(root: Path = ROOT) -> list[Path]:
    references = referenced_evidence(root)
    orphaned = sorted(evidence_files(root) - references)
    for relative in orphaned:
        (root / relative).unlink()
    for directory in EVIDENCE_ROOTS:
        for path in sorted(
            (root / directory).rglob("*"),
            key=lambda value: len(value.parts),
            reverse=True,
        ):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    return orphaned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prune-orphaned-evidence",
        action="store_true",
        help="delete only proof files not referenced by an active audit",
    )
    arguments = parser.parse_args()
    if arguments.prune_orphaned_evidence:
        removed = prune_orphaned_evidence()
        print(f"removed {len(removed)} orphaned proof files")
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    failed = any(
        result[key]
        for key in (
            "missing_evidence",
            "orphaned_evidence",
            "redundant_audit_documents",
            "digest_mismatches",
            "forbidden_paths",
            "tracked_regenerable_files",
            "unexpected_lfs_files",
            "original_rasters_missing_lfs",
            "unexpected_font_binaries",
            "unexpected_dist_entries",
            "release_inventory_issues",
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
