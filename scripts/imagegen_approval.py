#!/usr/bin/env python3
"""Validate hash-pinned approvals for the imagegen-first Han pipeline.

This module is the only admission boundary between generated image sheets and
the combined release font.  It deliberately does not import or inspect
``sources/authored``.  A source descriptor remains
``generated-unreviewed``/``pending`` forever; approval is a separate,
human-signed record backed by immutable raster, audit, vector-build, and
visual-review evidence.

The validator is fail-closed:

* the frozen 3,000-character repertoire and exact batch ranks are authoritative;
* every referenced file is project-relative and SHA-256 pinned;
* only the explicitly supported raster-audit schemas are accepted;
* only the v2 quadratic vector report is accepted;
* the complete vector artifact inventory is re-hashed;
* every glyph must have zero micro edges and zero acute micro turns;
* every requested small size must rasterize with non-zero coverage; and
* a separate per-glyph visual review and final authorization must both say
  ``approved``.

No command in this module creates an approval or guesses reviewer decisions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Mapping, NoReturn, Sequence
import unicodedata

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]

APPROVAL_SCHEMA_VERSION = 1
APPROVAL_RECORD_TYPE = "imagegen-batch-approval"
VISUAL_REVIEW_RECORD_TYPE = "imagegen-vector-visual-review"
VECTOR_PIPELINE = "imagegen-raster-potrace-quadratic-v2"

REPERTOIRE_RELATIVE_PATH = PurePosixPath(
    "sources/imagegen/repertoires/common-3000.json"
)
REPERTOIRE_ID = "tw-moe-dictionary-salience-han-3000-v1"
REPERTOIRE_SHA256 = (
    "c9f965516bed2821cf137480bddf23acd043a339165571cf9b3e87bbf5ffc66a"
)
REPERTOIRE_SEQUENCE_SHA256 = (
    "4f701cbd115f8525e2f3a417b9e330cd7bd5f74a6de81eb48092f90af9fed4cd"
)
REPERTOIRE_TOTAL = 3000
REPERTOIRE_BATCH_COUNT = 188
GRID_CAPACITY = 16

SMALL_SIZE_PIXELS = (12, 16, 20, 32, 56)
VISUAL_CHECKS = (
    "glyph-identity",
    "taiwan-traditional-topology",
    "contour-smoothness",
    "no-spikes-or-thorns",
    "counter-openness",
    "small-size-legibility",
)
VISUAL_POLARITIES = ("black-on-white", "white-on-black")
VISUAL_PROOF_KINDS = (
    "black-on-white",
    "white-on-black",
    "segmented-source",
)

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
CANONICAL_BATCH_PATTERN = re.compile(r"common-(?P<number>[0-9]{4})")
AUDIT_PATH_PATTERN = re.compile(
    r"reports/imagegen-common-[0-9]{4}-[0-9]{4}-audit\.json"
)
RFC3339_UTC_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


class ImagegenApprovalError(RuntimeError):
    """Approval evidence is missing, ambiguous, stale, or invalid."""


@dataclass(frozen=True)
class RepertoireBatch:
    """One exact batch from the frozen 3,000-character repertoire."""

    batch_id: str
    number: int
    start_rank: int
    end_rank: int
    characters: tuple[str, ...]
    empty_grid_cells: int

    @property
    def descriptor_batch_id(self) -> str:
        return f"imagegen-{self.batch_id}"


@dataclass(frozen=True)
class Repertoire:
    """Validated frozen repertoire and its batch plan."""

    path: Path
    sha256: str
    repertoire_id: str
    sequence_sha256: str
    characters: tuple[str, ...]
    batches: tuple[RepertoireBatch, ...]


@dataclass(frozen=True)
class ValidatedApproval:
    """All inputs needed to compile one admitted batch."""

    approval_path: Path
    approval_sha256: str
    batch: RepertoireBatch
    repertoire: Repertoire
    descriptor_path: Path
    descriptor_sha256: str
    raster_path: Path
    raster_sha256: str
    audit_path: Path
    audit_sha256: str
    vector_report_path: Path
    vector_report_sha256: str
    vector_build_directory: Path
    vector_report: Mapping[str, Any]
    visual_review_path: Path
    visual_review_sha256: str
    reviewer_name: str
    reviewed_at: str
    approver_name: str
    approved_at: str
    ttf_path: Path
    otf_path: Path

    @property
    def characters(self) -> tuple[str, ...]:
        return self.batch.characters


def sha256_path(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a regular file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fail(where: str | Path, message: str) -> NoReturn:
    raise ImagegenApprovalError(f"{where}: {message}")


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImagegenApprovalError(
            f"{path}: cannot read {label} JSON: {exc}"
        ) from exc
    if not isinstance(value, dict):
        _fail(path, f"{label} must be a JSON object")
    return value


def _exact_keys(
    value: Any,
    expected: Iterable[str],
    *,
    where: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(where, "must be an object")
    expected_set = set(expected)
    actual_set = set(value)
    if actual_set != expected_set:
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        _fail(where, f"wrong keys; missing={missing}, extra={extra}")
    return value


def _lower_sha256(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        _fail(where, "must be a lowercase 64-character SHA-256")
    return value


def _nonempty_string(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(where, "must be a non-empty string")
    if value != value.strip():
        _fail(where, "must not contain leading or trailing whitespace")
    return value


def _one_scalar(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or len(value) != 1:
        _fail(where, "must contain exactly one Unicode scalar")
    codepoint = ord(value)
    if 0xD800 <= codepoint <= 0xDFFF:
        _fail(where, "surrogate code points are forbidden")
    if not unicodedata.category(value).startswith("L"):
        _fail(where, "must be a Unicode letter")
    return value


def _relative_posix_path(value: Any, *, where: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        _fail(where, "must be a non-empty project-relative POSIX path")
    if "\\" in value:
        _fail(where, "backslashes are forbidden")
    relative = PurePosixPath(value)
    if relative.is_absolute() or relative.as_posix() != value:
        _fail(where, "must be a normalized project-relative POSIX path")
    if any(part in {"", ".", ".."} for part in relative.parts):
        _fail(where, "dot and parent components are forbidden")
    if "authored" in relative.parts:
        _fail(where, "authored-source paths are forbidden")
    return relative


def _resolve_regular_file(
    project_root: Path,
    relative: PurePosixPath,
    *,
    where: str,
) -> Path:
    root = project_root.resolve()
    path = root.joinpath(*relative.parts)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ImagegenApprovalError(
            f"{where}: referenced file does not resolve: {relative}: {exc}"
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError:
        _fail(where, f"path escapes project root: {relative}")
    if not resolved.is_file():
        _fail(where, f"not a regular file: {relative}")
    return resolved


def _require_rfc3339_utc(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or RFC3339_UTC_PATTERN.fullmatch(value) is None:
        _fail(where, "must be RFC 3339 UTC with second precision")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ImagegenApprovalError(f"{where}: invalid timestamp: {exc}") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        _fail(where, "timestamp is not canonical")
    return value


def _canonical_batch_id(value: Any, *, where: str) -> tuple[str, int]:
    if not isinstance(value, str):
        _fail(where, "must be a string")
    match = CANONICAL_BATCH_PATTERN.fullmatch(value)
    if match is None:
        _fail(where, "must have the form common-NNNN")
    number = int(match.group("number"))
    if not 1 <= number <= REPERTOIRE_BATCH_COUNT:
        _fail(where, f"batch number must be 0001..{REPERTOIRE_BATCH_COUNT:04d}")
    return value, number


def load_frozen_repertoire(project_root: Path = ROOT) -> Repertoire:
    """Load and fully validate the frozen common-3000 batch plan."""

    path = _resolve_regular_file(
        project_root,
        REPERTOIRE_RELATIVE_PATH,
        where="frozen repertoire",
    )
    actual_hash = sha256_path(path)
    if actual_hash != REPERTOIRE_SHA256:
        _fail(
            path,
            f"frozen repertoire hash drifted: expected {REPERTOIRE_SHA256}, "
            f"got {actual_hash}",
        )
    payload = _read_json_object(path, label="repertoire")
    if payload.get("schema_version") != 1:
        _fail(path, "schema_version must be 1")
    if payload.get("repertoire_id") != REPERTOIRE_ID:
        _fail(path, f"repertoire_id must be {REPERTOIRE_ID!r}")
    if payload.get("normalization") != "NFC":
        _fail(path, "normalization must be NFC")
    if payload.get("total_count") != REPERTOIRE_TOTAL:
        _fail(path, f"total_count must be {REPERTOIRE_TOTAL}")

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        _fail(path, "provenance must be an object")
    sequence_hash = _lower_sha256(
        provenance.get("sequence_sha256"),
        where=f"{path}: provenance.sequence_sha256",
    )
    if sequence_hash != REPERTOIRE_SEQUENCE_SHA256:
        _fail(path, "frozen sequence hash drifted")

    raw_batches = payload.get("batches")
    if not isinstance(raw_batches, list) or len(raw_batches) != REPERTOIRE_BATCH_COUNT:
        _fail(
            path,
            f"batches must contain exactly {REPERTOIRE_BATCH_COUNT} records",
        )
    batches: list[RepertoireBatch] = []
    sequence: list[str] = []
    next_rank = 1
    for offset, raw in enumerate(raw_batches, start=1):
        where = f"{path}: batches[{offset - 1}]"
        if not isinstance(raw, dict):
            _fail(where, "must be an object")
        expected_id = f"common-{offset:04d}"
        if raw.get("batch_id") != expected_id:
            _fail(where, f"batch_id must be {expected_id!r}")
        start_rank = raw.get("start_rank")
        end_rank = raw.get("end_rank")
        character_count = raw.get("character_count")
        empty_grid_cells = raw.get("empty_grid_cells")
        characters_raw = raw.get("characters")
        if start_rank != next_rank:
            _fail(where, f"start_rank must be {next_rank}")
        if not isinstance(characters_raw, str):
            _fail(where, "characters must be a string")
        characters = tuple(
            _one_scalar(character, where=f"{where}.characters")
            for character in characters_raw
        )
        expected_count = 8 if offset == REPERTOIRE_BATCH_COUNT else GRID_CAPACITY
        if len(characters) != expected_count:
            _fail(where, f"must contain exactly {expected_count} characters")
        if character_count != expected_count:
            _fail(where, f"character_count must be {expected_count}")
        expected_empty = GRID_CAPACITY - expected_count
        if empty_grid_cells != expected_empty:
            _fail(where, f"empty_grid_cells must be {expected_empty}")
        if raw.get("grid_capacity") != GRID_CAPACITY:
            _fail(where, f"grid_capacity must be {GRID_CAPACITY}")
        if end_rank != start_rank + expected_count - 1:
            _fail(where, "end_rank does not match character count")
        expected_codepoints = [f"U+{ord(character):04X}" for character in characters]
        if raw.get("codepoints") != expected_codepoints:
            _fail(where, "codepoints do not exactly match characters")
        expected_raster = f"sources/imagegen/raster/{expected_id}.png"
        if raw.get("raster_path") != expected_raster:
            _fail(where, f"raster_path must be {expected_raster!r}")
        batches.append(
            RepertoireBatch(
                batch_id=expected_id,
                number=offset,
                start_rank=start_rank,
                end_rank=end_rank,
                characters=characters,
                empty_grid_cells=expected_empty,
            )
        )
        sequence.extend(characters)
        next_rank = end_rank + 1

    characters = tuple(sequence)
    if len(characters) != REPERTOIRE_TOTAL:
        _fail(path, "batch sequence does not contain exactly 3,000 characters")
    if len(set(characters)) != len(characters):
        _fail(path, "batch sequence contains duplicate characters")
    computed_hash = sha256_text("".join(characters))
    if computed_hash != sequence_hash:
        _fail(path, "computed character sequence hash does not match provenance")
    raw_characters = payload.get("characters")
    if not isinstance(raw_characters, list) or len(raw_characters) != REPERTOIRE_TOTAL:
        _fail(path, "characters records must contain exactly 3,000 items")
    serialized_sequence = tuple(
        _one_scalar(
            item.get("character") if isinstance(item, dict) else None,
            where=f"{path}: characters[{index}].character",
        )
        for index, item in enumerate(raw_characters)
    )
    if serialized_sequence != characters:
        _fail(path, "characters records do not exactly match the batch sequence")
    return Repertoire(
        path=path,
        sha256=actual_hash,
        repertoire_id=REPERTOIRE_ID,
        sequence_sha256=sequence_hash,
        characters=characters,
        batches=tuple(batches),
    )


def _validate_approval_repertoire(
    value: Any,
    *,
    repertoire: Repertoire,
    batch: RepertoireBatch,
    where: str,
) -> None:
    reference = _exact_keys(
        value,
        {
            "path",
            "sha256",
            "repertoire_id",
            "sequence_sha256",
            "start_rank",
            "end_rank",
            "characters",
        },
        where=where,
    )
    relative = _relative_posix_path(reference["path"], where=f"{where}.path")
    if relative != REPERTOIRE_RELATIVE_PATH:
        _fail(f"{where}.path", f"must be {REPERTOIRE_RELATIVE_PATH}")
    if _lower_sha256(reference["sha256"], where=f"{where}.sha256") != repertoire.sha256:
        _fail(where, "repertoire sha256 does not match the frozen file")
    if reference["repertoire_id"] != repertoire.repertoire_id:
        _fail(where, "repertoire_id mismatch")
    if reference["sequence_sha256"] != repertoire.sequence_sha256:
        _fail(where, "sequence_sha256 mismatch")
    if reference["start_rank"] != batch.start_rank:
        _fail(where, "start_rank mismatch")
    if reference["end_rank"] != batch.end_rank:
        _fail(where, "end_rank mismatch")
    if reference["characters"] != "".join(batch.characters):
        _fail(where, "characters do not exactly match frozen repertoire batch")


def _validate_source_descriptor(
    path: Path,
    *,
    expected_hash: str,
    project_root: Path,
    batch: RepertoireBatch,
    approval_source: Mapping[str, Any],
) -> tuple[Path, str]:
    if sha256_path(path) != expected_hash:
        _fail(path, "source descriptor hash changed during validation")
    payload = _read_json_object(path, label="source descriptor")
    if payload.get("schema_version") != 1:
        _fail(path, "schema_version must be 1")
    if payload.get("batch_id") != batch.descriptor_batch_id:
        _fail(path, f"batch_id must be {batch.descriptor_batch_id!r}")
    if payload.get("state") != "generated-unreviewed":
        _fail(path, "state must remain generated-unreviewed")
    review = payload.get("review")
    if review != {
        "topology": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }:
        _fail(path, "source review must remain exactly pending for all checks")
    grid = payload.get("grid")
    if not isinstance(grid, dict):
        _fail(path, "grid must be an object")
    if grid.get("rows") != 4 or grid.get("columns") != 4:
        _fail(path, "grid must be exactly 4 by 4")
    if grid.get("characters") != list(batch.characters):
        _fail(path, "grid characters do not match frozen repertoire order")
    if grid.get("empty_grid_cells", 0) != batch.empty_grid_cells:
        _fail(path, "grid empty cell count does not match frozen repertoire")

    raster_relative = PurePosixPath(
        f"sources/imagegen/raster/{batch.batch_id}.png"
    )
    raw_raster = payload.get("raster")
    if not isinstance(raw_raster, str):
        _fail(path, "raster must be a relative path string")
    resolved_from_descriptor = (path.parent / raw_raster).resolve()
    expected_raster_path = project_root.resolve().joinpath(*raster_relative.parts)
    try:
        expected_raster_path = expected_raster_path.resolve(strict=True)
    except OSError as exc:
        raise ImagegenApprovalError(
            f"{path}: expected raster does not exist: {exc}"
        ) from exc
    if resolved_from_descriptor != expected_raster_path:
        _fail(path, f"raster must resolve to {raster_relative}")
    descriptor_raster_hash = _lower_sha256(
        payload.get("raster_sha256"), where=f"{path}: raster_sha256"
    )
    approval_raster_hash = _lower_sha256(
        approval_source.get("raster_sha256"),
        where="approval.source.raster_sha256",
    )
    if descriptor_raster_hash != approval_raster_hash:
        _fail(path, "descriptor and approval raster hashes differ")
    actual_raster_hash = sha256_path(expected_raster_path)
    if actual_raster_hash != descriptor_raster_hash:
        _fail(path, "raster hash mismatch")
    return expected_raster_path, actual_raster_hash


def _audit_summary_is_all_pass(payload: Mapping[str, Any], *, path: Path) -> None:
    """Validate the report-wide summary for one of two known audit schemas."""

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        _fail(path, "audit summary must be an object")
    if "report_id" in payload and "glyphs" not in payload:
        total = summary.get("glyph_count")
        passed = summary.get("pass_count")
        rejected = summary.get("reject_count")
        if summary.get("failed_cells") != []:
            _fail(path, "nested audit has failed cells")
    elif "audit_id" in payload and isinstance(payload.get("glyphs"), list):
        total = summary.get("total")
        passed = summary.get("pass")
        rejected = summary.get("reject")
        if summary.get("failed_cells") != []:
            _fail(path, "flat audit has failed cells")
        if summary.get("rejected_for_vectorization", 0) != 0:
            _fail(path, "flat audit rejected glyphs for vectorization")
    else:
        _fail(path, "unsupported raster-audit schema")
    if not isinstance(total, int) or total <= 0:
        _fail(path, "audit total must be a positive integer")
    if passed != total or rejected != 0:
        _fail(path, "audit summary is not all-PASS with zero rejects")
    if payload.get("failures", []) != []:
        _fail(path, "audit failures must be empty")


def _validate_declared_raster_audit_proofs(
    payload: Mapping[str, Any],
    *,
    path: Path,
    project_root: Path,
) -> None:
    """Re-hash every proof record declared by a raster-audit schema.

    Historical audit schemas did not serialize a proof inventory.  When an
    audit does declare ``proofs``, however, the declaration is part of the
    approval evidence and must not be treated as descriptive metadata: every
    recursively nested ``path``/``sha256`` pair is required to resolve below
    one of the two canonical audit-evidence roots and match its pinned bytes.
    """

    if "proofs" not in payload:
        return
    proofs = payload["proofs"]
    if not isinstance(proofs, (dict, list)):
        _fail(path, "audit proofs must be an object or array")

    records: list[tuple[str, Mapping[str, Any]]] = []

    def collect(value: Any, *, where: str) -> None:
        if isinstance(value, list):
            for index, item in enumerate(value):
                collect(item, where=f"{where}[{index}]")
            return
        if not isinstance(value, dict):
            return
        has_path = "path" in value
        has_hash = "sha256" in value
        if has_path != has_hash:
            _fail(where, "proof records must contain both path and sha256")
        if has_path:
            records.append((where, value))
        for key, item in value.items():
            collect(item, where=f"{where}.{key}")

    collect(proofs, where=f"{path}: proofs")
    if not records:
        _fail(path, "declared audit proofs contain no hash-pinned records")

    seen: set[PurePosixPath] = set()
    proof_roots = (
        PurePosixPath("reports/proofs"),
        PurePosixPath("build/imagegen-audit"),
    )
    for where, record in records:
        relative = _relative_posix_path(
            record["path"], where=f"{where}.path"
        )
        if not any(
            relative != root and root in relative.parents
            for root in proof_roots
        ):
            _fail(
                where,
                "raster-audit proof must be below reports/proofs or "
                "build/imagegen-audit",
            )
        if relative in seen:
            _fail(where, f"duplicate raster-audit proof path: {relative}")
        seen.add(relative)
        expected_hash = _lower_sha256(
            record["sha256"], where=f"{where}.sha256"
        )
        proof_path = _resolve_regular_file(
            project_root,
            relative,
            where=f"{where}.path",
        )
        if sha256_path(proof_path) != expected_hash:
            _fail(where, "raster-audit proof hash mismatch")


def _validate_raster_audit(
    path: Path,
    *,
    project_root: Path,
    batch: RepertoireBatch,
    raster_relative: PurePosixPath,
    raster_sha256: str,
) -> None:
    payload = _read_json_object(path, label="raster audit")
    if payload.get("schema_version") != 1:
        _fail(path, "schema_version must be 1")
    _audit_summary_is_all_pass(payload, path=path)
    _validate_declared_raster_audit_proofs(
        payload,
        path=path,
        project_root=project_root,
    )
    raw_batches = payload.get("batches")
    if not isinstance(raw_batches, list):
        _fail(path, "batches must be an array")
    selected = [
        item
        for item in raw_batches
        if isinstance(item, dict) and item.get("batch_id") == batch.batch_id
    ]
    if len(selected) != 1:
        _fail(path, f"must contain exactly one {batch.batch_id} batch record")
    batch_record = selected[0]
    expected_string = "".join(batch.characters)
    expected_raster = raster_relative.as_posix()
    if batch_record.get("start_rank") != batch.start_rank:
        _fail(path, "audit batch start_rank mismatch")
    if batch_record.get("end_rank") != batch.end_rank:
        _fail(path, "audit batch end_rank mismatch")
    if batch_record.get("characters") != expected_string:
        _fail(path, "audit batch characters mismatch")
    if batch_record.get("raster") != expected_raster:
        _fail(path, "audit batch raster path mismatch")
    if batch_record.get("sha256") != raster_sha256:
        _fail(path, "audit batch raster hash mismatch")

    if "report_id" in payload and "glyphs" not in payload:
        if batch_record.get("status") != "PASS":
            _fail(path, "nested audit batch status must be PASS")
        raw_glyphs = batch_record.get("glyphs")
        if not isinstance(raw_glyphs, list):
            _fail(path, "nested audit batch glyphs must be an array")
        if len(raw_glyphs) != len(batch.characters):
            _fail(path, "nested audit batch glyph count mismatch")
        for offset, (raw, character) in enumerate(
            zip(raw_glyphs, batch.characters), start=1
        ):
            where = f"{path}: {batch.batch_id} glyph {offset}"
            if not isinstance(raw, dict):
                _fail(where, "must be an object")
            if raw.get("cell") != offset:
                _fail(where, "cell index mismatch")
            if raw.get("rank") != batch.start_rank + offset - 1:
                _fail(where, "rank mismatch")
            if raw.get("character") != character:
                _fail(where, "character mismatch")
            if raw.get("codepoint") != f"U+{ord(character):04X}":
                _fail(where, "codepoint mismatch")
            for key in ("identity", "taiwan_topology", "no_spikes", "status"):
                if raw.get(key) != "PASS":
                    _fail(where, f"{key} must be PASS")
            legibility = raw.get("legibility_px")
            if legibility != {"128": "PASS", "64": "PASS", "32": "PASS"}:
                _fail(where, "128/64/32 legibility must all PASS")
            if raw.get("regeneration_prompt") is not None:
                _fail(where, "regeneration_prompt must be null")
    else:
        if batch_record.get("pass") != len(batch.characters):
            _fail(path, "flat audit batch pass count mismatch")
        if batch_record.get("reject") != 0:
            _fail(path, "flat audit batch reject count must be zero")
        raw_glyphs = payload.get("glyphs")
        assert isinstance(raw_glyphs, list)
        selected_glyphs = [
            item
            for item in raw_glyphs
            if isinstance(item, dict) and item.get("batch_id") == batch.batch_id
        ]
        if len(selected_glyphs) != len(batch.characters):
            _fail(path, "flat audit does not contain every batch glyph")
        selected_glyphs.sort(key=lambda item: item.get("index", -1))
        for offset, (raw, character) in enumerate(
            zip(selected_glyphs, batch.characters), start=1
        ):
            where = f"{path}: {batch.batch_id} glyph {offset}"
            if raw.get("index") != offset:
                _fail(where, "index mismatch")
            if raw.get("rank") != batch.start_rank + offset - 1:
                _fail(where, "rank mismatch")
            if raw.get("character") != character:
                _fail(where, "character mismatch")
            if raw.get("codepoint") != f"U+{ord(character):04X}":
                _fail(where, "codepoint mismatch")
            if raw.get("decision") != "PASS":
                _fail(where, "decision must be PASS")
            readability = raw.get("readability")
            if readability != {
                "native": "PASS",
                "128px": "PASS",
                "64px": "PASS",
                "32px": "PASS",
            }:
                _fail(where, "native/128/64/32 readability must all PASS")
            if raw.get("issues") != []:
                _fail(where, "issues must be empty")
            if raw.get("regeneration_prompt", None) is not None:
                _fail(where, "regeneration_prompt must be null when present")


def _artifact_path(
    build_directory: Path,
    relative_value: Any,
    *,
    where: str,
) -> tuple[PurePosixPath, Path]:
    relative = _relative_posix_path(relative_value, where=where)
    path = build_directory.joinpath(*relative.parts)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ImagegenApprovalError(
            f"{where}: vector artifact does not resolve: {exc}"
        ) from exc
    try:
        resolved.relative_to(build_directory.resolve())
    except ValueError:
        _fail(where, "vector artifact escapes its build directory")
    if not resolved.is_file():
        _fail(where, "vector artifact is not a regular file")
    return relative, resolved


def _actual_artifact_hashes(build_directory: Path) -> dict[str, str]:
    actual: dict[str, str] = {}
    for path in sorted(build_directory.rglob("*")):
        if path.is_symlink():
            _fail(build_directory, f"symlink artifact is forbidden: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(build_directory).as_posix()
        if relative == "report.json":
            continue
        if path.name.endswith(".pgm"):
            _fail(build_directory, f"temporary trace artifact remains: {relative}")
        actual[relative] = sha256_path(path)
    return actual


def _validate_batch_font(
    path: Path,
    *,
    batch: RepertoireBatch,
    expected_upm: int,
    expected_advance: int,
) -> None:
    try:
        font = TTFont(path, recalcTimestamp=False)
    except Exception as exc:
        raise ImagegenApprovalError(f"{path}: cannot open vector font: {exc}") from exc
    try:
        if "glyf" not in font or "CFF " in font or "CFF2" in font:
            _fail(path, "must be a quadratic glyf OpenType font")
        if font["head"].unitsPerEm != expected_upm:
            _fail(path, "unitsPerEm mismatch")
        expected_names = [
            "uni" + f"{ord(character):04X}"
            if ord(character) <= 0xFFFF
            else "u" + f"{ord(character):05X}"
            for character in batch.characters
        ]
        expected_cmap = {
            ord(character): name
            for character, name in zip(batch.characters, expected_names)
        }
        if font.getBestCmap() != expected_cmap:
            _fail(path, "cmap does not exactly match frozen batch")
        if font.getGlyphOrder() != [".notdef", *expected_names]:
            _fail(path, "glyph order does not exactly match frozen rank order")
        for name in expected_names:
            glyph = font["glyf"][name]
            if glyph.isComposite() or glyph.numberOfContours <= 0:
                _fail(path, f"{name} must be a non-empty simple glyph")
            advance, _ = font["hmtx"].metrics[name]
            if advance != expected_advance:
                _fail(path, f"{name} advance must be {expected_advance}")
    finally:
        font.close()


def _validate_vector_report(
    path: Path,
    *,
    project_root: Path,
    batch: RepertoireBatch,
    descriptor_sha256: str,
    raster_sha256: str,
) -> tuple[dict[str, Any], Path, Path]:
    from scripts.imagegen_derived_artifacts import (
        DerivedArtifactError,
        ensure_materialized,
    )

    try:
        ensure_materialized(path, project_root=project_root)
    except DerivedArtifactError as exc:
        _fail(path, str(exc))
    payload = _read_json_object(path, label="vector report")
    build_directory = path.parent.resolve()
    expected_build_relative = PurePosixPath(
        f"build/imagegen/{batch.descriptor_batch_id}"
    )
    expected_build_directory = project_root.resolve().joinpath(
        *expected_build_relative.parts
    )
    if build_directory != expected_build_directory.resolve():
        _fail(path, f"must be below {expected_build_relative}")
    if payload.get("schema_version") != 1:
        _fail(path, "schema_version must be 1")
    if payload.get("pipeline") != VECTOR_PIPELINE:
        _fail(path, f"pipeline must be exactly {VECTOR_PIPELINE!r}")
    if payload.get("approval_state") != "unreviewed":
        _fail(path, "vector report must remain unreviewed")
    if payload.get("batch_id") != batch.descriptor_batch_id:
        _fail(path, "vector report batch_id mismatch")
    if payload.get("source_descriptor_sha256") != descriptor_sha256:
        _fail(path, "source descriptor hash mismatch")
    if payload.get("source_state") != "generated-unreviewed":
        _fail(path, "source_state must remain generated-unreviewed")
    if payload.get("source_review") != {
        "topology": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }:
        _fail(path, "source_review must remain exactly pending")
    if payload.get("source_raster_sha256") != raster_sha256:
        _fail(path, "source raster hash mismatch")
    if payload.get("characters") != list(batch.characters):
        _fail(path, "vector characters do not match frozen repertoire")

    grid = payload.get("grid")
    if not isinstance(grid, dict):
        _fail(path, "vector grid must be an object")
    if grid.get("rows") != 4 or grid.get("columns") != 4:
        _fail(path, "vector grid must be 4 by 4")
    if grid.get("empty_grid_cells") != batch.empty_grid_cells:
        _fail(path, "vector empty-grid count mismatch")
    expected_slots = [*batch.characters, *([None] * batch.empty_grid_cells)]
    if grid.get("cell_slots") != expected_slots:
        _fail(path, "vector cell slots do not match exact row-major batch")
    if grid.get("synthesized_coordinates") is not False:
        _fail(path, "synthesized grid coordinates are forbidden")

    raw_artifacts = payload.get("artifact_sha256")
    if not isinstance(raw_artifacts, dict) or not raw_artifacts:
        _fail(path, "artifact_sha256 must be a non-empty object")
    reported_artifacts: dict[str, str] = {}
    for raw_relative, raw_hash in raw_artifacts.items():
        relative = _relative_posix_path(
            raw_relative, where=f"{path}: artifact_sha256 key"
        )
        normalized = relative.as_posix()
        if normalized in reported_artifacts:
            _fail(path, f"duplicate normalized artifact path: {normalized}")
        reported_artifacts[normalized] = _lower_sha256(
            raw_hash, where=f"{path}: artifact_sha256[{normalized!r}]"
        )
    actual_artifacts = _actual_artifact_hashes(build_directory)
    if actual_artifacts != reported_artifacts:
        missing = sorted(set(reported_artifacts) - set(actual_artifacts))
        extra = sorted(set(actual_artifacts) - set(reported_artifacts))
        mismatched = sorted(
            key
            for key in set(actual_artifacts) & set(reported_artifacts)
            if actual_artifacts[key] != reported_artifacts[key]
        )
        _fail(
            path,
            "vector artifact inventory mismatch; "
            f"missing={missing}, extra={extra}, hash_mismatch={mismatched}",
        )

    font_record = payload.get("font")
    if not isinstance(font_record, dict):
        _fail(path, "font must be an object")
    if font_record.get("units_per_em") != 1024:
        _fail(path, "font units_per_em must be 1024")
    if font_record.get("advance") != 1024:
        _fail(path, "font advance must be 1024")
    if font_record.get("cmap_count") != len(batch.characters):
        _fail(path, "font cmap_count mismatch")
    ttf_relative, ttf_path = _artifact_path(
        build_directory, font_record.get("ttf"), where=f"{path}: font.ttf"
    )
    otf_relative, otf_path = _artifact_path(
        build_directory, font_record.get("otf"), where=f"{path}: font.otf"
    )
    ttf_hash = _lower_sha256(
        font_record.get("ttf_sha256"), where=f"{path}: font.ttf_sha256"
    )
    otf_hash = _lower_sha256(
        font_record.get("otf_sha256"), where=f"{path}: font.otf_sha256"
    )
    if reported_artifacts.get(ttf_relative.as_posix()) != ttf_hash:
        _fail(path, "TTF hash is not pinned by artifact_sha256")
    if reported_artifacts.get(otf_relative.as_posix()) != otf_hash:
        _fail(path, "OTF hash is not pinned by artifact_sha256")
    if sha256_path(ttf_path) != ttf_hash or sha256_path(otf_path) != otf_hash:
        _fail(path, "font artifact hash mismatch")
    _validate_batch_font(
        ttf_path, batch=batch, expected_upm=1024, expected_advance=1024
    )
    _validate_batch_font(
        otf_path, batch=batch, expected_upm=1024, expected_advance=1024
    )

    raw_proofs = payload.get("proofs")
    proofs = _exact_keys(
        raw_proofs,
        {"black_on_white", "white_on_black", "segmented_source"},
        where=f"{path}: proofs",
    )
    for key in ("black_on_white", "white_on_black", "segmented_source"):
        relative, proof_path = _artifact_path(
            build_directory, proofs[key], where=f"{path}: proofs.{key}"
        )
        expected_hash = reported_artifacts.get(relative.as_posix())
        if expected_hash is None or sha256_path(proof_path) != expected_hash:
            _fail(path, f"proof {key} is not hash-pinned as an artifact")

    raw_glyphs = payload.get("glyphs")
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != len(batch.characters):
        _fail(path, "glyph report count mismatch")
    seen_names: set[str] = set()
    for offset, (raw, character) in enumerate(
        zip(raw_glyphs, batch.characters), start=1
    ):
        where = f"{path}: glyphs[{offset - 1}]"
        if not isinstance(raw, dict):
            _fail(where, "must be an object")
        codepoint = ord(character)
        expected_name = (
            f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"
        )
        if raw.get("character") != character:
            _fail(where, "character mismatch")
        if raw.get("codepoint") != f"U+{codepoint:04X}":
            _fail(where, "codepoint mismatch")
        if raw.get("glyph_name") != expected_name:
            _fail(where, "glyph_name mismatch")
        if expected_name in seen_names:
            _fail(where, "duplicate glyph name")
        seen_names.add(expected_name)
        if raw.get("row") != (offset - 1) // 4:
            _fail(where, "row mismatch")
        if raw.get("column") != (offset - 1) % 4:
            _fail(where, "column mismatch")
        if raw.get("micro_edge_count") != 0:
            _fail(where, "micro_edge_count must be zero")
        if raw.get("acute_micro_turn_count") != 0:
            _fail(where, "acute_micro_turn_count must be zero")
        minimum_edge = raw.get("minimum_control_edge")
        if not isinstance(minimum_edge, (int, float)) or minimum_edge < 1:
            _fail(where, "minimum_control_edge must be at least one unit")
        for path_key, hash_key in (
            ("source_png", "source_png_sha256"),
            ("svg", "svg_sha256"),
            ("proof_png", "proof_png_sha256"),
        ):
            relative, artifact_path = _artifact_path(
                build_directory, raw.get(path_key), where=f"{where}.{path_key}"
            )
            expected_hash = _lower_sha256(
                raw.get(hash_key), where=f"{where}.{hash_key}"
            )
            if reported_artifacts.get(relative.as_posix()) != expected_hash:
                _fail(where, f"{path_key} hash is absent from artifact manifest")
            if sha256_path(artifact_path) != expected_hash:
                _fail(where, f"{path_key} hash mismatch")

    raw_coverage = payload.get("small_size_coverage_pixels")
    if not isinstance(raw_coverage, dict):
        _fail(path, "small_size_coverage_pixels must be an object")
    expected_coverage_keys = {
        f"U+{ord(character):04X}" for character in batch.characters
    }
    if set(raw_coverage) != expected_coverage_keys:
        _fail(path, "small-size coverage codepoints mismatch")
    expected_sizes = {str(size) for size in SMALL_SIZE_PIXELS}
    for character in batch.characters:
        codepoint = f"U+{ord(character):04X}"
        per_size = raw_coverage[codepoint]
        if not isinstance(per_size, dict) or set(per_size) != expected_sizes:
            _fail(path, f"{codepoint} must cover exactly {SMALL_SIZE_PIXELS}")
        for size in SMALL_SIZE_PIXELS:
            coverage = per_size[str(size)]
            if (
                not isinstance(coverage, int)
                or isinstance(coverage, bool)
                or coverage < max(2, size // 6)
            ):
                _fail(
                    path,
                    f"{codepoint} has insufficient {size}px coverage: {coverage!r}",
                )
    return payload, ttf_path, otf_path


def _validate_visual_review(
    path: Path,
    *,
    project_root: Path,
    batch: RepertoireBatch,
    vector_report_relative: PurePosixPath,
    vector_report_sha256: str,
    vector_report: Mapping[str, Any],
) -> tuple[str, str]:
    payload = _read_json_object(path, label="vector visual review")
    top = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "review_state",
            "batch_id",
            "reviewer",
            "reviewed_at",
            "vector_report",
            "scope",
            "proofs",
            "glyphs",
            "summary",
        },
        where=str(path),
    )
    if top["schema_version"] != APPROVAL_SCHEMA_VERSION:
        _fail(path, f"schema_version must be {APPROVAL_SCHEMA_VERSION}")
    if top["record_type"] != VISUAL_REVIEW_RECORD_TYPE:
        _fail(path, f"record_type must be {VISUAL_REVIEW_RECORD_TYPE!r}")
    if top["review_state"] != "approved":
        _fail(path, "review_state must be approved")
    if top["batch_id"] != batch.batch_id:
        _fail(path, "batch_id mismatch")
    reviewer = _exact_keys(
        top["reviewer"], {"name", "role"}, where=f"{path}: reviewer"
    )
    reviewer_name = _nonempty_string(
        reviewer["name"], where=f"{path}: reviewer.name"
    )
    _nonempty_string(reviewer["role"], where=f"{path}: reviewer.role")
    reviewed_at = _require_rfc3339_utc(
        top["reviewed_at"], where=f"{path}: reviewed_at"
    )
    report_ref = _exact_keys(
        top["vector_report"], {"path", "sha256"}, where=f"{path}: vector_report"
    )
    if _relative_posix_path(
        report_ref["path"], where=f"{path}: vector_report.path"
    ) != vector_report_relative:
        _fail(path, "visual review references the wrong vector report")
    if _lower_sha256(
        report_ref["sha256"], where=f"{path}: vector_report.sha256"
    ) != vector_report_sha256:
        _fail(path, "visual review vector report hash mismatch")

    scope = _exact_keys(
        top["scope"],
        {
            "all_glyphs_reviewed",
            "checks",
            "sizes_px",
            "polarities",
        },
        where=f"{path}: scope",
    )
    if scope["all_glyphs_reviewed"] is not True:
        _fail(path, "scope.all_glyphs_reviewed must be true")
    if scope["checks"] != list(VISUAL_CHECKS):
        _fail(path, f"scope.checks must be exactly {list(VISUAL_CHECKS)!r}")
    if scope["sizes_px"] != list(SMALL_SIZE_PIXELS):
        _fail(path, f"scope.sizes_px must be exactly {list(SMALL_SIZE_PIXELS)!r}")
    if scope["polarities"] != list(VISUAL_POLARITIES):
        _fail(path, f"scope.polarities must be exactly {list(VISUAL_POLARITIES)!r}")

    build_directory = project_root.resolve() / "build/imagegen" / batch.descriptor_batch_id
    artifact_hashes = vector_report.get("artifact_sha256")
    assert isinstance(artifact_hashes, dict)
    report_proofs = vector_report.get("proofs")
    assert isinstance(report_proofs, dict)
    expected_proofs = {
        "black-on-white": report_proofs["black_on_white"],
        "white-on-black": report_proofs["white_on_black"],
        "segmented-source": report_proofs["segmented_source"],
    }
    raw_proofs = top["proofs"]
    if not isinstance(raw_proofs, list) or len(raw_proofs) != len(
        VISUAL_PROOF_KINDS
    ):
        _fail(path, "proofs must contain exactly the three required proofs")
    proof_by_kind: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(raw_proofs):
        record = _exact_keys(
            raw,
            {"kind", "path", "sha256", "decision"},
            where=f"{path}: proofs[{index}]",
        )
        kind = record["kind"]
        if kind not in VISUAL_PROOF_KINDS or kind in proof_by_kind:
            _fail(path, f"invalid or duplicate visual proof kind: {kind!r}")
        proof_by_kind[str(kind)] = record
    if set(proof_by_kind) != set(VISUAL_PROOF_KINDS):
        _fail(path, "visual proof kinds mismatch")
    for kind in VISUAL_PROOF_KINDS:
        record = proof_by_kind[kind]
        expected_artifact_relative = PurePosixPath(expected_proofs[kind])
        expected_project_relative = PurePosixPath(
            "build/imagegen",
            batch.descriptor_batch_id,
            *expected_artifact_relative.parts,
        )
        relative = _relative_posix_path(
            record["path"], where=f"{path}: proof {kind}.path"
        )
        if relative != expected_project_relative:
            _fail(path, f"visual proof {kind} path mismatch")
        expected_hash = artifact_hashes.get(expected_artifact_relative.as_posix())
        if expected_hash is None:
            _fail(path, f"visual proof {kind} is absent from artifact manifest")
        if record["sha256"] != expected_hash:
            _fail(path, f"visual proof {kind} hash mismatch")
        _, proof_path = _artifact_path(
            build_directory,
            expected_artifact_relative.as_posix(),
            where=f"{path}: proof {kind}",
        )
        if sha256_path(proof_path) != expected_hash:
            _fail(path, f"visual proof {kind} file hash mismatch")
        if record["decision"] != "PASS":
            _fail(path, f"visual proof {kind} decision must be PASS")

    raw_glyphs = top["glyphs"]
    if not isinstance(raw_glyphs, list) or len(raw_glyphs) != len(batch.characters):
        _fail(path, "visual glyph decisions must cover the whole batch")
    for offset, (raw, character) in enumerate(
        zip(raw_glyphs, batch.characters), start=1
    ):
        record = _exact_keys(
            raw,
            {"rank", "character", "decision", "notes"},
            where=f"{path}: glyphs[{offset - 1}]",
        )
        if record["rank"] != batch.start_rank + offset - 1:
            _fail(path, f"visual glyph {offset} rank mismatch")
        if record["character"] != character:
            _fail(path, f"visual glyph {offset} character mismatch")
        if record["decision"] != "PASS":
            _fail(path, f"visual glyph {offset} decision must be PASS")
        if not isinstance(record["notes"], str):
            _fail(path, f"visual glyph {offset} notes must be a string")

    summary = _exact_keys(
        top["summary"],
        {"glyph_count", "pass_count", "reject_count", "rejected_characters"},
        where=f"{path}: summary",
    )
    count = len(batch.characters)
    if summary["glyph_count"] != count or summary["pass_count"] != count:
        _fail(path, "visual summary counts do not cover all glyphs")
    if summary["reject_count"] != 0 or summary["rejected_characters"] != []:
        _fail(path, "visual summary must have zero rejects")
    return reviewer_name, reviewed_at


def validate_approval(
    approval_path: Path,
    *,
    project_root: Path = ROOT,
    repertoire: Repertoire | None = None,
) -> ValidatedApproval:
    """Validate one approval and every byte of evidence it references."""

    project_root = project_root.resolve()
    repertoire = repertoire or load_frozen_repertoire(project_root)
    approval_path = approval_path.resolve()
    try:
        relative_approval = approval_path.relative_to(project_root)
    except ValueError:
        _fail(approval_path, "approval must remain below project root")
    expected_parent = PurePosixPath("sources/imagegen/approvals")
    relative_parent = PurePosixPath(relative_approval.parent.as_posix())
    if relative_parent != expected_parent:
        _fail(
            approval_path,
            f"approval must be directly below {expected_parent.as_posix()}",
        )
    if approval_path.is_symlink() or not approval_path.is_file():
        _fail(approval_path, "approval must be a regular non-symlink file")
    payload = _read_json_object(approval_path, label="approval")
    top = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "approval_state",
            "batch_id",
            "repertoire",
            "source",
            "raster_audit",
            "vector_build",
            "vector_visual_review",
            "authorization",
        },
        where=str(approval_path),
    )
    if top["schema_version"] != APPROVAL_SCHEMA_VERSION:
        _fail(
            approval_path,
            f"schema_version must be {APPROVAL_SCHEMA_VERSION}",
        )
    if top["record_type"] != APPROVAL_RECORD_TYPE:
        _fail(
            approval_path, f"record_type must be {APPROVAL_RECORD_TYPE!r}"
        )
    if top["approval_state"] != "approved":
        _fail(approval_path, "approval_state must be approved")
    batch_id, number = _canonical_batch_id(
        top["batch_id"], where=f"{approval_path}: batch_id"
    )
    batch = repertoire.batches[number - 1]
    if batch.batch_id != batch_id:
        _fail(approval_path, "batch_id does not match frozen repertoire")
    expected_filename = f"{batch.batch_id}.approval.json"
    if approval_path.name != expected_filename:
        _fail(approval_path, f"filename must be {expected_filename!r}")
    _validate_approval_repertoire(
        top["repertoire"],
        repertoire=repertoire,
        batch=batch,
        where=f"{approval_path}: repertoire",
    )

    source = _exact_keys(
        top["source"],
        {
            "descriptor",
            "descriptor_sha256",
            "raster",
            "raster_sha256",
        },
        where=f"{approval_path}: source",
    )
    expected_descriptor_relative = PurePosixPath(
        f"sources/imagegen/batches/{batch.batch_id}.source.json"
    )
    descriptor_relative = _relative_posix_path(
        source["descriptor"], where=f"{approval_path}: source.descriptor"
    )
    if descriptor_relative != expected_descriptor_relative:
        _fail(approval_path, "source descriptor path mismatch")
    descriptor_sha256 = _lower_sha256(
        source["descriptor_sha256"],
        where=f"{approval_path}: source.descriptor_sha256",
    )
    descriptor_path = _resolve_regular_file(
        project_root,
        descriptor_relative,
        where=f"{approval_path}: source.descriptor",
    )
    if sha256_path(descriptor_path) != descriptor_sha256:
        _fail(approval_path, "source descriptor hash mismatch")
    expected_raster_relative = PurePosixPath(
        f"sources/imagegen/raster/{batch.batch_id}.png"
    )
    raster_relative = _relative_posix_path(
        source["raster"], where=f"{approval_path}: source.raster"
    )
    if raster_relative != expected_raster_relative:
        _fail(approval_path, "source raster path mismatch")
    raster_path, raster_sha256 = _validate_source_descriptor(
        descriptor_path,
        expected_hash=descriptor_sha256,
        project_root=project_root,
        batch=batch,
        approval_source=source,
    )

    audit_reference = _exact_keys(
        top["raster_audit"],
        {"report", "report_sha256"},
        where=f"{approval_path}: raster_audit",
    )
    audit_relative = _relative_posix_path(
        audit_reference["report"],
        where=f"{approval_path}: raster_audit.report",
    )
    if AUDIT_PATH_PATTERN.fullmatch(audit_relative.as_posix()) is None:
        _fail(approval_path, "raster audit path is not canonical")
    audit_sha256 = _lower_sha256(
        audit_reference["report_sha256"],
        where=f"{approval_path}: raster_audit.report_sha256",
    )
    audit_path = _resolve_regular_file(
        project_root,
        audit_relative,
        where=f"{approval_path}: raster_audit.report",
    )
    if sha256_path(audit_path) != audit_sha256:
        _fail(approval_path, "raster audit hash mismatch")
    _validate_raster_audit(
        audit_path,
        project_root=project_root,
        batch=batch,
        raster_relative=raster_relative,
        raster_sha256=raster_sha256,
    )

    vector_reference = _exact_keys(
        top["vector_build"],
        {"report", "report_sha256", "pipeline"},
        where=f"{approval_path}: vector_build",
    )
    expected_vector_relative = PurePosixPath(
        f"build/imagegen/{batch.descriptor_batch_id}/report.json"
    )
    vector_relative = _relative_posix_path(
        vector_reference["report"],
        where=f"{approval_path}: vector_build.report",
    )
    if vector_relative != expected_vector_relative:
        _fail(approval_path, "vector report path mismatch")
    vector_report_sha256 = _lower_sha256(
        vector_reference["report_sha256"],
        where=f"{approval_path}: vector_build.report_sha256",
    )
    if vector_reference["pipeline"] != VECTOR_PIPELINE:
        _fail(approval_path, f"vector pipeline must be {VECTOR_PIPELINE!r}")
    vector_report_path = _resolve_regular_file(
        project_root,
        vector_relative,
        where=f"{approval_path}: vector_build.report",
    )
    if sha256_path(vector_report_path) != vector_report_sha256:
        _fail(approval_path, "vector report hash mismatch")
    vector_report, ttf_path, otf_path = _validate_vector_report(
        vector_report_path,
        project_root=project_root,
        batch=batch,
        descriptor_sha256=descriptor_sha256,
        raster_sha256=raster_sha256,
    )

    visual_reference = _exact_keys(
        top["vector_visual_review"],
        {"record", "record_sha256"},
        where=f"{approval_path}: vector_visual_review",
    )
    expected_visual_relative = PurePosixPath(
        f"sources/imagegen/vector-reviews/{batch.batch_id}.vector-review.json"
    )
    visual_relative = _relative_posix_path(
        visual_reference["record"],
        where=f"{approval_path}: vector_visual_review.record",
    )
    if visual_relative != expected_visual_relative:
        _fail(approval_path, "vector visual-review path mismatch")
    visual_review_sha256 = _lower_sha256(
        visual_reference["record_sha256"],
        where=f"{approval_path}: vector_visual_review.record_sha256",
    )
    visual_review_path = _resolve_regular_file(
        project_root,
        visual_relative,
        where=f"{approval_path}: vector_visual_review.record",
    )
    if sha256_path(visual_review_path) != visual_review_sha256:
        _fail(approval_path, "vector visual-review hash mismatch")
    reviewer_name, reviewed_at = _validate_visual_review(
        visual_review_path,
        project_root=project_root,
        batch=batch,
        vector_report_relative=vector_relative,
        vector_report_sha256=vector_report_sha256,
        vector_report=vector_report,
    )

    authorization = _exact_keys(
        top["authorization"],
        {"decision", "approver", "approved_at"},
        where=f"{approval_path}: authorization",
    )
    if authorization["decision"] != "APPROVED":
        _fail(approval_path, "authorization.decision must be APPROVED")
    approver_name = _nonempty_string(
        authorization["approver"],
        where=f"{approval_path}: authorization.approver",
    )
    approved_at = _require_rfc3339_utc(
        authorization["approved_at"],
        where=f"{approval_path}: authorization.approved_at",
    )
    if approved_at < reviewed_at:
        _fail(approval_path, "final approval cannot predate visual review")

    return ValidatedApproval(
        approval_path=approval_path,
        approval_sha256=sha256_path(approval_path),
        batch=batch,
        repertoire=repertoire,
        descriptor_path=descriptor_path,
        descriptor_sha256=descriptor_sha256,
        raster_path=raster_path,
        raster_sha256=raster_sha256,
        audit_path=audit_path,
        audit_sha256=audit_sha256,
        vector_report_path=vector_report_path,
        vector_report_sha256=vector_report_sha256,
        vector_build_directory=vector_report_path.parent,
        vector_report=vector_report,
        visual_review_path=visual_review_path,
        visual_review_sha256=visual_review_sha256,
        reviewer_name=reviewer_name,
        reviewed_at=reviewed_at,
        approver_name=approver_name,
        approved_at=approved_at,
        ttf_path=ttf_path,
        otf_path=otf_path,
    )


def validate_approval_prefix(
    approval_paths: Sequence[Path],
    *,
    project_root: Path = ROOT,
) -> tuple[ValidatedApproval, ...]:
    """Validate approvals and require an exact rank prefix starting at batch 1."""

    if not approval_paths:
        _fail("approval prefix", "at least one approval record is required")
    repertoire = load_frozen_repertoire(project_root)
    validated = [
        validate_approval(
            path, project_root=project_root, repertoire=repertoire
        )
        for path in approval_paths
    ]
    by_number: dict[int, ValidatedApproval] = {}
    for approval in validated:
        number = approval.batch.number
        if number in by_number:
            _fail(
                "approval prefix",
                f"duplicate approval for {approval.batch.batch_id}",
            )
        by_number[number] = approval
    expected_numbers = list(range(1, len(by_number) + 1))
    actual_numbers = sorted(by_number)
    if actual_numbers != expected_numbers:
        _fail(
            "approval prefix",
            "approved batches must be the exact contiguous prefix "
            f"common-0001..common-{len(by_number):04d}; got {actual_numbers}",
        )
    ordered = tuple(by_number[number] for number in expected_numbers)
    characters = [
        character
        for approval in ordered
        for character in approval.characters
    ]
    if len(set(characters)) != len(characters):
        _fail("approval prefix", "approved batches contain duplicate characters")
    expected_prefix = repertoire.characters[: len(characters)]
    if tuple(characters) != expected_prefix:
        _fail("approval prefix", "approved glyph sequence is not the frozen rank prefix")
    repertoire_hashes = {approval.repertoire.sha256 for approval in ordered}
    if repertoire_hashes != {repertoire.sha256}:
        _fail("approval prefix", "approvals pin different repertoire files")
    return ordered


def discover_approval_paths(
    directory: Path,
    *,
    project_root: Path = ROOT,
) -> tuple[Path, ...]:
    """Return canonical Han approvals from the shared approval directory.

    Canonically named non-Han, vertical, and collection approvals may coexist
    in the same directory; every other JSON filename remains a hard error.
    """

    directory = directory.resolve()
    expected = (
        project_root.resolve() / "sources/imagegen/approvals"
    ).resolve()
    if directory != expected:
        _fail(directory, f"approval directory must be exactly {expected}")
    if not directory.is_dir():
        _fail(directory, "approval directory does not exist")
    paths = tuple(
        sorted(
            directory.glob(
                "common-[0-9][0-9][0-9][0-9].approval.json"
            )
        )
    )
    nonhan_paths = set(
        directory.glob(
            "nonhan-[0-9][0-9][0-9][0-9].approval.json"
        )
    )
    vertical_paths = set(
        directory.glob(
            "vertical-[0-9][0-9][0-9][0-9].approval.json"
        )
    )
    collection_paths = {
        directory / "moe-common-extension.approval.json",
        directory / "dictionary-salience-extension-1216.approval.json",
    }
    extra_json = sorted(
        path.name
        for path in directory.glob("*.json")
        if (
            path not in paths
            and path not in nonhan_paths
            and path not in vertical_paths
            and path not in collection_paths
        )
    )
    if extra_json:
        _fail(directory, f"non-canonical JSON files are forbidden: {extra_json}")
    return paths


def _relative_to_root(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def _validation_summary(
    approval: ValidatedApproval,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "batch_id": approval.batch.batch_id,
        "start_rank": approval.batch.start_rank,
        "end_rank": approval.batch.end_rank,
        "character_count": len(approval.characters),
        "characters": "".join(approval.characters),
        "approval": {
            "path": _relative_to_root(approval.approval_path, project_root),
            "sha256": approval.approval_sha256,
        },
        "source_descriptor_sha256": approval.descriptor_sha256,
        "raster_sha256": approval.raster_sha256,
        "raster_audit_sha256": approval.audit_sha256,
        "vector_report_sha256": approval.vector_report_sha256,
        "vector_visual_review_sha256": approval.visual_review_sha256,
        "reviewer": approval.reviewer_name,
        "reviewed_at": approval.reviewed_at,
        "approver": approval.approver_name,
        "approved_at": approval.approved_at,
        "status": "APPROVED",
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root containing the pinned imagegen layout",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    one = subparsers.add_parser("validate", help="validate one approval record")
    one.add_argument("approval", type=Path)
    prefix = subparsers.add_parser(
        "validate-prefix",
        help="validate every approval in the canonical directory as a rank prefix",
    )
    prefix.add_argument(
        "--approvals",
        type=Path,
        help="defaults to sources/imagegen/approvals below project root",
    )
    prefix.add_argument(
        "--summary",
        action="store_true",
        help="print only the validated batch and glyph cardinality",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    if args.command == "validate":
        approval_path = args.approval
        if not approval_path.is_absolute():
            approval_path = project_root / approval_path
        approval = validate_approval(
            approval_path, project_root=project_root
        )
        print(
            json.dumps(
                _validation_summary(approval, project_root=project_root),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    directory = args.approvals or (
        project_root / "sources/imagegen/approvals"
    )
    if not directory.is_absolute():
        directory = project_root / directory
    approvals = validate_approval_prefix(
        discover_approval_paths(directory, project_root=project_root),
        project_root=project_root,
    )
    if args.summary:
        glyph_count = sum(len(item.characters) for item in approvals)
        print(
            f"validated {len(approvals)} Han approvals "
            f"covering {glyph_count} glyphs"
        )
        return 0
    print(
        json.dumps(
            {
                "status": "APPROVED_PREFIX",
                "batch_count": len(approvals),
                "glyph_count": sum(len(item.characters) for item in approvals),
                "last_batch": approvals[-1].batch.batch_id,
                "approvals": [
                    _validation_summary(item, project_root=project_root)
                    for item in approvals
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
