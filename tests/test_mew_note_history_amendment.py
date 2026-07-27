from __future__ import annotations

from pathlib import Path

import pytest

from scripts import mew_note_batch_evidence as evidence
from scripts import mew_note_history_amendment as amendment


ROOT = Path(__file__).resolve().parents[1]


def _inputs(
    context: evidence.FamilyContext,
    values: list[dict],
) -> tuple[evidence.GenerationInput, ...]:
    return tuple(
        evidence.GenerationInput(
            role=value["role"],
            retention=value["retention"],
            path=(
                context.project_root / value["path"]
                if value["path"] is not None
                else None
            ),
            sha256=value["sha256"],
        )
        for value in values
    )


def test_preserved_prefix_accepts_only_an_exact_hash_chained_correction() -> None:
    context = evidence.load_context(ROOT)
    collection_id = "han-6060"
    batch_id = "han-0001"
    root = context.batch_paths(collection_id, batch_id).source
    history = evidence.validate_history(context, collection_id, batch_id)
    previous = history["steps"][0]
    prior_step = evidence.GenerationStep(
        operation=previous["operation"],
        disposition="rejected",
        call_id=previous["call_id"],
        prompt_path=context.project_root
        / previous["actual_tool_prompt"]["path"],
        inputs=_inputs(context, previous["inputs"]),
        output_sha256=previous["output"]["sha256"],
        output_path=None,
        parent_output_sha256=previous["parent_output_sha256"],
    )
    correction = evidence.GenerationStep(
        operation="correction",
        disposition="accepted",
        call_id="exec-00000000-0000-0000-0000-000000000099",
        prompt_path=root / "tool-step-0002.txt",
        inputs=(
            evidence.GenerationInput(
                role="parent-output",
                retention="hash-only-rejected",
                path=None,
                sha256=previous["output"]["sha256"],
            ),
            *_inputs(context, previous["inputs"]),
        ),
        output_sha256="9" * 64,
        output_path=ROOT / "not-read-by-prefix-check.png",
        parent_output_sha256=previous["output"]["sha256"],
    )
    amendment._assert_preserved_prefix(
        context,
        root,
        history,
        (prior_step, correction),
    )

    changed = evidence.GenerationStep(
        **{
            **prior_step.__dict__,
            "call_id": "exec-00000000-0000-0000-0000-000000000098",
        }
    )
    with pytest.raises(
        amendment.MewNoteAmendmentError,
        match="changed or removed",
    ):
        amendment._assert_preserved_prefix(
            context,
            root,
            history,
            (changed, correction),
        )


def test_reviewed_generation_evidence_is_immutable() -> None:
    context = evidence.load_context(ROOT)
    with pytest.raises(
        amendment.MewNoteAmendmentError,
        match="reviewed generation evidence is immutable",
    ):
        amendment.amend_unreviewed_history(
            context,
            "han-6060",
            "han-0001",
            steps=(),
        )


def test_prior_unreviewed_vector_build_is_retained_by_hash() -> None:
    context = evidence.load_context(ROOT)
    paths = context.batch_paths("han-6060", "han-0001")
    value = amendment._prior_vector_build(
        paths,
        prior_source_sha256=evidence.sha256_path(
            paths.source / "source.json"
        ),
    )
    assert value is not None
    assert value["retention"] == "hash-only-derived-unreviewed"
    assert set(value["proof_sha256"]) == {
        "black_on_white",
        "white_on_black",
        "segmented_source",
    }
