"""Improvement condition label formatting helper.

Description:
    Provides human-readable status labels for Parts to Improve configuration
    rules in the Builder workspace based on whether a strategy part is active
    (use) and what mutation action (add_or_replace, add, replace) is configured.

Purpose:
    FEAT-BUILDER-IMPROVEMENT-LABELS: Format human-readable improvement condition labels.

Key Capabilities:
    - FR-builder-improvement-labels: Pure function mapping (use, action) to descriptive
      label strings.

Python API Usage:
    from app.workspace.builder.improvement_labels import improvement_label
    text = improvement_label(use=True, action="add")

CLI Usage:
    python -c "from app.workspace.builder.improvement_labels import (
        improvement_label,
    ); print(improvement_label(use=True, action='add'))"
"""

from __future__ import annotations

from app.core.host.logging import get_logger

logger = get_logger(__name__)


def improvement_label(*, use: bool, action: str | None) -> str:
    """Format human-readable label for improvement rule configuration.

    Args:
        use: Whether this part is selected for mutation/improvement.
        action: The improvement action ('add_or_replace', 'add', 'replace', or None).

    Returns:
        Formatted label string.
    """
    if not use:
        logger.debug("Part not used; returning 'Keep existing'")
        return "Keep existing"

    if action == "add_or_replace":
        logger.debug("Action 'add_or_replace' -> 'Keep existing or generate randomly'")
        return "Keep existing or generate randomly"
    if action == "add":
        logger.debug("Action 'add' -> 'Keep existing + generate randomly'")
        return "Keep existing + generate randomly"

    logger.debug("Action '%s' -> 'Generate randomly'", action)
    return "Generate randomly"
