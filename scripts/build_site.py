#!/usr/bin/env python3
"""Build the dependency-free, multi-font GitHub Pages specimen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any
import unicodedata
import uuid

from fontTools.ttLib import TTFont

from scripts.inventory import han_block
from scripts.moe_common import load_moe_common
from scripts.requirements import RequirementInventoryError, load_requirements


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site"
CATALOG = SOURCE / "catalog.json"
REQUIREMENTS = ROOT / "inventories/font_requirements.json"
DEFAULT_OUTPUT = ROOT / "build/site"
STATIC_FILES = ("index.html", "styles.css", "app.js", "favicon.svg")
SOURCE_ASSET_KEYS = ("ttf", "otf", "woff", "woff2", "report", "license")
RELEASE_FONT_KEYS = ("ttf", "otf", "woff", "woff2", "css")
PROOF_SIZES = (12, 16, 20, 24, 32, 36, 56, 72)
RELEASE_PROOF_PATHS = frozenset(
    {
        f"proof/{polarity}-{size}px.png"
        for polarity in ("black-on-white", "white-on-black")
        for size in PROOF_SIZES
    }
    | {
        "proof/vertical-shaping-black-on-white-56px.png",
        "proof/vertical-shaping-white-on-black-56px.png",
    }
)
PROGRESS_GROUPS = (
    ("letters-phonetics", "字母與音標"),
    ("numbers", "數字"),
    ("punctuation-symbols", "標點與符號"),
    ("bopomofo", "注音"),
    ("kana", "日文假名"),
    ("common-han", "常用漢字"),
    ("uncommon-han", "非常用漢字"),
    ("other", "其他"),
)


class SiteBuildError(RuntimeError):
    """The specimen cannot be emitted without violating its catalog contract."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(value: Any, *, where: str) -> Path:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise SiteBuildError(f"{where} must be a canonical relative path")
    path = Path(value)
    if path.as_posix() != value:
        raise SiteBuildError(f"{where} must be a canonical relative path")
    return path


