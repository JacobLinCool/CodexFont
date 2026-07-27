#!/usr/bin/env python3
"""Replace rejected cells in an imagegen grid with isolated imagegen masters.

The original grid remains the source of placement, scale, and all accepted
cells.  Each replacement image must contain one isolated dark glyph on a
light background.  The replacement is cleaned, fitted into the rejected
cell's audited ink box without changing its aspect ratio, and composited on a
white cell interior.  Grid rules are never redrawn or synthesized.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from imagegen_font_pipeline import (  # noqa: E402
    INK_CORE_CEILING,
    INK_MIN_COMPONENT_AREA,
    INK_SUPPORT_CEILING,
    INK_SUPPORT_DILATION,
    ImagegenPipelineError,
    detect_grid,
    segment_cells,
)


class CorrectionCompositionError(RuntimeError):
    """A requested grid-cell correction cannot be composed exactly."""


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CorrectionCompositionError(f"{path}: expected a JSON object")
    return payload


def _extract_isolated_glyph(path: Path) -> Image.Image:
    if not path.is_file():
        raise CorrectionCompositionError(f"missing replacement image: {path}")
    gray = np.asarray(Image.open(path).convert("L"), dtype=np.uint8)
    core = gray <= INK_CORE_CEILING
    labels, count = ndimage.label(
        core,
        structure=np.ones((3, 3), dtype=np.uint8),
    )
    if count == 0:
        raise CorrectionCompositionError(f"{path}: no dark glyph found")
    areas = np.bincount(labels.ravel())
    accepted = np.flatnonzero(areas >= INK_MIN_COMPONENT_AREA)
    accepted = accepted[accepted != 0]
    if accepted.size == 0:
        raise CorrectionCompositionError(
            f"{path}: only sub-threshold speckles found"
        )
    kept = np.isin(labels, accepted)
    support = ndimage.binary_dilation(
        kept,
        iterations=INK_SUPPORT_DILATION,
    )
    support &= gray <= INK_SUPPORT_CEILING
    ys, xs = np.nonzero(support)
    if xs.size == 0:
        raise CorrectionCompositionError(
            f"{path}: antialias support contains no ink"
        )
    cleaned = np.full_like(gray, 255)
    cleaned[support] = gray[support]
    cropped = cleaned[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    return Image.fromarray(cropped, mode="L")


def _cell_slots(descriptor: dict[str, Any]) -> tuple[str | None, ...]:
    grid = descriptor.get("grid")
    if not isinstance(grid, dict):
        raise CorrectionCompositionError("descriptor has no grid object")
    characters = grid.get("characters")
    if not isinstance(characters, list):
        raise CorrectionCompositionError(
            "descriptor grid.characters must be a list"
        )
    empty = grid.get("empty_grid_cells")
    if not isinstance(empty, int) or not 0 <= empty <= 16:
        raise CorrectionCompositionError(
            "descriptor grid.empty_grid_cells is invalid"
        )
    slots: tuple[str | None, ...] = tuple(characters) + (None,) * empty
    if len(slots) != 16:
        raise CorrectionCompositionError(
            "descriptor grid must account for exactly 16 cells"
        )
    return slots


def compose(
    *,
    descriptor_path: Path,
    replacements_path: Path,
    output_path: Path,
) -> Path:
    descriptor = _read_object(descriptor_path)
    replacements_payload = _read_object(replacements_path)
    replacements = replacements_payload.get("replacements")
    if not isinstance(replacements, list) or not replacements:
        raise CorrectionCompositionError(
            "replacement manifest must contain a non-empty replacements list"
        )

    raster_value = descriptor.get("raster")
    if not isinstance(raster_value, str):
        raise CorrectionCompositionError("descriptor raster path is invalid")
    source_path = (descriptor_path.parent / raster_value).resolve()
    if not source_path.is_file():
        raise CorrectionCompositionError(f"missing source sheet: {source_path}")
    source = Image.open(source_path).convert("RGB")
    detection = detect_grid(source)
    slots = _cell_slots(descriptor)
    cells = segment_cells(source, detection, slots)
    by_character = {cell.character: cell for cell in cells}
    if len(by_character) != len(cells):
        raise CorrectionCompositionError(
            "source sheet contains duplicate characters"
        )

    composed = source.copy()
    for replacement in replacements:
        if not isinstance(replacement, dict):
            raise CorrectionCompositionError(
                "every replacement entry must be an object"
            )
        character = replacement.get("character")
        image_value = replacement.get("image")
        if (
            not isinstance(character, str)
            or len(character) != 1
            or not isinstance(image_value, str)
        ):
            raise CorrectionCompositionError(
                "replacement requires one character and one image path"
            )
        cell = by_character.get(character)
        if cell is None:
            raise CorrectionCompositionError(
                f"{character}: not present in source descriptor"
            )
        isolated_path = Path(image_value)
        if not isolated_path.is_absolute():
            isolated_path = (
                replacements_path.parent / isolated_path
            ).resolve()
        isolated = _extract_isolated_glyph(isolated_path)

        x0, y0, x1, y1 = cell.source_box
        cell_width = x1 - x0
        cell_height = y1 - y0
        left, bottom, right, top = cell.source_ink_bbox
        target_width = max(1, round((right - left) * cell_width))
        target_height = max(1, round((top - bottom) * cell_height))
        scale = min(
            target_width / isolated.width,
            target_height / isolated.height,
        )
        resized_width = max(1, round(isolated.width * scale))
        resized_height = max(1, round(isolated.height * scale))
        isolated = isolated.resize(
            (resized_width, resized_height),
            Image.Resampling.LANCZOS,
        )

        center_x = x0 + round(((left + right) / 2) * cell_width)
        center_y = y0 + round((1 - (bottom + top) / 2) * cell_height)
        paste_x = center_x - resized_width // 2
        paste_y = center_y - resized_height // 2
        clearance = 7
        composed.paste(
            "white",
            (
                x0 + clearance,
                y0 + clearance,
                x1 - clearance,
                y1 - clearance,
            ),
        )
        glyph_rgb = Image.merge("RGB", (isolated, isolated, isolated))
        composed.paste(
            glyph_rgb,
            (paste_x, paste_y),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    composed.save(output_path, optimize=True)

    # Re-run the same fail-closed segmentation contract before accepting the
    # composed sheet as a registration candidate.
    verification = Image.open(output_path).convert("RGB")
    verification_grid = detect_grid(verification)
    segment_cells(verification, verification_grid, slots)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor", type=Path, required=True)
    parser.add_argument("--replacements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(
        compose(
            descriptor_path=arguments.descriptor.resolve(),
            replacements_path=arguments.replacements.resolve(),
            output_path=arguments.output.resolve(),
        )
    )


if __name__ == "__main__":
    main()
