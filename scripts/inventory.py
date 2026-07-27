#!/usr/bin/env python3
"""Extract every Han character from the dictionary SQLite database.

The database is a compact lookup database rather than the original workbook.
`entries.readings` stores structured JSON.  This script scans logical JSON text
leaves instead of treating JSON punctuation as dictionary content, records the
exact table/field provenance of every occurrence, and handles supplementary
Unicode planes through Python's full code-point strings.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


HAN_BLOCKS: tuple[tuple[int, int, str], ...] = (
    (0x3007, 0x3007, "CJK Symbols and Punctuation (Ideographic Zero)"),
    (0x3400, 0x4DBF, "CJK Unified Ideographs Extension A"),
    (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    (0xF900, 0xFAFF, "CJK Compatibility Ideographs"),
    (0x20000, 0x2A6DF, "CJK Unified Ideographs Extension B"),
    (0x2A700, 0x2B73F, "CJK Unified Ideographs Extension C"),
    (0x2B740, 0x2B81F, "CJK Unified Ideographs Extension D"),
    (0x2B820, 0x2CEAF, "CJK Unified Ideographs Extension E"),
    (0x2CEB0, 0x2EBEF, "CJK Unified Ideographs Extension F"),
    (0x2EBF0, 0x2EE5F, "CJK Unified Ideographs Extension I"),
    (0x2F800, 0x2FA1F, "CJK Compatibility Ideographs Supplement"),
    (0x30000, 0x3134F, "CJK Unified Ideographs Extension G"),
    (0x31350, 0x323AF, "CJK Unified Ideographs Extension H"),
    (0x323B0, 0x3347F, "CJK Unified Ideographs Extension J"),
    (0xF0000, 0xFFFFD, "Supplementary Private Use Area-A (dictionary gaiji)"),
)

VARIANT_RE = re.compile(r"[「『](?P<target>.)[」』][^。；;]{0,12}異體字")


@dataclass(frozen=True)
class CharacterRecord:
    character: str
    codepoint: str
    codepoint_decimal: int
    unicode_name: str
    unicode_block: str
    unicode_plane: int
    usage_class: str
    occurrence_count: int
    source_tables: str
    source_fields: str
    source_details: str
    compatibility_mapping: str
    glyph_designed: bool
    quality_checked: bool


@dataclass(frozen=True)
class DatabaseCodepointRecord:
    character: str
    codepoint: str
    codepoint_decimal: int
    unicode_name: str
    general_category: str
    occurrence_count: int
    source_tables: str
    source_fields: str
    source_details: str
    required_in_font: bool
    requirement_reason: str
    glyph_verified: bool


def han_block(char: str) -> str | None:
    cp = ord(char)
    for start, end, name in HAN_BLOCKS:
        if start <= cp <= end:
            return name
    return None


def unicode_name(char: str) -> str:
    try:
        return unicodedata.name(char)
    except ValueError:
        if 0xF0000 <= ord(char) <= 0xFFFFD:
            return f"PRIVATE USE CHARACTER-{ord(char):X}"
        if han_block(char):
            return f"CJK UNIFIED IDEOGRAPH-{ord(char):X}"
        return "<UNASSIGNED>"


def big5_level(char: str) -> str | None:
    """Return the conventional Big5 level for a single Han character.

    Big5 level 1 occupies lead bytes A4-C6 and level 2 occupies C9-F9.
    CP950 is intentionally used as the operational Taiwan mapping.  Characters
    outside these byte bands are classified separately, not silently discarded.
    """

    try:
        encoded = char.encode("cp950")
    except UnicodeEncodeError:
        return None
    if len(encoded) != 2:
        return None
    lead = encoded[0]
    if 0xA4 <= lead <= 0xC6:
        return "common_big5_level_1"
    if 0xC9 <= lead <= 0xF9:
        return "secondary_big5_level_2"
    return "big5_extension_or_symbol"


def usage_class(char: str, block: str) -> str:
    if "Private Use" in block:
        return "dictionary_private_use_gaiji"
    level = big5_level(char)
    if level:
        return level
    if "Extension" in block:
        return "unicode_extension"
    if "Compatibility" in block:
        return "compatibility_ideograph"
    return "rare_or_unclassified"


def iter_json_text(value: Any, path: str = "readings") -> Iterator[tuple[str, str]]:
    """Yield `(logical_path, text)` for every string leaf in JSON data."""

    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        child_path = f"{path}[]"
        for item in value:
            yield from iter_json_text(item, child_path)
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from iter_json_text(value[key], f"{path}[].{key}" if path == "readings" else f"{path}.{key}")


def compatibility_mapping(char: str) -> str:
    normalized = unicodedata.normalize("NFKC", char)
    if normalized == char:
        return ""
    return " ".join(f"U+{ord(item):04X}" for item in normalized)


def db_schema(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    names = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )]
    for name in names:
        columns = []
        for cid, col_name, col_type, not_null, default, primary_key in connection.execute(
            f'PRAGMA table_info("{name}")'
        ):
            columns.append(
                {
                    "name": col_name,
                    "type": col_type,
                    "not_null": bool(not_null),
                    "default": default,
                    "primary_key_position": primary_key,
                }
            )
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()[0]
        count = connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        tables.append({"name": name, "row_count": count, "columns": columns, "sql": sql})
    return tables


def scan_database(
    database: Path,
) -> tuple[
    collections.Counter[str],
    dict[str, collections.Counter[str]],
    collections.Counter[str],
    dict[str, collections.Counter[str]],
    list[dict[str, str]],
    dict[str, Any],
]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    schema = db_schema(connection)
    encoding = connection.execute("PRAGMA encoding").fetchone()[0]
    metadata = dict(connection.execute("SELECT k, v FROM meta ORDER BY k"))

    counts: collections.Counter[str] = collections.Counter()
    provenance: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    text_counts: collections.Counter[str] = collections.Counter()
    text_provenance: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    variant_relations: list[dict[str, str]] = []
    json_errors: list[dict[str, Any]] = []
    scanned_paths: collections.Counter[str] = collections.Counter()

    def add_text(text: str, source: str) -> None:
        scanned_paths[source] += 1
        for char in text:
            text_counts[char] += 1
            text_provenance[char][source] += 1
            if han_block(char):
                counts[char] += 1
                provenance[char][source] += 1

    for row_number, row in enumerate(
        connection.execute("SELECT key, readings FROM entries ORDER BY key"), start=1
    ):
        key = row["key"] or ""
        add_text(key, "entries.key")
        raw = row["readings"] or ""
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as error:
            json_errors.append(
                {"row": row_number, "key": key, "error": str(error), "value": raw[:240]}
            )
            continue
        for logical_path, text in iter_json_text(parsed):
            source = f"entries.{logical_path}"
            add_text(text, source)
            if logical_path.endswith(".gloss") and len(key) == 1 and han_block(key):
                for match in VARIANT_RE.finditer(text):
                    target = match.group("target")
                    if han_block(target):
                        variant_relations.append(
                            {
                                "variant": key,
                                "variant_codepoint": f"U+{ord(key):04X}",
                                "standard": target,
                                "standard_codepoint": f"U+{ord(target):04X}",
                                "relation": "dictionary_gloss_variant",
                                "source": source,
                            }
                        )

    for char in sorted(counts, key=ord):
        normalized = unicodedata.normalize("NFKC", char)
        if normalized != char and len(normalized) == 1 and han_block(normalized):
            variant_relations.append(
                {
                    "variant": char,
                    "variant_codepoint": f"U+{ord(char):04X}",
                    "standard": normalized,
                    "standard_codepoint": f"U+{ord(normalized):04X}",
                    "relation": "unicode_compatibility_mapping",
                    "source": "Unicode NFKC",
                }
            )

    audit = {
        "database": str(database),
        "encoding": encoding,
        "sqlite_version": sqlite3.sqlite_version,
        "python_unicode_version": unicodedata.unidata_version,
        "metadata": metadata,
        "schema": schema,
        "scanned_logical_fields": dict(sorted(scanned_paths.items())),
        "json_error_count": len(json_errors),
        "json_errors": json_errors,
        "dictionary_text_occurrences": sum(text_counts.values()),
        "dictionary_text_unique_codepoints": len(text_counts),
        "excluded_format_or_control_codepoints": [
            {
                "character": char,
                "codepoint": f"U+{ord(char):04X}",
                "name": unicode_name(char),
                "category": unicodedata.category(char),
                "occurrence_count": text_counts[char],
            }
            for char in sorted(text_counts, key=ord)
            if unicodedata.category(char) in {"Cc", "Cf", "Cs"}
        ],
    }
    connection.close()
    unique_relations = {
        (item["variant_codepoint"], item["standard_codepoint"], item["relation"]): item
        for item in variant_relations
    }
    return (
        counts,
        provenance,
        text_counts,
        text_provenance,
        list(unique_relations.values()),
        audit,
    )


def read_verified_codepoints(path: Path | None) -> set[int]:
    if path is None or not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict) and isinstance(
        payload.get("valid_codepoints"), list
    ):
        values = payload["valid_codepoints"]
    elif isinstance(payload, dict) and isinstance(payload.get("glyphs"), list):
        values = [
            record["codepoint"]
            for record in payload["glyphs"]
            if isinstance(record, dict) and "codepoint" in record
        ]
        if len(values) != len(payload["glyphs"]):
            raise ValueError(f"{path}: every glyph record must declare codepoint")
    else:
        raise ValueError(
            f"{path}: expected a codepoint list, valid_codepoints list, "
            "or release report glyph list"
        )

    verified: set[int] = set()
    for value in values:
        if isinstance(value, int):
            codepoint = value
        elif isinstance(value, str):
            normalized = value.strip()
            if normalized.upper().startswith("U+"):
                normalized = normalized[2:]
            codepoint = int(normalized, 16)
        else:
            raise ValueError(f"{path}: invalid codepoint value {value!r}")
        if not 0 <= codepoint <= 0x10FFFF:
            raise ValueError(f"{path}: codepoint out of Unicode range: {codepoint}")
        verified.add(codepoint)
    if len(verified) != len(values):
        raise ValueError(f"{path}: duplicate verified codepoints")
    return verified


def make_records(
    counts: collections.Counter[str],
    provenance: dict[str, collections.Counter[str]],
    verified: set[int],
) -> list[CharacterRecord]:
    records: list[CharacterRecord] = []
    for char in sorted(counts, key=ord):
        block = han_block(char)
        assert block is not None
        details = provenance[char]
        sources = sorted(details)
        tables = sorted({source.split(".", 1)[0] for source in sources})
        records.append(
            CharacterRecord(
                character=char,
                codepoint=f"U+{ord(char):04X}",
                codepoint_decimal=ord(char),
                unicode_name=unicode_name(char),
                unicode_block=block,
                unicode_plane=ord(char) >> 16,
                usage_class=usage_class(char, block),
                occurrence_count=counts[char],
                source_tables=";".join(tables),
                source_fields=";".join(sources),
                source_details=json.dumps(dict(sorted(details.items())), ensure_ascii=False, separators=(",", ":")),
                compatibility_mapping=compatibility_mapping(char),
                glyph_designed=ord(char) in verified,
                quality_checked=ord(char) in verified,
            )
        )
    return records


def make_database_codepoint_records(
    counts: collections.Counter[str],
    provenance: dict[str, collections.Counter[str]],
    verified: set[int],
) -> list[DatabaseCodepointRecord]:
    records: list[DatabaseCodepointRecord] = []
    excluded_categories = {"Cc", "Cf", "Cs"}
    for char in sorted(counts, key=ord):
        details = provenance[char]
        sources = sorted(details)
        tables = sorted({source.split(".", 1)[0] for source in sources})
        category = unicodedata.category(char)
        required = category not in excluded_categories
        records.append(
            DatabaseCodepointRecord(
                character=char,
                codepoint=f"U+{ord(char):04X}",
                codepoint_decimal=ord(char),
                unicode_name=unicode_name(char),
                general_category=category,
                occurrence_count=counts[char],
                source_tables=";".join(tables),
                source_fields=";".join(sources),
                source_details=json.dumps(
                    dict(sorted(details.items())),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                required_in_font=required,
                requirement_reason=(
                    "printable_scalar_in_dictionary_text"
                    if required
                    else "excluded_unicode_format_or_control"
                ),
                glyph_verified=ord(char) in verified,
            )
        )
    return records


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    if not materialized:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)


def report_markdown(
    database: Path,
    records: list[CharacterRecord],
    database_records: list[DatabaseCodepointRecord],
    relations: list[dict[str, str]],
    audit: dict[str, Any],
) -> str:
    blocks = collections.Counter(record.unicode_block for record in records)
    classes = collections.Counter(record.usage_class for record in records)
    planes = collections.Counter(record.unicode_plane for record in records)
    total_occurrences = sum(record.occurrence_count for record in records)
    supplementary = sum(1 for record in records if record.unicode_plane > 0)
    unresolved = [record for record in records if record.unicode_name == "<UNASSIGNED>"]
    compatibility = [record for record in records if record.compatibility_mapping]
    required_text = [record for record in database_records if record.required_in_font]
    excluded_text = [record for record in database_records if not record.required_in_font]
    schema_lines = []
    for table in audit["schema"]:
        schema_lines.append(f"### `{table['name']}` ({table['row_count']:,} rows)")
        schema_lines.append("")
        schema_lines.append("| column | type | primary key | purpose |")
        schema_lines.append("|---|---:|---:|---|")
        for column in table["columns"]:
            purpose = {
                ("entries", "key"): "Dictionary headword / lookup key",
                ("entries", "readings"): "UTF-8 JSON array: pinyin, zhuyin, glosses and examples",
                ("meta", "k"): "Metadata key",
                ("meta", "v"): "Metadata value",
            }.get((table["name"], column["name"]), "Stored database field")
            schema_lines.append(
                f"| `{column['name']}` | `{column['type']}` | {column['primary_key_position']} | {purpose} |"
            )
        schema_lines.append("")

    field_lines = [
        f"- `{field}`: {value:,} string values scanned"
        for field, value in audit["scanned_logical_fields"].items()
    ]
    block_lines = [f"| {name} | {count:,} |" for name, count in sorted(blocks.items())]
    class_lines = [f"| `{name}` | {count:,} |" for name, count in sorted(classes.items())]
    plane_lines = [f"| Plane {plane} | {count:,} |" for plane, count in sorted(planes.items())]

    return f"""# SQLite dictionary character inventory

