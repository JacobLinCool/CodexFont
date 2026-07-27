#!/usr/bin/env python3
"""Freeze the 1,844 Ministry-common Han characters missing from the base font."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata

from scripts.moe_common import (
    EXPECTED_SHA256,
    MOE_COMMON,
    SOURCE_URL,
    load_moe_common,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_REPERTOIRE = (
    ROOT / "sources/imagegen/repertoires/common-3000.json"
)
OUTPUT = (
    ROOT / "sources/imagegen/repertoires/moe-common-extension-1844.json"
)
TEXT_OUTPUT = ROOT / "inventories/moe-common-extension-1844.txt"
EXPECTED_EXTENSION_COUNT = 1844
BATCH_CAPACITY = 16


class ExtensionBuildError(RuntimeError):
    """The frozen extension cannot be derived exactly."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build() -> tuple[Path, Path]:
    base = json.loads(BASE_REPERTOIRE.read_text(encoding="utf-8"))
    base_characters = {
        record["character"] for record in base["characters"]
    }
    if len(base_characters) != 3000:
        raise ExtensionBuildError("base repertoire must contain 3,000 glyphs")

    extension = [
        record
        for record in load_moe_common()
        if record.character not in base_characters
    ]
    if len(extension) != EXPECTED_EXTENSION_COUNT:
        raise ExtensionBuildError(
            f"expected {EXPECTED_EXTENSION_COUNT} missing characters, "
            f"found {len(extension)}"
        )
    characters = "".join(record.character for record in extension)
    codepoint_lines = "".join(
        f"U+{record.codepoint:04X}\n" for record in extension
    )
    batches = []
    for start in range(0, len(extension), BATCH_CAPACITY):
        records = extension[start : start + BATCH_CAPACITY]
        number = len(batches) + 1
        batches.append(
            {
                "batch_id": f"moe-common-{number:04d}",
                "start_rank": start + 1,
                "end_rank": start + len(records),
                "character_count": len(records),
                "grid_capacity": BATCH_CAPACITY,
                "empty_grid_cells": BATCH_CAPACITY - len(records),
                "characters": "".join(
                    record.character for record in records
                ),
                "codepoints": [
                    f"U+{record.codepoint:04X}" for record in records
                ],
                "raster_path": (
                    f"sources/imagegen/raster/moe-common-{number:04d}.png"
                ),
            }
        )

    payload = {
        "schema_version": 1,
        "repertoire_id": "tw-moe-common-4808-extension-1844-v1",
        "normalization": "NFC",
        "total_count": len(extension),
        "authority": {
            "source": "教育部《常用國字標準字體表》4,808 字",
            "source_url": SOURCE_URL,
            "published": "1982-09-01",
            "jurisdiction": "Taiwan",
            "role": "0.1 Preview common-Han completion gate",
        },
        "provenance": {
            "table_path": MOE_COMMON.relative_to(ROOT).as_posix(),
            "table_sha256": EXPECTED_SHA256,
            "base_repertoire_path": BASE_REPERTOIRE.relative_to(
                ROOT
            ).as_posix(),
            "base_repertoire_sha256": _sha256(BASE_REPERTOIRE),
            "selection": (
                "Ministry table order, excluding characters already present "
                "in common-3000.json"
            ),
            "sequence_sha256": _sha256_bytes(
                characters.encode("utf-8")
            ),
            "codepoint_lines_sha256": _sha256_bytes(
                codepoint_lines.encode("ascii")
            ),
            "known_source_errata": [
                {
                    "moe_id": "A02149",
                    "character": "汨",
                    "source_unicode_field": "U+6C69",
                    "correct_codepoint": "U+6C68",
                    "identity_basis": "Ministry ID and published character",
                }
            ],
        },
        "characters": [
            {
                "rank": rank,
                "moe_sequence": record.sequence,
                "moe_id": record.moe_id,
                "character": record.character,
                "codepoint": record.codepoint,
                "unicode": f"U+{record.codepoint:04X}",
                "unicode_name": unicodedata.name(record.character),
            }
            for rank, record in enumerate(extension, start=1)
        ],
        "batches": batches,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    TEXT_OUTPUT.write_text(codepoint_lines, encoding="ascii")
    return OUTPUT, TEXT_OUTPUT


def main() -> None:
    for path in build():
        print(path)


if __name__ == "__main__":
    main()
