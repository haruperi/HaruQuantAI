"""Configuration generation regression tests."""

from __future__ import annotations

import importlib.util
import tomllib
from types import ModuleType

import pytest


def _load_configure(orc: ModuleType) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "workflow_configure", orc.AGENTS_DIR / "configure.py"
    )
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_session_capable_adapters_emit_valid_toml(orc: ModuleType) -> None:
    module = _load_configure(orc)
    for vendor in module.SESSION_CLI_VENDORS:
        text = module._role_toml(
            "planner", vendor, 'model "quoted"', "high", "provider\\id"
        )
        parsed = tomllib.loads(text)
        assert parsed["session_continuity"] == "required"
        assert parsed["command"][-1] == "{prompt}"


def test_multi_delegate_rejects_unverified_native_session_adapter(
    orc: ModuleType,
) -> None:
    module = _load_configure(orc)
    with pytest.raises(ValueError, match="no verified native session adapter"):
        module._role_toml("planner", "claude", "sonnet", "high", "")


def test_repo_configuration_is_portable(orc: ModuleType) -> None:
    text = (orc.AGENTS_DIR / "orchestrator.toml").read_text(encoding="utf-8")
    assert "repo_path" not in text
