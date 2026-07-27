#!/usr/bin/env python3
"""Materialize approved, reproducible per-batch artifacts on demand.

The repository keeps original rasters, signed reports, and final review proofs.
Per-glyph previews, SVG outlines, JSON extracts, and preview fonts are derived
from those inputs and belong in the ignored build cache.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping


DERIVED_DIRECTORIES = ("font", "glyph-report", "png", "svg")
CACHE_RELATIVE = Path("build/cache/imagegen")
HAN_DELTA_SOURCE_RECORD_TYPE = "imagegen-han-delta-source"


class DerivedArtifactError(RuntimeError):
    """A pruned vector build could not be reproduced exactly."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise DerivedArtifactError(f"symlink artifact is forbidden: {path}")
        if not path.is_file() or path.name == "report.json":
            continue
        result[path.relative_to(directory).as_posix()] = _sha256(path)
    return result


def _derived_inventory(inventory: Mapping[str, str]) -> dict[str, str]:
    prefixes = tuple(f"{name}/" for name in DERIVED_DIRECTORIES)
    return {
        relative: digest
        for relative, digest in inventory.items()
        if relative.startswith(prefixes)
    }


def _report(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DerivedArtifactError(f"{path}: cannot read report: {exc}") from exc
    if not isinstance(value, dict):
        raise DerivedArtifactError(f"{path}: report root must be an object")
    inventory = value.get("artifact_sha256")
    if not isinstance(inventory, dict) or not inventory:
        raise DerivedArtifactError(f"{path}: artifact_sha256 is missing")
    if any(
        not isinstance(relative, str) or not isinstance(digest, str)
        for relative, digest in inventory.items()
    ):
        raise DerivedArtifactError(f"{path}: artifact inventory is malformed")
    return value


def _build(
    *,
    batch_id: str,
    descriptor_path: Path,
    project_root: Path,
    cache_root: Path,
) -> Path:
    if batch_id.startswith("imagegen-common-"):
        from scripts import imagegen_font_pipeline as pipeline

        return pipeline.build_batch(
            descriptor_path,
            output_root=cache_root,
        )
    descriptor = _report_or_descriptor(
        descriptor_path,
        label="source descriptor",
    )
    if descriptor.get("record_type") == HAN_DELTA_SOURCE_RECORD_TYPE:
        from scripts import imagegen_font_pipeline as pipeline
        from scripts.register_han_delta_sheet import (
            HanDeltaRegistrationError,
            validate_descriptor,
        )

        try:
            validated = validate_descriptor(
                descriptor_path,
                project_root=project_root,
            )
        except HanDeltaRegistrationError as exc:
            raise DerivedArtifactError(str(exc)) from exc
        if validated.get("batch_id") != batch_id:
            raise DerivedArtifactError(
                f"{descriptor_path}: Han-delta batch identity mismatch"
            )
        return pipeline.build_batch(
            descriptor_path,
            output_root=cache_root,
        )
    if batch_id.startswith("imagegen-nonhan-"):
        from scripts import imagegen_nonhan_pipeline as pipeline

        return pipeline.build_batch(
            descriptor_path,
            project_root=project_root,
            output_root=cache_root,
        )
    if batch_id.startswith("imagegen-vertical-"):
        from scripts import imagegen_vertical_pipeline as pipeline

        return pipeline.build_batch(
            descriptor_path,
            project_root=project_root,
            output_root=cache_root,
        )
    raise DerivedArtifactError(f"{batch_id}: unsupported imagegen batch")


def _report_or_descriptor(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DerivedArtifactError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise DerivedArtifactError(f"{path}: {label} must be an object")
    return value


def ensure_materialized(
    report_path: Path,
    *,
    project_root: Path,
) -> None:
    """Restore only ignored derived directories after exact regeneration.

    A partially present derived tree is treated as corruption. Automatic
    materialization is allowed only when every derived directory is absent and
    the retained report/proofs already match their pinned hashes.
    """

    project_root = project_root.resolve()
    report_path = report_path.resolve()
    build_directory = report_path.parent
    report = _report(report_path)
    batch_id = report.get("batch_id")
    if not isinstance(batch_id, str) or build_directory.name != batch_id:
        raise DerivedArtifactError(f"{report_path}: batch identity mismatch")
    expected = dict(report["artifact_sha256"])
    expected_derived = _derived_inventory(expected)
    actual = _inventory(build_directory)
    if actual == expected:
        return

    derived_prefixes = tuple(f"{name}/" for name in DERIVED_DIRECTORIES)
    present_derived = sorted(
        relative
        for relative in actual
        if relative.startswith(derived_prefixes)
    )
    retained_expected = {
        relative: digest
        for relative, digest in expected.items()
        if not relative.startswith(derived_prefixes)
    }
    if present_derived or actual != retained_expected:
        raise DerivedArtifactError(
            f"{build_directory}: incomplete or changed artifact tree; "
            "remove all ignored derived directories before rebuilding"
        )

    raw_descriptor = report.get("source_descriptor")
    if raw_descriptor is None:
        inferred = (
            "sources/imagegen/batches/"
            f"{batch_id.removeprefix('imagegen-')}.source.json"
        )
        inferred_path = project_root / inferred
        if batch_id.startswith("imagegen-common-"):
            raw_descriptor = inferred
        elif inferred_path.is_file():
            descriptor = _report_or_descriptor(
                inferred_path,
                label="source descriptor",
            )
            if (
                descriptor.get("record_type")
                == HAN_DELTA_SOURCE_RECORD_TYPE
            ):
                raw_descriptor = inferred
    if not isinstance(raw_descriptor, str):
        raise DerivedArtifactError(
            f"{report_path}: source_descriptor is missing"
        )
    descriptor_path = (project_root / raw_descriptor).resolve()
    try:
        descriptor_path.relative_to(project_root)
    except ValueError as exc:
        raise DerivedArtifactError(
            f"{report_path}: source descriptor escapes project root"
        ) from exc
    if not descriptor_path.is_file():
        raise DerivedArtifactError(
            f"{report_path}: source descriptor is missing"
        )

    cache_root = project_root / CACHE_RELATIVE
    cached = cache_root / batch_id
    cache_root.mkdir(parents=True, exist_ok=True)
    if cached.exists():
        cached_report = cached / "report.json"
        if (
            not cached_report.is_file()
            or _derived_inventory(_inventory(cached)) != expected_derived
        ):
            shutil.rmtree(cached)
    if not cached.exists():
        cached = _build(
            batch_id=batch_id,
            descriptor_path=descriptor_path,
            project_root=project_root,
            cache_root=cache_root,
        )
    cached_report = cached / "report.json"
    if (
        not cached_report.is_file()
        or _derived_inventory(_inventory(cached)) != expected_derived
    ):
        raise DerivedArtifactError(
            f"{batch_id}: regenerated derived artifacts differ from approval"
        )

    for name in DERIVED_DIRECTORIES:
        source = cached / name
        target = build_directory / name
        if not source.is_dir():
            raise DerivedArtifactError(
                f"{batch_id}: regenerated {name}/ directory is missing"
            )
        if target.exists():
            raise DerivedArtifactError(
                f"{batch_id}: refusing to replace existing {name}/ directory"
            )
        shutil.copytree(source, target)
    if _inventory(build_directory) != expected:
        raise DerivedArtifactError(
            f"{batch_id}: materialized artifact inventory differs from approval"
        )
