"""Unit tests for discretionary strategy module and registration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.services.strategy.discretionary import module as disc_module
from app.services.strategy.discretionary.registration import (
    _manifest,
    _policy,
    get_discretionary_strategy_id,
    register_discretionary_strategy,
    strategy_version_for,
)


def test_discretionary_module_and_id() -> None:
    """Verify discretionary module import and strategy identity functions."""
    assert disc_module.__all__ == []
    assert get_discretionary_strategy_id() == "discretionary-manual-order"
    assert strategy_version_for("SIMULATION") == "1.0.0-simulation"
    assert strategy_version_for("DEMO") == "1.0.0-demo"
    assert strategy_version_for("LIVE") == "1.0.0-live"


def test_discretionary_manifest_and_policy() -> None:
    """Verify _manifest and _policy builders."""
    man = _manifest("SIMULATION")
    assert man.strategy_id == "discretionary-manual-order"
    assert man.strategy_version == "1.0.0-simulation"

    pol = _policy()
    assert pol.policy_version == "discretionary-v1"


def test_register_discretionary_strategy_success() -> None:
    """Verify register_discretionary_strategy handles successful registrations."""
    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.data.status = "ACCEPTED"

    auth = MagicMock()
    with patch(
        "app.services.strategy.discretionary.registration.register_strategy_version",
        return_value=mock_result,
    ):
        results = register_discretionary_strategy(auth)
        assert len(results) == 3


def test_register_discretionary_strategy_envelope_failure() -> None:
    """Verify register_discretionary_strategy raises on envelope failure."""
    mock_result = MagicMock()
    mock_result.status = "error"
    mock_result.data = None
    mock_result.error = "INVALID_AUTH"

    auth = MagicMock()
    with (
        patch(
            "app.services.strategy.discretionary.registration.register_strategy_version",
            return_value=mock_result,
        ),
        pytest.raises(RuntimeError, match="discretionary strategy registration failed"),
    ):
        register_discretionary_strategy(auth)


def test_register_discretionary_strategy_rejection_failure() -> None:
    """Verify register_discretionary_strategy raises on mutation rejection."""
    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.data.status = "REJECTED"
    mock_result.data.reason_codes = ["UNAUTHORIZED"]

    auth = MagicMock()
    with (
        patch(
            "app.services.strategy.discretionary.registration.register_strategy_version",
            return_value=mock_result,
        ),
        pytest.raises(
            RuntimeError, match="discretionary strategy registration rejected"
        ),
    ):
        register_discretionary_strategy(auth)


def test_register_discretionary_strategy_already_exists_allowed() -> None:
    """Verify register_discretionary_strategy allows IMMUTABLE_VERSION_EXISTS rejection."""
    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.data.status = "REJECTED"
    mock_result.data.reason_codes = ["IMMUTABLE_VERSION_EXISTS"]

    auth = MagicMock()
    with patch(
        "app.services.strategy.discretionary.registration.register_strategy_version",
        return_value=mock_result,
    ):
        results = register_discretionary_strategy(auth)
        assert len(results) == 3
