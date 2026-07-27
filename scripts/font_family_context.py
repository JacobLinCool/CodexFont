#!/usr/bin/env python3
"""Load one explicitly bound, hash-pinned font-family pipeline context.

This module is the namespace boundary between a font family and every
authoring pipeline.  It deliberately has no default family, implicit
repository layout, or compatibility lookup.  A caller must name both the
family contract and the pipeline contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence


FAMILY_RECORD_TYPE = "codexfont-family-contract"
PIPELINE_RECORD_TYPE = "codexfont-family-pipeline-contract"
COLLECTION_RECORD_TYPE = "codexfont-family-collection-contract"
AUTHORING_RECORD_TYPE = "codexfont-family-authoring-contract"
EVIDENCE_RECORD_TYPE = "codexfont-family-evidence-binding"
SCHEMA_VERSION = 1
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class FamilyContextError(ValueError):
    """A family namespace, contract, or evidence chain is unsafe."""


@dataclass(frozen=True)
class PinnedFile:
    """One canonical repository file and its verified digest."""

    path: Path
    absolute_path: Path
    sha256: str

    def evidence_record(self) -> dict[str, str]:
        return {
            "path": self.path.as_posix(),
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class CollectionBinding:
    """One unique collection inside the pinned collection contract."""

    collection_id: str
    record_sha256: str
    record: Mapping[str, Any]


@dataclass(frozen=True)
class NamespacePaths:
    """Namespaced roots for one collection or batch."""

    source: Path
    build: Path
    cache: Path
    release: Path


@dataclass(frozen=True)
class FamilyContext:
    """A verified family/pipeline/collection namespace."""

    project_root: Path
    family_id: str
    pipeline_id: str
    family_contract: PinnedFile
    pipeline_contract: PinnedFile
    collection_contract: PinnedFile
    authoring_contract: PinnedFile
    family_root: Path
    source_root: Path
    build_root: Path
    cache_root: Path
    release_root: Path
    collections: Mapping[str, CollectionBinding]
    family_payload: Mapping[str, Any]
    pipeline_payload: Mapping[str, Any]
    collection_payload: Mapping[str, Any]
    authoring_payload: Mapping[str, Any]

    def collection(self, collection_id: str) -> CollectionBinding:
        """Return a declared collection, rejecting aliases and unknown IDs."""

        collection_id = _require_slug(
            collection_id,
            label="collection_id",
        )
        try:
            return self.collections[collection_id]
        except KeyError as exc:
            raise FamilyContextError(
                f"unknown collection_id {collection_id!r}"
            ) from exc

    def collection_paths(self, collection_id: str) -> NamespacePaths:
        """Return isolated source/build/cache/release paths for a collection."""

        binding = self.collection(collection_id)
        suffix = (
            Path("pipelines")
            / self.pipeline_id
            / "collections"
            / binding.collection_id
        )
        return NamespacePaths(
            source=self.source_root / suffix,
            build=self.build_root / suffix,
            cache=self.cache_root / suffix,
            release=self.release_root / suffix,
        )

    def batch_paths(
        self,
        collection_id: str,
        batch_id: str,
    ) -> NamespacePaths:
        """Return isolated paths for one strictly named collection batch."""

        batch_id = _require_slug(batch_id, label="batch_id")
        collection_paths = self.collection_paths(collection_id)
        suffix = Path("batches") / batch_id
        return NamespacePaths(
            source=collection_paths.source / suffix,
            build=collection_paths.build / suffix,
            cache=collection_paths.cache / suffix,
            release=collection_paths.release / suffix,
        )

    def evidence_binding(self, collection_id: str) -> dict[str, Any]:
        """Return the exact family/pipeline/collection evidence hash chain."""

        collection = self.collection(collection_id)
        binding: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": EVIDENCE_RECORD_TYPE,
            "family_id": self.family_id,
            "family_contract": self.family_contract.evidence_record(),
            "pipeline_id": self.pipeline_id,
            "pipeline_contract": self.pipeline_contract.evidence_record(),
            "collection_id": collection.collection_id,
            "collection_contract": (
                self.collection_contract.evidence_record()
            ),
            "collection_record_sha256": collection.record_sha256,
            "authoring_contract": (
                self.authoring_contract.evidence_record()
            ),
        }
        binding["binding_sha256"] = canonical_json_sha256(binding)
        return binding


def sha256_path(path: Path) -> str:
    """Hash one regular file without following a caller-selected alternate."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    """Hash JSON using one deterministic, Unicode-preserving serialization."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FamilyContextError(
            f"value is not canonical JSON: {exc}"
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def _require_slug(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SLUG_PATTERN.fullmatch(value) is None:
        raise FamilyContextError(
            f"{label} must be a lowercase ASCII slug"
        )
    return value


def _require_sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or SHA256_PATTERN.fullmatch(value) is None
    ):
        raise FamilyContextError(
            f"{label} must be a lowercase SHA-256 digest"
        )
    return value


