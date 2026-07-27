from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.imagegen_approval import Repertoire, RepertoireBatch
from scripts.record_imagegen_approval import (
    ImagegenApprovalRecorderError,
    _write_new_json,
    build_approval,
    build_visual_review,
    discover_raster_audit,
)


def _batch() -> RepertoireBatch:
    return RepertoireBatch(
        batch_id="common-0001",
        number=1,
        start_rank=1,
        end_rank=2,
        characters=("甲", "乙"),
        empty_grid_cells=14,
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _vector_fixture(root: Path, batch: RepertoireBatch) -> None:
    directory = root / "build/imagegen" / batch.descriptor_batch_id
    proofs = {
        "black_on_white": "proof/black.png",
        "white_on_black": "proof/white.png",
        "segmented_source": "proof/source.png",
    }
    artifacts = {}
    for relative in proofs.values():
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode("ascii"))
        from scripts.imagegen_approval import sha256_path

        artifacts[relative] = sha256_path(path)
    _write_json(
        directory / "report.json",
        {
            "pipeline": "imagegen-raster-potrace-quadratic-v2",
            "approval_state": "unreviewed",
            "batch_id": batch.descriptor_batch_id,
            "characters": list(batch.characters),
            "artifact_sha256": artifacts,
            "proofs": proofs,
        },
    )


def test_build_visual_review_covers_exact_batch_and_proofs(
    tmp_path: Path,
) -> None:
    batch = _batch()
    _vector_fixture(tmp_path, batch)
    record = build_visual_review(
        project_root=tmp_path,
        batch=batch,
        reviewer_name="Review Agent",
        reviewer_role="independent vector visual QA",
        reviewed_at="2026-07-26T10:00:00Z",
    )
    assert record["batch_id"] == batch.batch_id
    assert [item["character"] for item in record["glyphs"]] == ["甲", "乙"]
    assert [item["rank"] for item in record["glyphs"]] == [1, 2]
    assert {item["kind"] for item in record["proofs"]} == {
        "black-on-white",
        "white-on-black",
        "segmented-source",
    }
    assert record["summary"] == {
        "glyph_count": 2,
        "pass_count": 2,
        "reject_count": 0,
        "rejected_characters": [],
    }


def test_discover_raster_audit_requires_exactly_one_match(
    tmp_path: Path,
) -> None:
    batch = _batch()
    first = tmp_path / "reports/imagegen-common-0001-0004-audit.json"
    _write_json(first, {"batches": [{"batch_id": batch.batch_id}]})
    assert discover_raster_audit(project_root=tmp_path, batch=batch) == first
    second = tmp_path / "reports/imagegen-common-0001-0001-audit.json"
    _write_json(second, {"batches": [{"batch_id": batch.batch_id}]})
    with pytest.raises(ImagegenApprovalRecorderError, match="found 2"):
        discover_raster_audit(project_root=tmp_path, batch=batch)


def test_write_new_json_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    _write_new_json(path, {"value": 1})
    with pytest.raises(ImagegenApprovalRecorderError, match="overwrite"):
        _write_new_json(path, {"value": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"value": 1}


def test_build_approval_hash_pins_all_evidence(tmp_path: Path) -> None:
    batch = _batch()
    repertoire_path = (
        tmp_path / "sources/imagegen/repertoires/common-3000.json"
    )
    _write_json(repertoire_path, {"fixture": True})
    from scripts.imagegen_approval import sha256_path

    repertoire = Repertoire(
        path=repertoire_path,
        sha256=sha256_path(repertoire_path),
        repertoire_id="fixture-repertoire",
        sequence_sha256="1" * 64,
        characters=batch.characters,
        batches=(batch,),
    )
    descriptor = (
        tmp_path
        / "sources/imagegen/batches"
        / f"{batch.batch_id}.source.json"
    )
    raster = (
        tmp_path / "sources/imagegen/raster" / f"{batch.batch_id}.png"
    )
    review = (
        tmp_path
        / "sources/imagegen/vector-reviews"
        / f"{batch.batch_id}.vector-review.json"
    )
    audit = tmp_path / "reports/imagegen-common-0001-0001-audit.json"
    for path in (descriptor, raster, review, audit):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode("utf-8"))
    _vector_fixture(tmp_path, batch)
    payload = build_approval(
        project_root=tmp_path,
        repertoire=repertoire,
        batch=batch,
        raster_audit_path=audit,
        approver_name="Release Agent",
        approved_at="2026-07-26T10:01:00Z",
    )
    assert payload["source"]["descriptor_sha256"] == sha256_path(descriptor)
    assert payload["source"]["raster_sha256"] == sha256_path(raster)
    assert payload["raster_audit"]["report_sha256"] == sha256_path(audit)
    assert payload["vector_visual_review"]["record_sha256"] == sha256_path(
        review
    )
    assert payload["authorization"]["decision"] == "APPROVED"
