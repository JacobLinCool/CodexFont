#!/usr/bin/env python3
"""Validate and load the frozen project requirement inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import unicodedata
from typing import Any

from scripts.inventory import han_block, unicode_name


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "inventories/font_requirements.json"
POLICY = (
    "dictionary-printable + Taiwan-CP950-Han + "
    "frozen-project-repertoire-v1"
)
INPUT_PATHS = {
    "inventory": Path("inventories/han_characters.txt"),
    "dictionary_text": Path("inventories/dictionary_required_codepoints.txt"),
}
EXPECTED_COUNTS = {
    "all_required": 18_071,
    "outline_required": 18_054,
    "dictionary_text": 12_306,
    "dictionary_han": 11_958,
    "taiwan_big5": 13_058,
}
EMPTY_SPACING_CODEPOINTS = {
    0x0020,
    0x00A0,
    0x2000,
    0x2001,
    0x2002,
    0x2003,
    0x2004,
    0x2005,
    0x2006,
    0x2007,
    0x2008,
    0x2009,
    0x200A,
    0x202F,
    0x205F,
    0x3000,
}
SEMANTIC_EMPTY_CODEPOINTS = EMPTY_SPACING_CODEPOINTS | {0x034F}
ROW_KEYS = {
    "character",
    "codepoint",
    "codepoint_decimal",
    "unicode_name",
    "general_category",
    "categories",
    "outline_required",
}


class RequirementInventoryError(ValueError):
    """The frozen requirement inventory is malformed or stale."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_han_character_list(path: Path) -> set[int]:
    """Read a canonical one-scalar-per-line Han inventory."""

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Han inventory is empty: {path}")
    codepoints: list[int] = []
    previous = -1
    for line_number, line in enumerate(lines, start=1):
        if len(line) != 1:
            raise ValueError(
                f"Han inventory line {line_number} must contain exactly one "
                "Unicode scalar"
            )
        codepoint = ord(line)
        if han_block(line) is None:
            raise ValueError(
                f"Han inventory line {line_number} is not a Han scalar: "
                f"U+{codepoint:04X}"
            )
        if codepoint <= previous:
            relation = "duplicate" if codepoint == previous else "out of order"
            raise ValueError(
                f"Han inventory line {line_number} is {relation}: "
                f"U+{codepoint:04X}"
            )
        codepoints.append(codepoint)
        previous = codepoint
    return set(codepoints)


def read_codepoint_list(path: Path) -> set[int]:
    return {
        int(line.strip().removeprefix("U+"), 16)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _validate_inputs(
    inputs: object,
    *,
    root: Path,
) -> None:
    if not isinstance(inputs, dict) or set(inputs) != set(INPUT_PATHS):
        raise RequirementInventoryError(
            "inputs must contain only inventory and dictionary_text"
        )
    for identifier, expected_relative in INPUT_PATHS.items():
        record = inputs[identifier]
        if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
            raise RequirementInventoryError(
                f"invalid input record: {identifier}"
            )
        if not isinstance(record["path"], str) or not isinstance(
            record["sha256"], str
        ):
            raise RequirementInventoryError(
                f"invalid input value types: {identifier}"
            )
        relative = Path(record["path"])
        if (
            relative != expected_relative
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise RequirementInventoryError(
                f"input path must be repository-relative: {identifier}"
            )
        source = root / relative
        if not source.is_file():
            raise RequirementInventoryError(f"missing input: {relative}")
        if record["sha256"] != sha256(source):
            raise RequirementInventoryError(f"stale input hash: {relative}")


def _validate_row(
    row: object,
    *,
    previous: int,
) -> tuple[int, set[str], bool]:
    if not isinstance(row, dict) or set(row) != ROW_KEYS:
        raise RequirementInventoryError("requirement row has invalid keys")
    codepoint = row["codepoint_decimal"]
    if not isinstance(codepoint, int) or not 0 <= codepoint <= 0x10FFFF:
        raise RequirementInventoryError("invalid Unicode scalar")
    if codepoint <= previous:
        raise RequirementInventoryError(
            f"requirement rows are duplicate or out of order: U+{codepoint:04X}"
        )
    character = chr(codepoint)
    if row["character"] != character:
        raise RequirementInventoryError(
            f"character mismatch: U+{codepoint:04X}"
        )
    if row["codepoint"] != f"U+{codepoint:04X}":
        raise RequirementInventoryError(
            f"codepoint label mismatch: U+{codepoint:04X}"
        )
    if row["unicode_name"] != unicode_name(character):
        raise RequirementInventoryError(
            f"Unicode name mismatch: U+{codepoint:04X}"
        )
    if row["general_category"] != unicodedata.category(character):
        raise RequirementInventoryError(
            f"general category mismatch: U+{codepoint:04X}"
        )
    categories = row["categories"]
    if (
        not isinstance(categories, list)
        or not categories
        or not all(isinstance(value, str) and value for value in categories)
    ):
        raise RequirementInventoryError(
            f"invalid categories: U+{codepoint:04X}"
        )
    if categories != sorted(set(categories)):
        raise RequirementInventoryError(
            f"categories are duplicate or out of order: U+{codepoint:04X}"
        )
    outline_required = row["outline_required"]
    if (
        not isinstance(outline_required, bool)
        or outline_required != (codepoint not in SEMANTIC_EMPTY_CODEPOINTS)
    ):
        raise RequirementInventoryError(
            f"outline policy mismatch: U+{codepoint:04X}"
        )
    return codepoint, set(categories), outline_required


def validate(
    path: Path = DEFAULT_INVENTORY,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "policy",
        "inputs",
        "counts",
        "requirements",
    }:
        raise RequirementInventoryError("invalid top-level inventory contract")
    if payload["schema_version"] != 1 or payload["policy"] != POLICY:
        raise RequirementInventoryError("unsupported inventory contract")
    _validate_inputs(payload["inputs"], root=root)
    rows = payload["requirements"]
    if not isinstance(rows, list):
        raise RequirementInventoryError("requirements must be a list")

    previous = -1
    categories: dict[int, set[str]] = {}
    outline_required: dict[int, bool] = {}
    for row in rows:
        codepoint, values, required = _validate_row(row, previous=previous)
        categories[codepoint] = values
        outline_required[codepoint] = required
        previous = codepoint

    counts = {
        "all_required": len(categories),
        "outline_required": sum(outline_required.values()),
        "dictionary_text": sum(
            "dictionary_text" in values for values in categories.values()
        ),
        "dictionary_han": sum(
            "dictionary_han" in values for values in categories.values()
        ),
        "taiwan_big5": sum(
            "taiwan_big5" in values for values in categories.values()
        ),
    }
    if payload["counts"] != EXPECTED_COUNTS or counts != EXPECTED_COUNTS:
        raise RequirementInventoryError("requirement counts do not match contract")
    return payload


def load_requirements(
    path: Path = DEFAULT_INVENTORY,
) -> tuple[set[int], dict[int, set[str]], dict[int, bool]]:
    payload = validate(path)
    categories = {
        int(row["codepoint_decimal"]): set(row["categories"])
        for row in payload["requirements"]
    }
    outline_required = {
        int(row["codepoint_decimal"]): bool(row["outline_required"])
        for row in payload["requirements"]
    }
    return set(categories), categories, outline_required


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv or sys.argv[1:])
    payload = validate(arguments.inventory)
    print(json.dumps(payload["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
