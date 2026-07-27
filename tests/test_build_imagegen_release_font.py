from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
import pytest

from scripts import build_imagegen_release_font as release
from scripts import imagegen_nonhan_approval as nonhan_approval
from scripts import imagegen_vertical_approval as vertical_approval


def _rectangle(
    left: int = 100,
    bottom: int = 0,
    right: int = 500,
    top: int = 700,
):
    pen = TTGlyphPen(None)
    pen.moveTo((left, bottom))
    pen.lineTo((right, bottom))
    pen.lineTo((right, top))
    pen.lineTo((left, top))
    pen.closePath()
    return pen.glyph()


def _empty():
    return TTGlyphPen(None).glyph()


def _glyph(
    codepoint: int,
    *,
    outline=None,
    advance: int = 600,
    mark_placement: str | None = None,
    outline_required: bool = True,
) -> release.ReleaseGlyph:
    return release.ReleaseGlyph(
        codepoint=codepoint,
        name=release._glyph_name(codepoint),
        outline=outline if outline is not None else _rectangle(),
        horizontal_metric=(
            (0, -80) if mark_placement is not None else (advance, 100)
        ),
        vertical_metric=(
            (0, 0) if mark_placement is not None else (1024, 180)
        ),
        source_collection="synthetic-test",
        source_batch="synthetic",
        source_font_sha256="0" * 64,
        outline_required=outline_required,
        profile_id=(
            "nonspacing-mark"
            if mark_placement is not None
            else "proportional"
        ),
        mark_placement=mark_placement,
    )


def _vertical_alternate(
    base: release.ReleaseGlyph,
) -> release.VerticalAlternate:
    return release.VerticalAlternate(
        base_codepoint=base.codepoint,
        base_name=base.name,
        name=f"{base.name}.vert",
        outline=_rectangle(220, 80, 360, 620),
        horizontal_metric=base.horizontal_metric,
        vertical_metric=base.vertical_metric,
        preview_horizontal_metric=base.horizontal_metric,
        preview_vertical_metric=base.vertical_metric,
        source_batch="vertical-test",
        source_font_path=Path("synthetic-preview.ttf"),
        source_font_sha256="1" * 64,
        vertical_orientation="Tr",
        tailoring=None,
    )


def test_feature_builder_emits_kern_mark_mkmk_and_gdef(
    tmp_path: Path,
) -> None:
    glyphs = (
        _glyph(ord("A")),
        _glyph(ord("V")),
        _glyph(ord("a")),
        _glyph(ord("o")),
        _glyph(
            0x0301,
            outline=_rectangle(-80, 0, 80, 100),
            mark_placement="above",
        ),
        _glyph(
            0x034F,
            outline=_empty(),
            mark_placement="overlay",
            outline_required=False,
        ),
    )
    builder, summary = release._font_builder(
        glyphs,
        notdef=_rectangle(),
        x_height=520,
        cap_height=700,
    )
    path = tmp_path / "feature-smoke.ttf"
    builder.save(path)

    font = TTFont(path, checkChecksums=2)
    tags = {
        record.FeatureTag
        for record in font["GPOS"].table.FeatureList.FeatureRecord
    }
    assert tags == {"kern", "mark", "mkmk"}
    classes = font["GDEF"].table.GlyphClassDef.classDefs
    assert classes["uni0301"] == 3
    assert classes["uni034F"] == 3
    assert classes["uni0041"] == 1
    assert font["glyf"]["uni034F"].numberOfContours == 0
    assert font["hmtx"].metrics["uni034F"] == (0, -80)
    assert summary["kern_pair_rules"] > 0
    assert summary["mark_glyph_count"] == 2
    assert summary["placement_class_count"] == 2


def test_font_builder_uses_explicit_family_identity(
    tmp_path: Path,
) -> None:
    identity = release.FontIdentity(
        family="Mew Note TC",
        style="Regular",
        full_name="Mew Note TC Regular",
        postscript_name="MewNoteTC-Regular",
        version="Version 0.100",
        revision=0.1,
        unique_id="Mew Note TC 0.100",
        copyright="Copyright 2026 Test Authors",
        license_description="Test license",
        license_url="https://example.invalid/license",
    )
    builder, _summary = release._font_builder(
        (
            _glyph(ord("A")),
            _glyph(
                0x0301,
                outline=_rectangle(-80, 0, 80, 100),
                mark_placement="above",
            ),
        ),
        notdef=_rectangle(),
        x_height=520,
        cap_height=700,
        identity=identity,
    )
    path = tmp_path / "alternate-identity.ttf"
    builder.save(path)

    with TTFont(path, checkChecksums=2) as font:
        assert release._name_values(font, 1) == {identity.family}
        assert release._name_values(font, 3) == {identity.unique_id}
        assert release._name_values(font, 4) == {identity.full_name}
        assert release._name_values(font, 5) == {identity.version}
        assert release._name_values(font, 6) == {
            identity.postscript_name
        }
        assert release._name_values(font, 13) == {
            identity.license_description
        }
        assert release._name_values(font, 14) == {
            identity.license_url
        }
        assert font["head"].fontRevision == pytest.approx(
            identity.revision,
            abs=1e-5,
        )


