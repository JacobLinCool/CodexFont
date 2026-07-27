#!/usr/bin/env python3
"""Validate and approve the six image-generated vertical batches.

An approval is not inferred from a successful build.  The reviewer must first
record that every glyph was inspected at all five proof sizes in both
polarities.  Authorization then pins the source descriptor, report, proof
images, preview fonts, and per-glyph geometry to immutable SHA-256 values.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Mapping, Sequence

from fontTools.ttLib import TTFont
from PIL import Image, ImageChops

from scripts import imagegen_vertical_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
BUILD_ROOT = ROOT / "build/imagegen"
REVIEW_ROOT = IMAGEGEN_ROOT / "vector-reviews"
APPROVAL_ROOT = IMAGEGEN_ROOT / "approvals"

BATCH_PATTERN = re.compile(r"vertical-[0-9]{4}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
REVIEW_CONFIRMATION = (
    "I_REVIEWED_EVERY_VERTICAL_ALTERNATE_AT_"
    "12_16_20_32_56_PX_IN_BOTH_POLARITIES"
)
APPROVAL_CONFIRMATION = (
    "I_AUTHORIZE_THIS_HASH_PINNED_VERTICAL_BATCH_FOR_THE_RELEASE_FONT"
)
REVIEW_TYPE = "imagegen-vertical-vector-review-v1"
APPROVAL_TYPE = "imagegen-vertical-release-approval-v1"


class VerticalApprovalError(RuntimeError):
    """A build, review, or approval failed closed."""


@dataclass(frozen=True)
class ValidatedVerticalBuild:
    batch_id: str
    descriptor_path: Path
    descriptor_sha256: str
    report_path: Path
    report_sha256: str
    report: Mapping[str, Any]
    small_proof_sha256: Mapping[str, str]
    ttf_path: Path
    ttf_sha256: str
    otf_path: Path
    otf_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerticalApprovalError(f"{path}: cannot read JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise VerticalApprovalError(f"{path}: expected a JSON object")
    return value


def _write_json_once(path: Path, value: Mapping[str, Any]) -> Path:
    if path.exists():
        raise VerticalApprovalError(f"refusing to overwrite canonical record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def _canonical_batch_id(value: str) -> str:
    if BATCH_PATTERN.fullmatch(value) is None:
        raise VerticalApprovalError(f"invalid vertical batch ID: {value!r}")
    number = int(value.removeprefix("vertical-"))
    if not 1 <= number <= 6 or value != f"vertical-{number:04d}":
        raise VerticalApprovalError(f"vertical batch is outside 0001..0006: {value}")
    return value


def _validate_timestamp(value: Any, *, where: str) -> None:
    if not isinstance(value, str) or not value:
        raise VerticalApprovalError(f"{where} must be a nonempty ISO-8601 string")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerticalApprovalError(f"{where} must be ISO-8601") from exc


def _validate_trimmed_text(value: Any, *, where: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise VerticalApprovalError(
            f"{where} must be nonempty text without surrounding whitespace"
        )


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise VerticalApprovalError(f"{path}: path escapes project root") from exc


def _validate_artifact_inventory(
    directory: Path,
    report: Mapping[str, Any],
) -> Mapping[str, str]:
    inventory = report.get("artifact_sha256")
    if not isinstance(inventory, dict) or not inventory:
        raise VerticalApprovalError("report artifact inventory is missing")
    actual: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise VerticalApprovalError(f"symlink artifact is forbidden: {path}")
        if path.is_file() and path.name != "report.json":
            actual[path.relative_to(directory).as_posix()] = _sha256(path)
    if actual != inventory:
        raise VerticalApprovalError(
            f"{directory}: report artifact inventory/hash mismatch"
        )
    return actual


def _artifact_path(
    directory: Path,
    raw: Any,
    *,
    expected: str,
    inventory: Mapping[str, str],
    where: str,
) -> tuple[Path, str]:
    if raw != expected:
        raise VerticalApprovalError(
            f"{where}: artifact path must be exactly {expected!r}"
        )
    relative = PurePosixPath(expected)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise VerticalApprovalError(f"{where}: artifact path is not canonical")
    candidate = directory.joinpath(*relative.parts)
    if candidate.is_symlink():
        raise VerticalApprovalError(f"{where}: symlink artifact is forbidden")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(directory.resolve())
    except ValueError as exc:
        raise VerticalApprovalError(
            f"{where}: artifact path escapes vertical build"
        ) from exc
    if not resolved.is_file() or expected not in inventory:
        raise VerticalApprovalError(
            f"{where}: artifact is missing from the vertical build inventory"
        )
    return resolved, expected


def _validate_png(path: Path, *, where: str) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (OSError, ValueError) as exc:
        raise VerticalApprovalError(f"{where}: invalid PNG: {exc}") from exc


def _assert_same_png_pixels(
    actual_path: Path,
    expected_path: Path,
    *,
    where: str,
) -> None:
    try:
        with Image.open(actual_path) as actual_source:
            actual_source.load()
            actual = actual_source.copy()
        with Image.open(expected_path) as expected_source:
            expected_source.load()
            expected = expected_source.copy()
    except (OSError, ValueError) as exc:
        raise VerticalApprovalError(f"{where}: cannot decode proof PNG: {exc}") from exc
    if actual.mode != expected.mode or actual.size != expected.size:
        raise VerticalApprovalError(
            f"{where}: proof mode/size differs from a fresh render"
        )
    if ImageChops.difference(actual, expected).getbbox() is not None:
        raise VerticalApprovalError(
            f"{where}: proof pixels differ from a fresh render"
        )


def _validate_fresh_source_and_edge_proofs(
    descriptor: pipeline.VerticalDescriptor,
    *,
    ttf_path: Path,
    source_proof_path: Path,
    edge_proof_path: Path,
) -> None:
    try:
        with Image.open(descriptor.raster_path) as source:
            source.load()
            detection = pipeline.han_pipeline.detect_grid(source)
            cells = pipeline.nonhan.segment_cells(
                source,
                detection,
                descriptor.cell_slots,
            )
    except (
        OSError,
        ValueError,
        pipeline.han_pipeline.ImagegenPipelineError,
        pipeline.nonhan.NonHanPipelineError,
    ) as exc:
        raise VerticalApprovalError(
            f"{descriptor.raster_path}: cannot reconstruct proof cells: {exc}"
        ) from exc

    with tempfile.TemporaryDirectory(prefix=".vertical-proof-validation-") as raw:
        temporary = Path(raw)
        fresh_source = pipeline.nonhan._write_source_proof(
            cells,
            output=temporary / "segmented-source.png",
        )
        fresh_edge = pipeline.nonhan._write_edge_proof(
            cells,
            font_path=ttf_path,
            output=temporary / "edge-connect.png",
        )
        _assert_same_png_pixels(
            source_proof_path,
            fresh_source,
            where=f"{descriptor.base_batch_id}: segmented-source proof",
        )
        _assert_same_png_pixels(
            edge_proof_path,
            fresh_edge,
            where=f"{descriptor.base_batch_id}: edge-connect proof",
        )


def _validate_preview_font(
    path: Path,
    *,
    expected_cmap: Mapping[int, str],
    expected_order: Sequence[str],
    glyph_records: Sequence[Mapping[str, Any]],
) -> None:
    try:
        font = TTFont(
            path,
            lazy=False,
            checkChecksums=2,
            recalcTimestamp=False,
        )
    except Exception as exc:
        raise VerticalApprovalError(f"{path}: cannot reopen font: {exc}") from exc
    try:
        if font.getBestCmap() != dict(expected_cmap):
            raise VerticalApprovalError(f"{path}: preview cmap mismatch")
        if font.getGlyphOrder() != list(expected_order):
            raise VerticalApprovalError(f"{path}: glyph order mismatch")
        if "glyf" not in font or "CFF " in font or "CFF2" in font:
            raise VerticalApprovalError(f"{path}: expected quadratic glyf outlines")
        if "vhea" not in font or "vmtx" not in font:
            raise VerticalApprovalError(f"{path}: vertical metrics are missing")
        for glyph_name, record in zip(
            expected_order[1:],
            glyph_records,
            strict=True,
        ):
            glyph = font["glyf"][glyph_name]
            if glyph.isComposite() or glyph.numberOfContours <= 0:
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} must be a nonempty simple outline"
                )
            glyph.recalcBounds(font["glyf"])
            actual_bounds = [
                int(glyph.xMin),
                int(glyph.yMin),
                int(glyph.xMax),
                int(glyph.yMax),
            ]
            if record.get("final_bounds") != actual_bounds:
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} actual bounds differ from report"
                )
            metrics = record.get("metrics")
            if not isinstance(metrics, dict):
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} report metrics are missing"
                )
            if font["hmtx"].metrics[glyph_name] != (
                metrics.get("horizontal_advance"),
                metrics.get("left_side_bearing"),
            ):
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} actual horizontal metrics differ"
                )
            if font["vmtx"].metrics[glyph_name] != (
                metrics.get("vertical_advance"),
                metrics.get("top_side_bearing"),
            ):
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} actual vertical metrics differ"
                )
            try:
                (
                    contour_count,
                    point_count,
                    outer_count,
                    counter_count,
                    minimum_edge,
                    micro_edges,
                    acute_turns,
                ) = pipeline.han_pipeline._geometry_quality(glyph)
            except pipeline.han_pipeline.ImagegenPipelineError as exc:
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} actual geometry is invalid: {exc}"
                ) from exc
            actual_geometry = {
                "contour_count": contour_count,
                "point_count": point_count,
                "outer_contour_count": outer_count,
                "counter_count": counter_count,
                "minimum_control_edge": round(minimum_edge, 6),
                "micro_edge_count": micro_edges,
                "acute_micro_turn_count": acute_turns,
            }
            for key, value in actual_geometry.items():
                if record.get(key) != value:
                    raise VerticalApprovalError(
                        f"{path}: {glyph_name} actual {key} differs from report"
                    )
            if (
                record.get("base_profile_id")
                in {"box-drawing", "block-element"}
                and outer_count != record.get("source_component_count")
            ):
                raise VerticalApprovalError(
                    f"{path}: {glyph_name} actual edge topology differs "
                    "from source components"
                )
    finally:
        font.close()


def validate_build(
    batch_id: str,
    *,
    project_root: Path = ROOT,
) -> ValidatedVerticalBuild:
    from scripts.imagegen_derived_artifacts import (
        DerivedArtifactError,
        ensure_materialized,
    )

    batch_id = _canonical_batch_id(batch_id)
    project_root = project_root.resolve()
    imagegen_root = project_root / "sources/imagegen"
    descriptor_path = imagegen_root / f"batches/{batch_id}.source.json"
    try:
        descriptor = pipeline.load_source_descriptor(
            descriptor_path,
            project_root=project_root,
        )
    except pipeline.VerticalPipelineError as exc:
        raise VerticalApprovalError(str(exc)) from exc
    build_directory = project_root / f"build/imagegen/imagegen-{batch_id}"
    report_path = build_directory / "report.json"
    try:
        ensure_materialized(report_path, project_root=project_root)
    except DerivedArtifactError as exc:
        raise VerticalApprovalError(f"{report_path}: {exc}") from exc
    report = _read_object(report_path)
    if report.get("pipeline") != pipeline.PIPELINE_ID:
        raise VerticalApprovalError(f"{report_path}: pipeline identity changed")
    if report.get("approval_state") != "unreviewed":
        raise VerticalApprovalError(f"{report_path}: report must remain unreviewed")
    if report.get("batch_id") != f"imagegen-{batch_id}":
        raise VerticalApprovalError(f"{report_path}: batch identity mismatch")
    if (
        report.get("source_descriptor")
        != _relative(descriptor_path, project_root)
        or report.get("source_descriptor_sha256")
        != descriptor.source_sha256
        or report.get("source_raster_sha256")
        != descriptor.raster_sha256
        or report.get("source_repertoire_sha256")
        != descriptor.repertoire_sha256
        or report.get("source_prompt_sha256")
        != descriptor.prompt_sha256
        or report.get("source_copybook_sha256")
        != descriptor.copybook_sha256
        or report.get("source_style_reference_sha256")
        != descriptor.style_reference_sha256
    ):
        raise VerticalApprovalError(f"{report_path}: source hash chain mismatch")
    if report.get("source_review") != {
        "identity": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }:
        raise VerticalApprovalError(f"{report_path}: source review contract changed")
    artifact_hashes = _validate_artifact_inventory(build_directory, report)

    expected_names = [
        str(alternate["glyph_name"])
        for alternate in descriptor.alternates
    ]
    expected_codepoints = [glyph.codepoint for glyph in descriptor.glyphs]
    expected_labels = [f"U+{value:04X}" for value in expected_codepoints]
    if (
        report.get("base_codepoints") != expected_labels
        or report.get("unencoded_glyph_names") != expected_names
    ):
        raise VerticalApprovalError(f"{report_path}: vertical sequence mismatch")
    glyph_records = report.get("glyphs")
    if not isinstance(glyph_records, list) or len(glyph_records) != len(expected_names):
        raise VerticalApprovalError(f"{report_path}: glyph report cardinality mismatch")
    minimum_by_size = {
        str(size): max(
            pipeline.nonhan.MINIMUM_PROOF_COVERAGE_PIXELS,
            size // pipeline.VERTICAL_PROOF_COVERAGE_DIVISOR,
        )
        for size in pipeline.nonhan.SMALL_SIZE_PIXELS
    }
    for index, (record, alternate, expected_name, expected_label) in enumerate(
        zip(
            glyph_records,
            descriptor.alternates,
            expected_names,
            expected_labels,
            strict=True,
        ),
        start=1,
    ):
        if not isinstance(record, dict):
            raise VerticalApprovalError(
                f"{report_path}: glyph {index} record is not an object"
            )
        if (
            record.get("codepoint") != expected_label
            or record.get("glyph_name") != expected_name
            or record.get("unencoded_glyph_name") != expected_name
            or record.get("vertical_orientation")
            != alternate["vertical_orientation"]
            or record.get("tailoring") != alternate["tailoring"]
            or record.get("base_profile_id") != alternate["base_profile_id"]
            or record.get("base_metrics") != alternate["base_metrics"]
        ):
            raise VerticalApprovalError(
                f"{report_path}: glyph {index} identity/metric provenance mismatch"
            )
        stem = f"u{expected_codepoints[index - 1]:04x}-vert"
        for field, expected_path in (
            ("source_png", f"png/{stem}-source.png"),
            ("svg", f"svg/{stem}.svg"),
        ):
            artifact_path, relative = _artifact_path(
                build_directory,
                record.get(field),
                expected=expected_path,
                inventory=artifact_hashes,
                where=f"{report_path}: {expected_name} {field}",
            )
            digest = record.get(f"{field}_sha256")
            if (
                not isinstance(digest, str)
                or SHA256_PATTERN.fullmatch(digest) is None
                or artifact_hashes.get(relative) != digest
                or _sha256(artifact_path) != digest
            ):
                raise VerticalApprovalError(
                    f"{report_path}: {expected_name} {field} hash mismatch"
                )
            if field == "source_png":
                _validate_png(
                    artifact_path,
                    where=f"{report_path}: {expected_name} source PNG",
                )
        glyph_report_path, glyph_report_relative = _artifact_path(
            build_directory,
            f"glyph-report/{stem}.json",
            expected=f"glyph-report/{stem}.json",
            inventory=artifact_hashes,
            where=f"{report_path}: {expected_name} per-glyph report",
        )
        if (
            artifact_hashes.get(glyph_report_relative)
            != _sha256(glyph_report_path)
            or _read_object(glyph_report_path) != record
        ):
            raise VerticalApprovalError(
                f"{report_path}: {expected_name} per-glyph report differs"
            )
        for key in (
            "micro_edge_count",
            "acute_micro_turn_count",
            "micro_thorn_points_removed",
        ):
            if record.get(key) != 0:
                raise VerticalApprovalError(
                    f"{report_path}: {expected_name} has nonzero {key}"
                )
        if record.get("maximum_micro_thorn_displacement") != 0.0:
            raise VerticalApprovalError(
                f"{report_path}: {expected_name} has thorn displacement"
            )
        if (
            record.get("base_profile_id")
            in {"box-drawing", "block-element"}
            and record.get("source_component_count")
            != record.get("outer_contour_count")
        ):
            raise VerticalApprovalError(
                f"{report_path}: {expected_name} edge topology differs "
                "between source and vector report"
            )
        coverage = record.get("coverage_pixels")
        if not isinstance(coverage, dict) or set(coverage) != set(minimum_by_size):
            raise VerticalApprovalError(
                f"{report_path}: {expected_name} coverage keys mismatch"
            )
        for size, minimum in minimum_by_size.items():
            value = coverage[size]
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise VerticalApprovalError(
                    f"{report_path}: {expected_name} insufficient {size}px coverage"
                )

    proofs = report.get("proofs")
    if not isinstance(proofs, list) or len(proofs) != 12:
        raise VerticalApprovalError(f"{report_path}: proofs are missing")
    small_proofs: dict[str, str] = {}
    expected_pairs = {
        (size, polarity)
        for size in pipeline.nonhan.SMALL_SIZE_PIXELS
        for polarity in ("black-on-white", "white-on-black")
    }
    actual_pairs: set[tuple[int, str]] = set()
    singleton_paths: dict[str, Path] = {}
    for proof in proofs:
        if not isinstance(proof, dict):
            raise VerticalApprovalError(f"{report_path}: malformed proof record")
        kind = proof.get("kind")
        if kind in {"segmented-source", "edge-connect"}:
            if set(proof) != {"kind", "path", "sha256"} or kind in singleton_paths:
                raise VerticalApprovalError(
                    f"{report_path}: malformed/duplicate {kind} proof"
                )
            expected_path = (
                "proof/segmented-source.png"
                if kind == "segmented-source"
                else "proof/edge-connect.png"
            )
            proof_path, relative = _artifact_path(
                build_directory,
                proof.get("path"),
                expected=expected_path,
                inventory=artifact_hashes,
                where=f"{report_path}: {kind} proof",
            )
            digest = proof.get("sha256")
            if (
                not isinstance(digest, str)
                or SHA256_PATTERN.fullmatch(digest) is None
                or artifact_hashes.get(relative) != digest
                or _sha256(proof_path) != digest
            ):
                raise VerticalApprovalError(
                    f"{report_path}: {kind} proof hash mismatch"
                )
            _validate_png(proof_path, where=f"{report_path}: {kind} proof")
            singleton_paths[kind] = proof_path
            continue
        if kind != "small-size" or set(proof) != {
            "kind",
            "size_px",
            "polarity",
            "path",
            "sha256",
            "cell_size_px",
        }:
            raise VerticalApprovalError(
                f"{report_path}: malformed small-size proof record"
            )
        size = proof.get("size_px")
        polarity = proof.get("polarity")
        path_value = proof.get("path")
        digest = proof.get("sha256")
        pair = (size, polarity)
        if pair not in expected_pairs or pair in actual_pairs:
            raise VerticalApprovalError(f"{report_path}: invalid/duplicate proof {pair}")
        if (
            not isinstance(path_value, str)
            or not isinstance(digest, str)
            or SHA256_PATTERN.fullmatch(digest) is None
            or proof.get("cell_size_px") != max(36, size + 24)
        ):
            raise VerticalApprovalError(f"{report_path}: malformed proof record")
        expected_path = f"proof/{polarity}-{size}px.png"
        proof_path, relative = _artifact_path(
            build_directory,
            path_value,
            expected=expected_path,
            inventory=artifact_hashes,
            where=f"{report_path}: {polarity}-{size}px proof",
        )
        if (
            artifact_hashes.get(relative) != digest
            or _sha256(proof_path) != digest
        ):
            raise VerticalApprovalError(f"{report_path}: proof hash mismatch")
        _validate_png(
            proof_path,
            where=f"{report_path}: {polarity}-{size}px proof",
        )
        actual_pairs.add(pair)
        small_proofs[f"{polarity}-{size}px"] = digest
    if actual_pairs != expected_pairs:
        raise VerticalApprovalError(f"{report_path}: small-size proof set incomplete")
    if set(singleton_paths) != {"segmented-source", "edge-connect"}:
        raise VerticalApprovalError(
            f"{report_path}: source/edge proof set incomplete"
        )

    font_record = report.get("font")
    if not isinstance(font_record, dict) or set(font_record) != {
        "ttf",
        "ttf_sha256",
        "otf",
        "otf_sha256",
        "temporary_preview_cmap_count",
        "glyph_count",
        "release_alternates_are_unencoded",
    }:
        raise VerticalApprovalError(f"{report_path}: font record missing")
    if (
        font_record.get("temporary_preview_cmap_count") != len(expected_names)
        or font_record.get("glyph_count") != len(expected_names) + 1
        or font_record.get("release_alternates_are_unencoded") is not True
    ):
        raise VerticalApprovalError(f"{report_path}: font contract changed")
    number = batch_id.removeprefix("vertical-")
    ttf_path, ttf_relative = _artifact_path(
        build_directory,
        font_record.get("ttf"),
        expected=f"font/ClearHandTC-Vertical{number}-Unreviewed.ttf",
        inventory=artifact_hashes,
        where=f"{report_path}: preview TTF",
    )
    otf_path, otf_relative = _artifact_path(
        build_directory,
        font_record.get("otf"),
        expected=f"font/ClearHandTC-Vertical{number}-Unreviewed.otf",
        inventory=artifact_hashes,
        where=f"{report_path}: preview OTF",
    )
    ttf_hash = font_record.get("ttf_sha256")
    otf_hash = font_record.get("otf_sha256")
    if (
        not isinstance(ttf_hash, str)
        or not isinstance(otf_hash, str)
        or SHA256_PATTERN.fullmatch(ttf_hash) is None
        or SHA256_PATTERN.fullmatch(otf_hash) is None
        or artifact_hashes.get(ttf_relative) != ttf_hash
        or artifact_hashes.get(otf_relative) != otf_hash
        or _sha256(ttf_path) != ttf_hash
        or _sha256(otf_path) != otf_hash
    ):
        raise VerticalApprovalError(f"{report_path}: preview font hash mismatch")
    expected_cmap = dict(zip(expected_codepoints, expected_names, strict=True))
    expected_order = [".notdef", *expected_names]
    _validate_preview_font(
        ttf_path,
        expected_cmap=expected_cmap,
        expected_order=expected_order,
        glyph_records=glyph_records,
    )
    _validate_preview_font(
        otf_path,
        expected_cmap=expected_cmap,
        expected_order=expected_order,
        glyph_records=glyph_records,
    )
    _validate_fresh_source_and_edge_proofs(
        descriptor,
        ttf_path=ttf_path,
        source_proof_path=singleton_paths["segmented-source"],
        edge_proof_path=singleton_paths["edge-connect"],
    )
    return ValidatedVerticalBuild(
        batch_id=batch_id,
        descriptor_path=descriptor_path,
        descriptor_sha256=descriptor.source_sha256,
        report_path=report_path,
        report_sha256=_sha256(report_path),
        report=report,
        small_proof_sha256=dict(sorted(small_proofs.items())),
        ttf_path=ttf_path,
        ttf_sha256=ttf_hash,
        otf_path=otf_path,
        otf_sha256=otf_hash,
    )


def record_review(
    batch_id: str,
    *,
    reviewer_name: str,
    reviewer_role: str,
    reviewed_at: str,
    confirmation: str,
    project_root: Path = ROOT,
) -> Path:
    if confirmation != REVIEW_CONFIRMATION:
        raise VerticalApprovalError("review confirmation phrase is not exact")
    if not reviewer_name.strip() or not reviewer_role.strip():
        raise VerticalApprovalError("reviewer name and role are required")
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerticalApprovalError("reviewed_at must be ISO-8601") from exc
    build = validate_build(batch_id, project_root=project_root)
    glyph_reviews = [
        {
            "base_codepoint": record["codepoint"],
            "glyph_name": record["unencoded_glyph_name"],
            "status": "approved",
            "micro_edge_count": 0,
            "acute_micro_turn_count": 0,
            "micro_thorn_points_removed": 0,
            "reviewed_sizes_px": list(pipeline.nonhan.SMALL_SIZE_PIXELS),
            "reviewed_polarities": ["black-on-white", "white-on-black"],
        }
        for record in build.report["glyphs"]
    ]
    output = (
        project_root
        / f"sources/imagegen/vector-reviews/{build.batch_id}.vector-review.json"
    )
    return _write_json_once(
        output,
        {
            "schema_version": 1,
            "review_type": REVIEW_TYPE,
            "batch_id": build.batch_id,
            "pipeline": pipeline.PIPELINE_ID,
            "reviewer_name": reviewer_name.strip(),
            "reviewer_role": reviewer_role.strip(),
            "reviewed_at": reviewed_at,
            "confirmation": confirmation,
            "source_descriptor": _relative(
                build.descriptor_path,
                project_root,
            ),
            "source_descriptor_sha256": build.descriptor_sha256,
            "report": _relative(build.report_path, project_root),
            "report_sha256": build.report_sha256,
            "small_proof_sha256": dict(build.small_proof_sha256),
            "glyph_reviews": glyph_reviews,
        },
    )


def validate_review(
    batch_id: str,
    *,
    project_root: Path = ROOT,
) -> tuple[ValidatedVerticalBuild, Path, Mapping[str, Any]]:
    build = validate_build(batch_id, project_root=project_root)
    review_path = (
        project_root
        / f"sources/imagegen/vector-reviews/{build.batch_id}.vector-review.json"
    )
    review = _read_object(review_path)
    required = {
        "schema_version",
        "review_type",
        "batch_id",
        "pipeline",
        "reviewer_name",
        "reviewer_role",
        "reviewed_at",
        "confirmation",
        "source_descriptor",
        "source_descriptor_sha256",
        "report",
        "report_sha256",
        "small_proof_sha256",
        "glyph_reviews",
    }
    if set(review) != required:
        raise VerticalApprovalError(f"{review_path}: review fields are not exact")
    if (
        review["schema_version"] != 1
        or review["review_type"] != REVIEW_TYPE
        or review["batch_id"] != build.batch_id
        or review["pipeline"] != pipeline.PIPELINE_ID
        or review["confirmation"] != REVIEW_CONFIRMATION
        or review["source_descriptor_sha256"] != build.descriptor_sha256
        or review["report_sha256"] != build.report_sha256
        or review["small_proof_sha256"] != build.small_proof_sha256
    ):
        raise VerticalApprovalError(f"{review_path}: review hash chain mismatch")
    if (
        review["source_descriptor"]
        != _relative(build.descriptor_path, project_root)
        or review["report"] != _relative(build.report_path, project_root)
    ):
        raise VerticalApprovalError(
            f"{review_path}: review evidence path mismatch"
        )
    _validate_trimmed_text(
        review["reviewer_name"],
        where=f"{review_path}: reviewer_name",
    )
    _validate_trimmed_text(
        review["reviewer_role"],
        where=f"{review_path}: reviewer_role",
    )
    _validate_timestamp(
        review["reviewed_at"],
        where=f"{review_path}: reviewed_at",
    )
    glyph_reviews = review["glyph_reviews"]
    expected = [
        (record["codepoint"], record["unencoded_glyph_name"])
        for record in build.report["glyphs"]
    ]
    if (
        not isinstance(glyph_reviews, list)
        or [
            (record.get("base_codepoint"), record.get("glyph_name"))
            for record in glyph_reviews
            if isinstance(record, dict)
        ]
        != expected
    ):
        raise VerticalApprovalError(f"{review_path}: per-glyph review sequence mismatch")
    glyph_review_fields = {
        "base_codepoint",
        "glyph_name",
        "status",
        "micro_edge_count",
        "acute_micro_turn_count",
        "micro_thorn_points_removed",
        "reviewed_sizes_px",
        "reviewed_polarities",
    }
    for record in glyph_reviews:
        if (
            not isinstance(record, dict)
            or set(record) != glyph_review_fields
            or record.get("status") != "approved"
            or record.get("micro_edge_count") != 0
            or record.get("acute_micro_turn_count") != 0
            or record.get("micro_thorn_points_removed") != 0
            or record.get("reviewed_sizes_px")
            != list(pipeline.nonhan.SMALL_SIZE_PIXELS)
            or record.get("reviewed_polarities")
            != ["black-on-white", "white-on-black"]
        ):
            raise VerticalApprovalError(f"{review_path}: incomplete glyph review")
    return build, review_path, review


def authorize(
    batch_id: str,
    *,
    approver_name: str,
    approved_at: str,
    confirmation: str,
    project_root: Path = ROOT,
) -> Path:
    if confirmation != APPROVAL_CONFIRMATION:
        raise VerticalApprovalError("approval confirmation phrase is not exact")
    if not approver_name.strip():
        raise VerticalApprovalError("approver name is required")
    try:
        datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerticalApprovalError("approved_at must be ISO-8601") from exc
    build, review_path, _review = validate_review(
        batch_id,
        project_root=project_root,
    )
    glyphs = [
        {
            "base_codepoint": record["codepoint"],
            "glyph_name": record["unencoded_glyph_name"],
            "base_metrics": record["base_metrics"],
            "base_profile_id": record["base_profile_id"],
        }
        for record in build.report["glyphs"]
    ]
    output = (
        project_root
        / f"sources/imagegen/approvals/{build.batch_id}.approval.json"
    )
    return _write_json_once(
        output,
        {
            "schema_version": 1,
            "approval_type": APPROVAL_TYPE,
            "batch_id": build.batch_id,
            "pipeline": pipeline.PIPELINE_ID,
            "approver_name": approver_name.strip(),
            "approved_at": approved_at,
            "confirmation": confirmation,
            "source_descriptor": _relative(
                build.descriptor_path,
                project_root,
            ),
            "source_descriptor_sha256": build.descriptor_sha256,
            "report": _relative(build.report_path, project_root),
            "report_sha256": build.report_sha256,
            "vector_review": _relative(review_path, project_root),
            "vector_review_sha256": _sha256(review_path),
            "ttf": _relative(build.ttf_path, project_root),
            "ttf_sha256": build.ttf_sha256,
            "otf": _relative(build.otf_path, project_root),
            "otf_sha256": build.otf_sha256,
            "small_proof_sha256": dict(build.small_proof_sha256),
            "glyphs": glyphs,
        },
    )


def validate_approval(
    batch_id: str,
    *,
    project_root: Path = ROOT,
) -> Mapping[str, Any]:
    build, review_path, _review = validate_review(
        batch_id,
        project_root=project_root,
    )
    approval_path = (
        project_root
        / f"sources/imagegen/approvals/{build.batch_id}.approval.json"
    )
    approval = _read_object(approval_path)
    required = {
        "schema_version",
        "approval_type",
        "batch_id",
        "pipeline",
        "approver_name",
        "approved_at",
        "confirmation",
        "source_descriptor",
        "source_descriptor_sha256",
        "report",
        "report_sha256",
        "vector_review",
        "vector_review_sha256",
        "ttf",
        "ttf_sha256",
        "otf",
        "otf_sha256",
        "small_proof_sha256",
        "glyphs",
    }
    if set(approval) != required:
        raise VerticalApprovalError(
            f"{approval_path}: approval fields are not exact"
        )
    if (
        approval["schema_version"] != 1
        or approval["approval_type"] != APPROVAL_TYPE
        or approval["batch_id"] != build.batch_id
        or approval["pipeline"] != pipeline.PIPELINE_ID
        or approval["confirmation"] != APPROVAL_CONFIRMATION
        or approval["source_descriptor_sha256"] != build.descriptor_sha256
        or approval["report_sha256"] != build.report_sha256
        or approval["vector_review_sha256"] != _sha256(review_path)
        or approval["ttf_sha256"] != build.ttf_sha256
        or approval["otf_sha256"] != build.otf_sha256
        or approval["small_proof_sha256"] != build.small_proof_sha256
    ):
        raise VerticalApprovalError(
            f"{approval_path}: approval hash chain mismatch"
        )
    if (
        approval["source_descriptor"]
        != _relative(build.descriptor_path, project_root)
        or approval["report"] != _relative(build.report_path, project_root)
        or approval["vector_review"]
        != _relative(review_path, project_root)
        or approval["ttf"] != _relative(build.ttf_path, project_root)
        or approval["otf"] != _relative(build.otf_path, project_root)
    ):
        raise VerticalApprovalError(
            f"{approval_path}: approval evidence path mismatch"
        )
    _validate_trimmed_text(
        approval["approver_name"],
        where=f"{approval_path}: approver_name",
    )
    _validate_timestamp(
        approval["approved_at"],
        where=f"{approval_path}: approved_at",
    )
    expected_glyphs = [
        {
            "base_codepoint": record["codepoint"],
            "glyph_name": record["unencoded_glyph_name"],
            "base_metrics": record["base_metrics"],
            "base_profile_id": record["base_profile_id"],
        }
        for record in build.report["glyphs"]
    ]
    if approval["glyphs"] != expected_glyphs:
        raise VerticalApprovalError(
            f"{approval_path}: approved glyph sequence mismatch"
        )
    return approval


def load_complete_approvals(
    *,
    project_root: Path = ROOT,
) -> tuple[Mapping[str, Any], ...]:
    approval_root = project_root / "sources/imagegen/approvals"
    actual = {
        path.name.removesuffix(".approval.json")
        for path in approval_root.glob("vertical-*.approval.json")
    }
    expected = {f"vertical-{number:04d}" for number in range(1, 7)}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise VerticalApprovalError(
            f"vertical approvals incomplete: missing={missing}, extra={extra}"
        )
    return tuple(
        validate_approval(batch_id, project_root=project_root)
        for batch_id in sorted(expected)
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root containing the six canonical vertical approvals",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "validate-complete",
        help="validate the exact six-batch, 93-alternate approval set",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        approvals = load_complete_approvals(
            project_root=args.project_root.resolve()
        )
    except VerticalApprovalError as exc:
        raise SystemExit(str(exc)) from exc
    glyph_count = sum(len(approval["glyphs"]) for approval in approvals)
    print(
        f"validated {len(approvals)} vertical approvals "
        f"covering {glyph_count} alternates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
