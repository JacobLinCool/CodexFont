from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import mew_note_batch_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
FIRST_FIVE = tuple(f"han-{index:04d}" for index in range(1, 6))


def _context():
    return evidence.load_context(ROOT)


def _object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_contract_pins_approved_family_chain_and_family_local_pipeline() -> None:
    context = _context()
    contract = evidence.load_contract(context)
    assert contract["family_contract"] == (
        context.family_contract.evidence_record()
    )
    assert contract["pipeline_contract"] == (
        context.pipeline_contract.evidence_record()
    )
    assert contract["authoring_contract"] == (
        context.authoring_contract.evidence_record()
    )
    assert contract["collection_contract"] == (
        context.collection_contract.evidence_record()
    )
    assert contract["history_policy"]["rejected_outputs"] == "hash-only"
    assert (
        contract["vector_policy"]["family_local_raster_root_required"]
        is True
    )
    assert (
        contract["vector_policy"]["clear_hand_font_identity_allowed"]
        is False
    )
    assert [reference["path"] for reference in contract["style_references"]] == [
        "families/mew-note-tc/pilots/mew-note-han-v2-raster.png",
        "families/mew-note-tc/pilots/mew-note-nonhan-raster.png",
    ]


@pytest.mark.parametrize("batch_id", FIRST_FIVE)
def test_first_five_materializations_are_deterministic_and_exact(
    batch_id: str,
) -> None:
    context = _context()
    before = evidence.validate_draft(context, "han-6060", batch_id)
    before_bytes = {
        name: (
            context.batch_paths("han-6060", batch_id).source / name
        ).read_bytes()
        for name in (
            "prompt.md",
            "identity-copybook.png",
            "draft.json",
            "tool-step-0001.txt",
        )
    }
    rebuilt = evidence.materialize_batch(context, "han-6060", batch_id)
    assert rebuilt == before
    for name, expected in before_bytes.items():
        assert (
            context.batch_paths("han-6060", batch_id).source / name
        ).read_bytes() == expected

    batch = evidence.frozen_batch(context, "han-6060", batch_id)
    assert [entry["cell"] for entry in batch["entries"]] == list(
        range(1, 17)
    )
    assert batch["tail_terminal_cells"] == [2, 6, 10, 14]
    prompt = (
        context.batch_paths("han-6060", batch_id).source
        / "tool-step-0001.txt"
    ).read_text(encoding="utf-8")
    assert "exactly five horizontal and five vertical" in prompt
    assert "Tail-terminal cells only: 2, 6, 10, 14" in prompt
    for entry in batch["entries"]:
        assert (
            f"Cell {entry['cell']:02d}: {entry['codepoint']} "
            f"{entry['character']} — {entry['motif_class']}"
        ) in prompt


def test_copybook_is_identity_only_and_uses_only_pinned_external_fonts() -> None:
    context = _context()
    contract = evidence.load_contract(context)
    allowed = {
        str(Path(item["path"]).expanduser().resolve()): item["sha256"]
        for item in contract["identity_reference_fonts"]
    }
    for batch_id in FIRST_FIVE:
        root = context.batch_paths("han-6060", batch_id).source
        draft = _object(root / "draft.json")
        copybook = draft["identity_copybook"]
        assert copybook["role"] == (
            "identity-reference-only-no-outline-import"
        )
        assert len(copybook["glyphs"]) == 16
        for glyph in copybook["glyphs"]:
            font = glyph["external_font"]
            resolved = str(Path(font["path"]).expanduser().resolve())
            assert font["sha256"] == allowed[resolved]
            assert font["binary_committed"] is False
        serialized = json.dumps(draft, ensure_ascii=False)
        assert "sources/imagegen/raster/" not in serialized
        assert "sources/imagegen/vector-reviews/" not in serialized
        assert "sources/imagegen/approvals/" not in serialized


