#!/usr/bin/env python3
"""Materialize identity copybooks, exact prompts, and Han-delta drafts.

The collection manifest is the only family-specific input. External reference
font binaries stay local and are admitted only by exact path, SHA-256, cmap,
non-.notdef outline, and non-empty raster checks. Their printed outlines are
identity evidence only and never become font outlines.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence
import unicodedata

from PIL import Image, ImageDraw, ImageFont

from scripts.identity_reference_catalog import (
    IdentityReferenceCatalogError,
    ReferenceFace,
    load_reference_faces,
    pillow_font,
    select_references,
)
from scripts.register_han_delta_sheet import (
    HanDeltaCollection,
    HanDeltaRegistrationError,
    IDENTITY_COPYBOOK_ROLE,
    IDENTITY_MATERIALIZER,
    load_collection,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTION = Path(
    "sources/imagegen/collections/"
    "clear-hand-tc-dictionary-salience-1216.json"
)
DRAFT_RECORD_TYPE = "imagegen-han-delta-draft"
MATERIALIZATION_CONTRACT = "neutral-han-identity-copybook-v1"
COPYBOOK_SIDE = 1600
GRID_SIZE = 4
CELL_SIZE = COPYBOOK_SIDE // GRID_SIZE
GRID_GRAY = 218
INK_BLACK = 0
REFERENCE_VALIDATION = (
    "exact-cmap-hit",
    "non-notdef-glyph-name",
    "non-empty-distinct-outline",
    "non-empty-pillow-raster",
)


class HanDeltaMaterializationError(RuntimeError):
    """A Han-delta materialization input or artifact is not exact."""


@dataclass(frozen=True)
class CatalogGlyph:
    """One scalar identity requested from the shared font catalog."""

    character: str
    codepoint: int
    codepoint_label: str


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def _relative(path: Path, *, from_directory: Path) -> str:
    return Path(
        os.path.relpath(path.resolve(), start=from_directory.resolve())
    ).as_posix()


def _character_records(
    collection: HanDeltaCollection,
) -> dict[int, Mapping[str, Any]]:
    records = collection.repertoire.payload["characters"]
    result = {
        int(record["codepoint"]): record
        for record in records
    }
    if len(result) != len(records):
        raise HanDeltaMaterializationError(
            "repertoire character records are not unique"
        )
    return result


def _composition_index(
    collection: HanDeltaCollection,
) -> dict[int, Mapping[str, Any]]:
    result = {
        ord(str(record["character"])): record
        for record in collection.identity_compositions
    }
    if len(result) != len(collection.identity_compositions):
        raise HanDeltaMaterializationError(
            "identity composition targets are not unique"
        )
    return result


def _configured_font_paths(
    collection: HanDeltaCollection,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for index, record in enumerate(
        collection.identity_reference_fonts
    ):
        path = Path(str(record["path"])).expanduser().resolve()
        if not path.is_file():
            raise HanDeltaMaterializationError(
                f"identity reference font {index} is missing: {path}"
            )
        if sha256_path(path) != record["sha256"]:
            raise HanDeltaMaterializationError(
                f"identity reference font {index} hash mismatch: {path}"
            )
        try:
            path.relative_to(collection.project_root)
        except ValueError:
            pass
        else:
            raise HanDeltaMaterializationError(
                "identity reference font binaries must remain external"
            )
        paths.append(path)
    if len(set(paths)) != len(paths):
        raise HanDeltaMaterializationError(
            "identity reference font paths resolve to duplicates"
        )
    return tuple(paths)


def _catalog_glyph(
    character: str,
    *,
    record: Mapping[str, Any],
) -> CatalogGlyph:
    codepoint = ord(character)
    if (
        record.get("character") != character
        or int(record.get("codepoint", -1)) != codepoint
    ):
        raise HanDeltaMaterializationError(
            f"catalog record identity mismatch for U+{codepoint:04X}"
        )
    return CatalogGlyph(
        character=character,
        codepoint=codepoint,
        codepoint_label=f"U+{codepoint:04X}",
    )


def _reference_catalog(
    collection: HanDeltaCollection,
) -> tuple[
    tuple[ReferenceFace, ...],
    dict[int, dict[str, Any]],
]:
    character_records = _character_records(collection)
    compositions = _composition_index(collection)
    catalog: dict[int, CatalogGlyph] = {}
    for codepoint, record in character_records.items():
        if codepoint not in compositions:
            catalog[codepoint] = _catalog_glyph(
                chr(codepoint),
                record=record,
            )
    for composition in compositions.values():
        for component in composition["components"]:
            character = str(component["character"])
            codepoint = ord(character)
            catalog.setdefault(
                codepoint,
                _catalog_glyph(
                    character,
                    record={
                        "character": character,
                        "codepoint": codepoint,
                        "unicode": f"U+{codepoint:04X}",
                    },
                ),
            )
    font_paths = _configured_font_paths(collection)
    try:
        faces = load_reference_faces(catalog, font_paths)
        selected = select_references(catalog.values(), faces)
    except IdentityReferenceCatalogError as exc:
        raise HanDeltaMaterializationError(str(exc)) from exc

    configured = {
        str(path): record
        for path, record in zip(
            font_paths,
            collection.identity_reference_fonts,
            strict=True,
        )
    }
    references: dict[int, dict[str, Any]] = {}
    for codepoint, reference in selected.items():
        raw_font_path = str(reference["font_path"])
        font_path = str(Path(raw_font_path).resolve())
        if font_path not in configured:
            raise HanDeltaMaterializationError(
                f"unconfigured identity reference font: {font_path}"
            )
        source = configured[font_path]
        if reference["font_sha256"] != source["sha256"]:
            raise HanDeltaMaterializationError(
                f"identity reference font hash drifted: {font_path}"
            )
        references[codepoint] = {
            "path": source["path"],
            "sha256": reference["font_sha256"],
            "face_index": reference["font_index"],
            "postscript_name": reference["postscript_name"],
            "glyph_name": reference["glyph_name"],
            "source_name": source["source_name"],
            "source_url": source["source_url"],
            "license": source["license"],
            "external_font_binary_committed": False,
            "validation": list(REFERENCE_VALIDATION),
        }
    return faces, references


def _identity_reference(
    character: str,
    *,
    references: Mapping[int, Mapping[str, Any]],
    compositions: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    codepoint = ord(character)
    base = {
        "character": character,
        "codepoint": f"U+{codepoint:04X}",
        "role": IDENTITY_COPYBOOK_ROLE,
    }
    if codepoint not in compositions:
        if codepoint not in references:
            raise HanDeltaMaterializationError(
                f"missing exact identity reference for U+{codepoint:04X}"
            )
        return {
            **base,
            "method": "exact-cmap-glyph",
            "font": copy.deepcopy(dict(references[codepoint])),
        }
    composition = compositions[codepoint]
    components: list[dict[str, Any]] = []
    for component in composition["components"]:
        component_character = str(component["character"])
        component_codepoint = ord(component_character)
        if component_codepoint not in references:
            raise HanDeltaMaterializationError(
                "missing exact identity reference for composition "
                f"component U+{component_codepoint:04X}"
            )
        components.append(
            {
                "character": component_character,
                "codepoint": f"U+{component_codepoint:04X}",
                "placement": component["placement"],
                "font": copy.deepcopy(
                    dict(references[component_codepoint])
                ),
            }
        )
    return {
        **base,
        "method": composition["method"],
        "display": composition["display"],
        "authorization": composition["authorization"],
        "components": components,
    }


def _validated_font_provenance(
    value: Any,
    *,
    collection: HanDeltaCollection,
    where: str,
) -> dict[str, Any]:
    expected_keys = {
        "path",
        "sha256",
        "face_index",
        "postscript_name",
        "glyph_name",
        "source_name",
        "source_url",
        "license",
        "external_font_binary_committed",
        "validation",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise HanDeltaMaterializationError(
            f"{where}: font provenance key set drifted"
        )
    configured = {
        str(record["path"]): record
        for record in collection.identity_reference_fonts
    }
    raw_path = value["path"]
    if not isinstance(raw_path, str) or raw_path not in configured:
        raise HanDeltaMaterializationError(
            f"{where}: font path is not admitted by the collection"
        )
    expected = configured[raw_path]
    if (
        value["sha256"] != expected["sha256"]
        or value["source_name"] != expected["source_name"]
        or value["source_url"] != expected["source_url"]
        or value["license"] != expected["license"]
        or value["external_font_binary_committed"] is not False
        or value["validation"] != list(REFERENCE_VALIDATION)
        or not isinstance(value["face_index"], int)
        or isinstance(value["face_index"], bool)
        or value["face_index"] < 0
        or not isinstance(value["postscript_name"], str)
        or not value["postscript_name"]
        or not isinstance(value["glyph_name"], str)
        or not value["glyph_name"]
    ):
        raise HanDeltaMaterializationError(
            f"{where}: font provenance differs from the collection policy"
        )
    return copy.deepcopy(value)


def _validated_identity_references(
    value: Any,
    *,
    collection: HanDeltaCollection,
    characters: Sequence[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(characters):
        raise HanDeltaMaterializationError(
            "copybook reference cardinality differs from the batch"
        )
    compositions = _composition_index(collection)
    validated: list[dict[str, Any]] = []
    for index, (raw, character) in enumerate(
        zip(value, characters, strict=True)
    ):
        where = f"copybook reference {index}"
        if not isinstance(raw, dict):
            raise HanDeltaMaterializationError(
                f"{where}: expected an object"
            )
        codepoint = ord(character)
        common = {
            "character": character,
            "codepoint": f"U+{codepoint:04X}",
            "role": IDENTITY_COPYBOOK_ROLE,
        }
        if any(raw.get(key) != expected for key, expected in common.items()):
            raise HanDeltaMaterializationError(
                f"{where}: character identity or role drifted"
            )
        if codepoint not in compositions:
            if set(raw) != {
                "character",
                "codepoint",
                "role",
                "method",
                "font",
            } or raw.get("method") != "exact-cmap-glyph":
                raise HanDeltaMaterializationError(
                    f"{where}: exact-cmap contract drifted"
                )
            validated.append(
                {
                    **common,
                    "method": "exact-cmap-glyph",
                    "font": _validated_font_provenance(
                        raw["font"],
                        collection=collection,
                        where=f"{where}.font",
                    ),
                }
            )
            continue
        composition = compositions[codepoint]
        if (
            set(raw)
            != {
                "character",
                "codepoint",
                "role",
                "method",
                "display",
                "authorization",
                "components",
            }
            or raw.get("method") != composition["method"]
            or raw.get("display") != composition["display"]
            or raw.get("authorization")
            != composition["authorization"]
        ):
            raise HanDeltaMaterializationError(
                f"{where}: composition contract drifted"
            )
        raw_components = raw.get("components")
        expected_components = composition["components"]
        if (
            not isinstance(raw_components, list)
            or len(raw_components) != len(expected_components)
        ):
            raise HanDeltaMaterializationError(
                f"{where}: composition components drifted"
            )
        components: list[dict[str, Any]] = []
        for component_index, (
            raw_component,
            expected_component,
        ) in enumerate(
            zip(raw_components, expected_components, strict=True)
        ):
            if (
                not isinstance(raw_component, dict)
                or set(raw_component)
                != {"character", "codepoint", "placement", "font"}
                or any(
                    raw_component.get(key) != expected_component[key]
                    for key in ("character", "codepoint", "placement")
                )
            ):
                raise HanDeltaMaterializationError(
                    f"{where}: component {component_index} drifted"
                )
            components.append(
                {
                    "character": expected_component["character"],
                    "codepoint": expected_component["codepoint"],
                    "placement": expected_component["placement"],
                    "font": _validated_font_provenance(
                        raw_component["font"],
                        collection=collection,
                        where=(
                            f"{where}.components[{component_index}].font"
                        ),
                    ),
                }
            )
        validated.append(
            {
                **common,
                "method": composition["method"],
                "display": composition["display"],
                "authorization": composition["authorization"],
                "components": components,
            }
        )
    return validated


def _face_index(
    faces: Sequence[ReferenceFace],
) -> dict[tuple[str, str, int], ReferenceFace]:
    return {
        (
            str(face.path.resolve()),
            face.file_sha256,
            face.face_index,
        ): face
        for face in faces
    }


def _fit_font(
    face: ReferenceFace,
    character: str,
    *,
    maximum_width: int,
    maximum_height: int,
) -> tuple[ImageFont.FreeTypeFont, tuple[int, int, int, int]]:
    probe_size = 300
    probe = pillow_font(
        str(face.path),
        face.face_index,
        probe_size,
    )
    bbox = probe.getbbox(character)
    if bbox is None or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise HanDeltaMaterializationError(
            f"empty identity reference for U+{ord(character):04X}"
        )
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    scale = min(
        maximum_width / width,
        maximum_height / height,
    )
    size = max(32, min(420, int(round(probe_size * scale))))
    font = pillow_font(str(face.path), face.face_index, size)
    fitted = font.getbbox(character)
    if (
        fitted is None
        or fitted[2] <= fitted[0]
        or fitted[3] <= fitted[1]
    ):
        raise HanDeltaMaterializationError(
            f"fitted identity reference is empty for U+{ord(character):04X}"
        )
    return font, fitted


def _reference_face(
    font: Mapping[str, Any],
    *,
    faces: Mapping[tuple[str, str, int], ReferenceFace],
) -> ReferenceFace:
    key = (
        str(Path(str(font["path"])).expanduser().resolve()),
        str(font["sha256"]),
        int(font["face_index"]),
    )
    if key not in faces:
        raise HanDeltaMaterializationError(
            f"identity reference face is not admitted: {key[0]}"
        )
    return faces[key]


def _draw_character(
    draw: ImageDraw.ImageDraw,
    *,
    character: str,
    font_record: Mapping[str, Any],
    faces: Mapping[tuple[str, str, int], ReferenceFace],
    box: tuple[int, int, int, int],
) -> None:
    face = _reference_face(font_record, faces=faces)
    expected_name = face.glyphs.get(ord(character))
    if expected_name != font_record["glyph_name"]:
        raise HanDeltaMaterializationError(
            f"identity cmap drifted for U+{ord(character):04X}"
        )
    left, top, right, bottom = box
    font, bbox = _fit_font(
        face,
        character,
        maximum_width=right - left,
        maximum_height=bottom - top,
    )
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = left + (right - left - width) // 2 - bbox[0]
    y = top + (bottom - top - height) // 2 - bbox[1]
    draw.text((x, y), character, font=font, fill=INK_BLACK)


def render_copybook(
    characters: Sequence[str],
    *,
    identity_references: Sequence[Mapping[str, Any]],
    faces: Sequence[ReferenceFace],
) -> bytes:
    """Render one deterministic, unlabeled 4×4 identity-only sheet."""

    if len(characters) != 16 or len(identity_references) != 16:
        raise HanDeltaMaterializationError(
            "Han-delta copybooks require exactly sixteen occupied cells"
        )
    face_lookup = _face_index(faces)
    image = Image.new("L", (COPYBOOK_SIDE, COPYBOOK_SIDE), 255)
    draw = ImageDraw.Draw(image)
    for position in range(GRID_SIZE + 1):
        coordinate = min(COPYBOOK_SIDE - 1, position * CELL_SIZE)
        draw.line(
            (coordinate, 0, coordinate, COPYBOOK_SIDE - 1),
            fill=GRID_GRAY,
            width=3,
        )
        draw.line(
            (0, coordinate, COPYBOOK_SIDE - 1, coordinate),
            fill=GRID_GRAY,
            width=3,
        )
    for cell_index, (character, reference) in enumerate(
        zip(characters, identity_references, strict=True)
    ):
        if (
            reference["character"] != character
            or reference["codepoint"] != f"U+{ord(character):04X}"
        ):
            raise HanDeltaMaterializationError(
                "identity reference order differs from repertoire batch"
            )
        row, column = divmod(cell_index, GRID_SIZE)
        left = column * CELL_SIZE
        top = row * CELL_SIZE
        before = image.crop(
            (left + 5, top + 5, left + CELL_SIZE - 5, top + CELL_SIZE - 5)
        ).tobytes()
        if reference["method"] == "exact-cmap-glyph":
            _draw_character(
                draw,
                character=character,
                font_record=reference["font"],
                faces=face_lookup,
                box=(left + 55, top + 45, left + 345, top + 355),
            )
        elif reference["method"] == "vertical-ideographic-composition":
            upper, lower = reference["components"]
            _draw_character(
                draw,
                character=upper["character"],
                font_record=upper["font"],
                faces=face_lookup,
                box=(left + 80, top + 30, left + 320, top + 155),
            )
            _draw_character(
                draw,
                character=lower["character"],
                font_record=lower["font"],
                faces=face_lookup,
                box=(left + 65, top + 145, left + 335, top + 365),
            )
        else:
            raise HanDeltaMaterializationError(
                f"unsupported identity method: {reference['method']}"
            )
        after = image.crop(
            (left + 5, top + 5, left + CELL_SIZE - 5, top + CELL_SIZE - 5)
        ).tobytes()
        if before == after:
            raise HanDeltaMaterializationError(
                f"copybook cell has no ink for U+{ord(character):04X}"
            )
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _prompt_template(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(r"```text\n(.*?)\n```", text, flags=re.DOTALL)
    if len(matches) != 1:
        raise HanDeltaMaterializationError(
            f"{path}: prompt template must contain one text code fence"
        )
    return matches[0]


def prompt_for(
    collection: HanDeltaCollection,
    *,
    batch_id: str,
    characters: Sequence[str],
    copybook_path: Path,
    copybook_sha256: str,
) -> str:
    """Render the exact per-batch prompt from the pinned collection template."""

    rows = [
        "".join(characters[index : index + GRID_SIZE])
        for index in range(0, len(characters), GRID_SIZE)
    ]
    cell_lines = "\n".join(
        f"- Cell {index:02d}: U+{ord(character):04X} `{character}` "
        f"{unicodedata.name(character, f'CJK UNIFIED IDEOGRAPH-{ord(character):04X}')}"
        for index, character in enumerate(characters, start=1)
    )
    values = {
        "family_id": collection.family_id,
        "character_count": len(characters),
        "row_text": " / ".join(rows),
        "cell_lines": cell_lines,
        "verbatim_rows": "\n".join(rows),
        "unused_cells": (
            "All sixteen cells are occupied."
            if len(characters) == 16
            else (
                f"Cells {len(characters) + 1:02d}–16 are unused and "
                "must remain completely blank."
            )
        ),
    }
    try:
        exact_prompt = _prompt_template(
            collection.prompt_path
        ).format_map(values)
    except (KeyError, ValueError) as exc:
        raise HanDeltaMaterializationError(
            "prompt template variables do not match the materializer"
        ) from exc
    descriptor_directory = collection.descriptor_directory
    collection_reference = _relative(
        collection.path,
        from_directory=descriptor_directory,
    )
    repertoire_reference = _relative(
        collection.repertoire.path,
        from_directory=descriptor_directory,
    )
    template_reference = _relative(
        collection.prompt_path,
        from_directory=descriptor_directory,
    )
    style_reference = _relative(
        collection.style_reference_path,
        from_directory=descriptor_directory,
    )
    copybook_reference = _relative(
        copybook_path,
        from_directory=descriptor_directory,
    )
    return f"""# Image-generated Han-delta sheet {batch_id}

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/{batch_id}.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `{collection_reference}` (`{collection.sha256}`)
- Repertoire: `{repertoire_reference}` (`{collection.repertoire.sha256}`)
- Prompt template: `{template_reference}` (`{collection.prompt_sha256}`)
- Style reference: `{style_reference}` (`{collection.style_reference_sha256}`)
- Identity copybook: `{copybook_reference}` (`{copybook_sha256}`)
- Copybook role: {IDENTITY_COPYBOOK_ROLE}
- State: awaiting generation; all review gates pending

