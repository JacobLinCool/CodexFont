from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.register_imagegen_common_sheet import (
    IMAGEGEN_ROOT,
    RASTER_ROOT,
    RegistrationError,
    descriptor_for,
)


def test_descriptor_is_pending_and_matches_frozen_batch() -> None:
    payload = descriptor_for(
        batch_id="common-0003",
        generator_call="test-call",
        raster=RASTER_ROOT / "common-0003.png",
    )
    assert payload["state"] == "generated-unreviewed"
    assert payload["review"] == {
        "topology": "pending",
        "raster_quality": "pending",
        "vector_quality": "pending",
    }
    assert "".join(payload["grid"]["characters"]) == "是見來地成四元行了所無明指動比出"
    assert payload["grid"]["empty_grid_cells"] == 0


def test_wrong_raster_path_is_rejected(tmp_path: Path) -> None:
    wrong = tmp_path / "common-0003.png"
    wrong.write_bytes((RASTER_ROOT / "common-0003.png").read_bytes())
    with pytest.raises(RegistrationError, match="raster must be exactly"):
        descriptor_for(
            batch_id="common-0003",
            generator_call="test-call",
            raster=wrong,
        )


def test_registered_descriptors_never_claim_approval() -> None:
    for path in sorted((IMAGEGEN_ROOT / "batches").glob("common-*.source.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["state"] == "generated-unreviewed"
        assert set(payload["review"].values()) == {"pending"}
