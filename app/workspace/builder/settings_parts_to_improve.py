"""Parts to Improve settings and rules description service.

Description:
    Manages the Parts to Improve configuration tab in the Builder workspace,
    specifying which structural segments of a template or existing strategy
    (entry rules, exit rules, order types, SL, PT, trailing stop) are mutated,
    replaced, or augmented during improvement workflows.

Purpose:
    FEAT-BUILDER-PARTS-TO-IMPROVE: Configure selective strategy mutation rules.

Key Capabilities:
    - FR-builder-parts-to-improve-rules: Structured dataclasses for part
      improvement rules.
    - FR-builder-parts-to-improve-describe: Generate human-readable labels and
      validate condition count bounds using improvement_label helper.

Python API Usage:
    from app.workspace.builder.settings_parts_to_improve import (
        PartsToImproveSettings,
        SettingsPartsToImproveService,
    )
    service = SettingsPartsToImproveService()
    labels = service.describe_rules(PartsToImproveSettings())

CLI Usage:
    python -c "from app.workspace.builder.settings_parts_to_improve import (
        SettingsPartsToImproveService,
    ); print(1)"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.builder.improvement_labels import improvement_label

logger = get_logger(__name__)

_MIN_CONDITIONS: int = 1
_MAX_CONDITIONS: int = 10

PartId = Literal[
    "entry_long",
    "exit_long",
    "entry_short",
    "exit_short",
    "order_types",
    "stop_loss",
    "profit_target",
    "trailing_stop",
]

ImprovementAction = Literal["add_or_replace", "add", "replace"]


@dataclass(frozen=True, slots=True)
class PartImprovementRule:
    """Individual rule governing mutation of a specific strategy component."""

    part_id: PartId
    use: bool = False
    action: ImprovementAction = "replace"
    min_conditions: int = 1
    max_conditions: int = 3

    def to_dict(self) -> dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "part_id": self.part_id,
            "use": self.use,
            "action": self.action,
            "min_conditions": self.min_conditions,
            "max_conditions": self.max_conditions,
        }


def _build_default_rules() -> tuple[PartImprovementRule, ...]:
    """Build default tuple of PartImprovementRule instances."""
    parts: tuple[PartId, ...] = (
        "entry_long",
        "exit_long",
        "entry_short",
        "exit_short",
        "order_types",
        "stop_loss",
        "profit_target",
        "trailing_stop",
    )
    return tuple(PartImprovementRule(part_id=p) for p in parts)


@dataclass(frozen=True, slots=True)
class PartsToImproveSettings:
    """Settings governing strategy improvement mode and rules."""

    enabled: bool = False
    source_strategy_id: str | None = None
    rules: tuple[PartImprovementRule, ...] = field(default_factory=_build_default_rules)

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "enabled": self.enabled,
            "source_strategy_id": self.source_strategy_id,
            "rules": [r.to_dict() for r in self.rules],
        }


class SettingsPartsToImproveService:
    """Service formatting and validating Parts to Improve settings."""

    def describe_rules(self, settings: PartsToImproveSettings) -> dict[str, str]:
        """Map each part improvement rule to its descriptive condition label.

        Args:
            settings: PartsToImproveSettings instance.

        Returns:
            Dictionary mapping part_id to formatted label string.

        Raises:
            DomainError: If min_conditions or max_conditions violate bounds.
        """
        logger.debug("Describing %d improvement rules", len(settings.rules))
        descriptions: dict[str, str] = {}

        for rule in settings.rules:
            min_c = rule.min_conditions
            max_c = rule.max_conditions
            if not (_MIN_CONDITIONS <= min_c <= max_c <= _MAX_CONDITIONS):
                raise DomainError(
                    code="BUILDER_INVALID_IMPROVEMENT_BOUNDS",
                    message=(
                        f"Rule for '{rule.part_id}' has invalid bounds: "
                        f"min_conditions={min_c}, max_conditions={max_c}. "
                        "Must satisfy 1 <= min <= max <= 10."
                    ),
                )

            label = improvement_label(use=rule.use, action=rule.action)
            descriptions[rule.part_id] = label

        return descriptions
