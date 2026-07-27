#!/usr/bin/env python3
"""Freeze and validate Mew Note TC family-local bulk-authoring inputs.

This tool deliberately stops before raster generation. It projects shared
Unicode identity data into a Mew Note TC repertoire namespace, assigns the
approved motif class to every visible glyph, and writes one exact plan whose
batch paths are derived from a verified ``FamilyContext``. It never reads a
Clear Hand raster, outline, review, approval, or build artifact.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence
import unicodedata

from scripts.font_family_context import (
    FamilyContext,
    FamilyContextError,
    canonical_json_sha256,
    load_family_context,
    sha256_path,
)


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ID = "mew-note-tc"
PIPELINE_ID = "original-raster-v1"
FAMILY_PATH = Path("families/mew-note-tc/family.json")
PIPELINE_PATH = Path("families/mew-note-tc/pipeline.json")
AUTHORING_PATH = Path("families/mew-note-tc/authoring.json")
COLLECTIONS_PATH = Path("families/mew-note-tc/collections.json")
MOTIF_PATH = Path("families/mew-note-tc/motif-contract.json")
PROMPT_TEMPLATE_PATH = Path("families/mew-note-tc/prompt-template.md")
PLAN_PATH = Path(
    "families/mew-note-tc/sources/imagegen/pipelines/"
    "original-raster-v1/batch-plan.json"
)
REPERTOIRE_ROOT = Path(
    "families/mew-note-tc/sources/imagegen/repertoires"
)
HAN_PATH = REPERTOIRE_ROOT / "han-6060.json"
NONHAN_PATH = REPERTOIRE_ROOT / "nonhan-3060.json"
VERTICAL_PATH = REPERTOIRE_ROOT / "vertical-93.json"

SHARED_HAN_SEGMENTS = (
    (
        "dictionary-salience-base-3000",
        Path("sources/imagegen/repertoires/common-3000.json"),
        "c9f965516bed2821cf137480bddf23acd043a339165571cf9b3e87bbf5ffc66a",
        3000,
    ),
    (
        "moe-common-extension-1844",
        Path("sources/imagegen/repertoires/moe-common-extension-1844.json"),
        "f5f8e22beb919617cfd95d40d15f745e921e6434e95866fc7f9b184495bb2652",
        1844,
    ),
    (
        "dictionary-salience-additional-1216",
        Path(
            "sources/imagegen/repertoires/"
            "dictionary-salience-extension-1216.json"
        ),
        "8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840",
        1216,
    ),
)
SHARED_NONHAN_PATH = Path(
    "sources/imagegen/repertoires/nonhan-3060.json"
)
SHARED_NONHAN_SHA256 = (
    "42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4"
)
SHARED_VERTICAL_PATH = Path(
    "sources/imagegen/repertoires/vertical-93.json"
)
SHARED_VERTICAL_SHA256 = (
    "5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786"
)

REPERTOIRE_RECORD_TYPE = "mew-note-tc-family-repertoire"
PLAN_RECORD_TYPE = "mew-note-tc-bulk-authoring-plan"
PLAN_SCHEMA_VERSION = 1
GRID_ROWS = 4
GRID_COLUMNS = 4
GRID_CAPACITY = GRID_ROWS * GRID_COLUMNS
TARGET_HAN = 6060
TARGET_NONHAN = 3060
TARGET_ENCODED = 9120
TARGET_VISIBLE = 9103
TARGET_SEMANTIC_EMPTY = 17
TARGET_VERTICAL = 93
REQUIREMENTS_DENOMINATOR = 18071
REQUIRED_HIRAGANA = 93
REQUIRED_KATAKANA = 96
TAIL_PERIOD = 4
TAIL_PHASE = 2
MOTIF_CLASSES = {
    "tail-terminal",
    "soft-terminal",
    "neutral-safety",
}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
CODEPOINT_PATTERN = re.compile(r"U\+[0-9A-F]{4,6}")

NONHAN_TAIL_ELIGIBLE_GROUP_PREFIXES = (
    "P00-",
    "P01-",
    "P10-",
    "P11-",
    "P14-",
    "P18-",
    "P19-",
    "P30-",
    "P31-",
    "P32-",
    "P33-",
    "P34-",
    "P40-",
    "P41-",
)
NONHAN_NEUTRAL_PROFILE_IDS = {
    "block-element",
    "box-drawing",
    "nonspacing-mark",
}


class MewNoteBulkError(RuntimeError):
    """A Mew Note TC bulk-authoring contract is incomplete or stale."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteBulkError(f"{path}: cannot read JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise MewNoteBulkError(f"{path}: expected a JSON object")
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _json_bytes(value)
    if path.exists() and path.read_bytes() == data:
        return
    path.write_bytes(data)


def _project_root(project_root: Path) -> Path:
    try:
        resolved = project_root.resolve(strict=True)
    except OSError as exc:
        raise MewNoteBulkError("project root does not exist") from exc
    if not resolved.is_dir():
        raise MewNoteBulkError("project root is not a directory")
    return resolved


def _relative(path: Path) -> str:
    return path.as_posix()


def _require_hash(
    project_root: Path,
    path: Path,
    expected: str,
    *,
    label: str,
) -> None:
    if SHA256_PATTERN.fullmatch(expected) is None:
        raise MewNoteBulkError(f"{label}: invalid expected SHA-256")
    absolute = project_root / path
    if not absolute.is_file():
        raise MewNoteBulkError(f"{label}: missing {path.as_posix()}")
    if absolute.is_symlink():
        raise MewNoteBulkError(f"{label}: symlinks are forbidden")
    actual = sha256_path(absolute)
    if actual != expected:
        raise MewNoteBulkError(
            f"{label}: SHA-256 mismatch for {path.as_posix()}"
        )


def _codepoint_label(codepoint: int) -> str:
    if not 0 <= codepoint <= 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
        raise MewNoteBulkError(f"invalid Unicode scalar: {codepoint}")
    return f"U+{codepoint:04X}"


def _codepoint_lines(codepoints: Iterable[int]) -> bytes:
    return "".join(
        f"{_codepoint_label(codepoint)}\n" for codepoint in codepoints
    ).encode("ascii")


def _characters_hash(codepoints: Iterable[int]) -> str:
    return hashlib.sha256(
        "".join(chr(codepoint) for codepoint in codepoints).encode("utf-8")
    ).hexdigest()