def test_font_validator_rejects_family_total_glyph_count_mismatch(
    tmp_path: Path,
) -> None:
    glyph = _glyph(ord("A"))
    mark = _glyph(
        0x0301,
        outline=_rectangle(-80, 0, 80, 100),
        mark_placement="above",
    )
    notdef = _rectangle()
    builder, _summary = release._font_builder(
        (glyph, mark),
        notdef=notdef,
        x_height=520,
        cap_height=700,
    )
    path = tmp_path / "wrong-family-total.ttf"
    builder.save(path)

    with pytest.raises(
        release.ReleaseFontBuildError,
        match=r"total glyph count is 3, expected 4$",
    ):
        release._validate_font(
            path,
            (glyph, mark),
            (),
            notdef=notdef,
            expected_total_glyph_count=4,
        )


def test_feature_builder_emits_unencoded_vert_and_vrt2_substitutions(
    tmp_path: Path,
) -> None:
    base = _glyph(ord("A"))
    mark = _glyph(
        0x0301,
        outline=_rectangle(-80, 0, 80, 100),
        mark_placement="above",
    )
    alternate = _vertical_alternate(base)
    builder, summary = release._font_builder(
        (base, mark),
        alternates=(alternate,),
        notdef=_rectangle(),
        x_height=520,
        cap_height=700,
    )
    path = tmp_path / "vertical-feature-smoke.ttf"
    builder.save(path)

    font = TTFont(path, checkChecksums=2)
    try:
        assert font.getBestCmap() == {
            base.codepoint: base.name,
            mark.codepoint: mark.name,
        }
        assert font.getGlyphOrder() == [
            ".notdef",
            base.name,
            mark.name,
            alternate.name,
        ]
        assert release._gsub_feature_mapping(font, "vert") == {
            base.name: alternate.name
        }
        assert release._gsub_feature_mapping(font, "vrt2") == {
            base.name: alternate.name
        }
        assert (
            font["hmtx"].metrics[alternate.name]
            == font["hmtx"].metrics[base.name]
        )
        assert (
            font["vmtx"].metrics[alternate.name]
            == font["vmtx"].metrics[base.name]
        )
        assert (
            font["vhea"].caretSlopeRise,
            font["vhea"].caretSlopeRun,
            font["vhea"].caretOffset,
        ) == (0, 1, 0)
    finally:
        font.close()
    assert summary["vertical_substitution_count"] == 1
    assert summary["vertical_feature_count"] == 2


def test_extracts_all_approved_vertical_outlines_and_inherits_base_metrics() -> None:
    approvals = vertical_approval.load_complete_approvals()
    bases: list[release.ReleaseGlyph] = []
    for approval in approvals:
        for record in approval["glyphs"]:
            codepoint = int(record["base_codepoint"][2:], 16)
            horizontal_policy = record["base_metrics"]["horizontal_advance"]
            horizontal_advance = (
                horizontal_policy["value"]
                if horizontal_policy["kind"] == "fixed"
                else 640
            )
            vertical_advance = record["base_metrics"]["vertical_advance"][
                "value"
            ]
            bases.append(
                release.ReleaseGlyph(
                    codepoint=codepoint,
                    name=release._glyph_name(codepoint),
                    outline=_rectangle(),
                    horizontal_metric=(horizontal_advance, 91),
                    vertical_metric=(vertical_advance, 173),
                    source_collection="approved-base-test",
                    source_batch="base-test",
                    source_font_sha256="2" * 64,
                    outline_required=True,
                    profile_id=record["base_profile_id"],
                    mark_placement=None,
                )
            )

    alternates = release._extract_vertical_alternates(
        approvals,
        encoded_glyphs=bases,
        project_root=release.ROOT,
    )
    assert len(alternates) == 93
    assert len({item.base_codepoint for item in alternates}) == 93
    assert len({item.name for item in alternates}) == 93
    bases_by_codepoint = {item.codepoint: item for item in bases}
    for alternate in alternates:
        base = bases_by_codepoint[alternate.base_codepoint]
        assert alternate.name == f"{base.name}.vert"
        assert alternate.horizontal_metric[0] == base.horizontal_metric[0]
        assert alternate.vertical_metric[0] == base.vertical_metric[0]
        assert alternate.horizontal_metric[1] == (
            alternate.preview_horizontal_metric[1]
            + (
                base.horizontal_metric[0]
                - alternate.preview_horizontal_metric[0]
            )
            // 2
        )
        assert (
            alternate.vertical_metric[1]
            == alternate.preview_vertical_metric[1]
        )
        assert alternate.outline.numberOfContours > 0


