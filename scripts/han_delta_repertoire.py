#!/usr/bin/env python3
"""Build and validate reusable dictionary-salience Han delta repertoires."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence

from scripts.inventory import han_block


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = Path("inventories/han_characters.csv")
DEFAULT_REQUIREMENTS = Path("inventories/font_requirements.json")
DEFAULT_OUTPUT = Path(
    "sources/imagegen/repertoires/"
    "dictionary-salience-extension-1216.json"
)
DEFAULT_EXCLUDED_REPERTOIRES = (
    Path("sources/imagegen/repertoires/common-3000.json"),
    Path(
        "sources/imagegen/repertoires/"
        "moe-common-extension-1844.json"
    ),
    Path("sources/imagegen/repertoires/nonhan-3060.json"),
)
DEFAULT_FAMILY_ID = "clear-hand-tc"
DEFAULT_REPERTOIRE_ID = (
    "clear-hand-tc-dictionary-salience-extension-1216-v1"
)
DEFAULT_BATCH_PREFIX = "dict-han"
DEFAULT_COUNT = 1_216
GRID_ROWS = 4
GRID_COLUMNS = 4
GRID_CAPACITY = GRID_ROWS * GRID_COLUMNS
RECORD_TYPE = "han-delta-repertoire"
SELECTION_STRATEGY = "dictionary-occurrence-desc-codepoint-asc"
BUILDER_ID = "scripts/han_delta_repertoire.py"
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
INVENTORY_FIELDS = (
    "character",
    "codepoint",
    "codepoint_decimal",
    "unicode_name",
    "unicode_block",
    "unicode_plane",
    "usage_class",
    "occurrence_count",
    "source_tables",
    "source_fields",
    "source_details",
    "compatibility_mapping",
    "glyph_designed",
    "quality_checked",
)


class HanDeltaRepertoireError(ValueError):
    """A Han delta repertoire is ambiguous, stale, or malformed."""


@dataclass(frozen=True)
class HanDeltaBatch:
    """One exact row-major raster batch from a frozen Han delta."""

    batch_id: str
    start_rank: int
    end_rank: int
    characters: tuple[str, ...]
    empty_grid_cells: int


@dataclass(frozen=True)
class HanDeltaRepertoire:
    """A fully recomputed and validated Han delta repertoire."""

    path: Path
    sha256: str
    family_id: str
    repertoire_id: str
    batch_prefix: str
    sequence_sha256: str
    characters: tuple[str, ...]
    batches: tuple[HanDeltaBatch, ...]
    payload: Mapping[str, Any]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str, *, encoding: str = "utf-8") -> str:
    return hashlib.sha256(value.encode(encoding)).hexdigest()


def _slug(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or SLUG_PATTERN.fullmatch(value) is None:
        raise HanDeltaRepertoireError(
            f"{label} must be a lowercase ASCII slug"
        )
    return value


def _nonempty(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise HanDeltaRepertoireError(
            f"{label} must be non-empty without surrounding whitespace"
        )
    return value


def _relative_path(value: Any, *, label: str) -> Path:
    if not isinstance(value, str):
        raise HanDeltaRepertoireError(f"{label} must be a string")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or not pure.parts
        or ".." in pure.parts
        or "." in pure.parts
        or pure.as_posix() != value
    ):
        raise HanDeltaRepertoireError(
            f"{label} must be a canonical project-relative POSIX path"
        )
    return Path(*pure.parts)


def _project_relative(
    path: Path,
    *,
    project_root: Path,
    label: str,
) -> Path:
    root = project_root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise HanDeltaRepertoireError(
            f"{label} must remain below the project root"
        ) from exc
    return relative


def _regular_file(
    project_root: Path,
    relative: Path,
    *,
    label: str,
) -> Path:
    root = project_root.resolve()
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise HanDeltaRepertoireError(
            f"{label} is missing: {relative.as_posix()}"
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise HanDeltaRepertoireError(
            f"{label} escapes the project root"
        ) from exc
    if candidate.is_symlink() or not resolved.is_file():
        raise HanDeltaRepertoireError(
            f"{label} must be a regular non-symlink file"
        )
    return resolved


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HanDeltaRepertoireError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise HanDeltaRepertoireError(
            f"{path}: {label} must be an object"
        )
    return value


def _parse_codepoint(value: Any, *, label: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        codepoint = value
    elif (
        isinstance(value, str)
        and value.startswith("U+")
        and 4 <= len(value.removeprefix("U+")) <= 6
    ):
        try:
            codepoint = int(value.removeprefix("U+"), 16)
        except ValueError as exc:
            raise HanDeltaRepertoireError(
                f"{label} is not a Unicode code point"
            ) from exc
    else:
        raise HanDeltaRepertoireError(
            f"{label} is not a Unicode code point"
        )
    if (
        not 0 <= codepoint <= 0x10FFFF
        or 0xD800 <= codepoint <= 0xDFFF
    ):
        raise HanDeltaRepertoireError(
            f"{label} is not a Unicode scalar"
        )
    return codepoint


def _encoded_codepoints(path: Path) -> set[int]:
    payload = _read_json_object(path, label="excluded repertoire")
    raw_characters = payload.get("characters")
    raw_glyphs = payload.get("glyphs")
    if isinstance(raw_characters, list) and raw_glyphs is None:
        records = raw_characters
    elif isinstance(raw_glyphs, list) and raw_characters is None:
        records = raw_glyphs
    else:
        raise HanDeltaRepertoireError(
            f"{path}: excluded repertoire must contain exactly one "
            "characters or glyphs array"
        )
    codepoints: list[int] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise HanDeltaRepertoireError(
                f"{path}: record {index} must be an object"
            )
        codepoint = _parse_codepoint(
            record.get("codepoint"),
            label=f"{path}: record {index}.codepoint",
        )
        character = record.get("character")
        if character is not None and (
            not isinstance(character, str)
            or len(character) != 1
            or ord(character) != codepoint
        ):
            raise HanDeltaRepertoireError(
                f"{path}: record {index} character/codepoint mismatch"
            )
        codepoints.append(codepoint)
    if len(set(codepoints)) != len(codepoints):
        raise HanDeltaRepertoireError(
            f"{path}: excluded repertoire contains duplicate codepoints"
        )
    return set(codepoints)


def _inventory_rows(path: Path) -> list[dict[str, Any]]:
    try:
        stream = path.open(encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise HanDeltaRepertoireError(
            f"{path}: cannot read Han inventory"
        ) from exc
    with stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != INVENTORY_FIELDS:
            raise HanDeltaRepertoireError(
                f"{path}: Han inventory fields do not match the contract"
            )
        rows: list[dict[str, Any]] = []
        seen: set[int] = set()
        for line_number, raw in enumerate(reader, start=2):
            character = raw["character"]
            if len(character) != 1:
                raise HanDeltaRepertoireError(
                    f"{path}:{line_number}: character is not one scalar"
                )
            codepoint = ord(character)
            if (
                raw["codepoint"] != f"U+{codepoint:04X}"
                or raw["codepoint_decimal"] != str(codepoint)
                or han_block(character) is None
            ):
                raise HanDeltaRepertoireError(
                    f"{path}:{line_number}: Han identity drift"
                )
            if codepoint in seen:
                raise HanDeltaRepertoireError(
                    f"{path}:{line_number}: duplicate codepoint"
                )
            seen.add(codepoint)
            try:
                occurrence_count = int(raw["occurrence_count"])
                source_details = json.loads(raw["source_details"])
            except (ValueError, json.JSONDecodeError) as exc:
                raise HanDeltaRepertoireError(
                    f"{path}:{line_number}: invalid occurrence provenance"
                ) from exc
            if (
                occurrence_count <= 0
                or not isinstance(source_details, dict)
                or any(
                    not isinstance(key, str)
                    or not isinstance(value, int)
                    or value <= 0
                    for key, value in source_details.items()
                )
                or sum(source_details.values()) != occurrence_count
            ):
                raise HanDeltaRepertoireError(
                    f"{path}:{line_number}: occurrence count drift"
                )
            rows.append(
                {
                    "character": character,
                    "codepoint": codepoint,
                    "unicode": f"U+{codepoint:04X}",
                    "unicode_name": raw["unicode_name"],
                    "unicode_block": raw["unicode_block"],
                    "unicode_plane": int(raw["unicode_plane"]),
                    "usage_class": raw["usage_class"],
                    "occurrence_count": occurrence_count,
                    "source_tables": [
                        value
                        for value in raw["source_tables"].split(";")
                        if value
                    ],
                    "source_fields": [
                        value
                        for value in raw["source_fields"].split(";")
                        if value
                    ],
                    "source_occurrences": source_details,
                    "compatibility_mapping": raw[
                        "compatibility_mapping"
                    ],
                }
            )
    if not rows:
        raise HanDeltaRepertoireError(f"{path}: Han inventory is empty")
    return rows


def _dictionary_han_requirements(path: Path) -> set[int]:
    payload = _read_json_object(path, label="font requirements")
    rows = payload.get("requirements")
    if not isinstance(rows, list):
        raise HanDeltaRepertoireError(
            f"{path}: requirements array is missing"
        )
    result: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise HanDeltaRepertoireError(
                f"{path}: requirement {index} is malformed"
            )
        categories = row.get("categories")
        if isinstance(categories, list) and "dictionary_han" in categories:
            result.add(
                _parse_codepoint(
                    row.get("codepoint_decimal"),
                    label=f"{path}: requirement {index}.codepoint",
                )
            )
    if not result:
        raise HanDeltaRepertoireError(
            f"{path}: dictionary_han requirement set is empty"
        )
    return result


def build_dictionary_salience_delta_payload(
    *,
    project_root: Path,
    family_id: str,
    repertoire_id: str,
    batch_prefix: str,
    total_count: int,
    inventory_relative: Path,
    requirements_relative: Path,
    excluded_repertoire_relatives: Sequence[Path],
    authority_source: str,
    authority_jurisdiction: str,
    authority_role: str,
) -> dict[str, Any]:
    """Return one canonical, fully recomputed Han delta payload."""

    project_root = project_root.resolve()
    family_id = _slug(family_id, label="family_id")
    repertoire_id = _slug(repertoire_id, label="repertoire_id")
    batch_prefix = _slug(batch_prefix, label="batch_prefix")
    if (
        not isinstance(total_count, int)
        or isinstance(total_count, bool)
        or total_count <= 0
    ):
        raise HanDeltaRepertoireError("total_count must be positive")
    if not excluded_repertoire_relatives:
        raise HanDeltaRepertoireError(
            "at least one excluded repertoire is required"
        )
    authority = {
        "source": _nonempty(
            authority_source, label="authority.source"
        ),
        "jurisdiction": _nonempty(
            authority_jurisdiction,
            label="authority.jurisdiction",
        ),
        "role": _nonempty(
            authority_role, label="authority.role"
        ),
    }

    inventory_relative = _relative_path(
        inventory_relative.as_posix(),
        label="inventory path",
    )
    requirements_relative = _relative_path(
        requirements_relative.as_posix(),
        label="requirements path",
    )
    inventory_path = _regular_file(
        project_root,
        inventory_relative,
        label="Han inventory",
    )
    requirements_path = _regular_file(
        project_root,
        requirements_relative,
        label="font requirements",
    )
    inventory_rows = _inventory_rows(inventory_path)
    dictionary_han = _dictionary_han_requirements(requirements_path)

    excluded_records: list[dict[str, Any]] = []
    excluded_union: set[int] = set()
    for index, relative in enumerate(excluded_repertoire_relatives):
        relative = _relative_path(
            relative.as_posix(),
            label=f"excluded repertoire {index}",
        )
        path = _regular_file(
            project_root,
            relative,
            label=f"excluded repertoire {index}",
        )
        codepoints = _encoded_codepoints(path)
        excluded_records.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_path(path),
                "encoded_count": len(codepoints),
            }
        )
        excluded_union.update(codepoints)

    candidates = [
        row
        for row in inventory_rows
        if (
            row["codepoint"] in dictionary_han
            and row["codepoint"] not in excluded_union
        )
    ]
    candidates.sort(
        key=lambda row: (
            -int(row["occurrence_count"]),
            int(row["codepoint"]),
        )
    )
    if len(candidates) < total_count:
        raise HanDeltaRepertoireError(
            f"only {len(candidates)} dictionary Han candidates remain; "
            f"cannot select {total_count}"
        )
    selected = candidates[:total_count]
    selected_codepoints = {
        int(record["codepoint"]) for record in selected
    }
    if not selected_codepoints <= dictionary_han:
        unexpected = sorted(selected_codepoints - dictionary_han)
        raise HanDeltaRepertoireError(
            "selection contains codepoints outside dictionary_han: "
            + " ".join(f"U+{value:04X}" for value in unexpected[:8])
        )
    if selected_codepoints & excluded_union:
        raise HanDeltaRepertoireError(
            "selection overlaps the existing encoded repertoire"
        )

    character_records = [
        {
            "rank": rank,
            **record,
        }
        for rank, record in enumerate(selected, start=1)
    ]
    characters = "".join(
        str(record["character"]) for record in selected
    )
    codepoint_lines = "".join(
        f"U+{int(record['codepoint']):04X}\n"
        for record in selected
    )
    batches: list[dict[str, Any]] = []
    for start in range(0, total_count, GRID_CAPACITY):
        records = selected[start : start + GRID_CAPACITY]
        number = len(batches) + 1
        batch_id = f"{batch_prefix}-{number:04d}"
        batch_characters = "".join(
            str(record["character"]) for record in records
        )
        batches.append(
            {
                "batch_id": batch_id,
                "start_rank": start + 1,
                "end_rank": start + len(records),
                "character_count": len(records),
                "grid_capacity": GRID_CAPACITY,
                "empty_grid_cells": GRID_CAPACITY - len(records),
                "characters": batch_characters,
                "codepoints": [
                    f"U+{int(record['codepoint']):04X}"
                    for record in records
                ],
                "raster_path": (
                    f"sources/imagegen/raster/{batch_id}.png"
                ),
            }
        )

    return {
        "schema_version": 1,
        "record_type": RECORD_TYPE,
        "family_id": family_id,
        "repertoire_id": repertoire_id,
        "normalization": "NFC",
        "total_count": total_count,
        "batch_prefix": batch_prefix,
        "grid": {
            "rows": GRID_ROWS,
            "columns": GRID_COLUMNS,
            "capacity": GRID_CAPACITY,
            "order": "row-major",
            "unused_cells": "trailing-and-empty",
        },
        "authority": authority,
        "selection": {
            "strategy": SELECTION_STRATEGY,
            "candidate_set": "dictionary_han",
            "ordering": [
                "occurrence_count DESC",
                "codepoint ASC",
            ],
            "exclusion": (
                "all codepoints encoded by excluded repertoires"
            ),
            "selected_count": total_count,
            "first_occurrence_count": int(
                selected[0]["occurrence_count"]
            ),
            "last_occurrence_count": int(
                selected[-1]["occurrence_count"]
            ),
        },
        "provenance": {
            "builder": BUILDER_ID,
            "inventory": {
                "path": inventory_relative.as_posix(),
                "sha256": sha256_path(inventory_path),
                "row_count": len(inventory_rows),
            },
            "requirements": {
                "path": requirements_relative.as_posix(),
                "sha256": sha256_path(requirements_path),
                "dictionary_han_count": len(dictionary_han),
            },
            "excluded_repertoires": excluded_records,
            "existing_encoded_union_count": len(excluded_union),
            "sequence_sha256": _sha256_text(characters),
            "codepoint_lines_sha256": _sha256_text(
                codepoint_lines,
                encoding="ascii",
            ),
        },
        "characters": character_records,
        "batches": batches,
    }


def validate_payload(
    payload: Mapping[str, Any],
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Recompute and require byte-semantic equality with one payload."""

    if not isinstance(payload, dict):
        raise HanDeltaRepertoireError(
            "Han delta repertoire must be a JSON object"
        )
    expected_top_level = {
        "schema_version",
        "record_type",
        "family_id",
        "repertoire_id",
        "normalization",
        "total_count",
        "batch_prefix",
        "grid",
        "authority",
        "selection",
        "provenance",
        "characters",
        "batches",
    }
    if set(payload) != expected_top_level:
        raise HanDeltaRepertoireError(
            "Han delta repertoire has an invalid top-level key set"
        )
    if (
        payload.get("schema_version") != 1
        or payload.get("record_type") != RECORD_TYPE
        or payload.get("normalization") != "NFC"
    ):
        raise HanDeltaRepertoireError(
            "unsupported Han delta repertoire contract"
        )
    if payload.get("grid") != {
        "rows": GRID_ROWS,
        "columns": GRID_COLUMNS,
        "capacity": GRID_CAPACITY,
        "order": "row-major",
        "unused_cells": "trailing-and-empty",
    }:
        raise HanDeltaRepertoireError(
            "Han delta grid contract drifted"
        )
    selection = payload.get("selection")
    if (
        not isinstance(selection, dict)
        or selection.get("strategy") != SELECTION_STRATEGY
    ):
        raise HanDeltaRepertoireError(
            "unsupported Han delta selection strategy"
        )
    authority = payload.get("authority")
    provenance = payload.get("provenance")
    if (
        not isinstance(authority, dict)
        or set(authority)
        != {"source", "jurisdiction", "role"}
        or not isinstance(provenance, dict)
    ):
        raise HanDeltaRepertoireError(
            "Han delta authority or provenance is malformed"
        )
    inventory = provenance.get("inventory")
    requirements = provenance.get("requirements")
    excluded = provenance.get("excluded_repertoires")
    if (
        not isinstance(inventory, dict)
        or not isinstance(requirements, dict)
        or not isinstance(excluded, list)
        or not excluded
    ):
        raise HanDeltaRepertoireError(
            "Han delta input provenance is incomplete"
        )
    try:
        excluded_paths = [
            _relative_path(
                record["path"],
                label=f"excluded repertoire {index}",
            )
            for index, record in enumerate(excluded)
            if isinstance(record, dict)
        ]
    except KeyError as exc:
        raise HanDeltaRepertoireError(
            "excluded repertoire path is missing"
        ) from exc
    if len(excluded_paths) != len(excluded):
        raise HanDeltaRepertoireError(
            "excluded repertoire record is malformed"
        )

    rebuilt = build_dictionary_salience_delta_payload(
        project_root=project_root,
        family_id=_slug(
            payload.get("family_id"),
            label="family_id",
        ),
        repertoire_id=_slug(
            payload.get("repertoire_id"),
            label="repertoire_id",
        ),
        batch_prefix=_slug(
            payload.get("batch_prefix"),
            label="batch_prefix",
        ),
        total_count=payload.get("total_count"),
        inventory_relative=_relative_path(
            inventory.get("path"),
            label="inventory path",
        ),
        requirements_relative=_relative_path(
            requirements.get("path"),
            label="requirements path",
        ),
        excluded_repertoire_relatives=excluded_paths,
        authority_source=authority.get("source"),
        authority_jurisdiction=authority.get("jurisdiction"),
        authority_role=authority.get("role"),
    )
    if payload != rebuilt:
        raise HanDeltaRepertoireError(
            "Han delta repertoire does not equal the recomputed "
            "dictionary-salience selection"
        )
    return rebuilt


