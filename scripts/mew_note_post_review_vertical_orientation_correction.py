#!/usr/bin/env python3
"""Correct one reviewed Mew Note vertical batch after orientation rejection.

This module is intentionally independent from the release-metric correction
workflow.  It installs only a deterministic two-region composite made from an
exact image-generation output, preserves every pixel outside those regions,
and leaves the complete atomic batch requiring a replacement technical review
and collection release reapproval.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterator, Mapping, Sequence

from PIL import Image

from scripts.font_family_context import canonical_json_sha256, sha256_path
from scripts import imagegen_font_pipeline
from scripts import mew_note_batch_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = Path(
    "scripts/mew_note_post_review_vertical_orientation_correction.py"
)
APPROVAL_PATH = Path(
    "families/mew-note-tc/approvals/"
    "original-raster-v1-preview.approval.json"
)
RECORD_NAME = "post-review-vertical-orientation-correction.json"
RAW_CANDIDATE_NAME = "vertical-orientation-raw-candidate.png"
SCHEMA_VERSION = 1
RECORD_TYPE = (
    "mew-note-tc-post-review-vertical-orientation-correction"
)
REASON = "release-vertical-orientation-rejected"
CONFIRMATION = (
    "I_AUTHORIZE_POST_REVIEW_VERTICAL_ORIENTATION_CORRECTION"
)
COLLECTION_ID = "vertical-93"
BATCH_ID = "vertical-0002"
TARGETS: tuple[dict[str, Any], ...] = (
    {
        "cell": 6,
        "character": "」",
        "codepoint": "U+300D",
        "report_source_box": [318, 313, 625, 615],
        "replacement_box": [319, 314, 624, 614],
        "minimum_horizontal_to_vertical_ratio": 1.7,
        "expected_core_component_count": 1,
    },
    {
        "cell": 8,
        "character": "』",
        "codepoint": "U+300F",
        "report_source_box": [930, 313, 1237, 615],
        "replacement_box": [931, 314, 1236, 614],
        "minimum_horizontal_to_vertical_ratio": 1.5,
        "expected_core_component_count": 2,
    },
)
COMPOSITE_ALGORITHM = (
    "rgb-png-cell-interior-rectangular-replacement-v1"
)
PIXEL_HASH_ALGORITHM = "sha256-framed-rgb-row-major-v1"


class MewNoteVerticalOrientationCorrectionError(RuntimeError):
    """A vertical-orientation correction is incomplete, stale, or unsafe."""


def correction_path(context: evidence.FamilyContext) -> Path:
    return (
        context.batch_paths(COLLECTION_ID, BATCH_ID).source
        / RECORD_NAME
    )


def raw_candidate_path(context: evidence.FamilyContext) -> Path:
    return (
        context.batch_paths(COLLECTION_ID, BATCH_ID).source
        / RAW_CANDIDATE_NAME
    )


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


def _atomic_copy(source: Path, destination: Path) -> None:
    source = _regular_file(source, label="copy source")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        with source.open("rb") as incoming:
            shutil.copyfileobj(incoming, stream)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteVerticalOrientationCorrectionError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MewNoteVerticalOrientationCorrectionError(
            f"{path}: {label} must be an object"
        )
    return value


def _regular_file(path: Path, *, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise MewNoteVerticalOrientationCorrectionError(
            f"{label}: expected a regular non-symlink file: {path}"
        )
    return path.resolve()


def _relative(path: Path, *, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError as exc:
        raise MewNoteVerticalOrientationCorrectionError(
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
        raise MewNoteVerticalOrientationCorrectionError(
            f"{label} is not a lowercase SHA-256"
        )
    return value


def _exact_keys(
    value: Any,
    expected: set[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise MewNoteVerticalOrientationCorrectionError(
            f"{label} key set changed"
        )
    return value


def _load_rgb_png(path: Path, *, label: str) -> Image.Image:
    path = _regular_file(path, label=label)
    try:
        with Image.open(path) as source:
            source.load()
            if (
                source.format != "PNG"
                or source.mode != "RGB"
                or source.size != (1254, 1254)
            ):
                raise MewNoteVerticalOrientationCorrectionError(
                    f"{label} must be a 1254×1254 RGB PNG"
                )
            return source.copy()
    except (OSError, ValueError) as exc:
        raise MewNoteVerticalOrientationCorrectionError(
            f"{label} cannot be decoded: {exc}"
        ) from exc


def _framed_pixel_sha256(
    image: Image.Image,
    *,
    regions: Sequence[Sequence[int]],
    include_regions: bool,
) -> str:
    if image.mode != "RGB" or image.size != (1254, 1254):
        raise MewNoteVerticalOrientationCorrectionError(
            "pixel hash image contract changed"
        )
    normalized = tuple(tuple(int(value) for value in box) for box in regions)
    if any(
        len(box) != 4
        or not (0 <= box[0] < box[2] <= image.width)
        or not (0 <= box[1] < box[3] <= image.height)
        for box in normalized
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "pixel hash region is invalid"
        )
    framed = {
        "algorithm": PIXEL_HASH_ALGORITHM,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "regions": [list(box) for box in normalized],
        "selection": "inside" if include_regions else "outside",
    }
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            framed,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            inside = any(
                left <= x < right and top <= y < bottom
                for left, top, right, bottom in normalized
            )
            if inside is include_regions:
                digest.update(bytes(pixels[x, y]))
    return digest.hexdigest()


def _region_sha256(image: Image.Image, box: Sequence[int]) -> str:
    return _framed_pixel_sha256(
        image,
        regions=(box,),
        include_regions=True,
    )


def _save_png(image: Image.Image, path: Path) -> None:
    if image.mode != "RGB" or image.size != (1254, 1254):
        raise MewNoteVerticalOrientationCorrectionError(
            "composite canvas contract changed"
        )
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
    try:
        image.save(
            temporary,
            format="PNG",
            optimize=False,
            compress_level=9,
        )
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _compose(
    original_path: Path,
    candidate_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    original = _load_rgb_png(original_path, label="superseded raster")
    candidate = _load_rgb_png(candidate_path, label="raw candidate raster")
    boxes = [target["replacement_box"] for target in TARGETS]
    outside_before = _framed_pixel_sha256(
        original,
        regions=boxes,
        include_regions=False,
    )
    result = original.copy()
    regions: list[dict[str, Any]] = []
    for target in TARGETS:
        box = tuple(target["replacement_box"])
        old_digest = _region_sha256(original, box)
        new_digest = _region_sha256(candidate, box)
        if old_digest == new_digest:
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: candidate region is unchanged"
            )
        result.paste(candidate.crop(box), box)
        regions.append(
            {
                **target,
                "superseded_region_sha256": old_digest,
                "candidate_region_sha256": new_digest,
            }
        )
    outside_after = _framed_pixel_sha256(
        result,
        regions=boxes,
        include_regions=False,
    )
    if outside_after != outside_before:
        raise MewNoteVerticalOrientationCorrectionError(
            "composite changed pixels outside the two authorized regions"
        )
    for target in regions:
        if _region_sha256(
            result, target["replacement_box"]
        ) != target["candidate_region_sha256"]:
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: composite region drift"
            )
    _save_png(result, output_path)
    installed = _load_rgb_png(output_path, label="installed composite")
    if installed.tobytes() != result.tobytes():
        raise MewNoteVerticalOrientationCorrectionError(
            "deterministic PNG serialization changed composite pixels"
        )
    return {
        "algorithm": COMPOSITE_ALGORITHM,
        "pixel_hash_algorithm": PIXEL_HASH_ALGORITHM,
        "canvas": {
            "width": 1254,
            "height": 1254,
            "mode": "RGB",
        },
        "regions": regions,
        "preserved_outside_regions_sha256": outside_before,
        "installed_composite_sha256": sha256_path(output_path),
    }


def _report_ttf(
    report_path: Path,
    report: Mapping[str, Any],
) -> Path:
    font = report.get("font")
    if not isinstance(font, dict) or not isinstance(font.get("ttf"), str):
        raise MewNoteVerticalOrientationCorrectionError(
            f"{report_path}: vector TTF is missing"
        )
    candidate = (report_path.parent / font["ttf"]).resolve()
    try:
        candidate.relative_to(report_path.parent.resolve())
    except ValueError as exc:
        raise MewNoteVerticalOrientationCorrectionError(
            f"{report_path}: vector TTF path escapes build"
        ) from exc
    candidate = _regular_file(candidate, label="batch vector TTF")
    if sha256_path(candidate) != font.get("ttf_sha256"):
        raise MewNoteVerticalOrientationCorrectionError(
            f"{candidate}: vector TTF hash drift"
        )
    return candidate


def _orientation_diagnostics(
    report_path: Path,
    *,
    source_sha256: str,
    expect_accepted: bool,
) -> list[dict[str, Any]]:
    report = _object(report_path, label="batch vector report")
    glyphs = report.get("glyphs")
    if (
        report.get("approval_state") != "unreviewed"
        or report.get("source_descriptor_sha256") != source_sha256
        or not isinstance(glyphs, list)
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            f"{report_path}: vector report binding drift"
        )
    _report_ttf(report_path, report)
    result: list[dict[str, Any]] = []
    for target in TARGETS:
        matching = [
            glyph
            for glyph in glyphs
            if isinstance(glyph, dict)
            and glyph.get("codepoint") == target["codepoint"]
        ]
        if len(matching) != 1:
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: vector record is not unique"
            )
        glyph = matching[0]
        bounds = glyph.get("source_ink_bbox_normalized")
        if (
            glyph.get("character") != target["character"]
            or glyph.get("row") != 1
            or glyph.get("column") != target["cell"] - 5
            or glyph.get("source_box") != target["report_source_box"]
            or glyph.get("source_core_component_count")
            != target["expected_core_component_count"]
            or glyph.get("contour_count")
            != target["expected_core_component_count"]
            or glyph.get("micro_edge_count") != 0
            or glyph.get("acute_micro_turn_count") != 0
            or not isinstance(bounds, list)
            or len(bounds) != 4
            or any(
                not isinstance(value, (int, float))
                for value in bounds
            )
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: orientation topology drift"
            )
        width = round(float(bounds[2]) - float(bounds[0]), 6)
        height = round(float(bounds[3]) - float(bounds[1]), 6)
        if width <= 0 or height <= 0:
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: empty orientation bounds"
            )
        ratio = round(width / height, 6)
        accepted = (
            ratio
            >= target["minimum_horizontal_to_vertical_ratio"]
        )
        if accepted is not expect_accepted:
            expected = "pass" if expect_accepted else "fail"
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: orientation ratio {ratio} "
                f"does not {expected} the horizontal-form contract"
            )
        result.append(
            {
                "cell": target["cell"],
                "character": target["character"],
                "codepoint": target["codepoint"],
                "source_ink_bbox_normalized": bounds,
                "ink_width": width,
                "ink_height": height,
                "horizontal_to_vertical_ratio": ratio,
                "minimum_horizontal_to_vertical_ratio": (
                    target[
                        "minimum_horizontal_to_vertical_ratio"
                    ]
                ),
                "source_core_component_count": (
                    glyph["source_core_component_count"]
                ),
                "contour_count": glyph["contour_count"],
                "micro_edge_count": 0,
                "acute_micro_turn_count": 0,
                "decision": "ACCEPT" if accepted else "REJECT",
            }
        )
    return result


def _unchanged_glyph_evidence(
    old_report_path: Path,
    new_report_path: Path,
) -> list[dict[str, str]]:
    old_report = _object(
        old_report_path, label="superseded vector report"
    )
    new_report = _object(
        new_report_path, label="candidate vector report"
    )
    target_codepoints = {target["codepoint"] for target in TARGETS}
    fields = (
        "source_png_sha256",
        "svg_sha256",
        "proof_png_sha256",
    )
    old = {
        glyph["codepoint"]: glyph
        for glyph in old_report.get("glyphs", [])
        if isinstance(glyph, dict)
        and glyph.get("codepoint") not in target_codepoints
    }
    new = {
        glyph["codepoint"]: glyph
        for glyph in new_report.get("glyphs", [])
        if isinstance(glyph, dict)
        and glyph.get("codepoint") not in target_codepoints
    }
    if set(old) != set(new) or len(old) != 14:
        raise MewNoteVerticalOrientationCorrectionError(
            "non-target glyph inventory changed"
        )
    records: list[dict[str, str]] = []
    for codepoint in old:
        if (
            old[codepoint].get("character")
            != new[codepoint].get("character")
            or any(
                old[codepoint].get(field)
                != new[codepoint].get(field)
                for field in fields
            )
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{codepoint}: non-target vector evidence changed"
            )
        records.append(
            {
                "character": str(old[codepoint]["character"]),
                "codepoint": codepoint,
                **{
                    field: str(old[codepoint][field])
                    for field in fields
                },
            }
        )
    return records


def _build_snapshot(
    report_path: Path,
    *,
    project_root: Path,
    retention: str | None = None,
) -> dict[str, Any]:
    report = _object(report_path, label="batch vector report")
    ttf = _report_ttf(report_path, report)
    proofs = report.get("proofs")
    if not isinstance(proofs, dict):
        raise MewNoteVerticalOrientationCorrectionError(
            f"{report_path}: proof inventory is missing"
        )
    result: dict[str, Any] = {
        "report": _pin(
            report_path,
            project_root=project_root,
            retention=retention,
        ),
        "ttf": _pin(
            ttf,
            project_root=project_root,
            retention=retention,
        ),
    }
    for key in (
        "black_on_white",
        "white_on_black",
        "segmented_source",
    ):
        relative = proofs.get(key)
        if not isinstance(relative, str):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{report_path}: {key} proof is missing"
            )
        result[key] = _pin(
            report_path.parent / relative,
            project_root=project_root,
            retention=retention,
        )
    return result


def _prior_release_approval(
    *,
    context: evidence.FamilyContext,
    review_path: Path,
) -> dict[str, str]:
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
        and item.get("collection_id") == COLLECTION_ID
        and item.get("batch_id") == BATCH_ID
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
        raise MewNoteVerticalOrientationCorrectionError(
            "current release approval does not admit the exact prior review"
        )
    return _pin(
        approval_path,
        project_root=context.project_root,
        retention="hash-only-superseded-after-reapproval",
    )


def _history_steps(
    context: evidence.FamilyContext,
    history: Mapping[str, Any],
) -> list[evidence.GenerationStep]:
    result: list[evidence.GenerationStep] = []
    steps = history["steps"]
    for index, step in enumerate(steps):
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
                    if index == len(steps) - 1
                    else step["disposition"]
                ),
                call_id=step["call_id"],
                prompt_path=(
                    context.project_root
                    / step["actual_tool_prompt"]["path"]
                ),
                inputs=inputs,
                output_sha256=step["output"]["sha256"],
                output_path=None,
                parent_output_sha256=step["parent_output_sha256"],
            )
        )
    return result


def _minimal_descriptor(
    *,
    batch: Mapping[str, Any],
    raster_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "state": "generated-unreviewed",
        "raster": "raster.png",
        "raster_sha256": raster_sha256,
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


def _preflight_candidate(
    *,
    context: evidence.FamilyContext,
    batch: Mapping[str, Any],
    original_raster: Path,
    candidate_raster: Path,
    candidate_sha256: str,
    old_report_path: Path,
) -> tuple[dict[str, Any], Path]:
    candidate_raster = _regular_file(
        candidate_raster, label="raw candidate raster"
    )
    if sha256_path(candidate_raster) != candidate_sha256:
        raise MewNoteVerticalOrientationCorrectionError(
            "raw candidate raster hash mismatch"
        )
    temporary = Path(
        tempfile.mkdtemp(
            prefix="mew-note-vertical-orientation-preflight-"
        )
    )
    try:
        raster = temporary / "raster.png"
        composite = _compose(
            original_raster,
            candidate_raster,
            raster,
        )
        descriptor_path = temporary / "source.json"
        descriptor_path.write_bytes(
            _json_bytes(
                _minimal_descriptor(
                    batch=batch,
                    raster_sha256=sha256_path(raster),
                )
            )
        )
        final = imagegen_font_pipeline.build_batch(
            descriptor_path,
            output_root=temporary / "build",
            allowed_raster_root=temporary,
            family_name_prefix="Mew Note TC",
            postscript_name_prefix="MewNoteTC",
        )
        report_path = final / "report.json"
        diagnostics = _orientation_diagnostics(
            report_path,
            source_sha256=sha256_path(descriptor_path),
            expect_accepted=True,
        )
        unchanged = _unchanged_glyph_evidence(
            old_report_path,
            report_path,
        )
        report = _object(
            report_path, label="candidate vector report"
        )
        ttf = _report_ttf(report_path, report)
        result = {
            "raw_candidate_sha256": candidate_sha256,
            "installed_composite_sha256": (
                composite["installed_composite_sha256"]
            ),
            "ttf_sha256": sha256_path(ttf),
            "orientation_diagnostics": diagnostics,
            "unchanged_non_target_glyphs": unchanged,
            "micro_edge_count": sum(
                int(glyph["micro_edge_count"])
                for glyph in report["glyphs"]
            ),
            "acute_micro_turn_count": sum(
                int(glyph["acute_micro_turn_count"])
                for glyph in report["glyphs"]
            ),
        }
        if (
            result["micro_edge_count"] != 0
            or result["acute_micro_turn_count"] != 0
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                "candidate failed strict vector geometry"
            )
        retained_composite = temporary / "retained-composite.png"
        raster.replace(retained_composite)
        return result, retained_composite
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[Path]:
    lock = path.with_name(f".{path.name}.lock")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock, flags, 0o600)
    except FileExistsError as exc:
        raise MewNoteVerticalOrientationCorrectionError(
            f"correction lock already exists: {lock}"
        ) from exc
    try:
        os.write(
            descriptor,
            f"pid={os.getpid()}\n".encode("ascii"),
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    succeeded = False
    try:
        yield lock
        succeeded = True
    finally:
        if succeeded:
            lock.unlink(missing_ok=True)


def apply_correction(
    context: evidence.FamilyContext,
    *,
    candidate_raster: Path,
    candidate_sha256: str,
    call_id: str,
    confirmation: str,
    reason: str = REASON,
) -> dict[str, Any]:
    """Install the two-cell composite and invalidate review and approval."""

    if confirmation != CONFIRMATION:
        raise MewNoteVerticalOrientationCorrectionError(
            "explicit vertical-orientation correction authorization "
            "is required"
        )
    if reason != REASON:
        raise MewNoteVerticalOrientationCorrectionError(
            "unsupported vertical-orientation correction reason"
        )
    _sha(candidate_sha256, label="raw candidate hash")
    if evidence.CALL_ID_PATTERN.fullmatch(call_id) is None:
        raise MewNoteVerticalOrientationCorrectionError(
            "image-generation call ID is invalid"
        )
    record_path = correction_path(context)
    retained_candidate = raw_candidate_path(context)
    paths = context.batch_paths(COLLECTION_ID, BATCH_ID)
    root = paths.source
    with _exclusive_lock(record_path) as lock_path:
        if record_path.exists() or retained_candidate.exists():
            raise MewNoteVerticalOrientationCorrectionError(
                "vertical-orientation correction already exists"
            )
        history = evidence.validate_history(
            context, COLLECTION_ID, BATCH_ID
        )
        evidence.validate_source(context, COLLECTION_ID, BATCH_ID)
        batch = evidence.frozen_batch(
            context, COLLECTION_ID, BATCH_ID
        )
        if [
            (entry["cell"], entry["character"], entry["codepoint"])
            for entry in batch["entries"]
            if entry["codepoint"]
            in {target["codepoint"] for target in TARGETS}
        ] != [
            (
                target["cell"],
                target["character"],
                target["codepoint"],
            )
            for target in TARGETS
        ]:
            raise MewNoteVerticalOrientationCorrectionError(
                "target cells are not frozen at vertical-0002 cells 6/8"
            )
        source_path = root / "source.json"
        raster_path = root / "raster.png"
        review_path = _regular_file(
            root / "review.json",
            label="prior technical review",
        )
        report_path = paths.build / "report.json"
        review = _object(
            review_path, label="prior technical review"
        )
        if (
            review.get("decision") != "ACCEPT"
            or review.get("source")
            != _pin(
                source_path,
                project_root=context.project_root,
            )
            or review.get("evidence", {}).get("report")
            != _pin(
                report_path,
                project_root=context.project_root,
            )
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                "prior technical review is stale or incomplete"
            )
        rejected = _orientation_diagnostics(
            report_path,
            source_sha256=sha256_path(source_path),
            expect_accepted=False,
        )
        old_report = _object(
            report_path, label="superseded vector report"
        )
        prior_build = _build_snapshot(
            report_path,
            project_root=context.project_root,
            retention="hash-only-derived-superseded",
        )
        prior = {
            "history": _pin(
                root / "history.json",
                project_root=context.project_root,
                retention="hash-only-superseded",
            ),
            "source": _pin(
                source_path,
                project_root=context.project_root,
                retention="hash-only-superseded",
            ),
            "raster": _pin(
                raster_path,
                project_root=context.project_root,
                retention="hash-only-superseded",
            ),
            "review": _pin(
                review_path,
                project_root=context.project_root,
                retention="hash-only-superseded",
            ),
            "release_approval": _prior_release_approval(
                context=context,
                review_path=review_path,
            ),
            "build": prior_build,
        }
        preflight, retained_composite = _preflight_candidate(
            context=context,
            batch=batch,
            original_raster=raster_path,
            candidate_raster=candidate_raster,
            candidate_sha256=candidate_sha256,
            old_report_path=report_path,
        )
        temporary_root = retained_composite.parent
        composite_contract = _compose(
            raster_path,
            candidate_raster,
            temporary_root / "canonical-composite.png",
        )
        canonical_composite = temporary_root / "canonical-composite.png"
        if (
            sha256_path(canonical_composite)
            != preflight["installed_composite_sha256"]
            or sha256_path(retained_composite)
            != preflight["installed_composite_sha256"]
        ):
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise MewNoteVerticalOrientationCorrectionError(
                "candidate composite is not deterministic"
            )
        old_steps = _history_steps(context, history)
        prompt_path = root / f"tool-step-{len(old_steps) + 1:04d}.txt"
        _regular_file(prompt_path, label="orientation correction prompt")
        previous_hash = history["accepted_final"]["raster"]["sha256"]
        last_inputs = tuple(
            item
            for item in old_steps[-1].inputs
            if item.role != "parent-output"
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
            output_sha256=preflight[
                "installed_composite_sha256"
            ],
            output_path=canonical_composite,
            parent_output_sha256=previous_hash,
        )
        old_bytes = {
            path: path.read_bytes()
            for path in (
                root / "history.json",
                root / "source.json",
                root / "raster.png",
                root / "review.json",
            )
        }
        build_backup: Path | None = None
        if paths.build.exists():
            build_backup = paths.build.with_name(
                f".{paths.build.name}.vertical-orientation-backup"
            )
            if build_backup.exists():
                shutil.rmtree(temporary_root, ignore_errors=True)
                raise MewNoteVerticalOrientationCorrectionError(
                    f"stale correction backup exists: {build_backup}"
                )
            paths.build.replace(build_backup)
        try:
            _atomic_copy(candidate_raster, retained_candidate)
            if sha256_path(retained_candidate) != candidate_sha256:
                raise MewNoteVerticalOrientationCorrectionError(
                    "retained raw candidate hash drift"
                )
            evidence.register_history(
                context,
                COLLECTION_ID,
                BATCH_ID,
                steps=(*old_steps, correction_step),
            )
            current_evidence = evidence.build_vector_batch(
                context, COLLECTION_ID, BATCH_ID
            )
            current_report_path = paths.build / "report.json"
            corrected = _orientation_diagnostics(
                current_report_path,
                source_sha256=sha256_path(root / "source.json"),
                expect_accepted=True,
            )
            unchanged = _unchanged_glyph_evidence(
                build_backup / "report.json"
                if build_backup is not None
                else report_path,
                current_report_path,
            )
            current_report = _object(
                current_report_path,
                label="corrected vector report",
            )
            current_ttf = _report_ttf(
                current_report_path, current_report
            )
            if (
                sha256_path(current_ttf) != preflight["ttf_sha256"]
                or corrected
                != preflight["orientation_diagnostics"]
                or unchanged
                != preflight["unchanged_non_target_glyphs"]
            ):
                raise MewNoteVerticalOrientationCorrectionError(
                    "canonical correction build differs from preflight"
                )
            payload: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "record_type": RECORD_TYPE,
                "family_id": evidence.FAMILY_ID,
                "pipeline_id": evidence.PIPELINE_ID,
                "collection_id": COLLECTION_ID,
                "batch_id": BATCH_ID,
                "family_context": context.evidence_binding(
                    COLLECTION_ID
                ),
                "batch_contract_sha256": (
                    batch["batch_contract_sha256"]
                ),
                "implementation": _implementation_pin(
                    context.project_root
                ),
                "reason": REASON,
                "orientation_contract": {
                    "axis": "horizontal",
                    "diagnostic": (
                        "source-ink-bbox-horizontal-to-vertical-ratio"
                    ),
                    "targets": [
                        {
                            key: target[key]
                            for key in (
                                "cell",
                                "character",
                                "codepoint",
                                "report_source_box",
                                "minimum_horizontal_to_vertical_ratio",
                                "expected_core_component_count",
                            )
                        }
                        for target in TARGETS
                    ],
                },
                "rejected_orientation": rejected,
                "prior_evidence": prior,
                "candidate_generation": {
                    "call_id": call_id,
                    "actual_tool_prompt": _pin(
                        prompt_path,
                        project_root=context.project_root,
                    ),
                    "raw_candidate": _pin(
                        retained_candidate,
                        project_root=context.project_root,
                        retention=(
                            "retained-original-imagegen-output"
                        ),
                    ),
                },
                "composite_installation": composite_contract,
                "correction_generation": {
                    "appended_sequence": len(old_steps) + 1,
                    "parent_output_sha256": previous_hash,
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
                    "build": _build_snapshot(
                        current_report_path,
                        project_root=context.project_root,
                    ),
                    "batch_vector_evidence": current_evidence,
                    "orientation_diagnostics": corrected,
                    "unchanged_non_target_glyphs": unchanged,
                    "candidate_preflight": preflight,
                },
                "required_next_gates": [
                    "independent-raster-vector-technical-review",
                    "collection-release-reapproval",
                ],
                "state": "corrected-unreviewed-unapproved",
            }
            payload["correction_sha256"] = canonical_json_sha256(
                payload
            )
            _atomic_json(record_path, payload)
            result = validate_correction(
                context,
                require_new_review=False,
                require_reapproval=False,
            )
        except Exception:
            record_path.unlink(missing_ok=True)
            retained_candidate.unlink(missing_ok=True)
            if paths.build.exists():
                shutil.rmtree(paths.build)
            if build_backup is not None and build_backup.exists():
                build_backup.replace(paths.build)
            for path, data in old_bytes.items():
                _atomic_write(path, data)
            shutil.rmtree(temporary_root, ignore_errors=True)
            lock_path.unlink(missing_ok=True)
            raise
        else:
            if build_backup is not None:
                shutil.rmtree(build_backup)
            shutil.rmtree(temporary_root, ignore_errors=True)
            return result


def _validate_pin_schema(
    pin: Any,
    *,
    label: str,
    retention: str | None,
) -> Mapping[str, Any]:
    expected = {"path", "sha256"}
    if retention is not None:
        expected.add("retention")
    pin = _exact_keys(pin, expected, label=label)
    _sha(pin["sha256"], label=f"{label} hash")
    if (
        not isinstance(pin["path"], str)
        or not pin["path"]
        or Path(pin["path"]).is_absolute()
        or ".." in Path(pin["path"]).parts
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            f"{label} path is not canonical"
        )
    if retention is not None and pin["retention"] != retention:
        raise MewNoteVerticalOrientationCorrectionError(
            f"{label} retention changed"
        )
    return pin


def _validate_orientation_records(
    value: Any,
    *,
    expected_decision: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or len(value) != len(TARGETS):
        raise MewNoteVerticalOrientationCorrectionError(
            "orientation diagnostic inventory changed"
        )
    expected_keys = {
        "cell",
        "character",
        "codepoint",
        "source_ink_bbox_normalized",
        "ink_width",
        "ink_height",
        "horizontal_to_vertical_ratio",
        "minimum_horizontal_to_vertical_ratio",
        "source_core_component_count",
        "contour_count",
        "micro_edge_count",
        "acute_micro_turn_count",
        "decision",
    }
    for target, item in zip(TARGETS, value, strict=True):
        item = _exact_keys(
            item,
            expected_keys,
            label=f"{target['codepoint']} orientation diagnostic",
        )
        if (
            item["cell"] != target["cell"]
            or item["character"] != target["character"]
            or item["codepoint"] != target["codepoint"]
            or item["minimum_horizontal_to_vertical_ratio"]
            != target["minimum_horizontal_to_vertical_ratio"]
            or item["source_core_component_count"]
            != target["expected_core_component_count"]
            or item["contour_count"]
            != target["expected_core_component_count"]
            or item["micro_edge_count"] != 0
            or item["acute_micro_turn_count"] != 0
            or item["decision"] != expected_decision
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: orientation diagnostic drift"
            )
        ratio = item["horizontal_to_vertical_ratio"]
        minimum = target["minimum_horizontal_to_vertical_ratio"]
        if (
            not isinstance(ratio, (int, float))
            or (ratio >= minimum)
            is not (expected_decision == "ACCEPT")
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: orientation decision is unproven"
            )
    return value


def _validate_composite(
    *,
    context: evidence.FamilyContext,
    value: Any,
    prior_raster_sha256: str,
    raw_candidate: Mapping[str, Any],
    installed_raster: Mapping[str, Any],
) -> None:
    value = _exact_keys(
        value,
        {
            "algorithm",
            "pixel_hash_algorithm",
            "canvas",
            "regions",
            "preserved_outside_regions_sha256",
            "installed_composite_sha256",
        },
        label="composite installation",
    )
    canvas = _exact_keys(
        value["canvas"],
        {"width", "height", "mode"},
        label="composite canvas",
    )
    if (
        value["algorithm"] != COMPOSITE_ALGORITHM
        or value["pixel_hash_algorithm"] != PIXEL_HASH_ALGORITHM
        or canvas != {"width": 1254, "height": 1254, "mode": "RGB"}
        or value["installed_composite_sha256"]
        != installed_raster["sha256"]
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "composite contract drift"
        )
    _sha(
        value["preserved_outside_regions_sha256"],
        label="preserved outside-region hash",
    )
    regions = value["regions"]
    if not isinstance(regions, list) or len(regions) != len(TARGETS):
        raise MewNoteVerticalOrientationCorrectionError(
            "composite region inventory changed"
        )
    candidate_image = _load_rgb_png(
        context.project_root / raw_candidate["path"],
        label="retained raw candidate",
    )
    installed_image = _load_rgb_png(
        context.project_root / installed_raster["path"],
        label="installed composite",
    )
    boxes = [target["replacement_box"] for target in TARGETS]
    if (
        _framed_pixel_sha256(
            installed_image,
            regions=boxes,
            include_regions=False,
        )
        != value["preserved_outside_regions_sha256"]
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "installed composite outside-region pixels drifted"
        )
    if prior_raster_sha256 == installed_raster["sha256"]:
        raise MewNoteVerticalOrientationCorrectionError(
            "orientation correction did not change the raster"
        )
    expected_keys = {
        "cell",
        "character",
        "codepoint",
        "report_source_box",
        "replacement_box",
        "minimum_horizontal_to_vertical_ratio",
        "expected_core_component_count",
        "superseded_region_sha256",
        "candidate_region_sha256",
    }
    for target, region in zip(TARGETS, regions, strict=True):
        region = _exact_keys(
            region,
            expected_keys,
            label=f"{target['codepoint']} composite region",
        )
        if any(
            region[key] != target[key]
            for key in target
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: composite target drift"
            )
        _sha(
            region["superseded_region_sha256"],
            label=f"{target['codepoint']} superseded region hash",
        )
        _sha(
            region["candidate_region_sha256"],
            label=f"{target['codepoint']} candidate region hash",
        )
        if (
            region["superseded_region_sha256"]
            == region["candidate_region_sha256"]
            or _region_sha256(
                candidate_image, target["replacement_box"]
            )
            != region["candidate_region_sha256"]
            or _region_sha256(
                installed_image, target["replacement_box"]
            )
            != region["candidate_region_sha256"]
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"{target['codepoint']}: installed region provenance drift"
            )


def _validate_reapproval(
    context: evidence.FamilyContext,
    *,
    prior_approval_sha256: str,
    review_path: Path,
) -> None:
    approval_path = _regular_file(
        context.project_root / APPROVAL_PATH,
        label="replacement collection release approval",
    )
    if sha256_path(approval_path) == prior_approval_sha256:
        raise MewNoteVerticalOrientationCorrectionError(
            "collection release reapproval is still missing"
        )
    approval = _object(
        approval_path, label="replacement collection release approval"
    )
    reviewed = approval.get("reviewed_batches")
    matching = [
        item
        for item in reviewed
        if isinstance(item, dict)
        and item.get("collection_id") == COLLECTION_ID
        and item.get("batch_id") == BATCH_ID
    ] if isinstance(reviewed, list) else []
    if (
        approval.get("record_type")
        != "mew-note-tc-collection-release-approval"
        or approval.get("decision") != "APPROVED"
        or len(matching) != 1
        or matching[0].get("review")
        != _pin(
            review_path,
            project_root=context.project_root,
        )
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "replacement release approval does not admit the new review"
        )


def validate_correction(
    context: evidence.FamilyContext,
    *,
    require_new_review: bool,
    require_reapproval: bool,
) -> dict[str, Any]:
    """Validate the immutable correction and optional downstream gates."""

    path = correction_path(context)
    payload = _object(
        path, label="vertical-orientation correction"
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
        "reason",
        "orientation_contract",
        "rejected_orientation",
        "prior_evidence",
        "candidate_generation",
        "composite_installation",
        "correction_generation",
        "required_next_gates",
        "state",
        "correction_sha256",
    }
    payload = _exact_keys(
        payload,
        expected_keys,
        label="vertical-orientation correction",
    )
    batch = evidence.frozen_batch(
        context, COLLECTION_ID, BATCH_ID
    )
    if (
        payload["schema_version"] != SCHEMA_VERSION
        or payload["record_type"] != RECORD_TYPE
        or payload["family_id"] != evidence.FAMILY_ID
        or payload["pipeline_id"] != evidence.PIPELINE_ID
        or payload["collection_id"] != COLLECTION_ID
        or payload["batch_id"] != BATCH_ID
        or payload["family_context"]
        != context.evidence_binding(COLLECTION_ID)
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
        raise MewNoteVerticalOrientationCorrectionError(
            "vertical-orientation correction binding mismatch"
        )
    expected_digest = canonical_json_sha256(
        {
            key: value
            for key, value in payload.items()
            if key != "correction_sha256"
        }
    )
    if payload["correction_sha256"] != expected_digest:
        raise MewNoteVerticalOrientationCorrectionError(
            "vertical-orientation correction canonical hash mismatch"
        )
    contract = _exact_keys(
        payload["orientation_contract"],
        {"axis", "diagnostic", "targets"},
        label="orientation contract",
    )
    expected_targets = [
        {
            key: target[key]
            for key in (
                "cell",
                "character",
                "codepoint",
                "report_source_box",
                "minimum_horizontal_to_vertical_ratio",
                "expected_core_component_count",
            )
        }
        for target in TARGETS
    ]
    if contract != {
        "axis": "horizontal",
        "diagnostic": (
            "source-ink-bbox-horizontal-to-vertical-ratio"
        ),
        "targets": expected_targets,
    }:
        raise MewNoteVerticalOrientationCorrectionError(
            "orientation contract drift"
        )
    _validate_orientation_records(
        payload["rejected_orientation"],
        expected_decision="REJECT",
    )
    prior = _exact_keys(
        payload["prior_evidence"],
        {
            "history",
            "source",
            "raster",
            "review",
            "release_approval",
            "build",
        },
        label="prior evidence",
    )
    expected_retentions = {
        "history": "hash-only-superseded",
        "source": "hash-only-superseded",
        "raster": "hash-only-superseded",
        "review": "hash-only-superseded",
        "release_approval": (
            "hash-only-superseded-after-reapproval"
        ),
    }
    for label, retention in expected_retentions.items():
        _validate_pin_schema(
            prior[label],
            label=f"prior {label}",
            retention=retention,
        )
    paths = context.batch_paths(COLLECTION_ID, BATCH_ID)
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
    }
    if any(
        prior[label]["path"] != expected
        for label, expected in expected_prior_paths.items()
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "prior evidence canonical path drift"
        )
    prior_build = _exact_keys(
        prior["build"],
        {
            "report",
            "ttf",
            "black_on_white",
            "white_on_black",
            "segmented_source",
        },
        label="prior build evidence",
    )
    for label, pin in prior_build.items():
        _validate_pin_schema(
            pin,
            label=f"prior build {label}",
            retention="hash-only-derived-superseded",
        )
    candidate = _exact_keys(
        payload["candidate_generation"],
        {"call_id", "actual_tool_prompt", "raw_candidate"},
        label="candidate generation",
    )
    if evidence.CALL_ID_PATTERN.fullmatch(candidate["call_id"]) is None:
        raise MewNoteVerticalOrientationCorrectionError(
            "candidate call ID drift"
        )
    prompt_pin = _validate_pin_schema(
        candidate["actual_tool_prompt"],
        label="candidate prompt",
        retention=None,
    )
    raw_pin = _validate_pin_schema(
        candidate["raw_candidate"],
        label="raw candidate",
        retention="retained-original-imagegen-output",
    )
    expected_prompt = paths.source / (
        f"tool-step-"
        f"{len(evidence.validate_history(context, COLLECTION_ID, BATCH_ID)['steps']):04d}"
        ".txt"
    )
    if (
        prompt_pin
        != _pin(
            expected_prompt,
            project_root=context.project_root,
        )
        or raw_pin
        != _pin(
            raw_candidate_path(context),
            project_root=context.project_root,
            retention="retained-original-imagegen-output",
        )
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "candidate prompt or raster provenance drift"
        )
    source = evidence.validate_source(
        context, COLLECTION_ID, BATCH_ID
    )
    history = evidence.validate_history(
        context, COLLECTION_ID, BATCH_ID
    )
    generated = _exact_keys(
        payload["correction_generation"],
        {
            "appended_sequence",
            "parent_output_sha256",
            "history",
            "source",
            "raster",
            "build",
            "batch_vector_evidence",
            "orientation_diagnostics",
            "unchanged_non_target_glyphs",
            "candidate_preflight",
        },
        label="corrected generation",
    )
    for label, actual_path in (
        ("history", paths.source / "history.json"),
        ("source", paths.source / "source.json"),
        ("raster", paths.source / "raster.png"),
    ):
        if generated[label] != _pin(
            actual_path,
            project_root=context.project_root,
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                f"corrected {label} evidence drift"
            )
    if (
        generated["appended_sequence"] != len(history["steps"])
        or len(history["steps"]) < 2
        or generated["parent_output_sha256"]
        != history["steps"][-2]["output"]["sha256"]
        or candidate["call_id"]
        != history["accepted_final"]["call_id"]
        or generated["raster"]["sha256"]
        != source["raster_sha256"]
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "corrected history chain drift"
        )
    current_evidence = evidence.build_vector_batch(
        context, COLLECTION_ID, BATCH_ID
    )
    if generated["batch_vector_evidence"] != current_evidence:
        raise MewNoteVerticalOrientationCorrectionError(
            "corrected batch vector evidence drift"
        )
    current_build = _build_snapshot(
        paths.build / "report.json",
        project_root=context.project_root,
    )
    if generated["build"] != current_build:
        raise MewNoteVerticalOrientationCorrectionError(
            "corrected build inventory drift"
        )
    current_diagnostics = _orientation_diagnostics(
        paths.build / "report.json",
        source_sha256=sha256_path(paths.source / "source.json"),
        expect_accepted=True,
    )
    _validate_orientation_records(
        generated["orientation_diagnostics"],
        expected_decision="ACCEPT",
    )
    if generated["orientation_diagnostics"] != current_diagnostics:
        raise MewNoteVerticalOrientationCorrectionError(
            "corrected orientation evidence drift"
        )
    unchanged = generated["unchanged_non_target_glyphs"]
    if (
        not isinstance(unchanged, list)
        or len(unchanged) != 14
        or any(
            not isinstance(item, dict)
            or set(item)
            != {
                "character",
                "codepoint",
                "source_png_sha256",
                "svg_sha256",
                "proof_png_sha256",
            }
            for item in unchanged
        )
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "non-target vector evidence inventory drift"
        )
    preflight = _exact_keys(
        generated["candidate_preflight"],
        {
            "raw_candidate_sha256",
            "installed_composite_sha256",
            "ttf_sha256",
            "orientation_diagnostics",
            "unchanged_non_target_glyphs",
            "micro_edge_count",
            "acute_micro_turn_count",
        },
        label="candidate preflight",
    )
    if (
        preflight["raw_candidate_sha256"] != raw_pin["sha256"]
        or preflight["installed_composite_sha256"]
        != generated["raster"]["sha256"]
        or preflight["ttf_sha256"]
        != current_build["ttf"]["sha256"]
        or preflight["orientation_diagnostics"]
        != current_diagnostics
        or preflight["unchanged_non_target_glyphs"] != unchanged
        or preflight["micro_edge_count"] != 0
        or preflight["acute_micro_turn_count"] != 0
    ):
        raise MewNoteVerticalOrientationCorrectionError(
            "candidate preflight evidence drift"
        )
    _validate_composite(
        context=context,
        value=payload["composite_installation"],
        prior_raster_sha256=prior["raster"]["sha256"],
        raw_candidate=raw_pin,
        installed_raster=generated["raster"],
    )
    review_path = paths.source / "review.json"
    if require_new_review or require_reapproval:
        review_path = _regular_file(
            review_path,
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
            or review.get("evidence") != current_evidence
        ):
            raise MewNoteVerticalOrientationCorrectionError(
                "replacement technical review is missing or stale"
            )
    if require_reapproval:
        _validate_reapproval(
            context,
            prior_approval_sha256=(
                prior["release_approval"]["sha256"]
            ),
            review_path=review_path,
        )
    return dict(payload)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--candidate-raster", type=Path, required=True)
    apply_parser.add_argument("--candidate-sha256", required=True)
    apply_parser.add_argument("--call-id", required=True)
    apply_parser.add_argument("--confirmation", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--require-new-review", action="store_true")
    validate_parser.add_argument("--require-reapproval", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    context = evidence.load_context(args.project_root)
    if args.command == "apply":
        result = apply_correction(
            context,
            candidate_raster=args.candidate_raster,
            candidate_sha256=args.candidate_sha256,
            call_id=args.call_id,
            confirmation=args.confirmation,
        )
    else:
        result = validate_correction(
            context,
            require_new_review=args.require_new_review,
            require_reapproval=args.require_reapproval,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
