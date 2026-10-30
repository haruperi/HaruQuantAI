"""Unit tests for WaitForSettings and WaitForConfig.

Description:
    Validates parsing, serialization, identity preservation, default fallbacks,
    whitespace handling, and non-destructive dictionary updates for task WaitFor settings.

Purpose:
    FEAT-TASK-MANAGER: Validate task automation WaitFor configuration helper.

Key Capabilities:
    - FR-task-manager-wait-for-settings: Verify WaitFor load/write semantics.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest
from app.workspace.task_manager.wait_for_settings import (
    WaitForConfig,
    WaitForSettings,
)


def test_wait_defaults_and_missing_parent() -> None:
    """Load from empty dict or None preserves defaults or identity."""
    # Empty dict produces default config
    cfg_empty = WaitForSettings.load({})
    assert cfg_empty == WaitForConfig("", "user")

    # None without current produces default config
    cfg_none_default = WaitForSettings.load(None)
    assert cfg_none_default == WaitForConfig("", "user")

    # None with current preserves exact identity of current
    current = WaitForConfig("old", "file")
    preserved = WaitForSettings.load(None, current)
    assert preserved is current
    assert preserved.file == "old"
    assert preserved.action == "file"


def test_wait_preserves_text() -> None:
    """Values including leading/trailing spaces and custom action names are preserved."""
    payload = {"file": " a&b ", "action": "custom"}
    cfg = WaitForSettings.load(payload)
    assert cfg.file == " a&b "
    assert cfg.action == "custom"


def test_wait_write_preserves_attributes_and_siblings() -> None:
    """Writing config preserves existing unrelated keys and re-loads correctly."""
    target: dict[str, Any] = {
        "extra": "keep",
        "nested": {"k": 1, "items": [1, 2, 3]},
    }
    config = WaitForConfig("a&b", "file")
    WaitForSettings.write(target, config)

    # File and action are set
    assert target["file"] == "a&b"
    assert target["action"] == "file"

    # Unrelated keys and nested values are preserved
    assert target["extra"] == "keep"
    assert target["nested"] == {"k": 1, "items": [1, 2, 3]}

    # Re-loading from target yields identical configuration
    reloaded = WaitForSettings.load(target)
    assert reloaded == WaitForConfig("a&b", "file")


def test_wait_legacy_keys_and_empty_values(caplog: pytest.LogCaptureFixture) -> None:
    """Fallback to capitalized keys and empty values defaulting to defaults."""
    with caplog.at_level(logging.DEBUG):
        # Capitalized keys supported as fallback
        cfg_cap = WaitForSettings.load({"File": "path/test.txt", "Action": "run"})
        assert cfg_cap.file == "path/test.txt"
        assert cfg_cap.action == "run"

        # Explicit empty string uses defaults
        cfg_empty_vals = WaitForSettings.load({"file": "", "action": ""})
        assert cfg_empty_vals.file == ""
        assert cfg_empty_vals.action == "user"

        # Verify operational logging occurred
        assert any(
            "FR-task-manager-wait-for-settings" in record.message
            for record in caplog.records
        )
