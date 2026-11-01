"""Overview-template selection policy helper.

Description:
    Initial overview-template selection policy helper replicating donor
    controller template precedence rules for the Results overview tab.

Purpose:
    FEAT-RESULTS-OVERVIEW-POLICY: Select deterministic overview stats templates.

Key Capabilities:
    - FR-results-template-selection: Determine active template key with
      SQDefault priority.

Python API Usage:
    from app.workspace.results.overview_template_policy import (
        OverviewTemplatePolicy,
    )
    selected = OverviewTemplatePolicy.select(("CustomTemplate", "SQDefault"))

CLI Usage:
    python -m app.cli results template-select \
        --templates "CustomTemplate,SQDefault"
"""

from __future__ import annotations

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class OverviewTemplatePolicy:
    """Helper policy for resolving initial overview template selection."""

    @classmethod
    def select(cls, values: tuple[str, ...]) -> str:
        """Select default overview template following donor precedence rules.

        Args:
            values: Tuple of available template identifier strings.

        Returns:
            Chosen template identifier string.

        Raises:
            TypeError: If values is not a tuple or contains non-string items.
        """
        if not isinstance(values, tuple):
            raise TypeError("values must be a tuple of strings")

        for item in values:
            if not isinstance(item, str):
                raise TypeError("values must be a tuple of strings")

        selected = "SQDefault" if not values or "SQDefault" in values else values[0]

        logger.info(
            "FR-results-template-selection: resolved template %s from %d candidates",
            selected,
            len(values),
        )
        return selected