def _batch_records(
    records: Sequence[Mapping[str, Any]],
    *,
    prefix: str,
    rank_key: str,
    codepoint_key: str,
) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    for index, start in enumerate(
        range(0, len(records), GRID_CAPACITY),
        start=1,
    ):
        chunk = records[start : start + GRID_CAPACITY]
        codepoints = [int(record[codepoint_key]) for record in chunk]
        batches.append(
            {
                "batch_id": f"{prefix}-{index:04d}",
                "start_rank": int(chunk[0][rank_key]),
                "end_rank": int(chunk[-1][rank_key]),
                "character_count": len(chunk),
                "grid_capacity": GRID_CAPACITY,
                "empty_grid_cells": GRID_CAPACITY - len(chunk),
                "characters": "".join(
                    chr(codepoint) for codepoint in codepoints
                ),
                "codepoints": [
                    _codepoint_label(codepoint)
                    for codepoint in codepoints
                ],
            }
        )
    return batches


def build_han_repertoire(project_root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    seen: set[int] = set()
    for segment_id, relative, expected_hash, expected_count in (
        SHARED_HAN_SEGMENTS
    ):
        _require_hash(
            project_root,
            relative,
            expected_hash,
            label=segment_id,
        )
        source = _read_object(project_root / relative)
        raw_records = source.get("characters")
        if (
            not isinstance(raw_records, list)
            or len(raw_records) != expected_count
        ):
            raise MewNoteBulkError(
                f"{segment_id}: expected {expected_count} identities"
            )
        for source_rank, raw in enumerate(raw_records, start=1):
            if not isinstance(raw, dict):
                raise MewNoteBulkError(
                    f"{segment_id}: character {source_rank} is not an object"
                )
            character = raw.get("character")
            codepoint = raw.get("codepoint")
            if (
                not isinstance(character, str)
                or len(character) != 1
                or not isinstance(codepoint, int)
                or ord(character) != codepoint
            ):
                raise MewNoteBulkError(
                    f"{segment_id}: invalid identity at rank {source_rank}"
                )
            if codepoint in seen:
                raise MewNoteBulkError(
                    f"{segment_id}: duplicate {_codepoint_label(codepoint)}"
                )
            seen.add(codepoint)
            records.append(
                {
                    "rank": len(records) + 1,
                    "character": character,
                    "codepoint": codepoint,
                    "unicode": _codepoint_label(codepoint),
                    "unicode_name": str(
                        raw.get(
                            "unicode_name",
                            unicodedata.name(character, "<UNNAMED>"),
                        )
                    ),
                    "identity_source": {
                        "segment_id": segment_id,
                        "source_rank": int(raw.get("rank", source_rank)),
                    },
                }
            )
        sources.append(
            {
                "segment_id": segment_id,
                "path": _relative(relative),
                "sha256": expected_hash,
                "identity_count": expected_count,
                "role": (
                    "unicode-identity-and-order-only-no-raster-outline-"
                    "review-approval-reuse"
                ),
            }
        )
    if len(records) != TARGET_HAN:
        raise MewNoteBulkError(
            f"Han projection has {len(records)} records, expected {TARGET_HAN}"
        )
    codepoints = [int(record["codepoint"]) for record in records]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "record_type": REPERTOIRE_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "repertoire_id": "mew-note-tc-han-6060-v1",
        "normalization": "none",
        "counts": {
            "encoded": TARGET_HAN,
            "visible": TARGET_HAN,
            "semantic_empty": 0,
            "batches": (TARGET_HAN + GRID_CAPACITY - 1)
            // GRID_CAPACITY,
        },
        "ordering": (
            "Three exact hash-pinned identity segments in declared order; "
            "no normalization or character substitution"
        ),
        "identity_sources": sources,
        "sequence": {
            "serialization": "ascii-uppercase-codepoint-lines-v1",
            "sha256": hashlib.sha256(
                _codepoint_lines(codepoints)
            ).hexdigest(),
            "characters_sha256": _characters_hash(codepoints),
        },
        "glyphs": records,
        "batches": _batch_records(
            records,
            prefix="han",
            rank_key="rank",
            codepoint_key="codepoint",
        ),
    }
    return payload


