#!/usr/bin/env python3
"""Register and validate one immutable raster for any Han-delta collection."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from PIL import Image

from scripts.han_delta_repertoire import (
    HanDeltaBatch,
    HanDeltaRepertoire,
    HanDeltaRepertoireError,
    load_repertoire,
    sha256_path,
)

if TYPE_CHECKING:
    from scripts.han_delta_generation_history import GenerationHistory


ROOT = Path(__file__).resolve().parents[1]
COLLECTION_RECORD_TYPE = "imagegen-han-delta-collection"
SOURCE_RECORD_TYPE = "imagegen-han-delta-source"
VECTOR_PIPELINE = "imagegen-raster-potrace-quadratic-v2"
IDENTITY_MATERIALIZER = "scripts/materialize_han_delta_batches.py"
IDENTITY_COPYBOOK_ROLE = (
    "identity-reference-only-no-outline-import"
)
STYLE_REFERENCE_ROLE = "style-only-no-outline-import"
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class HanDeltaRegistrationError(ValueError):
    """A Han-delta collection or raster registration is invalid."""


@dataclass(frozen=True)
class HanDeltaCollection:
    """All immutable inputs and output roots for one Han delta."""

    project_root: Path
    path: Path
    sha256: str
    collection_id: str
    family_id: str
    vector_pipeline: str
    repertoire: HanDeltaRepertoire
    prompt_path: Path
    prompt_sha256: str
    style_reference_path: Path
    style_reference_sha256: str
    raster_directory: Path
    descriptor_directory: Path
    copybook_directory: Path
    build_directory: Path
    identity_copybook_required: bool
    identity_reference_fonts: tuple[Mapping[str, Any], ...]
    identity_compositions: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class IdentityCopybook:
    """One identity-only raster reference and its external provenance."""

    path: Path
    source_name: str
    source_url: str | None
    license: str
    materialization_draft: Path | None = None


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HanDeltaRegistrationError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise HanDeltaRegistrationError(
            f"{path}: {label} must be an object"
        )
    return value


def _slug(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SLUG_PATTERN.fullmatch(value) is None:
        raise HanDeltaRegistrationError(
            f"{label} must be a lowercase ASCII slug"
        )
    return value


def _nonempty(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise HanDeltaRegistrationError(
            f"{label} must be non-empty without surrounding whitespace"
        )
    return value


def _sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise HanDeltaRegistrationError(
            f"{label} must be a lowercase SHA-256"
        )
    return value


def _relative_path(value: Any, *, label: str) -> Path:
    if not isinstance(value, str):
        raise HanDeltaRegistrationError(f"{label} must be a string")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or not pure.parts
        or ".." in pure.parts
        or "." in pure.parts
        or pure.as_posix() != value
    ):
        raise HanDeltaRegistrationError(
            f"{label} must be a canonical project-relative POSIX path"
        )
    return Path(*pure.parts)


def _below_root(
    path: Path,
    *,
    project_root: Path,
    label: str,
    must_exist: bool,
) -> Path:
    root = project_root.resolve()
    try:
        resolved = path.resolve(strict=must_exist)
    except OSError as exc:
        raise HanDeltaRegistrationError(
            f"{label} is missing: {path}"
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise HanDeltaRegistrationError(
            f"{label} escapes the project root"
        ) from exc
    if path.is_symlink():
        raise HanDeltaRegistrationError(
            f"{label} must not be a symlink"
        )
    return resolved


def _regular_file(
    project_root: Path,
    relative: Path,
    *,
    label: str,
) -> Path:
    candidate = project_root.resolve() / relative
    resolved = _below_root(
        candidate,
        project_root=project_root,
        label=label,
        must_exist=True,
    )
    if not resolved.is_file():
        raise HanDeltaRegistrationError(
            f"{label} must be a regular file"
        )
    return resolved


def _directory(
    project_root: Path,
    relative: Path,
    *,
    label: str,
) -> Path:
    candidate = project_root.resolve() / relative
    resolved = _below_root(
        candidate,
        project_root=project_root,
        label=label,
        must_exist=False,
    )
    if resolved.exists() and not resolved.is_dir():
        raise HanDeltaRegistrationError(
            f"{label} must be a directory"
        )
    return resolved


def _png(path: Path, *, label: str) -> None:
    if path.suffix.lower() != ".png":
        raise HanDeltaRegistrationError(f"{label} must be a PNG")
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG" or image.width < 1 or image.height < 1:
                raise HanDeltaRegistrationError(
                    f"{label} is not a non-empty PNG"
                )
    except (OSError, ValueError) as exc:
        raise HanDeltaRegistrationError(
            f"{label} cannot be decoded as PNG: {path}"
        ) from exc


def _exact_record(
    value: Any,
    keys: set[str],
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise HanDeltaRegistrationError(
            f"{label} has an invalid key set"
        )
    return value


def _identity_reference_font(
    value: Any,
    *,
    index: int,
) -> dict[str, Any]:
    record = _exact_record(
        value,
        {"path", "sha256", "source_name", "source_url", "license"},
        label=f"collection identity reference font {index}",
    )
    raw_path = _nonempty(
        record["path"],
        label=f"collection identity reference font {index}.path",
    )
    pure = PurePosixPath(raw_path)
    if (
        not (pure.is_absolute() or raw_path.startswith("~/"))
        or ".." in pure.parts
        or "." in pure.parts
        or pure.as_posix() != raw_path
    ):
        raise HanDeltaRegistrationError(
            "identity reference font paths must be canonical absolute "
            "or home-relative POSIX paths"
        )
    source_url = record["source_url"]
    if source_url is not None:
        source_url = _nonempty(
            source_url,
            label=(
                f"collection identity reference font {index}.source_url"
            ),
        )
    return {
        "path": raw_path,
        "sha256": _sha256(
            record["sha256"],
            label=(
                f"collection identity reference font {index}.sha256"
            ),
        ),
        "source_name": _nonempty(
            record["source_name"],
            label=(
                f"collection identity reference font {index}.source_name"
            ),
        ),
        "source_url": source_url,
        "license": _nonempty(
            record["license"],
            label=(
                f"collection identity reference font {index}.license"
            ),
        ),
    }


def _identity_composition(
    value: Any,
    *,
    index: int,
) -> dict[str, Any]:
    record = _exact_record(
        value,
        {
            "character",
            "codepoint",
            "method",
            "display",
            "authorization",
            "components",
        },
        label=f"collection identity composition {index}",
    )
    character = record["character"]
    codepoint = record["codepoint"]
    if (
        not isinstance(character, str)
        or len(character) != 1
        or not isinstance(codepoint, str)
        or codepoint != f"U+{ord(character):04X}"
    ):
        raise HanDeltaRegistrationError(
            f"collection identity composition {index} identity mismatch"
        )
    if record["method"] != "vertical-ideographic-composition":
        raise HanDeltaRegistrationError(
            f"collection identity composition {index} method is unsupported"
        )
    raw_components = record["components"]
    if not isinstance(raw_components, list) or len(raw_components) != 2:
        raise HanDeltaRegistrationError(
            f"collection identity composition {index} needs two components"
        )
    components: list[dict[str, str]] = []
    for component_index, raw_component in enumerate(raw_components):
        component = _exact_record(
            raw_component,
            {"character", "codepoint", "placement"},
            label=(
                f"collection identity composition {index} "
                f"component {component_index}"
            ),
        )
        component_character = component["character"]
        component_codepoint = component["codepoint"]
        if (
            not isinstance(component_character, str)
            or len(component_character) != 1
            or not isinstance(component_codepoint, str)
            or component_codepoint
            != f"U+{ord(component_character):04X}"
        ):
            raise HanDeltaRegistrationError(
                f"collection identity composition {index} "
                f"component {component_index} identity mismatch"
            )
        components.append(
            {
                "character": component_character,
                "codepoint": component_codepoint,
                "placement": _nonempty(
                    component["placement"],
                    label=(
                        f"collection identity composition {index} "
                        f"component {component_index}.placement"
                    ),
                ),
            }
        )
    if [component["placement"] for component in components] != [
        "upper",
        "lower",
    ]:
        raise HanDeltaRegistrationError(
            f"collection identity composition {index} placements "
            "must be upper then lower"
        )
    return {
        "character": character,
        "codepoint": codepoint,
        "method": "vertical-ideographic-composition",
        "display": _nonempty(
            record["display"],
            label=f"collection identity composition {index}.display",
        ),
        "authorization": _nonempty(
            record["authorization"],
            label=(
                f"collection identity composition {index}.authorization"
            ),
        ),
        "components": components,
    }


def load_collection(
    path: Path,
    *,
    project_root: Path = ROOT,
) -> HanDeltaCollection:
    """Load a hash-pinned, reusable Han-delta collection contract."""

    project_root = project_root.resolve()
    if not path.is_absolute():
        path = project_root / path
    path = _below_root(
        path,
        project_root=project_root,
        label="collection",
        must_exist=True,
    )
    if not path.is_file():
        raise HanDeltaRegistrationError(
            "collection must be a regular file"
        )
    payload = _read_object(path, label="Han-delta collection")
    if set(payload) != {
        "schema_version",
        "record_type",
        "collection_id",
        "family_id",
        "vector_pipeline",
        "repertoire",
        "prompt",
        "style_reference",
        "identity_copybook_policy",
        "paths",
    }:
        raise HanDeltaRegistrationError(
            "collection has an invalid top-level key set"
        )
    if (
        payload.get("schema_version") != 1
        or payload.get("record_type") != COLLECTION_RECORD_TYPE
        or payload.get("vector_pipeline") != VECTOR_PIPELINE
    ):
        raise HanDeltaRegistrationError(
            "unsupported Han-delta collection contract"
        )
    collection_id = _slug(
        payload.get("collection_id"),
        label="collection_id",
    )
    family_id = _slug(payload.get("family_id"), label="family_id")

    repertoire_reference = _exact_record(
        payload.get("repertoire"),
        {"path", "sha256", "repertoire_id"},
        label="collection.repertoire",
    )
    repertoire_relative = _relative_path(
        repertoire_reference["path"],
        label="collection.repertoire.path",
    )
    repertoire_path = _regular_file(
        project_root,
        repertoire_relative,
        label="collection repertoire",
    )
    repertoire_sha256 = _sha256(
        repertoire_reference["sha256"],
        label="collection.repertoire.sha256",
    )
    if sha256_path(repertoire_path) != repertoire_sha256:
        raise HanDeltaRegistrationError(
            "collection repertoire hash mismatch"
        )
    try:
        repertoire = load_repertoire(
            repertoire_path,
            project_root=project_root,
        )
    except HanDeltaRepertoireError as exc:
        raise HanDeltaRegistrationError(str(exc)) from exc
    if (
        repertoire.family_id != family_id
        or repertoire.repertoire_id
        != repertoire_reference["repertoire_id"]
    ):
        raise HanDeltaRegistrationError(
            "collection/repertoire identity mismatch"
        )

    prompt_reference = _exact_record(
        payload.get("prompt"),
        {"path", "sha256"},
        label="collection.prompt",
    )
    prompt_path = _regular_file(
        project_root,
        _relative_path(
            prompt_reference["path"],
            label="collection.prompt.path",
        ),
        label="collection prompt",
    )
    prompt_sha256 = _sha256(
        prompt_reference["sha256"],
        label="collection.prompt.sha256",
    )
    if sha256_path(prompt_path) != prompt_sha256:
        raise HanDeltaRegistrationError(
            "collection prompt hash mismatch"
        )

    style_reference = _exact_record(
        payload.get("style_reference"),
        {"role", "path", "sha256"},
        label="collection.style_reference",
    )
    if style_reference["role"] != STYLE_REFERENCE_ROLE:
        raise HanDeltaRegistrationError(
            "collection style reference role is invalid"
        )
    style_reference_path = _regular_file(
        project_root,
        _relative_path(
            style_reference["path"],
            label="collection.style_reference.path",
        ),
        label="collection style reference",
    )
    style_reference_sha256 = _sha256(
        style_reference["sha256"],
        label="collection.style_reference.sha256",
    )
    if sha256_path(style_reference_path) != style_reference_sha256:
        raise HanDeltaRegistrationError(
            "collection style reference hash mismatch"
        )
    _png(style_reference_path, label="collection style reference")

    copybook_policy = _exact_record(
        payload.get("identity_copybook_policy"),
        {
            "required",
            "role",
            "directory",
            "external_font_binaries_committed",
            "materializer",
            "reference_fonts",
            "compositions",
        },
        label="collection.identity_copybook_policy",
    )
    if (
        not isinstance(copybook_policy["required"], bool)
        or copybook_policy["role"] != IDENTITY_COPYBOOK_ROLE
        or copybook_policy["external_font_binaries_committed"] is not False
        or copybook_policy["materializer"] != IDENTITY_MATERIALIZER
    ):
        raise HanDeltaRegistrationError(
            "collection identity-copybook policy is invalid"
        )
    raw_reference_fonts = copybook_policy["reference_fonts"]
    if not isinstance(raw_reference_fonts, list) or not raw_reference_fonts:
        raise HanDeltaRegistrationError(
            "collection identity-copybook reference fonts are missing"
        )
    identity_reference_fonts = tuple(
        _identity_reference_font(record, index=index)
        for index, record in enumerate(raw_reference_fonts)
    )
    resolved_reference_paths = [
        record["path"] for record in identity_reference_fonts
    ]
    if len(set(resolved_reference_paths)) != len(resolved_reference_paths):
        raise HanDeltaRegistrationError(
            "collection identity reference font paths must be unique"
        )
    raw_compositions = copybook_policy["compositions"]
    if not isinstance(raw_compositions, list):
        raise HanDeltaRegistrationError(
            "collection identity compositions must be an array"
        )
    identity_compositions = tuple(
        _identity_composition(record, index=index)
        for index, record in enumerate(raw_compositions)
    )
    composition_codepoints = [
        record["codepoint"] for record in identity_compositions
    ]
    if len(set(composition_codepoints)) != len(composition_codepoints):
        raise HanDeltaRegistrationError(
            "collection identity composition targets must be unique"
        )
    repertoire_codepoints = {
        f"U+{ord(character):04X}"
        for character in repertoire.characters
    }
    if not set(composition_codepoints) <= repertoire_codepoints:
        raise HanDeltaRegistrationError(
            "collection identity composition target is outside repertoire"
        )
    copybook_directory = _directory(
        project_root,
        _relative_path(
            copybook_policy["directory"],
            label="collection.identity_copybook_policy.directory",
        ),
        label="collection copybook directory",
    )

    paths = _exact_record(
        payload.get("paths"),
        {
            "raster_directory",
            "descriptor_directory",
            "build_directory",
        },
        label="collection.paths",
    )
    raster_directory = _directory(
        project_root,
        _relative_path(
            paths["raster_directory"],
            label="collection.paths.raster_directory",
        ),
        label="collection raster directory",
    )
    descriptor_directory = _directory(
        project_root,
        _relative_path(
            paths["descriptor_directory"],
            label="collection.paths.descriptor_directory",
        ),
        label="collection descriptor directory",
    )
    build_directory = _directory(
        project_root,
        _relative_path(
            paths["build_directory"],
            label="collection.paths.build_directory",
        ),
        label="collection build directory",
    )
    expected_raster_parent = raster_directory.relative_to(
        project_root
    ).as_posix()
    if any(
        PurePosixPath(
            str(record["raster_path"])
        ).parent.as_posix()
        != expected_raster_parent
        for record in repertoire.payload["batches"]
    ):
        raise HanDeltaRegistrationError(
            "repertoire raster paths do not match the collection"
        )
    return HanDeltaCollection(
        project_root=project_root,
        path=path,
        sha256=sha256_path(path),
        collection_id=collection_id,
        family_id=family_id,
        vector_pipeline=VECTOR_PIPELINE,
        repertoire=repertoire,
        prompt_path=prompt_path,
        prompt_sha256=prompt_sha256,
        style_reference_path=style_reference_path,
        style_reference_sha256=style_reference_sha256,
        raster_directory=raster_directory,
        descriptor_directory=descriptor_directory,
        copybook_directory=copybook_directory,
        build_directory=build_directory,
        identity_copybook_required=copybook_policy["required"],
        identity_reference_fonts=identity_reference_fonts,
        identity_compositions=identity_compositions,
    )


def _batch(
    collection: HanDeltaCollection,
    batch_id: str,
) -> HanDeltaBatch:
    expected_pattern = re.compile(
        rf"{re.escape(collection.repertoire.batch_prefix)}-[0-9]{{4}}"
    )
    if expected_pattern.fullmatch(batch_id) is None:
        raise HanDeltaRegistrationError(
            f"batch id must be "
            f"{collection.repertoire.batch_prefix}-NNNN"
        )
    matches = [
        batch
        for batch in collection.repertoire.batches
        if batch.batch_id == batch_id
    ]
    if len(matches) != 1:
        raise HanDeltaRegistrationError(
            f"{batch_id}: not in the frozen repertoire"
        )
    return matches[0]


def _relative_reference(path: Path, *, from_directory: Path) -> str:
    return Path(
        os.path.relpath(path, start=from_directory)
    ).as_posix()


def _identity_payload(
    *,
    collection: HanDeltaCollection,
    batch_id: str,
    descriptor_directory: Path,
    identity_copybook: IdentityCopybook | None,
) -> dict[str, Any] | None:
    if identity_copybook is None:
        if collection.identity_copybook_required:
            raise HanDeltaRegistrationError(
                f"{batch_id}: identity copybook is required"
            )
        return None
    path = _below_root(
        identity_copybook.path,
        project_root=collection.project_root,
        label="identity copybook",
        must_exist=True,
    )
    expected = collection.copybook_directory / f"{batch_id}.png"
    if path != expected.resolve():
        raise HanDeltaRegistrationError(
            f"identity copybook must be exactly {expected}"
        )
    _png(path, label="identity copybook")
    source_name = _nonempty(
        identity_copybook.source_name,
        label="identity copybook source name",
    )
    license_name = _nonempty(
        identity_copybook.license,
        label="identity copybook license",
    )
    source_url = identity_copybook.source_url
    if source_url is not None:
        source_url = _nonempty(
            source_url,
            label="identity copybook source URL",
        )
    draft_reference: dict[str, str] | None = None
    if (
        collection.identity_copybook_required
        and identity_copybook.materialization_draft is None
    ):
        raise HanDeltaRegistrationError(
            f"{batch_id}: required identity copybook must be loaded "
            "from its materialization draft"
        )
    if identity_copybook.materialization_draft is not None:
        from scripts.materialize_han_delta_batches import (
            HanDeltaMaterializationError,
            validate_draft,
        )

        draft_path = _below_root(
            identity_copybook.materialization_draft,
            project_root=collection.project_root,
            label="identity copybook materialization draft",
            must_exist=True,
        )
        try:
            draft = validate_draft(
                draft_path,
                project_root=collection.project_root,
            )
        except HanDeltaMaterializationError as exc:
            raise HanDeltaRegistrationError(str(exc)) from exc
        draft_identity = draft["identity_copybook"]
        draft_raster = (
            draft_path.parent / draft_identity["raster"]
        ).resolve()
        draft_provenance = draft_identity["provenance"]
        if (
            draft["batch_id"] != f"imagegen-{batch_id}"
            or draft_raster != path
            or draft_identity["raster_sha256"] != sha256_path(path)
            or draft_provenance["source_name"] != source_name
            or draft_provenance["source_url"] != source_url
            or draft_provenance["license"] != license_name
            or draft_provenance[
                "external_font_binary_committed"
            ]
            is not False
        ):
            raise HanDeltaRegistrationError(
                "identity copybook differs from its materialization draft"
            )
        draft_reference = {
            "path": _relative_reference(
                draft_path,
                from_directory=descriptor_directory,
            ),
            "sha256": sha256_path(draft_path),
        }
    return {
        "role": IDENTITY_COPYBOOK_ROLE,
        "raster": _relative_reference(
            path,
            from_directory=descriptor_directory,
        ),
        "raster_sha256": sha256_path(path),
        "provenance": {
            "source_name": source_name,
            "source_url": source_url,
            "license": license_name,
            "external_font_binary_committed": False,
            "materialization_draft": draft_reference,
        },
    }


def identity_copybook_from_draft(
    collection: HanDeltaCollection,
    batch_id: str,
) -> IdentityCopybook:
    """Load the canonical materialized copybook for one frozen batch."""

    from scripts.materialize_han_delta_batches import (
        HanDeltaMaterializationError,
        validate_draft,
    )

    draft_path = (
        collection.descriptor_directory / f"{batch_id}.draft.json"
    )
    try:
        draft = validate_draft(
            draft_path,
            project_root=collection.project_root,
        )
    except HanDeltaMaterializationError as exc:
        raise HanDeltaRegistrationError(str(exc)) from exc
    identity = draft["identity_copybook"]
    provenance = identity["provenance"]
    return IdentityCopybook(
        path=(draft_path.parent / identity["raster"]).resolve(),
        source_name=provenance["source_name"],
        source_url=provenance["source_url"],
        license=provenance["license"],
        materialization_draft=draft_path,
    )


def descriptor_payload(
    *,
    collection: HanDeltaCollection,
    batch_id: str,
    raster: Path,
    history: GenerationHistory,
    identity_copybook: IdentityCopybook | None = None,
) -> dict[str, Any]:
    """Create one exact pending descriptor without inferring approval."""

    batch = _batch(collection, batch_id)
    expected_raster = (
        collection.raster_directory / f"{batch_id}.png"
    ).resolve()
    raster = raster.resolve()
    if raster != expected_raster:
        raise HanDeltaRegistrationError(
            f"{batch_id}: raster must be exactly {expected_raster}"
        )
    if not raster.is_file() or raster.is_symlink():
        raise HanDeltaRegistrationError(
            f"{batch_id}: raster is missing or not a regular file"
        )
    _png(raster, label=f"{batch_id} raster")
    if (
        history.batch_id != batch_id
        or history.accepted_raster_path != raster
        or history.accepted_raster_sha256 != sha256_path(raster)
    ):
        raise HanDeltaRegistrationError(
            f"{batch_id}: generation history does not admit this raster"
        )
    descriptor_directory = collection.descriptor_directory
    identity = _identity_payload(
        collection=collection,
        batch_id=batch_id,
        descriptor_directory=descriptor_directory,
        identity_copybook=identity_copybook,
    )
    return {
        "schema_version": 1,
        "record_type": SOURCE_RECORD_TYPE,
        "vector_pipeline": collection.vector_pipeline,
        "batch_id": f"imagegen-{batch_id}",
        "state": "generated-unreviewed",
        "generator": "built-in-image_gen",
        "generation_history": {
            "path": _relative_reference(
                history.path,
                from_directory=descriptor_directory,
            ),
            "sha256": history.sha256,
            "step_count": history.step_count,
            "accepted_call_id": history.accepted_call_id,
        },
        "collection": {
            "path": _relative_reference(
                collection.path,
                from_directory=descriptor_directory,
            ),
            "sha256": collection.sha256,
            "collection_id": collection.collection_id,
            "family_id": collection.family_id,
        },
        "raster": _relative_reference(
            raster,
            from_directory=descriptor_directory,
        ),
        "raster_sha256": sha256_path(raster),
        "prompt": {
            "path": _relative_reference(
                history.exact_prompt_path,
                from_directory=descriptor_directory,
            ),
            "sha256": history.exact_prompt_sha256,
        },
        "intended_materialized_prompt": {
            "path": history.payload["intended_materialization"][
                "prompt"
            ]["path"],
            "sha256": history.payload["intended_materialization"][
                "prompt"
            ]["sha256"],
        },
        "prompt_template": {
            "path": _relative_reference(
                collection.prompt_path,
                from_directory=descriptor_directory,
            ),
            "sha256": collection.prompt_sha256,
        },
        "style_reference": {
            "role": STYLE_REFERENCE_ROLE,
            "raster": _relative_reference(
                collection.style_reference_path,
                from_directory=descriptor_directory,
            ),
            "raster_sha256": (
                collection.style_reference_sha256
            ),
        },
        "identity_copybook": identity,
        "repertoire": {
            "path": _relative_reference(
                collection.repertoire.path,
                from_directory=descriptor_directory,
            ),
            "sha256": collection.repertoire.sha256,
            "repertoire_id": (
                collection.repertoire.repertoire_id
            ),
            "sequence_sha256": (
                collection.repertoire.sequence_sha256
            ),
            "start_rank": batch.start_rank,
            "end_rank": batch.end_rank,
        },
        "grid": {
            "rows": 4,
            "columns": 4,
            "characters": list(batch.characters),
            "empty_grid_cells": batch.empty_grid_cells,
        },
        "review": {
            "topology": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }


def validate_descriptor(
    path: Path,
    *,
    project_root: Path = ROOT,
) -> dict[str, Any]:
    """Rebuild and compare one registered Han-delta descriptor."""

    project_root = project_root.resolve()
    path = _below_root(
        path,
        project_root=project_root,
        label="source descriptor",
        must_exist=True,
    )
    if not path.is_file():
        raise HanDeltaRegistrationError(
            "source descriptor must be a regular file"
        )
    payload = _read_object(path, label="Han-delta source descriptor")
    expected_keys = {
        "schema_version",
        "record_type",
        "vector_pipeline",
        "batch_id",
        "state",
        "generator",
        "generation_history",
        "collection",
        "raster",
        "raster_sha256",
        "prompt",
        "intended_materialized_prompt",
        "prompt_template",
        "style_reference",
        "identity_copybook",
        "repertoire",
        "grid",
        "review",
    }
    if set(payload) != expected_keys:
        raise HanDeltaRegistrationError(
            "source descriptor has an invalid top-level key set"
        )
    if (
        payload.get("schema_version") != 1
        or payload.get("record_type") != SOURCE_RECORD_TYPE
        or payload.get("vector_pipeline") != VECTOR_PIPELINE
        or payload.get("state") != "generated-unreviewed"
        or payload.get("generator") != "built-in-image_gen"
    ):
        raise HanDeltaRegistrationError(
            "unsupported Han-delta source descriptor"
        )
    collection_reference = _exact_record(
        payload.get("collection"),
        {"path", "sha256", "collection_id", "family_id"},
        label="descriptor.collection",
    )
    raw_collection_path = collection_reference["path"]
    if not isinstance(raw_collection_path, str):
        raise HanDeltaRegistrationError(
            "descriptor.collection.path must be a string"
        )
    collection_path = (path.parent / raw_collection_path).resolve()
    collection = load_collection(
        collection_path,
        project_root=project_root,
    )
    if (
        collection.sha256
        != _sha256(
            collection_reference["sha256"],
            label="descriptor.collection.sha256",
        )
        or collection.collection_id
        != collection_reference["collection_id"]
        or collection.family_id
        != collection_reference["family_id"]
    ):
        raise HanDeltaRegistrationError(
            "descriptor collection reference drifted"
        )
    history_reference = _exact_record(
        payload.get("generation_history"),
        {"path", "sha256", "step_count", "accepted_call_id"},
        label="descriptor.generation_history",
    )
    raw_history_path = history_reference["path"]
    if not isinstance(raw_history_path, str):
        raise HanDeltaRegistrationError(
            "descriptor generation history path must be a string"
        )
    from scripts.han_delta_generation_history import (
        HanDeltaHistoryError,
        load_history,
    )

    try:
        history = load_history(
            (path.parent / raw_history_path).resolve(),
            project_root=project_root,
        )
    except HanDeltaHistoryError as exc:
        raise HanDeltaRegistrationError(str(exc)) from exc
    if (
        history.sha256
        != _sha256(
            history_reference["sha256"],
            label="descriptor.generation_history.sha256",
        )
        or history.step_count != history_reference["step_count"]
        or history.accepted_call_id
        != history_reference["accepted_call_id"]
    ):
        raise HanDeltaRegistrationError(
            "descriptor generation history reference drifted"
        )
    expected_descriptor = (
        collection.descriptor_directory
        / f"{str(payload['batch_id']).removeprefix('imagegen-')}"
        ".source.json"
    ).resolve()
    if path != expected_descriptor:
        raise HanDeltaRegistrationError(
            f"source descriptor must be exactly {expected_descriptor}"
        )
    raster_raw = payload.get("raster")
    if not isinstance(raster_raw, str):
        raise HanDeltaRegistrationError(
            "descriptor raster path must be a string"
        )
    raster = (path.parent / raster_raw).resolve()
    identity_payload = payload.get("identity_copybook")
    identity: IdentityCopybook | None
    if identity_payload is None:
        identity = None
    else:
        identity_record = _exact_record(
            identity_payload,
            {"role", "raster", "raster_sha256", "provenance"},
            label="descriptor.identity_copybook",
        )
        if identity_record["role"] != IDENTITY_COPYBOOK_ROLE:
            raise HanDeltaRegistrationError(
                "identity copybook role drifted"
            )
        provenance = _exact_record(
            identity_record["provenance"],
            {
                "source_name",
                "source_url",
                "license",
                "external_font_binary_committed",
                "materialization_draft",
            },
            label="descriptor.identity_copybook.provenance",
        )
        if provenance["external_font_binary_committed"] is not False:
            raise HanDeltaRegistrationError(
                "external font binary must not be committed"
            )
        raw_draft = provenance["materialization_draft"]
        materialization_draft: Path | None
        if raw_draft is None:
            materialization_draft = None
        else:
            draft_record = _exact_record(
                raw_draft,
                {"path", "sha256"},
                label=(
                    "descriptor.identity_copybook.provenance."
                    "materialization_draft"
                ),
            )
            raw_draft_path = draft_record["path"]
            if not isinstance(raw_draft_path, str):
                raise HanDeltaRegistrationError(
                    "identity materialization draft path must be a string"
                )
            materialization_draft = (
                path.parent / raw_draft_path
            ).resolve()
            if (
                not materialization_draft.is_file()
                or sha256_path(materialization_draft)
                != _sha256(
                    draft_record["sha256"],
                    label=(
                        "descriptor identity materialization "
                        "draft hash"
                    ),
                )
            ):
                raise HanDeltaRegistrationError(
                    "identity materialization draft hash mismatch"
                )
        raw_identity_path = identity_record["raster"]
        if not isinstance(raw_identity_path, str):
            raise HanDeltaRegistrationError(
                "identity copybook raster path must be a string"
            )
        identity = IdentityCopybook(
            path=(path.parent / raw_identity_path).resolve(),
            source_name=provenance["source_name"],
            source_url=provenance["source_url"],
            license=provenance["license"],
            materialization_draft=materialization_draft,
        )
    raw_batch_id = payload.get("batch_id")
    if (
        not isinstance(raw_batch_id, str)
        or not raw_batch_id.startswith("imagegen-")
    ):
        raise HanDeltaRegistrationError(
            "descriptor batch_id must start with imagegen-"
        )
    rebuilt = descriptor_payload(
        collection=collection,
        batch_id=raw_batch_id.removeprefix("imagegen-"),
        raster=raster,
        history=history,
        identity_copybook=identity,
    )
    if payload != rebuilt:
        raise HanDeltaRegistrationError(
            "source descriptor differs from the recomputed collection batch"
        )
    return rebuilt


def _write_new_or_identical(
    path: Path,
    payload: Mapping[str, Any],
) -> bool:
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.is_symlink() or path.read_bytes() != encoded:
            raise HanDeltaRegistrationError(
                f"refusing to overwrite a different descriptor: {path}"
            )
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
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
    return True


def register(
    *,
    collection_path: Path,
    batch_id: str,
    raster: Path | None = None,
    identity_copybook: IdentityCopybook | None = None,
    project_root: Path = ROOT,
) -> Path:
    """Register one raster as pending and validate the emitted descriptor."""

    project_root = project_root.resolve()
    collection = load_collection(
        collection_path,
        project_root=project_root,
    )
    if (
        identity_copybook is None
        and collection.identity_copybook_required
    ):
        identity_copybook = identity_copybook_from_draft(
            collection,
            batch_id,
        )
    if raster is not None and not raster.is_absolute():
        raster = project_root / raster
    raster = raster or (
        collection.raster_directory / f"{batch_id}.png"
    )
    from scripts.han_delta_generation_history import (
        HanDeltaHistoryError,
        load_history,
    )

    try:
        history = load_history(
            collection.descriptor_directory
            / f"{batch_id}.history.json",
            project_root=project_root,
        )
    except HanDeltaHistoryError as exc:
        raise HanDeltaRegistrationError(str(exc)) from exc
    payload = descriptor_payload(
        collection=collection,
        batch_id=batch_id,
        raster=raster,
        history=history,
        identity_copybook=identity_copybook,
    )
    output = (
        collection.descriptor_directory
        / f"{batch_id}.source.json"
    )
    created = _write_new_or_identical(output, payload)
    try:
        validate_descriptor(output, project_root=project_root)
    except Exception:
        if created:
            output.unlink()
        raise
    return output


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("batch_id")
    parser.add_argument("--raster", type=Path)
    parser.add_argument("--identity-copybook", type=Path)
    parser.add_argument("--identity-source-name")
    parser.add_argument("--identity-source-url")
    parser.add_argument("--identity-license")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    collection_path = args.collection
    if not collection_path.is_absolute():
        collection_path = project_root / collection_path
    identity_values = (
        args.identity_copybook,
        args.identity_source_name,
        args.identity_license,
    )
    if any(value is not None for value in identity_values) and any(
        value is None for value in identity_values
    ):
        raise SystemExit(
            "--identity-copybook, --identity-source-name, and "
            "--identity-license must be provided together"
        )
    identity = (
        IdentityCopybook(
            path=(
                args.identity_copybook
                if args.identity_copybook.is_absolute()
                else project_root / args.identity_copybook
            ),
            source_name=args.identity_source_name,
            source_url=args.identity_source_url,
            license=args.identity_license,
        )
        if args.identity_copybook is not None
        else None
    )
    try:
        output = register(
            collection_path=collection_path,
            batch_id=args.batch_id,
            raster=args.raster,
            identity_copybook=identity,
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise SystemExit(str(exc)) from exc
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
