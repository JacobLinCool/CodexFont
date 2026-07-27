#!/usr/bin/env python3
"""Correct the handedness of Mew Note TC's vertical U+300D glyph.

This is a second, independent post-review correction chained after the
vertical-orientation correction.  It accepts exactly one image-generation
output, composites only the interior of vertical-0002 cell 6, proves the
U+FE42 presentation form is a bottom-left ``└`` corner using binary-ink
geometry, and leaves the batch requiring a new review and release approval.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterator, Mapping, Sequence

from PIL import Image

from scripts.font_family_context import canonical_json_sha256, sha256_path
from scripts import imagegen_font_pipeline
from scripts import mew_note_batch_evidence as evidence
from scripts import (
    mew_note_post_review_vertical_orientation_correction
    as orientation_predecessor
)


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = Path(
    "scripts/mew_note_post_review_vertical_handedness_correction.py"
)
APPROVAL_PATH = Path(
    "families/mew-note-tc/approvals/"
    "original-raster-v1-preview.approval.json"
)
APPROVAL_HISTORY_DIRECTORY = Path(
    "families/mew-note-tc/approvals/history"
)
RECORD_NAME = "post-review-vertical-handedness-correction.json"
RAW_CANDIDATE_NAME = "vertical-handedness-raw-candidate.png"
APPROVAL_FIELD = "post_review_vertical_handedness_correction"
SCHEMA_VERSION = 1
RECORD_TYPE = "mew-note-tc-post-review-vertical-handedness-correction"
REASON = "release-vertical-handedness-rejected"
CONFIRMATION = "I_AUTHORIZE_POST_REVIEW_VERTICAL_HANDEDNESS_CORRECTION"
COLLECTION_ID = "vertical-93"
BATCH_ID = "vertical-0002"
EXPECTED_CANDIDATE_SHA256 = (
    "065cac926d47615a7fbdbd8d4b490f3a82e06a3642ab03fbe1d742822afba249"
)
EXPECTED_CALL_ID = "call_VAas4tDotji4RZSEEodJvbLm"
EXPECTED_PROMPT_SHA256 = (
    "95a1da1f3aac6120e8bbc4f5f563360d25c52c3a71a63d4b52bb5a4661dd7ba2"
)
TARGET: Mapping[str, Any] = {
    "cell": 6,
    "row": 1,
    "column": 1,
    "character": "」",
    "codepoint": "U+300D",
    "vertical_presentation_character": "﹂",
    "vertical_presentation_codepoint": "U+FE42",
    "expected_corner": "└",
    "expected_handedness": (
        "short-vertical-on-left-long-bottom-horizontal-to-right"
    ),
    "report_source_box": [318, 313, 625, 615],
    "replacement_box": [319, 314, 624, 614],
    "expected_core_component_count": 1,
}
PRESERVED_CELL_8: Mapping[str, Any] = {
    "cell": 8,
    "character": "』",
    "codepoint": "U+300F",
    "replacement_box": [931, 314, 1236, 614],
}
COMPOSITE_ALGORITHM = (
    "rgb-png-single-cell-interior-rectangular-replacement-v1"
)
PIXEL_HASH_ALGORITHM = "sha256-framed-rgb-row-major-v1"
BINARY_INK_ALGORITHM = "threshold-128-endpoint-occupancy-v1"
INK_THRESHOLD = 128
MINIMUM_HORIZONTAL_TO_VERTICAL_RATIO = 1.5
MAXIMUM_HORIZONTAL_TO_VERTICAL_RATIO = 3.0
MINIMUM_UPPER_LEFT_INK_PIXELS = 64
MAXIMUM_UPPER_RIGHT_INK_PIXELS = 16
MINIMUM_LOWER_RIGHT_INK_PIXELS = 128
MINIMUM_LEFT_VERTICAL_SPAN_RATIO = 0.65
MAXIMUM_RIGHT_VERTICAL_SPAN_RATIO = 0.40
MINIMUM_BOTTOM_HORIZONTAL_SPAN_RATIO = 0.75


class MewNoteVerticalHandednessCorrectionError(RuntimeError):
    """The handedness correction is incomplete, stale, or unsafe."""


def correction_path(context: evidence.FamilyContext) -> Path:
    return (
        context.batch_paths(COLLECTION_ID, BATCH_ID).source
        / RECORD_NAME
    )


def raw_candidate_path(context: evidence.FamilyContext) -> Path:
    return (
        context.batch_paths(COLLECTION_ID, BATCH_ID).source
        / RAW_CANDIDATE_NAME
    )


def approval_snapshot_path(
    context: evidence.FamilyContext,
    approval_sha256: str,
) -> Path:
    _sha(approval_sha256, label="approval snapshot hash")
    return (
        context.project_root
        / APPROVAL_HISTORY_DIRECTORY
        / f"{approval_sha256}.approval.json"
    )


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise MewNoteVerticalHandednessCorrectionError(
                f"duplicate JSON object key {key!r}"
            )
        value[key] = item
    return value


def _object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except MewNoteVerticalHandednessCorrectionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{path}: {label} must be an object"
        )
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
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


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write(path, _json_bytes(value))


def _atomic_copy(source: Path, destination: Path) -> None:
    source = _regular_file(source, label="copy source")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        with source.open("rb") as incoming:
            shutil.copyfileobj(incoming, stream)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _regular_file(path: Path, *, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label}: missing file {path}"
        ) from exc
    if path.is_symlink() or not resolved.is_file():
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label}: expected a regular non-symlink file: {path}"
        )
    return resolved


def _relative(path: Path, *, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"path escapes repository: {path}"
        ) from exc


def _pin(
    path: Path,
    *,
    project_root: Path,
    retention: str | None = None,
) -> dict[str, str]:
    path = _regular_file(path, label="pinned handedness evidence")
    result = {
        "path": _relative(path, project_root=project_root),
        "sha256": sha256_path(path),
    }
    if retention is not None:
        result["retention"] = retention
    return result


def _historical_pin(
    path: Path,
    sha256: str,
    *,
    project_root: Path,
    retention: str,
) -> dict[str, str]:
    _sha(sha256, label="historical pin hash")
    return {
        "path": _relative(path, project_root=project_root),
        "sha256": sha256,
        "retention": retention,
    }


def _implementation_pin(project_root: Path) -> dict[str, str]:
    return _pin(
        project_root / IMPLEMENTATION_PATH,
        project_root=project_root,
    )


def _sha(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or evidence.SHA256_PATTERN.fullmatch(value) is None
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label} is not a lowercase SHA-256"
        )
    return value


def _exact_keys(
    value: Any,
    expected: set[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label} must be an object"
        )
    actual = set(value)
    if actual != expected:
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label} key drift; "
            f"unknown={sorted(actual - expected)}, "
            f"missing={sorted(expected - actual)}"
        )
    return value


def _load_rgb_png(path: Path, *, label: str) -> Image.Image:
    path = _regular_file(path, label=label)
    try:
        with Image.open(path) as source:
            source.load()
            if (
                source.format != "PNG"
                or source.mode != "RGB"
                or source.size != (1254, 1254)
            ):
                raise MewNoteVerticalHandednessCorrectionError(
                    f"{label} must be a 1254×1254 RGB PNG"
                )
            return source.copy()
    except (OSError, ValueError) as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label} cannot be decoded: {exc}"
        ) from exc


def _framed_pixel_sha256(
    image: Image.Image,
    *,
    regions: Sequence[Sequence[int]],
    include_regions: bool,
) -> str:
    if image.mode != "RGB" or image.size != (1254, 1254):
        raise MewNoteVerticalHandednessCorrectionError(
            "pixel hash image contract changed"
        )
    normalized = tuple(tuple(int(value) for value in box) for box in regions)
    if any(
        len(box) != 4
        or not (0 <= box[0] < box[2] <= image.width)
        or not (0 <= box[1] < box[3] <= image.height)
        for box in normalized
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "pixel hash region is invalid"
        )
    frame = {
        "algorithm": PIXEL_HASH_ALGORITHM,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "regions": [list(box) for box in normalized],
        "selection": "inside" if include_regions else "outside",
    }
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            frame,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            inside = any(
                left <= x < right and top <= y < bottom
                for left, top, right, bottom in normalized
            )
            if inside is include_regions:
                digest.update(bytes(pixels[x, y]))
    return digest.hexdigest()


def _region_sha256(image: Image.Image, box: Sequence[int]) -> str:
    return _framed_pixel_sha256(
        image,
        regions=(box,),
        include_regions=True,
    )


def _save_png(image: Image.Image, path: Path) -> None:
    if image.mode != "RGB" or image.size != (1254, 1254):
        raise MewNoteVerticalHandednessCorrectionError(
            "composite canvas contract changed"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
    try:
        image.save(
            temporary,
            format="PNG",
            optimize=False,
            compress_level=9,
        )
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _compose(
    original_path: Path,
    candidate_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    original = _load_rgb_png(original_path, label="superseded raster")
    candidate = _load_rgb_png(candidate_path, label="raw candidate raster")
    box = tuple(TARGET["replacement_box"])
    outside_before = _framed_pixel_sha256(
        original,
        regions=(box,),
        include_regions=False,
    )
    old_region = _region_sha256(original, box)
    candidate_region = _region_sha256(candidate, box)
    if old_region == candidate_region:
        raise MewNoteVerticalHandednessCorrectionError(
            "U+300D candidate region is unchanged"
        )
    cell_8_before = _region_sha256(
        original, PRESERVED_CELL_8["replacement_box"]
    )
    result = original.copy()
    result.paste(candidate.crop(box), box)
    outside_after = _framed_pixel_sha256(
        result,
        regions=(box,),
        include_regions=False,
    )
    if outside_after != outside_before:
        raise MewNoteVerticalHandednessCorrectionError(
            "composite changed pixels outside vertical-0002 cell 6"
        )
    if (
        _region_sha256(result, box) != candidate_region
        or _region_sha256(
            result, PRESERVED_CELL_8["replacement_box"]
        )
        != cell_8_before
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "single-cell composite provenance drift"
        )
    _save_png(result, output_path)
    installed = _load_rgb_png(
        output_path, label="installed candidate composite"
    )
    if installed.tobytes() != result.tobytes():
        raise MewNoteVerticalHandednessCorrectionError(
            "deterministic PNG serialization changed composite pixels"
        )
    return {
        "algorithm": COMPOSITE_ALGORITHM,
        "pixel_hash_algorithm": PIXEL_HASH_ALGORITHM,
        "canvas": {"width": 1254, "height": 1254, "mode": "RGB"},
        "region": {
            **TARGET,
            "superseded_region_sha256": old_region,
            "candidate_region_sha256": candidate_region,
        },
        "preserved_cell_8": {
            **PRESERVED_CELL_8,
            "region_sha256": cell_8_before,
        },
        "preserved_outside_region_sha256": outside_before,
        "installed_composite_sha256": sha256_path(output_path),
    }


def _component_count(points: set[tuple[int, int]]) -> int:
    remaining = set(points)
    count = 0
    while remaining:
        count += 1
        pending = [remaining.pop()]
        while pending:
            x, y = pending.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (x + dx, y + dy)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        pending.append(neighbor)
    return count


def _binary_handedness(
    image: Image.Image,
    *,
    expect_accepted: bool,
) -> dict[str, Any]:
    if image.mode != "RGB" or image.size != (1254, 1254):
        raise MewNoteVerticalHandednessCorrectionError(
            "binary handedness image contract changed"
        )
    left, top, right, bottom = TARGET["replacement_box"]
    crop = image.crop((left, top, right, bottom)).convert("L")
    points = {
        (x, y)
        for y in range(crop.height)
        for x in range(crop.width)
        if crop.getpixel((x, y)) < INK_THRESHOLD
    }
    if not points:
        raise MewNoteVerticalHandednessCorrectionError(
            "U+300D binary ink is empty"
        )
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    ink_left, ink_top = min(xs), min(ys)
    ink_right, ink_bottom = max(xs), max(ys)
    width = ink_right - ink_left + 1
    height = ink_bottom - ink_top + 1
    quarter = max(1, math.ceil(width / 4))
    half_height = max(1, math.ceil(height / 2))
    left_limit = ink_left + quarter - 1
    right_limit = ink_right - quarter + 1
    upper_limit = ink_top + half_height - 1
    lower_limit = ink_bottom - half_height + 1

    def occupancy(
        x0: int,
        x1: int,
        y0: int,
        y1: int,
    ) -> int:
        return sum(
            1
            for x, y in points
            if x0 <= x <= x1 and y0 <= y <= y1
        )

    upper_left = occupancy(
        ink_left, left_limit, ink_top, upper_limit
    )
    upper_right = occupancy(
        right_limit, ink_right, ink_top, upper_limit
    )
    lower_left = occupancy(
        ink_left, left_limit, lower_limit, ink_bottom
    )
    lower_right = occupancy(
        right_limit, ink_right, lower_limit, ink_bottom
    )
    column_spans = {
        x: sum(1 for point_x, _ in points if point_x == x)
        for x in range(ink_left, ink_right + 1)
    }
    row_spans = {
        y: sum(1 for _, point_y in points if point_y == y)
        for y in range(ink_top, ink_bottom + 1)
    }
    left_vertical_span_ratio = round(
        max(
            column_spans[x]
            for x in range(ink_left, left_limit + 1)
        )
        / height,
        6,
    )
    right_vertical_span_ratio = round(
        max(
            column_spans[x]
            for x in range(right_limit, ink_right + 1)
        )
        / height,
        6,
    )
    bottom_horizontal_span_ratio = round(
        max(
            row_spans[y]
            for y in range(lower_limit, ink_bottom + 1)
        )
        / width,
        6,
    )
    ratio = round(width / height, 6)
    components = _component_count(points)
    gates = {
        "one_connected_component": components == 1,
        "horizontal_ratio_in_range": (
            MINIMUM_HORIZONTAL_TO_VERTICAL_RATIO
            <= ratio
            <= MAXIMUM_HORIZONTAL_TO_VERTICAL_RATIO
        ),
        "upper_left_endpoint_occupied": (
            upper_left >= MINIMUM_UPPER_LEFT_INK_PIXELS
        ),
        "upper_right_endpoint_clear": (
            upper_right <= MAXIMUM_UPPER_RIGHT_INK_PIXELS
        ),
        "lower_right_arm_occupied": (
            lower_right >= MINIMUM_LOWER_RIGHT_INK_PIXELS
        ),
        "left_vertical_arm_present": (
            left_vertical_span_ratio
            >= MINIMUM_LEFT_VERTICAL_SPAN_RATIO
        ),
        "right_vertical_arm_absent": (
            right_vertical_span_ratio
            <= MAXIMUM_RIGHT_VERTICAL_SPAN_RATIO
        ),
        "bottom_horizontal_arm_present": (
            bottom_horizontal_span_ratio
            >= MINIMUM_BOTTOM_HORIZONTAL_SPAN_RATIO
        ),
        "clear_of_cell_interior_edges": (
            ink_left > 0
            and ink_top > 0
            and ink_right < crop.width - 1
            and ink_bottom < crop.height - 1
        ),
    }
    accepted = all(gates.values())
    if accepted is not expect_accepted:
        expected = "accept" if expect_accepted else "reject"
        failed = [key for key, passed in gates.items() if not passed]
        raise MewNoteVerticalHandednessCorrectionError(
            f"U+300D binary handedness does not {expected}; "
            f"failed={failed}"
        )
    return {
        "algorithm": BINARY_INK_ALGORITHM,
        "threshold": INK_THRESHOLD,
        "ink_bbox_in_cell_interior": [
            ink_left,
            ink_top,
            ink_right,
            ink_bottom,
        ],
        "ink_pixel_count": len(points),
        "connected_component_count": components,
        "ink_width": width,
        "ink_height": height,
        "horizontal_to_vertical_ratio": ratio,
        "endpoint_occupancy_pixels": {
            "upper_left": upper_left,
            "upper_right": upper_right,
            "lower_left": lower_left,
            "lower_right": lower_right,
        },
        "left_vertical_span_ratio": left_vertical_span_ratio,
        "right_vertical_span_ratio": right_vertical_span_ratio,
        "bottom_horizontal_span_ratio": bottom_horizontal_span_ratio,
        "gates": gates,
        "decision": "ACCEPT" if accepted else "REJECT",
    }


def _report_ttf(
    report_path: Path,
    report: Mapping[str, Any],
) -> Path:
    font = report.get("font")
    if not isinstance(font, dict) or not isinstance(font.get("ttf"), str):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{report_path}: vector TTF is missing"
        )
    candidate = (report_path.parent / font["ttf"]).resolve()
    try:
        candidate.relative_to(report_path.parent.resolve())
    except ValueError as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"{report_path}: vector TTF path escapes build"
        ) from exc
    candidate = _regular_file(candidate, label="batch vector TTF")
    if sha256_path(candidate) != font.get("ttf_sha256"):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{candidate}: vector TTF hash drift"
        )
    return candidate


def _handedness_diagnostics(
    report_path: Path,
    raster_path: Path,
    *,
    source_sha256: str,
    expect_accepted: bool,
) -> dict[str, Any]:
    report = _object(report_path, label="batch vector report")
    glyphs = report.get("glyphs")
    if (
        report.get("approval_state") != "unreviewed"
        or report.get("source_descriptor_sha256") != source_sha256
        or not isinstance(glyphs, list)
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{report_path}: vector report binding drift"
        )
    _report_ttf(report_path, report)
    matching = [
        glyph
        for glyph in glyphs
        if isinstance(glyph, dict)
        and glyph.get("codepoint") == TARGET["codepoint"]
    ]
    if len(matching) != 1:
        raise MewNoteVerticalHandednessCorrectionError(
            "U+300D vector record is not unique"
        )
    glyph = matching[0]
    bounds = glyph.get("source_ink_bbox_normalized")
    if (
        glyph.get("character") != TARGET["character"]
        or glyph.get("row") != TARGET["row"]
        or glyph.get("column") != TARGET["column"]
        or glyph.get("source_box") != TARGET["report_source_box"]
        or glyph.get("source_core_component_count")
        != TARGET["expected_core_component_count"]
        or glyph.get("contour_count")
        != TARGET["expected_core_component_count"]
        or glyph.get("micro_edge_count") != 0
        or glyph.get("acute_micro_turn_count") != 0
        or not isinstance(bounds, list)
        or len(bounds) != 4
        or any(not isinstance(value, (int, float)) for value in bounds)
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "U+300D vector topology drift"
        )
    width = round(float(bounds[2]) - float(bounds[0]), 6)
    height = round(float(bounds[3]) - float(bounds[1]), 6)
    if width <= 0 or height <= 0:
        raise MewNoteVerticalHandednessCorrectionError(
            "U+300D vector bounds are empty"
        )
    binary = _binary_handedness(
        _load_rgb_png(raster_path, label="handedness raster"),
        expect_accepted=expect_accepted,
    )
    return {
        "source_character": TARGET["character"],
        "source_codepoint": TARGET["codepoint"],
        "vertical_presentation_character": (
            TARGET["vertical_presentation_character"]
        ),
        "vertical_presentation_codepoint": (
            TARGET["vertical_presentation_codepoint"]
        ),
        "expected_corner": TARGET["expected_corner"],
        "expected_handedness": TARGET["expected_handedness"],
        "vector": {
            "source_ink_bbox_normalized": bounds,
            "ink_width": width,
            "ink_height": height,
            "horizontal_to_vertical_ratio": round(width / height, 6),
            "source_core_component_count": (
                glyph["source_core_component_count"]
            ),
            "contour_count": glyph["contour_count"],
            "micro_edge_count": 0,
            "acute_micro_turn_count": 0,
        },
        "binary_ink": binary,
        "decision": binary["decision"],
    }


def _glyph_digest(glyph: Mapping[str, Any]) -> str:
    return canonical_json_sha256(dict(glyph))


def _unchanged_glyph_evidence(
    old_report_path: Path,
    new_report_path: Path,
) -> list[dict[str, str]]:
    old_report = _object(
        old_report_path, label="superseded vector report"
    )
    new_report = _object(
        new_report_path, label="candidate vector report"
    )
    old = {
        glyph["codepoint"]: glyph
        for glyph in old_report.get("glyphs", [])
        if isinstance(glyph, dict)
        and glyph.get("codepoint") != TARGET["codepoint"]
    }
    new = {
        glyph["codepoint"]: glyph
        for glyph in new_report.get("glyphs", [])
        if isinstance(glyph, dict)
        and glyph.get("codepoint") != TARGET["codepoint"]
    }
    if set(old) != set(new) or len(old) != 15:
        raise MewNoteVerticalHandednessCorrectionError(
            "non-target glyph inventory changed"
        )
    records: list[dict[str, str]] = []
    for codepoint in old:
        old_digest = _glyph_digest(old[codepoint])
        new_digest = _glyph_digest(new[codepoint])
        if old_digest != new_digest:
            raise MewNoteVerticalHandednessCorrectionError(
                f"{codepoint}: non-target vector evidence changed"
            )
        records.append(
            {
                "character": str(old[codepoint]["character"]),
                "codepoint": str(codepoint),
                "glyph_record_sha256": old_digest,
                "source_png_sha256": str(
                    old[codepoint]["source_png_sha256"]
                ),
                "svg_sha256": str(old[codepoint]["svg_sha256"]),
                "proof_png_sha256": str(
                    old[codepoint]["proof_png_sha256"]
                ),
            }
        )
    if sum(
        item["codepoint"] == PRESERVED_CELL_8["codepoint"]
        for item in records
    ) != 1:
        raise MewNoteVerticalHandednessCorrectionError(
            "cell 8 / U+300F preservation evidence is missing"
        )
    return records


def _build_snapshot(
    report_path: Path,
    *,
    project_root: Path,
    retention: str | None = None,
) -> dict[str, Any]:
    report = _object(report_path, label="batch vector report")
    ttf = _report_ttf(report_path, report)
    proofs = report.get("proofs")
    if not isinstance(proofs, dict):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{report_path}: proof inventory is missing"
        )
    result: dict[str, Any] = {
        "report": _pin(
            report_path,
            project_root=project_root,
            retention=retention,
        ),
        "ttf": _pin(
            ttf,
            project_root=project_root,
            retention=retention,
        ),
    }
    for key in (
        "black_on_white",
        "white_on_black",
        "segmented_source",
    ):
        relative = proofs.get(key)
        if not isinstance(relative, str):
            raise MewNoteVerticalHandednessCorrectionError(
                f"{report_path}: {key} proof is missing"
            )
        result[key] = _pin(
            report_path.parent / relative,
            project_root=project_root,
            retention=retention,
        )
    return result


def _minimal_descriptor(
    *,
    batch: Mapping[str, Any],
    raster_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "state": "generated-unreviewed",
        "raster": "raster.png",
        "raster_sha256": raster_sha256,
        "grid": {
            "rows": evidence.GRID_ROWS,
            "columns": evidence.GRID_COLUMNS,
            "characters": [
                entry["character"] for entry in batch["entries"]
            ],
            "empty_grid_cells": (
                evidence.GRID_CAPACITY - len(batch["entries"])
            ),
        },
        "review": {
            "topology": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }


def _history_steps(
    context: evidence.FamilyContext,
    history: Mapping[str, Any],
) -> list[evidence.GenerationStep]:
    result: list[evidence.GenerationStep] = []
    steps = history["steps"]
    for index, step in enumerate(steps):
        inputs = tuple(
            evidence.GenerationInput(
                role=item["role"],
                retention=item["retention"],
                path=(
                    None
                    if item["path"] is None
                    else context.project_root / item["path"]
                ),
                sha256=item["sha256"],
            )
            for item in step["inputs"]
        )
        result.append(
            evidence.GenerationStep(
                operation=step["operation"],
                disposition=(
                    "rejected"
                    if index == len(steps) - 1
                    else step["disposition"]
                ),
                call_id=step["call_id"],
                prompt_path=(
                    context.project_root
                    / step["actual_tool_prompt"]["path"]
                ),
                inputs=inputs,
                output_sha256=step["output"]["sha256"],
                output_path=None,
                parent_output_sha256=step["parent_output_sha256"],
            )
        )
    return result


def _expected_pin(
    path: Path,
    *,
    project_root: Path,
) -> dict[str, str]:
    return {
        "path": _relative(path, project_root=project_root),
        "sha256": sha256_path(path),
    }


def _find_exact_supersession(
    approval: Mapping[str, Any],
    *,
    predecessor_sha256: str,
    reason: str,
    field: str,
    record_pin: Mapping[str, str],
) -> bool:
    expected = {
        "release_approval_sha256": predecessor_sha256,
        "reason": reason,
        "corrected_batches": [
            {
                "collection_id": COLLECTION_ID,
                "batch_id": BATCH_ID,
                field: dict(record_pin),
            }
        ],
    }
    supersedes = approval.get("supersedes")
    return (
        isinstance(supersedes, list)
        and sum(item == expected for item in supersedes) == 1
    )


def _snapshot_and_validate_predecessor_approval(
    *,
    context: evidence.FamilyContext,
    review_path: Path,
    orientation_record_path: Path,
    orientation_record: Mapping[str, Any],
) -> dict[str, Any]:
    approval_path = _regular_file(
        context.project_root / APPROVAL_PATH,
        label="canonical predecessor release approval",
    )
    approval_sha256 = sha256_path(approval_path)
    approval = _object(
        approval_path, label="canonical predecessor release approval"
    )
    orientation_pin = _expected_pin(
        orientation_record_path,
        project_root=context.project_root,
    )
    review_pin = _expected_pin(
        review_path, project_root=context.project_root
    )
    reviewed = approval.get("reviewed_batches")
    matching = [
        item
        for item in reviewed
        if isinstance(item, dict)
        and item.get("collection_id") == COLLECTION_ID
        and item.get("batch_id") == BATCH_ID
    ] if isinstance(reviewed, list) else []
    orientation_prior_approval = orientation_record["prior_evidence"][
        "release_approval"
    ]["sha256"]
    if (
        approval.get("record_type")
        != "mew-note-tc-collection-release-approval"
        or approval.get("decision") != "APPROVED"
        or approval_sha256 == orientation_prior_approval
        or len(matching) != 1
        or matching[0].get("review") != review_pin
        or matching[0].get(
            "post_review_vertical_orientation_correction"
        )
        != orientation_pin
        or not _find_exact_supersession(
            approval,
            predecessor_sha256=orientation_prior_approval,
            reason=orientation_predecessor.REASON,
            field="post_review_vertical_orientation_correction",
            record_pin=orientation_pin,
        )
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "canonical approval does not complete the exact "
            "vertical-orientation predecessor"
        )
    snapshot_path = approval_snapshot_path(
        context, approval_sha256
    )
    if snapshot_path.exists():
        snapshot_path = _regular_file(
            snapshot_path, label="existing approval snapshot"
        )
        if (
            snapshot_path.read_bytes() != approval_path.read_bytes()
            or sha256_path(snapshot_path) != approval_sha256
        ):
            raise MewNoteVerticalHandednessCorrectionError(
                "existing approval snapshot is not byte-identical"
            )
    else:
        _atomic_copy(approval_path, snapshot_path)
    if (
        snapshot_path.read_bytes() != approval_path.read_bytes()
        or sha256_path(snapshot_path) != approval_sha256
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "approval snapshot copy is not byte-identical"
        )
    return {
        "immutable_snapshot": _pin(
            snapshot_path,
            project_root=context.project_root,
            retention="immutable-release-approval-snapshot",
        ),
        "canonical_overwrite_target": _historical_pin(
            approval_path,
            approval_sha256,
            project_root=context.project_root,
            retention="canonical-overwrite-target",
        ),
    }


def _validate_predecessor(
    context: evidence.FamilyContext,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    paths = context.batch_paths(COLLECTION_ID, BATCH_ID)
    orientation_path = _regular_file(
        paths.source / orientation_predecessor.RECORD_NAME,
        label="vertical-orientation predecessor record",
    )
    orientation_record = _object(
        orientation_path, label="vertical-orientation predecessor record"
    )
    try:
        validated = orientation_predecessor.validate_correction(
            context,
            require_new_review=True,
            require_reapproval=True,
        )
    except (
        orientation_predecessor.MewNoteVerticalOrientationCorrectionError
    ) as exc:
        raise MewNoteVerticalHandednessCorrectionError(str(exc)) from exc
    if validated != orientation_record:
        raise MewNoteVerticalHandednessCorrectionError(
            "vertical-orientation predecessor parser drift"
        )
    history = evidence.validate_history(
        context, COLLECTION_ID, BATCH_ID
    )
    source = evidence.validate_source(
        context, COLLECTION_ID, BATCH_ID
    )
    review_path = _regular_file(
        paths.source / "review.json",
        label="vertical-orientation replacement review",
    )
    review = _object(
        review_path, label="vertical-orientation replacement review"
    )
    report_path = paths.build / "report.json"
    current_evidence = evidence.build_vector_batch(
        context, COLLECTION_ID, BATCH_ID
    )
    if (
        review.get("decision") != "ACCEPT"
        or review.get("source")
        != _expected_pin(
            paths.source / "source.json",
            project_root=context.project_root,
        )
        or review.get("evidence") != current_evidence
        or source["raster_sha256"]
        != sha256_path(paths.source / "raster.png")
        or history["accepted_final"]["raster"]["sha256"]
        != source["raster_sha256"]
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "vertical-orientation predecessor evidence is stale"
        )
    rejected = _handedness_diagnostics(
        report_path,
        paths.source / "raster.png",
        source_sha256=sha256_path(paths.source / "source.json"),
        expect_accepted=False,
    )
    approval = _snapshot_and_validate_predecessor_approval(
        context=context,
        review_path=review_path,
        orientation_record_path=orientation_path,
        orientation_record=orientation_record,
    )
    prior = {
        "vertical_orientation_correction": _pin(
            orientation_path,
            project_root=context.project_root,
            retention="immutable-predecessor-correction-record",
        ),
        "history": _pin(
            paths.source / "history.json",
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "source": _pin(
            paths.source / "source.json",
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "raster": _pin(
            paths.source / "raster.png",
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "review": _pin(
            review_path,
            project_root=context.project_root,
            retention="hash-only-superseded",
        ),
        "release_approval": approval,
        "build": _build_snapshot(
            report_path,
            project_root=context.project_root,
            retention="hash-only-derived-superseded",
        ),
    }
    return prior, rejected


def _preflight_candidate(
    *,
    context: evidence.FamilyContext,
    batch: Mapping[str, Any],
    original_raster: Path,
    candidate_raster: Path,
    old_report_path: Path,
) -> tuple[dict[str, Any], Path]:
    candidate_raster = _regular_file(
        candidate_raster, label="raw candidate raster"
    )
    if sha256_path(candidate_raster) != EXPECTED_CANDIDATE_SHA256:
        raise MewNoteVerticalHandednessCorrectionError(
            "raw candidate raster hash mismatch"
        )
    temporary = Path(
        tempfile.mkdtemp(prefix="mew-note-vertical-handedness-preflight-")
    )
    try:
        raster = temporary / "raster.png"
        composite = _compose(
            original_raster,
            candidate_raster,
            raster,
        )
        descriptor_path = temporary / "source.json"
        descriptor_path.write_bytes(
            _json_bytes(
                _minimal_descriptor(
                    batch=batch,
                    raster_sha256=sha256_path(raster),
                )
            )
        )
        final = imagegen_font_pipeline.build_batch(
            descriptor_path,
            output_root=temporary / "build",
            allowed_raster_root=temporary,
            family_name_prefix="Mew Note TC",
            postscript_name_prefix="MewNoteTC",
        )
        report_path = final / "report.json"
        diagnostics = _handedness_diagnostics(
            report_path,
            raster,
            source_sha256=sha256_path(descriptor_path),
            expect_accepted=True,
        )
        unchanged = _unchanged_glyph_evidence(
            old_report_path, report_path
        )
        report = _object(
            report_path, label="candidate vector report"
        )
        ttf = _report_ttf(report_path, report)
        result = {
            "raw_candidate_sha256": EXPECTED_CANDIDATE_SHA256,
            "installed_composite_sha256": (
                composite["installed_composite_sha256"]
            ),
            "ttf_sha256": sha256_path(ttf),
            "handedness_diagnostics": diagnostics,
            "unchanged_non_target_glyphs": unchanged,
            "micro_edge_count": sum(
                int(glyph["micro_edge_count"])
                for glyph in report["glyphs"]
            ),
            "acute_micro_turn_count": sum(
                int(glyph["acute_micro_turn_count"])
                for glyph in report["glyphs"]
            ),
        }
        if (
            result["micro_edge_count"] != 0
            or result["acute_micro_turn_count"] != 0
        ):
            raise MewNoteVerticalHandednessCorrectionError(
                "candidate failed strict vector geometry"
            )
        retained = temporary / "retained-composite.png"
        raster.replace(retained)
        return result, retained
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(f".{path.name}.lock")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock, flags, 0o600)
    except FileExistsError as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"correction lock already exists: {lock}"
        ) from exc
    except OSError as exc:
        raise MewNoteVerticalHandednessCorrectionError(
            f"cannot acquire correction lock {lock}: {exc}"
        ) from exc
    completed = False
    try:
        os.write(
            descriptor,
            f"pid={os.getpid()}\n".encode("ascii"),
        )
        os.fsync(descriptor)
        yield lock
        completed = True
    finally:
        os.close(descriptor)
        if completed:
            try:
                lock.unlink()
            except FileNotFoundError as exc:
                raise MewNoteVerticalHandednessCorrectionError(
                    f"correction lock disappeared: {lock}"
                ) from exc


def _verify_rollback(
    *,
    old_bytes: Mapping[Path, bytes],
    paths: evidence.BatchPaths,
    build_backup: Path | None,
) -> None:
    for path, expected in old_bytes.items():
        if path.read_bytes() != expected:
            raise MewNoteVerticalHandednessCorrectionError(
                f"rollback byte drift: {path}"
            )
    if build_backup is not None and build_backup.exists():
        raise MewNoteVerticalHandednessCorrectionError(
            "rollback left a build backup behind"
        )
    if not paths.build.is_dir():
        raise MewNoteVerticalHandednessCorrectionError(
            "rollback did not restore the vector build"
        )


def apply_correction(
    context: evidence.FamilyContext,
    *,
    candidate_raster: Path,
    candidate_sha256: str,
    call_id: str,
    confirmation: str,
    reason: str = REASON,
) -> dict[str, Any]:
    """Install the one-cell correction and invalidate review/approval."""

    if confirmation != CONFIRMATION:
        raise MewNoteVerticalHandednessCorrectionError(
            "explicit vertical-handedness correction authorization "
            "is required"
        )
    if reason != REASON:
        raise MewNoteVerticalHandednessCorrectionError(
            "unsupported vertical-handedness correction reason"
        )
    if (
        candidate_sha256 != EXPECTED_CANDIDATE_SHA256
        or call_id != EXPECTED_CALL_ID
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "candidate image-generation identity drift"
        )
    candidate_raster = _regular_file(
        candidate_raster, label="raw handedness candidate"
    )
    if sha256_path(candidate_raster) != EXPECTED_CANDIDATE_SHA256:
        raise MewNoteVerticalHandednessCorrectionError(
            "raw handedness candidate hash drift"
        )
    record_path = correction_path(context)
    retained_candidate = raw_candidate_path(context)
    approval_path = context.project_root / APPROVAL_PATH
    paths = context.batch_paths(COLLECTION_ID, BATCH_ID)
    root = paths.source
    deferred_error: BaseException | None = None
    with _exclusive_lock(record_path):
        with _exclusive_lock(approval_path):
            if record_path.exists() or retained_candidate.exists():
                raise MewNoteVerticalHandednessCorrectionError(
                    "vertical-handedness correction already exists"
                )
            prior, rejected = _validate_predecessor(context)
            batch = evidence.frozen_batch(
                context, COLLECTION_ID, BATCH_ID
            )
            if [
                (
                    entry["cell"],
                    entry["character"],
                    entry["codepoint"],
                )
                for entry in batch["entries"]
                if entry["codepoint"] == TARGET["codepoint"]
            ] != [
                (
                    TARGET["cell"],
                    TARGET["character"],
                    TARGET["codepoint"],
                )
            ]:
                raise MewNoteVerticalHandednessCorrectionError(
                    "U+300D is not frozen at vertical-0002 cell 6"
                )
            history = evidence.validate_history(
                context, COLLECTION_ID, BATCH_ID
            )
            source_path = root / "source.json"
            raster_path = root / "raster.png"
            review_path = root / "review.json"
            report_path = paths.build / "report.json"
            preflight, retained_composite = _preflight_candidate(
                context=context,
                batch=batch,
                original_raster=raster_path,
                candidate_raster=candidate_raster,
                old_report_path=report_path,
            )
            temporary_root = retained_composite.parent
            canonical_composite = (
                temporary_root / "canonical-composite.png"
            )
            composite_contract = _compose(
                raster_path,
                candidate_raster,
                canonical_composite,
            )
            if (
                sha256_path(canonical_composite)
                != preflight["installed_composite_sha256"]
                or sha256_path(retained_composite)
                != preflight["installed_composite_sha256"]
            ):
                shutil.rmtree(temporary_root, ignore_errors=True)
                raise MewNoteVerticalHandednessCorrectionError(
                    "candidate composite is not deterministic"
                )
            old_steps = _history_steps(context, history)
            prompt_path = root / (
                f"tool-step-{len(old_steps) + 1:04d}.txt"
            )
            prompt_path = _regular_file(
                prompt_path, label="handedness correction prompt"
            )
            if sha256_path(prompt_path) != EXPECTED_PROMPT_SHA256:
                shutil.rmtree(temporary_root, ignore_errors=True)
                raise MewNoteVerticalHandednessCorrectionError(
                    "exact image-generation prompt hash drift"
                )
            previous_hash = history["accepted_final"]["raster"][
                "sha256"
            ]
            last_inputs = tuple(
                item
                for item in old_steps[-1].inputs
                if item.role != "parent-output"
            )
            correction_step = evidence.GenerationStep(
                operation="correction",
                disposition="accepted",
                call_id=call_id,
                prompt_path=prompt_path,
                inputs=(
                    evidence.GenerationInput(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=previous_hash,
                    ),
                    *last_inputs,
                ),
                output_sha256=preflight[
                    "installed_composite_sha256"
                ],
                output_path=canonical_composite,
                parent_output_sha256=previous_hash,
            )
            old_bytes = {
                path: path.read_bytes()
                for path in (
                    root / "history.json",
                    root / "source.json",
                    root / "raster.png",
                    root / "review.json",
                )
            }
            build_backup: Path | None = None
            if paths.build.exists():
                build_backup = paths.build.with_name(
                    f".{paths.build.name}.vertical-handedness-backup"
                )
                if build_backup.exists():
                    shutil.rmtree(temporary_root, ignore_errors=True)
                    raise MewNoteVerticalHandednessCorrectionError(
                        f"stale correction backup exists: {build_backup}"
                    )
                paths.build.replace(build_backup)
            try:
                _atomic_copy(candidate_raster, retained_candidate)
                evidence.register_history(
                    context,
                    COLLECTION_ID,
                    BATCH_ID,
                    steps=(*old_steps, correction_step),
                )
                current_evidence = evidence.build_vector_batch(
                    context, COLLECTION_ID, BATCH_ID
                )
                current_report_path = paths.build / "report.json"
                corrected = _handedness_diagnostics(
                    current_report_path,
                    root / "raster.png",
                    source_sha256=sha256_path(root / "source.json"),
                    expect_accepted=True,
                )
                old_report = (
                    build_backup / "report.json"
                    if build_backup is not None
                    else report_path
                )
                unchanged = _unchanged_glyph_evidence(
                    old_report, current_report_path
                )
                current_report = _object(
                    current_report_path,
                    label="corrected vector report",
                )
                current_ttf = _report_ttf(
                    current_report_path, current_report
                )
                if (
                    sha256_path(current_ttf)
                    != preflight["ttf_sha256"]
                    or corrected
                    != preflight["handedness_diagnostics"]
                    or unchanged
                    != preflight["unchanged_non_target_glyphs"]
                ):
                    raise MewNoteVerticalHandednessCorrectionError(
                        "canonical correction build differs from preflight"
                    )
                payload: dict[str, Any] = {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": RECORD_TYPE,
                    "family_id": evidence.FAMILY_ID,
                    "pipeline_id": evidence.PIPELINE_ID,
                    "collection_id": COLLECTION_ID,
                    "batch_id": BATCH_ID,
                    "family_context": context.evidence_binding(
                        COLLECTION_ID
                    ),
                    "batch_contract_sha256": (
                        batch["batch_contract_sha256"]
                    ),
                    "implementation": _implementation_pin(
                        context.project_root
                    ),
                    "reason": REASON,
                    "vertical_presentation_contract": {
                        "source_character": TARGET["character"],
                        "source_codepoint": TARGET["codepoint"],
                        "vertical_presentation_character": (
                            TARGET[
                                "vertical_presentation_character"
                            ]
                        ),
                        "vertical_presentation_codepoint": (
                            TARGET[
                                "vertical_presentation_codepoint"
                            ]
                        ),
                        "expected_corner": TARGET["expected_corner"],
                        "expected_handedness": (
                            TARGET["expected_handedness"]
                        ),
                        "diagnostic": BINARY_INK_ALGORITHM,
                        "target_cell": TARGET["cell"],
                    },
                    "rejected_handedness": rejected,
                    "prior_evidence": prior,
                    "candidate_generation": {
                        "call_id": call_id,
                        "actual_tool_prompt": _pin(
                            prompt_path,
                            project_root=context.project_root,
                        ),
                        "raw_candidate": _pin(
                            retained_candidate,
                            project_root=context.project_root,
                            retention=(
                                "retained-original-imagegen-output"
                            ),
                        ),
                    },
                    "composite_installation": composite_contract,
                    "correction_generation": {
                        "appended_sequence": len(old_steps) + 1,
                        "parent_output_sha256": previous_hash,
                        "history": _pin(
                            root / "history.json",
                            project_root=context.project_root,
                        ),
                        "source": _pin(
                            root / "source.json",
                            project_root=context.project_root,
                        ),
                        "raster": _pin(
                            root / "raster.png",
                            project_root=context.project_root,
                        ),
                        "build": _build_snapshot(
                            current_report_path,
                            project_root=context.project_root,
                        ),
                        "batch_vector_evidence": current_evidence,
                        "handedness_diagnostics": corrected,
                        "unchanged_non_target_glyphs": unchanged,
                        "candidate_preflight": preflight,
                    },
                    "required_next_gates": [
                        "independent-raster-vector-technical-review",
                        "collection-release-reapproval",
                    ],
                    "state": "corrected-unreviewed-unapproved",
                }
                payload["correction_sha256"] = (
                    canonical_json_sha256(payload)
                )
                _atomic_json(record_path, payload)
                result = validate_correction(
                    context,
                    require_new_review=False,
                    require_reapproval=False,
                )
            except BaseException as exc:
                deferred_error = exc
                try:
                    record_path.unlink(missing_ok=True)
                    retained_candidate.unlink(missing_ok=True)
                    if paths.build.exists():
                        shutil.rmtree(paths.build)
                    if (
                        build_backup is not None
                        and build_backup.exists()
                    ):
                        build_backup.replace(paths.build)
                    for path, data in old_bytes.items():
                        _atomic_write(path, data)
                    _verify_rollback(
                        old_bytes=old_bytes,
                        paths=paths,
                        build_backup=build_backup,
                    )
                finally:
                    shutil.rmtree(
                        temporary_root, ignore_errors=True
                    )
            else:
                if build_backup is not None:
                    shutil.rmtree(build_backup)
                shutil.rmtree(temporary_root, ignore_errors=True)
    if deferred_error is not None:
        raise deferred_error
    return result


def _validate_pin_schema(
    pin: Any,
    *,
    label: str,
    retention: str | None,
) -> Mapping[str, Any]:
    expected = {"path", "sha256"}
    if retention is not None:
        expected.add("retention")
    pin = _exact_keys(pin, expected, label=label)
    _sha(pin["sha256"], label=f"{label} hash")
    if (
        not isinstance(pin["path"], str)
        or not pin["path"]
        or Path(pin["path"]).is_absolute()
        or ".." in Path(pin["path"]).parts
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label} path is not canonical"
        )
    if retention is not None and pin["retention"] != retention:
        raise MewNoteVerticalHandednessCorrectionError(
            f"{label} retention changed"
        )
    return pin


def _validate_binary_record(
    value: Any,
    *,
    expected_decision: str,
) -> Mapping[str, Any]:
    value = _exact_keys(
        value,
        {
            "algorithm",
            "threshold",
            "ink_bbox_in_cell_interior",
            "ink_pixel_count",
            "connected_component_count",
            "ink_width",
            "ink_height",
            "horizontal_to_vertical_ratio",
            "endpoint_occupancy_pixels",
            "left_vertical_span_ratio",
            "right_vertical_span_ratio",
            "bottom_horizontal_span_ratio",
            "gates",
            "decision",
        },
        label="binary handedness record",
    )
    occupancy = _exact_keys(
        value["endpoint_occupancy_pixels"],
        {"upper_left", "upper_right", "lower_left", "lower_right"},
        label="endpoint occupancy",
    )
    gate_names = {
        "one_connected_component",
        "horizontal_ratio_in_range",
        "upper_left_endpoint_occupied",
        "upper_right_endpoint_clear",
        "lower_right_arm_occupied",
        "left_vertical_arm_present",
        "right_vertical_arm_absent",
        "bottom_horizontal_arm_present",
        "clear_of_cell_interior_edges",
    }
    gates = _exact_keys(
        value["gates"], gate_names, label="handedness gates"
    )
    if (
        value["algorithm"] != BINARY_INK_ALGORITHM
        or value["threshold"] != INK_THRESHOLD
        or value["decision"] != expected_decision
        or any(
            not isinstance(item, int) or item < 0
            for item in occupancy.values()
        )
        or any(not isinstance(item, bool) for item in gates.values())
        or all(gates.values())
        is not (expected_decision == "ACCEPT")
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "binary handedness decision drift"
        )
    return value


def _validate_diagnostic(
    value: Any,
    *,
    expected_decision: str,
) -> Mapping[str, Any]:
    value = _exact_keys(
        value,
        {
            "source_character",
            "source_codepoint",
            "vertical_presentation_character",
            "vertical_presentation_codepoint",
            "expected_corner",
            "expected_handedness",
            "vector",
            "binary_ink",
            "decision",
        },
        label="handedness diagnostic",
    )
    vector = _exact_keys(
        value["vector"],
        {
            "source_ink_bbox_normalized",
            "ink_width",
            "ink_height",
            "horizontal_to_vertical_ratio",
            "source_core_component_count",
            "contour_count",
            "micro_edge_count",
            "acute_micro_turn_count",
        },
        label="handedness vector diagnostic",
    )
    if (
        value["source_character"] != TARGET["character"]
        or value["source_codepoint"] != TARGET["codepoint"]
        or value["vertical_presentation_character"]
        != TARGET["vertical_presentation_character"]
        or value["vertical_presentation_codepoint"]
        != TARGET["vertical_presentation_codepoint"]
        or value["expected_corner"] != TARGET["expected_corner"]
        or value["expected_handedness"]
        != TARGET["expected_handedness"]
        or value["decision"] != expected_decision
        or vector["source_core_component_count"] != 1
        or vector["contour_count"] != 1
        or vector["micro_edge_count"] != 0
        or vector["acute_micro_turn_count"] != 0
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "handedness diagnostic binding drift"
        )
    binary = _validate_binary_record(
        value["binary_ink"],
        expected_decision=expected_decision,
    )
    if binary["decision"] != value["decision"]:
        raise MewNoteVerticalHandednessCorrectionError(
            "binary/vector handedness decision mismatch"
        )
    return value


def _validate_composite(
    *,
    context: evidence.FamilyContext,
    value: Any,
    raw_candidate: Mapping[str, Any],
    installed_raster: Mapping[str, Any],
) -> None:
    value = _exact_keys(
        value,
        {
            "algorithm",
            "pixel_hash_algorithm",
            "canvas",
            "region",
            "preserved_cell_8",
            "preserved_outside_region_sha256",
            "installed_composite_sha256",
        },
        label="single-cell composite",
    )
    if (
        value["algorithm"] != COMPOSITE_ALGORITHM
        or value["pixel_hash_algorithm"] != PIXEL_HASH_ALGORITHM
        or value["canvas"]
        != {"width": 1254, "height": 1254, "mode": "RGB"}
        or value["installed_composite_sha256"]
        != installed_raster["sha256"]
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "single-cell composite contract drift"
        )
    region = _exact_keys(
        value["region"],
        set(TARGET)
        | {
            "superseded_region_sha256",
            "candidate_region_sha256",
        },
        label="U+300D composite region",
    )
    preserved = _exact_keys(
        value["preserved_cell_8"],
        set(PRESERVED_CELL_8) | {"region_sha256"},
        label="preserved cell 8",
    )
    if any(region[key] != item for key, item in TARGET.items()):
        raise MewNoteVerticalHandednessCorrectionError(
            "U+300D composite target drift"
        )
    if any(
        preserved[key] != item
        for key, item in PRESERVED_CELL_8.items()
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "cell 8 preservation target drift"
        )
    for label, digest in (
        (
            "superseded region",
            region["superseded_region_sha256"],
        ),
        ("candidate region", region["candidate_region_sha256"]),
        ("cell 8", preserved["region_sha256"]),
        (
            "outside region",
            value["preserved_outside_region_sha256"],
        ),
    ):
        _sha(digest, label=f"{label} hash")
    candidate = _load_rgb_png(
        context.project_root / raw_candidate["path"],
        label="retained handedness candidate",
    )
    installed = _load_rgb_png(
        context.project_root / installed_raster["path"],
        label="installed handedness composite",
    )
    if (
        region["superseded_region_sha256"]
        == region["candidate_region_sha256"]
        or _region_sha256(
            candidate, TARGET["replacement_box"]
        )
        != region["candidate_region_sha256"]
        or _region_sha256(
            installed, TARGET["replacement_box"]
        )
        != region["candidate_region_sha256"]
        or _region_sha256(
            installed, PRESERVED_CELL_8["replacement_box"]
        )
        != preserved["region_sha256"]
        or _framed_pixel_sha256(
            installed,
            regions=(TARGET["replacement_box"],),
            include_regions=False,
        )
        != value["preserved_outside_region_sha256"]
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "single-cell installed pixel provenance drift"
        )


def _validate_reapproval(
    context: evidence.FamilyContext,
    *,
    prior_approval: Mapping[str, Any],
    review_path: Path,
    record_path: Path,
) -> None:
    canonical = _regular_file(
        context.project_root / APPROVAL_PATH,
        label="replacement collection release approval",
    )
    prior_sha256 = prior_approval["canonical_overwrite_target"][
        "sha256"
    ]
    if sha256_path(canonical) == prior_sha256:
        raise MewNoteVerticalHandednessCorrectionError(
            "collection release reapproval is still missing"
        )
    approval = _object(
        canonical, label="replacement collection release approval"
    )
    record_pin = _expected_pin(
        record_path, project_root=context.project_root
    )
    review_pin = _expected_pin(
        review_path, project_root=context.project_root
    )
    reviewed = approval.get("reviewed_batches")
    matching = [
        item
        for item in reviewed
        if isinstance(item, dict)
        and item.get("collection_id") == COLLECTION_ID
        and item.get("batch_id") == BATCH_ID
    ] if isinstance(reviewed, list) else []
    if (
        approval.get("record_type")
        != "mew-note-tc-collection-release-approval"
        or approval.get("decision") != "APPROVED"
        or len(matching) != 1
        or matching[0].get("review") != review_pin
        or matching[0].get(APPROVAL_FIELD) != record_pin
        or not _find_exact_supersession(
            approval,
            predecessor_sha256=prior_sha256,
            reason=REASON,
            field=APPROVAL_FIELD,
            record_pin=record_pin,
        )
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "replacement approval lacks the exact correction pin "
            "and supersedes transition"
        )


def validate_correction(
    context: evidence.FamilyContext,
    *,
    require_new_review: bool,
    require_reapproval: bool,
) -> dict[str, Any]:
    """Validate the immutable correction and optional downstream gates."""

    path = correction_path(context)
    payload = _object(path, label="vertical-handedness correction")
    payload = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "family_id",
            "pipeline_id",
            "collection_id",
            "batch_id",
            "family_context",
            "batch_contract_sha256",
            "implementation",
            "reason",
            "vertical_presentation_contract",
            "rejected_handedness",
            "prior_evidence",
            "candidate_generation",
            "composite_installation",
            "correction_generation",
            "required_next_gates",
            "state",
            "correction_sha256",
        },
        label="vertical-handedness correction",
    )
    batch = evidence.frozen_batch(
        context, COLLECTION_ID, BATCH_ID
    )
    if (
        payload["schema_version"] != SCHEMA_VERSION
        or payload["record_type"] != RECORD_TYPE
        or payload["family_id"] != evidence.FAMILY_ID
        or payload["pipeline_id"] != evidence.PIPELINE_ID
        or payload["collection_id"] != COLLECTION_ID
        or payload["batch_id"] != BATCH_ID
        or payload["family_context"]
        != context.evidence_binding(COLLECTION_ID)
        or payload["batch_contract_sha256"]
        != batch["batch_contract_sha256"]
        or payload["implementation"]
        != _implementation_pin(context.project_root)
        or payload["reason"] != REASON
        or payload["required_next_gates"]
        != [
            "independent-raster-vector-technical-review",
            "collection-release-reapproval",
        ]
        or payload["state"] != "corrected-unreviewed-unapproved"
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "vertical-handedness correction binding mismatch"
        )
    expected_digest = canonical_json_sha256(
        {
            key: value
            for key, value in payload.items()
            if key != "correction_sha256"
        }
    )
    if payload["correction_sha256"] != expected_digest:
        raise MewNoteVerticalHandednessCorrectionError(
            "vertical-handedness correction canonical hash mismatch"
        )
    contract = _exact_keys(
        payload["vertical_presentation_contract"],
        {
            "source_character",
            "source_codepoint",
            "vertical_presentation_character",
            "vertical_presentation_codepoint",
            "expected_corner",
            "expected_handedness",
            "diagnostic",
            "target_cell",
        },
        label="vertical presentation contract",
    )
    if contract != {
        "source_character": TARGET["character"],
        "source_codepoint": TARGET["codepoint"],
        "vertical_presentation_character": (
            TARGET["vertical_presentation_character"]
        ),
        "vertical_presentation_codepoint": (
            TARGET["vertical_presentation_codepoint"]
        ),
        "expected_corner": TARGET["expected_corner"],
        "expected_handedness": TARGET["expected_handedness"],
        "diagnostic": BINARY_INK_ALGORITHM,
        "target_cell": TARGET["cell"],
    }:
        raise MewNoteVerticalHandednessCorrectionError(
            "vertical presentation contract drift"
        )
    _validate_diagnostic(
        payload["rejected_handedness"],
        expected_decision="REJECT",
    )
    prior = _exact_keys(
        payload["prior_evidence"],
        {
            "vertical_orientation_correction",
            "history",
            "source",
            "raster",
            "review",
            "release_approval",
            "build",
        },
        label="prior handedness evidence",
    )
    retention_by_label = {
        "vertical_orientation_correction": (
            "immutable-predecessor-correction-record"
        ),
        "history": "hash-only-superseded",
        "source": "hash-only-superseded",
        "raster": "hash-only-superseded",
        "review": "hash-only-superseded",
    }
    for label, retention in retention_by_label.items():
        _validate_pin_schema(
            prior[label],
            label=f"prior {label}",
            retention=retention,
        )
    paths = context.batch_paths(COLLECTION_ID, BATCH_ID)
    expected_prior_paths = {
        "vertical_orientation_correction": _relative(
            paths.source / orientation_predecessor.RECORD_NAME,
            project_root=context.project_root,
        ),
        "history": _relative(
            paths.source / "history.json",
            project_root=context.project_root,
        ),
        "source": _relative(
            paths.source / "source.json",
            project_root=context.project_root,
        ),
        "raster": _relative(
            paths.source / "raster.png",
            project_root=context.project_root,
        ),
        "review": _relative(
            paths.source / "review.json",
            project_root=context.project_root,
        ),
    }
    if any(
        prior[label]["path"] != expected
        for label, expected in expected_prior_paths.items()
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "prior evidence canonical path drift"
        )
    orientation_path = (
        context.project_root
        / prior["vertical_orientation_correction"]["path"]
    )
    if (
        sha256_path(
            _regular_file(
                orientation_path,
                label="pinned orientation predecessor",
            )
        )
        != prior["vertical_orientation_correction"]["sha256"]
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "orientation predecessor record hash drift"
        )
    prior_approval = _exact_keys(
        prior["release_approval"],
        {"immutable_snapshot", "canonical_overwrite_target"},
        label="prior release approval",
    )
    snapshot_pin = _validate_pin_schema(
        prior_approval["immutable_snapshot"],
        label="immutable approval snapshot",
        retention="immutable-release-approval-snapshot",
    )
    canonical_pin = _validate_pin_schema(
        prior_approval["canonical_overwrite_target"],
        label="canonical approval overwrite target",
        retention="canonical-overwrite-target",
    )
    expected_snapshot = approval_snapshot_path(
        context, canonical_pin["sha256"]
    )
    if (
        snapshot_pin["path"]
        != _relative(
            expected_snapshot,
            project_root=context.project_root,
        )
        or snapshot_pin["sha256"] != canonical_pin["sha256"]
        or canonical_pin["path"] != APPROVAL_PATH.as_posix()
        or _pin(
            expected_snapshot,
            project_root=context.project_root,
            retention="immutable-release-approval-snapshot",
        )
        != snapshot_pin
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "predecessor approval snapshot provenance drift"
        )
    prior_build = _exact_keys(
        prior["build"],
        {
            "report",
            "ttf",
            "black_on_white",
            "white_on_black",
            "segmented_source",
        },
        label="prior vector build",
    )
    for label, pin in prior_build.items():
        _validate_pin_schema(
            pin,
            label=f"prior build {label}",
            retention="hash-only-derived-superseded",
        )
    candidate = _exact_keys(
        payload["candidate_generation"],
        {"call_id", "actual_tool_prompt", "raw_candidate"},
        label="candidate generation",
    )
    if candidate["call_id"] != EXPECTED_CALL_ID:
        raise MewNoteVerticalHandednessCorrectionError(
            "candidate call ID drift"
        )
    prompt_pin = _validate_pin_schema(
        candidate["actual_tool_prompt"],
        label="candidate prompt",
        retention=None,
    )
    raw_pin = _validate_pin_schema(
        candidate["raw_candidate"],
        label="raw candidate",
        retention="retained-original-imagegen-output",
    )
    history = evidence.validate_history(
        context, COLLECTION_ID, BATCH_ID
    )
    expected_prompt = paths.source / (
        f"tool-step-{len(history['steps']):04d}.txt"
    )
    if (
        prompt_pin
        != _pin(
            expected_prompt,
            project_root=context.project_root,
        )
        or prompt_pin["sha256"] != EXPECTED_PROMPT_SHA256
        or raw_pin
        != _pin(
            raw_candidate_path(context),
            project_root=context.project_root,
            retention="retained-original-imagegen-output",
        )
        or raw_pin["sha256"] != EXPECTED_CANDIDATE_SHA256
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "candidate prompt or raster provenance drift"
        )
    source = evidence.validate_source(
        context, COLLECTION_ID, BATCH_ID
    )
    generated = _exact_keys(
        payload["correction_generation"],
        {
            "appended_sequence",
            "parent_output_sha256",
            "history",
            "source",
            "raster",
            "build",
            "batch_vector_evidence",
            "handedness_diagnostics",
            "unchanged_non_target_glyphs",
            "candidate_preflight",
        },
        label="corrected generation",
    )
    for label, actual in (
        ("history", paths.source / "history.json"),
        ("source", paths.source / "source.json"),
        ("raster", paths.source / "raster.png"),
    ):
        if generated[label] != _pin(
            actual, project_root=context.project_root
        ):
            raise MewNoteVerticalHandednessCorrectionError(
                f"corrected {label} evidence drift"
            )
    if (
        generated["appended_sequence"] != len(history["steps"])
        or len(history["steps"]) < 2
        or generated["parent_output_sha256"]
        != history["steps"][-2]["output"]["sha256"]
        or history["accepted_final"]["call_id"] != EXPECTED_CALL_ID
        or generated["raster"]["sha256"] != source["raster_sha256"]
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "corrected history chain drift"
        )
    current_evidence = evidence.build_vector_batch(
        context, COLLECTION_ID, BATCH_ID
    )
    if generated["batch_vector_evidence"] != current_evidence:
        raise MewNoteVerticalHandednessCorrectionError(
            "corrected batch vector evidence drift"
        )
    current_build = _build_snapshot(
        paths.build / "report.json",
        project_root=context.project_root,
    )
    if generated["build"] != current_build:
        raise MewNoteVerticalHandednessCorrectionError(
            "corrected build inventory drift"
        )
    diagnostics = _handedness_diagnostics(
        paths.build / "report.json",
        paths.source / "raster.png",
        source_sha256=sha256_path(paths.source / "source.json"),
        expect_accepted=True,
    )
    _validate_diagnostic(
        generated["handedness_diagnostics"],
        expected_decision="ACCEPT",
    )
    if generated["handedness_diagnostics"] != diagnostics:
        raise MewNoteVerticalHandednessCorrectionError(
            "corrected handedness evidence drift"
        )
    unchanged = generated["unchanged_non_target_glyphs"]
    expected_unchanged_keys = {
        "character",
        "codepoint",
        "glyph_record_sha256",
        "source_png_sha256",
        "svg_sha256",
        "proof_png_sha256",
    }
    if (
        not isinstance(unchanged, list)
        or len(unchanged) != 15
        or any(
            not isinstance(item, dict)
            or set(item) != expected_unchanged_keys
            for item in unchanged
        )
        or sum(
            item["codepoint"] == PRESERVED_CELL_8["codepoint"]
            for item in unchanged
        )
        != 1
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "non-target vector evidence inventory drift"
        )
    preflight = _exact_keys(
        generated["candidate_preflight"],
        {
            "raw_candidate_sha256",
            "installed_composite_sha256",
            "ttf_sha256",
            "handedness_diagnostics",
            "unchanged_non_target_glyphs",
            "micro_edge_count",
            "acute_micro_turn_count",
        },
        label="candidate preflight",
    )
    if (
        preflight["raw_candidate_sha256"]
        != EXPECTED_CANDIDATE_SHA256
        or preflight["installed_composite_sha256"]
        != generated["raster"]["sha256"]
        or preflight["ttf_sha256"]
        != current_build["ttf"]["sha256"]
        or preflight["handedness_diagnostics"] != diagnostics
        or preflight["unchanged_non_target_glyphs"] != unchanged
        or preflight["micro_edge_count"] != 0
        or preflight["acute_micro_turn_count"] != 0
    ):
        raise MewNoteVerticalHandednessCorrectionError(
            "candidate preflight evidence drift"
        )
    _validate_composite(
        context=context,
        value=payload["composite_installation"],
        raw_candidate=raw_pin,
        installed_raster=generated["raster"],
    )
    review_path = paths.source / "review.json"
    if require_new_review or require_reapproval:
        review_path = _regular_file(
            review_path, label="replacement handedness review"
        )
        review = _object(
            review_path, label="replacement handedness review"
        )
        if (
            sha256_path(review_path) == prior["review"]["sha256"]
            or review.get("decision") != "ACCEPT"
            or review.get("source")
            != _expected_pin(
                paths.source / "source.json",
                project_root=context.project_root,
            )
            or review.get("evidence") != current_evidence
        ):
            raise MewNoteVerticalHandednessCorrectionError(
                "replacement handedness review is missing or stale"
            )
    if require_reapproval:
        _validate_reapproval(
            context,
            prior_approval=prior_approval,
            review_path=review_path,
            record_path=path,
        )
    return dict(payload)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--candidate-raster", type=Path, required=True)
    apply_parser.add_argument("--candidate-sha256", required=True)
    apply_parser.add_argument("--call-id", required=True)
    apply_parser.add_argument("--confirmation", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--require-new-review", action="store_true")
    validate_parser.add_argument("--require-reapproval", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    context = evidence.load_context(args.project_root)
    if args.command == "apply":
        result = apply_correction(
            context,
            candidate_raster=args.candidate_raster,
            candidate_sha256=args.candidate_sha256,
            call_id=args.call_id,
            confirmation=args.confirmation,
        )
    else:
        result = validate_correction(
            context,
            require_new_review=args.require_new_review,
            require_reapproval=args.require_reapproval,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