def _canonical_relative_path(value: Any, *, label: str) -> Path:
    if not isinstance(value, str):
        raise FamilyContextError(f"{label} must be a string")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or not pure.parts
        or "." in pure.parts
        or ".." in pure.parts
        or pure.as_posix() != value
    ):
        raise FamilyContextError(
            f"{label} must be a canonical project-relative POSIX path"
        )
    return Path(*pure.parts)


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FamilyContextError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise FamilyContextError(f"{path}: {label} must be an object")
    return payload


def _relative_to_project(
    path: Path,
    *,
    project_root: Path,
    label: str,
) -> Path:
    if path.is_absolute():
        pure = PurePosixPath(path.as_posix())
        if "." in pure.parts or ".." in pure.parts:
            raise FamilyContextError(
                f"{label} must be a canonical path"
            )
        candidate = path
    else:
        relative_input = _canonical_relative_path(
            path.as_posix(),
            label=label,
        )
        candidate = project_root / relative_input
    absolute = candidate.absolute()
    try:
        relative = absolute.relative_to(project_root)
    except ValueError as exc:
        raise FamilyContextError(
            f"{label} must remain below the project root"
        ) from exc
    canonical = _canonical_relative_path(
        relative.as_posix(),
        label=label,
    )
    if project_root / canonical != absolute:
        raise FamilyContextError(f"{label} is not a canonical path")
    return canonical


def _reject_symlink_components(
    project_root: Path,
    relative: Path,
    *,
    label: str,
) -> None:
    cursor = project_root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise FamilyContextError(
                f"{label} contains a symlink component: "
                f"{cursor.relative_to(project_root).as_posix()}"
            )


def _regular_pinned_file(
    *,
    project_root: Path,
    relative: Path,
    expected_sha256: str | None,
    label: str,
) -> PinnedFile:
    _reject_symlink_components(
        project_root,
        relative,
        label=label,
    )
    absolute = project_root / relative
    if not absolute.is_file():
        raise FamilyContextError(
            f"{label} is missing or not a regular file: "
            f"{relative.as_posix()}"
        )
    actual_sha256 = sha256_path(absolute)
    if (
        expected_sha256 is not None
        and actual_sha256 != expected_sha256
    ):
        raise FamilyContextError(
            f"{label} SHA-256 mismatch: {relative.as_posix()}"
        )
    return PinnedFile(
        path=relative,
        absolute_path=absolute,
        sha256=actual_sha256,
    )


def _contract_reference(
    value: Any,
    *,
    project_root: Path,
    label: str,
) -> PinnedFile:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise FamilyContextError(
            f"{label} must contain exactly path and sha256"
        )
    relative = _canonical_relative_path(
        value["path"],
        label=f"{label}.path",
    )
    digest = _require_sha256(
        value["sha256"],
        label=f"{label}.sha256",
    )
    return _regular_pinned_file(
        project_root=project_root,
        relative=relative,
        expected_sha256=digest,
        label=label,
    )


