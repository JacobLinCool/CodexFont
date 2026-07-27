from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import mew_note_batch_evidence as evidence
from scripts import (
    mew_note_post_review_vertical_handedness_correction as correction,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = Path(
    "/Users/jacoblincool/.codex/generated_images/"
    "019f627c-e7f7-7b73-a42b-922f2f520a2a/"
    "call_VAas4tDotji4RZSEEodJvbLm.png"
)
PREDECESSOR_RASTER = ROOT / (
    "families/mew-note-tc/sources/imagegen/pipelines/original-raster-v1/"
    "collections/vertical-93/batches/vertical-0002/"
    "vertical-orientation-raw-candidate.png"
)
EXPECTED_PREDECESSOR_APPROVAL_SHA256 = (
    "bbef5f1b5f5ab050e921afda6f826e49c25dc18aec38197e20492d9a5e579c18"
)
EXPECTED_REAPPROVAL_SHA256 = (
    "0120e415be663bcbdcd15d87e2001a07971492021a57ffde30f487b6a1ab44c5"
)
PROMPT = (
    "Edit this exact 4×4 white glyph contact sheet, preserving the canvas, "
    "grid, line weight, margins, anti-aliasing, and every glyph except cell "
    "6 (counting left-to-right, top-to-bottom). This is original font-source "
    "artwork. Cell 6 is U+300D RIGHT CORNER BRACKET in its Unicode vertical "
    "form, corresponding to U+FE42. The current cell is mirrored incorrectly. "
    "Redraw it as an unmistakable bottom-left corner shaped like └: the SHORT "
    "VERTICAL ARM MUST BE ON THE LEFT, rising upward, and the LONG BOTTOM "
    "HORIZONTAL ARM MUST EXTEND TO THE RIGHT. The horizontal arm should be "
    "about 1.8 times the height of the vertical arm. Keep a clean rounded "
    "monoline turn, no spike, centered in the cell and clear of grid lines. "
    "Do not change cell 8 or any other cell. Output only the edited full "
    "contact sheet on white.\n"
)


def _context() -> evidence.FamilyContext:
    return evidence.load_context(ROOT)


def test_correction_contract_is_distinct_and_single_cell() -> None:
    implementation = (ROOT / correction.IMPLEMENTATION_PATH).read_text(
        encoding="utf-8"
    )

    assert correction.RECORD_NAME == (
        "post-review-vertical-handedness-correction.json"
    )
    assert correction.REASON == "release-vertical-handedness-rejected"
    assert correction.APPROVAL_FIELD == (
        "post_review_vertical_handedness_correction"
    )
    assert correction.COLLECTION_ID == "vertical-93"
    assert correction.BATCH_ID == "vertical-0002"
    assert correction.TARGET["cell"] == 6
    assert correction.TARGET["codepoint"] == "U+300D"
    assert correction.TARGET["vertical_presentation_codepoint"] == "U+FE42"
    assert correction.TARGET["expected_corner"] == "└"
    assert correction.PRESERVED_CELL_8["cell"] == 8
    assert correction.PRESERVED_CELL_8["codepoint"] == "U+300F"
    assert "release-metric-envelope-rejected" not in implementation


def test_exact_imagegen_candidate_and_prompt_are_frozen() -> None:
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == (
        correction.EXPECTED_CANDIDATE_SHA256
    )
    assert hashlib.sha256(PROMPT.encode("utf-8")).hexdigest() == (
        correction.EXPECTED_PROMPT_SHA256
    )
    assert correction.EXPECTED_CALL_ID == (
        "call_VAas4tDotji4RZSEEodJvbLm"
    )


def test_binary_gate_rejects_mirror_and_accepts_bottom_left_corner() -> None:
    rejected = correction._binary_handedness(
        correction._load_rgb_png(
            PREDECESSOR_RASTER, label="test predecessor"
        ),
        expect_accepted=False,
    )
    accepted = correction._binary_handedness(
        correction._load_rgb_png(CANDIDATE, label="test candidate"),
        expect_accepted=True,
    )

    assert rejected["decision"] == "REJECT"
    assert rejected["endpoint_occupancy_pixels"]["upper_left"] < (
        correction.MINIMUM_UPPER_LEFT_INK_PIXELS
    )
    assert rejected["endpoint_occupancy_pixels"]["upper_right"] > (
        correction.MAXIMUM_UPPER_RIGHT_INK_PIXELS
    )
    assert accepted["decision"] == "ACCEPT"
    assert all(accepted["gates"].values())
    assert accepted["connected_component_count"] == 1
    assert (
        accepted["left_vertical_span_ratio"]
        >= correction.MINIMUM_LEFT_VERTICAL_SPAN_RATIO
    )
    assert (
        accepted["right_vertical_span_ratio"]
        <= correction.MAXIMUM_RIGHT_VERTICAL_SPAN_RATIO
    )
    assert (
        accepted["bottom_horizontal_span_ratio"]
        >= correction.MINIMUM_BOTTOM_HORIZONTAL_SPAN_RATIO
    )


def test_composite_replaces_only_cell_six(tmp_path: Path) -> None:
    original_path = PREDECESSOR_RASTER
    output = tmp_path / "composite.png"
    record = correction._compose(original_path, CANDIDATE, output)
    original = correction._load_rgb_png(
        original_path, label="test predecessor"
    )
    candidate = correction._load_rgb_png(
        CANDIDATE, label="test candidate"
    )
    installed = correction._load_rgb_png(
        output, label="test composite"
    )

    assert record["region"]["cell"] == 6
    assert record["preserved_cell_8"]["cell"] == 8
    assert correction._region_sha256(
        installed, correction.TARGET["replacement_box"]
    ) == correction._region_sha256(
        candidate, correction.TARGET["replacement_box"]
    )
    assert correction._region_sha256(
        installed,
        correction.PRESERVED_CELL_8["replacement_box"],
    ) == correction._region_sha256(
        original,
        correction.PRESERVED_CELL_8["replacement_box"],
    )
    assert correction._framed_pixel_sha256(
        installed,
        regions=(correction.TARGET["replacement_box"],),
        include_regions=False,
    ) == correction._framed_pixel_sha256(
        original,
        regions=(correction.TARGET["replacement_box"],),
        include_regions=False,
    )


def test_recorded_preflight_preserves_all_fifteen_non_target_vectors() -> None:
    context = _context()
    record = correction.validate_correction(
        context,
        require_new_review=False,
        require_reapproval=False,
    )
    result = record["correction_generation"]["candidate_preflight"]
    unchanged = result["unchanged_non_target_glyphs"]

    assert len(unchanged) == 15
    assert sum(
        item["codepoint"]
        == correction.PRESERVED_CELL_8["codepoint"]
        for item in unchanged
    ) == 1
    assert result["handedness_diagnostics"]["decision"] == "ACCEPT"
    assert result["micro_edge_count"] == 0
    assert result["acute_micro_turn_count"] == 0


def test_predecessor_approval_is_snapshotted_byte_identically() -> None:
    context = _context()
    record = correction.validate_correction(
        context,
        require_new_review=False,
        require_reapproval=False,
    )
    prior = record["prior_evidence"]
    approval = prior["release_approval"]
    snapshot = (
        context.project_root
        / approval["immutable_snapshot"]["path"]
    )
    canonical = (
        context.project_root
        / approval["canonical_overwrite_target"]["path"]
    )
    snapshot_sha256 = evidence.sha256_path(snapshot)
    canonical_sha256 = evidence.sha256_path(canonical)
    admitted_predecessor = correction._object(
        snapshot,
        label="admitted predecessor approval snapshot",
    )
    matching = [
        item
        for item in admitted_predecessor["reviewed_batches"]
        if item["collection_id"] == correction.COLLECTION_ID
        and item["batch_id"] == correction.BATCH_ID
    ]
    orientation_pin = {
        key: value
        for key, value in prior[
            "vertical_orientation_correction"
        ].items()
        if key != "retention"
    }

    assert record["rejected_handedness"]["decision"] == "REJECT"
    assert snapshot_sha256 == EXPECTED_PREDECESSOR_APPROVAL_SHA256
    assert snapshot_sha256 == approval["immutable_snapshot"]["sha256"]
    assert snapshot_sha256 == (
        approval["canonical_overwrite_target"]["sha256"]
    )
    assert snapshot.name == (
        f"{EXPECTED_PREDECESSOR_APPROVAL_SHA256}.approval.json"
    )
    assert canonical_sha256 == EXPECTED_REAPPROVAL_SHA256
    assert canonical_sha256 != snapshot_sha256
    assert canonical.read_bytes() != snapshot.read_bytes()
    assert approval["immutable_snapshot"]["retention"] == (
        "immutable-release-approval-snapshot"
    )
    assert admitted_predecessor["decision"] == "APPROVED"
    assert len(matching) == 1
    assert matching[0]["review"]["sha256"] == prior["review"]["sha256"]
    assert matching[0][
        "post_review_vertical_orientation_correction"
    ] == orientation_pin


def test_duplicate_json_keys_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"state":"old","state":"new"}\n', encoding="utf-8")

    with pytest.raises(
        correction.MewNoteVerticalHandednessCorrectionError,
        match="duplicate JSON object key",
    ):
        correction._object(path, label="test duplicate")


