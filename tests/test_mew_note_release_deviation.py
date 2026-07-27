from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from scripts import mew_note_release_deviation as deviation


ROOT = Path(__file__).resolve().parents[1]


def _copy_evidence(project_root: Path) -> dict[str, Any]:
    for pin in (
        *deviation.FROZEN_CONTRACT_PINS.values(),
        deviation.PREDECESSOR_APPROVAL_SNAPSHOT_PIN,
    ):
        source = ROOT / pin["path"]
        target = project_root / pin["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    source = ROOT / deviation.DEVIATION_RELATIVE
    target = project_root / deviation.DEVIATION_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return json.loads(target.read_text(encoding="utf-8"))


def _write_payload(project_root: Path, payload: dict[str, Any]) -> None:
    path = project_root / deviation.DEVIATION_RELATIVE
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_canonical_release_deviation_pins_exact_authoring_history() -> None:
    result = deviation.validate_release_deviation(project_root=ROOT)

    assert result.deviation_path == ROOT / deviation.DEVIATION_RELATIVE
    assert result.predecessor_approval_sha256 == (
        "61cf38ff06a3adeb050fdf75ab98c9c52984eeb68f61c97d8d8f0fc6467af819"
    )
    assert result.predecessor_approval_snapshot_path.name == (
        "61cf38ff06a3adeb050fdf75ab98c9c52984eeb68f61c97d8d8f0fc6467af819"
        ".approval.json"
    )
    assert result.canonical_approval_path == (
        ROOT
        / "families/mew-note-tc/approvals/"
        "original-raster-v1-preview.approval.json"
    )
    assert result.required_overwrite_predecessor_sha256 == (
        result.predecessor_approval_sha256
    )
    assert (
        result.planned_encoded_count,
        result.admitted_encoded_count,
        result.withheld_encoded_count,
    ) == (9_120, 9_088, 32)
    assert [
        (batch["collection_id"], batch["batch_id"])
        for batch in result.withheld_batches
    ] == [
        ("han-6060", "han-0304"),
        ("han-6060", "han-0319"),
    ]
    assert sum(
        batch["character_count"] for batch in result.withheld_batches
    ) == 32
    assert result.authorized_by == "Codex release reviewer"


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        (
            lambda payload: payload.update({"unexpected": True}),
            "release deviation key drift",
        ),
        (
            lambda payload: payload["frozen_authoring_contracts"][
                "family_contract"
            ].update({"unexpected": True}),
            "family_contract key drift",
        ),
        (
            lambda payload: payload["canonical_approval_overwrite"].update(
                {"unexpected": True}
            ),
            "canonical_approval_overwrite key drift",
        ),
        (
            lambda payload: payload["withheld_batches"][0].update(
                {"unexpected": True}
            ),
            "withheld batch inventory drift",
        ),
        (
            lambda payload: payload["waiver"].update({"unexpected": True}),
            "waiver key drift",
        ),
        (
            lambda payload: payload["waiver"]["scope"].update(
                {"unexpected": True}
            ),
            "waiver.scope key drift",
        ),
        (
            lambda payload: payload["authorization"].update(
                {"unexpected": True}
            ),
            "authorization key drift",
        ),
    ),
)
def test_unknown_fields_fail_closed(
    tmp_path: Path,
    mutation: Any,
    match: str,
) -> None:
    payload = _copy_evidence(tmp_path)
    mutation(payload)
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match=match,
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_duplicate_json_keys_fail_closed(tmp_path: Path) -> None:
    _copy_evidence(tmp_path)
    path = tmp_path / deviation.DEVIATION_RELATIVE
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            '  "decision": "APPROVED",\n',
            (
                '  "decision": "APPROVED",\n'
                '  "decision": "APPROVED",\n'
            ),
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="duplicate JSON object key 'decision'",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_predecessor_approval_pin_is_exact(tmp_path: Path) -> None:
    payload = _copy_evidence(tmp_path)
    payload["predecessor_approval_snapshot"]["sha256"] = "0" * 64
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="predecessor_approval_snapshot pin drift",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_predecessor_approval_bytes_may_not_drift(tmp_path: Path) -> None:
    _copy_evidence(tmp_path)
    approval_path = (
        tmp_path / deviation.PREDECESSOR_APPROVAL_SNAPSHOT_PIN["path"]
    )
    approval_path.write_bytes(approval_path.read_bytes() + b"\n")

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="predecessor_approval_snapshot: SHA-256 drift",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_canonical_approval_may_advance_after_snapshot(
    tmp_path: Path,
) -> None:
    _copy_evidence(tmp_path)
    canonical = (
        tmp_path
        / deviation.CANONICAL_APPROVAL_OVERWRITE["path"]
    )
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(
        '{"new_validated_approval":"not-the-predecessor"}\n',
        encoding="utf-8",
    )

    result = deviation.validate_release_deviation(
        project_root=tmp_path
    )

    assert result.canonical_approval_path == canonical
    assert result.predecessor_approval_snapshot_path != canonical
    assert result.predecessor_approval_sha256 == (
        result.required_overwrite_predecessor_sha256
    )