def build_nonhan_repertoire(project_root: Path) -> dict[str, Any]:
    _require_hash(
        project_root,
        SHARED_NONHAN_PATH,
        SHARED_NONHAN_SHA256,
        label="shared non-Han repertoire",
    )
    source = _read_object(project_root / SHARED_NONHAN_PATH)
    glyphs = source.get("glyphs")
    batches = source.get("batches")
    counts = source.get("counts")
    if (
        not isinstance(glyphs, list)
        or len(glyphs) != TARGET_NONHAN
        or not isinstance(batches, list)
        or len(batches) != 206
        or not isinstance(counts, dict)
        or counts.get("outline_required") != 3043
        or counts.get("semantic_empty") != TARGET_SEMANTIC_EMPTY
    ):
        raise MewNoteBulkError("shared non-Han repertoire shape changed")
    projected: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, raw in enumerate(glyphs, start=1):
        if not isinstance(raw, dict):
            raise MewNoteBulkError(f"non-Han glyph {index} is not an object")
        label = raw.get("codepoint")
        character = raw.get("character")
        if (
            not isinstance(label, str)
            or CODEPOINT_PATTERN.fullmatch(label) is None
            or not isinstance(character, str)
            or len(character) != 1
        ):
            raise MewNoteBulkError(f"non-Han glyph {index} identity invalid")
        codepoint = int(label[2:], 16)
        if ord(character) != codepoint or codepoint in seen:
            raise MewNoteBulkError(f"non-Han glyph {index} is duplicated")
        seen.add(codepoint)
        projected.append(
            {
                "canonical_rank": int(raw["canonical_rank"]),
                "authoring_rank": int(raw["authoring_rank"]),
                "character": character,
                "codepoint": label,
                "unicode_name": str(raw["name"]),
                "general_category": str(raw["gc"]),
                "outline_required": bool(raw["outline_required"]),
                "profile_id": str(raw["profile_id"]),
                "metrics": raw["metrics"],
            }
        )
    hiragana = {
        int(record["codepoint"][2:], 16)
        for record in projected
        if 0x3041 <= int(record["codepoint"][2:], 16) <= 0x309F
    }
    katakana = {
        int(record["codepoint"][2:], 16)
        for record in projected
        if 0x30A0 <= int(record["codepoint"][2:], 16) <= 0x30FF
    }
    if (
        len(hiragana) != REQUIRED_HIRAGANA
        or len(katakana) != REQUIRED_KATAKANA
    ):
        raise MewNoteBulkError(
            "required Japanese kana are incomplete in non-Han repertoire"
        )
    projected_batches: list[dict[str, Any]] = []
    for index, raw in enumerate(batches, start=1):
        if not isinstance(raw, dict):
            raise MewNoteBulkError(f"non-Han batch {index} is not an object")
        source_batch_id = str(raw.get("batch_id"))
        if source_batch_id != f"nonhan-{index:04d}":
            raise MewNoteBulkError("non-Han batch order changed")
        projected_batches.append(
            {
                "batch_id": source_batch_id,
                "batch_kind": str(raw["batch_kind"]),
                "design_group": str(raw["design_group"]),
                "start_authoring_rank": int(
                    raw["start_authoring_rank"]
                ),
                "end_authoring_rank": int(raw["end_authoring_rank"]),
                "glyph_codepoints": list(raw["glyph_codepoints"]),
                "empty_grid_cells": (
                    int(raw["empty_grid_cells"])
                    if "empty_grid_cells" in raw
                    else None
                ),
            }
        )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "record_type": REPERTOIRE_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "repertoire_id": "mew-note-tc-nonhan-3060-v1",
        "normalization": "none",
        "counts": {
            "encoded": TARGET_NONHAN,
            "visible": TARGET_VISIBLE - TARGET_HAN,
            "semantic_empty": TARGET_SEMANTIC_EMPTY,
            "visible_raster_batches": 205,
            "semantic_empty_batches": 1,
            "total_batches": 206,
            "hiragana": len(hiragana),
            "katakana": len(katakana),
            "kana_total": len(hiragana | katakana),
        },
        "ordering": source["ordering"],
        "profiles": list(source["profile_ids"]),
        "identity_source": {
            "path": _relative(SHARED_NONHAN_PATH),
            "sha256": SHARED_NONHAN_SHA256,
            "identity_count": TARGET_NONHAN,
            "role": (
                "unicode-identity-metrics-and-semantic-policy-only-no-"
                "raster-outline-review-approval-reuse"
            ),
        },
        "sequence": source["sequence_hashes"],
        "required_subsets": [
            {
                "id": "hiragana",
                "range": "U+3041..U+309F",
                "count": REQUIRED_HIRAGANA,
            },
            {
                "id": "katakana",
                "range": "U+30A0..U+30FF",
                "count": REQUIRED_KATAKANA,
            },
            {
                "id": "kana-total",
                "members": ["hiragana", "katakana"],
                "count": REQUIRED_HIRAGANA + REQUIRED_KATAKANA,
            },
        ],
        "glyphs": projected,
        "batches": projected_batches,
    }
    return payload


def build_vertical_repertoire(project_root: Path) -> dict[str, Any]:
    _require_hash(
        project_root,
        SHARED_VERTICAL_PATH,
        SHARED_VERTICAL_SHA256,
        label="shared vertical repertoire",
    )
    source = _read_object(project_root / SHARED_VERTICAL_PATH)
    alternates = source.get("alternates")
    batches = source.get("batches")
    if (
        source.get("total") != TARGET_VERTICAL
        or not isinstance(alternates, list)
        or len(alternates) != TARGET_VERTICAL
        or not isinstance(batches, list)
        or len(batches) != 6
    ):
        raise MewNoteBulkError("shared vertical repertoire shape changed")
    projected: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for rank, raw in enumerate(alternates, start=1):
        if not isinstance(raw, dict) or int(raw.get("rank", -1)) != rank:
            raise MewNoteBulkError("vertical alternate order changed")
        glyph_name = str(raw["glyph_name"])
        if glyph_name in seen_names:
            raise MewNoteBulkError("vertical glyph names are not unique")
        seen_names.add(glyph_name)
        projected.append(
            {
                "rank": rank,
                "base_character": str(raw["base_character"]),
                "base_codepoint": str(raw["base_codepoint"]),
                "glyph_name": glyph_name,
                "unicode_name": str(raw["unicode_name"]),
                "vertical_orientation": str(raw["vertical_orientation"]),
                "tailoring": raw["tailoring"],
                "base_profile_id": str(raw["base_profile_id"]),
                "base_metrics": raw["base_metrics"],
            }
        )
    return {
        "schema_version": 1,
        "record_type": REPERTOIRE_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "repertoire_id": "mew-note-tc-vertical-93-v1",
        "normalization": "none",
        "counts": {
            "encoded": 0,
            "visible": TARGET_VERTICAL,
            "semantic_empty": 0,
            "batches": 6,
        },
        "identity_source": {
            "path": _relative(SHARED_VERTICAL_PATH),
            "sha256": SHARED_VERTICAL_SHA256,
            "identity_count": TARGET_VERTICAL,
            "role": (
                "unicode-identity-shaping-and-placement-only-no-raster-"
                "outline-review-approval-reuse"
            ),
        },
        "sequence": {
            "serialization": "glyph-name-lines-utf8-v1",
            "sha256": str(source["sequence_sha256"]),
        },
        "required_features": ["vert", "vrt2"],
        "alternates": projected,
        "batches": batches,
    }


def build_repertoires(project_root: Path) -> dict[str, str]:
    project_root = _project_root(project_root)
    payloads = {
        HAN_PATH: build_han_repertoire(project_root),
        NONHAN_PATH: build_nonhan_repertoire(project_root),
        VERTICAL_PATH: build_vertical_repertoire(project_root),
    }
    for relative, payload in payloads.items():
        _write_json(project_root / relative, payload)
    return {
        relative.as_posix(): sha256_path(project_root / relative)
        for relative in payloads
    }


def load_context(project_root: Path) -> FamilyContext:
    try:
        return load_family_context(
            project_root=project_root,
            family_contract_path=FAMILY_PATH,
            pipeline_contract_path=PIPELINE_PATH,
        )
    except FamilyContextError as exc:
        raise MewNoteBulkError(str(exc)) from exc


def _exact_reference(
    payload: Mapping[str, Any],
    key: str,
    *,
    context: FamilyContext,
) -> Mapping[str, str]:
    value = payload.get(key)
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise MewNoteBulkError(
            f"authoring.{key} must contain exactly path and sha256"
        )
    path = value["path"]
    digest = value["sha256"]
    if (
        not isinstance(path, str)
        or not isinstance(digest, str)
        or SHA256_PATTERN.fullmatch(digest) is None
    ):
        raise MewNoteBulkError(f"authoring.{key} is invalid")
    _require_hash(
        context.project_root,
        Path(path),
        digest,
        label=f"authoring.{key}",
    )
    return value


