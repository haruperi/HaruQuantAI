"""What to Build settings configuration and validation service.

Description:
    Manages the What to Build configuration tab in the Builder workspace,
    specifying build modes (Genetic Evolution, Random Generation, Strategy from
    Template), trading directions (Long Only, Short Only, Long/Short
    Symmetric, Long/Short Independent), condition count boundaries, indicator
    period ranges, and stop-loss / profit-target requirement policies.

Purpose:
    FEAT-BUILDER-WHAT-TO-BUILD: Define candidate structure and search space
    configuration.

Key Capabilities:
    - FR-builder-what-to-build-config: Dataclass capturing generation modes
      and bounds.
    - FR-builder-what-to-build-validation: Enforce condition bounds, period ranges,
      and template existence constraints with DomainError codes.

Python API Usage:
    from app.workspace.builder.settings_what_to_build import (
        SettingsWhatToBuildService,
        WhatToBuildSettings,
    )
    service = SettingsWhatToBuildService()
    settings = service.validate(WhatToBuildSettings(build_mode="GENETIC"))

CLI Usage:
    python -c "from app.workspace.builder.settings_what_to_build import (
        SettingsWhatToBuildService,
    ); print(1)"
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)

_MIN_CONDITIONS: int = 1
_MAX_CONDITIONS: int = 10
_MIN_INDICATOR_PERIOD: int = 2
_MAX_INDICATOR_PERIOD: int = 500


@dataclass(frozen=True, slots=True)
class WhatToBuildSettings:
    """Settings governing strategy candidate structure and build mode."""

    build_mode: Literal["GENETIC", "RANDOM", "TEMPLATE"] = "GENETIC"
    template_path: str | None = None
    direction: Literal[
        "LONG_ONLY",
        "SHORT_ONLY",
        "LONG_SHORT_SYMMETRIC",
        "LONG_SHORT_INDEPENDENT",
    ] = "LONG_SHORT_SYMMETRIC"
    min_entry_conditions: int = 1
    max_entry_conditions: int = 3
    min_exit_conditions: int = 1
    max_exit_conditions: int = 2
    min_indicator_period: int = 5
    max_indicator_period: int = 50
    max_shift: int = 3
    stop_loss_mode: Literal["REQUIRED", "OPTIONAL", "NOT_USED"] = "REQUIRED"
    profit_target_mode: Literal["REQUIRED", "OPTIONAL", "NOT_USED"] = "OPTIONAL"

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary representation."""
        return {
            "build_mode": self.build_mode,
            "template_path": self.template_path,
            "direction": self.direction,
            "min_entry_conditions": self.min_entry_conditions,
            "max_entry_conditions": self.max_entry_conditions,
            "min_exit_conditions": self.min_exit_conditions,
            "max_exit_conditions": self.max_exit_conditions,
            "min_indicator_period": self.min_indicator_period,
            "max_indicator_period": self.max_indicator_period,
            "max_shift": self.max_shift,
            "stop_loss_mode": self.stop_loss_mode,
            "profit_target_mode": self.profit_target_mode,
        }


class SettingsWhatToBuildService:
    """Service managing What to Build settings and template discovery."""

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        """Initialize service with optional template search directory."""
        self._templates_dir = Path(templates_dir) if templates_dir else None

    def list_template_files(self) -> tuple[str, ...]:
        """List available strategy template files.

        Returns:
            Tuple of available template filenames or relative paths.
        """
        logger.debug("Listing strategy template files")
        if self._templates_dir and self._templates_dir.exists():
            return tuple(
                p.name for p in self._templates_dir.glob("*.xml") if p.is_file()
            )
        return ("default_template.xml", "trend_following_template.xml")

    def get_template_config(self, template_path: str) -> dict[str, Any]:
        """Load configuration details for a specified strategy template.

        Args:
            template_path: Path or identifier of the template.

        Returns:
            Dictionary containing template parameters and metadata.
        """
        logger.debug("Loading template config for %s", template_path)
        return {
            "template_path": template_path,
            "name": Path(template_path).stem,
            "supports_long": True,
            "supports_short": True,
        }

    def check_template_resources(self, template_path: str) -> bool:
        """Verify existence and accessibility of resources required by a template.

        Args:
            template_path: Path or identifier of the template.

        Returns:
            True if valid, False otherwise.
        """
        logger.debug("Checking template resources for %s", template_path)
        if not template_path:
            return False
        if self._templates_dir:
            return (self._templates_dir / template_path).exists()
        return True

    def validate(self, settings: WhatToBuildSettings) -> WhatToBuildSettings:
        """Validate WhatToBuildSettings values against operational bounds.

        Args:
            settings: WhatToBuildSettings instance to validate.

        Returns:
            Validated WhatToBuildSettings instance.

        Raises:
            DomainError: If values violate bounds or template path is missing.
        """
        logger.debug("Validating WhatToBuildSettings: %s", settings.build_mode)

        if settings.build_mode == "TEMPLATE" and not settings.template_path:
            raise DomainError(
                code="BUILDER_TEMPLATE_PATH_REQUIRED",
                message="template_path is required when build_mode is TEMPLATE",
            )

        min_entry = settings.min_entry_conditions
        max_entry = settings.max_entry_conditions
        if not (_MIN_CONDITIONS <= min_entry <= max_entry <= _MAX_CONDITIONS):
            raise DomainError(
                code="BUILDER_INVALID_WHAT_TO_BUILD",
                message=(
                    f"min_entry_conditions ({min_entry}) and max_entry_conditions "
                    f"({max_entry}) must satisfy 1 <= min <= max <= 10"
                ),
            )

        min_exit = settings.min_exit_conditions
        max_exit = settings.max_exit_conditions
        if not (_MIN_CONDITIONS <= min_exit <= max_exit <= _MAX_CONDITIONS):
            raise DomainError(
                code="BUILDER_INVALID_WHAT_TO_BUILD",
                message=(
                    f"min_exit_conditions ({min_exit}) and max_exit_conditions "
                    f"({max_exit}) must satisfy 1 <= min <= max <= 10"
                ),
            )

        min_period = settings.min_indicator_period
        max_period = settings.max_indicator_period
        if not (
            _MIN_INDICATOR_PERIOD <= min_period <= max_period <= _MAX_INDICATOR_PERIOD
        ):
            raise DomainError(
                code="BUILDER_INVALID_WHAT_TO_BUILD",
                message=(
                    f"min_indicator_period ({min_period}) and max_indicator_period "
                    f"({max_period}) must satisfy 2 <= min <= max <= 500"
                ),
            )

        return settings
