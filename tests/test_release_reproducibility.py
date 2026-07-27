from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import verify_release_reproducibility as reproducibility


def _write_release(root: Path, artifacts: dict[str, bytes]) -> Path:
    root.mkdir(parents=True)
    inventory: dict[str, str] = {}
    for relative, contents in artifacts.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        inventory[relative] = hashlib.sha256(contents).hexdigest()
    (root / "report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_sha256": dict(sorted(inventory.items())),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def test_byte_identical_release_trees_pass(tmp_path: Path) -> None:
    artifacts = {
        "OFL.txt": b"license",
        "font/Example.ttf": b"font",
        "proof/16px.png": b"proof",
    }
    first = _write_release(tmp_path / "first", artifacts)
    second = _write_release(tmp_path / "second", artifacts)

    result = reproducibility.compare_release_trees(
        first,
        second,
        family_id="example",
    )

    assert result["family_id"] == "example"
    assert result["artifact_count_including_report"] == 4
    assert len(result["tree_sha256"]) == 64


def test_changed_artifact_is_rejected(tmp_path: Path) -> None:
    first = _write_release(
        tmp_path / "first",
        {"font/Example.ttf": b"first"},
    )
    second = _write_release(
        tmp_path / "second",
        {"font/Example.ttf": b"second"},
    )

    with pytest.raises(
        reproducibility.ReleaseReproducibilityError,
        match=r"changed=\['font/Example.ttf', 'report.json'\]",
    ):
        reproducibility.compare_release_trees(
            first,
            second,
            family_id="example",
        )


def test_extra_artifact_is_rejected(tmp_path: Path) -> None:
    first = _write_release(
        tmp_path / "first",
        {"font/Example.ttf": b"font"},
    )
    second = _write_release(
        tmp_path / "second",
        {
            "font/Example.ttf": b"font",
            "proof/extra.png": b"extra",
        },
    )

    with pytest.raises(
        reproducibility.ReleaseReproducibilityError,
        match=r"extra=\['proof/extra.png'\]",
    ):
        reproducibility.compare_release_trees(
            first,
            second,
            family_id="example",
        )


def test_report_inventory_drift_is_rejected(tmp_path: Path) -> None:
    release = _write_release(
        tmp_path / "release",
        {"font/Example.ttf": b"font"},
    )
    report = json.loads(
        (release / "report.json").read_text(encoding="utf-8")
    )
    report["artifact_sha256"] = {"font/Example.ttf": "0" * 64}
    (release / "report.json").write_text(
        json.dumps(report) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        reproducibility.ReleaseReproducibilityError,
        match="report artifact inventory does not match",
    ):
        reproducibility.snapshot_release_tree(release)


def test_symlinked_artifact_is_rejected(tmp_path: Path) -> None:
    release = _write_release(
        tmp_path / "release",
        {"font/Example.ttf": b"font"},
    )
    outside = tmp_path / "outside.ttf"
    outside.write_bytes(b"outside")
    linked = release / "font/linked.ttf"
    linked.symlink_to(outside)

    with pytest.raises(
        reproducibility.ReleaseReproducibilityError,
        match="symlink is forbidden",
    ):
        reproducibility.snapshot_release_tree(release)


def test_default_pairs_are_family_namespaced() -> None:
    assert reproducibility.RELEASE_PAIRS == (
        (
            "clear-hand-tc",
            Path("dist/clear-hand-tc"),
            Path("build/imagegen/release-9120"),
        ),
        (
            "mew-note-tc",
            Path("dist/mew-note-tc"),
            Path("build/families/mew-note-tc/release-9088"),
        ),
    )
