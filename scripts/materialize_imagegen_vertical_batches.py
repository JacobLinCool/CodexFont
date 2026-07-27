#!/usr/bin/env python3
"""Freeze, reference-render, prompt, and register 93 vertical alternates.

The encoded base scalars come from the approved non-Han repertoire.  The
alternate outlines themselves are new imagegen assets; neutral local fonts and
Unicode Vertical_Orientation data are used only to make identity copybooks.
No reference outline is imported into the release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import unicodedata
from typing import Any, Mapping, Sequence

import freetype
import uharfbuzz as hb
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN = ROOT / "sources/imagegen"
NONHAN_REPERTOIRE = IMAGEGEN / "repertoires/nonhan-3060.json"
VERTICAL_REPERTOIRE = IMAGEGEN / "repertoires/vertical-93.json"
VERTICAL_DATA = ROOT / "data/unicode/VerticalOrientation-17.0.0.txt"
VERTICAL_DATA_SHA256 = (
    "dcef09c3fb24d356b042569c328ec341efc5b53447700d799f2fb4834c3cd3cd"
)
VERTICAL_DATA_URL = (
    "https://www.unicode.org/Public/17.0.0/ucd/"
    "VerticalOrientation.txt"
)
REPERTOIRE_ID = (
    "clear-hand-tc-vertical-alternates-93-uax50-17.0-v1"
)

STYLE_REFERENCE = IMAGEGEN / "raster/common-0001.png"
REFERENCE_FONT = (
    Path.home() / "Library/Fonts/NotoSansJP-VariableFont_wght.ttf"
)
MATH_REFERENCE_FONT = Path(
    "/System/Library/Fonts/Supplemental/STIXTwoMath.otf"
)

ROWS = 4
COLUMNS = 4
CAPACITY = ROWS * COLUMNS
CELL = 400
COPYBOOK_SIZE = CELL * 4
REFERENCE_PX = 220

TAILORING: Mapping[int, str] = {
    0x2013: "vertical en dash: a short upright vertical stroke",
    0x2014: "vertical em dash: a long upright vertical stroke",
    0x2025: "two-dot leader: two vertically stacked dots",
    0x2026: "ellipsis: three vertically stacked dots",
    0x2032: "prime: vertical-writing prime orientation",
    0x2035: "reversed prime: vertical-writing reversed-prime orientation",
    0x2219: "bullet operator: centered round dot for vertical mathematics",
    0x2574: "box-drawing left half-line transformed to its vertical counterpart",
    0xFE4F: "wavy low line transformed into a vertical wavy rule",
    0xFE55: "small colon optically centered for vertical CJK text",
}

IDENTITY_NOTES: Mapping[int, str] = {
    0x2574: (
        "draw one straight vertical half-line only; no horizontal segment, "
        "corner, hook, or L shape"
    ),
    0x300C: (
        "draw a `┐` silhouette with one top horizontal and one right downstroke; "
        "do not add a left downstroke or make a three-sided cap"
    ),
    0x300D: (
        "draw a `└` silhouette with one left upstroke and one bottom horizontal; "
        "do not add a right upstroke or make a three-sided cup"
    ),
    0x300E: (
        "draw two nested `┐` strokes only; do not add any left downstroke"
    ),
    0x300F: (
        "draw two nested `└` strokes only; do not add any right upstroke"
    ),
    0x3014: (
        "draw a top trapezoid bracket opening downward, with one horizontal "
        "top and two short diagonal sides; never draw a sideways C shape"
    ),
    0x3015: (
        "draw a bottom trapezoid bracket opening upward, with one horizontal "
        "bottom and two short diagonal sides; never draw a backwards C shape"
    ),
    0x3018: (
        "draw the outlined top tortoise-shell form opening downward, not a "
        "sideways left bracket"
    ),
    0x3019: (
        "draw the outlined bottom tortoise-shell form opening upward, not a "
        "sideways right bracket"
    ),
    0x301D: (
        "draw exactly two short quote strokes total; do not duplicate them "
        "into two pairs"
    ),
    0x301E: (
        "draw exactly two short quote strokes total; do not duplicate them "
        "into two pairs"
    ),
    0x301F: (
        "draw exactly two short quote strokes total; do not add a third stroke"
    ),
    0x30FC: (
        "draw one straight vertical line for the vertical prolonged-sound mark"
    ),
    0x3127: (
        "keep Bopomofo I as one straight horizontal line; do not rotate it"
    ),
    0xFE4F: (
        "draw one slender vertical wavy rule, never a horizontal underline"
    ),
    0xFE55: (
        "draw exactly two small round dots stacked vertically"
    ),
    0xFF08: (
        "draw a top parenthesis arc opening downward, never a sideways `(`"
    ),
    0xFF09: (
        "draw a bottom parenthesis arc opening upward, never a sideways `)`"
    ),
    0xFF1A: (
        "draw exactly two round dots aligned horizontally in the vertical form"
    ),
    0xFF1B: (
        "draw the comma-like mark on the left and the round dot on the right, "
        "aligned horizontally; never stack them vertically"
    ),
    0xFF3B: (
        "draw a three-sided top square bracket opening downward"
    ),
    0xFF3D: (
        "draw a three-sided bottom square bracket opening upward"
    ),
    0xFF3F: (
        "draw one straight vertical line, not a horizontal low line"
    ),
    0xFF5B: (
        "draw the top horizontal curly-brace form shown in Image 2"
    ),
    0xFF5C: (
        "draw one straight horizontal line, not a vertical line"
    ),
    0xFF5D: (
        "draw the bottom horizontal curly-brace form shown in Image 2"
    ),
    0xFF5E: (
        "draw one vertical S-shaped tilde, not a horizontal wave"
    ),
    0xFF5F: (
        "draw the outlined top white-parenthesis form opening downward"
    ),
    0xFF60: (
        "draw the outlined bottom white-parenthesis form opening upward"
    ),
    0xFFE3: (
        "draw one straight vertical macron line"
    ),
}


class VerticalMaterializationError(RuntimeError):
    """Vertical repertoire/source materialization failed closed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _vertical_properties(
    codepoints: set[int],
) -> Mapping[int, str]:
    if not VERTICAL_DATA.is_file() or _sha256(VERTICAL_DATA) != VERTICAL_DATA_SHA256:
        raise VerticalMaterializationError(
            "Unicode VerticalOrientation 17.0.0 data is missing or changed"
        )
    result: dict[int, str] = {}
    for raw in VERTICAL_DATA.read_text(encoding="utf-8").splitlines():
        content = raw.split("#", 1)[0].strip()
        if not content:
            continue
        field, value = (part.strip() for part in content.split(";"))
        if ".." in field:
            first_text, last_text = field.split("..")
            first, last = int(first_text, 16), int(last_text, 16)
        else:
            first = last = int(field, 16)
        for codepoint in range(first, last + 1):
            if codepoint in codepoints:
                result[codepoint] = value
    return result