def validate_authoring_contract(
    context: FamilyContext,
) -> Mapping[str, Any]:
    payload = context.authoring_payload
    expected_keys = {
        "schema_version",
        "record_type",
        "family_id",
        "pipeline_id",
        "collection_contract",
        "motif_contract",
        "pilot_provenance",
        "pilot_review",
        "materializer",
        "context_loader",
        "identity_reference_renderer",
        "prompt_template",
        "style_references",
        "grid",
        "copybook_policy",
        "motif_assignment",
        "path_contract",
        "source_boundary",
        "stop_conditions",
    }
    if set(payload) != expected_keys:
        raise MewNoteBulkError(
            "authoring contract has an invalid top-level key set"
        )
    if (
        payload.get("family_id") != FAMILY_ID
        or payload.get("pipeline_id") != PIPELINE_ID
    ):
        raise MewNoteBulkError("authoring family or pipeline mismatch")
    for key in (
        "motif_contract",
        "pilot_provenance",
        "pilot_review",
        "materializer",
        "context_loader",
        "identity_reference_renderer",
        "prompt_template",
    ):
        _exact_reference(payload, key, context=context)
    family_contracts = context.family_payload["contracts"]
    expected_family_keys = {
        "motif_contract": "motif",
        "pilot_provenance": "pilot_provenance",
        "pilot_review": "pilot_review",
    }
    for authoring_key, family_key in expected_family_keys.items():
        if payload[authoring_key] != family_contracts[family_key]:
            raise MewNoteBulkError(
                f"authoring.{authoring_key} does not match family chain"
            )
    review = _read_object(
        context.project_root / payload["pilot_review"]["path"]
    )
    provenance = _read_object(
        context.project_root / payload["pilot_provenance"]["path"]
    )
    expected_active_pilots = [
        "mew-note-han-style-pilot-v2",
        "mew-note-nonhan-style-pilot",
    ]
    if (
        review.get("review_state") != "ACCEPT"
        or review.get("scope", {}).get("bulk_authoring_decision")
        is not True
        or review.get("authorization", {}).get(
            "bulk_authoring_allowed"
        )
        is not True
        or review.get("active_pilot_ids") != expected_active_pilots
        or review.get("summary", {}).get("active_cell_count") != 32
        or review.get("summary", {}).get("accepted_cell_count") != 32
        or review.get("summary", {}).get("rejected_cell_count") != 0
        or provenance.get("source_state") != "pilot-source-frozen"
        or provenance.get("active_pilot_ids") != expected_active_pilots
        or context.family_payload.get("authoring", {}).get(
            "bulk_authoring_allowed"
        )
        is not True
        or context.family_payload.get("authoring", {}).get(
            "active_pilot_ids"
        )
        != expected_active_pilots
    ):
        raise MewNoteBulkError(
            "active pilot review does not authorize bulk authoring"
        )
    motif = _read_object(
        context.project_root / payload["motif_contract"]["path"]
    )
    if (
        motif.get("family_id") != FAMILY_ID
        or motif["global_rules"][
            "detached_decorative_contours_allowed"
        ]
        is not False
        or motif["global_rules"]["maximum_motif_sites_per_glyph"] != 1
        or motif["geometry_gates"]["max_micro_edge_count"] != 0
        or motif["geometry_gates"]["max_acute_micro_turn_count"] != 0
    ):
        raise MewNoteBulkError("motif safety gates are not exact")
    grid = payload["grid"]
    if grid != {
        "rows": GRID_ROWS,
        "columns": GRID_COLUMNS,
        "capacity": GRID_CAPACITY,
        "order": "row-major",
        "copybook_role": "identity-reference-only-no-outline-import",
    }:
        raise MewNoteBulkError("authoring grid contract changed")
    copybook_policy = payload["copybook_policy"]
    if copybook_policy != {
        "required_for_every_visible_batch": True,
        "role": "identity-reference-only-no-outline-import",
        "external_reference_faces_must_be_explicitly_hash_pinned": True,
        "font_binaries_committed": False,
        "fallback_face_allowed": False,
        "missing_identity_allowed": False,
        "copybook_raster_may_become_glyph_source": False,
    }:
        raise MewNoteBulkError("copybook policy is not fail-closed")
    assignment = payload["motif_assignment"]
    if (
        assignment.get("tail_period") != TAIL_PERIOD
        or assignment.get("tail_phase") != TAIL_PHASE
        or assignment.get("minimum_readable_text_ratio") != 0.15
        or assignment.get("maximum_consecutive_tail_glyphs") != 2
        or assignment.get("maximum_repertoire_ratio") != 0.35
        or assignment.get("maximum_tail_terminals_per_glyph") != 1
        or assignment.get("detached_contours_allowed") is not False
        or assignment.get("spikes_allowed") is not False
    ):
        raise MewNoteBulkError("motif assignment contract changed")
    styles = payload["style_references"]
    if not isinstance(styles, list) or len(styles) != 2:
        raise MewNoteBulkError("exactly two style references are required")
    for index, style in enumerate(styles):
        if (
            not isinstance(style, dict)
            or set(style)
            != {"id", "path", "sha256", "role", "collections"}
            or style["role"]
            != "style-only-no-raster-or-outline-reuse"
        ):
            raise MewNoteBulkError(
                f"style reference {index} contract invalid"
            )
        _require_hash(
            context.project_root,
            Path(style["path"]),
            style["sha256"],
            label=f"style reference {index}",
        )
        if (
            "clear-hand-tc" in Path(style["path"]).parts
            or not set(style["collections"])
            <= {"han-6060", "nonhan-3060", "vertical-93"}
        ):
            raise MewNoteBulkError(
                f"style reference {index} crosses a family boundary"
            )
    if {
        style["id"]: style["collections"] for style in styles
    } != {
        "mew-note-han-style-pilot-v2": [
            "han-6060",
            "nonhan-3060",
        ],
        "mew-note-nonhan-style-pilot": [
            "nonhan-3060",
            "vertical-93",
        ],
    }:
        raise MewNoteBulkError("style reference assignment changed")
    expected_path_contract = {
        "batch_root": (
            "{source_root}/pipelines/{pipeline_id}/collections/"
            "{collection_id}/batches/{batch_id}"
        ),
        "prompt": "{batch_root}/prompt.md",
        "identity_copybook": "{batch_root}/identity-copybook.png",
        "draft": "{batch_root}/draft.json",
        "raster": "{batch_root}/raster.png",
        "build": (
            "{build_root}/pipelines/{pipeline_id}/collections/"
            "{collection_id}/batches/{batch_id}"
        ),
        "cache": (
            "{cache_root}/pipelines/{pipeline_id}/collections/"
            "{collection_id}/batches/{batch_id}"
        ),
        "release": (
            "{release_root}/pipelines/{pipeline_id}/collections/"
            "{collection_id}/batches/{batch_id}"
        ),
    }
    if payload["path_contract"] != expected_path_contract:
        raise MewNoteBulkError("authoring path contract changed")
    boundary = payload["source_boundary"]
    if (
        boundary.get("clear_hand_identity_data_allowed") is not True
        or any(
            boundary.get(key) is not False
            for key in (
                "clear_hand_raster_allowed",
                "clear_hand_outline_allowed",
                "clear_hand_review_allowed",
                "clear_hand_approval_allowed",
            )
        )
        or boundary.get("reference_outline_import_allowed") is not False
        or boundary.get("generated_raster_is_never_self_approved")
        is not True
    ):
        raise MewNoteBulkError("source boundary is not fail-closed")
    return payload


