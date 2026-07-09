"""Unit tests for gate policy matrix resolution."""

from __future__ import annotations

import pytest
from app.services.trading.contracts import TradingAction
from app.services.trading.gates.policy_matrix import (
    PolicyMatrix,
    PolicyMatrixEntry,
    resolve_policy,
)
from app.services.trading.security.error_mapping import TradingMappedError


def test_resolve_policy_returns_defined_entry() -> None:
    """resolve_policy returns the configured entry for a defined action."""
    entry = PolicyMatrixEntry(action=TradingAction.SUBMIT_ORDER)
    matrix = PolicyMatrix(entries={TradingAction.SUBMIT_ORDER: entry})
    resolved = resolve_policy(matrix=matrix, action=TradingAction.SUBMIT_ORDER)
    assert resolved is entry


def test_resolve_policy_fails_closed_when_undefined() -> None:
    """resolve_policy fails closed with TRADING_POLICY_UNDEFINED when missing."""
    matrix = PolicyMatrix(entries={})
    with pytest.raises(TradingMappedError) as exc_info:
        resolve_policy(matrix=matrix, action=TradingAction.CANCEL_ORDER)
    assert exc_info.value.code == "TRADING_POLICY_UNDEFINED"