def _load_nonhan() -> tuple[dict[str, Any], Mapping[int, Mapping[str, Any]]]:
    if not NONHAN_REPERTOIRE.is_file():
        raise VerticalMaterializationError("non-Han repertoire is missing")
    payload = json.loads(NONHAN_REPERTOIRE.read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("repertoire_id")
        != "clear-hand-tc-nonhan-3060-v1"
        or not isinstance(payload.get("glyphs"), list)
    ):
        raise VerticalMaterializationError("non-Han repertoire identity changed")
    rows = {
        int(record["codepoint"][2:], 16): record
        for record in payload["glyphs"]
    }
    return payload, rows


def _alternate_records() -> list[dict[str, Any]]:
    nonhan, by_codepoint = _load_nonhan()
    properties = _vertical_properties(set(by_codepoint))
    official = {
        codepoint
        for codepoint, value in properties.items()
        if value in {"Tu", "Tr"}
    }
    selected = sorted(official | set(TAILORING))
    if len(official) != 83 or len(selected) != 93:
        raise VerticalMaterializationError(
            f"vertical set changed: official={len(official)}, total={len(selected)}"
        )
    records: list[dict[str, Any]] = []
    for rank, codepoint in enumerate(selected, start=1):
        base = by_codepoint.get(codepoint)
        if base is None or base.get("outline_required") is not True:
            raise VerticalMaterializationError(
                f"U+{codepoint:04X}: vertical base is not a visible non-Han glyph"
            )
        records.append(
            {
                "rank": rank,
                "base_character": chr(codepoint),
                "base_codepoint": f"U+{codepoint:04X}",
                "unicode_name": unicodedata.name(chr(codepoint), "<UNNAMED>"),
                "vertical_orientation": (
                    properties.get(codepoint, "R")
                    if codepoint in official
                    else "Tailored"
                ),
                "tailoring": TAILORING.get(codepoint),
                "glyph_name": f"uni{codepoint:04X}.vert",
                "base_profile_id": base["profile_id"],
                "base_metrics": base["metrics"],
            }
        )
    return records


