from __future__ import annotations

from pathlib import Path
import shutil

from fontTools.ttLib import TTFont
from PIL import Image

from scripts import build_imagegen_nonhan_semantic_evidence as semantic
from scripts import imagegen_nonhan_approval as approval


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _copy_file(project: Path, relative: str) -> None:
    source = PROJECT_ROOT / relative
    destination = project / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _fixture_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    _copy_file(
        project,
        "sources/imagegen/repertoires/nonhan-3060.json",
    )
    _copy_file(project, "sources/imagegen/raster/common-0001.png")
    for number in ("0005", "0006"):
        for relative in (
            f"sources/imagegen/approvals/nonhan-{number}.approval.json",
            f"sources/imagegen/batches/nonhan-{number}.source.json",
            f"sources/imagegen/raster/nonhan-{number}.png",
            f"sources/imagegen/copybooks/nonhan-{number}.png",
            f"sources/imagegen/prompts/nonhan-{number}.md",
            f"sources/imagegen/vector-reviews/nonhan-{number}.vector-review.json",
        ):
            _copy_file(project, relative)
        shutil.copytree(
            PROJECT_ROOT
            / f"build/imagegen/imagegen-nonhan-{number}",
            project / f"build/imagegen/imagegen-nonhan-{number}",
        )
    return project


def _build(project: Path) -> Path:
    return semantic.build_semantic_evidence(
        project_root=project,
        output_directory=(
            project / "build/imagegen/imagegen-nonhan-0206"
        ),
        manifest_path=(
            project
            / "sources/imagegen/semantic/nonhan-0206.semantic.json"
        ),
    )


def test_builds_exact_empty_metrics_and_is_deterministic(
    tmp_path: Path,
) -> None:
    project = _fixture_project(tmp_path)
    manifest = _build(project)
    first = {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in (
            manifest,
            project
            / "build/imagegen/imagegen-nonhan-0206/font/"
            "ClearHandTC-NonHan0206-Semantic.ttf",
            project
            / "build/imagegen/imagegen-nonhan-0206/proof/blank-render.png",
        )
    }

    _build(project)
    second = {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in (
            manifest,
            project
            / "build/imagegen/imagegen-nonhan-0206/font/"
            "ClearHandTC-NonHan0206-Semantic.ttf",
            project
            / "build/imagegen/imagegen-nonhan-0206/proof/blank-render.png",
        )
    }
    assert first == second

    repertoire = approval.load_frozen_repertoire(project)
    batch = approval.batch_from_repertoire(repertoire, "nonhan-0206")
    evidence = approval.semantic_evidence(
        project_root=project,
        repertoire=repertoire,
        batch=batch,
    )
    font = TTFont(evidence.font_path, checkChecksums=2)
    assert len(font.getBestCmap()) == 17
    assert all(
        font["glyf"][name].numberOfContours == 0
        for name in font.getGlyphOrder()[1:]
    )
    assert font["hmtx"].metrics["uni2007"] == (620, 0)
    assert font["hmtx"].metrics["uni2008"] == (164, 0)
    assert font["hmtx"].metrics["uni034F"] == (0, 0)
    assert font["vmtx"].metrics["uni034F"] == (0, 0)
    with Image.open(evidence.blank_proof_path) as image:
        image.load()
        assert image.mode == "L"
        assert image.size == (320, 64)
        assert image.getextrema() == (255, 255)
        assert image.text == {}
