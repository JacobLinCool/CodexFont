#!/usr/bin/env python3
"""Fail-closed imagegen raster-sheet to quadratic OpenType pilot pipeline.

The input contract is deliberately narrow: one source descriptor names a
lossless PNG containing four rows by four columns of glyphs, separated by
exactly five neutral-grey horizontal and five neutral-grey vertical rules.
The rules are detected from the pixels; no nominal coordinates or equal-grid
fallback are used.  A failed detection therefore stops the build instead of
silently assigning the wrong character to a cell.

This pipeline is independent from ``sources/authored``.  Its output remains
explicitly unreviewed and is written only below ``build/imagegen``.  Running
it never creates authored metadata or changes either authored manifest.
"""

from __future__ import annotations

import argparse
from array import array
from dataclasses import dataclass
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET

import freetype
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path.parser import parse_path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
DEFAULT_DESCRIPTOR = IMAGEGEN_ROOT / "batches/pilot-common-0001.source.json"
DEFAULT_OUTPUT_ROOT = ROOT / "build/imagegen"

ROWS = 4
COLUMNS = 4
GRID_LINE_COUNT = 5
UPM = 1024
ADVANCE = 1024
FONT_X_MIN = 32
FONT_X_MAX = 992
FONT_Y_MIN = -40
FONT_Y_MAX = 920
ASCENDER = 928
DESCENDER = -96
WIN_ASCENT = 960
WIN_DESCENT = 112
REPRODUCIBLE_HEAD_TIMESTAMP = 2_082_844_800

CELL_RASTER_SIZE = 512
TRACE_SUPERSAMPLE = 1
TRACE_GAUSSIAN_RADIUS = 2.20
POTRACE_UNIT = 10
POTRACE_BLACKLEVEL = 0.82
POTRACE_TURDSIZE = 24
POTRACE_ALPHAMAX = 1.10
POTRACE_OPT_TOLERANCE = 0.50
CU2QU_MAX_ERROR = 2.00
MAX_BBOX_EDGE_DELTA = 0.040
MAX_BBOX_CENTER_DELTA = 0.022
MAX_BBOX_EXTENT_DELTA = 0.045
MICRO_THORN_MAX_EDGE = 16.0
MICRO_THORN_MAX_ANGLE = 12.0
MICRO_THORN_MAX_IMPLIED_DISPLACEMENT = 8.0

GRID_MIN_CONTRAST = 6.0
GRID_MIN_COVERAGE = 0.70
GRID_MAX_RULE_WIDTH = 8
GRID_MAX_RULE_MISSING_SCANLINES = 1
# Generated sheets can place the border rules with modest row-height drift.
# The rules themselves must still be independently evidenced, ordered and
# long; these tolerances do not authorize coordinate synthesis.
GRID_SPACING_RELATIVE_TOLERANCE = 0.12
GRID_ORTHOGONAL_RELATIVE_TOLERANCE = 0.06
GRID_MAX_OUTER_MARGIN_RATIO = 0.25
GRID_NEUTRAL_CHROMA = 6

INK_CORE_CEILING = 210
INK_SUPPORT_CEILING = 250
INK_MIN_COMPONENT_AREA = 10
INK_SUPPORT_DILATION = 3
INK_MIN_CELL_FRACTION = 0.0015
INK_MAX_CELL_FRACTION = 0.30

BATCH_ID_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?")
POTRACE_TRANSFORM_PATTERN = re.compile(
    r"translate\(0(?:\.0+)?,(?P<height>[0-9]+(?:\.0+)?)\) "
    r"scale\(0\.1(?:0*)?,-0\.1(?:0*)?\)"
)


class ImagegenPipelineError(RuntimeError):
    """An input or quality contract failed; no approved output may be used."""


@dataclass(frozen=True)
class SourceDescriptor:
    path: Path
    batch_id: str
    state: str
    raster_path: Path
    raster_sha256: str
    characters: tuple[str, ...]
    cell_slots: tuple[str | None, ...]
    empty_grid_cells: int
    review: Mapping[str, str]
    source_sha256: str


@dataclass(frozen=True)
class AxisDetection:
    centers: tuple[int, ...]
    groups: tuple[tuple[int, int], ...]
    profile_ceiling: float
    background_level: float
    center_coverages: tuple[float, ...]


@dataclass(frozen=True)
class GridDetection:
    x: AxisDetection
    y: AxisDetection


@dataclass(frozen=True)
class SegmentedCell:
    character: str
    codepoint: int
    row: int
    column: int
    source_box: tuple[int, int, int, int]
    source_ink_bbox: tuple[float, float, float, float]
    core_component_count: int
    core_pixel_count: int
    cleaned: Image.Image