Generated deterministically by `scripts/inventory.py` from `{database}`.

## Executive summary

| metric | value |
|---|---:|
| Database encoding (`PRAGMA encoding`) | {audit['encoding']} |
| Dictionary entry rows | {audit['metadata'].get('entries', 'unknown')} |
| Han-character occurrences | {total_occurrences:,} |
| Unique Han code points | {len(records):,} |
| All dictionary-text scalar occurrences | {audit['dictionary_text_occurrences']:,} |
| All distinct dictionary-text scalars | {len(database_records):,} |
| Printable dictionary-text scalars required in font | {len(required_text):,} |
| Format/control scalars explicitly excluded | {len(excluded_text):,} |
| Supplementary-plane Han code points | {supplementary:,} |
| JSON parse failures | {audit['json_error_count']:,} |
| Unassigned / unnameable Han code points | {len(unresolved):,} |
| Unicode compatibility mappings | {len(compatibility):,} |
| Dictionary/Unicode variant relations | {len(relations):,} |
| Glyphs marked designed and checked | {sum(record.quality_checked for record in records):,} |

Python's string iterator was used, so each supplementary-plane scalar value is
counted once; no UTF-16 code-unit splitting is possible in this pipeline.

`inventories/han_characters.txt` is the immutable pre-build Han acceptance
input. The CSV and JSON are QA snapshots: they retain the same facts and
provenance while recording the code points present in the
`--verified-codepoints` artifact used for that inventory run. They are not a
live release counter; current Clear Hand coverage is read from
`dist/clear-hand-tc/report.json`.
Aggregate manual visual sign-offs remain separate in
`reviews/manual_review_ledger.json`. Requirements hash only the immutable text
list, so a successful QA status update cannot change its own denominator.