def test_exclusive_lock_rejects_concurrent_writer(tmp_path: Path) -> None:
    target = tmp_path / "record.json"

    with correction._exclusive_lock(target):
        with pytest.raises(
            correction.MewNoteVerticalHandednessCorrectionError,
            match="correction lock already exists",
        ):
            with correction._exclusive_lock(target):
                pass

    assert not target.with_name(f".{target.name}.lock").exists()


def test_exclusive_lock_stays_fail_closed_after_exception(
    tmp_path: Path,
) -> None:
    target = tmp_path / "record.json"
    lock = target.with_name(f".{target.name}.lock")

    with pytest.raises(RuntimeError, match="uncertain install"):
        with correction._exclusive_lock(target):
            raise RuntimeError("uncertain install")

    assert lock.is_file()
    lock.unlink()


def test_current_record_pins_snapshot_and_replacement_review() -> None:
    context = _context()
    record = correction.validate_correction(
        context,
        require_new_review=True,
        require_reapproval=False,
    )
    paths = context.batch_paths(
        correction.COLLECTION_ID,
        correction.BATCH_ID,
    )

    assert record["reason"] == correction.REASON
    assert record["candidate_generation"]["call_id"] == (
        correction.EXPECTED_CALL_ID
    )
    assert record["candidate_generation"]["raw_candidate"]["sha256"] == (
        correction.EXPECTED_CANDIDATE_SHA256
    )
    assert record["rejected_handedness"]["decision"] == "REJECT"
    assert record["correction_generation"][
        "handedness_diagnostics"
    ]["decision"] == "ACCEPT"
    assert len(
        record["correction_generation"][
            "unchanged_non_target_glyphs"
        ]
    ) == 15
    assert record["prior_evidence"]["review"]["sha256"] != (
        evidence.sha256_path(paths.source / "review.json")
    )
    snapshot = record["prior_evidence"]["release_approval"][
        "immutable_snapshot"
    ]
    assert evidence.sha256_path(ROOT / snapshot["path"]) == (
        snapshot["sha256"]
    )