def _validate_contract_identity(
    payload: Mapping[str, Any],
    *,
    family_id: str,
    contract_name: str,
    path: Path,
) -> None:
    if contract_name == "design_brief":
        identity = payload.get("project_id")
        identity_label = "project_id"
    else:
        identity = payload.get("family_id")
        identity_label = "family_id"
    if identity != family_id:
        raise FamilyContextError(
            f"{path}: {contract_name}.{identity_label} does not match "
            f"family_id {family_id!r}"
        )


def _validate_family_contracts(
    payload: Mapping[str, Any],
    *,
    project_root: Path,
    family_id: str,
) -> dict[str, PinnedFile]:
    raw_contracts = payload.get("contracts")
    if not isinstance(raw_contracts, dict) or not raw_contracts:
        raise FamilyContextError(
            "family contract must pin at least one subordinate contract"
        )
    pinned: dict[str, PinnedFile] = {}
    seen_paths: set[Path] = set()
    for raw_name, raw_reference in raw_contracts.items():
        name = _require_slug(
            raw_name.replace("_", "-")
            if isinstance(raw_name, str)
            else raw_name,
            label="family contract name",
        )
        pinned_file = _contract_reference(
            raw_reference,
            project_root=project_root,
            label=f"family.contracts.{raw_name}",
        )
        if pinned_file.path in seen_paths:
            raise FamilyContextError(
                "family contract references must use unique paths"
            )
        seen_paths.add(pinned_file.path)
        try:
            contract_payload = _read_json_object(
                pinned_file.absolute_path,
                label=f"{raw_name} contract",
            )
        except FamilyContextError:
            raise
        _validate_contract_identity(
            contract_payload,
            family_id=family_id,
            contract_name=str(raw_name),
            path=pinned_file.path,
        )
        pinned[str(raw_name)] = pinned_file
    if "collections" not in pinned or "authoring" not in pinned:
        raise FamilyContextError(
            "family contract must pin collections and authoring contracts"
        )
    return pinned


def _validate_root_path(
    raw: Any,
    *,
    project_root: Path,
    family_id: str,
    label: str,
) -> tuple[Path, Path]:
    relative = _canonical_relative_path(raw, label=label)
    if family_id not in relative.parts:
        raise FamilyContextError(
            f"{label} must include the family_id namespace"
        )
    _reject_symlink_components(
        project_root,
        relative,
        label=label,
    )
    absolute = project_root / relative
    if absolute.exists() and not absolute.is_dir():
        raise FamilyContextError(
            f"{label} exists but is not a directory"
        )
    return relative, absolute


def _is_ancestor_or_equal(left: Path, right: Path) -> bool:
    try:
        right.relative_to(left)
    except ValueError:
        return False
    return True


def _require_disjoint_roots(
    roots: Mapping[str, Path],
) -> None:
    entries = list(roots.items())
    for index, (left_name, left) in enumerate(entries):
        for right_name, right in entries[index + 1 :]:
            if (
                _is_ancestor_or_equal(left, right)
                or _is_ancestor_or_equal(right, left)
            ):
                raise FamilyContextError(
                    f"workspace roots overlap: {left_name} and "
                    f"{right_name}"
                )


def _validate_recursive_file_pins(
    value: Any,
    *,
    project_root: Path,
    label: str,
) -> None:
    """Verify every declared path/hash pair in a collection contract."""

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_recursive_file_pins(
                item,
                project_root=project_root,
                label=f"{label}[{index}]",
            )
        return
    if not isinstance(value, dict):
        return

    pairs: list[tuple[str, str]] = []
    if "path" in value or "sha256" in value:
        if "path" not in value or "sha256" not in value:
            raise FamilyContextError(
                f"{label} has an incomplete path/sha256 pin"
            )
        pairs.append(("path", "sha256"))
    for key in value:
        if not key.endswith("_path") or key == "record_path":
            continue
        hash_key = f"{key.removesuffix('_path')}_sha256"
        if hash_key not in value:
            raise FamilyContextError(
                f"{label}.{key} is not hash-pinned"
            )
        pairs.append((key, hash_key))
    for path_key, hash_key in pairs:
        relative = _canonical_relative_path(
            value[path_key],
            label=f"{label}.{path_key}",
        )
        digest = _require_sha256(
            value[hash_key],
            label=f"{label}.{hash_key}",
        )
        _regular_pinned_file(
            project_root=project_root,
            relative=relative,
            expected_sha256=digest,
            label=f"{label}.{path_key}",
        )
    for key, item in value.items():
        if key not in {
            part for pair in pairs for part in pair
        }:
            _validate_recursive_file_pins(
                item,
                project_root=project_root,
                label=f"{label}.{key}",
            )


