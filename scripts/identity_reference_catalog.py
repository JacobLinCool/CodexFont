#!/usr/bin/env python3
"""Admit exact local-font glyphs for identity-only copybook rendering."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTCollection, TTFont, TTLibError
from PIL import ImageFont


FORBIDDEN_REFERENCE_PATH_PARTS = frozenset({"authored"})
FORBIDDEN_REFERENCE_FILENAMES = frozenset({"lastresort.otf"})
DEFAULT_REFERENCE_FONTS: tuple[Path, ...] = (
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/STIXTwoMath.otf"),
    Path.home() / "Library/Fonts/NotoSansJP-VariableFont_wght.ttf",
    Path("/System/Library/Fonts/LucidaGrande.ttc"),
    Path("/System/Library/Fonts/Apple Symbols.ttf"),
    Path("/System/Library/Fonts/SFNS.ttf"),
)


class IdentityReferenceCatalogError(RuntimeError):
    """A local font face cannot prove one requested scalar identity."""


class ReferenceGlyph(Protocol):
    """Minimum glyph identity consumed by the admission catalog."""

    character: str
    codepoint: int
    codepoint_label: str


@dataclass(frozen=True)
class ReferenceFace:
    """One local font face with verified non-tofu cmap entries."""

    path: Path
    manifest_path: str
    file_sha256: str
    face_index: int
    postscript_name: str
    glyphs: Mapping[int, str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _font_face_count(path: Path) -> int:
    if path.suffix.lower() not in {".ttc", ".otc"}:
        return 1
    try:
        collection = TTCollection(path, lazy=True)
    except (OSError, TTLibError) as exc:
        raise IdentityReferenceCatalogError(
            f"{path}: cannot open font collection: {exc}"
        ) from exc
    try:
        return len(collection.fonts)
    finally:
        collection.close()


def _open_font_face(path: Path, face_index: int) -> TTFont:
    try:
        return TTFont(path, fontNumber=face_index, lazy=True)
    except (OSError, TTLibError) as exc:
        raise IdentityReferenceCatalogError(
            f"{path} face {face_index}: cannot open font: {exc}"
        ) from exc


def _outline_recording(
    font: TTFont,
    glyph_name: str,
) -> tuple[tuple[str, tuple[Any, ...]], ...]:
    glyph_set = font.getGlyphSet()
    if glyph_name not in glyph_set:
        return ()
    pen = RecordingPen()
    try:
        glyph_set[glyph_name].draw(pen)
    except Exception:
        return ()
    return tuple(
        (operator, tuple(operands))
        for operator, operands in pen.value
    )


def _postscript_name(
    font: TTFont,
    *,
    path: Path,
    face_index: int,
) -> str:
    if "name" not in font:
        return f"{path.name}#{face_index}"
    value = font["name"].getDebugName(6) or font["name"].getDebugName(1)
    return value or f"{path.name}#{face_index}"


@lru_cache(maxsize=256)
def pillow_font(
    path: str,
    face_index: int,
    size: int,
) -> ImageFont.FreeTypeFont:
    """Open one cached Pillow face with deterministic basic layout."""

    try:
        return ImageFont.truetype(
            path,
            size=size,
            index=face_index,
            layout_engine=ImageFont.Layout.BASIC,
        )
    except (OSError, ValueError) as exc:
        raise IdentityReferenceCatalogError(
            f"{path} face {face_index}: Pillow cannot open the font: {exc}"
        ) from exc


def _pillow_has_ink(
    path: Path,
    face_index: int,
    character: str,
) -> bool:
    font = pillow_font(str(path), face_index, 256)
    try:
        return font.getmask(character, mode="L").getbbox() is not None
    except (OSError, ValueError):
        return False


def load_reference_faces(
    required_codepoints: Iterable[int],
    font_paths: Sequence[Path] = DEFAULT_REFERENCE_FONTS,
) -> tuple[ReferenceFace, ...]:
    """Build a deterministic, exact-cmap, non-tofu reference catalog."""

    required = frozenset(required_codepoints)
    if not required:
        raise IdentityReferenceCatalogError(
            "reference font catalog cannot be empty"
        )
    resolved_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for raw_path in font_paths:
        path = raw_path.expanduser().resolve()
        if path in seen_paths:
            raise IdentityReferenceCatalogError(
                f"duplicate reference font path: {path}"
            )
        seen_paths.add(path)
        if path.name.lower() in FORBIDDEN_REFERENCE_FILENAMES:
            raise IdentityReferenceCatalogError(
                f"{path}: LastResort/tofu fonts are forbidden"
            )
        if any(
            part.lower() in FORBIDDEN_REFERENCE_PATH_PARTS
            for part in path.parts
        ):
            raise IdentityReferenceCatalogError(
                f"{path}: sources/authored may not be reference fonts"
            )
        if not path.is_file():
            raise IdentityReferenceCatalogError(
                f"{path}: reference font is missing"
            )
        resolved_paths.append(path)

    faces: list[ReferenceFace] = []
    for path in resolved_paths:
        file_hash = _sha256(path)
        for face_index in range(_font_face_count(path)):
            font = _open_font_face(path, face_index)
            try:
                cmap = font.getBestCmap() or {}
                notdef_recording = (
                    _outline_recording(font, ".notdef")
                    if ".notdef" in font.getGlyphOrder()
                    else ()
                )
                accepted: dict[int, str] = {}
                for codepoint in sorted(required.intersection(cmap)):
                    glyph_name = cmap[codepoint]
                    if glyph_name in {
                        ".notdef",
                        ".null",
                        "nonmarkingreturn",
                    }:
                        continue
                    recording = _outline_recording(font, glyph_name)
                    if not recording or (
                        notdef_recording
                        and recording == notdef_recording
                    ):
                        continue
                    if not _pillow_has_ink(
                        path,
                        face_index,
                        chr(codepoint),
                    ):
                        continue
                    accepted[codepoint] = glyph_name
                if accepted:
                    faces.append(
                        ReferenceFace(
                            path=path,
                            manifest_path=str(path),
                            file_sha256=file_hash,
                            face_index=face_index,
                            postscript_name=_postscript_name(
                                font,
                                path=path,
                                face_index=face_index,
                            ),
                            glyphs=accepted,
                        )
                    )
            finally:
                font.close()
    if not faces:
        raise IdentityReferenceCatalogError(
            "no valid local reference font faces were found"
        )
    return tuple(faces)


def select_references(
    glyphs: Iterable[ReferenceGlyph],
    faces: Sequence[ReferenceFace],
) -> dict[int, dict[str, Any]]:
    """Select the first admitted face for every requested scalar."""

    references: dict[int, dict[str, Any]] = {}
    missing: list[ReferenceGlyph] = []
    for glyph in glyphs:
        face = next(
            (
                candidate
                for candidate in faces
                if glyph.codepoint in candidate.glyphs
            ),
            None,
        )
        if face is None:
            missing.append(glyph)
            continue
        references[glyph.codepoint] = {
            "role": "identity-reference-only-no-outline-import",
            "font_path": face.manifest_path,
            "font_sha256": face.file_sha256,
            "font_index": face.face_index,
            "postscript_name": face.postscript_name,
            "glyph_name": face.glyphs[glyph.codepoint],
            "validation": [
                "exact-cmap-hit",
                "non-notdef-glyph-name",
                "non-empty-distinct-outline",
                "non-empty-pillow-raster",
            ],
        }
    if missing:
        labels = " ".join(
            glyph.codepoint_label for glyph in missing
        )
        raise IdentityReferenceCatalogError(
            "no verified local reference glyph for "
            f"{len(missing)} codepoints: {labels}"
        )
    return references
