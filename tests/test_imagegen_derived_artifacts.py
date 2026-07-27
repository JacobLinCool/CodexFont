from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import imagegen_derived_artifacts as artifacts


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    batch_id = "imagegen-common-0001"
    project = tmp_path
    descriptor = project / "sources/imagegen/batches/common-0001.source.json"
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text("{}\n", encoding="utf-8")
    build = project / "build/imagegen" / batch_id
    proof = build / "proof/review.png"
    proof.parent.mkdir(parents=True)
    proof.write_bytes(b"approved proof")
    report: dict[str, object] = {
        "batch_id": batch_id,
        "source_descriptor": (
            "sources/imagegen/batches/common-0001.source.json"
        ),
        "artifact_sha256": {
            "font/preview.ttf": _sha256(b"preview font"),
            "proof/review.png": _sha256(b"approved proof"),
        },
    }
    report_path = build / "report.json"
    report_path.write_text(
        json.dumps(report, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return project, report_path, report


def test_materializes_only_missing_derived_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, report_path, _report = _fixture(tmp_path)

    def fake_build(
        *,
        batch_id: str,
        descriptor_path: Path,
        project_root: Path,
        cache_root: Path,
    ) -> Path:
        assert descriptor_path.is_file()
        assert project_root == project
        cached = cache_root / batch_id
        for name in artifacts.DERIVED_DIRECTORIES:
            (cached / name).mkdir(parents=True, exist_ok=True)
        (cached / "font/preview.ttf").write_bytes(b"preview font")
        (cached / "proof").mkdir()
        # Proofs are retained review evidence. A newer renderer may reproduce
        # different proof bytes without changing the approved derived font.
        (cached / "proof/review.png").write_bytes(b"new proof render")
        (cached / "report.json").write_bytes(report_path.read_bytes())
        return cached

    monkeypatch.setattr(artifacts, "_build", fake_build)
    artifacts.ensure_materialized(report_path, project_root=project)

    assert (report_path.parent / "font/preview.ttf").read_bytes() == b"preview font"
    assert (report_path.parent / "proof/review.png").read_bytes() == b"approved proof"


def test_rejects_partially_present_derived_tree(tmp_path: Path) -> None:
    project, report_path, _report = _fixture(tmp_path)
    partial = report_path.parent / "font/preview.ttf"
    partial.parent.mkdir()
    partial.write_bytes(b"wrong")

    with pytest.raises(
        artifacts.DerivedArtifactError,
        match="incomplete or changed artifact tree",
    ):
        artifacts.ensure_materialized(report_path, project_root=project)


def test_routes_declared_han_delta_to_generic_han_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = tmp_path / "dict-han-0001.source.json"
    descriptor.write_text(
        json.dumps(
            {
                "record_type": "imagegen-han-delta-source",
                "batch_id": "imagegen-dict-han-0001",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    expected = tmp_path / "cache/imagegen-dict-han-0001"

    from scripts import imagegen_font_pipeline
    from scripts import register_han_delta_sheet

    def fake_validate(
        path: Path,
        *,
        project_root: Path,
    ) -> dict[str, str]:
        assert path == descriptor
        assert project_root == tmp_path
        return {
            "batch_id": "imagegen-dict-han-0001",
        }

    def fake_build(
        path: Path,
        *,
        output_root: Path,
    ) -> Path:
        assert path == descriptor
        assert output_root == tmp_path / "cache"
        return expected

    monkeypatch.setattr(
        register_han_delta_sheet,
        "validate_descriptor",
        fake_validate,
    )
    monkeypatch.setattr(
        imagegen_font_pipeline,
        "build_batch",
        fake_build,
    )

    assert artifacts._build(
        batch_id="imagegen-dict-han-0001",
        descriptor_path=descriptor,
        project_root=tmp_path,
        cache_root=tmp_path / "cache",
    ) == expected


def test_infers_declared_han_delta_descriptor_for_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_id = "imagegen-dict-han-0001"
    project = tmp_path
    descriptor = (
        project
        / "sources/imagegen/batches/dict-han-0001.source.json"
    )
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps(
            {
                "record_type": "imagegen-han-delta-source",
                "batch_id": batch_id,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    build = project / "build/imagegen" / batch_id
    proof = build / "proof/review.png"
    proof.parent.mkdir(parents=True)
    proof.write_bytes(b"approved proof")
    report = {
        "batch_id": batch_id,
        "artifact_sha256": {
            "font/preview.ttf": _sha256(b"preview font"),
            "proof/review.png": _sha256(b"approved proof"),
        },
    }
    report_path = build / "report.json"
    report_path.write_text(
        json.dumps(report, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    def fake_build(
        *,
        batch_id: str,
        descriptor_path: Path,
        project_root: Path,
        cache_root: Path,
    ) -> Path:
        assert batch_id == "imagegen-dict-han-0001"
        assert descriptor_path == descriptor
        assert project_root == project
        cached = cache_root / batch_id
        for name in artifacts.DERIVED_DIRECTORIES:
            (cached / name).mkdir(parents=True, exist_ok=True)
        (cached / "font/preview.ttf").write_bytes(b"preview font")
        (cached / "proof").mkdir()
        (cached / "proof/review.png").write_bytes(b"new proof")
        (cached / "report.json").write_bytes(report_path.read_bytes())
        return cached

    monkeypatch.setattr(artifacts, "_build", fake_build)
    artifacts.ensure_materialized(report_path, project_root=project)

    assert (build / "font/preview.ttf").read_bytes() == b"preview font"
    assert (build / "proof/review.png").read_bytes() == b"approved proof"
