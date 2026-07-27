#!/usr/bin/env python3
"""Load the Ministry of Education's frozen 4,808 common-character table."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
from pathlib import Path

from scripts.inventory import han_block


ROOT = Path(__file__).resolve().parents[1]
MOE_COMMON = ROOT / "inventories/moe-common-4808.csv"
SOURCE_URL = (
    "https://language.moe.gov.tw/material/"
    "info?m=9fe3ff5a-5a8c-4817-9e60-6337dd55a509"
)
EXPECTED_SHA256 = (
    "fba1faf2568e66d9c3a32fc97f3e1d6be660a0af3f392ec6d3dc9bf885912405"
)
EXPECTED_COUNT = 4808
EXPECTED_FIELDS = ("流水序", "教育部字號", "Unicode", "常用字")


class MoeCommonError(RuntimeError):
    """The frozen Ministry of Education table is malformed or has drifted."""


@dataclass(frozen=True)
class MoeCommonRecord:
    sequence: int
    moe_id: str
    character: str
    codepoint: int
    source_unicode_field: int


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_moe_common(path: Path = MOE_COMMON) -> tuple[MoeCommonRecord, ...]:
    """Return 4,808 validated records in the Ministry's published order."""

    if _sha256(path) != EXPECTED_SHA256:
        raise MoeCommonError(f"{path}: unexpected SHA-256")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != EXPECTED_FIELDS:
            raise MoeCommonError(f"{path}: unexpected CSV columns")
        rows = list(reader)
    if len(rows) != EXPECTED_COUNT:
        raise MoeCommonError(
            f"{path}: expected {EXPECTED_COUNT} records, found {len(rows)}"
        )

    records: list[MoeCommonRecord] = []
    for sequence, row in enumerate(rows, start=1):
        expected_sequence = f"{sequence:05d}"
        expected_moe_id = f"A{sequence:05d}"
        if (
            row["流水序"] != expected_sequence
            or row["教育部字號"] != expected_moe_id
        ):
            raise MoeCommonError(f"{path}: sequence drift at record {sequence}")
        character = row["常用字"]
        if len(character) != 1 or han_block(character) is None:
            raise MoeCommonError(
                f"{path}: record {expected_moe_id} is not one Han scalar"
            )
        try:
            source_codepoint = int(row["Unicode"], 16)
        except ValueError as exc:
            raise MoeCommonError(
                f"{path}: invalid Unicode field at {expected_moe_id}"
            ) from exc
        codepoint = ord(character)

        # The supplied Ministry CSV has one known field typo. The Ministry's
        # current character entry identifies A02149 as 汨, U+6C68; the CSV's
        # Unicode column says U+6C69. Preserve the source bytes, but take the
        # published character and Ministry ID as the identity.
        if expected_moe_id == "A02149":
            if (source_codepoint, codepoint) != (0x6C69, 0x6C68):
                raise MoeCommonError(f"{path}: A02149 erratum changed")
        elif source_codepoint != codepoint:
            raise MoeCommonError(
                f"{path}: character/codepoint mismatch at {expected_moe_id}"
            )
        records.append(
            MoeCommonRecord(
                sequence=sequence,
                moe_id=expected_moe_id,
                character=character,
                codepoint=codepoint,
                source_unicode_field=source_codepoint,
            )
        )

    codepoints = {record.codepoint for record in records}
    if len(codepoints) != EXPECTED_COUNT:
        raise MoeCommonError(f"{path}: duplicate common characters")
    return tuple(records)

