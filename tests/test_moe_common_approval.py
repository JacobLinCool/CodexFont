from __future__ import annotations

from fontTools.ttLib import TTFont

from scripts import moe_common_approval
from scripts.moe_common import load_moe_common


def test_moe_common_extension_is_fully_approved_and_complete() -> None:
    approved = moe_common_approval.validate_approval()
    assert len(approved.batches) == 116
    assert len(approved.characters) == 1844
    assert len(set(approved.characters)) == 1844
    assert approved.reviewer_name == "Codex"
    assert approved.approver_name == "Codex"


def test_release_contains_every_moe_common_character() -> None:
    path = (
        moe_common_approval.ROOT
        / "dist/clear-hand-tc/font/ClearHandTC-Regular.ttf"
    )
    with TTFont(path, checkChecksums=2) as font:
        cmap = set(font.getBestCmap())
    moe_common = {record.codepoint for record in load_moe_common()}
    assert len(moe_common) == 4808
    assert moe_common <= cmap
    assert len(moe_common - cmap) == 0