def build_repertoire() -> Path:
    records = _alternate_records()
    batches = []
    for start in range(0, len(records), CAPACITY):
        number = start // CAPACITY + 1
        items = records[start : start + CAPACITY]
        batches.append(
            {
                "batch_id": f"vertical-{number:04d}",
                "start_rank": items[0]["rank"],
                "end_rank": items[-1]["rank"],
                "base_codepoints": [
                    item["base_codepoint"] for item in items
                ],
                "empty_grid_cells": CAPACITY - len(items),
            }
        )
    if len(batches) != 6:
        raise VerticalMaterializationError("vertical batch count is not six")
    sequence = "".join(item["base_character"] for item in records)
    payload = {
        "schema_version": 1,
        "repertoire_id": REPERTOIRE_ID,
        "source": {
            "unicode_version": "17.0.0",
            "vertical_orientation_url": VERTICAL_DATA_URL,
            "vertical_orientation_sha256": VERTICAL_DATA_SHA256,
            "nonhan_repertoire": (
                "sources/imagegen/repertoires/nonhan-3060.json"
            ),
            "nonhan_repertoire_sha256": _sha256(NONHAN_REPERTOIRE),
            "policy": (
                "all encoded non-Han Tu/Tr scalars plus ten reviewed "
                "Taiwan/CJK project-tailored forms"
            ),
        },
        "total": 93,
        "sequence_sha256": hashlib.sha256(
            sequence.encode("utf-8")
        ).hexdigest(),
        "alternates": records,
        "batches": batches,
    }
    _write_json(VERTICAL_REPERTOIRE, payload)
    return VERTICAL_REPERTOIRE


class _ReferenceRenderer:
    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise VerticalMaterializationError(
                f"identity reference font is missing: {path}"
            )
        self.path = path.resolve()
        self.data = self.path.read_bytes()
        self.hb_face = hb.Face(self.data)
        self.hb_font = hb.Font(self.hb_face)
        self.hb_font.scale = (self.hb_face.upem, self.hb_face.upem)
        if "VariableFont" in self.path.name:
            self.hb_font.set_variations({"wght": 400})
        self.ft_face = freetype.Face(str(self.path))
        self.ft_face.set_pixel_sizes(0, REFERENCE_PX)

    def glyph_id(
        self,
        character: str,
        *,
        vertical: bool,
    ) -> int:
        buffer = hb.Buffer()
        buffer.add_str(character)
        buffer.direction = "ttb" if vertical else "ltr"
        buffer.guess_segment_properties()
        hb.shape(
            self.hb_font,
            buffer,
            {"vert": 1, "vrt2": 1} if vertical else {},
        )
        if len(buffer.glyph_infos) != 1:
            raise VerticalMaterializationError(
                f"reference shaping did not return one glyph for "
                f"U+{ord(character):04X}"
            )
        return int(buffer.glyph_infos[0].codepoint)

    def bitmap(self, glyph_id: int) -> Image.Image:
        flags = (
            freetype.FT_LOAD_RENDER
            | freetype.FT_LOAD_NO_HINTING
            | freetype.FT_LOAD_TARGET_NORMAL
        )
        self.ft_face.load_glyph(glyph_id, flags)
        bitmap = self.ft_face.glyph.bitmap
        if bitmap.width <= 0 or bitmap.rows <= 0:
            raise VerticalMaterializationError(
                f"reference glyph ID {glyph_id} rendered empty in {self.path}"
            )
        raw = bytes(bitmap.buffer)
        if bitmap.pitch < bitmap.width:
            raise VerticalMaterializationError("unsupported reference bitmap pitch")
        image = Image.frombytes(
            "L",
            (bitmap.pitch, bitmap.rows),
            raw,
        ).crop((0, 0, bitmap.width, bitmap.rows))
        # FreeType's grayscale bitmap stores coverage (0 = background,
        # 255 = ink).  Copybooks are white-paper references, so convert the
        # coverage mask to black ink before compositing it onto the canvas.
        return ImageOps.invert(image)


