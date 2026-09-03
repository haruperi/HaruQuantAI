"""Unit tests for operate-trading configuration."""

import pytest
from app.services.interfaces.operate_trading.config import from_dict


def test_default_config() -> None:
    """Verify defaults are applied correctly."""
    config = from_dict(None)
    assert config.default_account_id == "default"
    assert config.max_order_quantity == 1000.0


def test_custom_valid_config() -> None:
    """Verify custom valid configuration parses."""
    config = from_dict({"default_account_id": "acc-123", "max_order_quantity": 50.0})
    assert config.default_account_id == "acc-123"
    assert config.max_order_quantity == 50.0


def test_unknown_key_rejected() -> None:
    """Verify unknown keys raise ValueError."""
    with pytest.raises(ValueError, match="Unknown operate-trading configuration keys"):
        from_dict({"unknown_key": "val"})


def test_invalid_types_rejected() -> None:
    """Verify invalid types raise TypeError."""
    with pytest.raises(
        TypeError, match="default_account_id must be a non-empty string"
    ):
        from_dict({"default_account_id": 123})
    with pytest.raises(TypeError, match="max_order_quantity must be a number"):
        from_dict({"max_order_quantity": "not-a-num"})