def test_generation_registration_rejects_unretained_or_unchained_evidence(
    tmp_path: Path,
) -> None:
    context = _context()
    root = context.batch_paths("han-6060", "han-0001").source
    style = (
        ROOT / "families/mew-note-tc/pilots/mew-note-han-v2-raster.png"
    )
    copybook = root / "identity-copybook.png"
    fake_output = tmp_path / "fake.png"
    fake_output.write_bytes(copybook.read_bytes())
    base_inputs = (
        evidence.GenerationInput(
            role="style-reference",
            path=style,
            sha256=evidence.sha256_path(style),
            retention="retained-reference",
        ),
        evidence.GenerationInput(
            role="identity-copybook",
            path=copybook,
            sha256=evidence.sha256_path(copybook),
            retention="retained-reference",
        ),
    )
    rejected_with_path = evidence.GenerationStep(
        operation="generate",
        disposition="rejected",
        call_id="exec-00000000-0000-0000-0000-000000000001",
        prompt_path=root / "tool-step-0001.txt",
        inputs=base_inputs,
        output_sha256=evidence.sha256_path(fake_output),
        output_path=fake_output,
    )
    with pytest.raises(
        evidence.MewNoteBatchError,
        match="rejected output must be hash-only",
    ):
        evidence.register_history(
            context,
            "han-6060",
            "han-0001",
            steps=[rejected_with_path],
        )


def test_vector_loader_requires_explicit_family_raster_namespace(
    tmp_path: Path,
) -> None:
    raster_root = tmp_path / "family-raster"
    raster_root.mkdir()
    raster = raster_root / "raster.png"
    raster.write_bytes(
        (
            ROOT
            / "families/mew-note-tc/pilots/mew-note-han-v2-raster.png"
        ).read_bytes()
    )
    descriptor = raster_root / "source.json"
    descriptor.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "batch_id": "mew-loader-test",
                "state": "generated-unreviewed",
                "raster": "raster.png",
                "raster_sha256": evidence.sha256_path(raster),
                "grid": {
                    "rows": 4,
                    "columns": 4,
                    "characters": [
                        "永",
                        "貓",
                        "手",
                        "寫",
                        "龍",
                        "鬱",
                        "國",
                        "愛",
                        "A",
                        "a",
                        "G",
                        "g",
                        "〇",
                        "八",
                        "あ",
                        "ア",
                    ],
                    "empty_grid_cells": 0,
                },
                "review": {
                    "topology": "pending",
                    "raster_quality": "pending",
                    "vector_quality": "pending",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        evidence.imagegen_font_pipeline.ImagegenPipelineError,
        match="raster must remain below",
    ):
        evidence.imagegen_font_pipeline.load_source_descriptor(descriptor)
    loaded = evidence.imagegen_font_pipeline.load_source_descriptor(
        descriptor,
        allowed_raster_root=raster_root,
    )
    assert loaded.raster_path == raster.resolve()
    assert evidence.imagegen_font_pipeline._font_family_and_ps(
        "han-0001",
        family_name_prefix="Mew Note TC",
        postscript_name_prefix="MewNoteTC",
    ) == (
        "Mew Note TC Han 0001 Unreviewed",
        "MewNoteTC-Han0001-Unreviewed",
    )


@pytest.mark.parametrize(
    ("batch_id", "expected_steps"),
    [
        ("han-0001", 1),
        ("han-0002", 2),
        ("han-0003", 1),
        ("han-0004", 2),
        ("han-0005", 1),
    ],
)
def test_first_five_sources_have_complete_history_and_vector_gates(
    batch_id: str,
    expected_steps: int,
) -> None:
    context = _context()
    source = evidence.validate_source(context, "han-6060", batch_id)
    history = evidence.validate_history(context, "han-6060", batch_id)
    assert len(history["steps"]) == expected_steps
    assert history["steps"][-1]["disposition"] == "accepted"
    assert history["steps"][-1]["output"]["retention"] == "retained-final"
    for step in history["steps"][:-1]:
        assert step["disposition"] == "rejected"
        assert step["output"]["retention"] == "hash-only-rejected"
        assert step["output"]["path"] is None
    assert source["family_id"] == "mew-note-tc"
    assert "families/mew-note-tc/" in source["generation_history"]["path"]

    report_path = (
        context.batch_paths("han-6060", batch_id).build / "report.json"
    )
    report = _object(report_path)
    assert report["approval_state"] == "unreviewed"
    assert report["font"]["cmap_count"] == 16
    assert all(
        glyph["micro_edge_count"] == 0 for glyph in report["glyphs"]
    )
    assert all(
        glyph["acute_micro_turn_count"] == 0 for glyph in report["glyphs"]
    )
    assert all(
        value > 0
        for sizes in report["small_size_coverage_pixels"].values()
        for value in sizes.values()
    )
    assert "MewNoteTC-" in Path(report["font"]["ttf"]).name