def test_canonical_overwrite_requires_exact_predecessor_sha(
    tmp_path: Path,
) -> None:
    payload = _copy_evidence(tmp_path)
    payload["canonical_approval_overwrite"][
        "required_predecessor_sha256"
    ] = "f" * 64
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="overwrite authorization drift",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("planned_encoded_count", 9_119),
        ("admitted_encoded_count", 9_089),
        ("withheld_encoded_count", 31),
        ("planned_visible_batch_count", 589),
        ("admitted_visible_batch_count", 589),
        ("withheld_visible_batch_count", 1),
    ),
)
def test_release_partition_is_exact(
    tmp_path: Path,
    field: str,
    value: int,
) -> None:
    payload = _copy_evidence(tmp_path)
    payload["release_counts"][field] = value
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="release count drift",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


@pytest.mark.parametrize(
    ("path", "value", "match"),
    (
        (
            ("release",),
            "0.2 Preview",
            "release deviation identity drift",
        ),
        (
            ("waiver", "scope", "future_releases"),
            "authorized",
            "release waiver scope drift",
        ),
        (
            ("waiver", "scope", "all_other_contract_conditions"),
            "also-waived",
            "release waiver scope drift",
        ),
        (
            ("waiver", "waived_stop_condition", "text"),
            "waive every release stop",
            "waived stop condition drift",
        ),
        (
            ("authorization", "confirmation"),
            "I_AUTHORIZE_EVERY_DEVIATION",
            "explicit scoped release-deviation authorization is required",
        ),
    ),
)
def test_waiver_cannot_expand_beyond_exact_0_1_preview_gate(
    tmp_path: Path,
    path: tuple[str, ...],
    value: str,
    match: str,
) -> None:
    payload = _copy_evidence(tmp_path)
    target: dict[str, Any] = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match=match,
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_withheld_batches_must_remain_two_exact_atomic_units(
    tmp_path: Path,
) -> None:
    payload = _copy_evidence(tmp_path)
    payload["withheld_batches"][0]["codepoints"].pop()
    payload["withheld_batches"][0]["character_count"] = 15
    payload["release_counts"]["withheld_encoded_count"] = 31
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="release count drift|withheld batch inventory drift",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        (
            "authorized_by",
            " Codex release reviewer",
            "must be an explicit person",
        ),
        (
            "authorized_at",
            "2026-07-29",
            "canonical UTC timestamp",
        ),
    ),
)
def test_authorization_is_explicit_and_canonical(
    tmp_path: Path,
    field: str,
    value: str,
    match: str,
) -> None:
    payload = _copy_evidence(tmp_path)
    payload["authorization"][field] = value
    _write_payload(tmp_path, payload)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match=match,
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_symlinked_frozen_contract_is_rejected(tmp_path: Path) -> None:
    _copy_evidence(tmp_path)
    family_path = (
        tmp_path
        / deviation.FROZEN_CONTRACT_PINS["family_contract"]["path"]
    )
    family_path.unlink()
    family_path.symlink_to(
        ROOT
        / deviation.FROZEN_CONTRACT_PINS["family_contract"]["path"]
    )

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="symlinked evidence is forbidden",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_noncanonical_deviation_path_is_rejected(tmp_path: Path) -> None:
    _copy_evidence(tmp_path)
    alternate = tmp_path / "alternate.json"
    shutil.copy2(
        tmp_path / deviation.DEVIATION_RELATIVE,
        alternate,
    )

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="path is not canonical",
    ):
        deviation.validate_release_deviation(
            project_root=tmp_path,
            deviation_path=alternate,
        )


def test_symlinked_deviation_is_rejected(tmp_path: Path) -> None:
    _copy_evidence(tmp_path)
    deviation_path = tmp_path / deviation.DEVIATION_RELATIVE
    content_path = tmp_path / "deviation-content.json"
    deviation_path.rename(content_path)
    deviation_path.symlink_to(content_path)

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="may not use symlinks",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)


def test_frozen_contract_bytes_may_not_drift(tmp_path: Path) -> None:
    _copy_evidence(tmp_path)
    plan_path = (
        tmp_path / deviation.FROZEN_CONTRACT_PINS["batch_plan"]["path"]
    )
    plan_path.write_bytes(plan_path.read_bytes() + b"\n")

    with pytest.raises(
        deviation.MewNoteReleaseDeviationError,
        match="batch_plan: SHA-256 drift",
    ):
        deviation.validate_release_deviation(project_root=tmp_path)
