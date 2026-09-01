"""Tests for the strict empty development compatibility configuration."""

import pytest
from app.services.plugins.development_compatibility.config import (
    DevelopmentCompatibilityConfig,
)


def test_empty_configuration_is_accepted() -> None:
    assert (
        DevelopmentCompatibilityConfig.from_dict(None)
        == DevelopmentCompatibilityConfig()
    )
    assert (
        DevelopmentCompatibilityConfig.from_dict({}) == DevelopmentCompatibilityConfig()
    )


def test_configuration_keys_and_invalid_types_are_rejected() -> None:
    with pytest.raises(ValueError, match="accepts no configuration keys"):
        DevelopmentCompatibilityConfig.from_dict({"unexpected": True})
    with pytest.raises(TypeError, match="must be a mapping"):
        DevelopmentCompatibilityConfig.from_dict([])  # type: ignore[arg-type]
