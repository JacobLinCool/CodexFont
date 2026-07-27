from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/design-font-family"
VALIDATOR = SKILL / "scripts/validate_design_brief.py"
TEMPLATE = SKILL / "assets/design-brief.template.json"


def _module():
    spec = importlib.util.spec_from_file_location("design_brief_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_design_font_family_skill_has_valid_brief_template() -> None:
    module = _module()
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    module.validate(payload)
    assert (SKILL / "SKILL.md").is_file()
    assert (SKILL / "agents/openai.yaml").is_file()


def test_design_brief_rejects_reference_outline_import() -> None:
    module = _module()
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    payload["references"][0]["outline_import_allowed"] = True
    with pytest.raises(ValueError, match="outline"):
        module.validate(payload)


def test_design_brief_accepts_preview_opentype_version() -> None:
    module = _module()
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    payload["family"]["version"] = "0.100"
    module.validate(payload)


@pytest.mark.parametrize(
    "version",
    ("00.100", "0.10", "01.000", "-0.100", "preview"),
)
def test_design_brief_rejects_malformed_opentype_version(
    version: str,
) -> None:
    module = _module()
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    payload["family"]["version"] = version
    with pytest.raises(ValueError, match="OpenType form"):
        module.validate(payload)


@pytest.mark.parametrize("value", ("2", True, 1, 2.0))
def test_design_brief_rejects_invalid_reproducible_build_count(
    value: object,
) -> None:
    module = _module()
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    payload["acceptance"]["reproducible_build_count"] = value
    with pytest.raises(ValueError, match="reproducible builds"):
        module.validate(payload)
