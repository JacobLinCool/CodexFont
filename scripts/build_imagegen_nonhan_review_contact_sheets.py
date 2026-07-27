#!/usr/bin/env python3
"""Compose hash-verified non-Han v3 proofs without resampling them.

The canonical review records pin the individual proof PNGs.  These contact
sheets are only a lossless viewing aid: every source proof is pasted at its
native pixel dimensions, and a manifest records both the source and composed
SHA-256 hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from scripts import imagegen_nonhan_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_ROOT = ROOT / "build/imagegen"
DEFAULT_OUTPUT = ROOT / "tmp/nonhan-v3-review-contact-sheets"
POLARITIES = ("black-on-white", "white-on-black")
HEADER_HEIGHT = 78
LABEL_HEIGHT = 20
OUTER_MARGIN = 12
COLUMN_GAP = 16
ROW_GAP = 10
GROUP_GAP = 20


class ContactSheetError(RuntimeError):
    """A proof contact sheet could not be composed without ambiguity."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContactSheetError(f"{path}: cannot read report: {exc}") from exc
    if not isinstance(value, dict):
        raise ContactSheetError(f"{path}: report is not an object")
    return value


def _proofs(
    batch_directory: Path,
    report: Mapping[str, Any],
) -> dict[tuple[int, str], tuple[Path, str]]:
    records = report.get("proofs")
    if not isinstance(records, list):
        raise ContactSheetError(f"{batch_directory}: proofs are missing")
    expected = {
        (size, polarity)
        for size in pipeline.SMALL_SIZE_PIXELS
        for polarity in POLARITIES
    }
    result: dict[tuple[int, str], tuple[Path, str]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("kind") != "small-size":
            continue
        key = (record.get("size_px"), record.get("polarity"))
        if key not in expected or key in result:
            raise ContactSheetError(
                f"{batch_directory}: unexpected/duplicate proof {key}"
            )
        relative = record.get("path")
        digest = record.get("sha256")
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise ContactSheetError(
                f"{batch_directory}: malformed proof record {key}"
            )
        path = batch_directory / relative
        if not path.is_file() or _sha256(path) != digest:
            raise ContactSheetError(
                f"{batch_directory}: proof hash mismatch for {key}"
            )
        result[key] = (path, digest)
    if set(result) != expected:
        raise ContactSheetError(
            f"{batch_directory}: incomplete small-size proof set"
        )
    return result


def _native_image(path: Path) -> Image.Image:
    image = Image.open(path)
    image.load()
    if image.mode != "L":
        raise ContactSheetError(f"{path}: expected an 8-bit grayscale PNG")
    return image


def _compose_batch(
    *,
    batch_id: str,
    build_root: Path,
    output_directory: Path,
) -> tuple[Path, Mapping[str, Any]]:
    batch_directory = build_root / f"imagegen-{batch_id}"
    report_path = batch_directory / "report.json"
    report = _read_object(report_path)
    if (
        report.get("pipeline") != pipeline.PIPELINE_ID
        or report.get("batch_id") != f"imagegen-{batch_id}"
    ):
        raise ContactSheetError(
            f"{report_path}: not a canonical non-Han v3 report"
        )
    proofs = _proofs(batch_directory, report)
    images = {
        key: _native_image(path)
        for key, (path, _digest) in proofs.items()
    }
    column_width = max(image.width for image in images.values())
    rows = [
        max(images[(size, polarity)].height for polarity in POLARITIES)
        for size in pipeline.SMALL_SIZE_PIXELS
    ]
    width = (
        OUTER_MARGIN * 2
        + column_width * 2
        + COLUMN_GAP
    )
    height = (
        OUTER_MARGIN * 2
        + HEADER_HEIGHT
        + sum(LABEL_HEIGHT + row for row in rows)
        + ROW_GAP * (len(rows) - 1)
    )
    canvas = Image.new("L", (width, height), 208)
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    labels = [
        str(record["codepoint"])
        for record in report.get("glyphs", [])
        if isinstance(record, dict) and isinstance(record.get("codepoint"), str)
    ]
    if not labels:
        raise ContactSheetError(f"{report_path}: glyph identities are missing")
    draw.text(
        (OUTER_MARGIN, OUTER_MARGIN),
        f"{batch_id}  {report['source_descriptor_sha256'][:16]}",
        fill=0,
        font=font,
    )
    midpoint = (len(labels) + 1) // 2
    draw.text(
        (OUTER_MARGIN, OUTER_MARGIN + 20),
        " ".join(labels[:midpoint]),
        fill=0,
        font=font,
    )
    draw.text(
        (OUTER_MARGIN, OUTER_MARGIN + 40),
        " ".join(labels[midpoint:]),
        fill=0,
        font=font,
    )

    y = OUTER_MARGIN + HEADER_HEIGHT
    source_records: list[dict[str, Any]] = []
    for size, row_height in zip(
        pipeline.SMALL_SIZE_PIXELS,
        rows,
        strict=True,
    ):
        for column, polarity in enumerate(POLARITIES):
            x = OUTER_MARGIN + column * (column_width + COLUMN_GAP)
            draw.text(
                (x, y),
                f"{size}px {polarity}",
                fill=0,
                font=font,
            )
            image = images[(size, polarity)]
            paste_x = x + (column_width - image.width) // 2
            paste_y = y + LABEL_HEIGHT
            canvas.paste(image, (paste_x, paste_y))
            path, digest = proofs[(size, polarity)]
            source_records.append(
                {
                    "size_px": size,
                    "polarity": polarity,
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": digest,
                    "native_width_px": image.width,
                    "native_height_px": image.height,
                    "paste_x": paste_x,
                    "paste_y": paste_y,
                    "resampled": False,
                }
            )
        y += LABEL_HEIGHT + row_height + ROW_GAP

    output_directory.mkdir(parents=True, exist_ok=True)
    output = output_directory / f"{batch_id}.png"
    canvas.save(output, optimize=False)
    return output, {
        "batch_id": batch_id,
        "report": report_path.relative_to(ROOT).as_posix(),
        "report_sha256": _sha256(report_path),
        "contact_sheet": output.relative_to(ROOT).as_posix(),
        "contact_sheet_sha256": _sha256(output),
        "width_px": width,
        "height_px": height,
        "proofs": source_records,
    }


def build_contact_sheets(
    batch_ids: Sequence[str],
    *,
    build_root: Path = DEFAULT_BUILD_ROOT,
    output_directory: Path = DEFAULT_OUTPUT,
    group_size: int = 4,
) -> Path:
    if not batch_ids:
        raise ContactSheetError("at least one batch is required")
    if group_size <= 0:
        raise ContactSheetError("group_size must be positive")
    records: list[Mapping[str, Any]] = []
    sheets: list[Path] = []
    for batch_id in batch_ids:
        if (
            not batch_id.startswith("nonhan-")
            or len(batch_id) != len("nonhan-0001")
            or not batch_id[-4:].isdigit()
        ):
            raise ContactSheetError(f"invalid batch ID: {batch_id}")
        sheet, record = _compose_batch(
            batch_id=batch_id,
            build_root=build_root,
            output_directory=output_directory,
        )
        sheets.append(sheet)
        records.append(record)

    group_records: list[dict[str, Any]] = []
    for start in range(0, len(sheets), group_size):
        paths = sheets[start : start + group_size]
        images = [_native_image(path) for path in paths]
        width = sum(image.width for image in images) + GROUP_GAP * (
            len(images) - 1
        )
        height = max(image.height for image in images)
        canvas = Image.new("L", (width, height), 160)
        x = 0
        for image in images:
            canvas.paste(image, (x, 0))
            x += image.width + GROUP_GAP
        first = batch_ids[start]
        last = batch_ids[start + len(paths) - 1]
        output = output_directory / f"group-{first}-{last}.png"
        canvas.save(output, optimize=False)
        group_records.append(
            {
                "first_batch": first,
                "last_batch": last,
                "path": output.relative_to(ROOT).as_posix(),
                "sha256": _sha256(output),
                "width_px": width,
                "height_px": height,
                "batch_contact_sheets": [
                    path.relative_to(ROOT).as_posix() for path in paths
                ],
                "resampled": False,
            }
        )

    manifest = output_directory / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pipeline": pipeline.PIPELINE_ID,
                "purpose": "lossless-manual-review-viewing-aid",
                "batch_count": len(batch_ids),
                "group_size": group_size,
                "batches": records,
                "groups": group_records,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batches", nargs="+")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--group-size", type=int, default=4)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_contact_sheets(
        args.batches,
        build_root=args.build_root.resolve(),
        output_directory=args.output.resolve(),
        group_size=args.group_size,
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
