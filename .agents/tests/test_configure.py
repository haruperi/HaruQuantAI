"""Configuration generation regression tests."""

from __future__ import annotations

import importlib.util
import tomllib
from types import ModuleType


def test_supported_adapters_emit_valid_toml(orc: ModuleType) -> None:
    configure = importlib.util.spec_from_file_location(
        "workflow_configure", orc.AGENTS_DIR / "configure.py"
    )
    assert configure
    assert configure.loader
    module = importlib.util.module_from_spec(configure)
    configure.loader.exec_module(module)
    for vendor in module.VENDORS:
        text = module._role_toml(
            "planner", vendor, 'model "quoted"', "high", "provider\\id"
        )
        tomllib.loads(text)


def test_repo_configuration_is_portable(orc: ModuleType) -> None:
    text = (orc.AGENTS_DIR / "orchestrator.toml").read_text(encoding="utf-8")
    assert "repo_path" not in text