def _collection_record(
    context: FamilyContext,
    collection_id: str,
) -> Mapping[str, Any]:
    return context.collection(collection_id).record


def _local_repertoire(
    context: FamilyContext,
    collection_id: str,
) -> dict[str, Any]:
    record = _collection_record(context, collection_id)
    reference = record.get("family_repertoire")
    if (
        not isinstance(reference, dict)
        or set(reference) != {"path", "sha256", "repertoire_id"}
    ):
        raise MewNoteBulkError(
            f"{collection_id}: family_repertoire pin is invalid"
        )
    relative = Path(str(reference["path"]))
    required_prefix = Path(
        f"families/{FAMILY_ID}/sources/imagegen/repertoires"
    )
    try:
        relative.relative_to(required_prefix)
    except ValueError as exc:
        raise MewNoteBulkError(
            f"{collection_id}: repertoire escapes family namespace"
        ) from exc
    _require_hash(
        context.project_root,
        relative,
        str(reference["sha256"]),
        label=f"{collection_id} repertoire",
    )
    payload = _read_object(context.project_root / relative)
    if (
        payload.get("record_type") != REPERTOIRE_RECORD_TYPE
        or payload.get("family_id") != FAMILY_ID
        or payload.get("pipeline_id") != PIPELINE_ID
        or payload.get("repertoire_id") != reference["repertoire_id"]
    ):
        raise MewNoteBulkError(
            f"{collection_id}: repertoire identity mismatch"
        )
    return payload


def _style_references_for(
    authoring: Mapping[str, Any],
    collection_id: str,
) -> list[dict[str, str]]:
    result = []
    for style in authoring["style_references"]:
        if collection_id in style["collections"]:
            result.append(
                {
                    "id": str(style["id"]),
                    "path": str(style["path"]),
                    "sha256": str(style["sha256"]),
                    "role": str(style["role"]),
                }
            )
    if not result:
        raise MewNoteBulkError(
            f"{collection_id}: no style reference is declared"
        )
    return result


def _nonhan_tail_eligible(
    glyph: Mapping[str, Any],
    *,
    design_group: str,
) -> bool:
    if not glyph["outline_required"]:
        return False
    if glyph["profile_id"] in NONHAN_NEUTRAL_PROFILE_IDS:
        return False
    return design_group.startswith(NONHAN_TAIL_ELIGIBLE_GROUP_PREFIXES)


def _motif_entries(
    collection_id: str,
    glyphs: Sequence[Mapping[str, Any]],
    *,
    design_group: str | None,
    eligible_counter: list[int],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for cell, glyph in enumerate(glyphs, start=1):
        if collection_id == "han-6060":
            eligible = True
        elif collection_id == "nonhan-3060":
            if design_group is None:
                raise MewNoteBulkError("non-Han design group missing")
            eligible = _nonhan_tail_eligible(
                glyph,
                design_group=design_group,
            )
        else:
            eligible = False
        if eligible:
            eligible_counter[0] += 1
            motif_class = (
                "tail-terminal"
                if eligible_counter[0] % TAIL_PERIOD == TAIL_PHASE
                else "soft-terminal"
            )
        else:
            motif_class = "neutral-safety"
        codepoint = (
            int(glyph["codepoint"])
            if isinstance(glyph["codepoint"], int)
            else int(str(glyph["codepoint"])[2:], 16)
        )
        entries.append(
            {
                "cell": cell,
                "character": str(glyph["character"]),
                "codepoint": _codepoint_label(codepoint),
                "source_rank": int(
                    glyph.get(
                        "rank",
                        glyph.get("authoring_rank", cell),
                    )
                ),
                "motif_class": motif_class,
            }
        )
    return entries


def _vertical_entries(
    alternates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "cell": cell,
            "character": str(record["base_character"]),
            "codepoint": str(record["base_codepoint"]),
            "glyph_name": str(record["glyph_name"]),
            "source_rank": int(record["rank"]),
            "motif_class": "neutral-safety",
        }
        for cell, record in enumerate(alternates, start=1)
    ]


def _render_prompt(
    template: str,
    *,
    collection_id: str,
    batch_id: str,
    entries: Sequence[Mapping[str, Any]],
    style_references: Sequence[Mapping[str, str]],
) -> str:
    character_rows = []
    for start in range(0, len(entries), GRID_COLUMNS):
        row = entries[start : start + GRID_COLUMNS]
        character_rows.append(" ".join(str(entry["character"]) for entry in row))
    assignments = "\n".join(
        "- Cell "
        f"{int(entry['cell']):02d}: {entry['character']} "
        f"({entry['codepoint']}) — {entry['motif_class']}"
        for entry in entries
    )
    tail_ranks = [
        int(entry["cell"])
        for entry in entries
        if entry["motif_class"] == "tail-terminal"
    ]
    style_lines = "\n".join(
        f"- `{reference['id']}`: {reference['role']} "
        f"({reference['path']}, SHA-256 {reference['sha256']})"
        for reference in style_references
    )
    replacements = {
        "{{FAMILY_ID}}": FAMILY_ID,
        "{{BATCH_ID}}": batch_id,
        "{{COLLECTION_ID}}": collection_id,
        "{{ROWS}}": str(GRID_ROWS),
        "{{COLUMNS}}": str(GRID_COLUMNS),
        "{{CHARACTER_ROWS}}": "\n".join(character_rows),
        "{{CELL_ASSIGNMENTS}}": assignments,
        "{{TAIL_RANKS}}": (
            ", ".join(str(rank) for rank in tail_ranks)
            if tail_ranks
            else "none"
        ),
        "{{STYLE_REFERENCE_ROLES}}": style_lines,
    }
    rendered = template
    for token, value in replacements.items():
        if token not in rendered:
            raise MewNoteBulkError(f"prompt template misses {token}")
        rendered = rendered.replace(token, value)
    if "{{" in rendered or "}}" in rendered:
        raise MewNoteBulkError("prompt template has unresolved tokens")
    return rendered


