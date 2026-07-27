#!/usr/bin/env python3
"""Register one immutable imagegen Common-Han raster sheet.

Registration is deliberately separate from approval.  It verifies the sheet
against the frozen 3,000-character repertoire, records its exact bytes and
generation provenance, and writes a ``generated-unreviewed`` descriptor.  It
does not infer character identity from pixels and never changes audit status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
REPERTOIRE = IMAGEGEN_ROOT / "repertoires/common-3000.json"
RASTER_ROOT = IMAGEGEN_ROOT / "raster"
BATCH_ROOT = IMAGEGEN_ROOT / "batches"
PROMPT = IMAGEGEN_ROOT / "prompts/common-grid-anchor-v1.md"
STYLE_REFERENCE = RASTER_ROOT / "common-0001.png"
BATCH_PATTERN = re.compile(r"common-(?P<number>[0-9]{4})")


class RegistrationError(RuntimeError):
    """The raster cannot be registered without inventing provenance."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistrationError(f"{path}: cannot read JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistrationError(f"{path}: expected a JSON object")
    return value


def find_batch(repertoire: dict[str, Any], batch_id: str) -> dict[str, Any]:
    batches = repertoire.get("batches")
    if not isinstance(batches, list):
        raise RegistrationError("repertoire batches are missing")
    matches = [
        batch
        for batch in batches
        if isinstance(batch, dict) and batch.get("batch_id") == batch_id
    ]
    if len(matches) != 1:
        raise RegistrationError(
            f"{batch_id}: expected exactly one frozen repertoire batch"
        )
    return matches[0]


def descriptor_for(
    *,
    batch_id: str,
    generator_call: str,
    raster: Path,
) -> dict[str, Any]:
    if BATCH_PATTERN.fullmatch(batch_id) is None:
        raise RegistrationError("batch id must be common-NNNN")
    repertoire = read_json(REPERTOIRE)
    batch = find_batch(repertoire, batch_id)
    characters = batch.get("characters")
    if not isinstance(characters, str) or not 1 <= len(characters) <= 16:
        raise RegistrationError(f"{batch_id}: invalid frozen character string")
    if len(set(characters)) != len(characters):
        raise RegistrationError(f"{batch_id}: frozen batch contains duplicates")
    expected_raster = (RASTER_ROOT / f"{batch_id}.png").resolve()
    raster = raster.resolve()
    if raster != expected_raster:
        raise RegistrationError(
            f"{batch_id}: raster must be exactly {expected_raster}"
        )
    if not raster.is_file():
        raise RegistrationError(f"{raster}: raster does not exist")
    if not generator_call.strip():
        raise RegistrationError("generator call provenance must not be blank")
    if not STYLE_REFERENCE.is_file():
        raise RegistrationError("style reference is missing")

    return {
        "schema_version": 1,
        "batch_id": f"imagegen-{batch_id}",
        "state": "generated-unreviewed",
        "generator": "built-in-image_gen",
        "generator_call": generator_call,
        "raster": f"../raster/{batch_id}.png",
        "raster_sha256": sha256(raster),
        "prompt": "../prompts/common-grid-anchor-v1.md",
        "prompt_variables": {
            "character_count": len(characters),
            "characters": characters,
            "rows": [
                characters[index : index + 4]
                for index in range(0, len(characters), 4)
            ],
        },
        "style_reference": {
            "role": "style-only",
            "raster": "../raster/common-0001.png",
            "raster_sha256": sha256(STYLE_REFERENCE),
        },
        "repertoire": {
            "path": "../repertoires/common-3000.json",
            "repertoire_id": repertoire.get("repertoire_id"),
            "sequence_sha256": repertoire.get("provenance", {}).get(
                "sequence_sha256"
            ),
            "start_rank": batch.get("start_rank"),
            "end_rank": batch.get("end_rank"),
        },
        "grid": {
            "rows": 4,
            "columns": 4,
            "characters": list(characters),
            "empty_grid_cells": 16 - len(characters),
        },
        "review": {
            "topology": "pending",
            "raster_quality": "pending",
            "vector_quality": "pending",
        },
    }


def register(*, batch_id: str, generator_call: str, raster: Path) -> Path:
    payload = descriptor_for(
        batch_id=batch_id,
        generator_call=generator_call,
        raster=raster,
    )
    output = BATCH_ROOT / f"{batch_id}.source.json"
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output.exists():
        existing = output.read_text(encoding="utf-8")
        if existing != serialized:
            raise RegistrationError(
                f"{output}: refusing to overwrite a non-identical descriptor"
            )
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch_id")
    parser.add_argument("--generator-call", required=True)
    parser.add_argument("--raster", type=Path)
    args = parser.parse_args()
    raster = args.raster or RASTER_ROOT / f"{args.batch_id}.png"
    output = register(
        batch_id=args.batch_id,
        generator_call=args.generator_call,
        raster=raster,
    )
    print(output)


if __name__ == "__main__":
    main()