def _identity_bitmap(
    record: Mapping[str, Any],
    primary: _ReferenceRenderer,
    math: _ReferenceRenderer,
) -> tuple[Image.Image, dict[str, Any]]:
    codepoint = int(str(record["base_codepoint"])[2:], 16)
    renderer = math if codepoint == 0x2219 else primary
    base_gid = renderer.glyph_id(chr(codepoint), vertical=False)
    vertical_gid = renderer.glyph_id(chr(codepoint), vertical=True)
    if base_gid == 0:
        raise VerticalMaterializationError(
            f"reference font has no U+{codepoint:04X}"
        )
    use_gid = vertical_gid if vertical_gid != 0 else base_gid
    image = renderer.bitmap(use_gid)
    transformed_by_reference = vertical_gid not in {0, base_gid}
    rotate = False
    orientation = record["vertical_orientation"]
    if not transformed_by_reference:
        if orientation == "Tr" or codepoint in {
            0x2013,
            0x2014,
            0x2025,
            0x2026,
            0x2032,
            0x2035,
            0x2574,
            0xFE4F,
        }:
            rotate = True
    if rotate:
        image = image.transpose(Image.Transpose.ROTATE_270)
    return image, {
        "role": "identity-reference-only-no-outline-import",
        "font_path": str(renderer.path),
        "font_sha256": _sha256(renderer.path),
        "font_index": 0,
        "postscript_name": renderer.ft_face.postscript_name.decode(
            "ascii", errors="replace"
        ),
        "base_glyph_id": base_gid,
        "vertical_glyph_id": vertical_gid,
        "used_glyph_id": use_gid,
        "reference_vert_substitution": transformed_by_reference,
        "reference_rotation_for_identity_only": rotate,
    }


def _copybook(
    records: Sequence[Mapping[str, Any]],
    *,
    output: Path,
) -> list[dict[str, Any]]:
    primary = _ReferenceRenderer(REFERENCE_FONT)
    math = _ReferenceRenderer(MATH_REFERENCE_FONT)
    canvas = Image.new("L", (COPYBOOK_SIZE, COPYBOOK_SIZE), 255)
    pixels = canvas.load()
    for coordinate in range(1, 4):
        value = coordinate * CELL
        for offset in (-1, 0, 1):
            for axis in range(COPYBOOK_SIZE):
                pixels[value + offset, axis] = 220
                pixels[axis, value + offset] = 220
    references: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        image, evidence = _identity_bitmap(record, primary, math)
        image = ImageOps.autocontrast(image)
        row, column = divmod(index, 4)
        scale = min(
            (CELL - 120) / image.width,
            (CELL - 120) / image.height,
            1.0,
        )
        if scale < 1.0:
            image = image.resize(
                (
                    max(1, round(image.width * scale)),
                    max(1, round(image.height * scale)),
                ),
                Image.Resampling.LANCZOS,
            )
        left = column * CELL + (CELL - image.width) // 2
        top = row * CELL + (CELL - image.height) // 2
        canvas.paste(image, (left, top))
        references.append(evidence)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=False)
    return references