def _load_collections(
    collection_contract: PinnedFile,
    *,
    project_root: Path,
    family_id: str,
) -> tuple[dict[str, Any], dict[str, CollectionBinding]]:
    payload = _read_json_object(
        collection_contract.absolute_path,
        label="collection contract",
    )
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("record_type") != COLLECTION_RECORD_TYPE
        or payload.get("family_id") != family_id
    ):
        raise FamilyContextError(
            "collection contract schema or family_id mismatch"
        )
    raw_collections = payload.get("collections")
    if not isinstance(raw_collections, list) or not raw_collections:
        raise FamilyContextError(
            "collection contract must contain collections"
        )
    _validate_recursive_file_pins(
        payload,
        project_root=project_root,
        label="collection_contract",
    )
    collections: dict[str, CollectionBinding] = {}
    for index, record in enumerate(raw_collections):
        if not isinstance(record, dict):
            raise FamilyContextError(
                f"collection {index} must be an object"
            )
        collection_id = _require_slug(
            record.get("id"),
            label=f"collection {index}.id",
        )
        if collection_id in collections:
            raise FamilyContextError(
                f"duplicate collection id {collection_id!r}"
            )
        collections[collection_id] = CollectionBinding(
            collection_id=collection_id,
            record_sha256=canonical_json_sha256(record),
            record=record,
        )
    return payload, collections


