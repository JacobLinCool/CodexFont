#!/usr/bin/env python3
"""Amend a failed, unreviewed Mew Note raster without erasing its history.

The hash-pinned base evidence pipeline remains immutable.  This extension only
permits a former accepted raster to become a hash-only rejected attempt when a
strict vector build failed before review.  Every correction then extends that
exact output hash.  Reviewed or successfully built batches cannot be amended.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

from scripts.font_family_context import canonical_json_sha256, sha256_path
from scripts import mew_note_batch_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = Path("scripts/mew_note_history_amendment.py")
SCHEMA_VERSION = 1
RECORD_TYPE = "mew-note-tc-generation-amendments"
REASON = "strict-vector-build-rejected"


class MewNoteAmendmentError(RuntimeError):
    """A proposed generation-history amendment is unsafe or stale."""


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(_json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _implementation_pin(project_root: Path) -> dict[str, str]:
    path = project_root / IMPLEMENTATION_PATH
    return {
        "path": IMPLEMENTATION_PATH.as_posix(),
        "sha256": sha256_path(path),
    }


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteAmendmentError(f"{path}: cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise MewNoteAmendmentError(f"{path}: {label} must be an object")
    return value


def _step_identity(
    context: evidence.FamilyContext,
    root: Path,
    step: evidence.GenerationStep,
) -> dict[str, Any]:
    if not step.prompt_path.is_file() or step.prompt_path.is_symlink():
        raise MewNoteAmendmentError("generation prompt is not a regular file")
    return {
        "operation": step.operation,
        "disposition": step.disposition,
        "call_id": step.call_id,
        "actual_tool_prompt": {
            "path": step.prompt_path.resolve()
            .relative_to(context.project_root.resolve())
            .as_posix(),
            "sha256": sha256_path(step.prompt_path),
        },
        "inputs": [
            evidence._generation_input_payload(
                item,
                context=context,
                root=root,
            )
            for item in step.inputs
        ],
        "parent_output_sha256": step.parent_output_sha256,
        "output_sha256": step.output_sha256,
        "output_path": step.output_path,
    }


def _assert_preserved_prefix(
    context: evidence.FamilyContext,
    root: Path,
    previous_history: Mapping[str, Any],
    steps: Sequence[evidence.GenerationStep],
) -> None:
    previous_steps = previous_history["steps"]
    if len(steps) <= len(previous_steps):
        raise MewNoteAmendmentError(
            "amendment must append at least one correction step"
        )
    for index, previous in enumerate(previous_steps):
        actual = _step_identity(context, root, steps[index])
        expected_disposition = (
            "rejected"
            if index == len(previous_steps) - 1
            else previous["disposition"]
        )
        expected_output_path = None
        if previous["disposition"] == "accepted" and index != (
            len(previous_steps) - 1
        ):
            raise MewNoteAmendmentError(
                "prior history accepted a non-final attempt"
            )
        if (
            actual["operation"] != previous["operation"]
            or actual["disposition"] != expected_disposition
            or actual["call_id"] != previous["call_id"]
            or actual["actual_tool_prompt"] != previous["actual_tool_prompt"]
            or actual["inputs"] != previous["inputs"]
            or actual["parent_output_sha256"]
            != previous["parent_output_sha256"]
            or actual["output_sha256"] != previous["output"]["sha256"]
            or actual["output_path"] is not expected_output_path
        ):
            raise MewNoteAmendmentError(
                "amendment changed or removed a prior generation attempt"
            )
    prior_hash = previous_steps[-1]["output"]["sha256"]
    first_correction = steps[len(previous_steps)]
    parent_inputs = [
        item for item in first_correction.inputs if item.role == "parent-output"
    ]
    if (
        first_correction.operation != "correction"
        or first_correction.parent_output_sha256 != prior_hash
        or len(parent_inputs) != 1
        or parent_inputs[0].sha256 != prior_hash
    ):
        raise MewNoteAmendmentError(
            "first correction does not extend the prior accepted raster hash"
        )


def _amendments_path(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Path:
    return context.batch_paths(collection_id, batch_id).source / "amendments.json"


def _validated_prior_revisions(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
) -> list[dict[str, Any]]:
    path = _amendments_path(context, collection_id, batch_id)
    if not path.exists():
        return []
    return list(
        validate_amendments(context, collection_id, batch_id)["revisions"]
    )


def _prior_vector_build(
    paths: Any,
    *,
    prior_source_sha256: str,
) -> dict[str, Any] | None:
    report_path = paths.build / "report.json"
    if not report_path.exists():
        return None
    report = _load_object(report_path, label="prior vector report")
    if (
        report.get("approval_state") != "unreviewed"
        or report.get("source_descriptor_sha256") != prior_source_sha256
    ):
        raise MewNoteAmendmentError(
            "only a current unreviewed vector build may be amended"
        )
    font = report.get("font")
    proofs = report.get("proofs")
    if not isinstance(font, dict) or not isinstance(proofs, dict):
        raise MewNoteAmendmentError("prior vector report is incomplete")
    proof_hashes = {}
    for key in ("black_on_white", "white_on_black", "segmented_source"):
        relative = proofs.get(key)
        if not isinstance(relative, str):
            raise MewNoteAmendmentError("prior vector proof inventory changed")
        proof_hashes[key] = sha256_path(paths.build / relative)
    return {
        "retention": "hash-only-derived-unreviewed",
        "report_sha256": sha256_path(report_path),
        "source_descriptor_sha256": prior_source_sha256,
        "ttf_sha256": font["ttf_sha256"],
        "otf_sha256": font["otf_sha256"],
        "proof_sha256": proof_hashes,
    }


def amend_unreviewed_history(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
    *,
    steps: Sequence[evidence.GenerationStep],
    reason: str = REASON,
) -> dict[str, Any]:
    """Install one correction chain after a failed pre-review vector build."""

    if reason != REASON:
        raise MewNoteAmendmentError("unsupported generation amendment reason")
    paths = context.batch_paths(collection_id, batch_id)
    root = paths.source
    if (root / "review.json").exists():
        raise MewNoteAmendmentError("reviewed generation evidence is immutable")
    previous_history = evidence.validate_history(
        context,
        collection_id,
        batch_id,
    )
    evidence.validate_source(context, collection_id, batch_id)
    previous_revisions = _validated_prior_revisions(
        context,
        collection_id,
        batch_id,
    )
    _assert_preserved_prefix(context, root, previous_history, steps)
    previous_history_file_sha256 = sha256_path(root / "history.json")
    previous_source_file_sha256 = sha256_path(root / "source.json")
    previous_raster_sha256 = sha256_path(root / "raster.png")
    prior_vector_build = _prior_vector_build(
        paths,
        prior_source_sha256=previous_source_file_sha256,
    )

    amended_source = evidence.register_history(
        context,
        collection_id,
        batch_id,
        steps=steps,
    )
    amended_history = evidence.validate_history(
        context,
        collection_id,
        batch_id,
    )
    revision = {
        "sequence": len(previous_revisions) + 1,
        "reason": reason,
        "prior_history_file_sha256": previous_history_file_sha256,
        "prior_source_file_sha256": previous_source_file_sha256,
        "prior_raster_sha256": previous_raster_sha256,
        "prior_accepted_call_id": previous_history["accepted_final"]["call_id"],
        "prior_accepted_output_sha256": previous_history["accepted_final"][
            "raster"
        ]["sha256"],
        "prior_vector_build": prior_vector_build,
        "amended_history_file_sha256": sha256_path(root / "history.json"),
        "amended_source_file_sha256": sha256_path(root / "source.json"),
        "amended_raster_sha256": amended_source["raster_sha256"],
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "family_id": evidence.FAMILY_ID,
        "pipeline_id": evidence.PIPELINE_ID,
        "collection_id": collection_id,
        "batch_id": batch_id,
        "family_context": context.evidence_binding(collection_id),
        "batch_contract_sha256": evidence.frozen_batch(
            context,
            collection_id,
            batch_id,
        )["batch_contract_sha256"],
        "implementation": _implementation_pin(context.project_root),
        "revisions": [*previous_revisions, revision],
    }
    payload["amendments_sha256"] = canonical_json_sha256(payload)
    _atomic_json(_amendments_path(context, collection_id, batch_id), payload)
    return validate_amendments(context, collection_id, batch_id)


def validate_amendments(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
) -> dict[str, Any]:
    root = context.batch_paths(collection_id, batch_id).source
    payload = _load_object(
        _amendments_path(context, collection_id, batch_id),
        label="generation amendments",
    )
    expected_keys = {
        "schema_version",
        "record_type",
        "family_id",
        "pipeline_id",
        "collection_id",
        "batch_id",
        "family_context",
        "batch_contract_sha256",
        "implementation",
        "revisions",
        "amendments_sha256",
    }
    batch = evidence.frozen_batch(context, collection_id, batch_id)
    if (
        set(payload) != expected_keys
        or payload["schema_version"] != SCHEMA_VERSION
        or payload["record_type"] != RECORD_TYPE
        or payload["family_id"] != evidence.FAMILY_ID
        or payload["pipeline_id"] != evidence.PIPELINE_ID
        or payload["collection_id"] != collection_id
        or payload["batch_id"] != batch_id
        or payload["family_context"] != context.evidence_binding(collection_id)
        or payload["batch_contract_sha256"]
        != batch["batch_contract_sha256"]
        or payload["implementation"]
        != _implementation_pin(context.project_root)
    ):
        raise MewNoteAmendmentError("generation amendments binding mismatch")
    expected_digest = canonical_json_sha256(
        {
            key: value
            for key, value in payload.items()
            if key != "amendments_sha256"
        }
    )
    if payload["amendments_sha256"] != expected_digest:
        raise MewNoteAmendmentError(
            "generation amendments canonical hash mismatch"
        )
    history = evidence.validate_history(context, collection_id, batch_id)
    source = evidence.validate_source(context, collection_id, batch_id)
    rejected_attempts = {
        (step["call_id"], step["output"]["sha256"])
        for step in history["steps"]
        if step["disposition"] == "rejected"
    }
    rejected_hashes = {item[1] for item in rejected_attempts}
    revisions = payload["revisions"]
    expected_revision_keys = {
        "sequence",
        "reason",
        "prior_history_file_sha256",
        "prior_source_file_sha256",
        "prior_raster_sha256",
        "prior_accepted_call_id",
        "prior_accepted_output_sha256",
        "prior_vector_build",
        "amended_history_file_sha256",
        "amended_source_file_sha256",
        "amended_raster_sha256",
    }
    if not isinstance(revisions, list) or not revisions:
        raise MewNoteAmendmentError("generation amendments are empty")
    for sequence, revision in enumerate(revisions, start=1):
        if (
            not isinstance(revision, dict)
            or set(revision) != expected_revision_keys
            or revision["sequence"] != sequence
            or revision["reason"] != REASON
            or revision["prior_raster_sha256"]
            != revision["prior_accepted_output_sha256"]
            or (
                revision["prior_accepted_call_id"],
                revision["prior_accepted_output_sha256"],
            )
            not in rejected_attempts
        ):
            raise MewNoteAmendmentError(
                "generation amendment lost its prior accepted attempt"
            )
        for key, value in revision.items():
            if key.endswith("_sha256") and evidence.SHA256_PATTERN.fullmatch(
                str(value)
            ) is None:
                raise MewNoteAmendmentError(
                    f"generation amendment {key} is not a SHA-256"
                )
        vector = revision["prior_vector_build"]
        if vector is not None:
            if (
                not isinstance(vector, dict)
                or set(vector)
                != {
                    "retention",
                    "report_sha256",
                    "source_descriptor_sha256",
                    "ttf_sha256",
                    "otf_sha256",
                    "proof_sha256",
                }
                or vector["retention"]
                != "hash-only-derived-unreviewed"
                or vector["source_descriptor_sha256"]
                != revision["prior_source_file_sha256"]
                or set(vector["proof_sha256"])
                != {
                    "black_on_white",
                    "white_on_black",
                    "segmented_source",
                }
            ):
                raise MewNoteAmendmentError(
                    "prior vector build amendment evidence is invalid"
                )
            for digest in (
                vector["report_sha256"],
                vector["source_descriptor_sha256"],
                vector["ttf_sha256"],
                vector["otf_sha256"],
                *vector["proof_sha256"].values(),
            ):
                if evidence.SHA256_PATTERN.fullmatch(str(digest)) is None:
                    raise MewNoteAmendmentError(
                        "prior vector build hash is invalid"
                    )
        if sequence > 1:
            prior = revisions[sequence - 2]
            if (
                revision["prior_history_file_sha256"]
                != prior["amended_history_file_sha256"]
                or revision["prior_source_file_sha256"]
                != prior["amended_source_file_sha256"]
                or revision["prior_raster_sha256"]
                != prior["amended_raster_sha256"]
                or prior["amended_raster_sha256"] not in rejected_hashes
            ):
                raise MewNoteAmendmentError(
                    "generation amendment hash chain is broken"
                )
    latest = revisions[-1]
    if (
        latest["amended_history_file_sha256"]
        != sha256_path(root / "history.json")
        or latest["amended_source_file_sha256"]
        != sha256_path(root / "source.json")
        or latest["amended_raster_sha256"] != source["raster_sha256"]
        or latest["amended_raster_sha256"]
        != history["accepted_final"]["raster"]["sha256"]
    ):
        raise MewNoteAmendmentError("latest generation amendment is stale")
    return payload


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--collection-id", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("command", choices=("validate",))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    context = evidence.load_context(args.project_root)
    result = validate_amendments(
        context,
        args.collection_id,
        args.batch_id,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
