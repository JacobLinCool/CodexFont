from __future__ import annotations

from pathlib import Path

from scripts import materialize_han_delta_batches as materializer
from scripts import register_han_delta_sheet as register


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = (
    ROOT
    / "sources/imagegen/collections/"
    "clear-hand-tc-dictionary-salience-1216.json"
)


def test_clear_hand_han_delta_materialization_is_complete() -> None:
    collection = register.load_collection(
        COLLECTION,
        project_root=ROOT,
    )
    result = materializer.validate_collection_artifacts(
        COLLECTION,
        project_root=ROOT,
    )

    assert result == {
        "collection_id": (
            "clear-hand-tc-dictionary-salience-extension-1216-v1"
        ),
        "glyph_count": 1216,
        "batch_count": 76,
        "copybook_count": 76,
        "prompt_count": 76,
        "draft_count": 76,
    }
    assert all(
        (
            collection.copybook_directory / f"{batch.batch_id}.png"
        ).is_file()
        and (
            collection.prompt_path.parent / f"{batch.batch_id}.md"
        ).is_file()
        and (
            collection.descriptor_directory
            / f"{batch.batch_id}.draft.json"
        ).is_file()
        for batch in collection.repertoire.batches
    )


def test_u25cd1_uses_the_authorized_bamboo_gate_composition() -> None:
    draft = materializer.validate_draft(
        ROOT
        / "sources/imagegen/batches/dict-han-0001.draft.json",
        project_root=ROOT,
    )
    references = draft["identity_copybook"]["provenance"][
        "references"
    ]
    reference = next(
        item
        for item in references
        if item["codepoint"] == "U+25CD1"
    )

    assert reference["character"] == "𥳑"
    assert reference["method"] == "vertical-ideographic-composition"
    assert reference["display"] == "竹＋閒"
    assert reference["authorization"] == (
        "project-owner-approved identity-copybook exception"
    )
    assert [
        (
            component["character"],
            component["codepoint"],
            component["placement"],
        )
        for component in reference["components"]
    ] == [
        ("竹", "U+7AF9", "upper"),
        ("閒", "U+9592", "lower"),
    ]
    assert all(
        component["font"]["external_font_binary_committed"] is False
        for component in reference["components"]
    )


def test_every_exact_cell_pins_noncommitted_font_provenance() -> None:
    draft = materializer.validate_draft(
        ROOT
        / "sources/imagegen/batches/dict-han-0076.draft.json",
        project_root=ROOT,
    )
    references = draft["identity_copybook"]["provenance"][
        "references"
    ]

    assert len(references) == 16
    assert {record["method"] for record in references} == {
        "exact-cmap-glyph"
    }
    assert all(
        record["font"]["external_font_binary_committed"] is False
        and len(record["font"]["sha256"]) == 64
        and record["font"]["validation"]
        == list(materializer.REFERENCE_VALIDATION)
        for record in references
    )