@dataclass(frozen=True)
class GlyphGeometry:
    character: str
    codepoint: int
    name: str
    glyph: Glyph
    source_ink_bbox: tuple[float, float, float, float]
    font_ink_bbox: tuple[float, float, float, float]
    contour_count: int
    point_count: int
    outer_contour_count: int
    counter_count: int
    minimum_control_edge: float
    micro_edge_count: int
    acute_micro_turn_count: int
    quantization_duplicate_points_removed: int
    maximum_quantization_collapse: float
    micro_thorn_points_removed: int
    maximum_micro_thorn_displacement: float
    coincident_flank_control_points_removed: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _glyph_name(codepoint: int) -> str:
    return (
        f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImagegenPipelineError(f"{path}: cannot read JSON descriptor: {exc}") from exc
    if not isinstance(value, dict):
        raise ImagegenPipelineError(f"{path}: descriptor must be a JSON object")
    return value


def _one_unicode_scalar(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or len(value) != 1:
        raise ImagegenPipelineError(f"{where}: expected exactly one Unicode scalar")
    codepoint = ord(value)
    if 0xD800 <= codepoint <= 0xDFFF:
        raise ImagegenPipelineError(f"{where}: surrogate code points are forbidden")
    category = unicodedata.category(value)
    if category[0] not in {"L", "M", "N", "P", "S"}:
        raise ImagegenPipelineError(
            f"{where}: {value!r} is not a visible Unicode glyph scalar"
        )
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def load_source_descriptor(
    path: Path = DEFAULT_DESCRIPTOR,
    *,
    allowed_raster_root: Path | None = None,
) -> SourceDescriptor:
    """Load and strictly validate one 4×4 generated-source descriptor."""

    path = path.resolve()
    payload = _read_json_object(path)
    if payload.get("schema_version") != 1:
        raise ImagegenPipelineError(f"{path}: schema_version must be 1")

    batch_id = payload.get("batch_id")
    if not isinstance(batch_id, str) or BATCH_ID_PATTERN.fullmatch(batch_id) is None:
        raise ImagegenPipelineError(
            f"{path}: batch_id must be a lowercase ASCII slug"
        )
    state = payload.get("state")
    if state != "generated-unreviewed":
        raise ImagegenPipelineError(
            f"{path}: state must be 'generated-unreviewed', got {state!r}"
        )

    grid = payload.get("grid")
    if not isinstance(grid, dict):
        raise ImagegenPipelineError(f"{path}: grid must be an object")
    if grid.get("rows") != ROWS or grid.get("columns") != COLUMNS:
        raise ImagegenPipelineError(
            f"{path}: only an explicit {ROWS}×{COLUMNS} source grid is accepted"
        )
    raw_characters = grid.get("characters")
    empty_grid_cells = grid.get("empty_grid_cells", 0)
    if (
        not isinstance(empty_grid_cells, int)
        or isinstance(empty_grid_cells, bool)
        or not 0 <= empty_grid_cells < ROWS * COLUMNS
    ):
        raise ImagegenPipelineError(
            f"{path}: grid.empty_grid_cells must be an integer from 0 to 15"
        )
    if (
        not isinstance(raw_characters, list)
        or len(raw_characters) + empty_grid_cells != ROWS * COLUMNS
    ):
        raise ImagegenPipelineError(
            f"{path}: grid.characters plus trailing empty_grid_cells must "
            f"occupy exactly {ROWS * COLUMNS} cells"
        )
    characters = tuple(
        _one_unicode_scalar(value, where=f"{path}: grid.characters[{index}]")
        for index, value in enumerate(raw_characters)
    )
    if len(set(characters)) != len(characters):
        raise ImagegenPipelineError(f"{path}: grid.characters contains duplicates")

    raster = payload.get("raster")
    expected_hash = payload.get("raster_sha256")
    if not isinstance(raster, str) or not raster.endswith(".png"):
        raise ImagegenPipelineError(f"{path}: raster must name a PNG")
    if not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
        raise ImagegenPipelineError(f"{path}: raster_sha256 must be lowercase SHA-256")
    raster_path = (path.parent / raster).resolve()
    allowed_raster_root = (
        (IMAGEGEN_ROOT / "raster")
        if allowed_raster_root is None
        else allowed_raster_root
    ).resolve()
    if not _is_relative_to(raster_path, allowed_raster_root):
        raise ImagegenPipelineError(
            f"{path}: raster must remain below {allowed_raster_root}"
        )
    if not raster_path.is_file():
        raise ImagegenPipelineError(f"{path}: raster does not exist: {raster_path}")
    actual_hash = _sha256(raster_path)
    if actual_hash != expected_hash:
        raise ImagegenPipelineError(
            f"{path}: raster hash mismatch: expected {expected_hash}, got {actual_hash}"
        )

    review = payload.get("review")
    if not isinstance(review, dict) or set(review) != {
        "topology",
        "raster_quality",
        "vector_quality",
    }:
        raise ImagegenPipelineError(
            f"{path}: review must contain topology/raster_quality/vector_quality"
        )
    normalized_review: dict[str, str] = {}
    for key, value in review.items():
        if value != "pending":
            raise ImagegenPipelineError(
                f"{path}: source review {key} must remain pending before this build"
            )
        normalized_review[str(key)] = str(value)

    return SourceDescriptor(
        path=path,
        batch_id=batch_id,
        state=state,
        raster_path=raster_path,
        raster_sha256=expected_hash,
        characters=characters,
        cell_slots=(*characters, *(None for _ in range(empty_grid_cells))),
        empty_grid_cells=empty_grid_cells,
        review=normalized_review,
        source_sha256=_sha256(path),
    )


def _contiguous_groups(
    indices: Iterable[int],
    *,
    max_missing: int = 0,
) -> list[list[int]]:
    groups: list[list[int]] = []
    for index in indices:
        if (
            not groups
            or index > groups[-1][-1] + max_missing + 1
        ):
            groups.append([index])
        else:
            groups[-1].append(index)
    return groups


def _detect_axis_lines(rgb: np.ndarray, *, vertical: bool) -> AxisDetection:
    """Detect exactly five long neutral-grey rules along one image axis."""

    gray = np.asarray(
        Image.fromarray(rgb, mode="RGB").convert("L"), dtype=np.uint8
    )
    chroma = rgb.max(axis=2).astype(np.int16) - rgb.min(axis=2).astype(np.int16)
    reduction_axis = 0 if vertical else 1
    profile = np.median(gray, axis=reduction_axis)
    background = float(np.quantile(profile, 0.85))
    ceiling = min(250.0, background - GRID_MIN_CONTRAST)
    if ceiling < 180:
        raise ImagegenPipelineError(
            "grid detection failed: implausibly dark sheet background"
        )

    neutral_rule_pixel = (
        (gray >= 96)
        & (gray <= int(math.floor(ceiling)))
        & (chroma <= GRID_NEUTRAL_CHROMA)
    )
    coverage = neutral_rule_pixel.mean(axis=reduction_axis)
    candidate = (profile <= ceiling) & (coverage >= GRID_MIN_COVERAGE)
    groups = _contiguous_groups(
        np.flatnonzero(candidate).tolist(),
        max_missing=GRID_MAX_RULE_MISSING_SCANLINES,
    )
    if len(groups) != GRID_LINE_COUNT:
        direction = "vertical" if vertical else "horizontal"
        raise ImagegenPipelineError(
            f"grid detection failed: expected exactly {GRID_LINE_COUNT} "
            f"{direction} rules, detected {len(groups)}"
        )
    if any(len(group) > GRID_MAX_RULE_WIDTH for group in groups):
        raise ImagegenPipelineError(
            "grid detection failed: a rule is wider than the audited maximum"
        )

    centers: list[int] = []
    center_coverages: list[float] = []
    spans: list[tuple[int, int]] = []
    for group in groups:
        # The darkest profile sample is the actual rule centre.  Coverage is a
        # deterministic tie-breaker, followed by the lower coordinate.
        center = min(group, key=lambda i: (float(profile[i]), -float(coverage[i]), i))
        centers.append(center)
        center_coverages.append(float(coverage[center]))
        spans.append((group[0], group[-1]))

    dimensions = rgb.shape[1] if vertical else rgb.shape[0]
    spacing = np.diff(np.asarray(centers, dtype=np.float64))
    median_spacing = float(np.median(spacing))
    if median_spacing <= 0:
        raise ImagegenPipelineError("grid detection failed: unordered rules")
    maximum_deviation = float(np.max(np.abs(spacing - median_spacing)))
    if maximum_deviation / median_spacing > GRID_SPACING_RELATIVE_TOLERANCE:
        raise ImagegenPipelineError(
            "grid detection failed: rule spacing is not a consistent 4×4 grid"
        )
    if centers[0] / median_spacing > GRID_MAX_OUTER_MARGIN_RATIO:
        raise ImagegenPipelineError(
            "grid detection failed: leading outer margin is implausible"
        )
    if (dimensions - 1 - centers[-1]) / median_spacing > GRID_MAX_OUTER_MARGIN_RATIO:
        raise ImagegenPipelineError(
            "grid detection failed: trailing outer margin is implausible"
        )
    return AxisDetection(
        centers=tuple(centers),
        groups=tuple(spans),
        profile_ceiling=ceiling,
        background_level=background,
        center_coverages=tuple(center_coverages),
    )


def detect_grid(image: Image.Image) -> GridDetection:
    """Return pixel-evidenced grid rules or raise; never synthesize a grid."""

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ImagegenPipelineError("grid detection requires an RGB-compatible image")
    if min(rgb.shape[:2]) < 512:
        raise ImagegenPipelineError("source sheet is too small for reliable tracing")
    x = _detect_axis_lines(rgb, vertical=True)
    y = _detect_axis_lines(rgb, vertical=False)
    x_spacing = float(np.median(np.diff(x.centers)))
    y_spacing = float(np.median(np.diff(y.centers)))
    if abs(x_spacing - y_spacing) / max(x_spacing, y_spacing) > GRID_ORTHOGONAL_RELATIVE_TOLERANCE:
        raise ImagegenPipelineError(
            "grid detection failed: horizontal and vertical cell scales disagree"
        )
    return GridDetection(x=x, y=y)


def _normalized_ink_bbox(mask: np.ndarray) -> tuple[float, float, float, float]:
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        raise ImagegenPipelineError("segmented cell contains no ink")
    height, width = mask.shape
    return (
        float(xs.min()) / width,
        1.0 - float(ys.max() + 1) / height,
        float(xs.max() + 1) / width,
        1.0 - float(ys.min()) / height,
    )


def _clean_cell(
    crop: Image.Image, *, boundary_clearance: int
) -> tuple[Image.Image, tuple[float, float, float, float], int, int]:
    gray = np.asarray(crop.convert("L"), dtype=np.uint8).copy()
    if min(gray.shape) < 128:
        raise ImagegenPipelineError("grid cell is too small for reliable segmentation")
    clear = max(3, boundary_clearance)
    gray[:clear, :] = 255
    gray[-clear:, :] = 255
    gray[:, :clear] = 255
    gray[:, -clear:] = 255

    core = gray <= INK_CORE_CEILING
    labels, label_count = ndimage.label(
        core, structure=np.ones((3, 3), dtype=np.uint8)
    )
    if label_count == 0:
        raise ImagegenPipelineError("segmented cell contains no dark ink core")
    areas = np.bincount(labels.ravel())
    accepted_labels = np.flatnonzero(areas >= INK_MIN_COMPONENT_AREA)
    accepted_labels = accepted_labels[accepted_labels != 0]
    if accepted_labels.size == 0:
        raise ImagegenPipelineError(
            "segmented cell contains only sub-threshold raster speckles"
        )
    kept_core = np.isin(labels, accepted_labels)
    core_pixels = int(kept_core.sum())
    fraction = core_pixels / kept_core.size
    if not INK_MIN_CELL_FRACTION <= fraction <= INK_MAX_CELL_FRACTION:
        raise ImagegenPipelineError(
            f"segmented ink fraction {fraction:.6f} is outside audited limits"
        )

    support = ndimage.binary_dilation(
        kept_core, iterations=INK_SUPPORT_DILATION
    )
    support &= gray <= INK_SUPPORT_CEILING
    cleaned = np.full_like(gray, 255)
    cleaned[support] = gray[support]
    if np.any(cleaned[:clear, :] < 255) or np.any(cleaned[-clear:, :] < 255):
        raise ImagegenPipelineError("top/bottom grid-rule removal was incomplete")
    if np.any(cleaned[:, :clear] < 255) or np.any(cleaned[:, -clear:] < 255):
        raise ImagegenPipelineError("left/right grid-rule removal was incomplete")

    resized = Image.fromarray(cleaned, mode="L").resize(
        (CELL_RASTER_SIZE, CELL_RASTER_SIZE), Image.Resampling.LANCZOS
    )
    resized_array = np.asarray(resized, dtype=np.uint8)
    # Lanczos can introduce a one-level halo around exact white; only retain
    # such antialiasing where it is adjacent to the accepted ink support.
    resized_core = resized_array <= INK_CORE_CEILING
    resized_support = ndimage.binary_dilation(resized_core, iterations=5)
    final_array = np.full_like(resized_array, 255)
    final_array[resized_support] = resized_array[resized_support]
    final = Image.fromarray(final_array, mode="L")
    bbox = _normalized_ink_bbox(final_array <= INK_CORE_CEILING)
    midtones = int(((final_array > 0) & (final_array < 255)).sum())
    if midtones == 0:
        raise ImagegenPipelineError(
            "segmentation destroyed all source antialiasing"
        )
    return final, bbox, int(accepted_labels.size), core_pixels


def segment_cells(
    image: Image.Image,
    detection: GridDetection,
    cell_slots: Sequence[str | None],
) -> tuple[SegmentedCell, ...]:
    if len(cell_slots) != ROWS * COLUMNS:
        raise ImagegenPipelineError("descriptor/cell cardinality mismatch")
    line_half_width = max(
        max(end - start + 1 for start, end in detection.x.groups),
        max(end - start + 1 for start, end in detection.y.groups),
    )
    clearance = line_half_width + 3
    cells: list[SegmentedCell] = []
    for row in range(ROWS):
        y0, y1 = detection.y.centers[row : row + 2]
        for column in range(COLUMNS):
            x0, x1 = detection.x.centers[column : column + 2]
            if x1 - x0 < 128 or y1 - y0 < 128:
                raise ImagegenPipelineError("detected cell has implausible dimensions")
            crop = image.crop((x0, y0, x1, y1))
            character = cell_slots[row * COLUMNS + column]
            if character is None:
                blank = np.asarray(crop.convert("L"), dtype=np.uint8).copy()
                blank[:clearance, :] = 255
                blank[-clearance:, :] = 255
                blank[:, :clearance] = 255
                blank[:, -clearance:] = 255
                labels, count = ndimage.label(
                    blank <= INK_CORE_CEILING,
                    structure=np.ones((3, 3), dtype=np.uint8),
                )
                areas = np.bincount(labels.ravel()) if count else np.asarray([0])
                if count and np.any(areas[1:] >= INK_MIN_COMPONENT_AREA):
                    raise ImagegenPipelineError(
                        f"declared empty cell at row {row}, column {column} "
                        "contains a visible ink component"
                    )
                continue
            cleaned, bbox, component_count, core_pixels = _clean_cell(
                crop, boundary_clearance=clearance
            )
            cells.append(
                SegmentedCell(
                    character=character,
                    codepoint=ord(character),
                    row=row,
                    column=column,
                    source_box=(x0, y0, x1, y1),
                    source_ink_bbox=bbox,
                    core_component_count=component_count,
                    core_pixel_count=core_pixels,
                    cleaned=cleaned,
                )
            )
    return tuple(cells)


def _potrace_version(potrace: Path) -> str:
    try:
        result = subprocess.run(
            [str(potrace), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ImagegenPipelineError(f"cannot execute Potrace: {exc}") from exc
    first_line = result.stdout.splitlines()[0].strip() if result.stdout else ""
    if re.match(r"potrace 1\.[0-9]+(?:[. ]|$)", first_line) is None:
        raise ImagegenPipelineError(
            f"unsupported or unparseable Potrace version: {first_line!r}"
        )
    return first_line


def _resolve_potrace(executable: str | Path | None) -> tuple[Path, str]:
    candidate = str(executable) if executable is not None else shutil.which("potrace")
    if not candidate:
        raise ImagegenPipelineError(
            "Potrace 1.x is required; no unverified vectorizer fallback is allowed"
        )
    path = Path(candidate).resolve()
    if not path.is_file():
        raise ImagegenPipelineError(f"Potrace executable does not exist: {path}")
    return path, _potrace_version(path)


def _trace_cell(
    cell: SegmentedCell,
    *,
    potrace: Path,
    bitmap_path: Path,
    svg_path: Path,
) -> None:
    trace_size = CELL_RASTER_SIZE * TRACE_SUPERSAMPLE
    trace_image = cell.cleaned.resize(
        (trace_size, trace_size), Image.Resampling.LANCZOS
    ).filter(ImageFilter.GaussianBlur(TRACE_GAUSSIAN_RADIUS))
    # PGM is a lossless, directly supported Potrace input.  It remains an
    # internal staging file, while the antialiased source PNG is retained.
    trace_image.save(bitmap_path, format="PPM")
    command = [
        str(potrace),
        str(bitmap_path),
        "--svg",
        "--flat",
        "--unit",
        str(POTRACE_UNIT),
        "--turnpolicy",
        "minority",
        "--turdsize",
        str(POTRACE_TURDSIZE),
        "--alphamax",
        f"{POTRACE_ALPHAMAX:.2f}",
        "--opttolerance",
        f"{POTRACE_OPT_TOLERANCE:.2f}",
        "--blacklevel",
        f"{POTRACE_BLACKLEVEL:.2f}",
        "--output",
        str(svg_path),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ImagegenPipelineError(
            f"U+{cell.codepoint:04X}: Potrace failed: {exc}"
        ) from exc
    if not svg_path.is_file() or svg_path.stat().st_size == 0:
        raise ImagegenPipelineError(
            f"U+{cell.codepoint:04X}: Potrace produced no SVG"
        )


def _svg_path_data(svg_path: Path) -> str:
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ImagegenPipelineError(f"{svg_path}: invalid Potrace SVG: {exc}") from exc
    view_box = root.attrib.get("viewBox", "").split()
    trace_size = CELL_RASTER_SIZE * TRACE_SUPERSAMPLE
    if len(view_box) != 4 or [float(value) for value in view_box] != [
        0.0,
        0.0,
        float(trace_size),
        float(trace_size),
    ]:
        raise ImagegenPipelineError(f"{svg_path}: unexpected Potrace viewBox")
    groups = [
        node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "g"
    ]
    paths = [
        node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "path"
    ]
    if len(groups) != 1 or len(paths) != 1:
        raise ImagegenPipelineError(
            f"{svg_path}: expected exactly one flat Potrace path"
        )
    transform = groups[0].attrib.get("transform", "")
    match = POTRACE_TRANSFORM_PATTERN.fullmatch(transform)
    if match is None or float(match.group("height")) != float(trace_size):
        raise ImagegenPipelineError(
            f"{svg_path}: unexpected Potrace coordinate transform {transform!r}"
        )
    path_data = paths[0].attrib.get("d")
    if not path_data:
        raise ImagegenPipelineError(f"{svg_path}: empty Potrace path")
    return path_data


def _contour_coordinates(glyph: Glyph) -> list[list[tuple[int, int]]]:
    if glyph.numberOfContours <= 0:
        return []
    coordinates = glyph.coordinates
    contours: list[list[tuple[int, int]]] = []
    start = 0
    for end in glyph.endPtsOfContours:
        contours.append(
            [
                (int(coordinates[index][0]), int(coordinates[index][1]))
                for index in range(start, end + 1)
            ]
        )
        start = end + 1
    return contours


def _signed_polygon_area(points: Sequence[tuple[int, int]]) -> float:
    return 0.5 * sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])
    )


def _canonicalize_quantized_on_off_duplicates(
    glyph: Glyph,
    unrounded_coordinates: Sequence[tuple[float, float]],
) -> tuple[int, float]:
    """Remove only geometrically redundant on/off pairs collapsed by rounding.

    Cu2Qu works in floating-point font units, while a TrueType ``glyf`` table
    stores integer coordinates.  Very occasionally an off-curve control point
    and its immediately adjacent on-curve endpoint round to the same integer
    coordinate.  Leaving that zero-length control edge in the font is unsafe:
    downstream rasterizers and outline operations can turn it into a cusp.

    For a mixed on/off pair at one final coordinate, retaining the on-curve
    point preserves the final geometric locus: the degenerate quadratic side
    is the same straight segment as the canonical line.  Equal-type duplicate
    pairs are not generally equivalent, so this function deliberately rejects
    them instead of attempting a broad outline simplification.
    """

    if len(unrounded_coordinates) != len(glyph.coordinates):
        raise ImagegenPipelineError(
            "quadratic quantization audit lost point correspondence"
        )

    contours: list[
        list[tuple[tuple[int, int], int, tuple[float, float]]]
    ] = []
    start = 0
    for end in glyph.endPtsOfContours:
        contour = [
            (
                (
                    int(glyph.coordinates[index][0]),
                    int(glyph.coordinates[index][1]),
                ),
                int(glyph.flags[index]),
                (
                    float(unrounded_coordinates[index][0]),
                    float(unrounded_coordinates[index][1]),
                ),
            )
            for index in range(start, end + 1)
        ]
        contours.append(contour)
        start = end + 1

    removed = 0
    maximum_collapse = 0.0
    for contour_index, contour in enumerate(contours):
        while True:
            duplicate_pair: tuple[int, int] | None = None
            for index, (point, _, _) in enumerate(contour):
                following_index = (index + 1) % len(contour)
                if point == contour[following_index][0]:
                    duplicate_pair = (index, following_index)
                    break
            if duplicate_pair is None:
                break

            first_index, second_index = duplicate_pair
            first = contour[first_index]
            second = contour[second_index]
            first_on_curve = bool(first[1] & 0x01)
            second_on_curve = bool(second[1] & 0x01)
            if first_on_curve == second_on_curve:
                raise ImagegenPipelineError(
                    f"contour {contour_index} contains a non-canonicalizable "
                    "same-type duplicate pair"
                )
            if len(contour) <= 4:
                raise ImagegenPipelineError(
                    f"contour {contour_index} would become underspecified while "
                    "canonicalizing a quantized duplicate"
                )

            # Keep the on-curve endpoint and remove only the coincident
            # off-curve control point.
            remove_index = second_index if first_on_curve else first_index
            raw_separation = math.dist(first[2], second[2])
            # Two coordinates that independently round to the same integer can
            # differ by at most sqrt(2) font units.  Enforce that provenance
            # explicitly so this never becomes a general-purpose simplifier.
            if raw_separation > math.sqrt(2.0) + 1e-9:
                raise ImagegenPipelineError(
                    f"contour {contour_index} duplicate pair did not arise from "
                    "integer quantization"
                )
            maximum_collapse = max(maximum_collapse, raw_separation)
            contour.pop(remove_index)
            removed += 1

    if not removed:
        return 0, 0.0

    coordinates: list[tuple[int, int]] = []
    flags: list[int] = []
    end_points: list[int] = []
    for contour in contours:
        coordinates.extend(point for point, _, _ in contour)
        flags.extend(flag for _, flag, _ in contour)
        end_points.append(len(coordinates) - 1)
    glyph.coordinates = GlyphCoordinates(coordinates)
    glyph.flags = array("B", flags)
    glyph.endPtsOfContours = end_points
    return removed, maximum_collapse


def _remove_acute_implied_point_thorns(
    glyph: Glyph,
) -> tuple[int, float, int]:
    """Replace tiny on-curve cusps between off-curves with an implied point.

    A Potrace cubic converted to TrueType quadratics can contain a very small
    reversal at a rounded extremum.  In a TrueType contour, removing an
    on-curve point between two off-curve controls replaces it with their
    well-defined implied midpoint.  We perform that operation only for the
    exact micro-thorn signature already rejected by ``_geometry_quality`` and
    only when the displacement to the implied midpoint is tightly bounded.
    """

    contours: list[list[tuple[tuple[int, int], int]]] = []
    start = 0
    for end in glyph.endPtsOfContours:
        contours.append(
            [
                (
                    (
                        int(glyph.coordinates[index][0]),
                        int(glyph.coordinates[index][1]),
                    ),
                    int(glyph.flags[index]),
                )
                for index in range(start, end + 1)
            ]
        )
        start = end + 1

    removed = 0
    maximum_displacement = 0.0
    coincident_flank_controls_removed = 0
    for contour_index, contour in enumerate(contours):
        while True:
            thorn_index: int | None = None
            thorn_displacement = 0.0
            coincident_flanks = False
            for index, (point, flag) in enumerate(contour):
                if not flag & 0x01:
                    continue
                previous_index = index - 1
                following_index = (index + 1) % len(contour)
                previous, previous_flag = contour[previous_index]
                following, following_flag = contour[following_index]
                incoming_length = math.dist(previous, point)
                outgoing_length = math.dist(point, following)
                if incoming_length == 0 or outgoing_length == 0:
                    continue
                v1 = (previous[0] - point[0], previous[1] - point[1])
                v2 = (following[0] - point[0], following[1] - point[1])
                cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (
                    incoming_length * outgoing_length
                )
                angle = math.degrees(
                    math.acos(max(-1.0, min(1.0, cosine)))
                )
                if not (
                    incoming_length < MICRO_THORN_MAX_EDGE
                    and outgoing_length < MICRO_THORN_MAX_EDGE
                    and angle < MICRO_THORN_MAX_ANGLE
                ):
                    continue
                if previous_flag & 0x01 or following_flag & 0x01:
                    raise ImagegenPipelineError(
                        f"contour {contour_index} contains an acute micro-thorn "
                        "that cannot be replaced by a TrueType implied point"
                    )
                implied = (
                    (previous[0] + following[0]) / 2,
                    (previous[1] + following[1]) / 2,
                )
                displacement = math.dist(point, implied)
                if displacement > MICRO_THORN_MAX_IMPLIED_DISPLACEMENT:
                    raise ImagegenPipelineError(
                        f"contour {contour_index} acute turn exceeds the bounded "
                        "micro-thorn repair displacement"
                    )
                if len(contour) <= 4:
                    raise ImagegenPipelineError(
                        f"contour {contour_index} would become underspecified "
                        "while removing an acute micro-thorn"
                    )
                if previous == following and len(contour) <= 5:
                    raise ImagegenPipelineError(
                        f"contour {contour_index} would become underspecified "
                        "while collapsing a coincident-flank micro-thorn"
                    )
                thorn_index = index
                thorn_displacement = displacement
                coincident_flanks = previous == following
                break
            if thorn_index is None:
                break
            contour.pop(thorn_index)
            if coincident_flanks:
                # The rejected shape was an out-and-back spike
                # ``off A -> on P -> off A``.  Once P is removed the two
                # identical off-curves would form a zero-length control edge.
                # Retaining one A produces the single smooth quadratic that
                # the one-unit excursion was approximating.
                contour.pop(thorn_index % len(contour))
                coincident_flank_controls_removed += 1
            removed += 1
            maximum_displacement = max(
                maximum_displacement, thorn_displacement
            )

    if not removed:
        return 0, 0.0, 0

    coordinates: list[tuple[int, int]] = []
    flags: list[int] = []
    end_points: list[int] = []
    for contour in contours:
        coordinates.extend(point for point, _ in contour)
        flags.extend(flag for _, flag in contour)
        end_points.append(len(coordinates) - 1)
    glyph.coordinates = GlyphCoordinates(coordinates)
    glyph.flags = array("B", flags)
    glyph.endPtsOfContours = end_points
    return (
        removed,
        maximum_displacement,
        coincident_flank_controls_removed,
    )


def _geometry_quality(
    glyph: Glyph,
) -> tuple[int, int, int, int, float, int, int]:
    contours = _contour_coordinates(glyph)
    if not contours:
        raise ImagegenPipelineError("quadratic conversion produced no contours")
    areas = [_signed_polygon_area(contour) for contour in contours]
    if any(area == 0 for area in areas):
        raise ImagegenPipelineError("quadratic conversion produced a zero-area contour")
    outer_count = sum(area < 0 for area in areas)
    counter_count = sum(area > 0 for area in areas)
    if outer_count == 0:
        raise ImagegenPipelineError(
            "contour winding is inverted: no clockwise outer contour"
        )
    largest = max(range(len(areas)), key=lambda index: abs(areas[index]))
    if areas[largest] >= 0:
        raise ImagegenPipelineError(
            "largest contour is not a clockwise TrueType outer contour"
        )
    largest_outer_area = max(abs(area) for area in areas if area < 0)
    if any(area >= largest_outer_area for area in areas if area > 0):
        raise ImagegenPipelineError("counter winding/containment is implausible")

    minimum_edge = math.inf
    micro_edges = 0
    acute_micro_turns = 0
    for contour_index, contour in enumerate(contours):
        if len(contour) < 4:
            raise ImagegenPipelineError(
                f"contour {contour_index} contains fewer than four control points"
            )
        for index, point in enumerate(contour):
            previous = contour[index - 1]
            following = contour[(index + 1) % len(contour)]
            incoming_length = math.dist(previous, point)
            outgoing_length = math.dist(point, following)
            if incoming_length == 0 or outgoing_length == 0:
                raise ImagegenPipelineError(
                    f"contour {contour_index} contains duplicate adjacent points"
                )
            minimum_edge = min(minimum_edge, incoming_length)
            if incoming_length < 1.0:
                micro_edges += 1
            # Only test on-curve vertices.  A very short two-sided cusp is a
            # characteristic vectorization thorn, not a legitimate pen tip.
            point_offset = sum(len(value) for value in contours[:contour_index]) + index
            if glyph.flags[point_offset] & 0x01:
                v1 = (previous[0] - point[0], previous[1] - point[1])
                v2 = (following[0] - point[0], following[1] - point[1])
                cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (
                    incoming_length * outgoing_length
                )
                angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
                if (
                    incoming_length < MICRO_THORN_MAX_EDGE
                    and outgoing_length < MICRO_THORN_MAX_EDGE
                    and angle < MICRO_THORN_MAX_ANGLE
                ):
                    acute_micro_turns += 1
    if micro_edges:
        raise ImagegenPipelineError(
            f"quadratic outline contains {micro_edges} sub-1-unit control edges"
        )
    if acute_micro_turns:
        raise ImagegenPipelineError(
            f"quadratic outline contains {acute_micro_turns} acute micro-thorns"
        )
    return (
        len(contours),
        sum(len(contour) for contour in contours),
        outer_count,
        counter_count,
        minimum_edge,
        micro_edges,
        acute_micro_turns,
    )


def _glyph_bbox(glyph: Glyph) -> tuple[int, int, int, int]:
    """Return the integer TrueType control-point bounds."""

    coordinates = glyph.coordinates
    if not coordinates:
        raise ImagegenPipelineError("glyph has no coordinates")
    xs = [int(point[0]) for point in coordinates]
    ys = [int(point[1]) for point in coordinates]
    return min(xs), min(ys), max(xs), max(ys)


def _glyph_outline_bbox(glyph: Glyph) -> tuple[float, float, float, float]:
    """Return exact visible quadratic bounds, excluding control overshoot."""

    pen = BoundsPen(None)
    try:
        glyph.draw(pen, None)
    except Exception as exc:
        raise ImagegenPipelineError(
            f"cannot compute exact quadratic outline bounds: {exc}"
        ) from exc
    if pen.bounds is None:
        raise ImagegenPipelineError("quadratic outline has no geometric bounds")
    return tuple(float(value) for value in pen.bounds)


def _normalized_font_bbox(glyph: Glyph) -> tuple[float, float, float, float]:
    x_min, y_min, x_max, y_max = _glyph_outline_bbox(glyph)
    return (
        (x_min - FONT_X_MIN) / (FONT_X_MAX - FONT_X_MIN),
        (y_min - FONT_Y_MIN) / (FONT_Y_MAX - FONT_Y_MIN),
        (x_max - FONT_X_MIN) / (FONT_X_MAX - FONT_X_MIN),
        (y_max - FONT_Y_MIN) / (FONT_Y_MAX - FONT_Y_MIN),
    )


def _svg_to_quadratic(
    cell: SegmentedCell,
    svg_path: Path,
) -> GlyphGeometry:
    path_data = _svg_path_data(svg_path)
    trace_extent = CELL_RASTER_SIZE * TRACE_SUPERSAMPLE * POTRACE_UNIT
    scale_x = (FONT_X_MAX - FONT_X_MIN) / trace_extent
    scale_y = (FONT_Y_MAX - FONT_Y_MIN) / trace_extent
    tt_pen = TTGlyphPen(None)
    cubic_to_quadratic = Cu2QuPen(
        tt_pen,
        CU2QU_MAX_ERROR,
        reverse_direction=True,
        all_quadratic=True,
    )
    transformed = TransformPen(
        cubic_to_quadratic,
        (scale_x, 0.0, 0.0, scale_y, FONT_X_MIN, FONT_Y_MIN),
    )
    try:
        # Potrace path coordinates are y-up before the SVG group's presentation
        # transform.  Parsing the path data directly therefore maps cleanly to
        # TrueType Cartesian coordinates while preserving cell placement.
        parse_path(path_data, transformed)
    except Exception as exc:
        raise ImagegenPipelineError(
            f"U+{cell.codepoint:04X}: SVG to quadratic conversion failed: {exc}"
        ) from exc
    unrounded_coordinates = tuple(
        (float(point[0]), float(point[1])) for point in tt_pen.points
    )
    glyph = tt_pen.glyph()
    (
        quantization_duplicate_points_removed,
        maximum_quantization_collapse,
    ) = _canonicalize_quantized_on_off_duplicates(
        glyph, unrounded_coordinates
    )
    (
        micro_thorn_points_removed,
        maximum_micro_thorn_displacement,
        coincident_flank_control_points_removed,
    ) = _remove_acute_implied_point_thorns(glyph)
    (
        contour_count,
        point_count,
        outer_count,
        counter_count,
        minimum_edge,
        micro_edges,
        acute_micro_turns,
    ) = _geometry_quality(glyph)
    font_bbox = _normalized_font_bbox(glyph)
    maximum_bbox_delta = max(
        abs(source - rendered)
        for source, rendered in zip(cell.source_ink_bbox, font_bbox)
    )
    source_center = (
        (cell.source_ink_bbox[0] + cell.source_ink_bbox[2]) / 2,
        (cell.source_ink_bbox[1] + cell.source_ink_bbox[3]) / 2,
    )
    font_center = (
        (font_bbox[0] + font_bbox[2]) / 2,
        (font_bbox[1] + font_bbox[3]) / 2,
    )
    center_delta = max(
        abs(source - rendered)
        for source, rendered in zip(source_center, font_center)
    )
    source_extent = (
        cell.source_ink_bbox[2] - cell.source_ink_bbox[0],
        cell.source_ink_bbox[3] - cell.source_ink_bbox[1],
    )
    font_extent = (
        font_bbox[2] - font_bbox[0],
        font_bbox[3] - font_bbox[1],
    )
    extent_delta = max(
        abs(source - rendered)
        for source, rendered in zip(source_extent, font_extent)
    )
    if (
        maximum_bbox_delta > MAX_BBOX_EDGE_DELTA
        or center_delta > MAX_BBOX_CENTER_DELTA
        or extent_delta > MAX_BBOX_EXTENT_DELTA
    ):
        raise ImagegenPipelineError(
            f"U+{cell.codepoint:04X}: vectorization moved/rescaled the cell ink "
            f"(edge={maximum_bbox_delta:.4f}, center={center_delta:.4f}, "
            f"extent={extent_delta:.4f}) beyond the audited contract"
        )
    x_min, y_min, x_max, y_max = _glyph_bbox(glyph)
    if x_min < 0 or x_max > ADVANCE:
        raise ImagegenPipelineError(
            f"U+{cell.codepoint:04X}: horizontal outline clips its full-width advance"
        )
    if y_min < DESCENDER or y_max > ASCENDER:
        raise ImagegenPipelineError(
            f"U+{cell.codepoint:04X}: vertical outline clips font metrics"
        )
    return GlyphGeometry(
        character=cell.character,
        codepoint=cell.codepoint,
        name=_glyph_name(cell.codepoint),
        glyph=glyph,
        source_ink_bbox=cell.source_ink_bbox,
        font_ink_bbox=font_bbox,
        contour_count=contour_count,
        point_count=point_count,
        outer_contour_count=outer_count,
        counter_count=counter_count,
        minimum_control_edge=minimum_edge,
        micro_edge_count=micro_edges,
        acute_micro_turn_count=acute_micro_turns,
        quantization_duplicate_points_removed=(
            quantization_duplicate_points_removed
        ),
        maximum_quantization_collapse=maximum_quantization_collapse,
        micro_thorn_points_removed=micro_thorn_points_removed,
        maximum_micro_thorn_displacement=(
            maximum_micro_thorn_displacement
        ),
        coincident_flank_control_points_removed=(
            coincident_flank_control_points_removed
        ),
    )


def _notdef_glyph() -> Glyph:
    pen = TTGlyphPen(None)
    pen.moveTo((96, 0))
    pen.lineTo((928, 0))
    pen.lineTo((928, 896))
    pen.lineTo((96, 896))
    pen.closePath()
    pen.moveTo((176, 80))
    pen.lineTo((176, 816))
    pen.lineTo((848, 816))
    pen.lineTo((848, 80))
    pen.closePath()
    return pen.glyph()


def _font_builder(
    glyphs: Sequence[GlyphGeometry],
    *,
    family: str,
    ps_name: str,
) -> FontBuilder:
    glyph_order = [".notdef", *(glyph.name for glyph in glyphs)]
    outlines = {".notdef": _notdef_glyph()}
    outlines.update({glyph.name: glyph.glyph for glyph in glyphs})
    cmap = {glyph.codepoint: glyph.name for glyph in glyphs}
    metrics = {".notdef": (ADVANCE, 96)}
    for glyph in glyphs:
        x_min, _, _, _ = _glyph_bbox(glyph.glyph)
        metrics[glyph.name] = (ADVANCE, x_min)

    builder = FontBuilder(UPM, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(outlines)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ASCENDER, descent=DESCENDER, lineGap=0)
    builder.setupNameTable(
        {
            "familyName": family,
            "styleName": "Regular",
            "uniqueFontIdentifier": f"{family} 0.1 unreviewed",
            "fullName": f"{family} Regular",
            "psName": ps_name,
            "version": "Version 0.1",
            "copyright": "Copyright 2026 The CodexFont Project Authors",
            "licenseDescription": (
                "This unreviewed pilot Font Software is licensed under the "
                "SIL Open Font License, Version 1.1."
            ),
            "licenseInfoURL": "https://openfontlicense.org",
        }
    )
    builder.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=0,
        usWinAscent=WIN_ASCENT,
        usWinDescent=WIN_DESCENT,
        achVendID="CDFT",
        fsType=0,
    )
    builder.setupPost(keepGlyphNames=True)
    builder.setupMaxp()
    builder.font["head"].created = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font["head"].modified = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font.recalcTimestamp = False
    return builder


def _font_family_and_ps(
    batch_id: str,
    *,
    family_name_prefix: str = "Clear Hand TC",
    postscript_name_prefix: str = "ClearHandTC",
) -> tuple[str, str]:
    suffix = " ".join(part.title() for part in batch_id.split("-"))
    family = f"{family_name_prefix} {suffix} Unreviewed"
    ps_suffix = "".join(part.title() for part in batch_id.split("-"))
    return family, f"{postscript_name_prefix}-{ps_suffix}-Unreviewed"


def _build_fonts(
    glyphs: Sequence[GlyphGeometry],
    *,
    batch_id: str,
    font_directory: Path,
    family_name_prefix: str = "Clear Hand TC",
    postscript_name_prefix: str = "ClearHandTC",
) -> tuple[Path, Path]:
    font_directory.mkdir(parents=True, exist_ok=True)
    family, ps_name = _font_family_and_ps(
        batch_id,
        family_name_prefix=family_name_prefix,
        postscript_name_prefix=postscript_name_prefix,
    )
    basename = ps_name
    ttf_path = font_directory / f"{basename}.ttf"
    otf_path = font_directory / f"{basename}.otf"
    _font_builder(glyphs, family=family, ps_name=ps_name).save(ttf_path)
    # OpenType permits a quadratic ``glyf`` outline flavor.  Build a second
    # deterministic sfnt rather than copying bytes, and keep the report
    # explicit about the outline technology.
    _font_builder(glyphs, family=family, ps_name=ps_name).save(otf_path)
    return ttf_path, otf_path


def _load_rendered_glyph(
    face: freetype.Face, character: str, size: int
) -> tuple[np.ndarray, int, int, int]:
    face.set_pixel_sizes(0, size)
    flags = (
        freetype.FT_LOAD_RENDER
        | freetype.FT_LOAD_NO_HINTING
        | freetype.FT_LOAD_TARGET_NORMAL
    )
    face.load_char(character, flags)
    slot = face.glyph
    bitmap = slot.bitmap
    if bitmap.width <= 0 or bitmap.rows <= 0:
        raise ImagegenPipelineError(
            f"U+{ord(character):04X} is empty at {size}px"
        )
    buffer = np.asarray(bitmap.buffer, dtype=np.uint8)
    if bitmap.pitch < bitmap.width or buffer.size < bitmap.pitch * bitmap.rows:
        raise ImagegenPipelineError("unexpected FreeType bitmap layout")
    alpha = buffer.reshape(bitmap.rows, bitmap.pitch)[:, : bitmap.width].copy()
    if int(alpha.max()) == 0:
        raise ImagegenPipelineError(
            f"U+{ord(character):04X} rasterizes to zero coverage at {size}px"
        )
    return alpha, int(slot.bitmap_left), int(slot.bitmap_top), int(slot.advance.x // 64)


def _paste_render(
    canvas: np.ndarray,
    alpha: np.ndarray,
    *,
    left: int,
    top: int,
    foreground: int,
) -> None:
    height, width = alpha.shape
    canvas_height, canvas_width = canvas.shape
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(canvas_width, left + width), min(canvas_height, top + height)
    if x0 >= x1 or y0 >= y1:
        raise ImagegenPipelineError("proof glyph is wholly outside its panel")
    source = alpha[y0 - top : y1 - top, x0 - left : x1 - left]
    destination = canvas[y0:y1, x0:x1]
    if foreground == 0:
        destination[:] = np.minimum(destination, 255 - source)
    else:
        destination[:] = np.maximum(destination, source)


def _small_size_raster_qa(
    font_path: Path, characters: Sequence[str]
) -> dict[str, dict[str, int]]:
    face = freetype.Face(str(font_path))
    results: dict[str, dict[str, int]] = {}
    for character in characters:
        per_size: dict[str, int] = {}
        for size in (12, 16, 20, 32, 56):
            alpha, _, _, advance = _load_rendered_glyph(face, character, size)
            if advance <= 0:
                raise ImagegenPipelineError(
                    f"U+{ord(character):04X}: non-positive FreeType advance"
                )
            coverage = int(np.count_nonzero(alpha))
            if coverage < max(2, size // 6):
                raise ImagegenPipelineError(
                    f"U+{ord(character):04X}: insufficient coverage at {size}px"
                )
            per_size[str(size)] = coverage
        results[f"U+{ord(character):04X}"] = per_size
    return results


def _proof_panel(
    face: freetype.Face,
    character: str,
    *,
    foreground: int,
    background: int,
) -> Image.Image:
    width, height = 210, 164
    canvas = np.full((height, width), background, dtype=np.uint8)
    for size, center_x, baseline in ((64, 68, 84), (32, 145, 70), (18, 170, 126)):
        alpha, bitmap_left, bitmap_top, advance = _load_rendered_glyph(
            face, character, size
        )
        origin_x = int(round(center_x - advance / 2))
        _paste_render(
            canvas,
            alpha,
            left=origin_x + bitmap_left,
            top=baseline - bitmap_top,
            foreground=foreground,
        )
    image = Image.fromarray(canvas, mode="L")
    draw = ImageDraw.Draw(image)
    label_color = 45 if foreground == 0 else 210
    draw.text((8, 142), f"U+{ord(character):04X}", fill=label_color)
    return image


def _write_proofs(
    font_path: Path,
    cells: Sequence[SegmentedCell],
    *,
    proof_directory: Path,
    png_directory: Path,
) -> tuple[Path, Path, Path]:
    proof_directory.mkdir(parents=True, exist_ok=True)
    face = freetype.Face(str(font_path))
    for cell in cells:
        panel = _proof_panel(
            face, cell.character, foreground=0, background=255
        )
        panel.save(png_directory / f"u{cell.codepoint:04x}-proof.png")

    def contact(foreground: int, background: int, name: str) -> Path:
        panel_width, panel_height = 210, 164
        sheet = Image.new(
            "L", (panel_width * COLUMNS, panel_height * ROWS), color=background
        )
        for cell in cells:
            sheet.paste(
                _proof_panel(
                    face,
                    cell.character,
                    foreground=foreground,
                    background=background,
                ),
                (cell.column * panel_width, cell.row * panel_height),
            )
        output = proof_directory / name
        sheet.save(output)
        return output

    black = contact(0, 255, "small-sizes-black-on-white.png")
    white = contact(255, 0, "small-sizes-white-on-black.png")

    source_panel = 170
    source_sheet = Image.new(
        "L", (source_panel * COLUMNS, source_panel * ROWS), color=255
    )
    for cell in cells:
        thumbnail = cell.cleaned.resize(
            (source_panel, source_panel), Image.Resampling.LANCZOS
        )
        source_sheet.paste(
            thumbnail, (cell.column * source_panel, cell.row * source_panel)
        )
    source_contact = proof_directory / "segmented-source-contact.png"
    source_sheet.save(source_contact)
    return black, white, source_contact


def _validate_built_fonts(
    ttf_path: Path,
    otf_path: Path,
    glyphs: Sequence[GlyphGeometry],
) -> None:
    expected_cmap = {glyph.codepoint: glyph.name for glyph in glyphs}
    for font_path in (ttf_path, otf_path):
        try:
            font = TTFont(font_path, recalcTimestamp=False)
        except Exception as exc:
            raise ImagegenPipelineError(f"{font_path}: cannot reopen font: {exc}") from exc
        if "glyf" not in font or "CFF " in font or "CFF2" in font:
            raise ImagegenPipelineError(
                f"{font_path}: output is not a quadratic glyf OpenType font"
            )
        cmap = font.getBestCmap()
        if cmap != expected_cmap:
            raise ImagegenPipelineError(
                f"{font_path}: cmap does not exactly match the descriptor"
            )
        if font.getGlyphOrder() != [".notdef", *(glyph.name for glyph in glyphs)]:
            raise ImagegenPipelineError(f"{font_path}: glyph order is not deterministic")
        for glyph in glyphs:
            outline = font["glyf"][glyph.name]
            if outline.isComposite() or outline.numberOfContours <= 0:
                raise ImagegenPipelineError(
                    f"{font_path}: {glyph.name} is empty or composite"
                )
            if font["hmtx"].metrics[glyph.name][0] != ADVANCE:
                raise ImagegenPipelineError(
                    f"{font_path}: {glyph.name} is not full-width"
                )
        font.close()


def _relative_artifact_hashes(stage: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(stage.rglob("*")):
        if path.is_file() and path.name != "report.json" and not path.name.endswith(".pgm"):
            hashes[path.relative_to(stage).as_posix()] = _sha256(path)
    return hashes


def _round_bbox(values: Sequence[float]) -> list[float]:
    return [round(float(value), 6) for value in values]


def build_batch(
    descriptor_path: Path = DEFAULT_DESCRIPTOR,
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    potrace_executable: str | Path | None = None,
    allowed_raster_root: Path | None = None,
    family_name_prefix: str = "Clear Hand TC",
    postscript_name_prefix: str = "ClearHandTC",
) -> Path:
    """Build one unreviewed imagegen batch and return its final directory."""

    descriptor = load_source_descriptor(
        descriptor_path,
        allowed_raster_root=allowed_raster_root,
    )
    potrace, potrace_version = _resolve_potrace(potrace_executable)
    try:
        source_image = Image.open(descriptor.raster_path)
        source_image.load()
    except (OSError, ValueError) as exc:
        raise ImagegenPipelineError(
            f"{descriptor.raster_path}: cannot decode source PNG: {exc}"
        ) from exc
    if source_image.format != "PNG":
        raise ImagegenPipelineError(
            f"{descriptor.raster_path}: decoded format is not PNG"
        )

    detection = detect_grid(source_image)
    cells = segment_cells(source_image, detection, descriptor.cell_slots)
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{descriptor.batch_id}-", dir=output_root)
    )
    final_directory = output_root / descriptor.batch_id
    try:
        png_directory = stage / "png"
        svg_directory = stage / "svg"
        bitmap_directory = stage / ".trace"
        font_directory = stage / "font"
        proof_directory = stage / "proof"
        glyph_report_directory = stage / "glyph-report"
        for directory in (
            png_directory,
            svg_directory,
            bitmap_directory,
            glyph_report_directory,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        geometries: list[GlyphGeometry] = []
        glyph_records: list[dict[str, Any]] = []
        for cell in cells:
            stem = f"u{cell.codepoint:04x}"
            png_path = png_directory / f"{stem}-source.png"
            bitmap_path = bitmap_directory / f"{stem}.pgm"
            svg_path = svg_directory / f"{stem}.svg"
            cell.cleaned.save(png_path)
            _trace_cell(
                cell,
                potrace=potrace,
                bitmap_path=bitmap_path,
                svg_path=svg_path,
            )
            geometry = _svg_to_quadratic(cell, svg_path)
            geometries.append(geometry)
            record = {
                "character": cell.character,
                "codepoint": f"U+{cell.codepoint:04X}",
                "glyph_name": geometry.name,
                "row": cell.row,
                "column": cell.column,
                "source_box": list(cell.source_box),
                "source_ink_bbox_normalized": _round_bbox(
                    geometry.source_ink_bbox
                ),
                "font_ink_bbox_normalized": _round_bbox(geometry.font_ink_bbox),
                "maximum_position_delta": round(
                    max(
                        abs(a - b)
                        for a, b in zip(
                            geometry.source_ink_bbox, geometry.font_ink_bbox
                        )
                    ),
                    6,
                ),
                "source_core_component_count": cell.core_component_count,
                "source_core_pixel_count": cell.core_pixel_count,
                "contour_count": geometry.contour_count,
                "point_count": geometry.point_count,
                "outer_contour_count": geometry.outer_contour_count,
                "counter_count": geometry.counter_count,
                "minimum_control_edge": round(
                    geometry.minimum_control_edge, 6
                ),
                "micro_edge_count": geometry.micro_edge_count,
                "acute_micro_turn_count": geometry.acute_micro_turn_count,
                "quantization_duplicate_points_removed": (
                    geometry.quantization_duplicate_points_removed
                ),
                "maximum_quantization_collapse": round(
                    geometry.maximum_quantization_collapse, 6
                ),
                "micro_thorn_points_removed": (
                    geometry.micro_thorn_points_removed
                ),
                "maximum_micro_thorn_displacement": round(
                    geometry.maximum_micro_thorn_displacement, 6
                ),
                "coincident_flank_control_points_removed": (
                    geometry.coincident_flank_control_points_removed
                ),
                "source_png": f"png/{stem}-source.png",
                "svg": f"svg/{stem}.svg",
                "proof_png": f"png/{stem}-proof.png",
                "source_png_sha256": _sha256(png_path),
                "svg_sha256": _sha256(svg_path),
            }
            glyph_records.append(record)
            (glyph_report_directory / f"{stem}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        ttf_path, otf_path = _build_fonts(
            geometries,
            batch_id=descriptor.batch_id,
            font_directory=font_directory,
            family_name_prefix=family_name_prefix,
            postscript_name_prefix=postscript_name_prefix,
        )
        _validate_built_fonts(ttf_path, otf_path, geometries)
        raster_qa = _small_size_raster_qa(ttf_path, descriptor.characters)
        black_proof, white_proof, source_proof = _write_proofs(
            ttf_path,
            cells,
            proof_directory=proof_directory,
            png_directory=png_directory,
        )
        # Proof PNG hashes are added only after the proof files exist.
        for record in glyph_records:
            record["proof_png_sha256"] = _sha256(stage / record["proof_png"])
            (glyph_report_directory / f"u{ord(record['character']):04x}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        shutil.rmtree(bitmap_directory)
        report = {
            "schema_version": 1,
            "pipeline": "imagegen-raster-potrace-quadratic-v2",
            "approval_state": "unreviewed",
            "batch_id": descriptor.batch_id,
            "source_descriptor_sha256": descriptor.source_sha256,
            "source_state": descriptor.state,
            "source_review": dict(descriptor.review),
            "source_raster_sha256": descriptor.raster_sha256,
            "characters": list(descriptor.characters),
            "grid": {
                "rows": ROWS,
                "columns": COLUMNS,
                "empty_grid_cells": descriptor.empty_grid_cells,
                "cell_slots": [
                    value if value is not None else None
                    for value in descriptor.cell_slots
                ],
                "x_rule_centers": list(detection.x.centers),
                "y_rule_centers": list(detection.y.centers),
                "x_rule_spans": [list(span) for span in detection.x.groups],
                "y_rule_spans": [list(span) for span in detection.y.groups],
                "x_center_coverages": [
                    round(value, 6) for value in detection.x.center_coverages
                ],
                "y_center_coverages": [
                    round(value, 6) for value in detection.y.center_coverages
                ],
                "synthesized_coordinates": False,
            },
            "segmentation": {
                "antialias_preserved": True,
                "grid_rules_removed": True,
                "cell_raster_size": CELL_RASTER_SIZE,
                "ink_core_ceiling": INK_CORE_CEILING,
                "minimum_component_area": INK_MIN_COMPONENT_AREA,
            },
            "vectorization": {
                "tool": potrace_version,
                "supersample": TRACE_SUPERSAMPLE,
                "gaussian_radius": TRACE_GAUSSIAN_RADIUS,
                "unit": POTRACE_UNIT,
                "turnpolicy": "minority",
                "turdsize": POTRACE_TURDSIZE,
                "alphamax": POTRACE_ALPHAMAX,
                "opttolerance": POTRACE_OPT_TOLERANCE,
                "blacklevel": POTRACE_BLACKLEVEL,
                "cu2qu_max_error": CU2QU_MAX_ERROR,
                "quantized_on_off_duplicate_policy": (
                    "retain-on-curve-reject-same-type"
                ),
                "acute_micro_thorn_policy": (
                    "bounded-implied-midpoint-or-coincident-flank-collapse"
                ),
                "micro_thorn_max_edge": MICRO_THORN_MAX_EDGE,
                "micro_thorn_max_angle": MICRO_THORN_MAX_ANGLE,
                "micro_thorn_max_implied_displacement": (
                    MICRO_THORN_MAX_IMPLIED_DISPLACEMENT
                ),
                "outline_format": "TrueType quadratic glyf",
                "position_audit_bbox": "exact quadratic geometric bounds",
                "format_clip_bbox": "TrueType integer control-point bounds",
                "contour_direction": "clockwise outer, counter-clockwise counter",
            },
            "font": {
                "units_per_em": UPM,
                "advance": ADVANCE,
                "ttf": f"font/{ttf_path.name}",
                "otf": f"font/{otf_path.name}",
                "ttf_sha256": _sha256(ttf_path),
                "otf_sha256": _sha256(otf_path),
                "cmap_count": len(geometries),
            },
            "proofs": {
                "black_on_white": f"proof/{black_proof.name}",
                "white_on_black": f"proof/{white_proof.name}",
                "segmented_source": f"proof/{source_proof.name}",
            },
            "small_size_coverage_pixels": raster_qa,
            "glyphs": glyph_records,
        }
        report["artifact_sha256"] = _relative_artifact_hashes(stage)
        (stage / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if final_directory.exists():
            shutil.rmtree(final_directory)
        stage.replace(final_directory)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return final_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--descriptor",
        type=Path,
        default=DEFAULT_DESCRIPTOR,
        help="strict generated-unreviewed 4×4 source descriptor",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="generated output root; batch_id is appended",
    )
    parser.add_argument(
        "--potrace",
        type=Path,
        help="Potrace 1.x executable (PATH lookup when omitted)",
    )
    parser.add_argument(
        "--allowed-raster-root",
        type=Path,
        help=(
            "explicit raster namespace for a non-default family; omitted "
            "means sources/imagegen/raster"
        ),
    )
    parser.add_argument(
        "--family-name-prefix",
        default="Clear Hand TC",
        help="unreviewed preview family prefix",
    )
    parser.add_argument(
        "--postscript-name-prefix",
        default="ClearHandTC",
        help="unreviewed preview PostScript-name prefix",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = build_batch(
        args.descriptor,
        output_root=args.output_root,
        potrace_executable=args.potrace,
        allowed_raster_root=args.allowed_raster_root,
        family_name_prefix=args.family_name_prefix,
        postscript_name_prefix=args.postscript_name_prefix,
    )
    print(output)
    print(output / "report.json")


if __name__ == "__main__":
    main()