def _exact_prompt(
    *,
    batch_id: str,
    records: Sequence[Mapping[str, Any]],
    copybook: Path,
) -> str:
    lines = [
        "Use case: font-source raster sheet",
        "Asset type: high-resolution 4×4 raster master sheet for original "
        "vertical-writing alternates in the Clear Hand TC family",
        "",
        "Input images:",
        "1. Image 1 is STYLE ONLY. Match its fine black gel-pen weight, rounded "
        "terminals, controlled handwritten rhythm, white background, and faint "
        "4×4 grid. Do not copy its Han characters.",
        "2. Image 2 is IDENTITY REFERENCE ONLY. Each cell shows the intended "
        "vertical-writing form using neutral reference fonts or a reference-only "
        "orientation transform. Never trace or import its printed outlines.",
        "",
        f"Draw exactly {len(records)} independently authored vertical alternate "
        "glyphs in strict row-major order. These are new unencoded `.vert` "
        "glyphs, not mechanically rotated copies of the horizontal Clear Hand "
        "TC glyphs. Redraw each form naturally for vertical typography.",
        "",
        "Critical orientation rule: every LEFT/RIGHT bracket or delimiter must "
        "use the TOP/BOTTOM vertical form visibly shown in Image 2. The opening "
        "left form becomes a top form opening downward; the closing right form "
        "becomes a bottom form opening upward. For example, `〈` must become "
        "`∧` and `〉` must become `∨`. Never retain a sideways `<`, `>`, `(`, "
        "`)`, `「`, `」`, or other left/right bracket silhouette in the output.",
        "",
    ]
    if batch_id == "vertical-0006":
        lines.extend(
            [
                "Critical Cell 01–02 rule: these two vertical alternates are "
                "side-by-side punctuation arrangements on one horizontal "
                "baseline. Cell 01 must be `•  •` from left to right. Cell 02 "
                "must be a comma-like mark on the left and one dot on the right. "
                "Never arrange either cell as a top/bottom vertical stack.",
                "",
            ]
        )
    lines.append("Exact occupied cells:")
    for index, record in enumerate(records, start=1):
        note = (
            record["tailoring"]
            or (
                "Unicode typographic vertical transform with upright fallback"
                if record["vertical_orientation"] == "Tu"
                else "Unicode typographic vertical transform with rotated fallback"
            )
        )
        lines.append(
            f"- Cell {index:02d}: `{record['base_codepoint']}` "
            f"{record['unicode_name']} — base `{record['base_character']}` — "
            f"alternate `{record['glyph_name']}` — "
            f"VO `{record['vertical_orientation']}` — {note}"
            + (
                f"; {IDENTITY_NOTES[ord(record['base_character'])]}."
                if ord(record["base_character"]) in IDENTITY_NOTES
                else "."
            )
        )
    empty = CAPACITY - len(records)
    lines.extend(
        [
            "",
            (
                "Unused cells: none."
                if empty == 0
                else f"Unused cells: the final {empty} trailing cell(s); leave "
                "them completely blank."
            ),
            "",
            "Composition: square image; four equal rows and columns; generous "
            "outer margin; faint thin light-gray separators; one centered black "
            "target in each occupied cell. Pure white background, no texture, "
            "shadow, labels, captions, Unicode text, logos, or watermarks.",
            "",
            "Preserve exact identity, direction, topology, dot/line count, paired "
            "bracket distinction, small-kana distinction, and punctuation "
            "position. Avoid typeset stiffness, brush blobs, sharp miter spikes, "
            "thorn protrusions, clipping, duplicate/missing/reordered glyphs, "
            "connected cells, or any visible mark in unused cells.",
        ]
    )
    return "\n".join(lines)


