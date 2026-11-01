"""Unit tests for SettingsPartsToImprove service and models."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.settings_parts_to_improve import (
    PartImprovementRule,
    PartsToImproveSettings,
    SettingsPartsToImproveService,
)


def test_describe_rules_golden_fixture() -> None:
    """Verify description labels for use=True, action='add' vs use=False, action='add'."""
    service = SettingsPartsToImproveService()
    settings = PartsToImproveSettings(
        rules=(
            PartImprovementRule(part_id="entry_long", use=True, action="add"),
            PartImprovementRule(part_id="exit_long", use=False, action="add"),
        )
    )

    descriptions = service.describe_rules(settings)
    assert descriptions["entry_long"] == "Keep existing + generate randomly"
    assert descriptions["exit_long"] == "Keep existing"


def test_default_rules_describe_cleanly() -> None:
    """Verify default rules all produce 'Keep existing' when disabled."""
    service = SettingsPartsToImproveService()
    settings = PartsToImproveSettings()
    descriptions = service.describe_rules(settings)

    assert len(descriptions) == 8
    assert all(desc == "Keep existing" for desc in descriptions.values())
    assert settings.to_dict()["enabled"] is False


def test_invalid_condition_bounds_raise() -> None:
    """Ensure bounds outside 1..10 or min > max raise BUILDER_INVALID_IMPROVEMENT_BOUNDS."""
    service = SettingsPartsToImproveService()

    # min > max
    with pytest.raises(DomainError) as exc:
        service.describe_rules(
            PartsToImproveSettings(
                rules=(
                    PartImprovementRule(
                        part_id="entry_long", min_conditions=4, max_conditions=2
                    ),
                )
            )
        )
    assert exc.value.code == "BUILDER_INVALID_IMPROVEMENT_BOUNDS"

    # min < 1
    with pytest.raises(DomainError) as exc:
        service.describe_rules(
            PartsToImproveSettings(
                rules=(
                    PartImprovementRule(
                        part_id="entry_long", min_conditions=0, max_conditions=3
                    ),
                )
            )
        )
    assert exc.value.code == "BUILDER_INVALID_IMPROVEMENT_BOUNDS"

    # max > 10
    with pytest.raises(DomainError) as exc:
        service.describe_rules(
            PartsToImproveSettings(
                rules=(
                    PartImprovementRule(
                        part_id="entry_long", min_conditions=1, max_conditions=12
                    ),
                )
            )
        )
    assert exc.value.code == "BUILDER_INVALID_IMPROVEMENT_BOUNDS"
