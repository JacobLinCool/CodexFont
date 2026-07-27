from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

import pytest

from scripts import build_site


def _source_catalog() -> dict[str, Any]:
    return json.loads(build_site.CATALOG.read_text(encoding="utf-8"))


def _write_catalog(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_release_fixture(
    root: Path,
    *,
    identifier: str = "fixture-font",
) -> tuple[dict[str, Any], Path]:
    release = root / "dist" / identifier
    font_paths = {
        "ttf": "font/Fixture-Regular.ttf",
        "otf": "font/Fixture-Regular.otf",
        "woff": "font/Fixture-Regular.woff",
        "woff2": "font/Fixture-Regular.woff2",
        "css": "font/Fixture-Regular.css",
    }
    artifact_data = {
        path: f"{key}-artifact".encode()
        for key, path in font_paths.items()
    }
    artifact_data["OFL.txt"] = b"fixture OFL"
    for path in build_site.RELEASE_PROOF_PATHS:
        artifact_data[path] = f"{path}-artifact".encode()
    for relative, data in artifact_data.items():
        path = release / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    report = {
        "schema_version": 1,
        "font": {
            **font_paths,
            **{
                f"{key}_sha256": _sha256(artifact_data[path])
                for key, path in font_paths.items()
            },
        },
        "license": {
            "path": "OFL.txt",
            "sha256": _sha256(artifact_data["OFL.txt"]),
        },
        "proofs": [
            {
                "path": path,
                "sha256": _sha256(artifact_data[path]),
            }
            for path in sorted(build_site.RELEASE_PROOF_PATHS)
        ],
        "artifact_sha256": {
            path: _sha256(data)
            for path, data in sorted(artifact_data.items())
        },
    }
    (release / "report.json").write_text(
        json.dumps(report),
        encoding="utf-8",
    )
    font = {
        "id": identifier,
        "sources": {
            "ttf": f"dist/{identifier}/{font_paths['ttf']}",
            "otf": f"dist/{identifier}/{font_paths['otf']}",
            "woff": f"dist/{identifier}/{font_paths['woff']}",
            "woff2": f"dist/{identifier}/{font_paths['woff2']}",
            "report": f"dist/{identifier}/report.json",
            "license": f"dist/{identifier}/OFL.txt",
        },
    }
    return font, release


def test_site_build_contains_exact_font_coverage_and_downloads(
    tmp_path: Path,
) -> None:
    output = build_site.build(
        tmp_path / "site",
        _allow_temporary_output=True,
    )
    source_catalog = _source_catalog()
    public_catalog = json.loads(
        (output / "fonts.json").read_text(encoding="utf-8")
    )
    assert public_catalog["schema_version"] == 1
    source_fonts = source_catalog["fonts"]
    public_fonts = public_catalog["fonts"]
    assert [font["id"] for font in public_fonts] == [
        font["id"] for font in source_fonts
    ]

    for declared, font in zip(source_fonts, public_fonts, strict=True):
        assert font["id"] == declared["id"]
        assert font["family"] == declared["family"]
        assert font["version"] == declared["version"]
        assert font["opentype_version"] == declared["opentype_version"]
        assert font["encoded_count"] == declared["encoded_count"]
        assert font["status"] == declared["status"]

        progress = font["coverage_progress"]
        assert progress["encoded_count"] == font["encoded_count"]
        assert progress["target_count"] == 18071
        assert progress["missing_count"] == (
            progress["target_count"] - progress["encoded_count"]
        )
        assert progress["percent"] == round(
            progress["encoded_count"] / progress["target_count"] * 100,
            6,
        )
        assert [group["id"] for group in progress["groups"]] == [
            identifier for identifier, _ in build_site.PROGRESS_GROUPS
        ]
        assert sum(
            group["encoded_count"] for group in progress["groups"]
        ) == progress["encoded_count"]
        assert sum(
            group["target_count"] for group in progress["groups"]
        ) == progress["target_count"]
        assert all(
            group["missing_count"]
            == group["target_count"] - group["encoded_count"]
            for group in progress["groups"]
        )

        assert set(font["assets"]) == {
            "ttf",
            "otf",
            "woff",
            "woff2",
            "report",
            "license",
        }
        assert all(
            path.startswith(f"fonts/{font['id']}/")
            for path in font["assets"].values()
        )
        assert all(
            (output / path).is_file()
            for path in font["assets"].values()
        )

        assert font["coverage_url"] == f"coverage/{font['id']}.json"
        coverage = json.loads(
            (output / font["coverage_url"]).read_text(encoding="utf-8")
        )
        assert coverage["schema_version"] == 1
        assert coverage["font_id"] == font["id"]
        assert coverage["encoded_count"] == font["encoded_count"]
        assert sum(
            end - start + 1 for start, end in coverage["ranges"]
        ) == font["encoded_count"]
        assert coverage["ranges"] == sorted(coverage["ranges"])


def test_site_source_exposes_editor_and_exact_coverage_lab() -> None:
    html = (build_site.SOURCE / "index.html").read_text(encoding="utf-8")
    javascript = (build_site.SOURCE / "app.js").read_text(encoding="utf-8")
    stylesheet = (build_site.SOURCE / "styles.css").read_text(encoding="utf-8")
    assert 'contenteditable="true"' in html
    assert 'id="paragraph-input"' in html
    assert 'id="missing-list"' in html
    assert "containsCodepoint" in javascript
    assert "Promise.all(state.fonts.map(loadFontFace))" not in javascript
    assert "loadFontResources" in javascript
    assert "state.resourceLoads" in javascript
    assert 'card.disabled = loadState === "loading"' in javascript
    assert 'setFontCardState(font, "error")' in javascript
    assert "if (!state.editorInitialized)" in javascript
    assert "if (!state.editorTouched)" in javascript
    assert javascript.count("state.editorTouched = true") == 3
    assert 'class="font-card-meta" aria-live="polite"' in html
    assert 'id="font-list" role="list"' not in html
    assert 'class="font-card" type="button" role="listitem"' not in html
    assert "缺字以下方檢查結果為準" in html
    assert 'id="progress-stack"' in html
    assert "renderProgress" in javascript
    assert "讓 Codex 製作開放字體。" in html
    horizontal_features = (
        '.font-preview {\n'
        '  font-family: var(--preview-family);\n'
        '  font-feature-settings: "kern" 1, "mark" 1, "mkmk" 1;\n'
        '}'
    )
    assert horizontal_features in stylesheet
    assert '"vert" 1' not in stylesheet
    assert '"vrt2" 1' not in stylesheet


def test_site_catalog_rejects_unsupported_schema(
    tmp_path: Path,
) -> None:
    payload = _source_catalog()
    payload["schema_version"] = 2
    with pytest.raises(
        build_site.SiteBuildError,
        match="schema_version must be 1",
    ):
        build_site._load_catalog(_write_catalog(tmp_path, payload))


def test_site_catalog_sources_are_family_namespaced() -> None:
    catalog = _source_catalog()
    for font in catalog["fonts"]:
        prefix = f"dist/{font['id']}/"
        assert all(
            path.startswith(prefix)
            for path in font["sources"].values()
        )


def test_site_catalog_rejects_empty_font_list(
    tmp_path: Path,
) -> None:
    payload = _source_catalog()
    payload["fonts"] = []
    with pytest.raises(
        build_site.SiteBuildError,
        match="at least one font",
    ):
        build_site._load_catalog(_write_catalog(tmp_path, payload))


def test_site_catalog_rejects_duplicate_font_ids(
    tmp_path: Path,
) -> None:
    payload = _source_catalog()
    payload["fonts"].append(deepcopy(payload["fonts"][0]))
    with pytest.raises(
        build_site.SiteBuildError,
        match="invalid or duplicate font id",
    ):
        build_site._load_catalog(_write_catalog(tmp_path, payload))


def test_site_catalog_rejects_invalid_font_keys(
    tmp_path: Path,
) -> None:
    payload = _source_catalog()
    del payload["fonts"][0]["tagline"]
    with pytest.raises(
        build_site.SiteBuildError,
        match="invalid key set",
    ):
        build_site._load_catalog(_write_catalog(tmp_path, payload))


def test_site_catalog_rejects_invalid_source_keys(
    tmp_path: Path,
) -> None:
    payload = _source_catalog()
    del payload["fonts"][0]["sources"]["woff2"]
    with pytest.raises(
        build_site.SiteBuildError,
        match="invalid features or sources",
    ):
        build_site._load_catalog(_write_catalog(tmp_path, payload))


def test_site_copy_rejects_catalog_source_outside_report(
    tmp_path: Path,
) -> None:
    font = deepcopy(_source_catalog()["fonts"][0])
    font["sources"]["woff2"] = (
        "dist/clear-hand-tc/font/does-not-exist.woff2"
    )
    with pytest.raises(
        build_site.SiteBuildError,
        match="catalog sources do not match",
    ):
        build_site._copy_font(font, tmp_path / "site")


def test_site_copy_rejects_declared_cmap_count_drift(
    tmp_path: Path,
) -> None:
    font = deepcopy(_source_catalog()["fonts"][0])
    font["encoded_count"] += 1
    with pytest.raises(
        build_site.SiteBuildError,
        match="declares .* codepoints",
    ):
        build_site._copy_font(font, tmp_path / "site")


def test_site_copy_rejects_font_identity_drift(
    tmp_path: Path,
) -> None:
    font = deepcopy(_source_catalog()["fonts"][0])
    font["family"] = "Wrong Family"
    with pytest.raises(
        build_site.SiteBuildError,
        match="catalog identity does not match",
    ):
        build_site._copy_font(font, tmp_path / "site")


def test_site_build_rejects_invalid_requirement_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.loads(
        build_site.REQUIREMENTS.read_text(encoding="utf-8")
    )
    payload["policy"] = "invalid"
    malformed = tmp_path / "font_requirements.json"
    malformed.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(build_site, "REQUIREMENTS", malformed)
    with pytest.raises(
        build_site.SiteBuildError,
        match="invalid frozen requirement inventory",
    ):
        build_site._coverage_progress(set())


def test_site_progress_keeps_bopomofo_and_kana_distinct() -> None:
    progress = build_site._coverage_progress(
        {0x3105, 0x3042, 0x30A2}
    )
    groups = {
        group["id"]: group for group in progress["groups"]
    }
    assert groups["bopomofo"]["encoded_count"] == 1
    assert groups["kana"]["encoded_count"] == 2
    assert groups["bopomofo"]["target_count"] == 68
    assert groups["kana"]["target_count"] == 189


def test_release_validation_accepts_exact_report_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, release = _write_release_fixture(root)
    monkeypatch.setattr(build_site, "ROOT", root)

    validated = build_site._validate_release(font)

    assert validated["root"] == release
    assert set(validated["artifact_sha256"]) == {
        path.relative_to(release).as_posix()
        for path in release.rglob("*")
        if path.is_file() and path.name != "report.json"
    }


def test_release_validation_rejects_artifact_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, release = _write_release_fixture(root)
    (release / "font/Fixture-Regular.woff2").write_bytes(b"tampered")
    monkeypatch.setattr(build_site, "ROOT", root)

    with pytest.raises(
        build_site.SiteBuildError,
        match="artifact SHA-256 mismatch",
    ):
        build_site._validate_release(font)


def test_release_validation_rejects_stale_unreported_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, release = _write_release_fixture(root)
    (release / "font/Stale-Regular.ttf").write_bytes(b"stale")
    monkeypatch.setattr(build_site, "ROOT", root)

    with pytest.raises(
        build_site.SiteBuildError,
        match="directory does not match report inventory",
    ):
        build_site._validate_release(font)


def test_release_validation_rejects_incomplete_formal_proofs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, release = _write_release_fixture(root)
    report_path = release / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["proofs"].pop()
    report_path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(build_site, "ROOT", root)

    with pytest.raises(
        build_site.SiteBuildError,
        match="incomplete formal proof inventory",
    ):
        build_site._validate_release(font)


def test_release_validation_rejects_cross_family_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, _ = _write_release_fixture(root)
    font["sources"]["report"] = "dist/another-family/report.json"
    monkeypatch.setattr(build_site, "ROOT", root)

    with pytest.raises(
        build_site.SiteBuildError,
        match="report must be family-namespaced",
    ):
        build_site._validate_release(font)


def test_release_validation_rejects_symlink_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, release = _write_release_fixture(root)
    artifact = release / "font/Fixture-Regular.woff"
    target = tmp_path / "outside.woff"
    target.write_bytes(artifact.read_bytes())
    artifact.unlink()
    artifact.symlink_to(target)
    monkeypatch.setattr(build_site, "ROOT", root)

    with pytest.raises(
        build_site.SiteBuildError,
        match="release contains symlinks",
    ):
        build_site._validate_release(font)


def test_release_validation_rejects_symlink_report_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    font, release = _write_release_fixture(root)
    report = release / "report.json"
    outside = tmp_path / "outside-report.json"
    outside.write_bytes(report.read_bytes())
    report.unlink()
    report.symlink_to(outside)
    monkeypatch.setattr(build_site, "ROOT", root)

    with pytest.raises(
        build_site.SiteBuildError,
        match="release report must not traverse a symlink",
    ):
        build_site._validate_release(font)


@pytest.mark.parametrize(
    "relative",
    [
        ".git/site",
        "dist/site",
        "site/generated",
        "sources/site",
        "build/site/nested",
        "build/another-site",
    ],
)
def test_site_build_rejects_every_noncanonical_repository_output(
    relative: str,
) -> None:
    with pytest.raises(
        build_site.SiteBuildError,
        match="production output must be canonical build/site",
    ):
        build_site.build(build_site.ROOT / relative)


def test_site_output_policy_allows_canonical_by_default() -> None:
    assert build_site._validated_output_path(build_site.DEFAULT_OUTPUT) == (
        build_site.ROOT.resolve() / "build/site"
    )


def test_site_output_policy_allows_temp_only_with_private_capability(
    tmp_path: Path,
) -> None:
    assert build_site._validated_output_path(
        tmp_path / "site",
        _allow_temporary_output=True,
    ) == (
        tmp_path / "site"
    ).resolve()


def test_site_build_rejects_temp_without_private_capability(
    tmp_path: Path,
) -> None:
    output = tmp_path / "site"
    with pytest.raises(
        build_site.SiteBuildError,
        match="production output must be canonical build/site",
    ):
        build_site.build(output)
    assert not output.exists()


def test_site_build_allows_temp_only_with_private_test_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        build_site,
        "_load_catalog",
        lambda: {"schema_version": 1, "fonts": []},
    )
    output = build_site.build(
        tmp_path / "site",
        _allow_temporary_output=True,
    )

    assert output == (tmp_path / "site").resolve()
    assert (output / "fonts.json").is_file()


