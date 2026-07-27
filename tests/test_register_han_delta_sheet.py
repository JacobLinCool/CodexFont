from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import unicodedata

from PIL import Image
from PIL import ImageDraw
import pytest

from scripts import han_delta_generation_history as history
from scripts import han_delta_repertoire as delta
from scripts import materialize_han_delta_batches as materializer
from scripts import register_han_delta_sheet as register


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = (
    ROOT
    / "sources/imagegen/collections/"
    "clear-hand-tc-dictionary-salience-1216.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _fixture_project(
    tmp_path: Path,
    *,
    create_history: bool = True,
) -> tuple[Path, Path]:
    project = tmp_path
    inventory = project / "inventories/han_characters.csv"
    inventory.parent.mkdir(parents=True)
    fieldnames = list(delta.INVENTORY_FIELDS)
    candidates = [chr(codepoint) for codepoint in range(0x4E00, 0x4E15)]
    with inventory.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for offset, character in enumerate(candidates):
            codepoint = ord(character)
            count = 100 - offset
            writer.writerow(
                {
                    "character": character,
                    "codepoint": f"U+{codepoint:04X}",
                    "codepoint_decimal": codepoint,
                    "unicode_name": unicodedata.name(character),
                    "unicode_block": "CJK Unified Ideographs",
                    "unicode_plane": 0,
                    "usage_class": "common_big5_level_1",
                    "occurrence_count": count,
                    "source_tables": "entries",
                    "source_fields": "entries.key",
                    "source_details": json.dumps(
                        {"entries.key": count},
                        separators=(",", ":"),
                    ),
                    "compatibility_mapping": "",
                    "glyph_designed": "False",
                    "quality_checked": "False",
                }
            )
    requirements = project / "inventories/font_requirements.json"
    _write_json(
        requirements,
        {
            "requirements": [
                {
                    "codepoint_decimal": ord(character),
                    "categories": ["dictionary_han"],
                }
                for character in candidates
                if character != candidates[4]
            ]
        },
    )
    excluded = (
        Path("sources/imagegen/repertoires/existing-a.json"),
    )
    _write_json(
        project / excluded[0],
        {
            "characters": [
                {
                    "character": character,
                    "codepoint": ord(character),
                }
                for character in candidates[:4]
            ]
        },
    )
    repertoire = (
        project
        / "sources/imagegen/repertoires/test-extension-16.json"
    )
    delta.write_repertoire(
        output=repertoire,
        project_root=project,
        family_id="test-family",
        repertoire_id="test-family-extension-16-v1",
        batch_prefix="test-han",
        total_count=16,
        inventory_relative=Path(
            "inventories/han_characters.csv"
        ),
        requirements_relative=Path(
            "inventories/font_requirements.json"
        ),
        excluded_repertoire_relatives=excluded,
        authority_source="Test dictionary",
        authority_jurisdiction="Test",
        authority_role="Test fixture",
    )

    prompt = project / "sources/imagegen/prompts/test.md"
    prompt.parent.mkdir(parents=True)
    shutil.copyfile(
        ROOT
        / "sources/imagegen/prompts/"
        "han-delta-grid-with-copybook-v1.md",
        prompt,
    )
    style = project / "sources/imagegen/raster/style.png"
    style.parent.mkdir(parents=True)
    shutil.copyfile(
        ROOT / "sources/imagegen/raster/common-0001.png",
        style,
    )
    for directory in (
        project / "sources/imagegen/batches",
        project / "sources/imagegen/copybooks",
        project / "build/imagegen",
    ):
        directory.mkdir(parents=True)
    collection = (
        project
        / "sources/imagegen/collections/test-extension-16.json"
    )
    _write_json(
        collection,
        {
            "schema_version": 1,
            "record_type": "imagegen-han-delta-collection",
            "collection_id": "test-family-extension-16-v1",
            "family_id": "test-family",
            "vector_pipeline": (
                "imagegen-raster-potrace-quadratic-v2"
            ),
            "repertoire": {
                "path": (
                    "sources/imagegen/repertoires/"
                    "test-extension-16.json"
                ),
                "sha256": _sha256(repertoire),
                "repertoire_id": "test-family-extension-16-v1",
            },
            "prompt": {
                "path": "sources/imagegen/prompts/test.md",
                "sha256": _sha256(prompt),
            },
            "style_reference": {
                "role": "style-only-no-outline-import",
                "path": "sources/imagegen/raster/style.png",
                "sha256": _sha256(style),
            },
            "identity_copybook_policy": {
                "required": True,
                "role": (
                    "identity-reference-only-no-outline-import"
                ),
                "directory": "sources/imagegen/copybooks",
                "external_font_binaries_committed": False,
                "materializer": (
                    "scripts/materialize_han_delta_batches.py"
                ),
                "reference_fonts": [
                    {
                        "path": "/external/test-reference.ttf",
                        "sha256": "0" * 64,
                        "source_name": "Test reference",
                        "source_url": None,
                        "license": "Test-only",
                    }
                ],
                "compositions": [],
            },
            "paths": {
                "raster_directory": "sources/imagegen/raster",
                "descriptor_directory": "sources/imagegen/batches",
                "build_directory": "build/imagegen",
            },
        },
    )
    loaded = register.load_collection(
        collection,
        project_root=project,
    )
    batch_id = "test-han-0001"
    characters = loaded.repertoire.batches[0].characters
    copybook = (
        project / f"sources/imagegen/copybooks/{batch_id}.png"
    )
    copybook_image = Image.new(
        "L",
        (
            materializer.COPYBOOK_SIDE,
            materializer.COPYBOOK_SIDE,
        ),
        255,
    )
    draw = ImageDraw.Draw(copybook_image)
    for index in range(16):
        row, column = divmod(index, 4)
        left = column * materializer.CELL_SIZE + 120
        top = row * materializer.CELL_SIZE + 120
        draw.rectangle(
            (left, top, left + 160, top + 160),
            fill=0,
        )
    copybook_image.save(copybook)
    font_provenance = {
        "path": "/external/test-reference.ttf",
        "sha256": "0" * 64,
        "face_index": 0,
        "postscript_name": "TestReference-Regular",
        "glyph_name": "test-glyph",
        "source_name": "Test reference",
        "source_url": None,
        "license": "Test-only",
        "external_font_binary_committed": False,
        "validation": list(materializer.REFERENCE_VALIDATION),
    }
    references = [
        {
            "character": character,
            "codepoint": f"U+{ord(character):04X}",
            "role": register.IDENTITY_COPYBOOK_ROLE,
            "method": "exact-cmap-glyph",
            "font": {
                **font_provenance,
                "glyph_name": f"uni{ord(character):04X}",
            },
        }
        for character in characters
    ]
    exact_prompt = (
        project / f"sources/imagegen/prompts/{batch_id}.md"
    )
    exact_prompt.write_text(
        materializer.prompt_for(
            loaded,
            batch_id=batch_id,
            characters=characters,
            copybook_path=copybook,
            copybook_sha256=_sha256(copybook),
        ),
        encoding="utf-8",
    )
    draft = materializer.draft_payload(
        loaded,
        batch_id=batch_id,
        prompt_path=exact_prompt,
        prompt_sha256=_sha256(exact_prompt),
        copybook_path=copybook,
        copybook_sha256=_sha256(copybook),
        identity_references=references,
    )
    draft_path = (
        project / f"sources/imagegen/batches/{batch_id}.draft.json"
    )
    _write_json(draft_path, draft)
    materializer.validate_draft(
        draft_path,
        project_root=project,
    )
    raster = project / f"sources/imagegen/raster/{batch_id}.png"
    shutil.copyfile(
        ROOT / "sources/imagegen/raster/common-0001.png",
        raster,
    )
    actual_prompt = (
        project
        / f"sources/imagegen/batches/{batch_id}.tool-step-0001.txt"
    )
    rows = [
        "".join(characters[index : index + 4])
        for index in range(0, len(characters), 4)
    ]
    actual_prompt.write_text(
        "Actual image-generation prompt.\n"
        "Use the supplied style reference and identity copybook.\n"
        + "\n".join(rows)
        + "\n"
        + "\n".join(
            f"- Cell {index:02d}: U+{ord(character):04X} "
            f"{character}"
            for index, character in enumerate(characters, start=1)
        )
        + "\n",
        encoding="utf-8",
    )
    if create_history:
        payload = history.single_step_history(
            loaded,
            batch_id=batch_id,
            call_id=(
                "exec-00000000-0000-4000-8000-000000000001"
            ),
            actual_prompt_path=actual_prompt,
        )
        history.write_history(
            project
            / f"sources/imagegen/batches/{batch_id}.history.json",
            payload,
            project_root=project,
        )
    return project, collection