def materialize() -> tuple[Path, ...]:
    repertoire_path = build_repertoire()
    repertoire = json.loads(repertoire_path.read_text(encoding="utf-8"))
    repertoire_hash = _sha256(repertoire_path)
    style_hash = _sha256(STYLE_REFERENCE)
    records = repertoire["alternates"]
    drafts: list[Path] = []
    for batch in repertoire["batches"]:
        batch_id = batch["batch_id"]
        items = records[
            batch["start_rank"] - 1 : batch["end_rank"]
        ]
        copybook = IMAGEGEN / "copybooks" / f"{batch_id}.png"
        references = _copybook(items, output=copybook)
        copybook_hash = _sha256(copybook)
        prompt_text = _exact_prompt(
            batch_id=batch_id,
            records=items,
            copybook=copybook,
        )
        prompt = IMAGEGEN / "prompts" / f"{batch_id}.md"
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text(
            f"# Image-generated vertical sheet {batch_id}\n\n"
            f"- Repertoire: `{repertoire_path.relative_to(ROOT)}` "
            f"(`{repertoire_hash}`)\n"
            f"- Style reference: `{STYLE_REFERENCE.relative_to(ROOT)}` "
            f"(`{style_hash}`)\n"
            f"- Identity copybook: `{copybook.relative_to(ROOT)}` "
            f"(`{copybook_hash}`)\n"
            "- State: awaiting generation\n\n"
            "## Exact tool prompt\n\n```text\n"
            f"{prompt_text}\n```\n",
            encoding="utf-8",
        )
        embedded = []
        for item, reference in zip(items, references, strict=True):
            embedded.append({**item, "copybook_reference": reference})
        draft = IMAGEGEN / "batches" / f"{batch_id}.draft.json"
        _write_json(
            draft,
            {
                "schema_version": 1,
                "source_type": "imagegen-vertical-alternate",
                "batch_id": f"imagegen-{batch_id}",
                "state": "awaiting-generation",
                "generator": "built-in-image_gen",
                "generator_call": "<PENDING: filled only by register>",
                "repertoire": {
                    "path": "../repertoires/vertical-93.json",
                    "sha256": repertoire_hash,
                    "repertoire_id": REPERTOIRE_ID,
                    "batch_id": batch_id,
                },
                "raster": f"../raster/{batch_id}.png",
                "raster_sha256": "<PENDING: filled only by register>",
                "prompt": f"../prompts/{batch_id}.md",
                "copybook": {
                    "path": f"../copybooks/{batch_id}.png",
                    "sha256": copybook_hash,
                    "role": "identity-reference-only-no-outline-import",
                },
                "style_reference": {
                    "path": "../raster/common-0001.png",
                    "sha256": style_hash,
                    "role": "style-only",
                },
                "grid": {
                    "rows": 4,
                    "columns": 4,
                    "alternates": embedded,
                    "empty_grid_cells": batch["empty_grid_cells"],
                },
                "review": {
                    "identity": "pending",
                    "raster_quality": "pending",
                    "vector_quality": "pending",
                },
            },
        )
        drafts.append(draft)
    return tuple(drafts)


def register(batch_id: str, generator_call: str) -> Path:
    if not batch_id.startswith("vertical-") or len(batch_id) != 13:
        raise VerticalMaterializationError("invalid vertical batch ID")
    draft = IMAGEGEN / "batches" / f"{batch_id}.draft.json"
    source = IMAGEGEN / "batches" / f"{batch_id}.source.json"
    raster = IMAGEGEN / "raster" / f"{batch_id}.png"
    if source.exists():
        raise VerticalMaterializationError(
            f"refusing to overwrite canonical source: {source}"
        )
    if (
        not generator_call
        or generator_call.startswith("<")
        or generator_call != generator_call.strip()
    ):
        raise VerticalMaterializationError(
            "generator_call must be exact non-placeholder provenance"
        )
    if not draft.is_file() or not raster.is_file():
        raise VerticalMaterializationError(
            f"draft or generated raster missing for {batch_id}"
        )
    with Image.open(raster) as image:
        image.load()
        if (
            image.format != "PNG"
            or image.size[0] < 1024
            or image.size[1] < 1024
        ):
            raise VerticalMaterializationError(
                f"{raster}: raster must be a high-resolution PNG"
            )
    payload = json.loads(draft.read_text(encoding="utf-8"))
    payload["state"] = "generated-unreviewed"
    payload["generator_call"] = generator_call
    payload["raster_sha256"] = _sha256(raster)
    _write_json(source, payload)
    return source


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("materialize")
    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("batch_id")
    register_parser.add_argument("--generator-call", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "materialize":
        for path in materialize():
            print(path)
    else:
        print(register(args.batch_id, args.generator_call))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
