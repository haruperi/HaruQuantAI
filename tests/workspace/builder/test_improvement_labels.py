"""Unit tests for improvement_label formatting helper."""

from __future__ import annotations

import pytest
from app.workspace.builder.improvement_labels import improvement_label


def test_disabled_keeps_existing() -> None:
    """Ensure that use=False returns 'Keep existing' for any action."""
    for action in ["add", "add_or_replace", "replace", None, "", "unknown"]:
        assert improvement_label(use=False, action=action) == "Keep existing"


def test_add_or_replace() -> None:
    """Ensure use=True and action='add_or_replace' returns expected text."""
    assert (
        improvement_label(use=True, action="add_or_replace")
        == "Keep existing or generate randomly"
    )


def test_add() -> None:
    """Ensure use=True and action='add' returns expected text."""
    assert (
        improvement_label(use=True, action="add") == "Keep existing + generate randomly"
    )


@pytest.mark.parametrize(
    "action",
    ["replace", None, "", "custom_unknown_action"],
)
def test_other_actions_generate(action: str | None) -> None:
    """Ensure use=True and replace/None/empty/unknown returns 'Generate randomly'."""
    assert improvement_label(use=True, action=action) == "Generate randomly"
