"""Settings for selecting candidate strategies and databanks to retest.

Description:
    Provides WhatToRetestSettings model and SettingsWhatToRetestService
    resolving candidate record keys, validating source and target databanks,
    and enforcing non-empty databank requirements.

Purpose:
    FEAT-RETESTER-SETTINGS: Candidate strategy selection and databank routing.

Key Capabilities:
    - FR-retest-what-to-retest-settings: Configure source/target databanks,
      strategy selection, and failed strategy retention flags.
    - FR-retest-what-to-retest-resolve: Resolve record keys via RetestPreflight.

Python API Usage:
    from app.workspace.retester.settings_what_to_retest import (
        WhatToRetestSettings,
        SettingsWhatToRetestService,
    )
    settings = WhatToRetestSettings(source_databank="Results")
    service = SettingsWhatToRetestService()
    keys = service.resolve_keys(settings, ("s1", "s2"))

CLI Usage:
    python -m app.cli retest what-to-retest --source Results --target Filtered
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.retester.preflight import RetestPreflight

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WhatToRetestSettings:
    """Settings controlling strategy and databank selection for retesting."""

    source_databank: str = "Results"
    target_databank: str = "Results"
    selected_keys: tuple[str, ...] | None = None
    dismiss_failed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary representation."""
        return {
            "source_databank": self.source_databank,
            "target_databank": self.target_databank,
            "selected_keys": list(self.selected_keys)
            if self.selected_keys is not None
            else None,
            "dismiss_failed": self.dismiss_failed,
        }


class SettingsWhatToRetestService:
    """Service validating what-to-retest configurations and resolving keys."""

    @staticmethod
    def validate_settings(settings: WhatToRetestSettings) -> None:
        """Validate databank names are non-empty strings.

        Args:
            settings: Configuration settings to validate.

        Raises:
            DomainError: If source or target databank is blank.
        """
        if not settings.source_databank.strip() or not settings.target_databank.strip():
            logger.error(
                "FR-retest-what-to-retest-settings: empty databank name provided"
            )
            raise DomainError(
                code="RETESTER_DATABANK_REQUIRED",
                message="Source and target databank names cannot be blank",
            )

    @classmethod
    def resolve_keys(
        cls,
        settings: WhatToRetestSettings,
        databank_keys: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Resolve candidate record keys using RetestPreflight.

        Args:
            settings: What-to-retest configuration.
            databank_keys: Strategy keys available in the source databank.

        Returns:
            Resolved tuple of strategy record keys.

        Raises:
            DomainError: If databank validation fails.
            TypeError: If key types are invalid.
        """
        cls.validate_settings(settings)
        resolved = RetestPreflight.record_keys(
            databank_keys=databank_keys,
            selected_keys=settings.selected_keys,
        )
        logger.info(
            "FR-retest-what-to-retest-resolve: resolved %d strategy keys "
            "from databank %s",
            len(resolved),
            settings.source_databank,
        )
        return resolved