def _batch_artifact_paths(
    context: FamilyContext,
    *,
    collection_id: str,
    batch_id: str,
    visible: bool,
) -> dict[str, Any]:
    paths = context.batch_paths(collection_id, batch_id)
    source = paths.source.relative_to(context.project_root)
    build = paths.build.relative_to(context.project_root)
    cache = paths.cache.relative_to(context.project_root)
    release = paths.release.relative_to(context.project_root)
    return {
        "prompt": (
            (source / "prompt.md").as_posix() if visible else None
        ),
        "identity_copybook": (
            (source / "identity-copybook.png").as_posix()
            if visible
            else None
        ),
        "draft": (source / "draft.json").as_posix(),
        "raster": (
            (source / "raster.png").as_posix() if visible else None
        ),
        "build_root": build.as_posix(),
        "cache_root": cache.as_posix(),
        "release_root": release.as_posix(),
    }


def _batch_contract_hash(record: Mapping[str, Any]) -> str:
    return canonical_json_sha256(
        {
            key: value
            for key, value in record.items()
            if key != "batch_contract_sha256"
        }
    )


def build_plan(context: FamilyContext) -> dict[str, Any]:
    authoring = validate_authoring_contract(context)
    template_path = context.project_root / authoring["prompt_template"]["path"]
    template = template_path.read_text(encoding="utf-8")
    repertoires = {
        collection_id: _local_repertoire(context, collection_id)
        for collection_id in ("han-6060", "nonhan-3060", "vertical-93")
    }
    batches: list[dict[str, Any]] = []
    eligible_counter = [0]

    han = repertoires["han-6060"]
    han_by_rank = {
        int(record["rank"]): record for record in han["glyphs"]
    }
    for raw_batch in han["batches"]:
        glyphs = [
            han_by_rank[rank]
            for rank in range(
                int(raw_batch["start_rank"]),
                int(raw_batch["end_rank"]) + 1,
            )
        ]
        entries = _motif_entries(
            "han-6060",
            glyphs,
            design_group=None,
            eligible_counter=eligible_counter,
        )
        batch_id = str(raw_batch["batch_id"])
        styles = _style_references_for(authoring, "han-6060")
        prompt = _render_prompt(
            template,
            collection_id="han-6060",
            batch_id=batch_id,
            entries=entries,
            style_references=styles,
        )
        record: dict[str, Any] = {
            "batch_id": batch_id,
            "collection_id": "han-6060",
            "materialization_kind": "visible-raster",
            "family_context": context.evidence_binding("han-6060"),
            "grid": {
                "rows": GRID_ROWS,
                "columns": GRID_COLUMNS,
                "capacity": GRID_CAPACITY,
                "order": "row-major",
                "empty_cells": GRID_CAPACITY - len(entries),
            },
            "entries": entries,
            "tail_terminal_cells": [
                entry["cell"]
                for entry in entries
                if entry["motif_class"] == "tail-terminal"
            ],
            "style_references": styles,
            "artifacts": _batch_artifact_paths(
                context,
                collection_id="han-6060",
                batch_id=batch_id,
                visible=True,
            ),
            "prompt_sha256": hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest(),
            "state": "planned-not-materialized",
        }
        record["batch_contract_sha256"] = _batch_contract_hash(record)
        batches.append(record)

    nonhan = repertoires["nonhan-3060"]
    nonhan_by_codepoint = {
        str(record["codepoint"]): record for record in nonhan["glyphs"]
    }
    for raw_batch in nonhan["batches"]:
        batch_id = str(raw_batch["batch_id"])
        batch_kind = str(raw_batch["batch_kind"])
        visible = batch_kind == "raster-outline"
        glyphs = [
            nonhan_by_codepoint[label]
            for label in raw_batch["glyph_codepoints"]
        ]
        entries = _motif_entries(
            "nonhan-3060",
            glyphs,
            design_group=str(raw_batch["design_group"]),
            eligible_counter=eligible_counter,
        )
        styles = (
            _style_references_for(authoring, "nonhan-3060")
            if visible
            else []
        )
        prompt_hash = None
        if visible:
            prompt = _render_prompt(
                template,
                collection_id="nonhan-3060",
                batch_id=batch_id,
                entries=entries,
                style_references=styles,
            )
            prompt_hash = hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest()
        record = {
            "batch_id": batch_id,
            "collection_id": "nonhan-3060",
            "materialization_kind": (
                "visible-raster" if visible else "semantic-empty"
            ),
            "family_context": context.evidence_binding("nonhan-3060"),
            "design_group": str(raw_batch["design_group"]),
            "grid": (
                {
                    "rows": GRID_ROWS,
                    "columns": GRID_COLUMNS,
                    "capacity": GRID_CAPACITY,
                    "order": "row-major",
                    "empty_cells": GRID_CAPACITY - len(entries),
                }
                if visible
                else None
            ),
            "entries": entries,
            "tail_terminal_cells": [
                entry["cell"]
                for entry in entries
                if entry["motif_class"] == "tail-terminal"
            ],
            "style_references": styles,
            "artifacts": _batch_artifact_paths(
                context,
                collection_id="nonhan-3060",
                batch_id=batch_id,
                visible=visible,
            ),
            "prompt_sha256": prompt_hash,
            "state": "planned-not-materialized",
        }
        record["batch_contract_sha256"] = _batch_contract_hash(record)
        batches.append(record)

    vertical = repertoires["vertical-93"]
    vertical_by_rank = {
        int(record["rank"]): record for record in vertical["alternates"]
    }
    for raw_batch in vertical["batches"]:
        batch_id = str(raw_batch["batch_id"])
        glyphs = [
            vertical_by_rank[rank]
            for rank in range(
                int(raw_batch["start_rank"]),
                int(raw_batch["end_rank"]) + 1,
            )
        ]
        entries = _vertical_entries(glyphs)
        styles = _style_references_for(authoring, "vertical-93")
        prompt = _render_prompt(
            template,
            collection_id="vertical-93",
            batch_id=batch_id,
            entries=entries,
            style_references=styles,
        )
        record = {
            "batch_id": batch_id,
            "collection_id": "vertical-93",
            "materialization_kind": "visible-raster",
            "family_context": context.evidence_binding("vertical-93"),
            "grid": {
                "rows": GRID_ROWS,
                "columns": GRID_COLUMNS,
                "capacity": GRID_CAPACITY,
                "order": "row-major",
                "empty_cells": GRID_CAPACITY - len(entries),
            },
            "entries": entries,
            "tail_terminal_cells": [],
            "style_references": styles,
            "artifacts": _batch_artifact_paths(
                context,
                collection_id="vertical-93",
                batch_id=batch_id,
                visible=True,
            ),
            "prompt_sha256": hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest(),
            "state": "planned-not-materialized",
        }
        record["batch_contract_sha256"] = _batch_contract_hash(record)
        batches.append(record)

    visible_entries = [
        entry
        for batch in batches
        if batch["materialization_kind"] == "visible-raster"
        for entry in batch["entries"]
    ]
    motif_counts = Counter(
        str(entry["motif_class"]) for entry in visible_entries
    )
    tail_ratio = motif_counts["tail-terminal"] / len(visible_entries)
    plan: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "record_type": PLAN_RECORD_TYPE,
        "family_id": FAMILY_ID,
        "pipeline_id": PIPELINE_ID,
        "family_contract": context.family_contract.evidence_record(),
        "pipeline_contract": context.pipeline_contract.evidence_record(),
        "authoring_contract": context.authoring_contract.evidence_record(),
        "collection_contract": context.collection_contract.evidence_record(),
        "motif_contract": authoring["motif_contract"],
        "pilot_provenance": authoring["pilot_provenance"],
        "pilot_review": authoring["pilot_review"],
        "prompt_template": authoring["prompt_template"],
        "targets": {
            "requirements_denominator": REQUIREMENTS_DENOMINATOR,
            "encoded_han": TARGET_HAN,
            "encoded_nonhan": TARGET_NONHAN,
            "encoded_total": TARGET_ENCODED,
            "visible_encoded": TARGET_VISIBLE,
            "semantic_empty": TARGET_SEMANTIC_EMPTY,
            "unencoded_vertical": TARGET_VERTICAL,
            "coverage_percent": 50.4676,
            "hiragana": REQUIRED_HIRAGANA,
            "katakana": REQUIRED_KATAKANA,
            "kana_total": REQUIRED_HIRAGANA + REQUIRED_KATAKANA,
        },
        "batch_counts": {
            "han": len(han["batches"]),
            "nonhan_visible": 205,
            "nonhan_semantic_empty": 1,
            "vertical": len(vertical["batches"]),
            "total": len(batches),
            "visible_raster": sum(
                batch["materialization_kind"] == "visible-raster"
                for batch in batches
            ),
        },
        "motif_summary": {
            "visible_glyph_count": len(visible_entries),
            "counts": {
                motif_class: motif_counts[motif_class]
                for motif_class in sorted(MOTIF_CLASSES)
            },
            "tail_ratio": round(tail_ratio, 8),
            "maximum_allowed_tail_ratio": 0.35,
            "maximum_consecutive_tail_glyphs": 2,
            "detached_contours_allowed": False,
            "spikes_allowed": False,
        },
        "batches": batches,
    }
    validate_plan_payload(plan, context=context)
    return plan


