"""Unit tests for SettingsWhatToBuild service and models."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.settings_what_to_build import (
    SettingsWhatToBuildService,
    WhatToBuildSettings,
)


def test_default_validation_passes() -> None:
    """Ensure default settings pass validation unchanged."""
    service = SettingsWhatToBuildService()
    settings = WhatToBuildSettings()
    validated = service.validate(settings)
    assert validated == settings
    assert validated.to_dict()["build_mode"] == "GENETIC"


def test_template_mode_requires_template_path() -> None:
    """Ensure build_mode='TEMPLATE' requires non-empty template_path."""
    service = SettingsWhatToBuildService()
    settings = WhatToBuildSettings(build_mode="TEMPLATE", template_path=None)

    with pytest.raises(DomainError) as exc_info:
        service.validate(settings)
    assert exc_info.value.code == "BUILDER_TEMPLATE_PATH_REQUIRED"


def test_invalid_condition_bounds_raise() -> None:
    """Ensure invalid condition bounds raise BUILDER_INVALID_WHAT_TO_BUILD."""
    service = SettingsWhatToBuildService()

    # min > max
    with pytest.raises(DomainError) as exc_info:
        service.validate(
            WhatToBuildSettings(min_entry_conditions=5, max_entry_conditions=2)
        )
    assert exc_info.value.code == "BUILDER_INVALID_WHAT_TO_BUILD"

    # min < 1
    with pytest.raises(DomainError) as exc_info:
        service.validate(
            WhatToBuildSettings(min_entry_conditions=0, max_entry_conditions=2)
        )
    assert exc_info.value.code == "BUILDER_INVALID_WHAT_TO_BUILD"

    # max > 10
    with pytest.raises(DomainError) as exc_info:
        service.validate(
            WhatToBuildSettings(min_entry_conditions=1, max_entry_conditions=11)
        )
    assert exc_info.value.code == "BUILDER_INVALID_WHAT_TO_BUILD"


def test_invalid_indicator_periods_raise() -> None:
    """Ensure invalid indicator period bounds raise BUILDER_INVALID_WHAT_TO_BUILD."""
    service = SettingsWhatToBuildService()

    # min < 2
    with pytest.raises(DomainError) as exc_info:
        service.validate(
            WhatToBuildSettings(min_indicator_period=1, max_indicator_period=20)
        )
    assert exc_info.value.code == "BUILDER_INVALID_WHAT_TO_BUILD"

    # min > max
    with pytest.raises(DomainError) as exc_info:
        service.validate(
            WhatToBuildSettings(min_indicator_period=60, max_indicator_period=50)
        )
    assert exc_info.value.code == "BUILDER_INVALID_WHAT_TO_BUILD"

    # max > 500
    with pytest.raises(DomainError) as exc_info:
        service.validate(
            WhatToBuildSettings(min_indicator_period=10, max_indicator_period=600)
        )
    assert exc_info.value.code == "BUILDER_INVALID_WHAT_TO_BUILD"


def test_template_helpers(tmp_path: pytest.TempPathFactory) -> None:
    """Verify template listing, config retrieval, and resource checks."""
    service = SettingsWhatToBuildService()
    files = service.list_template_files()
    assert len(files) > 0

    cfg = service.get_template_config("sample.xml")
    assert cfg["template_path"] == "sample.xml"
    assert service.check_template_resources("sample.xml") is True
    assert service.check_template_resources("") is False
