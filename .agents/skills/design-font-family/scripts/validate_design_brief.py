#!/usr/bin/env python3
"""Validate the durable contract required by the design-font-family skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


class BriefError(ValueError):
    """The design brief is incomplete or structurally unsafe."""


def _object(value: Any, *, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BriefError(f"{where} must be an object")
    return value


def _nonempty_text(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BriefError(f"{where} must be non-empty text")
    return value.strip()


def _nonempty_text_list(value: Any, *, where: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise BriefError(f"{where} must be a non-empty array")
    return [
        _nonempty_text(item, where=f"{where}[{index}]")
        for index, item in enumerate(value)
    ]


def validate(payload: Any) -> None:
    top = _object(payload, where="brief")
    required = {
        "schema_version",
        "project_id",
        "family",
        "intent",
        "design_contract",
        "repertoire",
        "references",
        "licensing",
        "acceptance",
    }
    if set(top) != required:
        raise BriefError(
            f"brief fields must be exact; missing={sorted(required - set(top))}, "
            f"extra={sorted(set(top) - required)}"
        )
    if top["schema_version"] != 1:
        raise BriefError("schema_version must be 1")
    project_id = _nonempty_text(top["project_id"], where="project_id")
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_id) is None:
        raise BriefError("project_id must use lowercase hyphen-case")

    family = _object(top["family"], where="family")
    if set(family) != {"name", "style", "version"}:
        raise BriefError("family fields must be name, style, and version")
    _nonempty_text(family["name"], where="family.name")
    _nonempty_text(family["style"], where="family.style")
    version = _nonempty_text(family["version"], where="family.version")
    if re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{3}", version) is None:
        raise BriefError(
            "family.version must use OpenType form such as 0.100 or 1.000"
        )

    intent = _object(top["intent"], where="intent")
    if set(intent) != {
        "use_cases",
        "audiences",
        "personality",
        "non_goals",
        "example_text",
    }:
        raise BriefError("intent fields are incomplete or unknown")
    for key in intent:
        _nonempty_text_list(intent[key], where=f"intent.{key}")

    contract = _object(top["design_contract"], where="design_contract")
    expected_contract = {
        "authoring_mode",
        "stroke_model",
        "spacing_model",
        "units_per_em",
        "directions",
        "required_features",
    }
    if set(contract) != expected_contract:
        raise BriefError("design_contract fields are incomplete or unknown")
    if contract["authoring_mode"] != "original-raster-first":
        raise BriefError("authoring_mode must be original-raster-first")
    _nonempty_text(contract["stroke_model"], where="design_contract.stroke_model")
    if contract["spacing_model"] not in {"proportional", "monospace"}:
        raise BriefError("spacing_model must be proportional or monospace")
    if (
        not isinstance(contract["units_per_em"], int)
        or isinstance(contract["units_per_em"], bool)
        or not (
        256 <= contract["units_per_em"] <= 16384
        )
    ):
        raise BriefError("units_per_em must be an integer from 256 to 16384")
    _nonempty_text_list(contract["directions"], where="design_contract.directions")
    _nonempty_text_list(
        contract["required_features"],
        where="design_contract.required_features",
    )

    repertoire = _object(top["repertoire"], where="repertoire")
    expected_repertoire = {
        "unicode_version",
        "normalization",
        "sources",
        "semantic_empty_policy",
        "unencoded_alternates",
    }
    if set(repertoire) != expected_repertoire:
        raise BriefError("repertoire fields are incomplete or unknown")
    _nonempty_text(repertoire["unicode_version"], where="repertoire.unicode_version")
    if repertoire["normalization"] not in {"none", "NFC", "NFD"}:
        raise BriefError("repertoire.normalization must be none, NFC, or NFD")
    if not isinstance(repertoire["sources"], list) or not repertoire["sources"]:
        raise BriefError("repertoire.sources must be non-empty")
    for index, raw in enumerate(repertoire["sources"]):
        source = _object(raw, where=f"repertoire.sources[{index}]")
        if set(source) != {"id", "authority", "ordered_codepoints_path"}:
            raise BriefError(f"repertoire.sources[{index}] fields are not exact")
        for key in source:
            _nonempty_text(source[key], where=f"repertoire.sources[{index}].{key}")
    _nonempty_text(
        repertoire["semantic_empty_policy"],
        where="repertoire.semantic_empty_policy",
    )
    if not isinstance(repertoire["unencoded_alternates"], list):
        raise BriefError("repertoire.unencoded_alternates must be an array")

    references = top["references"]
    if not isinstance(references, list):
        raise BriefError("references must be an array")
    for index, raw in enumerate(references):
        reference = _object(raw, where=f"references[{index}]")
        if set(reference) != {
            "description",
            "role",
            "license",
            "outline_import_allowed",
        }:
            raise BriefError(f"references[{index}] fields are not exact")
        _nonempty_text(reference["description"], where=f"references[{index}].description")
        _nonempty_text(reference["license"], where=f"references[{index}].license")
        if reference["role"] not in {
            "identity-reference-only-no-outline-import",
            "style-reference-only-no-outline-import",
        }:
            raise BriefError(f"references[{index}].role is not allowed")
        if reference["outline_import_allowed"] is not False:
            raise BriefError(f"references[{index}] must prohibit outline import")

    licensing = _object(top["licensing"], where="licensing")
    if set(licensing) != {"source_license", "release_license"}:
        raise BriefError("licensing fields must be source_license and release_license")
    _nonempty_text(licensing["source_license"], where="licensing.source_license")
    _nonempty_text(licensing["release_license"], where="licensing.release_license")

    acceptance = _object(top["acceptance"], where="acceptance")
    expected_acceptance = {
        "proof_sizes_px",
        "proof_polarities",
        "geometry",
        "independent_review_required",
        "hash_pinned_approval_required",
        "reproducible_build_count",
        "release_formats",
        "browser_qa_required",
    }
    if set(acceptance) != expected_acceptance:
        raise BriefError("acceptance fields are incomplete or unknown")
    sizes = acceptance["proof_sizes_px"]
    if (
        not isinstance(sizes, list)
        or not sizes
        or any(
            not isinstance(size, int)
            or isinstance(size, bool)
            or size <= 0
            for size in sizes
        )
        or sizes != sorted(set(sizes))
    ):
        raise BriefError("proof_sizes_px must be sorted unique positive integers")
    if acceptance["proof_polarities"] != [
        "black-on-white",
        "white-on-black",
    ]:
        raise BriefError("both proof polarities are required in canonical order")
    geometry = _object(acceptance["geometry"], where="acceptance.geometry")
    if geometry != {
        "max_micro_edge_count": 0,
        "max_acute_micro_turn_count": 0,
    }:
        raise BriefError("geometry must require zero micro edges and acute turns")
    for key in (
        "independent_review_required",
        "hash_pinned_approval_required",
        "browser_qa_required",
    ):
        if acceptance[key] is not True:
            raise BriefError(f"acceptance.{key} must be true")
    reproducible_build_count = acceptance["reproducible_build_count"]
    if (
        not isinstance(reproducible_build_count, int)
        or isinstance(reproducible_build_count, bool)
        or reproducible_build_count < 2
    ):
        raise BriefError("at least two reproducible builds are required")
    formats = set(
        _nonempty_text_list(
            acceptance["release_formats"],
            where="acceptance.release_formats",
        )
    )
    if not {"ttf", "woff2"} <= formats:
        raise BriefError("release_formats must include ttf and woff2")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.brief.read_text(encoding="utf-8"))
        validate(payload)
    except (OSError, json.JSONDecodeError, BriefError) as exc:
        parser.error(str(exc))
    print(f"valid design brief: {args.brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
