#!/usr/bin/env python3
"""Build the exact 17 empty non-Han glyphs and their review evidence.

The semantic batch is intentionally separate from raster authoring.  These
Unicode scalars are defined to carry spacing or text-control semantics without
ink, so generating or vectorizing a visible placeholder would be incorrect.
Two advances (FIGURE SPACE and PUNCTUATION SPACE) are resolved from already
approved imagegen glyphs and hash-pinned in the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping, Sequence

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from PIL import Image

from scripts import imagegen_nonhan_approval as approval


ROOT = approval.ROOT
OUTPUT_DIRECTORY = (
    ROOT / "build/imagegen/imagegen-nonhan-0206"
)
MANIFEST_PATH = (
    ROOT / "sources/imagegen/semantic/nonhan-0206.semantic.json"
)

UPM = 1024
ASCENDER = 928
DESCENDER = -96
VERTICAL_ORIGIN_Y = 880
REPRODUCIBLE_HEAD_TIMESTAMP = 2_082_844_800
FONT_NAME = "ClearHandTC-NonHan0206-Semantic"


class SemanticEvidenceBuildError(RuntimeError):
    """The empty-glyph evidence cannot be built from approved inputs."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _empty_glyph() -> Glyph:
    return TTGlyphPen(None).glyph()


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


def _glyph_name(codepoint: int) -> str:
    if not 0 <= codepoint <= 0xFFFF:
        raise SemanticEvidenceBuildError(
            f"semantic glyph U+{codepoint:04X} is outside the canonical BMP set"
        )
    return f"uni{codepoint:04X}"


def _project_relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise SemanticEvidenceBuildError(
            f"evidence path escapes project root: {path}"
        ) from exc


def _visible_advance(
    validated: approval.ValidatedApproval,
    codepoint: int,
) -> int:
    evidence = validated.visible_evidence
    if evidence is None:
        raise SemanticEvidenceBuildError(
            f"{validated.batch.batch_id} is not visible reference evidence"
        )
    matches = [
        record
        for record in evidence.report["glyphs"]
        if record["codepoint"] == f"U+{codepoint:04X}"
    ]
    if len(matches) != 1:
        raise SemanticEvidenceBuildError(
            f"{validated.batch.batch_id} does not contain exactly one "
            f"U+{codepoint:04X} metric"
        )
    value = matches[0]["metrics"]["horizontal_advance"]
    if isinstance(value, bool) or not isinstance(value, int):
        raise SemanticEvidenceBuildError(
            f"U+{codepoint:04X} reference advance is not an integer"
        )
    if not 0 <= value <= 4096:
        raise SemanticEvidenceBuildError(
            f"U+{codepoint:04X} reference advance is out of range"
        )
    return value


def _resolve_references(
    *,
    project_root: Path,
    repertoire: approval.Repertoire,
    batch: approval.RepertoireBatch,
) -> tuple[dict[int, int], list[dict[str, Any]]]:
    targets = sorted(
        {
            int(glyph.metrics["horizontal_advance"]["codepoint"][2:], 16)
            for glyph in batch.glyphs
            if glyph.metrics["horizontal_advance"]["kind"] == "reference"
        }
    )
    values: dict[int, int] = {}
    records: list[dict[str, Any]] = []
    for codepoint in targets:
        source_batch = next(
            candidate
            for candidate in repertoire.batches[: approval.VISIBLE_BATCHES]
            if any(glyph.codepoint == codepoint for glyph in candidate.glyphs)
        )
        path = (
            project_root
            / "sources/imagegen/approvals"
            / f"{source_batch.batch_id}.approval.json"
        )
        if not path.is_file():
            raise SemanticEvidenceBuildError(
                f"missing approved metric reference: {path}"
            )
        validated = approval.validate_approval(
            path,
            project_root=project_root,
            repertoire=repertoire,
        )
        advance = _visible_advance(validated, codepoint)
        values[codepoint] = advance
        records.append(
            {
                "codepoint": f"U+{codepoint:04X}",
                "horizontal_advance": advance,
                "source_approval": {
                    "path": _project_relative(path, project_root),
                    "sha256": _sha256(path),
                },
            }
        )
    return values, records


def _horizontal_advance(
    glyph: approval.RepertoireGlyph,
    references: Mapping[int, int],
) -> int:
    policy = glyph.metrics["horizontal_advance"]
    if policy["kind"] == "fixed":
        return int(policy["value"])
    if policy["kind"] == "reference":
        target = int(policy["codepoint"][2:], 16)
        if target not in references:
            raise SemanticEvidenceBuildError(
                f"{glyph.codepoint_label}: unresolved U+{target:04X} advance"
            )
        return references[target]
    raise SemanticEvidenceBuildError(
        f"{glyph.codepoint_label}: semantic glyph cannot be source-proportional"
    )