def _digest(value: Any, *, where: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise SiteBuildError(f"{where} must be a lowercase SHA-256 digest")
    return value


def _assert_no_symlink_components(path: Path, *, where: str) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            raise SiteBuildError(f"{where} must not traverse a symlink: {current}")
        if not current.exists():
            break


def _validated_output_path(
    output: Path,
    *,
    _allow_temporary_output: bool = False,
) -> Path:
    expanded = output.expanduser()
    if any(part in {".", ".."} for part in expanded.parts):
        raise SiteBuildError("output directory must not contain dot segments")
    lexical = Path(os.path.abspath(expanded))
    _assert_no_symlink_components(lexical, where="output directory")
    resolved = lexical.resolve(strict=False)
    repository = ROOT.resolve(strict=True)
    canonical = repository / "build/site"
    temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    protected = {
        Path("/").resolve(strict=True),
        Path.home().resolve(strict=True),
        repository,
        temporary_root,
    }
    if resolved in protected:
        raise SiteBuildError("refusing protected output directory")
    if resolved == canonical:
        pass
    elif not _allow_temporary_output:
        raise SiteBuildError("production output must be canonical build/site")
    elif temporary_root not in resolved.parents:
        raise SiteBuildError(
            "output must be canonical build/site or a system-temp descendant"
        )
    if resolved.exists() and not resolved.is_dir():
        raise SiteBuildError(f"output path is not a directory: {resolved}")
    return resolved


def _report_artifacts(
    identifier: str,
    report: dict[str, Any],
) -> tuple[dict[str, str], dict[str, Path]]:
    if report.get("schema_version") != 1:
        raise SiteBuildError(f"{identifier} report schema_version must be 1")
    font_record = report.get("font")
    license_record = report.get("license")
    proof_records = report.get("proofs")
    inventory = report.get("artifact_sha256")
    if (
        not isinstance(font_record, dict)
        or not isinstance(license_record, dict)
        or not isinstance(proof_records, list)
        or not isinstance(inventory, dict)
    ):
        raise SiteBuildError(f"{identifier} report is missing release records")

    expected: dict[str, str] = {}
    paths: dict[str, Path] = {}

    def admit(relative: Path, digest: str, *, where: str) -> None:
        key = relative.as_posix()
        if key in expected:
            raise SiteBuildError(f"{identifier} report repeats artifact path: {key}")
        expected[key] = digest
        paths[where] = relative

    stems: set[str] = set()
    for key in RELEASE_FONT_KEYS:
        relative = _relative_path(
            font_record.get(key),
            where=f"{identifier} report font.{key}",
        )
        if relative.parent != Path("font") or relative.suffix != f".{key}":
            raise SiteBuildError(
                f"{identifier} report font.{key} has an invalid release path"
            )
        stems.add(relative.name.removesuffix(f".{key}"))
        digest = _digest(
            font_record.get(f"{key}_sha256"),
            where=f"{identifier} report font.{key}_sha256",
        )
        admit(relative, digest, where=key)
    if len(stems) != 1:
        raise SiteBuildError(f"{identifier} release font filenames do not agree")

    license_path = _relative_path(
        license_record.get("path"),
        where=f"{identifier} report license.path",
    )
    if license_path != Path("OFL.txt"):
        raise SiteBuildError(f"{identifier} report license path must be OFL.txt")
    admit(
        license_path,
        _digest(
            license_record.get("sha256"),
            where=f"{identifier} report license.sha256",
        ),
        where="license",
    )

    proof_paths: set[str] = set()
    for index, proof in enumerate(proof_records):
        if not isinstance(proof, dict):
            raise SiteBuildError(f"{identifier} report proof {index} is invalid")
        relative = _relative_path(
            proof.get("path"),
            where=f"{identifier} report proof {index}.path",
        )
        digest = _digest(
            proof.get("sha256"),
            where=f"{identifier} report proof {index}.sha256",
        )
        proof_paths.add(relative.as_posix())
        admit(relative, digest, where=f"proof:{index}")
    if proof_paths != RELEASE_PROOF_PATHS:
        raise SiteBuildError(
            f"{identifier} report has an incomplete formal proof inventory"
        )

    declared: dict[str, str] = {}
    for raw_path, raw_digest in inventory.items():
        relative = _relative_path(
            raw_path,
            where=f"{identifier} report artifact_sha256 key",
        )
        key = relative.as_posix()
        if key in declared:
            raise SiteBuildError(f"{identifier} report repeats inventory path: {key}")
        declared[key] = _digest(
            raw_digest,
            where=f"{identifier} report artifact_sha256[{key!r}]",
        )
    if declared != expected:
        raise SiteBuildError(
            f"{identifier} report artifact inventory does not match release records"
        )
    return expected, paths


def _validate_release(font: dict[str, Any]) -> dict[str, Any]:
    identifier = font["id"]
    release_root = ROOT / "dist" / identifier
    report_path = release_root / "report.json"
    expected_report_source = Path("dist") / identifier / "report.json"
    catalog_report_source = _relative_path(
        font["sources"]["report"],
        where=f"{identifier} catalog report source",
    )
    if catalog_report_source != expected_report_source:
        raise SiteBuildError(
            f"{identifier} catalog report must be family-namespaced"
        )
    _assert_no_symlink_components(release_root, where=f"{identifier} release")
    _assert_no_symlink_components(
        report_path,
        where=f"{identifier} release report",
    )
    if not report_path.is_file():
        raise SiteBuildError(f"{identifier} is missing release report: {report_path}")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SiteBuildError(f"{identifier} release report is unreadable") from error
    if not isinstance(report, dict):
        raise SiteBuildError(f"{identifier} release report must be an object")
    artifact_hashes, report_paths = _report_artifacts(identifier, report)

    expected_catalog_sources = {
        key: (
            expected_report_source
            if key == "report"
            else Path("dist") / identifier / report_paths[key]
        )
        for key in SOURCE_ASSET_KEYS
    }
    actual_catalog_sources = {
        key: _relative_path(
            font["sources"][key],
            where=f"{identifier} catalog {key} source",
        )
        for key in SOURCE_ASSET_KEYS
    }
    if actual_catalog_sources != expected_catalog_sources:
        raise SiteBuildError(
            f"{identifier} catalog sources do not match its release report"
        )

    entries = list(release_root.rglob("*"))
    symlinks = [path for path in entries if path.is_symlink()]
    if symlinks:
        raise SiteBuildError(
            f"{identifier} release contains symlinks: "
            + ", ".join(path.as_posix() for path in symlinks)
        )
    actual_files = {
        path.relative_to(release_root).as_posix()
        for path in entries
        if path.is_file()
    }
    expected_files = set(artifact_hashes) | {"report.json"}
    if actual_files != expected_files:
        raise SiteBuildError(
            f"{identifier} release directory does not match report inventory"
        )
    for relative, expected_digest in artifact_hashes.items():
        path = release_root / relative
        if _sha256(path) != expected_digest:
            raise SiteBuildError(
                f"{identifier} release artifact SHA-256 mismatch: {relative}"
            )
    return {
        "root": release_root,
        "report": report_path,
        "report_sha256": _sha256(report_path),
        "artifact_sha256": artifact_hashes,
        "paths": report_paths,
    }


def _load_catalog(path: Path = CATALOG) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise SiteBuildError("catalog schema_version must be 1")
    fonts = payload.get("fonts")
    if not isinstance(fonts, list) or not fonts:
        raise SiteBuildError("catalog must contain at least one font")
    ids: set[str] = set()
    for font in fonts:
        required = {
            "id",
            "family",
            "style",
            "version",
            "opentype_version",
            "status",
            "tagline",
            "description",
            "sample",
            "paragraph",
            "encoded_count",
            "vertical_alternates",
            "license",
            "features",
            "sources",
        }
        if not isinstance(font, dict) or set(font) != required:
            raise SiteBuildError("font catalog entry has an invalid key set")
        identifier = font["id"]
        if (
            not isinstance(identifier, str)
            or not identifier
            or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in identifier)
            or identifier in ids
        ):
            raise SiteBuildError(f"invalid or duplicate font id: {identifier!r}")
        ids.add(identifier)
        if (
            not isinstance(font["features"], list)
            or not font["features"]
            or set(font["sources"]) != set(SOURCE_ASSET_KEYS)
        ):
            raise SiteBuildError(f"invalid features or sources for {identifier}")
    return payload


