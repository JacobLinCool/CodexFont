#!/usr/bin/env python3
"""Build and validate fail-closed image-generation histories for Han sheets."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Mapping, Sequence

from scripts.materialize_han_delta_batches import (
    HanDeltaMaterializationError,
    validate_draft,
)
from scripts.register_han_delta_sheet import (
    HanDeltaCollection,
    HanDeltaRegistrationError,
    load_collection,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTION = Path(
    "sources/imagegen/collections/"
    "clear-hand-tc-dictionary-salience-1216.json"
)
RECORD_TYPE = "imagegen-generation-history"
GENERATOR = "built-in-image_gen"
CALL_ID_PATTERN = re.compile(
    r"(?:"
    r"exec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}"
    r"|call_[0-9A-Za-z]{24}"
    r")"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
OPERATIONS = frozenset(
    {"generate", "correction", "component-generate", "assembly"}
)
DISPOSITIONS = frozenset({"rejected", "intermediate", "accepted"})
REFERENCE_ROLES = frozenset(
    {
        "style-reference",
        "identity-copybook",
        "parent-output",
        "component-output",
    }
)
RETENTIONS = frozenset(
    {
        "retained-reference",
        "hash-only-rejected",
        "hash-only-intermediate",
        "retained-final",
    }
)
ASSEMBLY_ID_PATTERN = re.compile(r"assembly-[0-9a-f]{64}")


class HanDeltaHistoryError(RuntimeError):
    """Generation provenance is incomplete, ambiguous, or inconsistent."""


@dataclass(frozen=True)
class InputImageSpec:
    """One exact image supplied to one generator call."""

    role: str
    retention: str
    path: Path | None
    sha256: str


@dataclass(frozen=True)
class GenerationStepSpec:
    """One actual generation or correction call in chronological order."""

    operation: str
    disposition: str
    call_id: str
    prompt_path: Path
    input_images: tuple[InputImageSpec, ...]
    parent_output_sha256: str | None
    output_retention: str
    output_path: Path | None
    output_sha256: str


@dataclass(frozen=True)
class GenerationHistory:
    """One fully validated canonical history and its accepted final raster."""

    path: Path
    sha256: str
    batch_id: str
    exact_prompt_path: Path
    exact_prompt_sha256: str
    accepted_call_id: str
    accepted_raster_path: Path
    accepted_raster_sha256: str
    step_count: int
    payload: Mapping[str, Any]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise HanDeltaHistoryError(
            f"{label} must be a lowercase SHA-256"
        )
    return value


def _exact_record(
    value: Any,
    keys: set[str],
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise HanDeltaHistoryError(f"{label} has an invalid key set")
    return value


def _relative_reference(path: Path, *, from_directory: Path) -> str:
    try:
        return path.resolve().relative_to(
            from_directory.resolve()
        ).as_posix()
    except ValueError:
        return Path(
            os.path.relpath(
                path.resolve(),
                start=from_directory.resolve(),
            )
        ).as_posix()


def _resolve_reference(
    raw: Any,
    *,
    parent: Path,
    project_root: Path,
    label: str,
    allow_none: bool = False,
) -> Path | None:
    if raw is None and allow_none:
        return None
    if not isinstance(raw, str):
        raise HanDeltaHistoryError(f"{label} must be a relative path")
    pure = PurePosixPath(raw)
    parts_after_parent_prefix = list(pure.parts)
    while (
        parts_after_parent_prefix
        and parts_after_parent_prefix[0] == ".."
    ):
        parts_after_parent_prefix.pop(0)
    if (
        pure.is_absolute()
        or not pure.parts
        or "." in pure.parts
        or ".." in parts_after_parent_prefix
        or pure.as_posix() != raw
    ):
        raise HanDeltaHistoryError(
            f"{label} must be a canonical relative POSIX path"
        )
    root = project_root.resolve()
    lexical = Path(
        os.path.normpath(parent / Path(*pure.parts))
    )
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise HanDeltaHistoryError(
            f"{label} escapes the project root"
        ) from exc
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise HanDeltaHistoryError(
                f"{label} must not traverse a symlink"
            )
    candidate = lexical.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HanDeltaHistoryError(
            f"{label} escapes the project root"
        ) from exc
    return candidate


def _regular_file(path: Path, *, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise HanDeltaHistoryError(
            f"{label} must be a regular non-symlink file: {path}"
        )


def _batch_characters(
    collection: HanDeltaCollection,
    batch_id: str,
) -> tuple[str, ...]:
    batches = [
        batch
        for batch in collection.repertoire.batches
        if batch.batch_id == batch_id
    ]
    if len(batches) != 1:
        raise HanDeltaHistoryError(
            f"{batch_id}: outside the frozen repertoire"
        )
    return batches[0].characters


def _actual_prompt_text(
    path: Path,
    *,
    batch_id: str,
    sequence: int,
    characters: Sequence[str],
    canonical_directory: Path,
    require_identity_manifest: bool,
) -> None:
    path = Path(os.path.abspath(path))
    _regular_file(path, label="actual tool prompt")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise HanDeltaHistoryError(
            f"{path}: actual tool prompt is not UTF-8"
        ) from exc
    if not text.strip() or "\x00" in text:
        raise HanDeltaHistoryError(
            f"{path}: actual tool prompt is empty or binary"
        )
    expected = (
        canonical_directory
        / f"{batch_id}.tool-step-{sequence:04d}.txt"
    ).resolve()
    if path != expected:
        raise HanDeltaHistoryError(
            f"actual tool prompt must be exactly {expected}"
        )
    if require_identity_manifest:
        rows = [
            "".join(characters[index : index + 4])
            for index in range(0, len(characters), 4)
        ]
        cursor = 0
        for row in rows:
            position = text.find(row, cursor)
            if position < 0:
                raise HanDeltaHistoryError(
                    f"{path}: generation prompt omits ordered row "
                    f"{row!r}"
                )
            cursor = position + len(row)
        cursor = 0
        for index, character in enumerate(characters, start=1):
            bare_cell = (
                f"Cell {index:02d}: U+{ord(character):04X} "
                f"{character}"
            )
            candidates = tuple(
                f"Cell {index:02d}{separator} "
                f"U+{ord(character):04X} {wrapper}{character}{wrapper}"
                for separator in (":", "")
                for wrapper in ("", "`")
            )
            matches = [
                (position, candidate)
                for candidate in candidates
                if (position := text.find(candidate, cursor)) >= 0
            ]
            escaped_character = re.escape(character)
            bare_match = re.search(
                rf"(?<![0-9A-Za-z]){index:02d} "
                rf"U\+{ord(character):04X} "
                rf"(?:{escaped_character}|`{escaped_character}`)"
                rf"(?=$|[;.\n])",
                text[cursor:],
            )
            if bare_match is not None:
                matches.append(
                    (
                        cursor + bare_match.start(),
                        bare_match.group(0),
                    )
                )
            if not matches:
                raise HanDeltaHistoryError(
                    f"{path}: generation prompt omits ordered "
                    f"{bare_cell!r} (colon optional; character may be "
                    "Markdown-quoted; an exact bare NN label is also "
                    "accepted)"
                )
            position, matched = min(matches, key=lambda value: value[0])
            cursor = position + len(matched)


def _path_record(
    path: Path,
    *,
    parent: Path,
) -> dict[str, str]:
    _regular_file(path, label="pinned file")
    return {
        "path": _relative_reference(path, from_directory=parent),
        "sha256": sha256_path(path),
    }


def _input_payload(
    value: InputImageSpec,
    *,
    history_directory: Path,
) -> dict[str, Any]:
    if value.role not in REFERENCE_ROLES:
        raise HanDeltaHistoryError(
            f"unsupported input image role: {value.role}"
        )
    if value.retention not in RETENTIONS:
        raise HanDeltaHistoryError(
            f"unsupported input retention: {value.retention}"
        )
    digest = _sha256(value.sha256, label="input image SHA-256")
    if value.retention in {
        "hash-only-rejected",
        "hash-only-intermediate",
    }:
        expected_role = (
            "parent-output"
            if value.retention == "hash-only-rejected"
            else "component-output"
        )
        if value.role != expected_role or value.path is not None:
            raise HanDeltaHistoryError(
                "hash-only input role and retention do not match"
            )
        raw_path = None
    else:
        if (
            value.role == "parent-output"
            or value.retention != "retained-reference"
        ):
            raise HanDeltaHistoryError(
                "style and copybook inputs must be retained references"
            )
        if value.path is None:
            raise HanDeltaHistoryError(
                "retained input image requires a path"
            )
        _regular_file(value.path, label="input image")
        if sha256_path(value.path) != digest:
            raise HanDeltaHistoryError(
                f"input image hash mismatch: {value.path}"
            )
        raw_path = _relative_reference(
            value.path,
            from_directory=history_directory,
        )
    return {
        "role": value.role,
        "retention": value.retention,
        "path": raw_path,
        "sha256": digest,
    }


def history_payload(
    collection: HanDeltaCollection,
    *,
    batch_id: str,
    steps: Sequence[GenerationStepSpec],
) -> dict[str, Any]:
    """Build one canonical generation history from explicit actual calls."""

    characters = _batch_characters(collection, batch_id)
    if not steps:
        raise HanDeltaHistoryError("generation history cannot be empty")
    history_directory = collection.descriptor_directory
    draft_path = history_directory / f"{batch_id}.draft.json"
    try:
        draft = validate_draft(
            draft_path,
            project_root=collection.project_root,
        )
    except HanDeltaMaterializationError as exc:
        raise HanDeltaHistoryError(str(exc)) from exc
    intended_prompt_path = (
        draft_path.parent / draft["prompt"]["path"]
    ).resolve()
    intended = {
        "draft": _path_record(
            draft_path,
            parent=history_directory,
        ),
        "prompt": _path_record(
            intended_prompt_path,
            parent=history_directory,
        ),
    }
    expected_style = (
        draft_path.parent / draft["style_reference"]["raster"]
    ).resolve()
    expected_copybook = (
        draft_path.parent / draft["identity_copybook"]["raster"]
    ).resolve()
    expected_reference_hashes = {
        "style-reference": draft["style_reference"]["raster_sha256"],
        "identity-copybook": draft["identity_copybook"][
            "raster_sha256"
        ],
    }

    records: list[dict[str, Any]] = []
    earlier_outputs: dict[str, tuple[str, str, str]] = {}
    seen_calls: set[str] = set()
    for sequence, step in enumerate(steps, start=1):
        if step.operation not in OPERATIONS:
            raise HanDeltaHistoryError(
                f"step {sequence}: unsupported operation"
            )
        if step.disposition not in DISPOSITIONS:
            raise HanDeltaHistoryError(
                f"step {sequence}: unsupported disposition"
            )
        valid_execution_id = (
            isinstance(step.call_id, str)
            and (
                (
                    step.operation == "assembly"
                    and ASSEMBLY_ID_PATTERN.fullmatch(step.call_id)
                    is not None
                )
                or (
                    step.operation != "assembly"
                    and CALL_ID_PATTERN.fullmatch(step.call_id)
                    is not None
                )
            )
        )
        if not valid_execution_id or step.call_id in seen_calls:
            raise HanDeltaHistoryError(
                f"step {sequence}: call id is invalid or duplicated"
            )
        seen_calls.add(step.call_id)
        if sequence == 1 and step.operation != "generate":
            raise HanDeltaHistoryError(
                "the first generation step must be generate"
            )
        _actual_prompt_text(
            step.prompt_path,
            batch_id=batch_id,
            sequence=sequence,
            characters=characters,
            canonical_directory=history_directory,
            require_identity_manifest=(step.operation == "generate"),
        )
        if (
            step.operation == "assembly"
            and step.call_id
            != f"assembly-{sha256_path(step.prompt_path)}"
        ):
            raise HanDeltaHistoryError(
                f"step {sequence}: assembly id must pin its manifest"
            )
        inputs = [
            _input_payload(
                value,
                history_directory=history_directory,
            )
            for value in step.input_images
        ]
        roles = [value["role"] for value in inputs]
        if step.operation in {"generate", "component-generate"}:
            if (
                step.parent_output_sha256 is not None
                or roles
                != ["style-reference", "identity-copybook"]
            ):
                raise HanDeltaHistoryError(
                    f"step {sequence}: {step.operation} must use "
                    "style and copybook only, without a parent"
                )
        elif step.operation == "correction":
            parent_digest = _sha256(
                step.parent_output_sha256,
                label=f"step {sequence} parent output",
            )
            if (
                parent_digest not in earlier_outputs
                or earlier_outputs[parent_digest][0]
                not in {"generate", "correction"}
                or not inputs
                or inputs[0]["role"] != "parent-output"
                or inputs[0]["retention"] != "hash-only-rejected"
                or inputs[0]["path"] is not None
                or inputs[0]["sha256"] != parent_digest
            ):
                raise HanDeltaHistoryError(
                    f"step {sequence}: parent hash chain is broken"
                )
            if len(set(roles)) != len(roles):
                raise HanDeltaHistoryError(
                    f"step {sequence}: input roles are duplicated"
                )
        else:
            parent_digest = _sha256(
                step.parent_output_sha256,
                label=f"step {sequence} parent output",
            )
            if (
                parent_digest not in earlier_outputs
                or earlier_outputs[parent_digest][0]
                not in {"generate", "correction"}
                or roles != ["parent-output", "component-output"]
                or inputs[0]["retention"] != "hash-only-rejected"
                or inputs[0]["path"] is not None
                or inputs[0]["sha256"] != parent_digest
                or inputs[1]["retention"] != "hash-only-intermediate"
                or inputs[1]["path"] is not None
                or inputs[1]["sha256"] not in earlier_outputs
                or earlier_outputs[inputs[1]["sha256"]][0]
                != "component-generate"
            ):
                raise HanDeltaHistoryError(
                    f"step {sequence}: assembly inputs are not "
                    "earlier sheet and component outputs"
                )
        for input_record in inputs:
            role = input_record["role"]
            if role in expected_reference_hashes:
                expected_path = (
                    expected_style
                    if role == "style-reference"
                    else expected_copybook
                )
                resolved = (
                    history_directory / input_record["path"]
                ).resolve()
                if (
                    resolved != expected_path
                    or input_record["sha256"]
                    != expected_reference_hashes[role]
                ):
                    raise HanDeltaHistoryError(
                        f"step {sequence}: {role} differs from draft"
                    )
            elif role == "component-output":
                component = earlier_outputs.get(input_record["sha256"])
                if component is None or component[0] != "component-generate":
                    raise HanDeltaHistoryError(
                        f"step {sequence}: component input is not an "
                        "earlier generated component"
                    )
        output_digest = _sha256(
            step.output_sha256,
            label=f"step {sequence} output",
        )
        is_final = sequence == len(steps)
        if is_final:
            expected_output = (
                collection.raster_directory / f"{batch_id}.png"
            ).resolve()
            if (
                step.operation == "component-generate"
                or
                step.disposition != "accepted"
                or step.output_retention != "retained-final"
                or step.output_path is None
                or step.output_path.resolve() != expected_output
            ):
                raise HanDeltaHistoryError(
                    "final step must retain the accepted canonical raster"
                )
            _regular_file(step.output_path, label="accepted final raster")
            if sha256_path(step.output_path) != output_digest:
                raise HanDeltaHistoryError(
                    "accepted final raster hash mismatch"
                )
            output_path: str | None = _relative_reference(
                step.output_path,
                from_directory=history_directory,
            )
        else:
            if step.operation == "component-generate":
                expected_disposition = "intermediate"
                expected_retention = "hash-only-intermediate"
            else:
                expected_disposition = "rejected"
                expected_retention = "hash-only-rejected"
            if (
                step.disposition != expected_disposition
                or step.output_retention != expected_retention
                or step.output_path is not None
            ):
                raise HanDeltaHistoryError(
                    "non-final output disposition or retention is invalid"
                )
            output_path = None
        records.append(
            {
                "sequence": sequence,
                "operation": step.operation,
                "disposition": step.disposition,
                "call_id": step.call_id,
                "prompt": _path_record(
                    step.prompt_path,
                    parent=history_directory,
                ),
                "input_images": inputs,
                "parent_output_sha256": (
                    step.parent_output_sha256
                    if sequence > 1
                    else None
                ),
                "output": {
                    "retention": step.output_retention,
                    "path": output_path,
                    "sha256": output_digest,
                },
            }
        )
        if output_digest in earlier_outputs:
            raise HanDeltaHistoryError(
                f"step {sequence}: output hash duplicates an earlier step"
            )
        earlier_outputs[output_digest] = (
            step.operation,
            step.disposition,
            step.output_retention,
        )
    accepted = records[-1]
    return {
        "schema_version": 1,
        "record_type": RECORD_TYPE,
        "batch_id": batch_id,
        "generator": GENERATOR,
        "collection": {
            "path": _relative_reference(
                collection.path,
                from_directory=history_directory,
            ),
            "sha256": collection.sha256,
            "collection_id": collection.collection_id,
            "family_id": collection.family_id,
        },
        "intended_materialization": intended,
        "steps": records,
        "canonical_output": {
            "accepted_step": accepted["sequence"],
            "path": accepted["output"]["path"],
            "sha256": accepted["output"]["sha256"],
        },
    }


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HanDeltaHistoryError(
            f"{path}: cannot read generation history: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise HanDeltaHistoryError(
            f"{path}: generation history must be an object"
        )
    return value


def _step_specs(
    payload: Mapping[str, Any],
    *,
    history_path: Path,
    project_root: Path,
) -> tuple[GenerationStepSpec, ...]:
    raw_steps = payload.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise HanDeltaHistoryError("history steps are missing")
    specs: list[GenerationStepSpec] = []
    for index, raw in enumerate(raw_steps, start=1):
        step = _exact_record(
            raw,
            {
                "sequence",
                "operation",
                "disposition",
                "call_id",
                "prompt",
                "input_images",
                "parent_output_sha256",
                "output",
            },
            label=f"history step {index}",
        )
        if step["sequence"] != index:
            raise HanDeltaHistoryError(
                "history step sequence is not contiguous"
            )
        prompt = _exact_record(
            step["prompt"],
            {"path", "sha256"},
            label=f"history step {index}.prompt",
        )
        prompt_path = _resolve_reference(
            prompt["path"],
            parent=history_path.parent,
            project_root=project_root,
            label=f"history step {index}.prompt.path",
        )
        assert prompt_path is not None
        if (
            not prompt_path.is_file()
            or sha256_path(prompt_path)
            != _sha256(
                prompt["sha256"],
                label=f"history step {index}.prompt.sha256",
            )
        ):
            raise HanDeltaHistoryError(
                f"history step {index}: prompt hash mismatch"
            )
        raw_inputs = step["input_images"]
        if not isinstance(raw_inputs, list):
            raise HanDeltaHistoryError(
                f"history step {index}: input_images must be an array"
            )
        inputs: list[InputImageSpec] = []
        for input_index, raw_input in enumerate(raw_inputs):
            image = _exact_record(
                raw_input,
                {"role", "retention", "path", "sha256"},
                label=(
                    f"history step {index}.input_images[{input_index}]"
                ),
            )
            image_path = _resolve_reference(
                image["path"],
                parent=history_path.parent,
                project_root=project_root,
                label=(
                    f"history step {index}.input_images"
                    f"[{input_index}].path"
                ),
                allow_none=True,
            )
            inputs.append(
                InputImageSpec(
                    role=image["role"],
                    retention=image["retention"],
                    path=image_path,
                    sha256=image["sha256"],
                )
            )
        output = _exact_record(
            step["output"],
            {"retention", "path", "sha256"},
            label=f"history step {index}.output",
        )
        output_path = _resolve_reference(
            output["path"],
            parent=history_path.parent,
            project_root=project_root,
            label=f"history step {index}.output.path",
            allow_none=True,
        )
        specs.append(
            GenerationStepSpec(
                operation=step["operation"],
                disposition=step["disposition"],
                call_id=step["call_id"],
                prompt_path=prompt_path,
                input_images=tuple(inputs),
                parent_output_sha256=step["parent_output_sha256"],
                output_retention=output["retention"],
                output_path=output_path,
                output_sha256=output["sha256"],
            )
        )
    return tuple(specs)


def load_history(
    path: Path,
    *,
    project_root: Path = ROOT,
) -> GenerationHistory:
    """Load and fully recompute one canonical generation history."""

    project_root = project_root.resolve()
    path = path.resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise HanDeltaHistoryError(
            "generation history escapes the project root"
        ) from exc
    _regular_file(path, label="generation history")
    payload = _read_object(path)
    if set(payload) != {
        "schema_version",
        "record_type",
        "batch_id",
        "generator",
        "collection",
        "intended_materialization",
        "steps",
        "canonical_output",
    }:
        raise HanDeltaHistoryError(
            "generation history top-level key set drifted"
        )
    if (
        payload.get("schema_version") != 1
        or payload.get("record_type") != RECORD_TYPE
        or payload.get("generator") != GENERATOR
    ):
        raise HanDeltaHistoryError(
            "unsupported generation history contract"
        )
    batch_id = payload.get("batch_id")
    if not isinstance(batch_id, str):
        raise HanDeltaHistoryError("history batch_id is malformed")
    expected_path = path.parent / f"{batch_id}.history.json"
    if path != expected_path.resolve():
        raise HanDeltaHistoryError(
            f"generation history must be exactly {expected_path}"
        )
    collection_record = _exact_record(
        payload["collection"],
        {"path", "sha256", "collection_id", "family_id"},
        label="history.collection",
    )
    collection_path = _resolve_reference(
        collection_record["path"],
        parent=path.parent,
        project_root=project_root,
        label="history.collection.path",
    )
    assert collection_path is not None
    try:
        collection = load_collection(
            collection_path,
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise HanDeltaHistoryError(str(exc)) from exc
    if (
        collection.sha256
        != _sha256(
            collection_record["sha256"],
            label="history.collection.sha256",
        )
        or collection.collection_id
        != collection_record["collection_id"]
        or collection.family_id != collection_record["family_id"]
    ):
        raise HanDeltaHistoryError(
            "generation history collection reference drifted"
        )
    rebuilt = history_payload(
        collection,
        batch_id=batch_id,
        steps=_step_specs(
            payload,
            history_path=path,
            project_root=project_root,
        ),
    )
    if payload != rebuilt:
        raise HanDeltaHistoryError(
            "generation history differs from recomputed files and chain"
        )
    first = rebuilt["steps"][0]
    accepted = rebuilt["steps"][-1]
    exact_prompt_path = (
        path.parent / first["prompt"]["path"]
    ).resolve()
    accepted_raster_path = (
        path.parent / accepted["output"]["path"]
    ).resolve()
    return GenerationHistory(
        path=path,
        sha256=sha256_path(path),
        batch_id=batch_id,
        exact_prompt_path=exact_prompt_path,
        exact_prompt_sha256=first["prompt"]["sha256"],
        accepted_call_id=accepted["call_id"],
        accepted_raster_path=accepted_raster_path,
        accepted_raster_sha256=accepted["output"]["sha256"],
        step_count=len(rebuilt["steps"]),
        payload=rebuilt,
    )


def write_history(
    path: Path,
    payload: Mapping[str, Any],
    *,
    project_root: Path = ROOT,
) -> Path:
    """Atomically create a new canonical history; never overwrite."""

    path = path.resolve()
    if path.exists():
        raise HanDeltaHistoryError(
            f"refusing to overwrite generation history: {path}"
        )
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
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
    try:
        temporary.replace(path)
        load_history(path, project_root=project_root)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return path


def single_step_history(
    collection: HanDeltaCollection,
    *,
    batch_id: str,
    call_id: str,
    actual_prompt_path: Path,
) -> dict[str, Any]:
    """Build a one-call accepted history for a normal batch."""

    draft_path = (
        collection.descriptor_directory / f"{batch_id}.draft.json"
    )
    try:
        draft = validate_draft(
            draft_path,
            project_root=collection.project_root,
        )
    except HanDeltaMaterializationError as exc:
        raise HanDeltaHistoryError(str(exc)) from exc
    style_path = (
        draft_path.parent / draft["style_reference"]["raster"]
    ).resolve()
    copybook_path = (
        draft_path.parent / draft["identity_copybook"]["raster"]
    ).resolve()
    raster_path = (
        collection.raster_directory / f"{batch_id}.png"
    )
    return history_payload(
        collection,
        batch_id=batch_id,
        steps=(
            GenerationStepSpec(
                operation="generate",
                disposition="accepted",
                call_id=call_id,
                prompt_path=actual_prompt_path,
                input_images=(
                    InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style_path,
                        sha256=sha256_path(style_path),
                    ),
                    InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook_path,
                        sha256=sha256_path(copybook_path),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="retained-final",
                output_path=raster_path,
                output_sha256=sha256_path(raster_path),
            ),
        ),
    )


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument(
        "--collection",
        type=Path,
        default=DEFAULT_COLLECTION,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    single = subparsers.add_parser(
        "single",
        help="create one single-call canonical history",
    )
    single.add_argument("batch_id")
    single.add_argument("--call-id", required=True)
    single.add_argument("--actual-prompt", type=Path, required=True)
    validate = subparsers.add_parser(
        "validate",
        help="validate one canonical history",
    )
    validate.add_argument("history", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    if args.command == "validate":
        history_path = args.history
        if not history_path.is_absolute():
            history_path = project_root / history_path
        history = load_history(
            history_path,
            project_root=project_root,
        )
        print(
            f"validated {history.batch_id}: "
            f"{history.step_count} generation step(s)"
        )
        return 0
    collection_path = args.collection
    if not collection_path.is_absolute():
        collection_path = project_root / collection_path
    try:
        collection = load_collection(
            collection_path,
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise SystemExit(str(exc)) from exc
    actual_prompt = args.actual_prompt
    if not actual_prompt.is_absolute():
        actual_prompt = project_root / actual_prompt
    payload = single_step_history(
        collection,
        batch_id=args.batch_id,
        call_id=args.call_id,
        actual_prompt_path=actual_prompt.resolve(),
    )
    output = (
        collection.descriptor_directory
        / f"{args.batch_id}.history.json"
    )
    write_history(output, payload, project_root=project_root)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
