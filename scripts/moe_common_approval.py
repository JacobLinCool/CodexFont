#!/usr/bin/env python3
"""Record and validate the reviewed MOE common-Han extension.

The approval record pins the irreplaceable generated rasters and their source
descriptors. Rebuildable vector reports and fonts are validated in place but
are intentionally not committed as source evidence.
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

from scripts.moe_common import EXPECTED_COUNT as MOE_COMMON_COUNT
from scripts.moe_common import load_moe_common


ROOT = Path(__file__).resolve().parents[1]
REPERTOIRE_RELATIVE = Path(
    "sources/imagegen/repertoires/moe-common-extension-1844.json"
)
APPROVAL_RELATIVE = Path(
    "sources/imagegen/approvals/moe-common-extension.approval.json"
)
REPERTOIRE_ID = "tw-moe-common-4808-extension-1844-v1"
REPERTOIRE_COUNT = 1844
BATCH_COUNT = 116
GRID_CAPACITY = 16
PIPELINE_ID = "imagegen-raster-potrace-quadratic-v2"
SMALL_SIZES = ("12", "16", "20", "32", "56")
CONFIRMATION = (
    "I_REVIEWED_ALL_1844_GLYPHS_AND_APPROVE_THEM_FOR_0_1_PREVIEW"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


class MoeCommonApprovalError(RuntimeError):
    """The common-Han extension evidence is incomplete or has drifted."""


@dataclass(frozen=True)
class ApprovedBatch:
    batch_id: str
    characters: tuple[str, ...]
    descriptor_path: Path
    descriptor_sha256: str
    raster_path: Path
    raster_sha256: str
    report_path: Path
    report_sha256: str
    ttf_path: Path
    ttf_sha256: str


@dataclass(frozen=True)
class ApprovedExtension:
    approval_path: Path
    approval_sha256: str
    repertoire_path: Path
    repertoire_sha256: str
    repertoire_id: str
    sequence_sha256: str
    reviewer_name: str
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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MoeCommonApprovalError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MoeCommonApprovalError(f"{path}: {label} must be an object")
    return value


def _require_file(project_root: Path, relative: str, *, label: str) -> Path:
    path = project_root / relative
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MoeCommonApprovalError(f"{label}: missing {path}") from exc
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError as exc:
        raise MoeCommonApprovalError(f"{label}: path escapes repository") from exc
    if not resolved.is_file() or path.is_symlink():
        raise MoeCommonApprovalError(f"{label}: not a regular file: {path}")
    return resolved


def _require_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise MoeCommonApprovalError(f"{label}: invalid SHA-256")
    return value


def _require_timestamp(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise MoeCommonApprovalError(f"{label}: invalid UTC timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise MoeCommonApprovalError(f"{label}: invalid UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise MoeCommonApprovalError(f"{label}: noncanonical UTC timestamp")
    return value


def _load_repertoire(
    project_root: Path,
) -> tuple[Path, dict[str, Any], tuple[dict[str, Any], ...]]:
    path = _require_file(
        project_root,
        REPERTOIRE_RELATIVE.as_posix(),
        label="MOE extension repertoire",
    )
    value = _read_object(path, label="MOE extension repertoire")
    if (
        value.get("schema_version") != 1
        or value.get("repertoire_id") != REPERTOIRE_ID
        or value.get("normalization") != "NFC"
        or value.get("total_count") != REPERTOIRE_COUNT
    ):
        raise MoeCommonApprovalError(f"{path}: repertoire identity drift")
    raw_batches = value.get("batches")
    if not isinstance(raw_batches, list) or len(raw_batches) != BATCH_COUNT:
        raise MoeCommonApprovalError(f"{path}: expected {BATCH_COUNT} batches")
    batches: list[dict[str, Any]] = []
    sequence: list[str] = []
    next_rank = 1
    for number, raw in enumerate(raw_batches, start=1):
        if not isinstance(raw, dict):
            raise MoeCommonApprovalError(f"{path}: batch {number} is malformed")
        batch_id = f"moe-common-{number:04d}"
        characters = raw.get("characters")
        expected_count = (
            REPERTOIRE_COUNT % GRID_CAPACITY
            if number == BATCH_COUNT
            else GRID_CAPACITY
        )
        if (
            raw.get("batch_id") != batch_id
            or raw.get("start_rank") != next_rank
            or not isinstance(characters, str)
            or len(characters) != expected_count
            or raw.get("character_count") != expected_count
            or raw.get("end_rank") != next_rank + expected_count - 1
            or raw.get("grid_capacity") != GRID_CAPACITY
            or raw.get("empty_grid_cells") != GRID_CAPACITY - expected_count
            or raw.get("raster_path")
            != f"sources/imagegen/raster/{batch_id}.png"
            or raw.get("codepoints")
            != [f"U+{ord(character):04X}" for character in characters]
        ):
            raise MoeCommonApprovalError(f"{path}: {batch_id} drift")
        batches.append(raw)
        sequence.extend(characters)
        next_rank += expected_count
    if len(sequence) != REPERTOIRE_COUNT or len(set(sequence)) != len(sequence):
        raise MoeCommonApprovalError(f"{path}: extension sequence is invalid")
    sequence_sha256 = value.get("provenance", {}).get("sequence_sha256")
    if sequence_sha256 != _sha256_text("".join(sequence)):
        raise MoeCommonApprovalError(f"{path}: sequence hash drift")

    common = {record.character for record in load_moe_common()}
    base_path = project_root / "sources/imagegen/repertoires/common-3000.json"
    base = _read_object(base_path, label="base Han repertoire")
    base_characters = {
        row["character"] for row in base.get("characters", [])
        if isinstance(row, dict) and isinstance(row.get("character"), str)
    }
    if len(base_characters) != 3000:
        raise MoeCommonApprovalError("base Han repertoire must contain 3,000")
    if set(sequence) != common - base_characters:
        raise MoeCommonApprovalError(
            "extension is not the exact missing part of the MOE 4,808 set"
        )
    return path, value, tuple(batches)


def _validate_source(
    project_root: Path,
    batch: Mapping[str, Any],
) -> tuple[Path, str, Path, str]:
    batch_id = str(batch["batch_id"])
    descriptor_relative = f"sources/imagegen/batches/{batch_id}.source.json"
    descriptor_path = _require_file(
        project_root, descriptor_relative, label=f"{batch_id} descriptor"
    )
    descriptor = _read_object(descriptor_path, label="source descriptor")
    raster_relative = f"sources/imagegen/raster/{batch_id}.png"
    raster_path = _require_file(
        project_root, raster_relative, label=f"{batch_id} raster"
    )
    raster_sha256 = _sha256(raster_path)
    if (
        descriptor.get("schema_version") != 1
        or descriptor.get("batch_id") != f"imagegen-{batch_id}"
        or descriptor.get("state") != "generated-unreviewed"
        or descriptor.get("generator") != "built-in-image_gen"
        or descriptor.get("raster") != f"../raster/{batch_id}.png"
        or descriptor.get("raster_sha256") != raster_sha256
        or descriptor.get("grid", {}).get("characters")
        != list(str(batch["characters"]))
        or descriptor.get("grid", {}).get("empty_grid_cells")
        != batch["empty_grid_cells"]
        or descriptor.get("review")
        != {
            "topology": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        }
    ):
        raise MoeCommonApprovalError(f"{descriptor_path}: source drift")
    return descriptor_path, _sha256(descriptor_path), raster_path, raster_sha256


def _validate_vector(
    project_root: Path,
    batch: Mapping[str, Any],
    *,
    descriptor_sha256: str,
    raster_sha256: str,
) -> tuple[Path, str, Path, str]:
    batch_id = str(batch["batch_id"])
    build = project_root / "build/imagegen" / f"imagegen-{batch_id}"
    report_path = _require_file(
        project_root,
        report_relative := (
            f"build/imagegen/imagegen-{batch_id}/report.json"
        ),
        label=f"{batch_id} vector report",
    )
    report = _read_object(report_path, label="vector report")
    characters = list(str(batch["characters"]))
    if (
        report.get("schema_version") != 1
        or report.get("pipeline") != PIPELINE_ID
        or report.get("batch_id") != f"imagegen-{batch_id}"
        or report.get("approval_state") != "unreviewed"
        or report.get("source_state") != "generated-unreviewed"
        or report.get("source_descriptor_sha256") != descriptor_sha256
        or report.get("source_raster_sha256") != raster_sha256
        or report.get("characters") != characters
    ):
        raise MoeCommonApprovalError(f"{report_path}: vector identity drift")
    glyphs = report.get("glyphs")
    coverage = report.get("small_size_coverage_pixels")
    if (
        not isinstance(glyphs, list)
        or len(glyphs) != len(characters)
        or not isinstance(coverage, dict)
    ):
        raise MoeCommonApprovalError(f"{report_path}: vector QA is incomplete")
    for character, glyph in zip(characters, glyphs, strict=True):
        label = f"U+{ord(character):04X}"
        if (
            not isinstance(glyph, dict)
            or glyph.get("character") != character
            or glyph.get("codepoint") != label
            or glyph.get("micro_edge_count") != 0
            or glyph.get("acute_micro_turn_count") != 0
            or glyph.get("micro_thorn_points_removed") != 0
            or glyph.get("contour_count", 0) <= 0
            or glyph.get("point_count", 0) <= 0
        ):
            raise MoeCommonApprovalError(
                f"{report_path}: {label} failed outline QA"
            )
        pixels = coverage.get(label)
        if (
            not isinstance(pixels, dict)
            or set(pixels) != set(SMALL_SIZES)
            or any(
                not isinstance(pixels[size], int) or pixels[size] <= 0
                for size in SMALL_SIZES
            )
        ):
            raise MoeCommonApprovalError(
                f"{report_path}: {label} failed small-size QA"
            )
    font = report.get("font")
    if not isinstance(font, dict) or font.get("cmap_count") != len(characters):
        raise MoeCommonApprovalError(f"{report_path}: font record drift")
    ttf_relative = font.get("ttf")
    if not isinstance(ttf_relative, str):
        raise MoeCommonApprovalError(f"{report_path}: missing TTF")
    ttf_path = _require_file(
        project_root,
        f"build/imagegen/imagegen-{batch_id}/{ttf_relative}",
        label=f"{batch_id} TTF",
    )
    ttf_sha256 = _sha256(ttf_path)
    if ttf_sha256 != font.get("ttf_sha256"):
        raise MoeCommonApprovalError(f"{report_path}: TTF hash drift")
    with TTFont(ttf_path, lazy=False, checkChecksums=2) as ttfont:
        cmap = ttfont.getBestCmap()
        expected = {
            ord(character): (
                f"uni{ord(character):04X}"
                if ord(character) <= 0xFFFF
                else f"u{ord(character):05X}"
            )
            for character in characters
        }
        if cmap != expected:
            raise MoeCommonApprovalError(f"{ttf_path}: cmap drift")
        for name in expected.values():
            glyph = ttfont["glyf"][name]
            if glyph.isComposite() or glyph.numberOfContours <= 0:
                raise MoeCommonApprovalError(
                    f"{ttf_path}: {name} is empty or composite"
                )
    if report_path != (project_root / report_relative).resolve():
        raise MoeCommonApprovalError(f"{report_path}: noncanonical report path")
    return report_path, _sha256(report_path), ttf_path, ttf_sha256


def _source_inventory(
    project_root: Path,
    batches: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for batch in batches:
        descriptor, descriptor_hash, raster, raster_hash = _validate_source(
            project_root, batch
        )
        report, report_hash, ttf, ttf_hash = _validate_vector(
            project_root,
            batch,
            descriptor_sha256=descriptor_hash,
            raster_sha256=raster_hash,
        )
        records.append(
            {
                "batch_id": str(batch["batch_id"]),
                "descriptor": descriptor.relative_to(project_root).as_posix(),
                "descriptor_sha256": descriptor_hash,
                "raster": raster.relative_to(project_root).as_posix(),
                "raster_sha256": raster_hash,
                "vector_report": report.relative_to(project_root).as_posix(),
                "vector_report_sha256": report_hash,
                "vector_ttf": ttf.relative_to(project_root).as_posix(),
                "vector_ttf_sha256": ttf_hash,
            }
        )
    return records


def record_approval(
    *,
    project_root: Path,
    reviewer_name: str,
    reviewed_at: str,
    confirmation: str,
) -> Path:
    if confirmation != CONFIRMATION:
        raise MoeCommonApprovalError("explicit review confirmation is required")
    if not reviewer_name.strip() or reviewer_name != reviewer_name.strip():
        raise MoeCommonApprovalError("reviewer name is invalid")
    reviewed_at = _require_timestamp(reviewed_at, label="reviewed_at")
    repertoire_path, repertoire, batches = _load_repertoire(project_root)
    inventory = _source_inventory(project_root, batches)
    payload = {
        "schema_version": 1,
        "record_type": "moe-common-extension-approval",
        "decision": "APPROVED",
        "release": "0.1 Preview",
        "repertoire": {
            "path": REPERTOIRE_RELATIVE.as_posix(),
            "sha256": _sha256(repertoire_path),
            "repertoire_id": REPERTOIRE_ID,
            "count": REPERTOIRE_COUNT,
            "sequence_sha256": repertoire["provenance"]["sequence_sha256"],
        },
        "review": {
            "reviewer_name": reviewer_name,
            "reviewer_role": "font designer and release reviewer",
            "reviewed_at": reviewed_at,
            "scope": (
                "all 1,844 extension glyphs: source topology, Taiwan "
                "Traditional identity, vector contours, spike/thorn checks, "
                "counter openness, and 12/16/20/32/56 px legibility"
            ),
            "copybook_policy": (
                "TW-Kai was used only to verify identity and topology; its "
                "outlines are not release inputs"
            ),
            "identity_corrections": 19,
        },
        "authorization": {
            "decision": "APPROVED",
            "approver_name": reviewer_name,
            "approved_at": reviewed_at,
        },
        "source_batches": inventory,
    }
    output = project_root / APPROVAL_RELATIVE
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=False
    ) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != encoded:
        raise MoeCommonApprovalError(f"refusing to overwrite {output}")
    output.write_text(encoded, encoding="utf-8")
    validate_approval(project_root=project_root, approval_path=output)
    return output


def validate_approval(
    *,
    project_root: Path = ROOT,
    approval_path: Path | None = None,
) -> ApprovedExtension:
    project_root = project_root.resolve()
    expected_approval = (project_root / APPROVAL_RELATIVE).resolve()
    approval_path = (approval_path or expected_approval).resolve()
    if approval_path != expected_approval:
        raise MoeCommonApprovalError("approval path is not canonical")
    approval = _read_object(approval_path, label="MOE extension approval")
    if (
        approval.get("schema_version") != 1
        or approval.get("record_type") != "moe-common-extension-approval"
        or approval.get("decision") != "APPROVED"
        or approval.get("release") != "0.1 Preview"
    ):
        raise MoeCommonApprovalError(f"{approval_path}: approval drift")
    repertoire_path, repertoire, batches = _load_repertoire(project_root)
    reference = approval.get("repertoire")
    if (
        not isinstance(reference, dict)
        or reference.get("path") != REPERTOIRE_RELATIVE.as_posix()
        or reference.get("sha256") != _sha256(repertoire_path)
        or reference.get("repertoire_id") != REPERTOIRE_ID
        or reference.get("count") != REPERTOIRE_COUNT
        or reference.get("sequence_sha256")
        != repertoire["provenance"]["sequence_sha256"]
    ):
        raise MoeCommonApprovalError(f"{approval_path}: repertoire drift")
    review = approval.get("review")
    authorization = approval.get("authorization")
    if (
        not isinstance(review, dict)
        or not isinstance(authorization, dict)
        or review.get("identity_corrections") != 19
        or authorization.get("decision") != "APPROVED"
    ):
        raise MoeCommonApprovalError(f"{approval_path}: review is incomplete")
    reviewer = review.get("reviewer_name")
    approver = authorization.get("approver_name")
    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
        or not isinstance(approver, str)
        or not approver.strip()
    ):
        raise MoeCommonApprovalError(f"{approval_path}: reviewer is invalid")
    reviewed_at = _require_timestamp(
        review.get("reviewed_at"), label="reviewed_at"
    )
    approved_at = _require_timestamp(
        authorization.get("approved_at"), label="approved_at"
    )
    if approved_at < reviewed_at:
        raise MoeCommonApprovalError("approval predates review")

    raw_sources = approval.get("source_batches")
    if not isinstance(raw_sources, list) or len(raw_sources) != BATCH_COUNT:
        raise MoeCommonApprovalError("source batch inventory is incomplete")
    admitted: list[ApprovedBatch] = []
    for batch, pinned in zip(batches, raw_sources, strict=True):
        if not isinstance(pinned, dict):
            raise MoeCommonApprovalError("source batch record is malformed")
        descriptor, descriptor_hash, raster, raster_hash = _validate_source(
            project_root, batch
        )
        report, report_hash, ttf, ttf_hash = _validate_vector(
            project_root,
            batch,
            descriptor_sha256=descriptor_hash,
            raster_sha256=raster_hash,
        )
        expected_pinned = {
            "batch_id": batch["batch_id"],
            "descriptor": descriptor.relative_to(project_root).as_posix(),
            "descriptor_sha256": descriptor_hash,
            "raster": raster.relative_to(project_root).as_posix(),
            "raster_sha256": raster_hash,
            "vector_report": report.relative_to(project_root).as_posix(),
            "vector_report_sha256": report_hash,
            "vector_ttf": ttf.relative_to(project_root).as_posix(),
            "vector_ttf_sha256": ttf_hash,
        }
        if pinned != expected_pinned:
            raise MoeCommonApprovalError(
                f"{batch['batch_id']}: pinned source drift"
            )
        admitted.append(
            ApprovedBatch(
                batch_id=str(batch["batch_id"]),
                characters=tuple(str(batch["characters"])),
                descriptor_path=descriptor,
                descriptor_sha256=descriptor_hash,
                raster_path=raster,
                raster_sha256=raster_hash,
                report_path=report,
                report_sha256=report_hash,
                ttf_path=ttf,
                ttf_sha256=ttf_hash,
            )
        )
    extension = ApprovedExtension(
        approval_path=approval_path,
        approval_sha256=_sha256(approval_path),
        repertoire_path=repertoire_path,
        repertoire_sha256=_sha256(repertoire_path),
        repertoire_id=REPERTOIRE_ID,
        sequence_sha256=repertoire["provenance"]["sequence_sha256"],
        reviewer_name=reviewer,
        reviewed_at=reviewed_at,
        approver_name=approver,
        approved_at=approved_at,
        batches=tuple(admitted),
    )
    if len(extension.characters) != REPERTOIRE_COUNT:
        raise MoeCommonApprovalError("validated extension count drift")
    if len(set(extension.characters)) != REPERTOIRE_COUNT:
        raise MoeCommonApprovalError("validated extension contains duplicates")
    if len(load_moe_common()) != MOE_COMMON_COUNT:
        raise MoeCommonApprovalError("MOE common inventory count drift")
    return extension


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    record = subparsers.add_parser("record")
    record.add_argument("--reviewer", required=True)
    record.add_argument("--reviewed-at", required=True)
    record.add_argument("--confirmation", required=True)
    subparsers.add_parser("validate")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    if args.command == "record":
        print(
            record_approval(
                project_root=project_root,
                reviewer_name=args.reviewer,
                reviewed_at=args.reviewed_at,
                confirmation=args.confirmation,
            )
        )
    else:
        approved = validate_approval(project_root=project_root)
        print(
            f"validated {len(approved.batches)} batches covering "
            f"{len(approved.characters)} glyphs"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