## Database structure

Database file: `{database.name}`  
SQLite library: `{audit['sqlite_version']}`  
Unicode character database: `{audit['python_unicode_version']}`

{chr(10).join(schema_lines)}
## Scanned content fields

`entries.readings` is JSON. The report names parsed logical leaves rather than
claiming nonexistent physical SQL columns.

{chr(10).join(field_lines)}

The `meta` table is metadata and contains no dictionary prose, so it is audited
but deliberately excluded from the character occurrence count.

## Complete dictionary-text scalar audit

Every scalar in parsed dictionary text is recorded independently of the Han
classification. Printable letters, kana, Greek and symbols are required font
inputs. Unicode format/control scalars are retained in the audit but excluded
from glyph requirements because they are shaping controls rather than visible
characters.

| disposition | unique code points |
|---|---:|
| required printable scalars | {len(required_text):,} |
| excluded format/control scalars | {len(excluded_text):,} |

The excluded list is explicit in `reports/database_audit.json`; in this source
database U+FEFF is preserved as a reported data-cleanliness finding rather than
silently counted as a printable glyph.

## Unicode block counts

| Unicode block | unique code points |
|---|---:|
{chr(10).join(block_lines)}

## Unicode plane counts

| plane | unique code points |
|---|---:|
{chr(10).join(plane_lines)}