def load_repertoire(
    path: Path = ROOT / DEFAULT_OUTPUT,
    *,
    project_root: Path = ROOT,
) -> HanDeltaRepertoire:
    """Load a frozen repertoire and independently recompute every record."""

    project_root = project_root.resolve()
    path = path.resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise HanDeltaRepertoireError(
            "repertoire path must remain below the project root"
        ) from exc
    if path.is_symlink() or not path.is_file():
        raise HanDeltaRepertoireError(
            f"repertoire must be a regular non-symlink file: {path}"
        )
    payload = validate_payload(
        _read_json_object(path, label="Han delta repertoire"),
        project_root=project_root,
    )
    characters = tuple(
        str(record["character"]) for record in payload["characters"]
    )
    batches = tuple(
        HanDeltaBatch(
            batch_id=str(record["batch_id"]),
            start_rank=int(record["start_rank"]),
            end_rank=int(record["end_rank"]),
            characters=tuple(str(record["characters"])),
            empty_grid_cells=int(record["empty_grid_cells"]),
        )
        for record in payload["batches"]
    )
    if len(batches) != math.ceil(len(characters) / GRID_CAPACITY):
        raise HanDeltaRepertoireError(
            "Han delta batch cardinality drifted"
        )
    return HanDeltaRepertoire(
        path=path,
        sha256=sha256_path(path),
        family_id=str(payload["family_id"]),
        repertoire_id=str(payload["repertoire_id"]),
        batch_prefix=str(payload["batch_prefix"]),
        sequence_sha256=str(
            payload["provenance"]["sequence_sha256"]
        ),
        characters=characters,
        batches=batches,
        payload=payload,
    )


