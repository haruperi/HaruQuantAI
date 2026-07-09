"""Unit tests for the concurrency and coordination runtime module."""

from __future__ import annotations

import threading
import time

import pytest
from app.services.trading.runtime.coordination import (
    ConcurrencyLockManager,
    CrossStrategyPolicyEvaluator,
    StrategyOwnershipValidator,
)
from app.services.trading.security.error_mapping import TradingValidationError


class MockPolicyMatrix:
    """Mock policy matrix for testing permissions."""

    def __init__(
        self, cross_authorized: bool = False, cross_policy: str = "block"
    ) -> None:
        self.cross_authorized = cross_authorized
        self.cross_policy = cross_policy
        self.is_authorized_called = 0
        self.get_cross_policy_called = 0

    def is_authorized(
        self,
        request_strategy_id: str,
        record_strategy_id: str,
        action: str,
    ) -> bool:
        self.is_authorized_called += 1
        return self.cross_authorized

    def get_cross_policy(
        self,
        account_id: str,
        symbol: str,
        request_strategy_id: str,
        conflicting_strategies: list[str],
    ) -> str:
        self.get_cross_policy_called += 1
        return self.cross_policy


def test_lock_acquisition_success_and_release() -> None:
    """Verify lock manager acquires and releases locks correctly."""
    mgr = ConcurrencyLockManager()

    # Acquire lock on (acct-1, EURUSD)
    assert mgr.acquire_lock("acct-1", "EURUSD", timeout=0.1)

    # Second acquisition on same key fails
    assert not mgr.acquire_lock("acct-1", "EURUSD", timeout=0.05)

    # Acquisition on different key succeeds
    assert mgr.acquire_lock("acct-1", "GBPUSD", timeout=0.1)

    # Release first lock
    mgr.release_lock("acct-1", "EURUSD")

    # Now first lock can be acquired
    assert mgr.acquire_lock("acct-1", "EURUSD", timeout=0.1)

    # Cleanup releases
    mgr.release_lock("acct-1", "EURUSD")
    mgr.release_lock("acct-1", "GBPUSD")


def test_lock_acquisition_backpressure() -> None:
    """Exceeding max queue capacity triggers immediate backpressure validation error (TRD-FR-074)."""
    mgr = ConcurrencyLockManager(max_queue_capacity=2)

    # Hold lock 1
    assert mgr.acquire_lock("acct-1", "EURUSD", timeout=0.1)

    # Thread to block queue
    def block_queue() -> None:
        mgr.acquire_lock("acct-1", "EURUSD", timeout=0.5)

    t1 = threading.Thread(target=block_queue)
    t1.start()

    # Give thread time to increment queue count
    time.sleep(0.05)

    # Now queue count is 1. Next request will be queue count 2 (allowed up to 2).
    # Thread 2 to exceed limit
    t2 = threading.Thread(target=block_queue)
    t2.start()
    time.sleep(0.05)

    # Queue count is now 2. Next request must trigger backpressure immediately
    with pytest.raises(TradingValidationError, match="queue capacity exceeded"):
        mgr.acquire_lock("acct-1", "EURUSD", timeout=0.1)

    t1.join()
    t2.join()
    mgr.release_lock("acct-1", "EURUSD")


def test_strategy_ownership_validation() -> None:
    """Ownership validator restricts cross-strategy mutations (TRD-FR-075)."""
    val = StrategyOwnershipValidator()

    # Same strategy is allowed
    val.validate_ownership(
        record_strategy_id="strat-1",
        request_strategy_id="strat-1",
    )

    # Different strategy without policy -> Blocked
    with pytest.raises(TradingValidationError, match="ownership constraints"):
        val.validate_ownership(
            record_strategy_id="strat-1",
            request_strategy_id="strat-2",
        )

    # Different strategy with authorization policy -> Allowed
    policy = MockPolicyMatrix(cross_authorized=True)
    val.validate_ownership(
        record_strategy_id="strat-1",
        request_strategy_id="strat-2",
        policy_matrix=policy,
    )
    assert policy.is_authorized_called == 1


def test_opposing_orders_or_positions_detection() -> None:
    """CrossStrategyPolicyEvaluator detects opposing orders/positions and applies policy (TRD-FR-076)."""
    evaluator = CrossStrategyPolicyEvaluator()

    working_orders = [
        {
            "owner_strategy_id": "strat-2",
            "side": "sell",
        }
    ]
    active_positions = [
        {
            "owner_strategy_id": "strat-3",
            "type": "sell",
        }
    ]

    # No conflict: request is sell, opposing are sell
    action = evaluator.detect_opposing_orders_or_positions(
        request_strategy_id="strat-1",
        account_id="acct-1",
        symbol="EURUSD",
        request_side="sell",
        working_orders=working_orders,
        active_positions=active_positions,
    )
    assert action == "allow"

    # Conflict: request is buy (opposing sell orders/positions present)
    # 1. No policy matrix -> Default to block
    action = evaluator.detect_opposing_orders_or_positions(
        request_strategy_id="strat-1",
        account_id="acct-1",
        symbol="EURUSD",
        request_side="buy",
        working_orders=working_orders,
        active_positions=active_positions,
    )
    assert action == "block"

    # 2. Policy matrix resolves custom action (e.g. warn_and_allow)
    policy = MockPolicyMatrix(cross_policy="warn_and_allow")
    action = evaluator.detect_opposing_orders_or_positions(
        request_strategy_id="strat-1",
        account_id="acct-1",
        symbol="EURUSD",
        request_side="buy",
        working_orders=working_orders,
        active_positions=active_positions,
        policy_matrix=policy,
    )
    assert action == "warn_and_allow"
    assert policy.get_cross_policy_called == 1