def _font_builder(
    batch: approval.RepertoireBatch,
    references: Mapping[int, int],
) -> FontBuilder:
    glyph_names = [_glyph_name(glyph.codepoint) for glyph in batch.glyphs]
    order = [".notdef", *glyph_names]
    outlines = {".notdef": _notdef_glyph()}
    outlines.update({name: _empty_glyph() for name in glyph_names})
    hmetrics = {".notdef": (UPM, 96)}
    vmetrics = {
        ".notdef": (UPM, VERTICAL_ORIGIN_Y - 896),
    }
    for glyph, name in zip(batch.glyphs, glyph_names, strict=True):
        hmetrics[name] = (_horizontal_advance(glyph, references), 0)
        vmetrics[name] = (
            int(glyph.metrics["vertical_advance"]["value"]),
            0,
        )

    builder = FontBuilder(UPM, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(
        {
            glyph.codepoint: name
            for glyph, name in zip(batch.glyphs, glyph_names, strict=True)
        }
    )
    builder.setupGlyf(outlines)
    builder.setupHorizontalMetrics(hmetrics)
    builder.setupVerticalMetrics(vmetrics)
    builder.setupHorizontalHeader(
        ascent=ASCENDER,
        descent=DESCENDER,
        lineGap=0,
    )
    builder.setupVerticalHeader(ascent=500, descent=-500, lineGap=0)
    builder.setupNameTable(
        {
            "familyName": "Clear Hand TC NonHan 0206 Semantic",
            "styleName": "Regular",
            "uniqueFontIdentifier": (
                "Clear Hand TC NonHan 0206 Semantic 1.000"
            ),
            "fullName": "Clear Hand TC NonHan 0206 Semantic Regular",
            "psName": FONT_NAME,
            "version": "Version 1.000",
            "copyright": "Copyright 2026 The CodexFont Project Authors",
            "licenseDescription": (
                "This Font Software is licensed under the SIL Open Font "
                "License, Version 1.1."
            ),
            "licenseInfoURL": "https://openfontlicense.org",
        }
    )
    builder.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=0,
        usWinAscent=960,
        usWinDescent=112,
        achVendID="CDFT",
        fsType=0,
    )
    builder.setupPost(keepGlyphNames=True)
    builder.setupMaxp()
    builder.font["head"].created = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font["head"].modified = REPRODUCIBLE_HEAD_TIMESTAMP
    builder.font.recalcTimestamp = False
    return builder


def _repertoire_payload(
    repertoire: approval.Repertoire,
    batch: approval.RepertoireBatch,
) -> dict[str, Any]:
    return {
        "path": approval.REPERTOIRE_RELATIVE_PATH.as_posix(),
        "sha256": repertoire.sha256,
        "repertoire_id": repertoire.repertoire_id,
        "batch_id": batch.batch_id,
        "start_authoring_rank": batch.start_authoring_rank,
        "end_authoring_rank": batch.end_authoring_rank,
        "glyph_codepoints": [
            glyph.codepoint_label for glyph in batch.glyphs
        ],
    }


def _manifest_glyphs(
    batch: approval.RepertoireBatch,
    references: Mapping[int, int],
) -> list[dict[str, Any]]:
    return [
        {
            "authoring_rank": glyph.authoring_rank,
            "character": glyph.character,
            "codepoint": glyph.codepoint_label,
            "name": glyph.name,
            "gc": glyph.general_category,
            "profile_id": glyph.profile_id,
            "metrics": glyph.metrics,
            "glyph_name": _glyph_name(glyph.codepoint),
            "resolved_horizontal_advance": _horizontal_advance(
                glyph, references
            ),
        }
        for glyph in batch.glyphs
    ]


def _validate_written_font(
    path: Path,
    *,
    batch: approval.RepertoireBatch,
    references: Mapping[int, int],
) -> None:
    font = TTFont(path, lazy=False, checkChecksums=2, recalcTimestamp=False)
    try:
        expected_order = [
            ".notdef", *(_glyph_name(glyph.codepoint) for glyph in batch.glyphs)
        ]
        if font.getGlyphOrder() != expected_order:
            raise SemanticEvidenceBuildError("semantic glyph order drifted")
        if font.getBestCmap() != {
            glyph.codepoint: _glyph_name(glyph.codepoint)
            for glyph in batch.glyphs
        }:
            raise SemanticEvidenceBuildError("semantic cmap drifted")
        for glyph in batch.glyphs:
            name = _glyph_name(glyph.codepoint)
            if font["glyf"][name].numberOfContours != 0:
                raise SemanticEvidenceBuildError(
                    f"{glyph.codepoint_label}: semantic outline is not empty"
                )
            expected_h = (_horizontal_advance(glyph, references), 0)
            expected_v = (
                int(glyph.metrics["vertical_advance"]["value"]),
                0,
            )
            if font["hmtx"].metrics[name] != expected_h:
                raise SemanticEvidenceBuildError(
                    f"{glyph.codepoint_label}: hmtx drifted"
                )
            if font["vmtx"].metrics[name] != expected_v:
                raise SemanticEvidenceBuildError(
                    f"{glyph.codepoint_label}: vmtx drifted"
                )
    finally:
        font.close()