@pytest.mark.parametrize(
    "location",
    ("root", "composite", "binary", "preflight"),
)
def test_unknown_record_fields_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    location: str,
) -> None:
    context = _context()
    path = correction.correction_path(context)
    value = json.loads(path.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(value)
    if location == "root":
        mutated["unknown"] = True
    elif location == "composite":
        mutated["composite_installation"]["unknown"] = True
    elif location == "binary":
        mutated["correction_generation"]["handedness_diagnostics"][
            "binary_ink"
        ]["unknown"] = True
    else:
        mutated["correction_generation"]["candidate_preflight"][
            "unknown"
        ] = True
    original = correction._object

    def substitute(candidate: Path, *, label: str):
        if candidate.resolve() == path.resolve():
            return mutated
        return original(candidate, label=label)

    monkeypatch.setattr(correction, "_object", substitute)
    with pytest.raises(
        correction.MewNoteVerticalHandednessCorrectionError,
    ):
        correction.validate_correction(
            context,
            require_new_review=False,
            require_reapproval=False,
        )


def test_standalone_reapproval_requires_pin_and_supersedes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    record = correction.validate_correction(
        context,
        require_new_review=True,
        require_reapproval=False,
    )
    paths = context.batch_paths(
        correction.COLLECTION_ID,
        correction.BATCH_ID,
    )
    prior_approval = record["prior_evidence"]["release_approval"]
    review_path = paths.source / "review.json"
    record_path = correction.correction_path(context)
    record_pin = correction._expected_pin(
        record_path, project_root=ROOT
    )
    review_pin = correction._expected_pin(
        review_path, project_root=ROOT
    )
    predecessor = prior_approval["canonical_overwrite_target"][
        "sha256"
    ]
    fake = {
        "record_type": "mew-note-tc-collection-release-approval",
        "decision": "APPROVED",
        "reviewed_batches": [
            {
                "collection_id": correction.COLLECTION_ID,
                "batch_id": correction.BATCH_ID,
                "review": review_pin,
                correction.APPROVAL_FIELD: record_pin,
            }
        ],
        "supersedes": [
            {
                "release_approval_sha256": predecessor,
                "reason": correction.REASON,
                "corrected_batches": [
                    {
                        "collection_id": correction.COLLECTION_ID,
                        "batch_id": correction.BATCH_ID,
                        correction.APPROVAL_FIELD: record_pin,
                    }
                ],
            }
        ],
    }
    canonical = ROOT / correction.APPROVAL_PATH
    original_object = correction._object
    original_sha = correction.sha256_path

    def object_substitute(path: Path, *, label: str):
        if path.resolve() == canonical.resolve():
            return fake
        return original_object(path, label=label)

    def sha_substitute(path: Path):
        if path.resolve() == canonical.resolve():
            return "f" * 64
        return original_sha(path)

    monkeypatch.setattr(correction, "_object", object_substitute)
    monkeypatch.setattr(correction, "sha256_path", sha_substitute)
    correction._validate_reapproval(
        context,
        prior_approval=prior_approval,
        review_path=review_path,
        record_path=record_path,
    )

    del fake["reviewed_batches"][0][correction.APPROVAL_FIELD]
    with pytest.raises(
        correction.MewNoteVerticalHandednessCorrectionError,
        match="exact correction pin",
    ):
        correction._validate_reapproval(
            context,
            prior_approval=prior_approval,
            review_path=review_path,
            record_path=record_path,
        )