def write_repertoire(
    *,
    output: Path,
    project_root: Path,
    family_id: str,
    repertoire_id: str,
    batch_prefix: str,
    total_count: int,
    inventory_relative: Path,
    requirements_relative: Path,
    excluded_repertoire_relatives: Sequence[Path],
    authority_source: str,
    authority_jurisdiction: str,
    authority_role: str,
) -> Path:
    """Write one canonical repertoire, refusing unsafe destinations."""

    project_root = project_root.resolve()
    output = output.resolve()
    _project_relative(
        output,
        project_root=project_root,
        label="output",
    )
    payload = build_dictionary_salience_delta_payload(
        project_root=project_root,
        family_id=family_id,
        repertoire_id=repertoire_id,
        batch_prefix=batch_prefix,
        total_count=total_count,
        inventory_relative=inventory_relative,
        requirements_relative=requirements_relative,
        excluded_repertoire_relatives=excluded_repertoire_relatives,
        authority_source=authority_source,
        authority_jurisdiction=authority_jurisdiction,
        authority_role=authority_role,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    if output.exists() and output.read_text(encoding="utf-8") != encoded:
        raise HanDeltaRepertoireError(
            f"refusing to overwrite a different repertoire: {output}"
        )
    output.write_text(encoded, encoding="utf-8")
    load_repertoire(output, project_root=project_root)
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
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    build = subparsers.add_parser(
        "build",
        help="build one dictionary-salience Han delta",
    )
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--family-id", required=True)
    build.add_argument("--repertoire-id", required=True)
    build.add_argument("--batch-prefix", required=True)
    build.add_argument("--count", type=int, required=True)
    build.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY,
    )
    build.add_argument(
        "--requirements",
        type=Path,
        default=DEFAULT_REQUIREMENTS,
    )
    build.add_argument(
        "--exclude-repertoire",
        type=Path,
        action="append",
        required=True,
    )
    build.add_argument("--authority-source", required=True)
    build.add_argument("--authority-jurisdiction", required=True)
    build.add_argument("--authority-role", required=True)

    validate = subparsers.add_parser(
        "validate",
        help="recompute and validate one frozen Han delta",
    )
    validate.add_argument("repertoire", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    if args.command == "build":
        output = args.output
        if not output.is_absolute():
            output = project_root / output
        path = write_repertoire(
            output=output,
            project_root=project_root,
            family_id=args.family_id,
            repertoire_id=args.repertoire_id,
            batch_prefix=args.batch_prefix,
            total_count=args.count,
            inventory_relative=args.inventory,
            requirements_relative=args.requirements,
            excluded_repertoire_relatives=args.exclude_repertoire,
            authority_source=args.authority_source,
            authority_jurisdiction=args.authority_jurisdiction,
            authority_role=args.authority_role,
        )
        print(path)
        return 0
    repertoire = args.repertoire
    if not repertoire.is_absolute():
        repertoire = project_root / repertoire
    validated = load_repertoire(
        repertoire,
        project_root=project_root,
    )
    print(
        f"validated {len(validated.characters)} Han glyphs in "
        f"{len(validated.batches)} batches"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