def load_family_context(
    *,
    project_root: Path,
    family_contract_path: Path,
    pipeline_contract_path: Path,
) -> FamilyContext:
    """Load a context from two explicit contracts and no implicit fallback."""

    if project_root.is_symlink():
        raise FamilyContextError("project_root must not be a symlink")
    try:
        project_root = project_root.resolve(strict=True)
    except OSError as exc:
        raise FamilyContextError("project_root does not exist") from exc
    if not project_root.is_dir():
        raise FamilyContextError("project_root must be a directory")

    family_relative = _relative_to_project(
        family_contract_path,
        project_root=project_root,
        label="family contract path",
    )
    pipeline_relative = _relative_to_project(
        pipeline_contract_path,
        project_root=project_root,
        label="pipeline contract path",
    )
    family_contract = _regular_pinned_file(
        project_root=project_root,
        relative=family_relative,
        expected_sha256=None,
        label="family contract",
    )
    pipeline_contract = _regular_pinned_file(
        project_root=project_root,
        relative=pipeline_relative,
        expected_sha256=None,
        label="pipeline contract",
    )
    family_payload = _read_json_object(
        family_contract.absolute_path,
        label="family contract",
    )
    if (
        family_payload.get("schema_version") != SCHEMA_VERSION
        or family_payload.get("record_type") != FAMILY_RECORD_TYPE
    ):
        raise FamilyContextError(
            "unsupported family contract schema"
        )
    family_id = _require_slug(
        family_payload.get("family_id"),
        label="family_id",
    )
    pinned_contracts = _validate_family_contracts(
        family_payload,
        project_root=project_root,
        family_id=family_id,
    )

    raw_family_workspace = family_payload.get("workspace")
    if not isinstance(raw_family_workspace, dict) or set(
        raw_family_workspace
    ) != {
        "family_root",
        "source_root",
        "build_root",
        "release_root",
    }:
        raise FamilyContextError(
            "family workspace must declare exactly family/source/build/"
            "release roots"
        )
    family_root_relative, family_root = _validate_root_path(
        raw_family_workspace["family_root"],
        project_root=project_root,
        family_id=family_id,
        label="family.workspace.family_root",
    )
    if family_relative.parent != family_root_relative:
        raise FamilyContextError(
            "family contract must be directly inside family_root"
        )
    source_relative, source_root = _validate_root_path(
        raw_family_workspace["source_root"],
        project_root=project_root,
        family_id=family_id,
        label="family.workspace.source_root",
    )
    try:
        source_relative.relative_to(family_root_relative)
    except ValueError as exc:
        raise FamilyContextError(
            "source_root must remain below family_root"
        ) from exc
    if source_relative == family_root_relative:
        raise FamilyContextError(
            "source_root must be below, not equal to, family_root"
        )
    build_relative, build_root = _validate_root_path(
        raw_family_workspace["build_root"],
        project_root=project_root,
        family_id=family_id,
        label="family.workspace.build_root",
    )
    release_relative, release_root = _validate_root_path(
        raw_family_workspace["release_root"],
        project_root=project_root,
        family_id=family_id,
        label="family.workspace.release_root",
    )
    _require_disjoint_roots(
        {
            "family_root": family_root,
            "build_root": build_root,
            "release_root": release_root,
        }
    )

    licensing = family_payload.get("licensing")
    if not isinstance(licensing, dict):
        raise FamilyContextError(
            "family.licensing must be an object"
        )
    _contract_reference(
        {
            "path": licensing.get("path"),
            "sha256": licensing.get("sha256"),
        },
        project_root=project_root,
        label="family.licensing",
    )

    pipeline_payload = _read_json_object(
        pipeline_contract.absolute_path,
        label="pipeline contract",
    )
    expected_pipeline_keys = {
        "schema_version",
        "record_type",
        "family_id",
        "pipeline_id",
        "family_contract",
        "collection_contract",
        "authoring_contract",
        "workspace",
    }
    if set(pipeline_payload) != expected_pipeline_keys:
        raise FamilyContextError(
            "pipeline contract has an invalid top-level key set"
        )
    if (
        pipeline_payload.get("schema_version") != SCHEMA_VERSION
        or pipeline_payload.get("record_type")
        != PIPELINE_RECORD_TYPE
        or pipeline_payload.get("family_id") != family_id
    ):
        raise FamilyContextError(
            "pipeline contract schema or family_id mismatch"
        )
    pipeline_id = _require_slug(
        pipeline_payload.get("pipeline_id"),
        label="pipeline_id",
    )
    pinned_family_from_pipeline = _contract_reference(
        pipeline_payload["family_contract"],
        project_root=project_root,
        label="pipeline.family_contract",
    )
    if pinned_family_from_pipeline != family_contract:
        raise FamilyContextError(
            "pipeline family contract pin does not match the explicit "
            "family contract"
        )
    pinned_collection_from_pipeline = _contract_reference(
        pipeline_payload["collection_contract"],
        project_root=project_root,
        label="pipeline.collection_contract",
    )
    collection_contract = pinned_contracts["collections"]
    if pinned_collection_from_pipeline != collection_contract:
        raise FamilyContextError(
            "pipeline collection contract pin does not match the family "
            "contract chain"
        )
    pinned_authoring_from_pipeline = _contract_reference(
        pipeline_payload["authoring_contract"],
        project_root=project_root,
        label="pipeline.authoring_contract",
    )
    authoring_contract = pinned_contracts["authoring"]
    if pinned_authoring_from_pipeline != authoring_contract:
        raise FamilyContextError(
            "pipeline authoring contract pin does not match the family "
            "contract chain"
        )
    authoring_payload = _read_json_object(
        authoring_contract.absolute_path,
        label="authoring contract",
    )
    if (
        authoring_payload.get("schema_version") != SCHEMA_VERSION
        or authoring_payload.get("record_type")
        != AUTHORING_RECORD_TYPE
        or authoring_payload.get("family_id") != family_id
        or authoring_payload.get("pipeline_id") != pipeline_id
    ):
        raise FamilyContextError(
            "authoring contract schema, family_id, or pipeline_id "
            "mismatch"
        )
    _validate_recursive_file_pins(
        authoring_payload,
        project_root=project_root,
        label="authoring_contract",
    )
    raw_authoring_collection = authoring_payload.get(
        "collection_contract"
    )
    if raw_authoring_collection is None:
        raise FamilyContextError(
            "authoring contract must pin the collection contract"
        )
    pinned_collection_from_authoring = _contract_reference(
        raw_authoring_collection,
        project_root=project_root,
        label="authoring.collection_contract",
    )
    if pinned_collection_from_authoring != collection_contract:
        raise FamilyContextError(
            "authoring collection contract pin does not match the family "
            "contract chain"
        )

    raw_pipeline_workspace = pipeline_payload["workspace"]
    if not isinstance(raw_pipeline_workspace, dict) or set(
        raw_pipeline_workspace
    ) != {
        "source_root",
        "build_root",
        "cache_root",
        "release_root",
    }:
        raise FamilyContextError(
            "pipeline workspace must declare exactly source/build/cache/"
            "release roots"
        )
    expected_shared = {
        "source_root": source_relative.as_posix(),
        "build_root": build_relative.as_posix(),
        "release_root": release_relative.as_posix(),
    }
    for key, expected in expected_shared.items():
        if raw_pipeline_workspace.get(key) != expected:
            raise FamilyContextError(
                f"pipeline.workspace.{key} does not match the family "
                "contract"
            )
    _, cache_root = _validate_root_path(
        raw_pipeline_workspace["cache_root"],
        project_root=project_root,
        family_id=family_id,
        label="pipeline.workspace.cache_root",
    )
    if (
        _is_ancestor_or_equal(family_root, cache_root)
        or _is_ancestor_or_equal(cache_root, family_root)
    ):
        raise FamilyContextError(
            "workspace roots overlap: family_root and cache_root"
        )
    _require_disjoint_roots(
        {
            "source_root": source_root,
            "build_root": build_root,
            "cache_root": cache_root,
            "release_root": release_root,
        }
    )

    collection_payload, collections = _load_collections(
        collection_contract,
        project_root=project_root,
        family_id=family_id,
    )
    return FamilyContext(
        project_root=project_root,
        family_id=family_id,
        pipeline_id=pipeline_id,
        family_contract=family_contract,
        pipeline_contract=pipeline_contract,
        collection_contract=collection_contract,
        authoring_contract=authoring_contract,
        family_root=family_root,
        source_root=source_root,
        build_root=build_root,
        cache_root=cache_root,
        release_root=release_root,
        collections=collections,
        family_payload=family_payload,
        pipeline_payload=pipeline_payload,
        collection_payload=collection_payload,
        authoring_payload=authoring_payload,
    )


