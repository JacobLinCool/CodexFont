from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image
import pytest

from scripts import imagegen_vertical_approval as approval


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _copy_vertical_build_project(
    tmp_path: Path,
    batch_id: str = "vertical-0001",
) -> Path:
    project = tmp_path / "project"
    imagegen = project / "sources/imagegen"
    for relative in (
        f"batches/{batch_id}.source.json",
        f"raster/{batch_id}.png",
        f"prompts/{batch_id}.md",
        f"copybooks/{batch_id}.png",
        "raster/common-0001.png",
        "repertoires/vertical-93.json",
    ):
        source = ROOT / "sources/imagegen" / relative
        target = imagegen / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(
        ROOT / f"build/imagegen/imagegen-{batch_id}",
        project / f"build/imagegen/imagegen-{batch_id}",
    )
    return project


def test_all_six_vertical_approvals_validate_exactly_93_glyphs() -> None:
    admitted = approval.load_complete_approvals()
    assert [item["batch_id"] for item in admitted] == [
        f"vertical-{number:04d}" for number in range(1, 7)
    ]
    assert [len(item["glyphs"]) for item in admitted] == [
        16,
        16,
        16,
        16,
        16,
        13,
    ]
    assert sum(len(item["glyphs"]) for item in admitted) == 93
    assert all(
        glyph["glyph_name"].endswith(".vert")
        for item in admitted
        for glyph in item["glyphs"]
    )


def test_validate_complete_cli_reports_exact_cardinality(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert approval.main(["validate-complete"]) == 0
    assert capsys.readouterr().out == (
        "validated 6 vertical approvals covering 93 alternates\n"
    )


def test_vertical_approval_rejects_evidence_path_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (
        approval.APPROVAL_ROOT / "vertical-0001.approval.json"
    ).resolve()
    actual_read = approval._read_object

    def drifted_read(path: Path) -> dict[str, object]:
        value = actual_read(path)
        if path.resolve() == target:
            value = copy.deepcopy(value)
            value["ttf"] = "build/imagegen/wrong.ttf"
        return value

    monkeypatch.setattr(approval, "_read_object", drifted_read)
    with pytest.raises(
        approval.VerticalApprovalError,
        match="approval evidence path mismatch",
    ):
        approval.validate_approval("vertical-0001")


def test_vertical_review_rejects_hash_chain_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (
        approval.REVIEW_ROOT
        / "vertical-0001.vector-review.json"
    ).resolve()
    actual_read = approval._read_object

    def drifted_read(path: Path) -> dict[str, object]:
        value = actual_read(path)
        if path.resolve() == target:
            value = copy.deepcopy(value)
            value["report_sha256"] = "0" * 64
        return value

    monkeypatch.setattr(approval, "_read_object", drifted_read)
    with pytest.raises(
        approval.VerticalApprovalError,
        match="review hash chain mismatch",
    ):
        approval.validate_review("vertical-0001")


def test_vertical_build_rejects_report_artifact_path_escape(
    tmp_path: Path,
) -> None:
    project = _copy_vertical_build_project(tmp_path)
    report_path = (
        project / "build/imagegen/imagegen-vertical-0001/report.json"
    )
    report = approval._read_object(report_path)
    report["proofs"][0]["path"] = "../outside.png"
    _write_json(report_path, report)
    with pytest.raises(
        approval.VerticalApprovalError,
        match="artifact path must be exactly",
    ):
        approval.validate_build("vertical-0001", project_root=project)


def test_vertical_build_rejects_hash_consistent_stale_edge_proof(
    tmp_path: Path,
) -> None:
    project = _copy_vertical_build_project(tmp_path)
    build = project / "build/imagegen/imagegen-vertical-0001"
    report_path = build / "report.json"
    proof_path = build / "proof/edge-connect.png"
    with Image.open(proof_path) as source:
        image = source.convert("RGB")
    current = image.getpixel((0, 0))
    image.putpixel((0, 0), tuple(255 - value for value in current))
    image.save(proof_path, optimize=False)
    digest = _sha256(proof_path)
    report = approval._read_object(report_path)
    edge = next(
        item for item in report["proofs"] if item["kind"] == "edge-connect"
    )
    edge["sha256"] = digest
    report["artifact_sha256"]["proof/edge-connect.png"] = digest
    _write_json(report_path, report)
    with pytest.raises(
        approval.VerticalApprovalError,
        match="proof pixels differ from a fresh render",
    ):
        approval.validate_build("vertical-0001", project_root=project)


def test_vertical_build_recomputes_forged_edge_geometry(
    tmp_path: Path,
) -> None:
    project = _copy_vertical_build_project(tmp_path)
    build = project / "build/imagegen/imagegen-vertical-0001"
    report_path = build / "report.json"
    report = approval._read_object(report_path)
    record = next(
        item
        for item in report["glyphs"]
        if item["base_profile_id"] == "box-drawing"
    )
    record["source_component_count"] = 2
    record["outer_contour_count"] = 2
    stem = record["codepoint"].removeprefix("U+").lower()
    glyph_report = build / f"glyph-report/u{stem}-vert.json"
    _write_json(glyph_report, record)
    relative = glyph_report.relative_to(build).as_posix()
    report["artifact_sha256"][relative] = _sha256(glyph_report)
    _write_json(report_path, report)
    with pytest.raises(
        approval.VerticalApprovalError,
        match="actual outer_contour_count differs from report",
    ):
        approval.validate_build("vertical-0001", project_root=project)


def test_vertical_review_requires_exact_confirmation() -> None:
    with pytest.raises(
        approval.VerticalApprovalError,
        match="confirmation phrase is not exact",
    ):
        approval.record_review(
            "vertical-0001",
            reviewer_name="QA",
            reviewer_role="reviewer",
            reviewed_at="2026-07-26T00:00:00+08:00",
            confirmation="not-reviewed",
        )


def test_vertical_records_are_immutable(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    approval._write_json_once(path, {"state": "first"})
    with pytest.raises(
        approval.VerticalApprovalError,
        match="refusing to overwrite canonical record",
    ):
        approval._write_json_once(path, {"state": "second"})
    assert approval._read_object(path) == {"state": "first"}
