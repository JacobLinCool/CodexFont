from __future__ import annotations

import json
from types import SimpleNamespace

from fontTools.pens.ttGlyphPen import TTGlyphPen
import pytest

from scripts import build_imagegen_release_font as engine
from scripts import build_mew_note_release_font as mew


def test_release_identity_matches_frozen_family_contract() -> None:
    family = json.loads(
        (mew.ROOT / "families/mew-note-tc/family.json").read_text(
            encoding="utf-8"
        )
    )
    identity = family["release_identity"]

    assert mew.IDENTITY.version == (
        f"Version {float(identity['opentype_version']):.3f}"
    )
    assert mew.IDENTITY.revision == identity["font_revision"]


def test_build_release_passes_mew_glyph_total_to_shared_engine(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopAfterWebContractCheck(RuntimeError):
        pass

    output = tmp_path / "release"
    notdef = _rectangle()
    validated_counts: list[int] = []
    web_counts: list[int] = []

    monkeypatch.setattr(
        mew,
        "_allowed_destination",
        lambda _project_root, destination: destination,
    )
    monkeypatch.setattr(
        mew.approval,
        "validate_approval",
        lambda **_kwargs: object(),
    )
    monkeypatch.setattr(
        mew,
        "_load_source_outlines",
        lambda _admitted: ({}, {}),
    )
    monkeypatch.setattr(
        mew,
        "_build_encoded_glyphs",
        lambda _admitted, _outlines: (),
    )
    monkeypatch.setattr(
        mew,
        "_build_vertical_alternates",
        lambda _glyphs, _sources: (),
    )
    monkeypatch.setattr(
        mew,
        "_notdef",
        lambda _admitted: (notdef, object()),
    )

    def fake_write_sfnt(stage, **_kwargs):
        font_directory = stage / "font"
        font_directory.mkdir()
        ttf = font_directory / "MewNoteTC-Regular.ttf"
        otf = font_directory / "MewNoteTC-Regular.otf"
        ttf.write_bytes(b"ttf")
        otf.write_bytes(b"otf")
        return ttf, otf, {}

    def fake_validate(_path, _glyphs, _alternates, **kwargs):
        assert kwargs["identity"] == mew.IDENTITY
        validated_counts.append(kwargs["expected_total_glyph_count"])

    def fake_write_web(_ttf, **kwargs):
        assert kwargs["identity"] == mew.IDENTITY
        web_counts.append(kwargs["expected_total_glyph_count"])
        raise StopAfterWebContractCheck

    monkeypatch.setattr(
        mew.engine,
        "_write_sfnt_fonts",
        fake_write_sfnt,
    )
    monkeypatch.setattr(
        mew.engine,
        "_validate_font",
        fake_validate,
    )
    monkeypatch.setattr(
        mew.engine,
        "_write_web_fonts",
        fake_write_web,
    )

    assert mew.TOTAL_GLYPH_COUNT == (
        1 + mew.CMAP_COUNT + mew.VERTICAL_COUNT
    ) == 9_182
    with pytest.raises(StopAfterWebContractCheck):
        mew.build_release(
            project_root=tmp_path,
            output_directory=output,
        )

    assert validated_counts == [mew.TOTAL_GLYPH_COUNT] * 2
    assert web_counts == [mew.TOTAL_GLYPH_COUNT]


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


def _record(
    character: str,
    *,
    profile_id: str,
    horizontal: dict[str, int | str],
    vertical_advance: int = 1024,
    left: int = 0,
    right: int = 0,
) -> dict[str, object]:
    return {
        "character": character,
        "codepoint": f"U+{ord(character):04X}",
        "profile_id": profile_id,
        "metrics": {
            "horizontal_advance": horizontal,
            "vertical_advance": {
                "kind": "fixed",
                "value": vertical_advance,
            },
            "side_bearings": {
                "left": left,
                "right": right,
            },
        },
    }


def test_source_proportional_metric_uses_frozen_bearings() -> None:
    outline, horizontal, vertical, placement = (
        mew._position_visible_nonhan(
            _rectangle(),
            _record(
                "!",
                profile_id="proportional",
                horizontal={"kind": "source-proportional"},
                left=48,
                right=48,
            ),
        )
    )

    assert mew._bounds(outline) == (48, 0, 448, 700)
    assert horizontal == (496, 48)
    assert vertical == (
        1024,
        engine.VERTICAL_ORIGIN_Y - 700,
    )
    assert placement is None


def test_fixed_metric_centers_ink_inside_frozen_bearings() -> None:
    outline, horizontal, _vertical, placement = (
        mew._position_visible_nonhan(
            _rectangle(100, 0, 400, 700),
            _record(
                "0",
                profile_id="tabular-digit",
                horizontal={"kind": "fixed", "value": 620},
                left=56,
                right=56,
            ),
        )
    )

    assert mew._bounds(outline) == (160, 0, 460, 700)
    assert horizontal == (620, 160)
    assert placement is None


def test_fixed_metric_rejects_source_ink_outside_envelope() -> None:
    with pytest.raises(
        mew.MewNoteReleaseBuildError,
        match="regenerate the source glyph narrower",
    ):
        mew._position_visible_nonhan(
            _rectangle(0, 0, 600, 700),
            _record(
                "0",
                profile_id="tabular-digit",
                horizontal={"kind": "fixed", "value": 620},
                left=56,
                right=56,
            ),
        )


def test_nonspacing_mark_is_centered_at_origin_and_classified() -> None:
    outline, horizontal, vertical, placement = (
        mew._position_visible_nonhan(
            _rectangle(-80, 400, 80, 500),
            _record(
                "\u0300",
                profile_id="nonspacing-mark",
                horizontal={"kind": "fixed", "value": 0},
                vertical_advance=0,
            ),
        )
    )

    assert mew._bounds(outline) == (-80, 0, 80, 100)
    assert horizontal == (0, -80)
    assert vertical == (
        0,
        engine.VERTICAL_ORIGIN_Y - 100,
    )
    assert placement == "above"


def test_vertical_outline_is_centered_without_shape_scaling() -> None:
    outline, lsb = mew._center_outline(
        _rectangle(120, 0, 420, 700),
        advance=1024,
    )

    assert mew._bounds(outline) == (362, 0, 662, 700)
    assert lsb == 362


def test_final_proof_coverage_digest_requires_every_contract_size() -> None:
    glyph = engine.ReleaseGlyph(
        codepoint=ord("A"),
        name="uni0041",
        outline=_rectangle(),
        horizontal_metric=(1024, 100),
        vertical_metric=(1024, 324),
        source_collection="test",
        source_batch="test-0001",
        source_font_sha256="a" * 64,
        outline_required=True,
        profile_id="test",
        mark_placement=None,
    )
    complete = {
        "U+0041": {
            str(size): size
            for size in mew.PROOF_SIZES
        }
    }

    assert len(mew._coverage_digest((glyph,), complete)) == 64
    incomplete = {
        "U+0041": {
            str(size): size
            for size in mew.PROOF_SIZES[:-1]
        }
    }
    with pytest.raises(
        mew.MewNoteReleaseBuildError,
        match="proof size inventory drift",
    ):
        mew._coverage_digest((glyph,), incomplete)


def test_complete_frozen_repertoires_compile_to_exact_partition() -> None:
    han = json.loads(mew.HAN_REPERTOIRE.read_text(encoding="utf-8"))
    nonhan = json.loads(
        mew.NONHAN_REPERTOIRE.read_text(encoding="utf-8")
    )
    withheld_labels = {
        codepoint
        for frozen_batch in han["batches"]
        if ("han-6060", frozen_batch["batch_id"])
        in mew.approval.WITHHELD_BATCHES
        for codepoint in frozen_batch["codepoints"]
    }
    batch = SimpleNamespace(
        batch_id="synthetic-reviewed-batch",
        ttf_sha256="a" * 64,
    )
    outlines = {
        int(record["codepoint"]): (_rectangle(), batch)
        for record in han["glyphs"]
    }
    for record in nonhan["glyphs"]:
        if not record["outline_required"]:
            continue
        codepoint = int(record["codepoint"][2:], 16)
        horizontal = record["metrics"]["horizontal_advance"]
        if record["profile_id"] == "nonspacing-mark":
            width = 80
        elif horizontal["kind"] == "fixed":
            bearings = record["metrics"]["side_bearings"]
            available = (
                horizontal["value"]
                - bearings["left"]
                - bearings["right"]
            )
            width = max(1, min(280, available))
        else:
            width = 280
        outlines[codepoint] = (
            _rectangle(0, 0, width, 700),
            batch,
        )

    glyphs = mew._build_encoded_glyphs(
        SimpleNamespace(
            plan_sha256="b" * 64,
            withheld_entries=[
                {"codepoint": codepoint}
                for codepoint in sorted(withheld_labels)
            ],
        ),
        outlines,
    )
    codepoints = {glyph.codepoint for glyph in glyphs}

    assert len(withheld_labels) == (
        mew.PLANNED_HAN_COUNT - mew.HAN_COUNT
    )
    assert codepoints.isdisjoint(
        int(codepoint[2:], 16) for codepoint in withheld_labels
    )
    assert len(glyphs) == mew.CMAP_COUNT
    assert len(codepoints) == mew.CMAP_COUNT
    assert sum(glyph.outline_required for glyph in glyphs) == (
        mew.VISIBLE_COUNT
    )
    assert sum(not glyph.outline_required for glyph in glyphs) == (
        mew.SEMANTIC_EMPTY_COUNT
    )
    assert sum(0x3041 <= value <= 0x309F for value in codepoints) == 93
    assert sum(0x30A0 <= value <= 0x30FF for value in codepoints) == 96