def validate_evidence_context(
    payload: Mapping[str, Any],
    *,
    context: FamilyContext,
    collection_id: str,
    field: str = "family_context",
    label: str = "evidence",
) -> Mapping[str, Any]:
    """Require an exact context chain in a descriptor or report payload."""

    if not isinstance(payload, Mapping):
        raise FamilyContextError(f"{label} must be an object")
    actual = payload.get(field)
    expected = context.evidence_binding(collection_id)
    if actual != expected:
        raise FamilyContextError(
            f"{label}.{field} does not match the verified family/"
            "pipeline/collection hash chain"
        )
    return actual


def add_family_context_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """Add mandatory, explicit contract arguments to a pipeline CLI."""

    parser.add_argument(
        "--family-contract",
        type=Path,
        required=True,
        help="explicit project-relative family contract",
    )
    parser.add_argument(
        "--pipeline-contract",
        type=Path,
        required=True,
        help="explicit project-relative pipeline contract",
    )


def load_family_context_from_args(
    args: argparse.Namespace,
    *,
    project_root: Path,
) -> FamilyContext:
    """Load context from arguments added by add_family_context_arguments."""

    return load_family_context(
        project_root=project_root,
        family_contract_path=args.family_contract,
        pipeline_contract_path=args.pipeline_contract,
    )


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        required=True,
    )
    add_family_context_arguments(parser)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    context = load_family_context_from_args(
        args,
        project_root=args.project_root,
    )
    print(
        json.dumps(
            {
                "family_id": context.family_id,
                "pipeline_id": context.pipeline_id,
                "collections": sorted(context.collections),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