@pytest.mark.parametrize(
    "output",
    [
        Path("/"),
        Path.home(),
        build_site.ROOT,
        build_site.ROOT.parent,
        Path(tempfile.gettempdir()).resolve(),
        Path(tempfile.gettempdir()).resolve().parent,
    ],
)
def test_site_build_rejects_protected_or_non_temp_output(
    output: Path,
) -> None:
    with pytest.raises(
        build_site.SiteBuildError,
        match=(
            "protected output directory|"
            "production output must be canonical build/site"
        ),
    ):
        build_site.build(output)


@pytest.mark.parametrize(
    "output",
    [
        Path.home(),
        build_site.ROOT.parent,
        Path(tempfile.gettempdir()).resolve(),
    ],
)
def test_private_test_capability_does_not_authorize_unsafe_output(
    output: Path,
) -> None:
    with pytest.raises(build_site.SiteBuildError):
        build_site._validated_output_path(
            output,
            _allow_temporary_output=True,
        )


def test_atomic_install_rejects_non_temp_existing_directory(
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    output = Path.home()

    with pytest.raises(
        build_site.SiteBuildError,
        match="protected output directory",
    ):
        build_site._install_directory(staging, output)


def test_site_build_rejects_symlink_output(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    output = tmp_path / "linked-output"
    output.symlink_to(target, target_is_directory=True)

    with pytest.raises(
        build_site.SiteBuildError,
        match="must not traverse a symlink",
    ):
        build_site.build(output)


def test_site_build_rejects_symlink_output_ancestor(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(target, target_is_directory=True)

    with pytest.raises(
        build_site.SiteBuildError,
        match="must not traverse a symlink",
    ):
        build_site.build(linked_parent / "site")


def test_site_build_rejects_dot_segments_before_resolution(
    tmp_path: Path,
) -> None:
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(Path.home(), target_is_directory=True)

    with pytest.raises(
        build_site.SiteBuildError,
        match="must not contain dot segments",
    ):
        build_site.build(linked_parent / ".." / "site")


def test_atomic_install_rolls_back_existing_site_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "site"
    staging = tmp_path / ".site-staging"
    output.mkdir()
    staging.mkdir()
    (output / "version.txt").write_text("old", encoding="utf-8")
    (staging / "version.txt").write_text("new", encoding="utf-8")
    real_rename = Path.rename

    def fail_staging_install(self: Path, target: Path) -> Path:
        if self == staging and Path(target) == output:
            raise OSError("simulated install failure")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", fail_staging_install)
    with pytest.raises(
        build_site.SiteBuildError,
        match="site install failed; the previous site was restored",
    ):
        build_site._install_directory(
            staging,
            output,
            _allow_temporary_output=True,
        )

    assert (output / "version.txt").read_text(encoding="utf-8") == "old"
    assert (staging / "version.txt").read_text(encoding="utf-8") == "new"
    assert not list(tmp_path.glob(".site.rollback-*"))


def test_atomic_install_replaces_existing_site_without_stale_backup(
    tmp_path: Path,
) -> None:
    output = tmp_path / "site"
    staging = tmp_path / ".site-staging"
    output.mkdir()
    staging.mkdir()
    (output / "version.txt").write_text("old", encoding="utf-8")
    (staging / "version.txt").write_text("new", encoding="utf-8")

    build_site._install_directory(
        staging,
        output,
        _allow_temporary_output=True,
    )

    assert (output / "version.txt").read_text(encoding="utf-8") == "new"
    assert not staging.exists()
    assert not list(tmp_path.glob(".site.rollback-*"))