def build_semantic_evidence(
    *,
    project_root: Path = ROOT,
    output_directory: Path = OUTPUT_DIRECTORY,
    manifest_path: Path = MANIFEST_PATH,
) -> Path:
    """Create and validate the canonical semantic evidence manifest."""

    project_root = project_root.resolve()
    output_directory = output_directory.resolve()
    manifest_path = manifest_path.resolve()
    expected_output = (
        project_root / "build/imagegen/imagegen-nonhan-0206"
    ).resolve()
    expected_manifest = (
        project_root
        / "sources/imagegen/semantic/nonhan-0206.semantic.json"
    ).resolve()
    if output_directory != expected_output:
        raise SemanticEvidenceBuildError(
            f"output directory must be exactly {expected_output}"
        )
    if manifest_path != expected_manifest:
        raise SemanticEvidenceBuildError(
            f"manifest path must be exactly {expected_manifest}"
        )

    repertoire = approval.load_frozen_repertoire(project_root)
    batch = approval.batch_from_repertoire(
        repertoire, approval.SEMANTIC_BATCH_ID
    )
    if batch.batch_kind != "semantic-empty" or len(batch.glyphs) != 17:
        raise SemanticEvidenceBuildError("canonical semantic batch changed")
    references, reference_records = _resolve_references(
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
    )

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=".imagegen-nonhan-0206-",
            dir=output_directory.parent,
        )
    )
    try:
        font_path = stage / "font" / f"{FONT_NAME}.ttf"
        font_path.parent.mkdir(parents=True)
        _font_builder(batch, references).save(font_path)
        _validate_written_font(
            font_path, batch=batch, references=references
        )

        proof_path = stage / "proof/blank-render.png"
        proof_path.parent.mkdir(parents=True)
        Image.new("L", (320, 64), 255).save(
            proof_path,
            format="PNG",
            optimize=False,
        )
        with Image.open(proof_path) as image:
            image.load()
            if (
                image.mode != "L"
                or image.size != (320, 64)
                or image.getextrema() != (255, 255)
                or image.text
            ):
                raise SemanticEvidenceBuildError(
                    "blank render proof is not exact white grayscale evidence"
                )

        if output_directory.exists():
            shutil.rmtree(output_directory)
        stage.replace(output_directory)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise

    final_font = (
        output_directory / "font" / f"{FONT_NAME}.ttf"
    )
    final_proof = output_directory / "proof/blank-render.png"
    manifest = {
        "schema_version": 1,
        "record_type": approval.SEMANTIC_RECORD_TYPE,
        "batch_id": batch.batch_id,
        "repertoire": _repertoire_payload(repertoire, batch),
        "font": {
            "path": _project_relative(final_font, project_root),
            "sha256": _sha256(final_font),
            "format": "TrueType quadratic glyf",
        },
        "blank_render_proof": {
            "path": _project_relative(final_proof, project_root),
            "sha256": _sha256(final_proof),
            "format": "PNG",
            "mode": "L",
            "size": [320, 64],
            "sizes_px": list(approval.SMALL_SIZE_PIXELS),
            "expected_ink_pixels": 0,
        },
        "reference_metrics": reference_records,
        "glyphs": _manifest_glyphs(batch, references),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest = manifest_path.with_suffix(
        ".semantic.json.tmp"
    )
    temporary_manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(manifest_path)

    # Re-run the independent admission validator on the exact installed bytes.
    approval.semantic_evidence(
        project_root=project_root,
        repertoire=repertoire,
        batch=batch,
    )
    return manifest_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=ROOT,
        help="project root containing the frozen repertoire and approvals",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    path = build_semantic_evidence(
        project_root=args.project_root,
        output_directory=(
            args.project_root / "build/imagegen/imagegen-nonhan-0206"
        ),
        manifest_path=(
            args.project_root
            / "sources/imagegen/semantic/nonhan-0206.semantic.json"
        ),
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
