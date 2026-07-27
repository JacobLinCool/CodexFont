from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import font_family_context as family_context


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _build_family(
    root: Path,
    family_id: str,
    *,
    pipeline_id: str = "raster-authoring-v1",
    collection_ids: tuple[str, ...] = ("han-main", "nonhan-main"),
) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    license_path = root / "OFL.txt"
    if not license_path.exists():
        license_path.write_text("fixture license\n", encoding="utf-8")

    family_root = root / "families" / family_id
    collections_path = family_root / "collections.json"
    _write_json(
        collections_path,
        {
            "schema_version": 1,
            "record_type": (
                family_context.COLLECTION_RECORD_TYPE
            ),
            "family_id": family_id,
            "collections": [
                {
                    "id": collection_id,
                    "kind": "fixture",
                    "encoded_count": index + 1,
                }
                for index, collection_id in enumerate(collection_ids)
            ],
        },
    )
    authoring_path = family_root / "authoring.json"
    _write_json(
        authoring_path,
        {
            "schema_version": 1,
            "record_type": (
                family_context.AUTHORING_RECORD_TYPE
            ),
            "family_id": family_id,
            "pipeline_id": pipeline_id,
            "collection_contract": {
                "path": collections_path.relative_to(root).as_posix(),
                "sha256": _sha256(collections_path),
            },
        },
    )
    family_path = family_root / "family.json"
    family_payload = {
        "schema_version": 1,
        "record_type": family_context.FAMILY_RECORD_TYPE,
        "family_id": family_id,
        "contracts": {
            "collections": {
                "path": collections_path.relative_to(root).as_posix(),
                "sha256": _sha256(collections_path),
            },
            "authoring": {
                "path": authoring_path.relative_to(root).as_posix(),
                "sha256": _sha256(authoring_path),
            },
        },
        "workspace": {
            "family_root": family_root.relative_to(root).as_posix(),
            "source_root": (
                family_root / "sources" / "imagegen"
            ).relative_to(root).as_posix(),
            "build_root": f"build/families/{family_id}",
            "release_root": f"dist/{family_id}",
        },
        "licensing": {
            "path": "OFL.txt",
            "sha256": _sha256(license_path),
            "identifier": "OFL-1.1",
        },
    }
    _write_json(family_path, family_payload)

    pipeline_path = family_root / "pipeline.json"
    _write_json(
        pipeline_path,
        {
            "schema_version": 1,
            "record_type": (
                family_context.PIPELINE_RECORD_TYPE
            ),
            "family_id": family_id,
            "pipeline_id": pipeline_id,
            "family_contract": {
                "path": family_path.relative_to(root).as_posix(),
                "sha256": _sha256(family_path),
            },
            "collection_contract": {
                "path": collections_path.relative_to(root).as_posix(),
                "sha256": _sha256(collections_path),
            },
            "authoring_contract": {
                "path": authoring_path.relative_to(root).as_posix(),
                "sha256": _sha256(authoring_path),
            },
            "workspace": {
                "source_root": (
                    family_payload["workspace"]["source_root"]
                ),
                "build_root": (
                    family_payload["workspace"]["build_root"]
                ),
                "cache_root": f"cache/families/{family_id}",
                "release_root": (
                    family_payload["workspace"]["release_root"]
                ),
            },
        },
    )
    return family_path, pipeline_path


def _load(
    root: Path,
    family_path: Path,
    pipeline_path: Path,
) -> family_context.FamilyContext:
    return family_context.load_family_context(
        project_root=root,
        family_contract_path=family_path,
        pipeline_contract_path=pipeline_path,
    )


def test_loads_explicit_context_and_builds_hash_chained_evidence(
    tmp_path: Path,
) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    context = _load(tmp_path, family_path, pipeline_path)

    assert context.family_id == "fixture-hand"
    assert context.pipeline_id == "raster-authoring-v1"
    paths = context.batch_paths("han-main", "shared-0001")
    assert paths.source.relative_to(tmp_path).as_posix() == (
        "families/fixture-hand/sources/imagegen/pipelines/"
        "raster-authoring-v1/collections/han-main/batches/shared-0001"
    )
    assert paths.cache.relative_to(tmp_path).as_posix() == (
        "cache/families/fixture-hand/pipelines/raster-authoring-v1/"
        "collections/han-main/batches/shared-0001"
    )

    descriptor = {
        "family_context": context.evidence_binding("han-main"),
        "batch_id": "shared-0001",
    }
    binding = family_context.validate_evidence_context(
        descriptor,
        context=context,
        collection_id="han-main",
        label="descriptor",
    )
    assert binding["family_contract"]["sha256"] == _sha256(
        family_path
    )
    assert binding["pipeline_contract"]["sha256"] == _sha256(
        pipeline_path
    )
    assert binding["authoring_contract"]["sha256"] == _sha256(
        family_path.parent / "authoring.json"
    )
    assert binding["binding_sha256"] == (
        family_context.canonical_json_sha256(
            {
                key: value
                for key, value in binding.items()
                if key != "binding_sha256"
            }
        )
    )


def test_cross_family_contract_swap_is_rejected(
    tmp_path: Path,
) -> None:
    family_a, pipeline_a = _build_family(tmp_path, "family-a")
    family_b, _ = _build_family(tmp_path, "family-b")
    payload = json.loads(pipeline_a.read_text(encoding="utf-8"))
    payload["family_contract"] = {
        "path": family_b.relative_to(tmp_path).as_posix(),
        "sha256": _sha256(family_b),
    }
    _write_json(pipeline_a, payload)

    with pytest.raises(
        family_context.FamilyContextError,
        match="family contract pin does not match",
    ):
        _load(tmp_path, family_a, pipeline_a)