def _ranges(codepoints: list[int]) -> list[list[int]]:
    if not codepoints:
        return []
    result: list[list[int]] = []
    start = previous = codepoints[0]
    for codepoint in codepoints[1:]:
        if codepoint == previous + 1:
            previous = codepoint
            continue
        result.append([start, previous])
        start = previous = codepoint
    result.append([start, previous])
    return result


def _progress_group(codepoint: int, moe_common: set[int]) -> str:
    character = chr(codepoint)
    if han_block(character) is not None:
        return "common-han" if codepoint in moe_common else "uncommon-han"
    if (
        0x3040 <= codepoint <= 0x30FF
        or 0x31F0 <= codepoint <= 0x31FF
    ):
        return "kana"
    if (
        0x3100 <= codepoint <= 0x312F
        or 0x31A0 <= codepoint <= 0x31BF
    ):
        return "bopomofo"
    category = unicodedata.category(character)
    if category.startswith("N"):
        return "numbers"
    if category[0] in {"P", "S"}:
        return "punctuation-symbols"
    if (
        category.startswith("L")
        or 0x0250 <= codepoint <= 0x02FF
        or 0x0300 <= codepoint <= 0x036F
    ):
        return "letters-phonetics"
    return "other"


def _coverage_progress(codepoints: set[int]) -> dict[str, Any]:
    try:
        required, _, _ = load_requirements(REQUIREMENTS)
    except RequirementInventoryError as error:
        raise SiteBuildError(
            f"invalid frozen requirement inventory: {error}"
        ) from error
    if not codepoints <= required:
        raise SiteBuildError("compiled font contains codepoints outside requirements")
    moe_common = {
        record.codepoint for record in load_moe_common()
    }
    if not moe_common <= required:
        raise SiteBuildError("Ministry common characters fall outside requirements")

    groups: list[dict[str, Any]] = []
    for identifier, label in PROGRESS_GROUPS:
        target = {
            codepoint
            for codepoint in required
            if _progress_group(codepoint, moe_common) == identifier
        }
        encoded_count = len(codepoints & target)
        target_count = len(target)
        groups.append(
            {
                "id": identifier,
                "label": label,
                "encoded_count": encoded_count,
                "target_count": target_count,
                "missing_count": target_count - encoded_count,
                "percent": round(encoded_count / target_count * 100, 6),
            }
        )

    encoded_count = len(codepoints)
    target_count = len(required)
    return {
        "encoded_count": encoded_count,
        "target_count": target_count,
        "missing_count": target_count - encoded_count,
        "percent": round(encoded_count / target_count * 100, 6),
        "groups": groups,
    }


