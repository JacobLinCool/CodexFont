from __future__ import annotations

import copy
from pathlib import Path

from PIL import Image
import pytest

from scripts import mew_note_batch_evidence as evidence
from scripts import mew_note_release_approval as release_approval
from scripts import mew_note_release_deviation as release_deviation
from scripts import (
    mew_note_post_review_vertical_orientation_correction as correction,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SHA256 = (
    "ef4f3c21df6b685cc151d90f26ab2101d8473455c3048a6bec6bd160fc18cbaf"
)
CALL_ID = "call_WUgMqJyIuObkzWRskiXh3M6S"


@pytest.fixture(scope="module")
def historical_orientation() -> tuple[
    evidence.FamilyContext,
    dict[str, object],
]:
    context = evidence.load_context(ROOT)
    release = release_deviation.validate_release_deviation(
        project_root=ROOT
    )
    release_approval._validate_correction_ledger_inventory(context)
    audit = release_approval._discover_transition_audit(
        context,
        release_deviation=release,
    )
    spec = next(
        item
        for item in release_approval.CORRECTION_TRANSITION_SPECS
        if item.stage == "orientation"
    )
    path = correction.correction_path(context)
    record = release_approval._read_object(
        path,
        label="historical vertical-orientation correction",
    )
    predecessor = release_approval._correction_predecessor_sha256(
        spec,
        record,
        project_root=ROOT,
    )
    release_approval._validate_historical_correction_admission(
        audit.predecessor_approval,
        spec=spec,
        collection_id=correction.COLLECTION_ID,
        batch_id=correction.BATCH_ID,
        path=path,
        ledger_predecessor_sha256=predecessor,
        project_root=ROOT,
    )
    assert audit.latest_order == 40
    assert audit.predecessor_approval_sha256 == (
        "bbef5f1b5f5ab050e921afda6f826e49c25dc18aec38197e20492d9a5e579c18"
    )
    return context, record


def test_correction_is_vertical_specific_and_not_a_metric_claim() -> None:
    implementation = (ROOT / correction.IMPLEMENTATION_PATH).read_text(
        encoding="utf-8"
    )

    assert correction.REASON == "release-vertical-orientation-rejected"
    assert "release-metric-envelope-rejected" not in implementation
    assert "mew_note_post_review_correction" not in implementation
    assert "mew_note_release_approval" not in implementation
    assert [target["codepoint"] for target in correction.TARGETS] == [
        "U+300D",
        "U+300F",
    ]


def test_historical_correction_pins_raw_candidate_and_atomic_composite(
    historical_orientation: tuple[
        evidence.FamilyContext,
        dict[str, object],
    ],
) -> None:
    context, record = historical_orientation
    paths = context.batch_paths(
        correction.COLLECTION_ID,
        correction.BATCH_ID,
    )
    history = evidence.validate_history(
        context,
        correction.COLLECTION_ID,
        correction.BATCH_ID,
    )
    step = next(
        item for item in history["steps"] if item["call_id"] == CALL_ID
    )

    assert record["candidate_generation"]["call_id"] == CALL_ID
    assert record["candidate_generation"]["raw_candidate"]["sha256"] == (
        CANDIDATE_SHA256
    )
    assert record["reason"] == correction.REASON
    assert record["required_next_gates"] == [
        "independent-raster-vector-technical-review",
        "collection-release-reapproval",
    ]
    assert record["prior_evidence"]["review"]["sha256"] != (
        evidence.sha256_path(paths.source / "review.json")
    )
    assert record["prior_evidence"]["release_approval"]["retention"] == (
        "hash-only-superseded-after-reapproval"
    )
    assert record["correction_generation"]["raster"]["sha256"] == (
        step["output"]["sha256"]
    )
    assert record["correction_generation"]["raster"]["sha256"] != (
        evidence.sha256_path(paths.source / "raster.png")
    )


def test_only_cells_six_and_eight_were_installed_from_raw_candidate(
    historical_orientation: tuple[
        evidence.FamilyContext,
        dict[str, object],
    ],
    tmp_path: Path,
) -> None:
    context, record = historical_orientation
    composite = record["composite_installation"]
    candidate = correction._load_rgb_png(
        correction.raw_candidate_path(context),
        label="test raw candidate",
    )
    current = (
        context.batch_paths(
            correction.COLLECTION_ID,
            correction.BATCH_ID,
        ).source
        / "raster.png"
    )
    reconstructed_path = tmp_path / "orientation-composite.png"
    reconstructed = correction._load_rgb_png(
        current,
        label="current handedness successor",
    )
    for target in correction.TARGETS:
        box = tuple(target["replacement_box"])
        reconstructed.paste(candidate.crop(box), box)
    correction._save_png(reconstructed, reconstructed_path)
    installed = correction._load_rgb_png(
        reconstructed_path,
        label="reconstructed historical orientation composite",
    )

    assert evidence.sha256_path(reconstructed_path) == (
        composite["installed_composite_sha256"]
    )
    assert composite["algorithm"] == correction.COMPOSITE_ALGORITHM
    assert [region["cell"] for region in composite["regions"]] == [6, 8]
    for target, region in zip(
        correction.TARGETS,
        composite["regions"],
        strict=True,
    ):
        assert region["replacement_box"] == target["replacement_box"]
        assert correction._region_sha256(
            candidate, target["replacement_box"]
        ) == region["candidate_region_sha256"]
        assert correction._region_sha256(
            installed, target["replacement_box"]
        ) == region["candidate_region_sha256"]
        assert region["superseded_region_sha256"] != (
            region["candidate_region_sha256"]
        )
    assert correction._framed_pixel_sha256(
        installed,
        regions=[
            target["replacement_box"]
            for target in correction.TARGETS
        ],
        include_regions=False,
    ) == composite["preserved_outside_regions_sha256"]


def test_orientation_rejection_and_replacement_are_both_proven(
    historical_orientation: tuple[
        evidence.FamilyContext,
        dict[str, object],
    ],
) -> None:
    _context, record = historical_orientation
    assert [
        item["decision"]
        for item in record["rejected_orientation"]
    ] == ["REJECT", "REJECT"]
    accepted = record["correction_generation"][
        "orientation_diagnostics"
    ]
    assert [item["decision"] for item in accepted] == [
        "ACCEPT",
        "ACCEPT",
    ]
    assert all(
        item["horizontal_to_vertical_ratio"]
        >= item["minimum_horizontal_to_vertical_ratio"]
        for item in accepted
    )
    assert all(
        item["micro_edge_count"] == 0
        and item["acute_micro_turn_count"] == 0
        for item in accepted
    )
    assert len(
        record["correction_generation"][
            "unchanged_non_target_glyphs"
        ]
    ) == 14


def test_history_step_eight_is_exact_orientation_composite(
    historical_orientation: tuple[
        evidence.FamilyContext,
        dict[str, object],
    ],
) -> None:
    context, record = historical_orientation
    history = evidence.validate_history(
        context,
        correction.COLLECTION_ID,
        correction.BATCH_ID,
    )
    matching = [
        item for item in history["steps"] if item["call_id"] == CALL_ID
    ]
    assert len(matching) == 1
    step = matching[0]

    assert history["steps"][7] == step
    assert step["disposition"] == "rejected"
    assert step["actual_tool_prompt"]["path"].endswith(
        "tool-step-0008.txt"
    )
    assert step["actual_tool_prompt"] == (
        record["candidate_generation"]["actual_tool_prompt"]
    )
    assert step["output"]["sha256"] == (
        record["composite_installation"][
            "installed_composite_sha256"
        ]
    )
    assert step["output"]["sha256"] != CANDIDATE_SHA256
    assert step["parent_output_sha256"] == (
        record["prior_evidence"]["raster"]["sha256"]
    )


@pytest.mark.parametrize(
    "location",
    ("root", "composite", "candidate_preflight"),
)
def test_unknown_fields_fail_closed(
    historical_orientation: tuple[
        evidence.FamilyContext,
        dict[str, object],
    ],
    location: str,
) -> None:
    _context, value = historical_orientation
    mutated = copy.deepcopy(value)
    if location == "root":
        mutated["unknown"] = True
    elif location == "composite":
        mutated["composite_installation"]["unknown"] = True
    else:
        mutated["correction_generation"]["candidate_preflight"][
            "unknown"
        ] = True
    assert correction.canonical_json_sha256(
        {
            key: item
            for key, item in mutated.items()
            if key != "correction_sha256"
        }
    ) != mutated["correction_sha256"]


def test_pixel_hash_selection_is_deterministic_and_disjoint() -> None:
    image = Image.new("RGB", (1254, 1254), "white")
    image.putpixel((2, 2), (0, 0, 0))
    regions = ([1, 1, 4, 4],)

    inside = correction._framed_pixel_sha256(
        image,
        regions=regions,
        include_regions=True,
    )
    outside = correction._framed_pixel_sha256(
        image,
        regions=regions,
        include_regions=False,
    )
    assert inside != outside
    assert inside == correction._framed_pixel_sha256(
        image,
        regions=regions,
        include_regions=True,
    )

    changed_inside = image.copy()
    changed_inside.putpixel((2, 2), (1, 1, 1))
    assert correction._framed_pixel_sha256(
        changed_inside,
        regions=regions,
        include_regions=True,
    ) != inside
    assert correction._framed_pixel_sha256(
        changed_inside,
        regions=regions,
        include_regions=False,
    ) == outside


def test_exclusive_lock_rejects_concurrent_apply(tmp_path: Path) -> None:
    record_path = tmp_path / "correction.json"

    with correction._exclusive_lock(record_path):
        with pytest.raises(
            correction.MewNoteVerticalOrientationCorrectionError,
            match="correction lock already exists",
        ):
            with correction._exclusive_lock(record_path):
                pass

    assert not record_path.with_name(
        f".{record_path.name}.lock"
    ).exists()


def test_exclusive_lock_stays_fail_closed_after_exception(
    tmp_path: Path,
) -> None:
    record_path = tmp_path / "correction.json"
    lock_path = record_path.with_name(f".{record_path.name}.lock")

    with pytest.raises(RuntimeError, match="simulated uncertain install"):
        with correction._exclusive_lock(record_path):
            raise RuntimeError("simulated uncertain install")

    assert lock_path.is_file()
    lock_path.unlink()