def test_cross_family_evidence_swap_is_rejected(
    tmp_path: Path,
) -> None:
    family_a, pipeline_a = _build_family(tmp_path, "family-a")
    family_b, pipeline_b = _build_family(tmp_path, "family-b")
    context_a = _load(tmp_path, family_a, pipeline_a)
    context_b = _load(tmp_path, family_b, pipeline_b)
    report = {
        "family_context": context_b.evidence_binding("han-main"),
    }

    with pytest.raises(
        family_context.FamilyContextError,
        match="does not match",
    ):
        family_context.validate_evidence_context(
            report,
            context=context_a,
            collection_id="han-main",
            label="report",
        )


def test_cross_pipeline_evidence_swap_is_rejected(
    tmp_path: Path,
) -> None:
    family_a, pipeline_a = _build_family(
        tmp_path / "pipeline-a-root",
        "fixture-hand",
        pipeline_id="raster-authoring-v1",
    )
    family_b, pipeline_b = _build_family(
        tmp_path / "pipeline-b-root",
        "fixture-hand",
        pipeline_id="raster-authoring-v2",
    )
    context_a = _load(
        tmp_path / "pipeline-a-root",
        family_a,
        pipeline_a,
    )
    context_b = _load(
        tmp_path / "pipeline-b-root",
        family_b,
        pipeline_b,
    )

    with pytest.raises(
        family_context.FamilyContextError,
        match="does not match",
    ):
        family_context.validate_evidence_context(
            {
                "family_context": context_b.evidence_binding(
                    "han-main"
                )
            },
            context=context_a,
            collection_id="han-main",
        )


def test_cross_collection_evidence_swap_is_rejected(
    tmp_path: Path,
) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    context = _load(tmp_path, family_path, pipeline_path)

    with pytest.raises(
        family_context.FamilyContextError,
        match="does not match",
    ):
        family_context.validate_evidence_context(
            {
                "family_context": context.evidence_binding(
                    "nonhan-main"
                )
            },
            context=context,
            collection_id="han-main",
        )


def test_same_batch_id_has_family_isolated_cache_paths(
    tmp_path: Path,
) -> None:
    family_a, pipeline_a = _build_family(tmp_path, "family-a")
    family_b, pipeline_b = _build_family(tmp_path, "family-b")
    context_a = _load(tmp_path, family_a, pipeline_a)
    context_b = _load(tmp_path, family_b, pipeline_b)

    cache_a = context_a.batch_paths(
        "han-main",
        "same-0001",
    ).cache
    cache_b = context_b.batch_paths(
        "han-main",
        "same-0001",
    ).cache
    assert cache_a != cache_b
    assert "family-a" in cache_a.parts
    assert "family-b" in cache_b.parts


def test_stale_subordinate_contract_hash_is_rejected(
    tmp_path: Path,
) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    collections_path = family_path.parent / "collections.json"
    payload = json.loads(collections_path.read_text(encoding="utf-8"))
    payload["collections"][0]["encoded_count"] = 99
    _write_json(collections_path, payload)

    with pytest.raises(
        family_context.FamilyContextError,
        match="SHA-256 mismatch",
    ):
        _load(tmp_path, family_path, pipeline_path)


def test_stale_evidence_hash_is_rejected(
    tmp_path: Path,
) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    context = _load(tmp_path, family_path, pipeline_path)
    evidence = context.evidence_binding("han-main")
    tampered = deepcopy(evidence)
    tampered["collection_record_sha256"] = "0" * 64

    with pytest.raises(
        family_context.FamilyContextError,
        match="does not match",
    ):
        family_context.validate_evidence_context(
            {"family_context": tampered},
            context=context,
            collection_id="han-main",
        )


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))
    pipeline["workspace"]["cache_root"] = "../escaped-cache"
    _write_json(pipeline_path, pipeline)

    with pytest.raises(
        family_context.FamilyContextError,
        match="canonical project-relative",
    ):
        _load(tmp_path, family_path, pipeline_path)


def test_symlink_component_is_rejected(tmp_path: Path) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    family_root = family_path.parent
    outside = tmp_path / "outside"
    outside.mkdir()
    (family_root / "sources").symlink_to(
        outside,
        target_is_directory=True,
    )

    with pytest.raises(
        family_context.FamilyContextError,
        match="symlink component",
    ):
        _load(tmp_path, family_path, pipeline_path)


def test_overlapping_operational_roots_are_rejected(
    tmp_path: Path,
) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
    )
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))
    pipeline["workspace"]["cache_root"] = (
        "build/families/fixture-hand/cache"
    )
    _write_json(pipeline_path, pipeline)

    with pytest.raises(
        family_context.FamilyContextError,
        match="workspace roots overlap",
    ):
        _load(tmp_path, family_path, pipeline_path)


def test_duplicate_collection_ids_are_rejected(
    tmp_path: Path,
) -> None:
    family_path, pipeline_path = _build_family(
        tmp_path,
        "fixture-hand",
        collection_ids=("same", "same"),
    )
    with pytest.raises(
        family_context.FamilyContextError,
        match="duplicate collection id",
    ):
        _load(tmp_path, family_path, pipeline_path)


def test_cli_contract_arguments_are_mandatory(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        family_context.parse_args(
            ["--project-root", str(tmp_path)]
        )