def _batch_identity_sequence(
    batches: Sequence[Mapping[str, Any]],
    collection_id: str,
) -> list[str]:
    return [
        str(entry["codepoint"])
        for batch in batches
        if batch["collection_id"] == collection_id
        for entry in batch["entries"]
    ]


def validate_plan_payload(
    plan: Mapping[str, Any],
    *,
    context: FamilyContext,
) -> None:
    authoring = validate_authoring_contract(context)
    if (
        plan.get("schema_version") != PLAN_SCHEMA_VERSION
        or plan.get("record_type") != PLAN_RECORD_TYPE
        or plan.get("family_id") != FAMILY_ID
        or plan.get("pipeline_id") != PIPELINE_ID
    ):
        raise MewNoteBulkError("plan identity mismatch")
    expected_pins = {
        "family_contract": context.family_contract.evidence_record(),
        "pipeline_contract": context.pipeline_contract.evidence_record(),
        "authoring_contract": context.authoring_contract.evidence_record(),
        "collection_contract": context.collection_contract.evidence_record(),
        "motif_contract": authoring["motif_contract"],
        "pilot_provenance": authoring["pilot_provenance"],
        "pilot_review": authoring["pilot_review"],
        "prompt_template": authoring["prompt_template"],
    }
    for key, expected in expected_pins.items():
        if plan.get(key) != expected:
            raise MewNoteBulkError(f"plan {key} pin mismatch")
    batches = plan.get("batches")
    if not isinstance(batches, list) or len(batches) != 591:
        raise MewNoteBulkError("plan must contain exactly 591 batches")
    template = (
        context.project_root / authoring["prompt_template"]["path"]
    ).read_text(encoding="utf-8")
    seen_batch_keys: set[tuple[str, str]] = set()
    visible_entries: list[Mapping[str, Any]] = []
    consecutive_tails = 0
    maximum_consecutive = 0
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            raise MewNoteBulkError(f"batch {index} is not an object")
        collection_id = str(batch.get("collection_id"))
        batch_id = str(batch.get("batch_id"))
        key = (collection_id, batch_id)
        if key in seen_batch_keys:
            raise MewNoteBulkError(f"duplicate batch key {key}")
        seen_batch_keys.add(key)
        if collection_id not in {
            "han-6060",
            "nonhan-3060",
            "vertical-93",
        }:
            raise MewNoteBulkError(f"unknown collection {collection_id}")
        if batch.get("family_context") != context.evidence_binding(
            collection_id
        ):
            raise MewNoteBulkError(
                f"{collection_id}/{batch_id}: context mismatch"
            )
        if batch.get("batch_contract_sha256") != _batch_contract_hash(
            batch
        ):
            raise MewNoteBulkError(
                f"{collection_id}/{batch_id}: record hash mismatch"
            )
        visible = batch.get("materialization_kind") == "visible-raster"
        artifacts = batch.get("artifacts")
        expected_artifacts = _batch_artifact_paths(
            context,
            collection_id=collection_id,
            batch_id=batch_id,
            visible=visible,
        )
        if artifacts != expected_artifacts:
            raise MewNoteBulkError(
                f"{collection_id}/{batch_id}: path namespace mismatch"
            )
        for artifact_path in artifacts.values():
            if artifact_path is None:
                continue
            parts = Path(artifact_path).parts
            if (
                "clear-hand-tc" in parts
                or (
                    artifact_path.startswith("sources/imagegen/")
                    and FAMILY_ID not in parts
                )
            ):
                raise MewNoteBulkError(
                    f"{collection_id}/{batch_id}: cross-family artifact"
                )
        entries = batch.get("entries")
        if not isinstance(entries, list) or not entries:
            raise MewNoteBulkError(
                f"{collection_id}/{batch_id}: entries missing"
            )
        for entry in entries:
            motif_class = entry.get("motif_class")
            if motif_class not in MOTIF_CLASSES:
                raise MewNoteBulkError(
                    f"{collection_id}/{batch_id}: invalid motif class"
                )
            if collection_id == "vertical-93" and motif_class != (
                "neutral-safety"
            ):
                raise MewNoteBulkError("vertical glyph has decoration")
            if motif_class == "tail-terminal":
                consecutive_tails += 1
                maximum_consecutive = max(
                    maximum_consecutive,
                    consecutive_tails,
                )
            else:
                consecutive_tails = 0
        if visible:
            visible_entries.extend(entries)
            styles = batch.get("style_references")
            expected_prompt = _render_prompt(
                template,
                collection_id=collection_id,
                batch_id=batch_id,
                entries=entries,
                style_references=styles,
            )
            if batch.get("prompt_sha256") != hashlib.sha256(
                expected_prompt.encode("utf-8")
            ).hexdigest():
                raise MewNoteBulkError(
                    f"{collection_id}/{batch_id}: prompt hash mismatch"
                )
        else:
            if (
                batch.get("materialization_kind") != "semantic-empty"
                or batch.get("prompt_sha256") is not None
                or batch.get("style_references") != []
                or batch.get("grid") is not None
                or any(
                    entry["motif_class"] != "neutral-safety"
                    for entry in entries
                )
            ):
                raise MewNoteBulkError(
                    "semantic-empty batch attempts visible authoring"
                )
    if maximum_consecutive > 2:
        raise MewNoteBulkError("tail assignments exceed consecutive limit")
    motif_counts = Counter(
        str(entry["motif_class"]) for entry in visible_entries
    )
    tail_ratio = motif_counts["tail-terminal"] / len(visible_entries)
    if not 0.15 <= tail_ratio <= 0.35:
        raise MewNoteBulkError("overall readable tail ratio is out of range")
    expected_summary = {
        "visible_glyph_count": len(visible_entries),
        "counts": {
            motif_class: motif_counts[motif_class]
            for motif_class in sorted(MOTIF_CLASSES)
        },
        "tail_ratio": round(tail_ratio, 8),
        "maximum_allowed_tail_ratio": 0.35,
        "maximum_consecutive_tail_glyphs": 2,
        "detached_contours_allowed": False,
        "spikes_allowed": False,
    }
    if plan.get("motif_summary") != expected_summary:
        raise MewNoteBulkError("motif summary mismatch")
    han = _local_repertoire(context, "han-6060")
    nonhan = _local_repertoire(context, "nonhan-3060")
    vertical = _local_repertoire(context, "vertical-93")
    expected_han = [
        _codepoint_label(int(record["codepoint"]))
        for record in han["glyphs"]
    ]
    expected_nonhan = [
        str(record["codepoint"])
        for record in sorted(
            nonhan["glyphs"],
            key=lambda record: int(record["authoring_rank"]),
        )
    ]
    expected_vertical = [
        str(record["base_codepoint"])
        for record in vertical["alternates"]
    ]
    if _batch_identity_sequence(batches, "han-6060") != expected_han:
        raise MewNoteBulkError("Han batches do not exhaust repertoire")
    if _batch_identity_sequence(batches, "nonhan-3060") != expected_nonhan:
        raise MewNoteBulkError("non-Han batches do not exhaust repertoire")
    if _batch_identity_sequence(batches, "vertical-93") != expected_vertical:
        raise MewNoteBulkError("vertical batches do not exhaust repertoire")
    encoded = set(expected_han) | set(expected_nonhan)
    if (
        len(expected_han) != TARGET_HAN
        or len(expected_nonhan) != TARGET_NONHAN
        or len(encoded) != TARGET_ENCODED
    ):
        raise MewNoteBulkError("encoded target or partition mismatch")
    hiragana = {
        label
        for label in expected_nonhan
        if 0x3041 <= int(label[2:], 16) <= 0x309F
    }
    katakana = {
        label
        for label in expected_nonhan
        if 0x30A0 <= int(label[2:], 16) <= 0x30FF
    }
    if (
        len(hiragana) != REQUIRED_HIRAGANA
        or len(katakana) != REQUIRED_KATAKANA
    ):
        raise MewNoteBulkError("plan kana coverage mismatch")
    if TARGET_ENCODED / REQUIREMENTS_DENOMINATOR <= 0.5:
        raise MewNoteBulkError("target no longer exceeds half")