## Taiwan usage classes

The common/secondary split is an explicit reproducible operational definition:
CP950/Big5 level-1 lead bytes `A4-C6` are “common”, level-2 lead bytes `C9-F9`
are “secondary”, and the remaining Han code points are reported as rare,
compatibility, or extension characters. It is not presented as a replacement
for a particular edition of the Ministry of Education character tables.

| class | unique code points |
|---|---:|
{chr(10).join(class_lines)}

## Invalid, compatibility and variant findings

- JSON parse failures: {audit['json_error_count']:,}
- Unassigned or unnameable Han scalars: {len(unresolved):,}
- Compatibility characters with an NFKC relation: {len(compatibility):,}
- Suspected variant relations from dictionary glosses or Unicode: {len(relations):,}

The complete relations are in `inventories/variant_relations.csv` and JSON.
Compatibility and variant characters remain independent required code points;
normalization is analysis only and never removes a glyph requirement.

## Machine-readable deliverables

- `inventories/han_characters.csv`: one complete row per code point with
  counts, provenance, and the pinned inventory-run QA snapshot.
- `inventories/han_characters.json`: the same snapshot as UTF-8 JSON.
- `inventories/han_characters.txt`: the immutable, strictly ordered pre-build
  Han acceptance input, with one literal Unicode scalar per line.
