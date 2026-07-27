#!/usr/bin/env python3
"""Validate the one scoped Mew Note TC 0.1 Preview release deviation.

The frozen family, collection, authoring, and batch-plan contracts continue to
describe the complete 9,120-codepoint authoring target. This module does not
rewrite those historical contracts. It validates a separate authorization that
permits the already approved 9,088-codepoint subset to ship only as 0.1
Preview, while two exact 16-glyph Han batches remain withheld.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEVIATION_RELATIVE = Path(
    "families/mew-note-tc/release-deviations/"
    "0.1-preview-9088.release-deviation.json"
)
FAMILY_ID = "mew-note-tc"
PIPELINE_ID = "original-raster-v1"
RELEASE = "0.1 Preview"
PLANNED_ENCODED_COUNT = 9_120
ADMITTED_ENCODED_COUNT = 9_088
WITHHELD_ENCODED_COUNT = 32
PLANNED_VISIBLE_BATCH_COUNT = 590
ADMITTED_VISIBLE_BATCH_COUNT = 588
WITHHELD_VISIBLE_BATCH_COUNT = 2
PREDECESSOR_APPROVAL_SHA256 = (
    "61cf38ff06a3adeb050fdf75ab98c9c52984eeb68f61c97d8d8f0fc6467af819"
)
AUTHORIZATION_CONFIRMATION = (
    "I_AUTHORIZE_ONLY_THE_MEW_NOTE_0_1_PREVIEW_9120_TO_9088_"
    "RELEASE_DEVIATION"
)
WAIVED_STOP_CONDITION = (
    "Do not publish coverage unless the compiled cmap contains exactly the "
    "declared 9120-codepoint partition"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)

FROZEN_CONTRACT_PINS: Mapping[str, Mapping[str, str]] = {
    "family_contract": {
        "path": "families/mew-note-tc/family.json",
        "sha256": (
            "5d9799a4a8c33632d0285c2639e127e2b6a1080da03c652c99ebc760ab1a599f"
        ),
    },
    "collection_contract": {
        "path": "families/mew-note-tc/collections.json",
        "sha256": (
            "75e4ca4bc269e272739635afea6be8ecda6020e4d1f09be1d39d9e70d01d741f"
        ),
    },
    "authoring_contract": {
        "path": "families/mew-note-tc/authoring.json",
        "sha256": (
            "2fcf4549ecf28086cf09c7a1f934b5944643608506e0610f05d1db4ce6f61c7a"
        ),
    },
    "batch_plan": {
        "path": (
            "families/mew-note-tc/sources/imagegen/pipelines/"
            "original-raster-v1/batch-plan.json"
        ),
        "sha256": (
            "b68ccd3162b30f9288dafde56fbcaa96921222fb39a9876897a523dec3301232"
        ),
    },
}

PREDECESSOR_APPROVAL_SNAPSHOT_PIN: Mapping[str, str] = {
    "path": (
        "families/mew-note-tc/approvals/history/"
        "61cf38ff06a3adeb050fdf75ab98c9c52984eeb68f61c97d8d8f0fc6467af819"
        ".approval.json"
    ),
    "sha256": PREDECESSOR_APPROVAL_SHA256,
}

CANONICAL_APPROVAL_OVERWRITE: Mapping[str, str] = {
    "path": (
        "families/mew-note-tc/approvals/"
        "original-raster-v1-preview.approval.json"
    ),
    "required_predecessor_sha256": PREDECESSOR_APPROVAL_SHA256,
    "permission": (
        "replace-only-this-exact-predecessor-with-a-new-validated-approval"
    ),
}

WITHHELD_BATCHES: tuple[Mapping[str, Any], ...] = (
    {
        "collection_id": "han-6060",
        "batch_id": "han-0304",
        "batch_contract_sha256": (
            "ee0c3af0f65866394ad0297ddebce62108bc1d62cde59c96d174d969a1874d96"
        ),
        "missing_identity_codepoint": "U+25CD1",
        "codepoints": [
            "U+6BEC",
            "U+25CD1",
            "U+5B62",
            "U+8B14",
            "U+6746",
            "U+6609",
            "U+8AD5",
            "U+768B",
            "U+8E30",
            "U+52AD",
            "U+8ADB",
            "U+8B8E",
            "U+6713",
            "U+7BB8",
            "U+8E47",
            "U+887E",
        ],
        "character_count": 16,
        "reason": "missing-exact-cmap-in-frozen-identity-reference-catalog",
        "policy": "withhold-the-atomic-16-glyph-batch",
    },
    {
        "collection_id": "han-6060",
        "batch_id": "han-0319",
        "batch_contract_sha256": (
            "561d542e3b2b92d3c6662eb9c6bdaf5baf2c1aed3173fd40899c6450b6fab13b"
        ),
        "missing_identity_codepoint": "U+3473",
        "codepoints": [
            "U+9D08",
            "U+3473",
            "U+4EB9",
            "U+54FD",
            "U+5F0B",
            "U+6C4E",
            "U+6F09",
            "U+6FA0",
            "U+6FEE",
            "U+7162",
            "U+737C",
            "U+747E",
            "U+7FCA",
            "U+887F",
            "U+8E05",
            "U+8F05",
        ],
        "character_count": 16,
        "reason": "missing-exact-cmap-in-frozen-identity-reference-catalog",
        "policy": "withhold-the-atomic-16-glyph-batch",
    },
)

RELEASE_COUNTS: Mapping[str, int] = {
    "planned_encoded_count": PLANNED_ENCODED_COUNT,
    "admitted_encoded_count": ADMITTED_ENCODED_COUNT,
    "withheld_encoded_count": WITHHELD_ENCODED_COUNT,
    "planned_visible_batch_count": PLANNED_VISIBLE_BATCH_COUNT,
    "admitted_visible_batch_count": ADMITTED_VISIBLE_BATCH_COUNT,
    "withheld_visible_batch_count": WITHHELD_VISIBLE_BATCH_COUNT,
}

WAIVER_SCOPE: Mapping[str, Any] = {
    "release": RELEASE,
    "applies_only_to": "exact-9120-compiled-cmap-stop-condition",
    "permission": "publish-the-approved-9088-codepoint-cmap",
    "planned_encoded_count": PLANNED_ENCODED_COUNT,
    "admitted_encoded_count": ADMITTED_ENCODED_COUNT,
    "withheld_encoded_count": WITHHELD_ENCODED_COUNT,
    "all_other_contract_conditions": "remain-enforced",
    "future_releases": "not-authorized",
}


class MewNoteReleaseDeviationError(RuntimeError):
    """The scoped Mew Note release deviation is invalid or has drifted."""


@dataclass(frozen=True)
class ValidatedMewNoteReleaseDeviation:
    """The exact, authorized 0.1 Preview release exception."""

    deviation_path: Path
    deviation_sha256: str
    predecessor_approval_snapshot_path: Path
    predecessor_approval_sha256: str
    canonical_approval_path: Path
    required_overwrite_predecessor_sha256: str
    planned_encoded_count: int
    admitted_encoded_count: int
    withheld_encoded_count: int
    withheld_batches: tuple[Mapping[str, Any], ...]
    authorized_by: str
    authorized_at: str


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise MewNoteReleaseDeviationError(
                f"duplicate JSON object key {key!r}"
            )
        value[key] = item
    return value


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except MewNoteReleaseDeviationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MewNoteReleaseDeviationError(
            f"{path}: cannot read {label}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MewNoteReleaseDeviationError(
            f"{path}: {label} must be an object"
        )
    return value


def _exact_keys(
    value: Any,
    expected: set[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise MewNoteReleaseDeviationError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        unknown = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise MewNoteReleaseDeviationError(
            f"{label} key drift; unknown={unknown}, missing={missing}"
        )
    return value


def _regular_pinned_file(
    project_root: Path,
    pin: Mapping[str, str],
    *,
    label: str,
) -> Path:
    relative = Path(pin["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise MewNoteReleaseDeviationError(
            f"{label}: pinned path must be repository-relative"
        )
    candidate = project_root / relative
    current = project_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise MewNoteReleaseDeviationError(
                f"{label}: symlinked evidence is forbidden"
            )
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise MewNoteReleaseDeviationError(
            f"{label}: missing pinned evidence {candidate}"
        ) from exc
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise MewNoteReleaseDeviationError(
            f"{label}: pinned evidence escapes repository"
        ) from exc
    if not resolved.is_file():
        raise MewNoteReleaseDeviationError(
            f"{label}: pinned evidence must be a regular file"
        )
    actual_sha256 = _sha256_path(resolved)
    if actual_sha256 != pin["sha256"]:
        raise MewNoteReleaseDeviationError(
            f"{label}: SHA-256 drift; expected {pin['sha256']}, "
            f"found {actual_sha256}"
        )
    return resolved


def _timestamp(value: Any) -> str:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise MewNoteReleaseDeviationError(
            "authorization.authorized_at must be a canonical UTC timestamp"
        )
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise MewNoteReleaseDeviationError(
            "authorization.authorized_at must be a canonical UTC timestamp"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise MewNoteReleaseDeviationError(
            "authorization.authorized_at must be a canonical UTC timestamp"
        )
    return value


def _person(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise MewNoteReleaseDeviationError(
            "authorization.authorized_by must be an explicit person"
        )
    return value


def _validate_pin_object(
    value: Any,
    expected: Mapping[str, str],
    *,
    label: str,
) -> Mapping[str, str]:
    pin = _exact_keys(value, {"path", "sha256"}, label=label)
    if pin != expected:
        raise MewNoteReleaseDeviationError(f"{label} pin drift")
    if SHA256_PATTERN.fullmatch(str(pin["sha256"])) is None:
        raise MewNoteReleaseDeviationError(f"{label} has invalid SHA-256")
    return {"path": str(pin["path"]), "sha256": str(pin["sha256"])}


def _validate_withheld_batches(
    value: Any,
    *,
    plan: Mapping[str, Any],
    approval: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        raise MewNoteReleaseDeviationError(
            "withheld_batches must be an array"
        )
    expected = [dict(item) for item in WITHHELD_BATCHES]
    if value != expected:
        raise MewNoteReleaseDeviationError(
            "withheld batch inventory drift"
        )
    batch_keys = {
        "collection_id",
        "batch_id",
        "batch_contract_sha256",
        "missing_identity_codepoint",
        "codepoints",
        "character_count",
        "reason",
        "policy",
    }
    for index, batch in enumerate(value):
        _exact_keys(
            batch,
            batch_keys,
            label=f"withheld_batches[{index}]",
        )
    plan_batches = plan.get("batches")
    if not isinstance(plan_batches, list):
        raise MewNoteReleaseDeviationError(
            "pinned batch plan has no batch array"
        )
    planned_by_id = {
        (item.get("collection_id"), item.get("batch_id")): item
        for item in plan_batches
        if isinstance(item, dict)
    }
    for batch in value:
        key = (batch["collection_id"], batch["batch_id"])
        planned = planned_by_id.get(key)
        if not isinstance(planned, dict):
            raise MewNoteReleaseDeviationError(
                f"{key[0]}/{key[1]} is absent from the pinned plan"
            )
        entries = planned.get("entries")
        if (
            planned.get("materialization_kind") != "visible-raster"
            or planned.get("batch_contract_sha256")
            != batch["batch_contract_sha256"]
            or not isinstance(entries, list)
            or [entry.get("codepoint") for entry in entries]
            != batch["codepoints"]
            or len(entries) != batch["character_count"]
            or batch["missing_identity_codepoint"]
            not in batch["codepoints"]
        ):
            raise MewNoteReleaseDeviationError(
                f"{key[0]}/{key[1]} does not match the pinned plan"
            )
    if approval.get("withheld_batches") != value:
        raise MewNoteReleaseDeviationError(
            "deviation withheld batches differ from predecessor approval"
        )
    return tuple(dict(batch) for batch in value)


def validate_release_deviation(
    *,
    project_root: Path = ROOT,
    deviation_path: Path | None = None,
) -> ValidatedMewNoteReleaseDeviation:
    """Validate the canonical deviation and every immutable evidence pin."""

    project_root = project_root.resolve()
    expected_path = project_root / DEVIATION_RELATIVE
    requested_path = deviation_path or expected_path
    if not requested_path.is_absolute():
        requested_path = project_root / requested_path
    requested_path = requested_path.absolute()
    if requested_path != expected_path:
        raise MewNoteReleaseDeviationError(
            "Mew Note release deviation path is not canonical"
        )
    current = project_root
    for part in DEVIATION_RELATIVE.parts:
        current = current / part
        if current.is_symlink():
            raise MewNoteReleaseDeviationError(
                "Mew Note release deviation may not use symlinks"
            )
    try:
        actual_path = requested_path.resolve(strict=True)
    except OSError as exc:
        raise MewNoteReleaseDeviationError(
            "Mew Note release deviation is missing"
        ) from exc
    if not actual_path.is_file():
        raise MewNoteReleaseDeviationError(
            "Mew Note release deviation must be a regular file"
        )
    payload = _read_object(
        actual_path,
        label="Mew Note release deviation",
    )
    root = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "decision",
            "family_id",
            "pipeline_id",
            "release",
            "frozen_authoring_contracts",
            "predecessor_approval_snapshot",
            "canonical_approval_overwrite",
            "release_counts",
            "withheld_batches",
            "waiver",
            "authorization",
        },
        label="release deviation",
    )
    if (
        root["schema_version"] != 1
        or root["record_type"] != "mew-note-tc-release-deviation"
        or root["decision"] != "APPROVED"
        or root["family_id"] != FAMILY_ID
        or root["pipeline_id"] != PIPELINE_ID
        or root["release"] != RELEASE
    ):
        raise MewNoteReleaseDeviationError(
            "release deviation identity drift"
        )

    contract_values = _exact_keys(
        root["frozen_authoring_contracts"],
        set(FROZEN_CONTRACT_PINS),
        label="frozen_authoring_contracts",
    )
    pinned_paths: dict[str, Path] = {}
    for name, expected_pin in FROZEN_CONTRACT_PINS.items():
        pin = _validate_pin_object(
            contract_values[name],
            expected_pin,
            label=f"frozen_authoring_contracts.{name}",
        )
        pinned_paths[name] = _regular_pinned_file(
            project_root,
            pin,
            label=f"frozen_authoring_contracts.{name}",
        )

    predecessor_snapshot_pin = _validate_pin_object(
        root["predecessor_approval_snapshot"],
        PREDECESSOR_APPROVAL_SNAPSHOT_PIN,
        label="predecessor_approval_snapshot",
    )
    predecessor_snapshot_path = _regular_pinned_file(
        project_root,
        predecessor_snapshot_pin,
        label="predecessor_approval_snapshot",
    )
    overwrite = _exact_keys(
        root["canonical_approval_overwrite"],
        set(CANONICAL_APPROVAL_OVERWRITE),
        label="canonical_approval_overwrite",
    )
    if overwrite != CANONICAL_APPROVAL_OVERWRITE:
        raise MewNoteReleaseDeviationError(
            "canonical approval overwrite authorization drift"
        )
    canonical_approval_relative = Path(str(overwrite["path"]))
    if (
        canonical_approval_relative.is_absolute()
        or ".." in canonical_approval_relative.parts
    ):
        raise MewNoteReleaseDeviationError(
            "canonical approval overwrite path must be repository-relative"
        )
    canonical_approval_path = (
        project_root / canonical_approval_relative
    ).absolute()
    try:
        canonical_approval_path.relative_to(project_root)
    except ValueError as exc:
        raise MewNoteReleaseDeviationError(
            "canonical approval overwrite path escapes repository"
        ) from exc
    if (
        overwrite["required_predecessor_sha256"]
        != PREDECESSOR_APPROVAL_SHA256
    ):
        raise MewNoteReleaseDeviationError(
            "canonical approval overwrite predecessor drift"
        )
    if (
        _sha256_path(predecessor_snapshot_path)
        != overwrite["required_predecessor_sha256"]
    ):
        raise MewNoteReleaseDeviationError(
            "overwrite predecessor differs from immutable history snapshot"
        )
    if canonical_approval_path == predecessor_snapshot_path:
        raise MewNoteReleaseDeviationError(
            "canonical approval and immutable history snapshot must differ"
    )
    plan = _read_object(
        pinned_paths["batch_plan"],
        label="pinned batch plan",
    )
    approval = _read_object(
        predecessor_snapshot_path,
        label="pinned predecessor approval",
    )

    counts = _exact_keys(
        root["release_counts"],
        set(RELEASE_COUNTS),
        label="release_counts",
    )
    if counts != RELEASE_COUNTS:
        raise MewNoteReleaseDeviationError("release count drift")
    if (
        counts["planned_encoded_count"]
        - counts["admitted_encoded_count"]
        != counts["withheld_encoded_count"]
        or counts["planned_visible_batch_count"]
        - counts["admitted_visible_batch_count"]
        != counts["withheld_visible_batch_count"]
    ):
        raise MewNoteReleaseDeviationError(
            "release count partition is inconsistent"
        )
    plan_pin = approval.get("plan")
    if not isinstance(plan_pin, dict) or (
        plan_pin.get("planned_visible_batch_count")
        != PLANNED_VISIBLE_BATCH_COUNT
        or plan_pin.get("admitted_visible_batch_count")
        != ADMITTED_VISIBLE_BATCH_COUNT
        or plan_pin.get("planned_encoded_count")
        != PLANNED_ENCODED_COUNT
        or plan_pin.get("encoded_count") != ADMITTED_ENCODED_COUNT
    ):
        raise MewNoteReleaseDeviationError(
            "predecessor approval release count drift"
        )

    withheld = _validate_withheld_batches(
        root["withheld_batches"],
        plan=plan,
        approval=approval,
    )
    if (
        sum(int(batch["character_count"]) for batch in withheld)
        != WITHHELD_ENCODED_COUNT
        or len(withheld) != WITHHELD_VISIBLE_BATCH_COUNT
    ):
        raise MewNoteReleaseDeviationError(
            "withheld batch count partition is inconsistent"
        )

    waiver = _exact_keys(
        root["waiver"],
        {
            "waived_stop_condition",
            "scope",
        },
        label="waiver",
    )
    stop_condition = _exact_keys(
        waiver["waived_stop_condition"],
        {
            "contract",
            "json_pointer",
            "text",
        },
        label="waiver.waived_stop_condition",
    )
    family_pin = _validate_pin_object(
        stop_condition["contract"],
        FROZEN_CONTRACT_PINS["family_contract"],
        label="waiver.waived_stop_condition.contract",
    )
    if (
        stop_condition["json_pointer"] != "/stop_conditions/5"
        or stop_condition["text"] != WAIVED_STOP_CONDITION
    ):
        raise MewNoteReleaseDeviationError(
            "waived stop condition drift"
        )
    family = _read_object(
        _regular_pinned_file(
            project_root,
            family_pin,
            label="waiver.waived_stop_condition.contract",
        ),
        label="pinned family contract",
    )
    stop_conditions = family.get("stop_conditions")
    if (
        not isinstance(stop_conditions, list)
        or len(stop_conditions) <= 5
        or stop_conditions[5] != WAIVED_STOP_CONDITION
    ):
        raise MewNoteReleaseDeviationError(
            "waived stop condition is absent from pinned family contract"
        )
    scope = _exact_keys(
        waiver["scope"],
        set(WAIVER_SCOPE),
        label="waiver.scope",
    )
    if scope != WAIVER_SCOPE:
        raise MewNoteReleaseDeviationError(
            "release waiver scope drift"
        )

    authorization = _exact_keys(
        root["authorization"],
        {
            "authorized_by",
            "authorized_at",
            "confirmation",
        },
        label="authorization",
    )
    authorized_by = _person(authorization["authorized_by"])
    authorized_at = _timestamp(authorization["authorized_at"])
    if authorization["confirmation"] != AUTHORIZATION_CONFIRMATION:
        raise MewNoteReleaseDeviationError(
            "explicit scoped release-deviation authorization is required"
        )

    return ValidatedMewNoteReleaseDeviation(
        deviation_path=actual_path,
        deviation_sha256=_sha256_path(actual_path),
        predecessor_approval_snapshot_path=predecessor_snapshot_path,
        predecessor_approval_sha256=PREDECESSOR_APPROVAL_SHA256,
        canonical_approval_path=canonical_approval_path,
        required_overwrite_predecessor_sha256=(
            PREDECESSOR_APPROVAL_SHA256
        ),
        planned_encoded_count=PLANNED_ENCODED_COUNT,
        admitted_encoded_count=ADMITTED_ENCODED_COUNT,
        withheld_encoded_count=WITHHELD_ENCODED_COUNT,
        withheld_batches=withheld,
        authorized_by=authorized_by,
        authorized_at=authorized_at,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("command", choices=("validate",))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    deviation = validate_release_deviation(
        project_root=args.project_root.resolve()
    )
    print(
        "validated Mew Note TC 0.1 Preview release deviation: "
        f"{deviation.planned_encoded_count} planned, "
        f"{deviation.admitted_encoded_count} admitted, "
        f"{deviation.withheld_encoded_count} withheld"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
