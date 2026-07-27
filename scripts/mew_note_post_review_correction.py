#!/usr/bin/env python3
"""Correct a reviewed Mew Note batch after a release-only metric rejection.

This is deliberately separate from ``mew_note_history_amendment.py``.  That
module governs failures found before review; this module handles the narrower
case where a reviewed raster passes batch QA but cannot fit its frozen release
metric envelope.

The correction ledger keeps the superseded review and collection approval by
SHA-256 provenance, appends (never rewrites) the generation call chain, and
leaves the batch in a state that requires a fresh technical review and a fresh
collection approval.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping, Sequence

from fontTools.ttLib import TTFont

from scripts.font_family_context import canonical_json_sha256, sha256_path
from scripts import imagegen_font_pipeline
from scripts import mew_note_batch_evidence as evidence
from scripts import mew_note_bulk_pipeline as bulk


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = Path("scripts/mew_note_post_review_correction.py")
APPROVAL_PATH = Path(
    "families/mew-note-tc/approvals/"
    "original-raster-v1-preview.approval.json"
)
RECORD_NAME = "post-review-correction.json"
SCHEMA_VERSION = 1
RECORD_TYPE = "mew-note-tc-post-review-generation-correction"
REASON = "release-metric-envelope-rejected"
CONFIRMATION = "I_AUTHORIZE_POST_REVIEW_GENERATION_CORRECTION"


class MewNotePostReviewCorrectionError(RuntimeError):
    """A post-review correction is unproven, stale, or unsafe."""


def correction_path(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
) -> Path:
    return context.batch_paths(collection_id, batch_id).source / RECORD_NAME


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


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write(path, _json_bytes(value))


def _object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNotePostReviewCorrectionError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MewNotePostReviewCorrectionError(
            f"{path}: {label} must be an object"
        )
    return value


def _regular_file(path: Path, *, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise MewNotePostReviewCorrectionError(
            f"{label}: expected a regular non-symlink file: {path}"
        )
    return path.resolve()


def _relative(path: Path, *, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError as exc:
        raise MewNotePostReviewCorrectionError(
            f"path escapes repository: {path}"
        ) from exc


def _pin(
    path: Path,
    *,
    project_root: Path,
    retention: str | None = None,
) -> dict[str, str]:
    path = _regular_file(path, label="pinned correction evidence")
    result = {
        "path": _relative(path, project_root=project_root),
        "sha256": sha256_path(path),
    }
    if retention is not None:
        result["retention"] = retention
    return result


def _implementation_pin(project_root: Path) -> dict[str, str]:
    return _pin(
        project_root / IMPLEMENTATION_PATH,
        project_root=project_root,
    )


def _sha(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or evidence.SHA256_PATTERN.fullmatch(value) is None
    ):
        raise MewNotePostReviewCorrectionError(
            f"{label} is not a lowercase SHA-256"
        )
    return value


def _codepoint(value: str) -> int:
    if (
        not isinstance(value, str)
        or not value.startswith("U+")
        or len(value) not in {6, 7, 8}
    ):
        raise MewNotePostReviewCorrectionError("invalid codepoint label")
    try:
        scalar = int(value[2:], 16)
    except ValueError as exc:
        raise MewNotePostReviewCorrectionError(
            "invalid codepoint label"
        ) from exc
    if (
        not 0 <= scalar <= 0x10FFFF
        or 0xD800 <= scalar <= 0xDFFF
        or f"U+{scalar:04X}" != value
    ):
        raise MewNotePostReviewCorrectionError(
            "codepoint label is not canonical"
        )
    return scalar


def _metric_contract(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
    codepoint: str,
) -> dict[str, Any]:
    if collection_id != "nonhan-3060":
        raise MewNotePostReviewCorrectionError(
            "release metric corrections are currently defined only for "
            "the frozen non-Han metric contract"
        )
    batch = evidence.frozen_batch(context, collection_id, batch_id)
    matching_entries = [
        entry
        for entry in batch["entries"]
        if entry.get("codepoint") == codepoint
    ]
    if len(matching_entries) != 1:
        raise MewNotePostReviewCorrectionError(
            f"{codepoint} is not uniquely assigned to {batch_id}"
        )
    repertoire = _object(
        context.project_root / bulk.NONHAN_PATH,
        label="frozen non-Han repertoire",
    )
    matching = [
        glyph
        for glyph in repertoire.get("glyphs", [])
        if isinstance(glyph, dict) and glyph.get("codepoint") == codepoint
    ]
    if len(matching) != 1:
        raise MewNotePostReviewCorrectionError(
            f"{codepoint} is not unique in the frozen non-Han repertoire"
        )
    glyph = matching[0]
    horizontal = glyph.get("metrics", {}).get("horizontal_advance")
    bearings = glyph.get("metrics", {}).get("side_bearings")
    if (
        not isinstance(horizontal, dict)
        or horizontal.get("kind") != "fixed"
        or not isinstance(horizontal.get("value"), int)
        or not isinstance(bearings, dict)
        or not isinstance(bearings.get("left"), int)
        or not isinstance(bearings.get("right"), int)
    ):
        raise MewNotePostReviewCorrectionError(
            f"{codepoint} does not have a fixed frozen metric envelope"
        )
    allowed = (
        horizontal["value"] - bearings["left"] - bearings["right"]
    )
    if allowed <= 0:
        raise MewNotePostReviewCorrectionError(
            f"{codepoint} has an invalid frozen metric envelope"
        )
    return {
        "codepoint": codepoint,
        "character": glyph["character"],
        "profile_id": glyph["profile_id"],
        "horizontal_advance": horizontal["value"],
        "left_bearing": bearings["left"],
        "right_bearing": bearings["right"],
        "maximum_ink_width": allowed,
    }


def _ttf_bounds(ttf_path: Path, codepoint: str) -> list[int]:
    scalar = _codepoint(codepoint)
    with TTFont(
        _regular_file(ttf_path, label="batch vector TTF"),
        lazy=False,
        checkChecksums=2,
    ) as font:
        cmap = font.getBestCmap()
        glyph_name = cmap.get(scalar)
        if glyph_name is None:
            raise MewNotePostReviewCorrectionError(
                f"{ttf_path}: {codepoint} is absent from cmap"
            )
        glyph = font["glyf"][glyph_name]
        if glyph.isComposite() or glyph.numberOfContours <= 0:
            raise MewNotePostReviewCorrectionError(
                f"{ttf_path}: {codepoint} is empty or composite"
            )
        glyph.recalcBounds(font["glyf"])
        return [glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax]


def _vector_metric(
    *,
    report_path: Path,
    codepoint: str,
    metric: Mapping[str, Any],
    source_sha256: str,
    expect_rejected: bool,
) -> dict[str, Any]:
    report = _object(report_path, label="batch vector report")
    glyphs = report.get("glyphs")
    font = report.get("font")
    if (
        report.get("approval_state") != "unreviewed"
        or report.get("source_descriptor_sha256") != source_sha256
        or not isinstance(glyphs, list)
        or not isinstance(font, dict)
        or not isinstance(font.get("ttf"), str)
    ):
        raise MewNotePostReviewCorrectionError(
            f"{report_path}: vector report binding drift"
        )
    matching = [
        glyph
        for glyph in glyphs
        if isinstance(glyph, dict) and glyph.get("codepoint") == codepoint
    ]
    if (
        len(matching) != 1
        or matching[0].get("micro_edge_count") != 0
        or matching[0].get("acute_micro_turn_count") != 0
    ):
        raise MewNotePostReviewCorrectionError(
            f"{report_path}: {codepoint} failed strict vector geometry"
        )
    ttf_path = _regular_file(
        report_path.parent / font["ttf"],
        label="batch vector TTF",
    )
    if sha256_path(ttf_path) != font.get("ttf_sha256"):
        raise MewNotePostReviewCorrectionError(
            f"{ttf_path}: vector TTF hash drift"
        )
    bounds = _ttf_bounds(ttf_path, codepoint)
    width = bounds[2] - bounds[0]
    maximum = int(metric["maximum_ink_width"])
    rejected = width > maximum
    if rejected is not expect_rejected:
        expectation = "exceed" if expect_rejected else "fit"
        raise MewNotePostReviewCorrectionError(
            f"{codepoint} width {width} does not {expectation} "
            f"the frozen envelope {maximum}"
        )
    return {
        "report": {
            "path": report_path,
            "sha256": sha256_path(report_path),
        },
        "ttf": {
            "path": ttf_path,
            "sha256": sha256_path(ttf_path),
        },
        "bounds": bounds,
        "width": width,
        "micro_edge_count": 0,
        "acute_micro_turn_count": 0,
    }


def _history_steps(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
    history: Mapping[str, Any],
) -> list[evidence.GenerationStep]:
    result: list[evidence.GenerationStep] = []
    for step in history["steps"]:
        inputs = tuple(
            evidence.GenerationInput(
                role=item["role"],
                retention=item["retention"],
                path=(
                    None
                    if item["path"] is None
                    else context.project_root / item["path"]
                ),
                sha256=item["sha256"],
            )
            for item in step["inputs"]
        )
        result.append(
            evidence.GenerationStep(
                operation=step["operation"],
                disposition=(
                    "rejected"
                    if step is history["steps"][-1]
                    else step["disposition"]
                ),
                call_id=step["call_id"],
                prompt_path=context.project_root
                / step["actual_tool_prompt"]["path"],
                inputs=inputs,
                output_sha256=step["output"]["sha256"],
                output_path=None,
                parent_output_sha256=step["parent_output_sha256"],
            )
        )
    return result


def _preflight_candidate(
    *,
    context: evidence.FamilyContext,
    batch: Mapping[str, Any],
    candidate_raster: Path,
    candidate_sha256: str,
    metric: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_raster = _regular_file(
        candidate_raster, label="candidate raster"
    )
    if sha256_path(candidate_raster) != candidate_sha256:
        raise MewNotePostReviewCorrectionError(
            "candidate raster hash mismatch"
        )
    try:
        with tempfile.TemporaryDirectory(
            prefix="mew-note-post-review-preflight-"
        ) as temporary:
            root = Path(temporary)
            raster = root / "raster.png"
            shutil.copyfile(candidate_raster, raster)
            descriptor = {
                "schema_version": 1,
                "batch_id": batch["batch_id"],
                "state": "generated-unreviewed",
                "raster": "raster.png",
                "raster_sha256": candidate_sha256,
                "grid": {
                    "rows": evidence.GRID_ROWS,
                    "columns": evidence.GRID_COLUMNS,
                    "characters": [
                        entry["character"] for entry in batch["entries"]
                    ],
                    "empty_grid_cells": (
                        evidence.GRID_CAPACITY - len(batch["entries"])
                    ),
                },
                "review": {
                    "topology": "pending",
                    "raster_quality": "pending",
                    "vector_quality": "pending",
                },
            }
            descriptor_path = root / "source.json"
            descriptor_path.write_text(
                json.dumps(
                    descriptor,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            final = imagegen_font_pipeline.build_batch(
                descriptor_path,
                output_root=root / "build",
                allowed_raster_root=root,
                family_name_prefix="Mew Note TC",
                postscript_name_prefix="MewNoteTC",
            )
            result = _vector_metric(
                report_path=final / "report.json",
                codepoint=str(metric["codepoint"]),
                metric=metric,
                source_sha256=sha256_path(descriptor_path),
                expect_rejected=False,
            )
            return {
                "candidate_raster_sha256": candidate_sha256,
                "ttf_sha256": result["ttf"]["sha256"],
                "bounds": result["bounds"],
                "width": result["width"],
                "micro_edge_count": 0,
                "acute_micro_turn_count": 0,
            }
    except (
        imagegen_font_pipeline.ImagegenPipelineError,
        OSError,
    ) as exc:
        raise MewNotePostReviewCorrectionError(
            f"candidate preflight failed: {exc}"
        ) from exc


def _prior_release_approval(
    *,
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
    review_path: Path,
) -> dict[str, Any]:
    approval_path = _regular_file(
        context.project_root / APPROVAL_PATH,
        label="current collection release approval",
    )
    approval = _object(
        approval_path, label="current collection release approval"
    )
    reviewed = approval.get("reviewed_batches")
    matching = [
        item
        for item in reviewed
        if isinstance(item, dict)
        and item.get("collection_id") == collection_id
        and item.get("batch_id") == batch_id
    ] if isinstance(reviewed, list) else []
    expected_review = {
        "path": _relative(
            review_path, project_root=context.project_root
        ),
        "sha256": sha256_path(review_path),
    }
    if (
        approval.get("record_type")
        != "mew-note-tc-collection-release-approval"
        or approval.get("decision") != "APPROVED"
        or len(matching) != 1
        or matching[0].get("review") != expected_review
    ):
        raise MewNotePostReviewCorrectionError(
            "current release approval does not admit the exact prior review"
        )
    return _pin(
        approval_path,
        project_root=context.project_root,
        retention="hash-only-superseded-after-reapproval",
    )


def apply_correction(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
    *,
    codepoint: str,
    candidate_raster: Path,
    candidate_sha256: str,
    call_id: str,
    confirmation: str,
    reason: str = REASON,
) -> dict[str, Any]:
    """Append one release-metric correction and require new review/approval."""

    if confirmation != CONFIRMATION:
        raise MewNotePostReviewCorrectionError(
            "explicit post-review correction authorization is required"
        )
    if reason != REASON:
        raise MewNotePostReviewCorrectionError(
            "unsupported post-review correction reason"
        )
    _sha(candidate_sha256, label="candidate raster hash")
    record_path = correction_path(context, collection_id, batch_id)
    if record_path.exists():
        raise MewNotePostReviewCorrectionError(
            "a post-review correction already exists for this batch"
        )
    paths = context.batch_paths(collection_id, batch_id)
    history = evidence.validate_history(context, collection_id, batch_id)
    evidence.validate_source(context, collection_id, batch_id)
    batch = evidence.frozen_batch(context, collection_id, batch_id)
    metric = _metric_contract(
        context, collection_id, batch_id, codepoint
    )
    review_path = _regular_file(
        paths.source / "review.json",
        label="prior technical review",
    )
    review = _object(review_path, label="prior technical review")
    source_path = paths.source / "source.json"
    report_path = paths.build / "report.json"
    if (
        review.get("decision") != "ACCEPT"
        or review.get("source")
        != {
            "path": _relative(
                source_path, project_root=context.project_root
            ),
            "sha256": sha256_path(source_path),
        }
        or review.get("evidence", {}).get("report", {}).get("sha256")
        != sha256_path(report_path)
    ):
        raise MewNotePostReviewCorrectionError(
            "prior technical review is stale or incomplete"
        )
    rejected = _vector_metric(
        report_path=report_path,
        codepoint=codepoint,
        metric=metric,
        source_sha256=sha256_path(source_path),
        expect_rejected=True,
    )
    preflight = _preflight_candidate(
        context=context,
        batch=batch,
        candidate_raster=candidate_raster,
        candidate_sha256=candidate_sha256,
        metric=metric,
    )
    prior = {
        "history": _pin(
            paths.source / "history.json",
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "source": _pin(
            source_path,
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "raster": _pin(
            paths.source / "raster.png",
            project_root=context.project_root,
            retention="hash-only-rejected",
        ),
        "review": _pin(
            review_path,
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "release_approval": _prior_release_approval(
            context=context,
            collection_id=collection_id,
            batch_id=batch_id,
            review_path=review_path,
        ),
        "vector_report": _pin(
            rejected["report"]["path"],
            project_root=context.project_root,
            retention="hash-only-derived-superseded",
        ),
        "vector_ttf": _pin(
            rejected["ttf"]["path"],
            project_root=context.project_root,
            retention="hash-only-derived-superseded",
        ),
    }
    old_steps = _history_steps(
        context, collection_id, batch_id, history
    )
    root = paths.source
    prompt_path = root / f"tool-step-{len(old_steps) + 1:04d}.txt"
    _regular_file(prompt_path, label="correction tool prompt")
    previous_hash = history["accepted_final"]["raster"]["sha256"]
    last_inputs = tuple(
        item for item in old_steps[-1].inputs if item.role != "parent-output"
    )
    correction_step = evidence.GenerationStep(
        operation="correction",
        disposition="accepted",
        call_id=call_id,
        prompt_path=prompt_path,
        inputs=(
            evidence.GenerationInput(
                role="parent-output",
                retention="hash-only-rejected",
                path=None,
                sha256=previous_hash,
            ),
            *last_inputs,
        ),
        output_sha256=candidate_sha256,
        output_path=candidate_raster,
        parent_output_sha256=previous_hash,
    )
    old_bytes = {
        path: path.read_bytes()
        for path in (
            root / "history.json",
            root / "source.json",
            root / "raster.png",
        )
    }
    build_backup: Path | None = None
    if paths.build.exists():
        build_backup = paths.build.with_name(
            f".{paths.build.name}.post-review-backup"
        )
        if build_backup.exists():
            raise MewNotePostReviewCorrectionError(
                f"stale correction backup exists: {build_backup}"
            )
        paths.build.replace(build_backup)
    try:
        evidence.register_history(
            context,
            collection_id,
            batch_id,
            steps=(*old_steps, correction_step),
        )
        evidence.build_vector_batch(context, collection_id, batch_id)
        corrected = _vector_metric(
            report_path=paths.build / "report.json",
            codepoint=codepoint,
            metric=metric,
            source_sha256=sha256_path(root / "source.json"),
            expect_rejected=False,
        )
        if corrected["ttf"]["sha256"] != preflight["ttf_sha256"]:
            raise MewNotePostReviewCorrectionError(
                "canonical correction build differs from preflight"
            )
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": RECORD_TYPE,
            "family_id": evidence.FAMILY_ID,
            "pipeline_id": evidence.PIPELINE_ID,
            "collection_id": collection_id,
            "batch_id": batch_id,
            "family_context": context.evidence_binding(collection_id),
            "batch_contract_sha256": batch["batch_contract_sha256"],
            "implementation": _implementation_pin(
                context.project_root
            ),
            "reason": REASON,
            "metric_contract": metric,
            "rejected_release_metric": {
                "bounds": rejected["bounds"],
                "width": rejected["width"],
                "maximum_ink_width": metric["maximum_ink_width"],
                "decision": "REJECT",
            },
            "prior_evidence": prior,
            "correction_generation": {
                "appended_sequence": len(old_steps) + 1,
                "call_id": call_id,
                "parent_output_sha256": previous_hash,
                "candidate_preflight": preflight,
                "history": _pin(
                    root / "history.json",
                    project_root=context.project_root,
                ),
                "source": _pin(
                    root / "source.json",
                    project_root=context.project_root,
                ),
                "raster": _pin(
                    root / "raster.png",
                    project_root=context.project_root,
                ),
                "vector_report": _pin(
                    corrected["report"]["path"],
                    project_root=context.project_root,
                ),
                "vector_ttf": _pin(
                    corrected["ttf"]["path"],
                    project_root=context.project_root,
                ),
                "corrected_bounds": corrected["bounds"],
                "corrected_width": corrected["width"],
                "micro_edge_count": 0,
                "acute_micro_turn_count": 0,
            },
            "required_next_gates": [
                "independent-raster-vector-technical-review",
                "collection-release-reapproval",
            ],
            "state": "corrected-unreviewed-unapproved",
        }
        payload["correction_sha256"] = canonical_json_sha256(payload)
        _atomic_json(record_path, payload)
        result = validate_correction(
            context,
            collection_id,
            batch_id,
            require_new_review=False,
        )
    except Exception:
        record_path.unlink(missing_ok=True)
        if paths.build.exists():
            shutil.rmtree(paths.build)
        if build_backup is not None and build_backup.exists():
            build_backup.replace(paths.build)
        for path, data in old_bytes.items():
            _atomic_write(path, data)
        raise
    else:
        if build_backup is not None:
            shutil.rmtree(build_backup)
        return result


def validate_correction(
    context: evidence.FamilyContext,
    collection_id: str,
    batch_id: str,
    *,
    require_new_review: bool,
) -> dict[str, Any]:
    """Validate the correction ledger and optionally its replacement review."""

    path = correction_path(context, collection_id, batch_id)
    payload = _object(path, label="post-review correction")
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
        "reason",
        "metric_contract",
        "rejected_release_metric",
        "prior_evidence",
        "correction_generation",
        "required_next_gates",
        "state",
        "correction_sha256",
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
        or payload["family_context"]
        != context.evidence_binding(collection_id)
        or payload["batch_contract_sha256"]
        != batch["batch_contract_sha256"]
        or payload["implementation"]
        != _implementation_pin(context.project_root)
        or payload["reason"] != REASON
        or payload["required_next_gates"]
        != [
            "independent-raster-vector-technical-review",
            "collection-release-reapproval",
        ]
        or payload["state"] != "corrected-unreviewed-unapproved"
    ):
        raise MewNotePostReviewCorrectionError(
            "post-review correction binding mismatch"
        )
    expected_digest = canonical_json_sha256(
        {
            key: value
            for key, value in payload.items()
            if key != "correction_sha256"
        }
    )
    if payload["correction_sha256"] != expected_digest:
        raise MewNotePostReviewCorrectionError(
            "post-review correction canonical hash mismatch"
        )
    recorded_metric = payload["metric_contract"]
    if not isinstance(recorded_metric, dict):
        raise MewNotePostReviewCorrectionError(
            "post-review metric contract is not an object"
        )
    metric = _metric_contract(
        context,
        collection_id,
        batch_id,
        recorded_metric.get("codepoint"),
    )
    if recorded_metric != metric:
        raise MewNotePostReviewCorrectionError(
            "post-review metric contract drift"
        )
    rejected = payload["rejected_release_metric"]
    if (
        not isinstance(rejected, dict)
        or set(rejected)
        != {
            "bounds",
            "width",
            "maximum_ink_width",
            "decision",
        }
        or rejected["decision"] != "REJECT"
        or rejected["maximum_ink_width"]
        != metric["maximum_ink_width"]
        or rejected["width"] <= metric["maximum_ink_width"]
        or not isinstance(rejected["bounds"], list)
        or len(rejected["bounds"]) != 4
        or any(
            not isinstance(value, int)
            for value in rejected["bounds"]
        )
        or rejected["width"]
        != rejected["bounds"][2] - rejected["bounds"][0]
    ):
        raise MewNotePostReviewCorrectionError(
            "rejected release metric is not proven"
        )
    prior = payload["prior_evidence"]
    if (
        not isinstance(prior, dict)
        or set(prior)
        != {
            "history",
            "source",
            "raster",
            "review",
            "release_approval",
            "vector_report",
            "vector_ttf",
        }
    ):
        raise MewNotePostReviewCorrectionError(
            "prior evidence inventory drift"
        )
    for label, pin in prior.items():
        if (
            not isinstance(pin, dict)
            or set(pin) != {"path", "sha256", "retention"}
        ):
            raise MewNotePostReviewCorrectionError(
                f"invalid prior {label} provenance"
            )
        _sha(pin["sha256"], label=f"prior {label} hash")
    paths = context.batch_paths(collection_id, batch_id)
    expected_prior_paths = {
        "history": _relative(
            paths.source / "history.json",
            project_root=context.project_root,
        ),
        "source": _relative(
            paths.source / "source.json",
            project_root=context.project_root,
        ),
        "raster": _relative(
            paths.source / "raster.png",
            project_root=context.project_root,
        ),
        "review": _relative(
            paths.source / "review.json",
            project_root=context.project_root,
        ),
        "release_approval": APPROVAL_PATH.as_posix(),
        "vector_report": _relative(
            paths.build / "report.json",
            project_root=context.project_root,
        ),
    }
    expected_retentions = {
        "history": "hash-only-superseded",
        "source": "hash-only-superseded",
        "raster": "hash-only-rejected",
        "review": "hash-only-superseded",
        "release_approval": (
            "hash-only-superseded-after-reapproval"
        ),
        "vector_report": "hash-only-derived-superseded",
        "vector_ttf": "hash-only-derived-superseded",
    }
    if any(
        prior[label]["path"] != expected
        or prior[label]["retention"]
        != expected_retentions[label]
        for label, expected in expected_prior_paths.items()
    ):
        raise MewNotePostReviewCorrectionError(
            "prior evidence canonical path or retention drift"
        )
    if (
        not isinstance(prior["vector_ttf"]["path"], str)
        or not prior["vector_ttf"]["path"].startswith(
            _relative(
                paths.build,
                project_root=context.project_root,
            )
            + "/font/"
        )
        or prior["vector_ttf"]["retention"]
        != expected_retentions["vector_ttf"]
    ):
        raise MewNotePostReviewCorrectionError(
            "prior vector TTF path or retention drift"
        )
    source = evidence.validate_source(
        context, collection_id, batch_id
    )
    history = evidence.validate_history(
        context, collection_id, batch_id
    )
    generated = payload["correction_generation"]
    corrected_bounds = (
        generated.get("corrected_bounds")
        if isinstance(generated, dict)
        else None
    )
    if (
        not isinstance(generated, dict)
        or set(generated)
        != {
            "appended_sequence",
            "call_id",
            "parent_output_sha256",
            "candidate_preflight",
            "history",
            "source",
            "raster",
            "vector_report",
            "vector_ttf",
            "corrected_bounds",
            "corrected_width",
            "micro_edge_count",
            "acute_micro_turn_count",
        }
        or generated["source"]
        != _pin(
            context.batch_paths(
                collection_id, batch_id
            ).source
            / "source.json",
            project_root=context.project_root,
        )
        or generated["raster"]
        != _pin(
            context.batch_paths(
                collection_id, batch_id
            ).source
            / "raster.png",
            project_root=context.project_root,
        )
        or generated["history"]
        != _pin(
            context.batch_paths(
                collection_id, batch_id
            ).source
            / "history.json",
            project_root=context.project_root,
        )
        or generated["micro_edge_count"] != 0
        or generated["acute_micro_turn_count"] != 0
        or not isinstance(corrected_bounds, list)
        or len(corrected_bounds) != 4
        or any(
            not isinstance(value, int)
            for value in corrected_bounds
        )
        or not isinstance(generated["corrected_width"], int)
        or generated["corrected_width"] > metric["maximum_ink_width"]
        or generated["corrected_width"]
        != corrected_bounds[2] - corrected_bounds[0]
        or generated["raster"]["sha256"] != source["raster_sha256"]
        or generated["appended_sequence"] != len(history["steps"])
        or generated["call_id"]
        != history["accepted_final"]["call_id"]
        or len(history["steps"]) < 2
        or generated["parent_output_sha256"]
        != history["steps"][-2]["output"]["sha256"]
    ):
        raise MewNotePostReviewCorrectionError(
            "corrected generation evidence drift"
        )
    current = _vector_metric(
        report_path=paths.build / "report.json",
        codepoint=metric["codepoint"],
        metric=metric,
        source_sha256=sha256_path(paths.source / "source.json"),
        expect_rejected=False,
    )
    if (
        generated["vector_report"]
        != _pin(
            current["report"]["path"],
            project_root=context.project_root,
        )
        or generated["vector_ttf"]
        != _pin(
            current["ttf"]["path"],
            project_root=context.project_root,
        )
        or generated["corrected_bounds"] != current["bounds"]
        or generated["corrected_width"] != current["width"]
    ):
        raise MewNotePostReviewCorrectionError(
            "corrected vector evidence drift"
        )
    preflight = generated["candidate_preflight"]
    if (
        not isinstance(preflight, dict)
        or set(preflight)
        != {
            "candidate_raster_sha256",
            "ttf_sha256",
            "bounds",
            "width",
            "micro_edge_count",
            "acute_micro_turn_count",
        }
        or preflight["candidate_raster_sha256"]
        != generated["raster"]["sha256"]
        or preflight["ttf_sha256"]
        != generated["vector_ttf"]["sha256"]
        or preflight["bounds"] != generated["corrected_bounds"]
        or preflight["width"] != generated["corrected_width"]
        or preflight["micro_edge_count"] != 0
        or preflight["acute_micro_turn_count"] != 0
    ):
        raise MewNotePostReviewCorrectionError(
            "candidate preflight provenance drift"
        )
    if require_new_review:
        review_path = _regular_file(
            paths.source / "review.json",
            label="replacement technical review",
        )
        review = _object(
            review_path, label="replacement technical review"
        )
        if (
            sha256_path(review_path) == prior["review"]["sha256"]
            or review.get("decision") != "ACCEPT"
            or review.get("source")
            != _pin(
                paths.source / "source.json",
                project_root=context.project_root,
            )
            or review.get("evidence", {}).get("report")
            != _pin(
                paths.build / "report.json",
                project_root=context.project_root,
            )
        ):
            raise MewNotePostReviewCorrectionError(
                "replacement technical review is missing or stale"
            )
    return payload


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--collection-id", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("command", choices=("apply", "validate"))
    parser.add_argument("--codepoint")
    parser.add_argument("--candidate-raster", type=Path)
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--call-id")
    parser.add_argument("--confirmation")
    parser.add_argument("--require-new-review", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    context = evidence.load_context(args.project_root)
    if args.command == "apply":
        missing = [
            name
            for name in (
                "codepoint",
                "candidate_raster",
                "candidate_sha256",
                "call_id",
                "confirmation",
            )
            if getattr(args, name) is None
        ]
        if missing:
            raise MewNotePostReviewCorrectionError(
                "apply requires " + ", ".join(missing)
            )
        result = apply_correction(
            context,
            args.collection_id,
            args.batch_id,
            codepoint=args.codepoint,
            candidate_raster=args.candidate_raster,
            candidate_sha256=args.candidate_sha256,
            call_id=args.call_id,
            confirmation=args.confirmation,
        )
    else:
        result = validate_correction(
            context,
            args.collection_id,
            args.batch_id,
            require_new_review=args.require_new_review,
        )
    print(
        json.dumps(
            result, ensure_ascii=False, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
