from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts import repository_hygiene


def _write_release(
    dist: Path,
    family: str,
    artifacts: dict[str, bytes],
) -> Path:
    directory = dist / family
    for relative, contents in artifacts.items():
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    inventory = {
        relative: hashlib.sha256(contents).hexdigest()
        for relative, contents in sorted(artifacts.items())
    }
    (directory / "report.json").write_text(
        json.dumps({"artifact_sha256": inventory}) + "\n",
        encoding="utf-8",
    )
    return directory


def _write_complete_dist(root: Path) -> Path:
    dist = root / "dist"
    _write_release(
        dist,
        "clear-hand-tc",
        {
            "OFL.txt": b"license",
            "font/ClearHandTC-Regular.ttf": b"clear hand",
        },
    )
    _write_release(
        dist,
        "mew-note-tc",
        {
            "OFL.txt": b"license",
            "font/MewNoteTC-Regular.ttf": b"mew note",
        },
    )
    return dist


def test_repository_contains_only_active_proof_evidence() -> None:
    result = repository_hygiene.audit()
    assert result["active_audit_reports"] == 48
    assert result["referenced_evidence_files"] == 725
    assert result["evidence_files"] == 725
    assert result["missing_evidence"] == []
    assert result["orphaned_evidence"] == []
    assert result["redundant_audit_documents"] == []
    assert result["digest_mismatches"] == []
    assert result["forbidden_paths"] == []
    assert result["tracked_regenerable_files"] == []
    assert result["unexpected_lfs_files"] == []
    assert result["original_rasters_missing_lfs"] == []
    assert result["unexpected_font_binaries"] == []
    assert result["unexpected_dist_entries"] == []
    assert result["release_inventory_issues"] == []


def test_only_irreplaceable_family_rasters_are_lfs_eligible() -> None:
    assert repository_hygiene._is_original_raster(
        Path("sources/imagegen/raster/dict-han-0001.png")
    )
    assert repository_hygiene._is_original_raster(
        Path("families/mew-note-tc/pilots/mew-note-han-v2-raster.png")
    )
    assert repository_hygiene._is_original_raster(
        Path(
            "families/mew-note-tc/sources/imagegen/pipelines/"
            "original-raster-v1/collections/han-6060/batches/"
            "han-0001/raster.png"
        )
    )
    assert repository_hygiene._is_original_raster(
        Path(
            "families/mew-note-tc/sources/imagegen/pipelines/"
            "original-raster-v1/collections/vertical-93/batches/"
            "vertical-0002/vertical-orientation-raw-candidate.png"
        )
    )
    assert not repository_hygiene._is_original_raster(
        Path(
            "families/mew-note-tc/sources/imagegen/pipelines/"
            "original-raster-v1/collections/han-6060/batches/"
            "han-0001/identity-copybook.png"
        )
    )
    assert not repository_hygiene._is_original_raster(
        Path("build/families/mew-note-tc/proof.png")
    )


def test_lfs_policy_is_checked_in_both_directions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / ".git").mkdir()
    original = Path(
        "families/mew-note-tc/sources/imagegen/pipelines/"
        "original-raster-v1/collections/han-6060/batches/"
        "han-0001/raster.png"
    )
    wrong_pointer = Path("reports/preview.png")

    def fake_git_paths(_root: Path, *arguments: str) -> list[Path]:
        if arguments == ("ls-files",):
            return [original, wrong_pointer]
        if arguments[:1] == ("grep",):
            return [wrong_pointer]
        raise AssertionError(arguments)

    monkeypatch.setattr(
        repository_hygiene,
        "_git_paths",
        fake_git_paths,
    )

    assert repository_hygiene.original_rasters_missing_lfs(tmp_path) == [
        original
    ]
    assert repository_hygiene.unexpected_lfs_files(tmp_path) == [
        wrong_pointer
    ]


def test_release_font_binary_allowlist_is_family_namespaced() -> None:
    assert repository_hygiene.ALLOWED_FONT_BINARY_ROOTS == (
        Path("dist/clear-hand-tc/font"),
        Path("dist/mew-note-tc/font"),
    )
    assert Path("dist/font") in repository_hygiene.FORBIDDEN_PATHS
    assert Path("dist/proof") in repository_hygiene.FORBIDDEN_PATHS
    assert Path("dist/OFL.txt") in repository_hygiene.FORBIDDEN_PATHS
    assert Path("dist/report.json") in repository_hygiene.FORBIDDEN_PATHS


def test_temporary_helper_scripts_are_forbidden(
    tmp_path: Path,
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    temporary = scripts / "_tmp_manual_release_helper.py"
    temporary.write_text("raise SystemExit('temporary')\n", encoding="utf-8")

    assert repository_hygiene.forbidden_paths(tmp_path) == [
        Path("scripts/_tmp_manual_release_helper.py")
    ]


def test_dist_top_level_allows_only_two_real_family_directories(
    tmp_path: Path,
) -> None:
    dist = _write_complete_dist(tmp_path)
    assert repository_hygiene.unexpected_dist_entries(tmp_path) == []

    (dist / "stray.txt").write_text("not a release", encoding="utf-8")
    (dist / "other-family").mkdir()
    assert repository_hygiene.unexpected_dist_entries(tmp_path) == [
        Path("dist/other-family"),
        Path("dist/stray.txt"),
    ]


def test_release_reports_pin_the_complete_artifact_inventory(
    tmp_path: Path,
) -> None:
    dist = _write_complete_dist(tmp_path)
    assert repository_hygiene.release_inventory_issues(tmp_path) == []

    changed = dist / "mew-note-tc/font/MewNoteTC-Regular.ttf"
    changed.write_bytes(b"changed")
    issues = repository_hygiene.release_inventory_issues(tmp_path)
    assert len(issues) == 1
    assert "hash_mismatch=['font/MewNoteTC-Regular.ttf']" in issues[0]

    changed.write_bytes(b"mew note")
    undeclared = dist / "clear-hand-tc/proof/new.png"
    undeclared.parent.mkdir()
    undeclared.write_bytes(b"proof")
    issues = repository_hygiene.release_inventory_issues(tmp_path)
    assert len(issues) == 1
    assert "missing=['proof/new.png']" in issues[0]


def test_release_inventory_rejects_missing_family_and_malformed_paths(
    tmp_path: Path,
) -> None:
    dist = tmp_path / "dist"
    clear = _write_release(
        dist,
        "clear-hand-tc",
        {"font/ClearHandTC-Regular.ttf": b"clear hand"},
    )
    report = json.loads((clear / "report.json").read_text(encoding="utf-8"))
    report["artifact_sha256"]["../escape"] = "0" * 64
    (clear / "report.json").write_text(
        json.dumps(report) + "\n",
        encoding="utf-8",
    )

    issues = repository_hygiene.release_inventory_issues(tmp_path)
    assert any("malformed entries" in issue for issue in issues)
    assert any("dist/mew-note-tc: family release is missing" in issue for issue in issues)
