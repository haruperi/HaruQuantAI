"""Retest value source normalization helper.

Description:
    Normalizes legacy boolean string flags ("false", "true") into canonical
    data source choices ("custom", "strategy") for automated retest configurations.

Purpose:
    FEAT-RETESTER-PREFLIGHT: Provide legacy value source normalization.

Key Capabilities:
    - FR-retest-value-source-normalization: Map "false" to "custom" and "true"
      to "strategy" while preserving valid strings and None.

Python API Usage:
    from app.workspace.retester.value_source import RetestValueSource
    source = RetestValueSource.normalize("false")  # returns "custom"

CLI Usage:
    python -m app.cli retest normalize-source --value false
"""

from __future__ import annotations

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class RetestValueSource:
    """Helper for normalizing legacy value source flags."""

    @staticmethod
    def normalize(value: str | None) -> str | None:
        """Normalize legacy boolean flag string to canonical source name.

        Args:
            value: Legacy source string ("false", "true", "custom",
                "strategy") or None.

        Returns:
            Normalized source string ("custom", "strategy", or original),
            or None.

        Raises:
            TypeError: If value is not a string or None (including booleans).
        """
        if value is not None and not isinstance(value, str):
            raise TypeError("value must be str or None")

        if value == "false":
            logger.info(
                "FR-retest-value-source-normalization: mapped 'false' to 'custom'"
            )
            return "custom"
        if value == "true":
            logger.info(
                "FR-retest-value-source-normalization: mapped 'true' to 'strategy'"
            )
            return "strategy"

        logger.debug(
            "FR-retest-value-source-normalization: preserved value %s",
            value,
        )
        return value