def _multi_step_history(
    project: Path,
    collection_path: Path,
) -> tuple[Path, dict[str, object]]:
    loaded = register.load_collection(
        collection_path,
        project_root=project,
    )
    batch_id = "test-han-0001"
    batch_directory = project / "sources/imagegen/batches"
    draft = materializer.validate_draft(
        batch_directory / f"{batch_id}.draft.json",
        project_root=project,
    )
    style = (
        batch_directory / draft["style_reference"]["raster"]
    ).resolve()
    copybook = (
        batch_directory / draft["identity_copybook"]["raster"]
    ).resolve()
    first_prompt = (
        batch_directory / f"{batch_id}.tool-step-0001.txt"
    )
    correction_one = (
        batch_directory / f"{batch_id}.tool-step-0002.txt"
    )
    correction_two = (
        batch_directory / f"{batch_id}.tool-step-0003.txt"
    )
    correction_one.write_text(
        "Correct the first output using the attached parent, "
        "copybook, and style reference.\n",
        encoding="utf-8",
    )
    correction_two.write_text(
        "Correct the second output using the attached parent "
        "and copybook.\n",
        encoding="utf-8",
    )
    first_output = "1" * 64
    second_output = "2" * 64
    raster = project / f"sources/imagegen/raster/{batch_id}.png"
    payload = history.history_payload(
        loaded,
        batch_id=batch_id,
        steps=(
            history.GenerationStepSpec(
                operation="generate",
                disposition="rejected",
                call_id=(
                    "exec-00000000-0000-4000-8000-000000000001"
                ),
                prompt_path=first_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=first_output,
            ),
            history.GenerationStepSpec(
                operation="correction",
                disposition="rejected",
                call_id=(
                    "exec-00000000-0000-4000-8000-000000000002"
                ),
                prompt_path=correction_one,
                input_images=(
                    history.InputImageSpec(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=first_output,
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                ),
                parent_output_sha256=first_output,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=second_output,
            ),
            history.GenerationStepSpec(
                operation="correction",
                disposition="accepted",
                call_id=(
                    "exec-00000000-0000-4000-8000-000000000003"
                ),
                prompt_path=correction_two,
                input_images=(
                    history.InputImageSpec(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=second_output,
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=second_output,
                output_retention="retained-final",
                output_path=raster,
                output_sha256=_sha256(raster),
            ),
        ),
    )
    path = batch_directory / f"{batch_id}.history.json"
    history.write_history(
        path,
        payload,
        project_root=project,
    )
    return path, payload


def test_clear_hand_collection_pins_the_frozen_delta() -> None:
    collection = register.load_collection(
        COLLECTION,
        project_root=ROOT,
    )
    assert collection.family_id == "clear-hand-tc"
    assert len(collection.repertoire.characters) == 1216
    assert len(collection.repertoire.batches) == 76
    assert collection.repertoire.batch_prefix == "dict-han"
    assert collection.identity_copybook_required is True
    assert len(collection.identity_reference_fonts) == 2
    assert [item["codepoint"] for item in collection.identity_compositions] == [
        "U+25CD1"
    ]


def test_single_step_history_pins_actual_and_intended_prompts(
    tmp_path: Path,
) -> None:
    project, _ = _fixture_project(tmp_path)
    loaded = history.load_history(
        project
        / "sources/imagegen/batches/test-han-0001.history.json",
        project_root=project,
    )

    assert loaded.step_count == 1
    assert loaded.accepted_call_id.endswith("000000000001")
    assert loaded.exact_prompt_path.name == (
        "test-han-0001.tool-step-0001.txt"
    )
    assert loaded.exact_prompt_path.parent == (
        project / "sources/imagegen/batches"
    )
    assert loaded.payload["intended_materialization"]["prompt"][
        "path"
    ].endswith("test-han-0001.md")
    step = loaded.payload["steps"][0]
    assert [item["role"] for item in step["input_images"]] == [
        "style-reference",
        "identity-copybook",
    ]
    assert step["output"]["retention"] == "retained-final"
    assert loaded.accepted_raster_sha256 == _sha256(
        loaded.accepted_raster_path
    )


def test_single_step_history_accepts_observed_direct_call_id(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    payload = history.single_step_history(
        collection,
        batch_id="test-han-0001",
        call_id="call_qC31KUUqn1pcW4w2U743m0kd",
        actual_prompt_path=(
            project
            / "sources/imagegen/batches/"
            "test-han-0001.tool-step-0001.txt"
        ),
    )

    assert payload["steps"][0]["call_id"] == (
        "call_qC31KUUqn1pcW4w2U743m0kd"
    )


def test_generation_history_rejects_malformed_call_ids(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    actual_prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    malformed = (
        "call_" + "a" * 23,
        "call_" + "a" * 25,
        "call_qC31KUUqn1pcW4w2U743m0k-",
        "exec-00000000-0000-4000-8000-00000000000G",
        "unscoped-generator-call",
    )

    for call_id in malformed:
        with pytest.raises(
            history.HanDeltaHistoryError,
            match="call id is invalid",
        ):
            history.single_step_history(
                collection,
                batch_id="test-han-0001",
                call_id=call_id,
                actual_prompt_path=actual_prompt,
            )


def test_multi_step_history_retains_only_the_accepted_raster(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    path, _ = _multi_step_history(project, collection_path)
    loaded = history.load_history(path, project_root=project)

    assert loaded.step_count == 3
    assert loaded.accepted_call_id.endswith("000000000003")
    assert [
        step["output"]["retention"]
        for step in loaded.payload["steps"]
    ] == [
        "hash-only-rejected",
        "hash-only-rejected",
        "retained-final",
    ]
    assert [
        step["output"]["path"]
        for step in loaded.payload["steps"]
    ] == [
        None,
        None,
        "../raster/test-han-0001.png",
    ]
    assert loaded.payload["steps"][1]["input_images"][0] == {
        "role": "parent-output",
        "retention": "hash-only-rejected",
        "path": None,
        "sha256": "1" * 64,
    }


def test_generation_history_preserves_independent_generate_retries(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    batch_id = "test-han-0001"
    batch_directory = project / "sources/imagegen/batches"
    first_prompt = (
        batch_directory / f"{batch_id}.tool-step-0001.txt"
    )
    retry_prompt = (
        batch_directory / f"{batch_id}.tool-step-0002.txt"
    )
    retry_prompt.write_bytes(first_prompt.read_bytes())
    correction_prompt = (
        batch_directory / f"{batch_id}.tool-step-0003.txt"
    )
    correction_prompt.write_text(
        "Correct the attached parent output against the copybook.\n",
        encoding="utf-8",
    )
    draft = materializer.validate_draft(
        batch_directory / f"{batch_id}.draft.json",
        project_root=project,
    )
    style = (
        batch_directory / draft["style_reference"]["raster"]
    ).resolve()
    copybook = (
        batch_directory / draft["identity_copybook"]["raster"]
    ).resolve()
    raster = project / f"sources/imagegen/raster/{batch_id}.png"
    first_output = "1" * 64
    retry_output = "2" * 64

    payload = history.history_payload(
        collection,
        batch_id=batch_id,
        steps=(
            history.GenerationStepSpec(
                operation="generate",
                disposition="rejected",
                call_id="call_111111111111111111111111",
                prompt_path=first_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=first_output,
            ),
            history.GenerationStepSpec(
                operation="generate",
                disposition="rejected",
                call_id="call_222222222222222222222222",
                prompt_path=retry_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=retry_output,
            ),
            history.GenerationStepSpec(
                operation="correction",
                disposition="accepted",
                call_id="call_333333333333333333333333",
                prompt_path=correction_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=retry_output,
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=retry_output,
                output_retention="retained-final",
                output_path=raster,
                output_sha256=_sha256(raster),
            ),
        ),
    )
    path = batch_directory / f"{batch_id}.history.json"
    history.write_history(path, payload, project_root=project)
    loaded = history.load_history(path, project_root=project)

    assert [
        step["operation"] for step in loaded.payload["steps"]
    ] == ["generate", "generate", "correction"]
    assert loaded.payload["steps"][1]["parent_output_sha256"] is None
    assert loaded.payload["steps"][2]["parent_output_sha256"] == (
        retry_output
    )


def test_generation_history_preserves_branched_correction_parent(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    batch_id = "test-han-0001"
    batch_directory = project / "sources/imagegen/batches"
    first_prompt = (
        batch_directory / f"{batch_id}.tool-step-0001.txt"
    )
    correction_one = (
        batch_directory / f"{batch_id}.tool-step-0002.txt"
    )
    correction_two = (
        batch_directory / f"{batch_id}.tool-step-0003.txt"
    )
    correction_one.write_text(
        "Try one correction from the first parent.\n",
        encoding="utf-8",
    )
    correction_two.write_text(
        "Try a different correction from that same first parent.\n",
        encoding="utf-8",
    )
    draft = materializer.validate_draft(
        batch_directory / f"{batch_id}.draft.json",
        project_root=project,
    )
    style = (
        batch_directory / draft["style_reference"]["raster"]
    ).resolve()
    copybook = (
        batch_directory / draft["identity_copybook"]["raster"]
    ).resolve()
    raster = project / f"sources/imagegen/raster/{batch_id}.png"
    first_output = "1" * 64
    abandoned_branch = "2" * 64

    payload = history.history_payload(
        collection,
        batch_id=batch_id,
        steps=(
            history.GenerationStepSpec(
                operation="generate",
                disposition="rejected",
                call_id="call_111111111111111111111111",
                prompt_path=first_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=first_output,
            ),
            history.GenerationStepSpec(
                operation="correction",
                disposition="rejected",
                call_id="call_222222222222222222222222",
                prompt_path=correction_one,
                input_images=(
                    history.InputImageSpec(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=first_output,
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=first_output,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=abandoned_branch,
            ),
            history.GenerationStepSpec(
                operation="correction",
                disposition="accepted",
                call_id="call_333333333333333333333333",
                prompt_path=correction_two,
                input_images=(
                    history.InputImageSpec(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=first_output,
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=first_output,
                output_retention="retained-final",
                output_path=raster,
                output_sha256=_sha256(raster),
            ),
        ),
    )
    path = batch_directory / f"{batch_id}.history.json"
    history.write_history(path, payload, project_root=project)
    loaded = history.load_history(path, project_root=project)

    assert loaded.payload["steps"][1]["parent_output_sha256"] == first_output
    assert loaded.payload["steps"][2]["parent_output_sha256"] == first_output
    assert loaded.payload["steps"][1]["output"]["sha256"] == (
        abandoned_branch
    )


def test_generation_history_records_generated_component_assembly(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    batch_id = "test-han-0001"
    batch_directory = project / "sources/imagegen/batches"
    first_prompt = (
        batch_directory / f"{batch_id}.tool-step-0001.txt"
    )
    component_prompt = (
        batch_directory / f"{batch_id}.tool-step-0002.txt"
    )
    assembly_manifest = (
        batch_directory / f"{batch_id}.tool-step-0003.txt"
    )
    component_prompt.write_text(
        "Generate one isolated replacement glyph from the pinned "
        "style and identity copybook.\n",
        encoding="utf-8",
    )
    assembly_manifest.write_text(
        "Deterministically fit the generated component into one "
        "specified parent-sheet cell.\n",
        encoding="utf-8",
    )
    draft = materializer.validate_draft(
        batch_directory / f"{batch_id}.draft.json",
        project_root=project,
    )
    style = (
        batch_directory / draft["style_reference"]["raster"]
    ).resolve()
    copybook = (
        batch_directory / draft["identity_copybook"]["raster"]
    ).resolve()
    raster = project / f"sources/imagegen/raster/{batch_id}.png"
    parent_output = "1" * 64
    component_output = "2" * 64
    assembly_id = f"assembly-{_sha256(assembly_manifest)}"

    payload = history.history_payload(
        collection,
        batch_id=batch_id,
        steps=(
            history.GenerationStepSpec(
                operation="generate",
                disposition="rejected",
                call_id="call_111111111111111111111111",
                prompt_path=first_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="hash-only-rejected",
                output_path=None,
                output_sha256=parent_output,
            ),
            history.GenerationStepSpec(
                operation="component-generate",
                disposition="intermediate",
                call_id="call_222222222222222222222222",
                prompt_path=component_prompt,
                input_images=(
                    history.InputImageSpec(
                        role="style-reference",
                        retention="retained-reference",
                        path=style,
                        sha256=_sha256(style),
                    ),
                    history.InputImageSpec(
                        role="identity-copybook",
                        retention="retained-reference",
                        path=copybook,
                        sha256=_sha256(copybook),
                    ),
                ),
                parent_output_sha256=None,
                output_retention="hash-only-intermediate",
                output_path=None,
                output_sha256=component_output,
            ),
            history.GenerationStepSpec(
                operation="assembly",
                disposition="accepted",
                call_id=assembly_id,
                prompt_path=assembly_manifest,
                input_images=(
                    history.InputImageSpec(
                        role="parent-output",
                        retention="hash-only-rejected",
                        path=None,
                        sha256=parent_output,
                    ),
                    history.InputImageSpec(
                        role="component-output",
                        retention="hash-only-intermediate",
                        path=None,
                        sha256=component_output,
                    ),
                ),
                parent_output_sha256=parent_output,
                output_retention="retained-final",
                output_path=raster,
                output_sha256=_sha256(raster),
            ),
        ),
    )
    path = batch_directory / f"{batch_id}.history.json"
    history.write_history(path, payload, project_root=project)
    loaded = history.load_history(path, project_root=project)

    assert [step["operation"] for step in loaded.payload["steps"]] == [
        "generate",
        "component-generate",
        "assembly",
    ]
    assert loaded.payload["steps"][1]["disposition"] == "intermediate"
    assert loaded.payload["steps"][1]["output"]["retention"] == (
        "hash-only-intermediate"
    )
    assert loaded.accepted_call_id == assembly_id


def test_generate_retry_rejects_a_parent_output(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    batch_id = "test-han-0001"
    batch_directory = project / "sources/imagegen/batches"
    first_prompt = (
        batch_directory / f"{batch_id}.tool-step-0001.txt"
    )
    retry_prompt = (
        batch_directory / f"{batch_id}.tool-step-0002.txt"
    )
    retry_prompt.write_bytes(first_prompt.read_bytes())
    draft = materializer.validate_draft(
        batch_directory / f"{batch_id}.draft.json",
        project_root=project,
    )
    style = (
        batch_directory / draft["style_reference"]["raster"]
    ).resolve()
    copybook = (
        batch_directory / draft["identity_copybook"]["raster"]
    ).resolve()
    raster = project / f"sources/imagegen/raster/{batch_id}.png"
    first_output = "1" * 64

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="generate must use style and copybook only",
    ):
        history.history_payload(
            collection,
            batch_id=batch_id,
            steps=(
                history.GenerationStepSpec(
                    operation="generate",
                    disposition="rejected",
                    call_id="call_111111111111111111111111",
                    prompt_path=first_prompt,
                    input_images=(
                        history.InputImageSpec(
                            role="style-reference",
                            retention="retained-reference",
                            path=style,
                            sha256=_sha256(style),
                        ),
                        history.InputImageSpec(
                            role="identity-copybook",
                            retention="retained-reference",
                            path=copybook,
                            sha256=_sha256(copybook),
                        ),
                    ),
                    parent_output_sha256=None,
                    output_retention="hash-only-rejected",
                    output_path=None,
                    output_sha256=first_output,
                ),
                history.GenerationStepSpec(
                    operation="generate",
                    disposition="accepted",
                    call_id="call_222222222222222222222222",
                    prompt_path=retry_prompt,
                    input_images=(
                        history.InputImageSpec(
                            role="parent-output",
                            retention="hash-only-rejected",
                            path=None,
                            sha256=first_output,
                        ),
                        history.InputImageSpec(
                            role="identity-copybook",
                            retention="retained-reference",
                            path=copybook,
                            sha256=_sha256(copybook),
                        ),
                    ),
                    parent_output_sha256=first_output,
                    output_retention="retained-final",
                    output_path=raster,
                    output_sha256=_sha256(raster),
                ),
            ),
        )


def test_generate_retry_rejects_an_incomplete_identity_manifest(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    batch_id = "test-han-0001"
    batch_directory = project / "sources/imagegen/batches"
    first_prompt = (
        batch_directory / f"{batch_id}.tool-step-0001.txt"
    )
    retry_prompt = (
        batch_directory / f"{batch_id}.tool-step-0002.txt"
    )
    retry_prompt.write_text(
        "Retry the same generated sheet.\n",
        encoding="utf-8",
    )
    draft = materializer.validate_draft(
        batch_directory / f"{batch_id}.draft.json",
        project_root=project,
    )
    style = (
        batch_directory / draft["style_reference"]["raster"]
    ).resolve()
    copybook = (
        batch_directory / draft["identity_copybook"]["raster"]
    ).resolve()
    raster = project / f"sources/imagegen/raster/{batch_id}.png"

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="generation prompt omits ordered row",
    ):
        history.history_payload(
            collection,
            batch_id=batch_id,
            steps=(
                history.GenerationStepSpec(
                    operation="generate",
                    disposition="rejected",
                    call_id="call_111111111111111111111111",
                    prompt_path=first_prompt,
                    input_images=(
                        history.InputImageSpec(
                            role="style-reference",
                            retention="retained-reference",
                            path=style,
                            sha256=_sha256(style),
                        ),
                        history.InputImageSpec(
                            role="identity-copybook",
                            retention="retained-reference",
                            path=copybook,
                            sha256=_sha256(copybook),
                        ),
                    ),
                    parent_output_sha256=None,
                    output_retention="hash-only-rejected",
                    output_path=None,
                    output_sha256="1" * 64,
                ),
                history.GenerationStepSpec(
                    operation="generate",
                    disposition="accepted",
                    call_id="call_222222222222222222222222",
                    prompt_path=retry_prompt,
                    input_images=(
                        history.InputImageSpec(
                            role="style-reference",
                            retention="retained-reference",
                            path=style,
                            sha256=_sha256(style),
                        ),
                        history.InputImageSpec(
                            role="identity-copybook",
                            retention="retained-reference",
                            path=copybook,
                            sha256=_sha256(copybook),
                        ),
                    ),
                    parent_output_sha256=None,
                    output_retention="retained-final",
                    output_path=raster,
                    output_sha256=_sha256(raster),
                ),
            ),
        )


def test_generation_prompt_accepts_quoted_identities_without_colons(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    characters = collection.repertoire.batches[0].characters
    text = prompt.read_text(encoding="utf-8")
    for index, character in enumerate(characters, start=1):
        text = text.replace(
            f"U+{ord(character):04X} {character}",
            f"U+{ord(character):04X} `{character}`",
        )
        text = text.replace(f"Cell {index:02d}:", f"Cell {index:02d}")
    prompt.write_text(text, encoding="utf-8")

    payload = history.single_step_history(
        collection,
        batch_id="test-han-0001",
        call_id="call_qC31KUUqn1pcW4w2U743m0kd",
        actual_prompt_path=prompt,
    )

    assert payload["steps"][0]["prompt"]["sha256"] == _sha256(
        prompt
    )


def test_generation_prompt_accepts_exact_bare_cell_labels(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    text = prompt.read_text(encoding="utf-8")
    for index in range(1, 17):
        text = text.replace(f"Cell {index:02d}:", f"{index:02d}")
    prompt.write_text(text, encoding="utf-8")

    payload = history.single_step_history(
        collection,
        batch_id="test-han-0001",
        call_id="call_cQF7FU0CCM2Go3cz5ktkc9GM",
        actual_prompt_path=prompt,
    )

    assert payload["steps"][0]["prompt"]["sha256"] == _sha256(
        prompt
    )


def test_generation_prompt_rejects_bare_cell_labels_with_colons(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    text = prompt.read_text(encoding="utf-8")
    for index in range(1, 17):
        text = text.replace(f"Cell {index:02d}:", f"{index:02d}:")
    prompt.write_text(text, encoding="utf-8")

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="generation prompt omits ordered",
    ):
        history.single_step_history(
            collection,
            batch_id="test-han-0001",
            call_id="call_HrR8EdBJLBiqMw4gpmeLBMO0",
            actual_prompt_path=prompt,
        )


def test_generation_prompt_rejects_prefixed_bare_cell_labels(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    collection = register.load_collection(
        collection_path,
        project_root=project,
    )
    prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    text = prompt.read_text(encoding="utf-8")
    for index in range(1, 17):
        text = text.replace(f"Cell {index:02d}:", f"x{index:02d}")
    prompt.write_text(text, encoding="utf-8")

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="generation prompt omits ordered",
    ):
        history.single_step_history(
            collection,
            batch_id="test-han-0001",
            call_id="call_R71BhVHHAHmBZwCHBoNrRlLJ",
            actual_prompt_path=prompt,
        )


def test_multi_step_history_rejects_parent_output_drift(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )
    path, payload = _multi_step_history(project, collection_path)
    steps = payload["steps"]
    steps[1]["parent_output_sha256"] = "3" * 64
    steps[1]["input_images"][0]["sha256"] = "3" * 64
    _write_json(path, payload)

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="parent hash chain is broken",
    ):
        history.load_history(path, project_root=project)


def test_generation_history_rejects_actual_prompt_drift(
    tmp_path: Path,
) -> None:
    project, _ = _fixture_project(tmp_path)
    history_path = (
        project
        / "sources/imagegen/batches/test-han-0001.history.json"
    )
    actual_prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    actual_prompt.write_text(
        actual_prompt.read_text(encoding="utf-8")
        + "Unrecorded change.\n",
        encoding="utf-8",
    )

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="prompt hash mismatch",
    ):
        history.load_history(history_path, project_root=project)


def test_generation_history_rejects_symlinked_prompt(
    tmp_path: Path,
) -> None:
    project, _ = _fixture_project(tmp_path)
    history_path = (
        project
        / "sources/imagegen/batches/test-han-0001.history.json"
    )
    actual_prompt = (
        project
        / "sources/imagegen/batches/"
        "test-han-0001.tool-step-0001.txt"
    )
    target = actual_prompt.with_name("retained-prompt-target.txt")
    actual_prompt.rename(target)
    actual_prompt.symlink_to(target.name)

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="must not traverse a symlink",
    ):
        history.load_history(history_path, project_root=project)


def test_generation_history_rejects_relative_path_escape(
    tmp_path: Path,
) -> None:
    project, _ = _fixture_project(tmp_path)
    history_path = (
        project
        / "sources/imagegen/batches/test-han-0001.history.json"
    )
    payload = json.loads(history_path.read_text(encoding="utf-8"))
    payload["collection"]["path"] = (
        "../../../../outside-project.json"
    )
    _write_json(history_path, payload)

    with pytest.raises(
        history.HanDeltaHistoryError,
        match="escapes the project root",
    ):
        history.load_history(history_path, project_root=project)


def test_registration_refuses_missing_generation_history(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(
        tmp_path,
        create_history=False,
    )

    with pytest.raises(
        register.HanDeltaRegistrationError,
        match="generation history",
    ):
        register.register(
            collection_path=collection_path,
            batch_id="test-han-0001",
            project_root=project,
        )


def test_registers_pending_descriptor_with_canonical_history(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(tmp_path)
    output = register.register(
        collection_path=collection_path,
        batch_id="test-han-0001",
        project_root=project,
    )
    payload = register.validate_descriptor(
        output,
        project_root=project,
    )

    assert payload["state"] == "generated-unreviewed"
    assert payload["record_type"] == "imagegen-han-delta-source"
    assert payload["batch_id"] == "imagegen-test-han-0001"
    assert len(payload["grid"]["characters"]) == 16
    assert set(payload["review"].values()) == {"pending"}
    generation = payload["generation_history"]
    assert generation["step_count"] == 1
    assert generation["accepted_call_id"] == (
        "exec-00000000-0000-4000-8000-000000000001"
    )
    assert "generator_call" not in payload
    assert payload["prompt"]["path"].endswith(
        "test-han-0001.tool-step-0001.txt"
    )
    assert payload["intended_materialized_prompt"]["path"].endswith(
        "test-han-0001.md"
    )
    identity = payload["identity_copybook"]
    copybook = (
        project / "sources/imagegen/copybooks/test-han-0001.png"
    )
    assert identity["raster_sha256"] == _sha256(copybook)
    assert identity["provenance"]["materialization_draft"][
        "path"
    ].endswith("test-han-0001.draft.json")


def test_required_collection_infers_the_pinned_materialization_draft() -> None:
    collection = register.load_collection(
        COLLECTION,
        project_root=ROOT,
    )
    identity = register.identity_copybook_from_draft(
        collection,
        "dict-han-0001",
    )

    assert identity.path == (
        ROOT / "sources/imagegen/copybooks/dict-han-0001.png"
    )
    assert identity.materialization_draft == (
        ROOT
        / "sources/imagegen/batches/dict-han-0001.draft.json"
    )
    assert identity.source_name == (
        "neutral local-font Han identity copybook"
    )


def test_descriptor_validation_rejects_changed_copybook(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(tmp_path)
    copybook = (
        project / "sources/imagegen/copybooks/test-han-0001.png"
    )
    output = register.register(
        collection_path=collection_path,
        batch_id="test-han-0001",
        project_root=project,
    )
    Image.new("L", (1600, 1600), "white").save(copybook)
    with pytest.raises(
        register.HanDeltaRegistrationError,
        match="copybook hash mismatch",
    ):
        register.validate_descriptor(
            output,
            project_root=project,
        )


def test_registration_refuses_noncanonical_raster_path(
    tmp_path: Path,
) -> None:
    project, collection_path = _fixture_project(tmp_path)
    wrong = project / "wrong.png"
    shutil.copyfile(
        ROOT / "sources/imagegen/raster/common-0001.png",
        wrong,
    )
    with pytest.raises(
        register.HanDeltaRegistrationError,
        match="raster must be exactly",
    ):
        register.register(
            collection_path=collection_path,
            batch_id="test-han-0001",
            raster=wrong,
            project_root=project,
        )