def test_latin_base_groups_accents_and_special_letters() -> None:
    assert release._latin_base("Á") == "A"
    assert release._latin_base("ç") == "c"
    assert release._latin_base("Œ") == "O"
    assert release._latin_base("ł") == "l"
    assert release._latin_base("ㄅ") is None


def test_release_artifact_inventory_excludes_only_root_report(
    tmp_path: Path,
) -> None:
    root_report = tmp_path / "report.json"
    root_report.write_text("self-referential root report", encoding="utf-8")
    font = tmp_path / "font/release.ttf"
    font.parent.mkdir()
    font.write_bytes(b"font")
    nested_report = tmp_path / "evidence/report.json"
    nested_report.parent.mkdir()
    nested_report.write_text("nested evidence report", encoding="utf-8")

    assert release._artifact_hashes(tmp_path) == {
        "evidence/report.json": release._sha256(nested_report),
        "font/release.ttf": release._sha256(font),
    }


def test_notdef_report_pins_exact_approved_source_font(
    tmp_path: Path,
) -> None:
    base = _glyph(ord("A"))
    mark = _glyph(
        0x0301,
        outline=_rectangle(-80, 0, 80, 100),
        mark_placement="above",
    )
    builder, _summary = release._font_builder(
        (base, mark),
        notdef=_rectangle(),
        x_height=520,
        cap_height=700,
    )
    source_font = tmp_path / "approved-common-0001.ttf"
    builder.save(source_font)
    admitted = SimpleNamespace(
        batch=SimpleNamespace(batch_id="common-0001"),
        ttf_path=source_font,
    )

    notdef = release._notdef_from_first_han((admitted,))
    assert notdef.outline.numberOfContours > 0
    assert release._notdef_report_record(notdef) == {
        "glyph_order_index": 0,
        "glyph_name": ".notdef",
        "encoded": False,
        "source_collection": "common-han-3000",
        "source_batch": "common-0001",
        "source_font_sha256": release._sha256(source_font),
    }


def test_nonhan_release_repertoire_record_has_exact_frozen_sequence_hashes() -> None:
    repertoire = nonhan_approval.load_frozen_repertoire()
    record = release._nonhan_repertoire_record(
        repertoire,
        project_root=release.ROOT,
    )

    assert set(record) == {
        "path",
        "sha256",
        "repertoire_id",
        "count",
        "sequence_hashes",
    }
    assert record["path"] == (
        nonhan_approval.REPERTOIRE_RELATIVE_PATH.as_posix()
    )
    assert record["sha256"] == nonhan_approval.REPERTOIRE_SHA256
    assert record["repertoire_id"] == nonhan_approval.REPERTOIRE_ID
    assert record["count"] == release.NONHAN_COUNT
    assert record["sequence_hashes"] == {
        "serialization": (
            nonhan_approval.SEQUENCE_HASH_SERIALIZATION
        ),
        "canonical": nonhan_approval.CANONICAL_SEQUENCE_SHA256,
        "authoring": nonhan_approval.AUTHORING_SEQUENCE_SHA256,
        "visible_authoring": (
            nonhan_approval.VISIBLE_AUTHORING_SEQUENCE_SHA256
        ),
        "serialization_definition": {
            "algorithm": "SHA-256",
            "encoding": "ASCII",
            "record_format": "U+{codepoint:04X}\\n",
            "hexadecimal_case": "uppercase",
            "hexadecimal_width": (
                "minimum 4 digits; supplementary scalars use 5 or 6 digits"
            ),
            "record_order": "the named repertoire sequence",
            "final_record_terminator": "LF present",
            "byte_order_mark": "none",
        },
    }


def test_nonhan_release_repertoire_record_rejects_sequence_schema_drift() -> None:
    repertoire = nonhan_approval.load_frozen_repertoire()
    drifted = replace(
        repertoire,
        sequence_hashes={
            **repertoire.sequence_hashes,
            "unexpected": "0" * 64,
        },
    )
    with pytest.raises(
        release.ReleaseFontBuildError,
        match="sequence-hash schema drift",
    ):
        release._nonhan_repertoire_record(
            drifted,
            project_root=release.ROOT,
        )