def _copy_font(font: dict[str, Any], staging: Path) -> dict[str, Any]:
    identifier = font["id"]
    release = _validate_release(font)
    ttf_path = release["root"] / release["paths"]["ttf"]
    with TTFont(ttf_path, lazy=False, recalcTimestamp=False) as ttfont:
        codepoints = sorted(ttfont.getBestCmap())
        family = ttfont["name"].getDebugName(1)
        version = ttfont["name"].getDebugName(5)
    if len(codepoints) != font["encoded_count"]:
        raise SiteBuildError(
            f"{identifier} declares {font['encoded_count']} codepoints, "
            f"compiled font has {len(codepoints)}"
        )
    if (
        family != font["family"]
        or version
        != f"Version {float(font['opentype_version']):.3f}"
    ):
        raise SiteBuildError(
            f"{identifier} catalog identity does not match compiled font"
        )

    asset_directory = staging / "fonts" / identifier
    asset_directory.mkdir(parents=True)
    public_assets: dict[str, str] = {}
    for key in SOURCE_ASSET_KEYS:
        relative = (
            Path("report.json")
            if key == "report"
            else release["paths"][key]
        )
        source = (
            release["report"]
            if key == "report"
            else release["root"] / relative
        )
        destination = asset_directory / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        expected_digest = (
            release["report_sha256"]
            if key == "report"
            else release["artifact_sha256"][relative.as_posix()]
        )
        if _sha256(destination) != expected_digest:
            raise SiteBuildError(
                f"{identifier} copied artifact SHA-256 mismatch: {relative}"
            )
        public_assets[key] = destination.relative_to(staging).as_posix()

    coverage_path = staging / "coverage" / f"{identifier}.json"
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage = {
        "schema_version": 1,
        "font_id": identifier,
        "encoded_count": len(codepoints),
        "ranges": _ranges(codepoints),
    }
    coverage_path.write_text(
        json.dumps(coverage, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    public = {key: value for key, value in font.items() if key != "sources"}
    public["coverage_url"] = coverage_path.relative_to(staging).as_posix()
    public["coverage_progress"] = _coverage_progress(set(codepoints))
    public["assets"] = public_assets
    return public


def _install_directory(
    staging: Path,
    output: Path,
    *,
    _allow_temporary_output: bool = False,
) -> None:
    validated_output = _validated_output_path(
        output,
        _allow_temporary_output=_allow_temporary_output,
    )
    if validated_output != output:
        raise SiteBuildError("site output must use its validated absolute path")
    if (
        staging.parent.resolve(strict=True)
        != validated_output.parent.resolve(strict=True)
        or staging.is_symlink()
        or not staging.is_dir()
    ):
        raise SiteBuildError("site staging directory must be a real sibling")
    if validated_output.is_symlink() or (
        validated_output.exists() and not validated_output.is_dir()
    ):
        raise SiteBuildError("site output must be a real directory")
    if not validated_output.exists():
        try:
            staging.rename(validated_output)
        except OSError as error:
            raise SiteBuildError("atomic site directory install failed") from error
        return

    backup = validated_output.with_name(
        f".{validated_output.name}.rollback-{uuid.uuid4().hex}"
    )
    if backup.exists() or backup.is_symlink():
        raise SiteBuildError("could not allocate a site rollback path")
    try:
        validated_output.rename(backup)
    except OSError as error:
        raise SiteBuildError(
            "could not move the existing site to its rollback path"
        ) from error
    try:
        staging.rename(validated_output)
    except OSError as install_error:
        try:
            backup.rename(validated_output)
        except OSError as rollback_error:
            raise SiteBuildError(
                "site install failed and rollback failed; "
                f"the previous site is preserved at {backup}"
            ) from rollback_error
        raise SiteBuildError(
            "site install failed; the previous site was restored"
        ) from install_error
    try:
        shutil.rmtree(backup)
    except OSError as error:
        raise SiteBuildError(
            f"new site installed but obsolete rollback remains: {backup}"
        ) from error


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    _allow_temporary_output: bool = False,
) -> Path:
    output = _validated_output_path(
        output,
        _allow_temporary_output=_allow_temporary_output,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_components(output, where="output directory")
    catalog = _load_catalog()
    with tempfile.TemporaryDirectory(
        prefix=f".{output.name}-",
        dir=output.parent,
    ) as temporary:
        staging = Path(temporary)
        for filename in STATIC_FILES:
            source = SOURCE / filename
            _assert_no_symlink_components(source, where="static site source")
            if not source.is_file():
                raise SiteBuildError(f"missing static source: {source}")
            shutil.copyfile(source, staging / filename)
        public_fonts = [
            _copy_font(font, staging)
            for font in catalog["fonts"]
        ]
        (staging / "fonts.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fonts": public_fonts,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (staging / ".nojekyll").write_text("", encoding="utf-8")
        _install_directory(
            staging,
            output,
            _allow_temporary_output=_allow_temporary_output,
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    output = build(arguments.output)
    print(f"built GitHub Pages specimen: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
