# SQLite dictionary character inventory

Generated deterministically by `scripts/inventory.py` from `data/dict_lookup.sqlite`.

## Executive summary

| metric | value |
|---|---:|
| Database encoding (`PRAGMA encoding`) | UTF-8 |
| Dictionary entry rows | 161197 |
| Han-character occurrences | 5,268,037 |
| Unique Han code points | 11,958 |
| All dictionary-text scalar occurrences | 11,499,007 |
| All distinct dictionary-text scalars | 12,307 |
| Printable dictionary-text scalars required in font | 12,306 |
| Format/control scalars explicitly excluded | 1 |
| Supplementary-plane Han code points | 327 |
| JSON parse failures | 0 |
| Unassigned / unnameable Han code points | 0 |
| Unicode compatibility mappings | 58 |
| Dictionary/Unicode variant relations | 1,533 |
| Glyphs marked designed and checked | 4,844 |

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

Database file: `dict_lookup.sqlite`  
SQLite library: `3.50.4`  
Unicode character database: `14.0.0`

### `entries` (161,197 rows)

| column | type | primary key | purpose |
|---|---:|---:|---|
| `key` | `TEXT` | 1 | Dictionary headword / lookup key |
| `readings` | `TEXT` | 0 | UTF-8 JSON array: pinyin, zhuyin, glosses and examples |

### `meta` (6 rows)

| column | type | primary key | purpose |
|---|---:|---:|---|
| `k` | `TEXT` | 1 | Metadata key |
| `v` | `TEXT` | 0 | Metadata value |

## Scanned content fields

`entries.readings` is JSON. The report names parsed logical leaves rather than
claiming nonexistent physical SQL columns.

- `entries.key`: 161,197 string values scanned
- `entries.readings[].examples[]`: 18,530 string values scanned
- `entries.readings[].gloss`: 164,860 string values scanned
- `entries.readings[].pinyin`: 163,383 string values scanned
- `entries.readings[].pinyin_num[]`: 431,532 string values scanned
- `entries.readings[].variant`: 943 string values scanned
- `entries.readings[].zhuyin`: 163,383 string values scanned

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
| required printable scalars | 12,306 |
| excluded format/control scalars | 1 |

The excluded list is explicit in `reports/database_audit.json`; in this source
database U+FEFF is preserved as a reported data-cleanliness finding rather than
silently counted as a printable glyph.

## Unicode block counts

| Unicode block | unique code points |
|---|---:|
| CJK Compatibility Ideographs | 1 |
| CJK Compatibility Ideographs Supplement | 57 |
| CJK Symbols and Punctuation (Ideographic Zero) | 1 |
| CJK Unified Ideographs | 11,413 |
| CJK Unified Ideographs Extension A | 216 |
| CJK Unified Ideographs Extension B | 152 |
| CJK Unified Ideographs Extension C | 3 |
| CJK Unified Ideographs Extension E | 3 |
| CJK Unified Ideographs Extension F | 1 |
| Supplementary Private Use Area-A (dictionary gaiji) | 111 |

## Unicode plane counts

| plane | unique code points |
|---|---:|
| Plane 0 | 11,631 |
| Plane 2 | 216 |
| Plane 15 | 111 |

## Taiwan usage classes

The common/secondary split is an explicit reproducible operational definition:
CP950/Big5 level-1 lead bytes `A4-C6` are “common”, level-2 lead bytes `C9-F9`
are “secondary”, and the remaining Han code points are reported as rare,
compatibility, or extension characters. It is not presented as a replacement
for a particular edition of the Ministry of Education character tables.

| class | unique code points |
|---|---:|
| `common_big5_level_1` | 5,386 |
| `compatibility_ideograph` | 58 |
| `dictionary_private_use_gaiji` | 111 |
| `rare_or_unclassified` | 1,409 |
| `secondary_big5_level_2` | 4,619 |
| `unicode_extension` | 375 |

## Invalid, compatibility and variant findings

- JSON parse failures: 0
- Unassigned or unnameable Han scalars: 0
- Compatibility characters with an NFKC relation: 58
- Suspected variant relations from dictionary glosses or Unicode: 1,533

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