def test_coverage_character_hash_serialization_is_exact_utf8() -> None:
    assert release._characters_sha256_serialization() == {
        "algorithm": "SHA-256",
        "scope": (
            "encoded glyphs in release glyph order; .notdef and unencoded "
            "vertical alternates excluded"
        ),
        "serialization": (
            "raw Unicode scalar values concatenated without separators or "
            "a final terminator"
        ),
        "normalization": "none",
        "encoding": "UTF-8",
        "byte_order_mark": "none",
    }
    assert release._sha256_text("é") != release._sha256_text("e\u0301")


def test_release_destination_is_strictly_allowlisted(tmp_path: Path) -> None:
    project_root = tmp_path.resolve()
    assert release._validated_release_destination(
        project_root,
        project_root / "dist/clear-hand-tc",
    ) == project_root / "dist/clear-hand-tc"
    assert release._validated_release_destination(
        project_root,
        Path("build/imagegen/release-9120"),
    ) == project_root / "build/imagegen/release-9120"

    for forbidden in (
        project_root,
        project_root / "dist",
        project_root / "dist/mew-note-tc",
        project_root / "dist/other-family",
        project_root / "build",
        project_root / "build/imagegen",
        project_root / "sources",
        project_root.parent,
    ):
        with pytest.raises(
            release.ReleaseFontBuildError,
            match="release output must be exactly one of",
        ):
            release._validated_release_destination(
                project_root,
                forbidden,
            )


def test_release_destination_rejects_symlink_components(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "project").resolve()
    project_root.mkdir()
    external = tmp_path / "external"
    external.mkdir()

    (project_root / "dist").symlink_to(external, target_is_directory=True)
    with pytest.raises(
        release.ReleaseFontBuildError,
        match="contains a symlink",
    ):
        release._validated_release_destination(
            project_root,
            project_root / "dist/clear-hand-tc",
        )

    (project_root / "dist").unlink()
    (project_root / "build").symlink_to(external, target_is_directory=True)
    with pytest.raises(
        release.ReleaseFontBuildError,
        match="contains a symlink",
    ):
        release._validated_release_destination(
            project_root,
            project_root / "build/imagegen/release-9120",
        )


def test_release_install_swaps_and_removes_backup(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    destination = dist / "clear-hand-tc"
    destination.mkdir(parents=True)
    (destination / "old.txt").write_text("old", encoding="utf-8")
    mew = dist / "mew-note-tc"
    mew.mkdir()
    (mew / "release.txt").write_text("mew", encoding="utf-8")
    stage = dist / ".clear-hand-tc-stage"
    stage.mkdir()
    (stage / "new.txt").write_text("new", encoding="utf-8")

    release._install_release_directory(stage, destination)

    assert not stage.exists()
    assert not (destination / "old.txt").exists()
    assert (destination / "new.txt").read_text(encoding="utf-8") == "new"
    assert (mew / "release.txt").read_text(encoding="utf-8") == "mew"
    assert list(dist.glob(".clear-hand-tc.backup-*")) == []


def test_release_install_rolls_back_when_stage_swap_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dist = tmp_path / "dist"
    destination = dist / "clear-hand-tc"
    destination.mkdir(parents=True)
    (destination / "old.txt").write_text("old", encoding="utf-8")
    mew = dist / "mew-note-tc"
    mew.mkdir()
    (mew / "release.txt").write_text("mew", encoding="utf-8")
    stage = dist / ".clear-hand-tc-stage"
    stage.mkdir()
    (stage / "new.txt").write_text("new", encoding="utf-8")
    real_replace = Path.replace

    def fail_stage_swap(self: Path, target: Path) -> Path:
        if self == stage and Path(target) == destination:
            raise OSError("injected stage swap failure")
        return real_replace(self, target)

    monkeypatch.setattr(Path, "replace", fail_stage_swap)
    with pytest.raises(
        release.ReleaseFontBuildError,
        match="previous release restored",
    ):
        release._install_release_directory(stage, destination)

    assert (destination / "old.txt").read_text(encoding="utf-8") == "old"
    assert not (destination / "new.txt").exists()
    assert (stage / "new.txt").read_text(encoding="utf-8") == "new"
    assert (mew / "release.txt").read_text(encoding="utf-8") == "mew"
    assert list(dist.glob(".clear-hand-tc.backup-*")) == []
