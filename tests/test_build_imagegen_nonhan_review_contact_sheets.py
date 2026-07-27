from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image
import pytest

from scripts import build_imagegen_nonhan_review_contact_sheets as contact
from scripts import imagegen_nonhan_pipeline as pipeline


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_batch(root: Path, batch_id: str) -> Path:
    batch = root / "build" / f"imagegen-{batch_id}"
    proof_directory = batch / "proof"
    proof_directory.mkdir(parents=True)
    proofs: list[dict[str, object]] = []
    for size in pipeline.SMALL_SIZE_PIXELS:
        for polarity in contact.POLARITIES:
            width = size + (3 if polarity == "white-on-black" else 1)
            height = size + 2
            background = 0 if polarity == "white-on-black" else 255
            foreground = 255 - background
            image = Image.new("L", (width, height), background)
            image.putpixel((width // 2, height // 2), foreground)
            relative = Path("proof") / f"{polarity}-{size}px.png"
            path = batch / relative
            image.save(path)
            proofs.append(
                {
                    "kind": "small-size",
                    "size_px": size,
                    "polarity": polarity,
                    "path": relative.as_posix(),
                    "sha256": _sha256(path),
                }
            )
    report = {
        "pipeline": pipeline.PIPELINE_ID,
        "batch_id": f"imagegen-{batch_id}",
        "source_descriptor_sha256": "a" * 64,
        "glyphs": [
            {"codepoint": "U+0041"},
            {"codepoint": "U+0042"},
        ],
        "proofs": proofs,
    }
    (batch / "report.json").write_text(
        json.dumps(report),
        encoding="utf-8",
    )
    return batch


def test_contact_sheets_preserve_every_native_proof_pixel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(contact, "ROOT", tmp_path)
    batch_id = "nonhan-0001"
    _write_batch(tmp_path, batch_id)
    output = tmp_path / "review"

    manifest_path = contact.build_contact_sheets(
        [batch_id],
        build_root=tmp_path / "build",
        output_directory=output,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["pipeline"] == pipeline.PIPELINE_ID
    assert manifest["batch_count"] == 1
    assert manifest["groups"][0]["resampled"] is False
    batch_record = manifest["batches"][0]
    composed = Image.open(tmp_path / batch_record["contact_sheet"])
    composed.load()
    for proof in batch_record["proofs"]:
        assert proof["resampled"] is False
        source = Image.open(tmp_path / proof["path"])
        source.load()
        box = (
            proof["paste_x"],
            proof["paste_y"],
            proof["paste_x"] + proof["native_width_px"],
            proof["paste_y"] + proof["native_height_px"],
        )
        assert composed.crop(box).tobytes() == source.tobytes()


def test_contact_sheets_refuse_mutated_hash_pinned_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(contact, "ROOT", tmp_path)
    batch_id = "nonhan-0001"
    batch = _write_batch(tmp_path, batch_id)
    proof = batch / "proof" / "black-on-white-12px.png"
    image = Image.open(proof)
    image.load()
    image.putpixel((0, 0), 0)
    image.save(proof)

    with pytest.raises(contact.ContactSheetError, match="proof hash mismatch"):
        contact.build_contact_sheets(
            [batch_id],
            build_root=tmp_path / "build",
            output_directory=tmp_path / "review",
        )
