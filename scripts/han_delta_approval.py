#!/usr/bin/env python3
"""Review, approve, and validate the 1,216-glyph Clear Hand Han delta.

The review record is the compact, final human-QA evidence for the collection.
It pins every irreplaceable source raster and the exact generated source,
history, vector report, font, and proof bytes that were inspected. Rebuildable
vector artifacts remain ignored by Git, but must be present and hash-identical
when an approval is validated or a release is compiled.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from fontTools.ttLib import TTFont

from scripts.han_delta_generation_history import (
    HanDeltaHistoryError,
    load_history,
)
from scripts.han_delta_repertoire import (
    HanDeltaBatch,
    HanDeltaRepertoire,
    HanDeltaRepertoireError,
    load_repertoire,
)
from scripts.register_han_delta_sheet import (
    HanDeltaRegistrationError,
    load_collection,
    validate_descriptor,
)


ROOT = Path(__file__).resolve().parents[1]
REPERTOIRE_RELATIVE = Path(
    "sources/imagegen/repertoires/"
    "dictionary-salience-extension-1216.json"
)
COLLECTION_RELATIVE = Path(
    "sources/imagegen/collections/"
    "clear-hand-tc-dictionary-salience-1216.json"
)
REVIEW_RELATIVE = Path(
    "sources/imagegen/reviews/"
    "dictionary-salience-extension-1216.review.json"
)
APPROVAL_RELATIVE = Path(
    "sources/imagegen/approvals/"
    "dictionary-salience-extension-1216.approval.json"
)

FAMILY_ID = "clear-hand-tc"
REPERTOIRE_ID = (
    "clear-hand-tc-dictionary-salience-extension-1216-v1"
)
COLLECTION_ID = REPERTOIRE_ID
PIPELINE_ID = "imagegen-raster-potrace-quadratic-v2"
REPERTOIRE_COUNT = 1_216
BATCH_COUNT = 76
SMALL_SIZES = ("12", "16", "20", "32", "56")
REVIEW_CONFIRMATION = (
    "I_INDEPENDENTLY_REVIEWED_ALL_1216_CLEAR_HAND_DELTA_GLYPHS"
)
APPROVAL_CONFIRMATION = (
    "I_AUTHORIZE_THE_REVIEWED_1216_GLYPHS_FOR_0_1_PREVIEW"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


class HanDeltaApprovalError(RuntimeError):
    """The delta review or approval is incomplete, ambiguous, or stale."""


@dataclass(frozen=True)
class ApprovedBatch:
    """One approved batch and its rebuildable vector font."""

    batch_id: str
    characters: tuple[str, ...]
    descriptor_path: Path
    descriptor_sha256: str
    raster_path: Path
    raster_sha256: str
    history_path: Path
    history_sha256: str
    report_path: Path
    report_sha256: str
    ttf_path: Path
    ttf_sha256: str


@dataclass(frozen=True)
class ApprovedDelta:
    """The complete, independently reviewed Han delta."""

    approval_path: Path
    approval_sha256: str
    review_path: Path
    review_sha256: str
    repertoire: HanDeltaRepertoire
    collection_path: Path
    collection_sha256: str
    reviewer_name: str
    reviewer_role: str
    reviewed_at: str
    approver_name: str
    approved_at: str
    batches: tuple[ApprovedBatch, ...]

    @property
    def characters(self) -> tuple[str, ...]:
        return tuple(
            character
            for batch in self.batches
            for character in batch.characters
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HanDeltaApprovalError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise HanDeltaApprovalError(f"{path}: {label} must be an object")
    return value


def _require_file(
    project_root: Path,
    relative: Path | str,
    *,
    label: str,
) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise HanDeltaApprovalError(
            f"{label}: expected a repository-relative path"
        )
    candidate = project_root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise HanDeltaApprovalError(
            f"{label}: missing {relative.as_posix()}"
        ) from exc
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError as exc:
        raise HanDeltaApprovalError(
            f"{label}: path escapes the repository"
        ) from exc
    if candidate.is_symlink() or not resolved.is_file():
        raise HanDeltaApprovalError(
            f"{label}: expected a regular non-symlink file"
        )
    return resolved


def _relative(path: Path, *, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError as exc:
        raise HanDeltaApprovalError(
            f"path escapes the repository: {path}"
        ) from exc


def _digest(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise HanDeltaApprovalError(f"{label}: invalid SHA-256")
    return value


def _timestamp(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise HanDeltaApprovalError(f"{label}: invalid UTC timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise HanDeltaApprovalError(
            f"{label}: invalid UTC timestamp"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise HanDeltaApprovalError(
            f"{label}: noncanonical UTC timestamp"
        )
    return value


def _person(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise HanDeltaApprovalError(f"{label}: invalid person name")
    return value


def _load_inputs(
    project_root: Path,
) -> tuple[HanDeltaRepertoire, Path, str]:
    try:
        repertoire = load_repertoire(
            project_root / REPERTOIRE_RELATIVE,
            project_root=project_root,
        )
        collection = load_collection(
            project_root / COLLECTION_RELATIVE,
            project_root=project_root,
        )
    except (HanDeltaRepertoireError, HanDeltaRegistrationError) as exc:
        raise HanDeltaApprovalError(str(exc)) from exc
    if (
        repertoire.family_id != FAMILY_ID
        or repertoire.repertoire_id != REPERTOIRE_ID
        or repertoire.batch_prefix != "dict-han"
        or len(repertoire.characters) != REPERTOIRE_COUNT
        or len(repertoire.batches) != BATCH_COUNT
        or collection.collection_id != COLLECTION_ID
        or collection.family_id != FAMILY_ID
        or collection.vector_pipeline != PIPELINE_ID
        or collection.repertoire.sha256 != repertoire.sha256
    ):
        raise HanDeltaApprovalError("Han delta input identity drift")
    return repertoire, collection.path, collection.sha256


def _expected_cmap(
    characters: Sequence[str],
) -> dict[int, str]:
    return {
        ord(character): (
            f"uni{ord(character):04X}"
            if ord(character) <= 0xFFFF
            else f"u{ord(character):05X}"
        )
        for character in characters
    }


def _validate_vector(
    project_root: Path,
    batch: HanDeltaBatch,
    *,
    descriptor_path: Path,
    descriptor_sha256: str,
    raster_sha256: str,
) -> tuple[Path, str, Path, str, dict[str, dict[str, str]]]:
    build_relative = Path(
        "build/imagegen"
    ) / f"imagegen-{batch.batch_id}"
    build_directory = project_root / build_relative
    report_candidate = build_directory / "report.json"
    if not report_candidate.is_file():
        if build_directory.exists():
            raise HanDeltaApprovalError(
                f"{build_directory}: partial vector build is present; "
                "remove the ignored directory before rebuilding"
            )
        from scripts import imagegen_font_pipeline

        try:
            rebuilt = imagegen_font_pipeline.build_batch(
                descriptor_path,
                output_root=project_root / "build/imagegen",
            )
        except imagegen_font_pipeline.ImagegenPipelineError as exc:
            raise HanDeltaApprovalError(
                f"{batch.batch_id}: cannot rebuild vector evidence: {exc}"
            ) from exc
        if rebuilt.resolve() != build_directory.resolve():
            raise HanDeltaApprovalError(
                f"{batch.batch_id}: vector rebuild destination drift"
            )
    report_path = _require_file(
        project_root,
        build_relative / "report.json",
        label=f"{batch.batch_id} vector report",
    )
    report = _read_object(report_path, label="vector report")
    characters = list(batch.characters)
    if (
        report.get("schema_version") != 1
        or report.get("pipeline") != PIPELINE_ID
        or report.get("batch_id") != f"imagegen-{batch.batch_id}"
        or report.get("approval_state") != "unreviewed"
        or report.get("source_state") != "generated-unreviewed"
        or report.get("source_descriptor_sha256") != descriptor_sha256
        or report.get("source_raster_sha256") != raster_sha256
        or report.get("characters") != characters
    ):
        raise HanDeltaApprovalError(
            f"{report_path}: vector identity drift"
        )
    glyphs = report.get("glyphs")
    coverage = report.get("small_size_coverage_pixels")
    if (
        not isinstance(glyphs, list)
        or len(glyphs) != len(characters)
        or not isinstance(coverage, dict)
    ):
        raise HanDeltaApprovalError(
            f"{report_path}: vector QA is incomplete"
        )
    for character, glyph in zip(characters, glyphs, strict=True):
        codepoint = f"U+{ord(character):04X}"
        pixels = coverage.get(codepoint)
        if (
            not isinstance(glyph, dict)
            or glyph.get("character") != character
            or glyph.get("codepoint") != codepoint
            or glyph.get("micro_edge_count") != 0
            or glyph.get("acute_micro_turn_count") != 0
            or glyph.get("micro_thorn_points_removed") != 0
            or glyph.get("contour_count", 0) <= 0
            or glyph.get("point_count", 0) <= 0
            or not isinstance(pixels, dict)
            or set(pixels) != set(SMALL_SIZES)
            or any(
                not isinstance(pixels[size], int) or pixels[size] <= 0
                for size in SMALL_SIZES
            )
        ):
            raise HanDeltaApprovalError(
                f"{report_path}: {codepoint} failed vector QA"
            )
    font = report.get("font")
    if (
        not isinstance(font, dict)
        or font.get("cmap_count") != len(characters)
        or not isinstance(font.get("ttf"), str)
    ):
        raise HanDeltaApprovalError(f"{report_path}: font record drift")
    ttf_path = _require_file(
        project_root,
        build_relative / str(font["ttf"]),
        label=f"{batch.batch_id} vector TTF",
    )
    ttf_sha256 = _sha256(ttf_path)
    if ttf_sha256 != font.get("ttf_sha256"):
        raise HanDeltaApprovalError(f"{ttf_path}: TTF hash drift")
    with TTFont(ttf_path, lazy=False, checkChecksums=2) as font_file:
        expected = _expected_cmap(characters)
        if font_file.getBestCmap() != expected:
            raise HanDeltaApprovalError(f"{ttf_path}: cmap drift")
        for glyph_name in expected.values():
            outline = font_file["glyf"][glyph_name]
            if outline.isComposite() or outline.numberOfContours <= 0:
                raise HanDeltaApprovalError(
                    f"{ttf_path}: {glyph_name} is empty or composite"
                )

    proofs = report.get("proofs")
    if not isinstance(proofs, dict) or set(proofs) != {
        "black_on_white",
        "white_on_black",
        "segmented_source",
    }:
        raise HanDeltaApprovalError(
            f"{report_path}: proof inventory drift"
        )
    proof_records: dict[str, dict[str, str]] = {}
    for key in ("black_on_white", "white_on_black", "segmented_source"):
        value = proofs[key]
        if not isinstance(value, str):
            raise HanDeltaApprovalError(
                f"{report_path}: invalid {key} proof path"
            )
        proof_path = _require_file(
            project_root,
            build_relative / value,
            label=f"{batch.batch_id} {key} proof",
        )
        proof_records[key] = {
            "path": _relative(proof_path, project_root=project_root),
            "sha256": _sha256(proof_path),
        }
    return (
        report_path,
        _sha256(report_path),
        ttf_path,
        ttf_sha256,
        proof_records,
    )


def _batch_evidence(
    project_root: Path,
    batch: HanDeltaBatch,
) -> tuple[dict[str, Any], ApprovedBatch]:
    descriptor_path = _require_file(
        project_root,
        Path("sources/imagegen/batches")
        / f"{batch.batch_id}.source.json",
        label=f"{batch.batch_id} descriptor",
    )
    try:
        descriptor = validate_descriptor(
            descriptor_path,
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise HanDeltaApprovalError(str(exc)) from exc
    if descriptor.get("grid", {}).get("characters") != list(
        batch.characters
    ):
        raise HanDeltaApprovalError(
            f"{descriptor_path}: batch character drift"
        )
    descriptor_sha256 = _sha256(descriptor_path)
    raster_path = _require_file(
        project_root,
        Path("sources/imagegen/raster") / f"{batch.batch_id}.png",
        label=f"{batch.batch_id} raster",
    )
    raster_sha256 = _sha256(raster_path)
    if descriptor.get("raster_sha256") != raster_sha256:
        raise HanDeltaApprovalError(
            f"{descriptor_path}: raster hash drift"
        )
    history_path = _require_file(
        project_root,
        Path("sources/imagegen/batches")
        / f"{batch.batch_id}.history.json",
        label=f"{batch.batch_id} generation history",
    )
    try:
        history = load_history(history_path, project_root=project_root)
    except HanDeltaHistoryError as exc:
        raise HanDeltaApprovalError(str(exc)) from exc
    if (
        history.batch_id != batch.batch_id
        or history.accepted_raster_sha256 != raster_sha256
        or descriptor.get("generation_history", {}).get("sha256")
        != history.sha256
    ):
        raise HanDeltaApprovalError(
            f"{history_path}: accepted-source drift"
        )
    (
        report_path,
        report_sha256,
        ttf_path,
        ttf_sha256,
        proofs,
    ) = _validate_vector(
        project_root,
        batch,
        descriptor_path=descriptor_path,
        descriptor_sha256=descriptor_sha256,
        raster_sha256=raster_sha256,
    )
    evidence = {
        "batch_id": batch.batch_id,
        "characters": "".join(batch.characters),
        "decision": {
            "topology": "PASS",
            "raster_quality": "PASS",
            "vector_quality": "PASS",
            "small_size_legibility": "PASS",
            "spike_and_thorn_check": "PASS",
        },
        "descriptor": {
            "path": _relative(
                descriptor_path, project_root=project_root
            ),
            "sha256": descriptor_sha256,
        },
        "history": {
            "path": _relative(history_path, project_root=project_root),
            "sha256": history.sha256,
        },
        "raster": {
            "path": _relative(raster_path, project_root=project_root),
            "sha256": raster_sha256,
        },
        "vector_report": {
            "path": _relative(report_path, project_root=project_root),
            "sha256": report_sha256,
        },
        "vector_ttf": {
            "path": _relative(ttf_path, project_root=project_root),
            "sha256": ttf_sha256,
        },
        "proofs": proofs,
    }
    admitted = ApprovedBatch(
        batch_id=batch.batch_id,
        characters=batch.characters,
        descriptor_path=descriptor_path,
        descriptor_sha256=descriptor_sha256,
        raster_path=raster_path,
        raster_sha256=raster_sha256,
        history_path=history_path,
        history_sha256=history.sha256,
        report_path=report_path,
        report_sha256=report_sha256,
        ttf_path=ttf_path,
        ttf_sha256=ttf_sha256,
    )
    return evidence, admitted


def _repertoire_record(
    repertoire: HanDeltaRepertoire,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "path": _relative(repertoire.path, project_root=project_root),
        "sha256": repertoire.sha256,
        "repertoire_id": repertoire.repertoire_id,
        "count": len(repertoire.characters),
        "sequence_sha256": repertoire.sequence_sha256,
    }


def _collection_record(
    collection_path: Path,
    collection_sha256: str,
    *,
    project_root: Path,
) -> dict[str, str]:
    return {
        "path": _relative(collection_path, project_root=project_root),
        "sha256": collection_sha256,
        "collection_id": COLLECTION_ID,
    }


def _write_new_or_identical(
    path: Path,
    payload: Mapping[str, Any],
) -> Path:
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise HanDeltaApprovalError(f"refusing to overwrite {path}")
    path.write_text(encoded, encoding="utf-8")
    return path


def record_review(
    *,
    project_root: Path,
    reviewer_name: str,
    reviewer_role: str,
    reviewed_at: str,
    confirmation: str,
) -> Path:
    """Record the independent collection review after visual inspection."""

    if confirmation != REVIEW_CONFIRMATION:
        raise HanDeltaApprovalError(
            "explicit independent-review confirmation is required"
        )
    project_root = project_root.resolve()
    reviewer_name = _person(reviewer_name, label="reviewer_name")
    reviewer_role = _person(reviewer_role, label="reviewer_role")
    reviewed_at = _timestamp(reviewed_at, label="reviewed_at")
    repertoire, collection_path, collection_sha256 = _load_inputs(
        project_root
    )
    inventory = [
        _batch_evidence(project_root, batch)[0]
        for batch in repertoire.batches
    ]
    payload = {
        "schema_version": 1,
        "record_type": "clear-hand-han-delta-collection-review",
        "decision": "ACCEPTED",
        "family_id": FAMILY_ID,
        "release": "0.1 Preview",
        "repertoire": _repertoire_record(
            repertoire, project_root=project_root
        ),
        "collection": _collection_record(
            collection_path,
            collection_sha256,
            project_root=project_root,
        ),
        "review": {
            "reviewer_name": reviewer_name,
            "reviewer_role": reviewer_role,
            "reviewed_at": reviewed_at,
            "scope": (
                "all 1,216 glyphs: Traditional Chinese identity and "
                "topology, handwritten raster quality, vector contour "
                "quality, unexpected spikes/thorns, counter openness, and "
                "12/16/20/32/56 px legibility"
            ),
            "method": (
                "identity-copybook comparison plus black-on-white, "
                "white-on-black, and segmented-source proof inspection"
            ),
        },
        "source_batches": inventory,
    }
    output = project_root / REVIEW_RELATIVE
    _write_new_or_identical(output, payload)
    validate_review(project_root=project_root, review_path=output)
    return output


def _expect_pin(
    value: Any,
    *,
    path: Path,
    digest: str,
    label: str,
) -> None:
    expected = {"path": path.as_posix(), "sha256": digest}
    if value != expected:
        raise HanDeltaApprovalError(f"{label}: evidence pin drift")


def validate_review(
    *,
    project_root: Path = ROOT,
    review_path: Path | None = None,
) -> tuple[
    dict[str, Any],
    HanDeltaRepertoire,
    Path,
    str,
    tuple[ApprovedBatch, ...],
]:
    """Validate the review and every byte of evidence it pins."""

    project_root = project_root.resolve()
    expected_path = (project_root / REVIEW_RELATIVE).resolve()
    review_path = (review_path or expected_path).resolve()
    if review_path != expected_path:
        raise HanDeltaApprovalError("review path is not canonical")
    review = _read_object(review_path, label="Han delta review")
    if (
        review.get("schema_version") != 1
        or review.get("record_type")
        != "clear-hand-han-delta-collection-review"
        or review.get("decision") != "ACCEPTED"
        or review.get("family_id") != FAMILY_ID
        or review.get("release") != "0.1 Preview"
    ):
        raise HanDeltaApprovalError(f"{review_path}: review identity drift")
    repertoire, collection_path, collection_sha256 = _load_inputs(
        project_root
    )
    if review.get("repertoire") != _repertoire_record(
        repertoire, project_root=project_root
    ):
        raise HanDeltaApprovalError(f"{review_path}: repertoire pin drift")
    if review.get("collection") != _collection_record(
        collection_path,
        collection_sha256,
        project_root=project_root,
    ):
        raise HanDeltaApprovalError(f"{review_path}: collection pin drift")
    reviewer = review.get("review")
    if not isinstance(reviewer, dict):
        raise HanDeltaApprovalError(f"{review_path}: review metadata missing")
    _person(reviewer.get("reviewer_name"), label="reviewer_name")
    _person(reviewer.get("reviewer_role"), label="reviewer_role")
    _timestamp(reviewer.get("reviewed_at"), label="reviewed_at")
    sources = review.get("source_batches")
    if not isinstance(sources, list) or len(sources) != BATCH_COUNT:
        raise HanDeltaApprovalError(
            f"{review_path}: source batch inventory is incomplete"
        )
    admitted: list[ApprovedBatch] = []
    for batch, pinned in zip(repertoire.batches, sources, strict=True):
        if not isinstance(pinned, dict):
            raise HanDeltaApprovalError(
                f"{batch.batch_id}: malformed review evidence"
            )
        expected, approved = _batch_evidence(project_root, batch)
        if pinned != expected:
            raise HanDeltaApprovalError(
                f"{batch.batch_id}: reviewed evidence drift"
            )
        admitted.append(approved)
    return (
        review,
        repertoire,
        collection_path,
        collection_sha256,
        tuple(admitted),
    )


def record_approval(
    *,
    project_root: Path,
    approver_name: str,
    approved_at: str,
    confirmation: str,
) -> Path:
    """Authorize the already-recorded independent review for release."""

    if confirmation != APPROVAL_CONFIRMATION:
        raise HanDeltaApprovalError(
            "explicit release authorization is required"
        )
    project_root = project_root.resolve()
    approver_name = _person(approver_name, label="approver_name")
    approved_at = _timestamp(approved_at, label="approved_at")
    (
        review,
        repertoire,
        collection_path,
        collection_sha256,
        _batches,
    ) = validate_review(project_root=project_root)
    review_meta = review["review"]
    reviewed_at = _timestamp(
        review_meta["reviewed_at"], label="reviewed_at"
    )
    if approved_at < reviewed_at:
        raise HanDeltaApprovalError("approval predates the review")
    review_path = project_root / REVIEW_RELATIVE
    payload = {
        "schema_version": 1,
        "record_type": "clear-hand-han-delta-collection-approval",
        "decision": "APPROVED",
        "family_id": FAMILY_ID,
        "release": "0.1 Preview",
        "repertoire": _repertoire_record(
            repertoire, project_root=project_root
        ),
        "collection": _collection_record(
            collection_path,
            collection_sha256,
            project_root=project_root,
        ),
        "review": {
            "path": REVIEW_RELATIVE.as_posix(),
            "sha256": _sha256(review_path),
            "reviewer_name": review_meta["reviewer_name"],
            "reviewer_role": review_meta["reviewer_role"],
            "reviewed_at": reviewed_at,
        },
        "authorization": {
            "decision": "APPROVED",
            "approver_name": approver_name,
            "approved_at": approved_at,
        },
    }
    output = project_root / APPROVAL_RELATIVE
    _write_new_or_identical(output, payload)
    validate_approval(project_root=project_root, approval_path=output)
    return output


def validate_approval(
    *,
    project_root: Path = ROOT,
    approval_path: Path | None = None,
) -> ApprovedDelta:
    """Validate release authorization, review, and all admitted glyphs."""

    project_root = project_root.resolve()
    expected_path = (project_root / APPROVAL_RELATIVE).resolve()
    approval_path = (approval_path or expected_path).resolve()
    if approval_path != expected_path:
        raise HanDeltaApprovalError("approval path is not canonical")
    approval = _read_object(approval_path, label="Han delta approval")
    if (
        approval.get("schema_version") != 1
        or approval.get("record_type")
        != "clear-hand-han-delta-collection-approval"
        or approval.get("decision") != "APPROVED"
        or approval.get("family_id") != FAMILY_ID
        or approval.get("release") != "0.1 Preview"
    ):
        raise HanDeltaApprovalError(
            f"{approval_path}: approval identity drift"
        )
    (
        review,
        repertoire,
        collection_path,
        collection_sha256,
        batches,
    ) = validate_review(project_root=project_root)
    if approval.get("repertoire") != _repertoire_record(
        repertoire, project_root=project_root
    ):
        raise HanDeltaApprovalError(
            f"{approval_path}: repertoire pin drift"
        )
    if approval.get("collection") != _collection_record(
        collection_path,
        collection_sha256,
        project_root=project_root,
    ):
        raise HanDeltaApprovalError(
            f"{approval_path}: collection pin drift"
        )
    review_meta = review["review"]
    expected_review = {
        "path": REVIEW_RELATIVE.as_posix(),
        "sha256": _sha256(project_root / REVIEW_RELATIVE),
        "reviewer_name": review_meta["reviewer_name"],
        "reviewer_role": review_meta["reviewer_role"],
        "reviewed_at": review_meta["reviewed_at"],
    }
    if approval.get("review") != expected_review:
        raise HanDeltaApprovalError(
            f"{approval_path}: review authorization pin drift"
        )
    authorization = approval.get("authorization")
    if (
        not isinstance(authorization, dict)
        or authorization.get("decision") != "APPROVED"
    ):
        raise HanDeltaApprovalError(
            f"{approval_path}: authorization missing"
        )
    approver_name = _person(
        authorization.get("approver_name"), label="approver_name"
    )
    approved_at = _timestamp(
        authorization.get("approved_at"), label="approved_at"
    )
    reviewed_at = _timestamp(
        review_meta["reviewed_at"], label="reviewed_at"
    )
    if approved_at < reviewed_at:
        raise HanDeltaApprovalError("approval predates the review")
    result = ApprovedDelta(
        approval_path=approval_path,
        approval_sha256=_sha256(approval_path),
        review_path=project_root / REVIEW_RELATIVE,
        review_sha256=expected_review["sha256"],
        repertoire=repertoire,
        collection_path=collection_path,
        collection_sha256=collection_sha256,
        reviewer_name=str(review_meta["reviewer_name"]),
        reviewer_role=str(review_meta["reviewer_role"]),
        reviewed_at=reviewed_at,
        approver_name=approver_name,
        approved_at=approved_at,
        batches=batches,
    )
    if (
        len(result.characters) != REPERTOIRE_COUNT
        or result.characters != repertoire.characters
        or len(set(result.characters)) != REPERTOIRE_COUNT
    ):
        raise HanDeltaApprovalError("approved character sequence drift")
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    review = subparsers.add_parser("record-review")
    review.add_argument("--reviewer", required=True)
    review.add_argument("--reviewer-role", required=True)
    review.add_argument("--reviewed-at", required=True)
    review.add_argument("--confirmation", required=True)
    approval = subparsers.add_parser("record-approval")
    approval.add_argument("--approver", required=True)
    approval.add_argument("--approved-at", required=True)
    approval.add_argument("--confirmation", required=True)
    subparsers.add_parser("validate-review")
    subparsers.add_parser("validate")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    if args.command == "record-review":
        output = record_review(
            project_root=project_root,
            reviewer_name=args.reviewer,
            reviewer_role=args.reviewer_role,
            reviewed_at=args.reviewed_at,
            confirmation=args.confirmation,
        )
        print(output)
    elif args.command == "record-approval":
        output = record_approval(
            project_root=project_root,
            approver_name=args.approver,
            approved_at=args.approved_at,
            confirmation=args.confirmation,
        )
        print(output)
    elif args.command == "validate-review":
        _review, repertoire, _path, _digest_value, batches = (
            validate_review(project_root=project_root)
        )
        print(
            f"validated {len(batches)} reviewed batches covering "
            f"{len(repertoire.characters)} glyphs"
        )
    else:
        approved = validate_approval(project_root=project_root)
        print(
            f"validated {len(approved.batches)} approved batches covering "
            f"{len(approved.characters)} glyphs"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
