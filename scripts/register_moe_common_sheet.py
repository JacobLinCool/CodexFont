#!/usr/bin/env python3
"""Register one immutable Ministry-common extension raster sheet."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IMAGEGEN_ROOT = ROOT / "sources/imagegen"
REPERTOIRE = (
    IMAGEGEN_ROOT / "repertoires/moe-common-extension-1844.json"
)
RASTER_ROOT = IMAGEGEN_ROOT / "raster"
BATCH_ROOT = IMAGEGEN_ROOT / "batches"
CORRECTION_ROOT = IMAGEGEN_ROOT / "corrections"
PROMPT = IMAGEGEN_ROOT / "prompts/common-grid-anchor-v1.md"
STYLE_REFERENCE = RASTER_ROOT / "common-0001.png"
BATCH_PATTERN = re.compile(r"moe-common-(?P<number>[0-9]{4})")
RFC3339_UTC_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


class RegistrationError(RuntimeError):
    """The generated source cannot be registered exactly."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RegistrationError(f"{path}: expected a JSON object")
    return value


def _batch_payload(
    *,
    batch_id: str,
    generator_call: str,
    raster: Path,
) -> dict[str, Any]:
    if BATCH_PATTERN.fullmatch(batch_id) is None:
        raise RegistrationError("batch id must be moe-common-NNNN")
    repertoire = _read_json(REPERTOIRE)
    matches = [
        batch
        for batch in repertoire["batches"]
        if batch["batch_id"] == batch_id
    ]
    if len(matches) != 1:
        raise RegistrationError(f"{batch_id}: not in frozen repertoire")
    batch = matches[0]
    characters = batch["characters"]
    if not raster.is_file():
        raise RegistrationError(f"{batch_id}: missing raster {raster}")
    if not generator_call.strip():
        raise RegistrationError("generator call provenance is required")

    return {
        "schema_version": 1,
        "batch_id": f"imagegen-{batch_id}",
        "state": "generated-unreviewed",
        "generator": "built-in-image_gen",
        "generator_call": generator_call,
        "raster": f"../raster/{batch_id}.png",
        "raster_sha256": _sha256(raster),
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
            "raster_sha256": _sha256(STYLE_REFERENCE),
        },
        "repertoire": {
            "path": "../repertoires/moe-common-extension-1844.json",
            "repertoire_id": repertoire["repertoire_id"],
            "sequence_sha256": repertoire["provenance"][
                "sequence_sha256"
            ],
            "start_rank": batch["start_rank"],
            "end_rank": batch["end_rank"],
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


def _serialize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def register(
    *,
    batch_id: str,
    generator_call: str,
    raster: Path | None = None,
) -> Path:
    expected_raster = RASTER_ROOT / f"{batch_id}.png"
    raster = (raster or expected_raster).resolve()
    if raster != expected_raster.resolve():
        raise RegistrationError(
            f"{batch_id}: raster must be exactly {expected_raster}"
        )
    payload = _batch_payload(
        batch_id=batch_id,
        generator_call=generator_call,
        raster=raster,
    )
    output = BATCH_ROOT / f"{batch_id}.source.json"
    serialized = _serialize(payload)
    if output.exists() and output.read_text(encoding="utf-8") != serialized:
        raise RegistrationError(
            f"{output}: refusing to overwrite non-identical descriptor"
        )
    output.write_text(serialized, encoding="utf-8")
    return output


def replace_registration(
    *,
    batch_id: str,
    generator_call: str,
    replacement_raster: Path,
    reason: str,
    replaced_at: str,
) -> Path:
    """Atomically replace one rejected raster and record both source hashes."""

    if not reason.strip():
        raise RegistrationError("replacement reason is required")
    if RFC3339_UTC_PATTERN.fullmatch(replaced_at) is None:
        raise RegistrationError("replaced-at must be RFC 3339 UTC to seconds")
    try:
        datetime.strptime(replaced_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise RegistrationError("replaced-at is not a valid UTC timestamp") from exc

    expected_raster = RASTER_ROOT / f"{batch_id}.png"
    descriptor = BATCH_ROOT / f"{batch_id}.source.json"
    replacement_raster = replacement_raster.resolve()
    if not expected_raster.is_file() or not descriptor.is_file():
        raise RegistrationError(
            f"{batch_id}: replacement requires an existing raster and descriptor"
        )
    if not replacement_raster.is_file():
        raise RegistrationError(
            f"{batch_id}: missing replacement raster {replacement_raster}"
        )

    old_descriptor_bytes = descriptor.read_bytes()
    old_payload = _read_json(descriptor)
    old_raster_sha256 = _sha256(expected_raster)
    if old_payload.get("raster_sha256") != old_raster_sha256:
        raise RegistrationError(
            f"{batch_id}: existing descriptor does not pin the current raster"
        )
    new_raster_sha256 = _sha256(replacement_raster)
    if new_raster_sha256 == old_raster_sha256:
        raise RegistrationError(f"{batch_id}: replacement raster is unchanged")

    staged_raster = expected_raster.with_suffix(".replacement.png")
    staged_descriptor = descriptor.with_suffix(".replacement.json")
    shutil.copyfile(replacement_raster, staged_raster)
    new_payload = _batch_payload(
        batch_id=batch_id,
        generator_call=generator_call,
        raster=staged_raster,
    )
    new_descriptor_bytes = _serialize(new_payload).encode("utf-8")
    staged_descriptor.write_bytes(new_descriptor_bytes)

    CORRECTION_ROOT.mkdir(parents=True, exist_ok=True)
    existing = sorted(CORRECTION_ROOT.glob(f"{batch_id}-*.correction.json"))
    sequence = len(existing) + 1
    correction = CORRECTION_ROOT / (
        f"{batch_id}-{sequence:02d}.correction.json"
    )
    if correction.exists():
        raise RegistrationError(f"{correction}: correction record already exists")
    correction_payload = {
        "schema_version": 1,
        "record_type": "imagegen-source-correction",
        "batch_id": batch_id,
        "replaced_at": replaced_at,
        "reason": reason.strip(),
        "old_source": {
            "generator_call": old_payload.get("generator_call"),
            "raster_sha256": old_raster_sha256,
            "descriptor_sha256": hashlib.sha256(
                old_descriptor_bytes
            ).hexdigest(),
        },
        "new_source": {
            "generator_call": generator_call,
            "raster_sha256": new_raster_sha256,
            "descriptor_sha256": hashlib.sha256(
                new_descriptor_bytes
            ).hexdigest(),
        },
    }

    try:
        staged_raster.replace(expected_raster)
        staged_descriptor.replace(descriptor)
        correction.write_text(
            _serialize(correction_payload),
            encoding="utf-8",
        )
    except Exception:
        staged_raster.unlink(missing_ok=True)
        staged_descriptor.unlink(missing_ok=True)
        raise
    return correction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch_id")
    parser.add_argument("--generator-call", required=True)
    parser.add_argument("--raster", type=Path)
    parser.add_argument("--replacement-raster", type=Path)
    parser.add_argument("--reason")
    parser.add_argument("--replaced-at")
    arguments = parser.parse_args()
    replacement_values = (
        arguments.replacement_raster,
        arguments.reason,
        arguments.replaced_at,
    )
    if any(value is not None for value in replacement_values):
        if arguments.raster is not None or any(
            value is None for value in replacement_values
        ):
            parser.error(
                "replacement requires --replacement-raster, --reason, and "
                "--replaced-at; --raster is not accepted"
            )
        print(
            replace_registration(
                batch_id=arguments.batch_id,
                generator_call=arguments.generator_call,
                replacement_raster=arguments.replacement_raster,
                reason=arguments.reason,
                replaced_at=arguments.replaced_at,
            )
        )
    else:
        print(
            register(
                batch_id=arguments.batch_id,
                generator_call=arguments.generator_call,
                raster=arguments.raster,
            )
        )


if __name__ == "__main__":
    main()