def write_plan(context: FamilyContext) -> Path:
    plan = build_plan(context)
    path = context.project_root / PLAN_PATH
    _write_json(path, plan)
    return path


def validate_plan(context: FamilyContext, path: Path) -> dict[str, Any]:
    payload = _read_object(path)
    validate_plan_payload(payload, context=context)
    return {
        "path": path.relative_to(context.project_root).as_posix(),
        "sha256": sha256_path(path),
        "batches": len(payload["batches"]),
        "visible_raster_batches": payload["batch_counts"][
            "visible_raster"
        ],
        "encoded_target": payload["targets"]["encoded_total"],
        "tail_ratio": payload["motif_summary"]["tail_ratio"],
        "kana_total": payload["targets"]["kana_total"],
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-repertoires")
    subparsers.add_parser("build-plan")
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument(
        "--plan",
        type=Path,
        default=PLAN_PATH,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = _project_root(args.project_root)
    if args.command == "build-repertoires":
        result: Mapping[str, Any] = build_repertoires(project_root)
    else:
        context = load_context(project_root)
        if args.command == "build-plan":
            path = write_plan(context)
            result = validate_plan(context, path)
        else:
            plan_path = args.plan
            if not plan_path.is_absolute():
                plan_path = project_root / plan_path
            result = validate_plan(context, plan_path)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