## Exact tool prompt

```text
{exact_prompt}
```
"""


def draft_payload(
    collection: HanDeltaCollection,
    *,
    batch_id: str,
    prompt_path: Path,
    prompt_sha256: str,
    copybook_path: Path,
    copybook_sha256: str,
    identity_references: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return one exact pre-generation descriptor."""

    batches = [
        batch
        for batch in collection.repertoire.batches
        if batch.batch_id == batch_id
    ]
    if len(batches) != 1:
        raise HanDeltaMaterializationError(
            f"{batch_id}: not in the frozen collection repertoire"
        )
    batch = batches[0]
    characters = list(batch.characters)
    if len(identity_references) != len(characters):
        raise HanDeltaMaterializationError(
            f"{batch_id}: identity reference cardinality mismatch"
        )
    descriptor_directory = collection.descriptor_directory
    return {
        "schema_version": 1,
        "record_type": DRAFT_RECORD_TYPE,
        "vector_pipeline": collection.vector_pipeline,
        "batch_id": f"imagegen-{batch_id}",
        "state": "awaiting-generation",
        "generator": "built-in-image_gen",
        "generator_call": None,
        "collection": {
            "path": _relative(
                collection.path,
                from_directory=descriptor_directory,
            ),
            "sha256": collection.sha256,
            "collection_id": collection.collection_id,
            "family_id": collection.family_id,
        },
        "raster": f"../raster/{batch_id}.png",
        "raster_sha256": None,
        "prompt": {
            "path": _relative(
                prompt_path,
                from_directory=descriptor_directory,
            ),
            "sha256": prompt_sha256,
            "template_path": _relative(
                collection.prompt_path,
                from_directory=descriptor_directory,
            ),
            "template_sha256": collection.prompt_sha256,
        },
        "style_reference": {
            "role": "style-only-no-outline-import",
            "raster": _relative(
                collection.style_reference_path,
                from_directory=descriptor_directory,
            ),
            "raster_sha256": collection.style_reference_sha256,
        },
        "identity_copybook": {
            "role": IDENTITY_COPYBOOK_ROLE,
            "raster": _relative(
                copybook_path,
                from_directory=descriptor_directory,
            ),
            "raster_sha256": copybook_sha256,
            "provenance": {
                "materializer": IDENTITY_MATERIALIZER,
                "contract": MATERIALIZATION_CONTRACT,
                "source_name": (
                    "neutral local-font Han identity copybook"
                ),
                "source_url": None,
                "license": (
                    "identity-reference-only; source licenses are "
                    "recorded per cell"
                ),
                "external_font_binary_committed": False,
                "references": copy.deepcopy(
                    list(identity_references)
                ),
            },
        },
        "repertoire": {
            "path": _relative(
                collection.repertoire.path,
                from_directory=descriptor_directory,
            ),
            "sha256": collection.repertoire.sha256,
            "repertoire_id": collection.repertoire.repertoire_id,
            "sequence_sha256": collection.repertoire.sequence_sha256,
            "start_rank": batch.start_rank,
            "end_rank": batch.end_rank,
        },
        "grid": {
            "rows": GRID_SIZE,
            "columns": GRID_SIZE,
            "characters": characters,
            "empty_grid_cells": batch.empty_grid_cells,
        },
        "review": {
            "identity": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }


def _decoded_copybook(path: Path) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            if (
                image.format != "PNG"
                or image.size != (COPYBOOK_SIDE, COPYBOOK_SIDE)
                or image.mode != "L"
            ):
                raise HanDeltaMaterializationError(
                    f"{path}: copybook PNG contract drifted"
                )
            for row in range(GRID_SIZE):
                for column in range(GRID_SIZE):
                    box = (
                        column * CELL_SIZE + 5,
                        row * CELL_SIZE + 5,
                        (column + 1) * CELL_SIZE - 5,
                        (row + 1) * CELL_SIZE - 5,
                    )
                    extrema = image.crop(box).getextrema()
                    if extrema is None or extrema[0] > 32:
                        raise HanDeltaMaterializationError(
                            f"{path}: copybook cell {row * 4 + column + 1} "
                            "has no black identity ink"
                        )
    except OSError as exc:
        raise HanDeltaMaterializationError(
            f"{path}: copybook cannot be decoded"
        ) from exc


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HanDeltaMaterializationError(
            f"{path}: cannot read draft: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise HanDeltaMaterializationError(
            f"{path}: draft must be an object"
        )
    return value


def validate_draft(
    path: Path,
    *,
    project_root: Path = ROOT,
) -> dict[str, Any]:
    """Validate one draft and every retained asset without external fonts."""

    project_root = project_root.resolve()
    path = path.resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise HanDeltaMaterializationError(
            "draft must remain below the project root"
        ) from exc
    if path.is_symlink() or not path.is_file():
        raise HanDeltaMaterializationError(
            f"{path}: draft must be a regular non-symlink file"
        )
    payload = _read_object(path)
    collection_record = payload.get("collection")
    if not isinstance(collection_record, dict):
        raise HanDeltaMaterializationError(
            f"{path}: collection reference is missing"
        )
    raw_collection_path = collection_record.get("path")
    if not isinstance(raw_collection_path, str):
        raise HanDeltaMaterializationError(
            f"{path}: collection path is missing"
        )
    try:
        collection = load_collection(
            (path.parent / raw_collection_path).resolve(),
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise HanDeltaMaterializationError(str(exc)) from exc
    raw_batch_id = payload.get("batch_id")
    if (
        not isinstance(raw_batch_id, str)
        or not raw_batch_id.startswith("imagegen-")
    ):
        raise HanDeltaMaterializationError(
            f"{path}: batch identity is malformed"
        )
    batch_id = raw_batch_id.removeprefix("imagegen-")
    batches = [
        batch
        for batch in collection.repertoire.batches
        if batch.batch_id == batch_id
    ]
    if len(batches) != 1:
        raise HanDeltaMaterializationError(
            f"{path}: batch is outside the frozen repertoire"
        )
    batch = batches[0]
    expected_characters = list(batch.characters)
    expected_path = (
        collection.descriptor_directory
        / f"{batch_id}.draft.json"
    ).resolve()
    if path != expected_path:
        raise HanDeltaMaterializationError(
            f"draft must be exactly {expected_path}"
        )
    copybook = payload.get("identity_copybook")
    prompt = payload.get("prompt")
    if not isinstance(copybook, dict) or not isinstance(prompt, dict):
        raise HanDeltaMaterializationError(
            f"{path}: prompt or identity copybook is missing"
        )
    raw_copybook_path = copybook.get("raster")
    raw_prompt_path = prompt.get("path")
    if (
        not isinstance(raw_copybook_path, str)
        or not isinstance(raw_prompt_path, str)
    ):
        raise HanDeltaMaterializationError(
            f"{path}: retained asset paths are malformed"
        )
    copybook_path = (path.parent / raw_copybook_path).resolve()
    prompt_path = (path.parent / raw_prompt_path).resolve()
    expected_copybook = (
        collection.copybook_directory / f"{batch_id}.png"
    ).resolve()
    expected_prompt = (
        collection.prompt_path.parent / f"{batch_id}.md"
    ).resolve()
    if copybook_path != expected_copybook or prompt_path != expected_prompt:
        raise HanDeltaMaterializationError(
            f"{path}: retained asset path drifted"
        )
    if (
        not copybook_path.is_file()
        or sha256_path(copybook_path) != copybook.get("raster_sha256")
    ):
        raise HanDeltaMaterializationError(
            f"{path}: copybook hash mismatch"
        )
    _decoded_copybook(copybook_path)
    if (
        not prompt_path.is_file()
        or sha256_path(prompt_path) != prompt.get("sha256")
    ):
        raise HanDeltaMaterializationError(
            f"{path}: prompt hash mismatch"
        )
    provenance = copybook.get("provenance")
    if (
        not isinstance(provenance, dict)
        or set(provenance)
        != {
            "materializer",
            "contract",
            "source_name",
            "source_url",
            "license",
            "external_font_binary_committed",
            "references",
        }
        or provenance.get("materializer") != IDENTITY_MATERIALIZER
        or provenance.get("contract") != MATERIALIZATION_CONTRACT
        or provenance.get("source_name")
        != "neutral local-font Han identity copybook"
        or provenance.get("source_url") is not None
        or provenance.get("license")
        != (
            "identity-reference-only; source licenses are "
            "recorded per cell"
        )
        or provenance.get("external_font_binary_committed") is not False
    ):
        raise HanDeltaMaterializationError(
            f"{path}: copybook provenance contract drifted"
        )
    references = _validated_identity_references(
        provenance.get("references"),
        collection=collection,
        characters=expected_characters,
    )
    expected_prompt_text = prompt_for(
        collection,
        batch_id=batch_id,
        characters=expected_characters,
        copybook_path=copybook_path,
        copybook_sha256=sha256_path(copybook_path),
    )
    if prompt_path.read_text(encoding="utf-8") != expected_prompt_text:
        raise HanDeltaMaterializationError(
            f"{path}: exact prompt differs from the collection template"
        )
    rebuilt = draft_payload(
        collection,
        batch_id=batch_id,
        prompt_path=prompt_path,
        prompt_sha256=sha256_path(prompt_path),
        copybook_path=copybook_path,
        copybook_sha256=sha256_path(copybook_path),
        identity_references=references,
    )
    if payload != rebuilt:
        raise HanDeltaMaterializationError(
            f"{path}: draft differs from recomputed retained assets"
        )
    return rebuilt


def materialize(
    collection_path: Path,
    *,
    project_root: Path = ROOT,
) -> dict[str, Any]:
    """Materialize every pre-generation artifact in one Han collection."""

    project_root = project_root.resolve()
    try:
        collection = load_collection(
            collection_path,
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise HanDeltaMaterializationError(str(exc)) from exc
    if not collection.identity_copybook_required:
        raise HanDeltaMaterializationError(
            "Han-delta materialization requires identity copybooks"
        )
    faces, references = _reference_catalog(collection)
    compositions = _composition_index(collection)
    prompt_root = collection.prompt_path.parent
    character_records = _character_records(collection)
    for batch in collection.repertoire.batches:
        source = (
            collection.descriptor_directory
            / f"{batch.batch_id}.source.json"
        )
        if source.exists():
            raise HanDeltaMaterializationError(
                f"{source}: registered provenance already exists"
            )
    draft_paths: list[Path] = []
    font_usage: dict[str, int] = {}
    for batch in collection.repertoire.batches:
        characters = list(batch.characters)
        identity_references = [
            _identity_reference(
                character,
                references=references,
                compositions=compositions,
            )
            for character in characters
        ]
        for reference in identity_references:
            fonts = (
                [reference["font"]]
                if reference["method"] == "exact-cmap-glyph"
                else [
                    component["font"]
                    for component in reference["components"]
                ]
            )
            for font in fonts:
                key = (
                    f"{font['source_name']} {font['path']}#"
                    f"{font['face_index']} {font['sha256']}"
                )
                font_usage[key] = font_usage.get(key, 0) + 1
        copybook_path = (
            collection.copybook_directory / f"{batch.batch_id}.png"
        )
        _atomic_replace(
            copybook_path,
            render_copybook(
                characters,
                identity_references=identity_references,
                faces=faces,
            ),
        )
        copybook_hash = sha256_path(copybook_path)
        prompt_path = prompt_root / f"{batch.batch_id}.md"
        prompt = prompt_for(
            collection,
            batch_id=batch.batch_id,
            characters=characters,
            copybook_path=copybook_path,
            copybook_sha256=copybook_hash,
        )
        _atomic_replace(prompt_path, prompt.encode("utf-8"))
        draft = draft_payload(
            collection,
            batch_id=batch.batch_id,
            prompt_path=prompt_path,
            prompt_sha256=sha256_path(prompt_path),
            copybook_path=copybook_path,
            copybook_sha256=copybook_hash,
            identity_references=identity_references,
        )
        draft_path = (
            collection.descriptor_directory
            / f"{batch.batch_id}.draft.json"
        )
        _atomic_replace(draft_path, _json_bytes(draft))
        validate_draft(draft_path, project_root=project_root)
        draft_paths.append(draft_path)
    if len(character_records) != sum(
        len(batch.characters)
        for batch in collection.repertoire.batches
    ):
        raise HanDeltaMaterializationError(
            "materialized batches do not exhaust the repertoire"
        )
    return {
        "schema_version": 1,
        "record_type": "han-delta-materialization-result",
        "collection_id": collection.collection_id,
        "collection_sha256": collection.sha256,
        "repertoire_id": collection.repertoire.repertoire_id,
        "repertoire_sha256": collection.repertoire.sha256,
        "glyph_count": len(character_records),
        "batch_count": len(draft_paths),
        "copybook_count": len(draft_paths),
        "prompt_count": len(draft_paths),
        "draft_count": len(draft_paths),
        "font_usage": font_usage,
    }


def validate_collection_artifacts(
    collection_path: Path,
    *,
    project_root: Path = ROOT,
) -> dict[str, Any]:
    """Validate that every frozen batch owns all three exact artifacts."""

    project_root = project_root.resolve()
    try:
        collection = load_collection(
            collection_path,
            project_root=project_root,
        )
    except HanDeltaRegistrationError as exc:
        raise HanDeltaMaterializationError(str(exc)) from exc
    for batch in collection.repertoire.batches:
        validate_draft(
            collection.descriptor_directory
            / f"{batch.batch_id}.draft.json",
            project_root=project_root,
        )
    return {
        "collection_id": collection.collection_id,
        "glyph_count": len(collection.repertoire.characters),
        "batch_count": len(collection.repertoire.batches),
        "copybook_count": len(collection.repertoire.batches),
        "prompt_count": len(collection.repertoire.batches),
        "draft_count": len(collection.repertoire.batches),
    }


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument(
        "--collection",
        type=Path,
        default=DEFAULT_COLLECTION,
    )
    parser.add_argument(
        "command",
        choices=("materialize", "validate"),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    collection = args.collection
    if not collection.is_absolute():
        collection = project_root / collection
    result = (
        materialize(collection, project_root=project_root)
        if args.command == "materialize"
        else validate_collection_artifacts(
            collection,
            project_root=project_root,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