- `inventories/variant_relations.csv` and `.json`: suspected relationships.
- `inventories/database_codepoints.csv` and `.json`: every scalar found in
  dictionary content, including the inclusion decision and exact provenance.
- `inventories/dictionary_required_codepoints.txt`: the independent printable
  dictionary-text requirement set consumed by the font build and QA.
- `reports/database_audit.json`: schema, metadata, scanned paths and parse log.
- `reports/glyph_progress.csv`: post-build per-code-point construction and
  automatic QA status (generated by `scripts/qa_font.py`).
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=Path("data/dict_lookup.sqlite"))
    parser.add_argument("--inventory-dir", type=Path, default=Path("inventories"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    parser.add_argument(
        "--verified-codepoints",
        type=Path,
        help="Optional QA JSON used to set the final glyph status columns.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    args.inventory_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (
        counts,
        provenance,
        text_counts,
        text_provenance,
        relations,
        audit,
    ) = scan_database(args.database)
    verified = read_verified_codepoints(args.verified_codepoints)
    records = make_records(counts, provenance, verified)
    database_records = make_database_codepoint_records(text_counts, text_provenance, verified)
    serializable = [asdict(record) for record in records]
    database_serializable = [asdict(record) for record in database_records]

    write_csv(args.inventory_dir / "han_characters.csv", serializable)
    (args.inventory_dir / "han_characters.json").write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.inventory_dir / "han_characters.txt").write_text(
        "\n".join(record.character for record in records) + "\n", encoding="utf-8"
    )
    write_csv(args.inventory_dir / "database_codepoints.csv", database_serializable)
    (args.inventory_dir / "database_codepoints.json").write_text(
        json.dumps(database_serializable, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.inventory_dir / "dictionary_required_codepoints.txt").write_text(
        "\n".join(
            record.codepoint for record in database_records if record.required_in_font
        )
        + "\n",
        encoding="utf-8",
    )
    relations = sorted(
        relations,
        key=lambda item: (int(item["variant_codepoint"][2:], 16), item["relation"]),
    )
    write_csv(args.inventory_dir / "variant_relations.csv", relations)
    (args.inventory_dir / "variant_relations.json").write_text(
        json.dumps(relations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.report_dir / "database_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.report_dir / "character_inventory.md").write_text(
        report_markdown(args.database, records, database_records, relations, audit),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "occurrences": sum(counts.values()),
                "unique": len(records),
                "supplementary": sum(record.unicode_plane > 0 for record in records),
                "dictionary_text_unique": len(database_records),
                "dictionary_text_required": sum(
                    record.required_in_font for record in database_records
                ),
                "json_errors": audit["json_error_count"],
                "verified": len(verified & {record.codepoint_decimal for record in records}),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
