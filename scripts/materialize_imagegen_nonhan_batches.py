#!/usr/bin/env python3
"""Materialize and register the imagegen-first non-Han source batches.

``materialize`` creates three immutable-input artifacts for every visible
non-Han repertoire batch:

* a neutral-font 4×4 identity copybook;
* the exact per-batch image-generation prompt; and
* a schema-v2 draft descriptor with deliberately empty raster provenance.

The copybook is never a glyph source.  Its per-cell fonts are accepted only
after an exact cmap lookup, a non-empty outline check, a non-.notdef check,
and a non-empty Pillow raster check.  The selected local font path, file
SHA-256, face index, and glyph name are recorded in the draft descriptor.

``register`` is a separate admission step.  It hash-pins an already generated
PNG and its generator call in a new canonical ``.source.json`` descriptor.
Registration refuses to overwrite any existing canonical descriptor and
does not claim visual approval.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from scripts.identity_reference_catalog import (
    DEFAULT_REFERENCE_FONTS,
    IdentityReferenceCatalogError as MaterializationError,
    ReferenceFace,
    load_reference_faces,
    pillow_font as _pillow_font,
    select_references,
)


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
REPERTOIRE = IMAGEGEN_ROOT / "repertoires/nonhan-3060.json"
BATCH_ROOT = IMAGEGEN_ROOT / "batches"
PROMPT_ROOT = IMAGEGEN_ROOT / "prompts"
COPYBOOK_ROOT = IMAGEGEN_ROOT / "copybooks"
RASTER_ROOT = IMAGEGEN_ROOT / "raster"
STYLE_REFERENCE = RASTER_ROOT / "common-0001.png"

ROWS = 4
COLUMNS = 4
GRID_CAPACITY = ROWS * COLUMNS
VISIBLE_GLYPH_COUNT = 3043
SEMANTIC_EMPTY_COUNT = 17
BATCH_COUNT = 205
COPYBOOK_SIDE = 1600
COPYBOOK_CELL = COPYBOOK_SIDE // COLUMNS
COPYBOOK_GRID_GRAY = 218
COPYBOOK_GLYPH_BLACK = 0
COPYBOOK_GLYPH_BOX = 284
COPYBOOK_BASE_FONT_SIZE = 300
COPYBOOK_MAX_FONT_SIZE = 380

BATCH_ID_PATTERN = re.compile(r"nonhan-(?P<number>[0-9]{4})")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

PROFILE_INSTRUCTIONS: Mapping[str, tuple[str, ...]] = {
    "proportional": (
        "Keep natural proportional side bearings and optical width; do not "
        "force the glyph into a fullwidth square.",
    ),
    "tabular-digit": (
        "Keep every digit on one shared tabular visual width and baseline while "
        "preserving the exact requested figure.",
    ),
    "nonspacing-mark": (
        "Draw only the requested combining-mark ink, enlarged enough to identify "
        "in its cell; do not add a base, dotted circle, or carrier glyph.",
        "The final font metric is zero advance; the raster cell is an identity "
        "capture canvas, not evidence of final spacing.",
    ),
    "fullwidth": (
        "Use the exact fullwidth identity and balanced full-em optical scale; do "
        "not substitute an ASCII or halfwidth compatibility character.",
    ),
    "halfwidth": (
        "Use the compact halfwidth identity; do not substitute its fullwidth "
        "counterpart or stretch it to fill the cell.",
    ),
    "cjk-wide": (
        "Compose the glyph for a full CJK em with the requested encoded "
        "orientation and punctuation position.",
    ),
    "box-drawing": (
        "Preserve every endpoint, junction, single/double line, and weight "
        "distinction exactly; connection topology outranks decorative variation.",
        "Keep the authored topology centered and clearly separated from the "
        "gray grid. The vector stage will normalize each Unicode-required arm "
        "to its exact em boundary without replacing the generated outline.",
    ),
    "block-element": (
        "Preserve the exact fill fraction, edge, quadrant, and light/dark state; "
        "do not round away functional coverage boundaries.",
        "Keep the authored fill centered and clearly separated from the gray "
        "grid while preserving exact relative fractions. The vector stage will "
        "normalize its Unicode-defined bounds to exact em-boundary coordinates.",
    ),
}

BATCH_INSTRUCTIONS: Mapping[str, str] = {
    "nonhan-0202": """Box-drawing topology requirements:
- Cell 01's arc encodes UP and RIGHT. Cells 02–04 preserve the exact slash,
  backslash, or crossed-pair topology.
- Cells 05–12 are eight isolated single-arm marks, never opposing full spans.
  Cells 05/09 are horizontal LEFT arms; Cells 06/10 are vertical UP arms;
  Cells 07/11 are horizontal RIGHT arms; Cells 08/12 are vertical DOWN arms.
  Preserve the light/heavy distinction and the authored rounded terminal
  morphology. The Unicode name supplies the functional arm direction.
- A source mark may be optically centered, and antialiased ink may cross the
  geometric cell midpoint. Its absolute raster bounding box is segmentation
  and layout evidence, not Unicode identity and not a release metric. Do not
  reject or relabel a single arm solely from its source-side bbox.
- Cells 13/15 encode LEFT-to-RIGHT spans with their requested light/heavy
  halves. Cells 14/16 encode UP-to-DOWN spans with their requested light/heavy
  halves. The weight changes only at the exact center junction, with zero
  white seam; every glyph must remain exactly one connected component.
- All Cells 01–16 must each contain exactly one black connected component.
  In particular, the light and heavy halves in Cells 13–16 must overlap
  cleanly at the center rather than merely touch across an antialiased gap.
- The raster supplies original topology, weights, and junction quality.
  Standard v3 vector metric normalization uses `_edge_target_bounds` to map
  every Unicode-required arm to its exact named half-em and em boundary."""
}


@dataclass(frozen=True)
class RepertoireGlyph:
    """One exact visible scalar and its untouched repertoire record."""

    character: str
    codepoint: int
    codepoint_label: str
    unicode_name: str
    profile_id: str
    metrics: Mapping[str, Any]
    record: Mapping[str, Any]


@dataclass(frozen=True)
class RepertoireBatch:
    """One frozen 4×4 batch and its explicit prompt profile."""

    batch_id: str
    design_group: str
    profile_ids: tuple[str, ...]
    profile_instructions: tuple[str, ...]
    glyphs: tuple[RepertoireGlyph, ...]
    empty_grid_cells: int
    record: Mapping[str, Any]

def sha256(path: Path) -> str:
    """Return the lowercase SHA-256 of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterializationError(f"{path}: cannot read JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise MaterializationError(f"{path}: expected a JSON object")
    return value


def _one_unicode_scalar(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or len(value) != 1:
        raise MaterializationError(f"{where}: expected exactly one Unicode scalar")
    codepoint = ord(value)
    if 0xD800 <= codepoint <= 0xDFFF:
        raise MaterializationError(f"{where}: surrogate code points are forbidden")
    return value


def _codepoint(value: Any, *, where: str) -> tuple[int, str]:
    if not isinstance(value, str) or re.fullmatch(r"U\+[0-9A-F]{4,6}", value) is None:
        raise MaterializationError(
            f"{where}: codepoint must be uppercase U+XXXX notation"
        )
    return int(value[2:], 16), value


def load_repertoire(path: Path = REPERTOIRE) -> tuple[dict[str, Any], tuple[RepertoireBatch, ...]]:
    """Validate all 206 batches and return only the 205 raster batches."""

    payload = _read_json(path)
    repertoire_id = payload.get("repertoire_id")
    if not isinstance(repertoire_id, str) or not repertoire_id.strip():
        raise MaterializationError(f"{path}: repertoire_id is missing")
    raw_glyph_records = payload.get("glyphs")
    if not isinstance(raw_glyph_records, list) or len(raw_glyph_records) != (
        VISIBLE_GLYPH_COUNT + SEMANTIC_EMPTY_COUNT
    ):
        raise MaterializationError(f"{path}: expected exactly 3,060 glyph records")
    known_profiles = payload.get("profile_ids")
    if (
        not isinstance(known_profiles, list)
        or set(known_profiles) != set(PROFILE_INSTRUCTIONS)
        or len(known_profiles) != len(PROFILE_INSTRUCTIONS)
    ):
        raise MaterializationError(
            f"{path}: profile_ids must be the eight audited metric profiles"
        )

    glyph_index: dict[str, RepertoireGlyph] = {}
    for glyph_index_number, raw_glyph in enumerate(raw_glyph_records):
        where = f"{path}: glyphs[{glyph_index_number}]"
        if not isinstance(raw_glyph, dict):
            raise MaterializationError(f"{where}: expected an object")
        character = _one_unicode_scalar(
            raw_glyph.get("character"), where=f"{where}.character"
        )
        codepoint, codepoint_label = _codepoint(
            raw_glyph.get("codepoint"), where=f"{where}.codepoint"
        )
        if ord(character) != codepoint:
            raise MaterializationError(f"{where}: character/codepoint mismatch")
        if codepoint_label in glyph_index:
            raise MaterializationError(f"{where}: duplicate {codepoint_label}")
        unicode_name = raw_glyph.get("name")
        if not isinstance(unicode_name, str) or not unicode_name.strip():
            raise MaterializationError(f"{where}.name: expected a non-empty string")
        profile_id = raw_glyph.get("profile_id")
        if profile_id not in PROFILE_INSTRUCTIONS:
            raise MaterializationError(f"{where}: unknown profile_id {profile_id!r}")
        metrics = raw_glyph.get("metrics")
        if not isinstance(metrics, dict):
            raise MaterializationError(f"{where}.metrics: expected an object")
        glyph_index[codepoint_label] = RepertoireGlyph(
            character=character,
            codepoint=codepoint,
            codepoint_label=codepoint_label,
            unicode_name=unicode_name,
            profile_id=str(profile_id),
            metrics=copy.deepcopy(metrics),
            record=copy.deepcopy(raw_glyph),
        )

    raw_batches = payload.get("batches")
    if not isinstance(raw_batches, list) or len(raw_batches) != BATCH_COUNT + 1:
        raise MaterializationError(
            f"{path}: expected 205 raster batches plus one semantic-empty batch"
        )

    batches: list[RepertoireBatch] = []
    seen_labels: set[str] = set()
    for index, raw_batch in enumerate(raw_batches[:BATCH_COUNT], start=1):
        where = f"{path}: batches[{index - 1}]"
        if not isinstance(raw_batch, dict):
            raise MaterializationError(f"{where}: expected an object")
        expected_batch_id = f"nonhan-{index:04d}"
        if raw_batch.get("batch_id") != expected_batch_id:
            raise MaterializationError(
                f"{where}: expected batch_id {expected_batch_id!r}"
            )
        if raw_batch.get("batch_kind") != "raster-outline":
            raise MaterializationError(f"{where}: batch_kind must be raster-outline")
        design_group = raw_batch.get("design_group")
        if not isinstance(design_group, str) or not design_group:
            raise MaterializationError(f"{where}: design_group is missing")
        raw_codepoints = raw_batch.get("glyph_codepoints")
        if not isinstance(raw_codepoints, list) or not 1 <= len(raw_codepoints) <= GRID_CAPACITY:
            raise MaterializationError(
                f"{where}.glyph_codepoints: expected 1..16 entries"
            )
        if not all(isinstance(value, str) for value in raw_codepoints):
            raise MaterializationError(
                f"{where}.glyph_codepoints: expected strings"
            )
        empty_grid_cells = GRID_CAPACITY - len(raw_codepoints)
        recorded_empty = raw_batch.get("empty_grid_cells")
        if recorded_empty != empty_grid_cells:
            raise MaterializationError(
                f"{where}: empty_grid_cells does not match glyph count"
            )

        glyphs: list[RepertoireGlyph] = []
        for glyph_position, codepoint_label in enumerate(raw_codepoints):
            glyph_where = f"{where}.glyph_codepoints[{glyph_position}]"
            if codepoint_label not in glyph_index:
                raise MaterializationError(
                    f"{glyph_where}: unknown repertoire glyph {codepoint_label!r}"
                )
            glyph = glyph_index[codepoint_label]
            if glyph.record.get("outline_required") is not True:
                raise MaterializationError(
                    f"{glyph_where}: semantic-empty scalar entered raster batch"
                )
            if codepoint_label in seen_labels:
                raise MaterializationError(
                    f"{glyph_where}: duplicate visible {codepoint_label}"
                )
            seen_labels.add(codepoint_label)
            glyphs.append(glyph)
        profile_ids = tuple(dict.fromkeys(glyph.profile_id for glyph in glyphs))
        profile_instructions = tuple(
            instruction
            for profile_id in profile_ids
            for instruction in PROFILE_INSTRUCTIONS[profile_id]
        )
        batches.append(
            RepertoireBatch(
                batch_id=expected_batch_id,
                design_group=design_group,
                profile_ids=profile_ids,
                profile_instructions=profile_instructions,
                glyphs=tuple(glyphs),
                empty_grid_cells=empty_grid_cells,
                record=copy.deepcopy(raw_batch),
            )
        )

    if len(seen_labels) != VISIBLE_GLYPH_COUNT:
        raise MaterializationError(
            f"{path}: expected {VISIBLE_GLYPH_COUNT} unique visible codepoints, "
            f"got {len(seen_labels)}"
        )

    semantic_where = f"{path}: batches[{BATCH_COUNT}]"
    semantic_batch = raw_batches[BATCH_COUNT]
    if not isinstance(semantic_batch, dict):
        raise MaterializationError(f"{semantic_where}: expected an object")
    semantic_labels = semantic_batch.get("glyph_codepoints")
    if (
        semantic_batch.get("batch_id") != "nonhan-0206"
        or semantic_batch.get("batch_kind") != "semantic-empty"
        or semantic_batch.get("design_group") != "P04-SEMANTIC-EMPTY"
        or not isinstance(semantic_labels, list)
        or len(semantic_labels) != SEMANTIC_EMPTY_COUNT
    ):
        raise MaterializationError(
            f"{semantic_where}: invalid semantic-empty terminal batch"
        )
    if set(semantic_labels).intersection(seen_labels):
        raise MaterializationError(f"{semantic_where}: overlaps raster batches")
    for codepoint_label in semantic_labels:
        if (
            codepoint_label not in glyph_index
            or glyph_index[codepoint_label].record.get("outline_required") is not False
        ):
            raise MaterializationError(
                f"{semantic_where}: invalid semantic-empty {codepoint_label!r}"
            )
    if seen_labels.union(semantic_labels) != set(glyph_index):
        raise MaterializationError(f"{path}: batch partition is not exhaustive")

    counts = payload.get("counts")
    if not isinstance(counts, dict) or counts != {
        "total": 3060,
        "outline_required": 3043,
        "semantic_empty": 17,
        "visible_nonspacing_marks": 112,
        "visible_raster_batches": 205,
        "total_batches": 206,
    }:
        raise MaterializationError(f"{path}: frozen counts contract changed")
    return payload, tuple(batches)


def _manifest_font_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _reference_face_lookup(
    faces: Sequence[ReferenceFace],
) -> dict[tuple[str, str, int], ReferenceFace]:
    return {
        (face.manifest_path, face.file_sha256, face.face_index): face
        for face in faces
    }


def _fit_font_and_bbox(
    face: ReferenceFace, character: str
) -> tuple[ImageFont.FreeTypeFont, tuple[int, int, int, int]]:
    font = _pillow_font(
        str(face.path), face.face_index, COPYBOOK_BASE_FONT_SIZE
    )
    bbox = font.getbbox(character)
    if bbox is None or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise MaterializationError(
            f"{face.path} face {face.face_index}: empty Pillow bbox for "
            f"U+{ord(character):04X}"
        )
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    ratio = min(
        COPYBOOK_GLYPH_BOX / max(width, 1),
        COPYBOOK_GLYPH_BOX / max(height, 1),
    )
    target_size = max(
        48,
        min(
            COPYBOOK_MAX_FONT_SIZE,
            int(round(COPYBOOK_BASE_FONT_SIZE * ratio)),
        ),
    )
    font = _pillow_font(str(face.path), face.face_index, target_size)
    bbox = font.getbbox(character)
    if bbox is None or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise MaterializationError(
            f"{face.path} face {face.face_index}: fitted glyph has no bbox"
        )
    return font, bbox


def render_copybook(
    batch: RepertoireBatch,
    references: Mapping[int, Mapping[str, Any]],
    faces: Sequence[ReferenceFace],
) -> bytes:
    """Render a deterministic unlabeled 4×4 identity-only copybook PNG."""

    face_lookup = _reference_face_lookup(faces)
    image = Image.new("L", (COPYBOOK_SIDE, COPYBOOK_SIDE), 255)
    draw = ImageDraw.Draw(image)
    for position in range(ROWS + 1):
        coordinate = min(COPYBOOK_SIDE - 1, position * COPYBOOK_CELL)
        draw.line(
            (coordinate, 0, coordinate, COPYBOOK_SIDE - 1),
            fill=COPYBOOK_GRID_GRAY,
            width=3,
        )
        draw.line(
            (0, coordinate, COPYBOOK_SIDE - 1, coordinate),
            fill=COPYBOOK_GRID_GRAY,
            width=3,
        )

    for cell_index, glyph in enumerate(batch.glyphs):
        reference = references[glyph.codepoint]
        key = (
            str(reference["font_path"]),
            str(reference["font_sha256"]),
            int(reference["font_index"]),
        )
        if key not in face_lookup:
            raise MaterializationError(
                f"{batch.batch_id} {glyph.codepoint_label}: unknown reference face"
            )
        face = face_lookup[key]
        if face.glyphs.get(glyph.codepoint) != reference["glyph_name"]:
            raise MaterializationError(
                f"{batch.batch_id} {glyph.codepoint_label}: reference cmap drift"
            )
        font, bbox = _fit_font_and_bbox(face, glyph.character)
        row, column = divmod(cell_index, COLUMNS)
        cell_left = column * COPYBOOK_CELL
        cell_top = row * COPYBOOK_CELL
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x = cell_left + (COPYBOOK_CELL - width) // 2 - bbox[0]
        y = cell_top + (COPYBOOK_CELL - height) // 2 - bbox[1]
        before = image.crop(
            (
                cell_left + 4,
                cell_top + 4,
                cell_left + COPYBOOK_CELL - 4,
                cell_top + COPYBOOK_CELL - 4,
            )
        )
        draw.text((x, y), glyph.character, font=font, fill=COPYBOOK_GLYPH_BLACK)
        after = image.crop(
            (
                cell_left + 4,
                cell_top + 4,
                cell_left + COPYBOOK_CELL - 4,
                cell_top + COPYBOOK_CELL - 4,
            )
        )
        if before.tobytes() == after.tobytes():
            raise MaterializationError(
                f"{batch.batch_id} {glyph.codepoint_label}: copybook cell has no ink"
            )

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def prompt_for(
    batch: RepertoireBatch,
    *,
    repertoire_path: Path,
    repertoire_sha256: str,
    copybook_path: Path,
    copybook_sha256: str,
    style_sha256: str,
) -> str:
    """Return the exact recorded image-generation prompt for one batch."""

    cells = "\n".join(
        f"- Cell {index:02d}: `{glyph.codepoint_label}` "
        f"{glyph.unicode_name} — character `{glyph.character}` — "
        f"profile `{glyph.profile_id}` — metrics "
        f"`{json.dumps(glyph.metrics, ensure_ascii=False, separators=(',', ':'))}`"
        for index, glyph in enumerate(batch.glyphs, start=1)
    )
    empty_note = (
        f"Cells {len(batch.glyphs) + 1:02d}–16 are intentionally unused and "
        "must remain completely blank."
        if batch.empty_grid_cells
        else "All sixteen cells are occupied."
    )
    profile_text = "\n".join(
        f"- [{profile_id}] {instruction}"
        for profile_id in batch.profile_ids
        for instruction in PROFILE_INSTRUCTIONS[profile_id]
    )
    batch_section = (
        f"\n{BATCH_INSTRUCTIONS[batch.batch_id]}\n"
        if batch.batch_id in BATCH_INSTRUCTIONS
        else ""
    )
    profile_display = ", ".join(batch.profile_ids)
    repertoire_display = _manifest_font_path(repertoire_path)
    copybook_display = _manifest_font_path(copybook_path)
    style_display = _manifest_font_path(STYLE_REFERENCE)
    separator_guidance = (
        "Keep all black source ink well away from separators. For box-drawing "
        "and block-element profiles, exact Unicode edge placement is applied "
        "later as standard vector metric normalization; the generated raster "
        "must supply the original topology, line weights, fill pattern, and "
        "relative proportions."
    )
    primary_request = (
        f"Primary request: draw exactly {len(batch.glyphs)} new isolated "
        "glyphs in a\nstrict four-by-four grid, in the exact row-major "
        "cell order below. Author each\nglyph as original Clear Hand TC "
        "handwriting from a blank canvas."
    )
    exact_prompt = f"""Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for original non-Han
glyphs in the Clear Hand TC family

Input images:
1. Image 1 (`{style_display}`, SHA-256 `{style_sha256}`) is STYLE ONLY.
   Match its fine black gel-pen weight, rounded terminals, natural but
   controlled handwriting rhythm, optical scale, pure-white background, and
   faint 4×4 grid. Do not copy its Han characters.
2. Image 2 (`{copybook_display}`, SHA-256 `{copybook_sha256}`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

{primary_request}

Design group: `{batch.design_group}`
Metric/design profiles present: `{profile_display}`
{profile_text}

Exact occupied cells:
{cells}
{batch_section}
Unused cells: {empty_note}

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. {separator_guidance} Use
pure white with no texture, gradient, lighting, or shadow.

Constraints: preserve every requested Unicode identity, direction, topology,
dot, line count, enclosure, fill state, and paired distinction; output each
target exactly once and only in its assigned cell; keep the style handwritten
and legible at small text sizes. The identity copybook is evidence, never an
outline source.

Do not include any U+XXXX label, Unicode name, cell number, caption, legend,
dotted-circle carrier, annotation, signature, logo, or watermark. Do not
render anything in unused cells. Avoid typeset appearance, brush blobs, dry
brush, ink splatter, sharp miter spikes, thorn-like protrusions, clipping,
duplicate glyphs, missing glyphs, reordered cells, or unintended black bridges
between neighboring cells."""
    return f"""# Image-generated non-Han sheet {batch.batch_id}

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/{batch.batch_id}.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `{repertoire_display}`
- Repertoire SHA-256: `{repertoire_sha256}`
- Design group: `{batch.design_group}`
- Metric/design profiles: `{profile_display}`
- Style reference: `{style_display}` (`{style_sha256}`)
- Identity copybook: `{copybook_display}` (`{copybook_sha256}`)
- Copybook role: identity-reference-only-no-outline-import
- State: awaiting generation; all review gates pending

## Exact tool prompt

```text
{exact_prompt}
```
"""


def _descriptor_glyphs(
    batch: RepertoireBatch,
    references: Mapping[int, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for glyph in batch.glyphs:
        record = copy.deepcopy(dict(glyph.record))
        if "copybook_reference" in record:
            raise MaterializationError(
                f"{batch.batch_id} {glyph.codepoint_label}: repertoire record "
                "already owns reserved copybook_reference key"
            )
        record["copybook_reference"] = copy.deepcopy(
            dict(references[glyph.codepoint])
        )
        records.append(record)
    return records


def draft_descriptor_for(
    batch: RepertoireBatch,
    *,
    repertoire_path: Path,
    repertoire_id: str,
    repertoire_sha256: str,
    copybook_sha256: str,
    style_sha256: str,
    references: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Create a schema-v2 pre-generation descriptor skeleton."""

    return {
        "schema_version": 2,
        "batch_id": f"imagegen-{batch.batch_id}",
        "state": "awaiting-generation",
        "generator": "built-in-image_gen",
        "generator_call": None,
        "repertoire": {
            "path": "../repertoires/nonhan-3060.json",
            "sha256": repertoire_sha256,
            "repertoire_id": repertoire_id,
            "batch_id": batch.batch_id,
        },
        "raster": f"../raster/{batch.batch_id}.png",
        "raster_sha256": None,
        "prompt": f"../prompts/{batch.batch_id}.md",
        "copybook": {
            "path": f"../copybooks/{batch.batch_id}.png",
            "sha256": copybook_sha256,
            "role": "identity-reference-only-no-outline-import",
        },
        "style_reference": {
            "path": "../raster/common-0001.png",
            "sha256": style_sha256,
            "role": "style-only",
        },
        "grid": {
            "rows": ROWS,
            "columns": COLUMNS,
            "glyphs": _descriptor_glyphs(batch, references),
            "empty_grid_cells": batch.empty_grid_cells,
        },
        "review": {
            "identity": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }


def _atomic_replace_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_replace_text(path: Path, value: str) -> None:
    _atomic_replace_bytes(path, value.encode("utf-8"))


def _atomic_create_text(path: Path, value: str) -> None:
    """Publish one complete file atomically while refusing any overwrite."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise MaterializationError(
                f"{path}: refusing to overwrite an existing canonical descriptor"
            ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize(
    *,
    repertoire_path: Path = REPERTOIRE,
    imagegen_root: Path = IMAGEGEN_ROOT,
    font_paths: Sequence[Path] = DEFAULT_REFERENCE_FONTS,
) -> dict[str, Any]:
    """Materialize all copybooks, prompts, and draft descriptors."""

    repertoire_path = repertoire_path.resolve()
    imagegen_root = imagegen_root.resolve()
    payload, batches = load_repertoire(repertoire_path)
    style_reference = imagegen_root / "raster/common-0001.png"
    if not style_reference.is_file():
        raise MaterializationError(f"{style_reference}: style reference is missing")
    style_hash = sha256(style_reference)
    repertoire_hash = sha256(repertoire_path)
    repertoire_id = str(payload["repertoire_id"])
    all_glyphs = tuple(glyph for batch in batches for glyph in batch.glyphs)
    faces = load_reference_faces(
        (glyph.codepoint for glyph in all_glyphs), font_paths
    )
    references = select_references(all_glyphs, faces)

    copybook_root = imagegen_root / "copybooks"
    prompt_root = imagegen_root / "prompts"
    batch_root = imagegen_root / "batches"
    for batch in batches:
        canonical = batch_root / f"{batch.batch_id}.source.json"
        if canonical.exists():
            raise MaterializationError(
                f"{canonical}: canonical descriptor already exists; "
                "materialize refuses to mutate registered provenance"
            )

    copybook_hashes: dict[str, str] = {}
    for batch in batches:
        copybook_path = copybook_root / f"{batch.batch_id}.png"
        copybook_bytes = render_copybook(batch, references, faces)
        _atomic_replace_bytes(copybook_path, copybook_bytes)
        copybook_hash = sha256(copybook_path)
        copybook_hashes[batch.batch_id] = copybook_hash

        prompt = prompt_for(
            batch,
            repertoire_path=repertoire_path,
            repertoire_sha256=repertoire_hash,
            copybook_path=copybook_path,
            copybook_sha256=copybook_hash,
            style_sha256=style_hash,
        )
        _atomic_replace_text(prompt_root / f"{batch.batch_id}.md", prompt)

        descriptor = draft_descriptor_for(
            batch,
            repertoire_path=repertoire_path,
            repertoire_id=repertoire_id,
            repertoire_sha256=repertoire_hash,
            copybook_sha256=copybook_hash,
            style_sha256=style_hash,
            references=references,
        )
        serialized = json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n"
        _atomic_replace_text(
            batch_root / f"{batch.batch_id}.draft.json", serialized
        )

    font_usage: dict[str, int] = {}
    for reference in references.values():
        key = (
            f"{reference['font_path']}#{reference['font_index']} "
            f"{reference['font_sha256']}"
        )
        font_usage[key] = font_usage.get(key, 0) + 1
    return {
        "schema_version": 1,
        "repertoire": _manifest_font_path(repertoire_path),
        "repertoire_sha256": repertoire_hash,
        "repertoire_id": repertoire_id,
        "batch_count": len(batches),
        "visible_glyph_count": len(references),
        "semantic_empty_glyph_count": SEMANTIC_EMPTY_COUNT,
        "copybook_count": len(copybook_hashes),
        "prompt_count": len(batches),
        "draft_descriptor_count": len(batches),
        "font_usage": font_usage,
    }


def _resolve_descriptor_path(parent: Path, raw: Any, *, where: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise MaterializationError(f"{where}: expected a relative path")
    candidate = (parent / raw).resolve()
    try:
        candidate.relative_to(parent.parent.resolve())
    except ValueError as exc:
        raise MaterializationError(f"{where}: path escapes sources/imagegen") from exc
    return candidate


def _validate_png(path: Path) -> None:
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise MaterializationError(f"{path}: raster must be a PNG")
            if image.width != image.height or image.width < 1024:
                raise MaterializationError(
                    f"{path}: raster must be square and at least 1024 px"
                )
            image.verify()
    except (OSError, UnidentifiedImageError) as exc:
        raise MaterializationError(f"{path}: invalid PNG: {exc}") from exc


def register(
    *,
    batch_id: str,
    generator_call: str,
    raster: Path | None = None,
    imagegen_root: Path = IMAGEGEN_ROOT,
) -> Path:
    """Atomically register one generated raster in a new canonical descriptor."""

    if BATCH_ID_PATTERN.fullmatch(batch_id) is None:
        raise MaterializationError("batch id must be nonhan-NNNN")
    number = int(batch_id[-4:])
    if not 1 <= number <= BATCH_COUNT:
        raise MaterializationError(f"{batch_id}: batch number is outside 0001..0205")
    if (
        not isinstance(generator_call, str)
        or not generator_call.strip()
        or generator_call != generator_call.strip()
        or generator_call.startswith("<")
    ):
        raise MaterializationError("generator call provenance must be non-blank")

    imagegen_root = imagegen_root.resolve()
    batch_root = imagegen_root / "batches"
    draft_path = batch_root / f"{batch_id}.draft.json"
    canonical_path = batch_root / f"{batch_id}.source.json"
    expected_raster = imagegen_root / f"raster/{batch_id}.png"
    raster_path = (raster or expected_raster).resolve()
    if raster_path != expected_raster.resolve():
        raise MaterializationError(
            f"{batch_id}: raster must be exactly {expected_raster.resolve()}"
        )
    if canonical_path.exists():
        raise MaterializationError(
            f"{canonical_path}: refusing to overwrite an existing canonical descriptor"
        )
    draft = _read_json(draft_path)
    if draft.get("schema_version") != 2:
        raise MaterializationError(f"{draft_path}: schema_version must be 2")
    if draft.get("batch_id") != f"imagegen-{batch_id}":
        raise MaterializationError(f"{draft_path}: batch identity mismatch")
    if draft.get("state") != "awaiting-generation":
        raise MaterializationError(
            f"{draft_path}: draft state must be awaiting-generation"
        )
    if draft.get("generator_call") is not None or draft.get("raster_sha256") is not None:
        raise MaterializationError(
            f"{draft_path}: draft must not contain invented raster provenance"
        )

    if not raster_path.is_file():
        raise MaterializationError(f"{raster_path}: generated raster is missing")
    _validate_png(raster_path)

    descriptor_parent = draft_path.parent
    repertoire = draft.get("repertoire")
    if not isinstance(repertoire, dict):
        raise MaterializationError(f"{draft_path}: repertoire object is missing")
    repertoire_path = _resolve_descriptor_path(
        descriptor_parent,
        repertoire.get("path"),
        where=f"{draft_path}: repertoire.path",
    )
    if not repertoire_path.is_file() or sha256(repertoire_path) != repertoire.get(
        "sha256"
    ):
        raise MaterializationError(f"{draft_path}: repertoire hash mismatch")

    for key in ("copybook", "style_reference"):
        record = draft.get(key)
        if not isinstance(record, dict):
            raise MaterializationError(f"{draft_path}: {key} object is missing")
        asset = _resolve_descriptor_path(
            descriptor_parent,
            record.get("path"),
            where=f"{draft_path}: {key}.path",
        )
        if not asset.is_file() or sha256(asset) != record.get("sha256"):
            raise MaterializationError(f"{draft_path}: {key} hash mismatch")
    prompt_path = _resolve_descriptor_path(
        descriptor_parent,
        draft.get("prompt"),
        where=f"{draft_path}: prompt",
    )
    if not prompt_path.is_file():
        raise MaterializationError(f"{draft_path}: exact prompt is missing")

    canonical = copy.deepcopy(draft)
    canonical["state"] = "generated-unreviewed"
    canonical["generator_call"] = generator_call
    canonical["raster_sha256"] = sha256(raster_path)
    expected_review = {
        "identity": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }
    if canonical.get("review") != expected_review:
        raise MaterializationError(
            f"{draft_path}: all source review gates must remain pending"
        )
    serialized = json.dumps(canonical, ensure_ascii=False, indent=2) + "\n"
    _atomic_create_text(canonical_path, serialized)
    return canonical_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize_parser = subparsers.add_parser(
        "materialize", help="write all 205 copybooks/prompts/draft descriptors"
    )
    materialize_parser.add_argument("--repertoire", type=Path, default=REPERTOIRE)
    materialize_parser.add_argument(
        "--font",
        action="append",
        type=Path,
        dest="fonts",
        help="ordered local reference font; repeat to replace the default set",
    )

    register_parser = subparsers.add_parser(
        "register", help="hash-pin one generated PNG and generator call"
    )
    register_parser.add_argument("batch_id")
    register_parser.add_argument("--generator-call", required=True)
    register_parser.add_argument("--raster", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "materialize":
        summary = materialize(
            repertoire_path=args.repertoire,
            font_paths=tuple(args.fonts) if args.fonts else DEFAULT_REFERENCE_FONTS,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    output = register(
        batch_id=args.batch_id,
        generator_call=args.generator_call,
        raster=args.raster,
    )
    print(output)


if __name__ == "__main__":
    main()
