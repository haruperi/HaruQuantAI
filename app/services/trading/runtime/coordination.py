"""Concurrency lock and strategy ownership coordination services.

Implements TRD-FR-073 through TRD-FR-076.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.contracts import JsonObject


class ConcurrencyLockManager:
    """Manages optimistic concurrency locks per (account_id, symbol)."""

    def __init__(self, max_queue_capacity: int = 10) -> None:
        """Initialize the lock manager.

        Args:
            max_queue_capacity: Max queue count before triggering backpressure.
        """
        self.max_queue_capacity = max_queue_capacity
        self._locks: dict[tuple[str, str], threading.Lock] = {}
        self._queues: dict[tuple[str, str], int] = {}
        self._manager_lock = threading.Lock()

    def acquire_lock(self, account_id: str, symbol: str, timeout: float = 1.0) -> bool:
        """Acquire a concurrency lock with timeout and queue-based backpressure.

        Tracked requirements: TRD-FR-073, TRD-FR-074.

        Args:
            account_id: Account identifier.
            symbol: Financial instrument symbol.
            timeout: Timeout for lock acquisition in seconds.

        Returns:
            bool: True if lock acquired successfully.

        Raises:
            TradingValidationError: If queue capacity is exceeded.
        """
        key = (account_id, symbol)

        with self._manager_lock:
            # Check queue capacity limits
            current_queue = self._queues.get(key, 0)
            if current_queue >= self.max_queue_capacity:
                logger.warning(
                    "Request queue capacity exceeded for key {}. "
                    "Triggering backpressure.",
                    key,
                )
                msg = f"Request queue capacity exceeded for {account_id}:{symbol}."
                raise TradingValidationError(msg)

            # Increment queue count
            self._queues[key] = current_queue + 1

            # Get or create the underlying lock
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            lock = self._locks[key]

        # Attempt to acquire lock with timeout
        start_time = time.monotonic()
        acquired = False
        while (time.monotonic() - start_time) < timeout:
            if lock.acquire(blocking=False):
                acquired = True
                break
            time.sleep(0.01)

        # Decrement queue count
        with self._manager_lock:
            self._queues[key] = max(0, self._queues[key] - 1)
            if not acquired and self._queues[key] == 0:
                # Clean up lock reference if unused
                self._locks.pop(key, None)

        if not acquired:
            logger.error("Lock acquisition timed out for key {}.", key)
            return False

        logger.debug("Lock acquired successfully for key {}.", key)
        return True

    def release_lock(self, account_id: str, symbol: str) -> None:
        """Release the concurrency lock for (account_id, symbol)."""
        key = (account_id, symbol)
        with self._manager_lock:
            lock = self._locks.get(key)
            if lock is not None:
                try:
                    lock.release()
                    logger.debug("Lock released successfully for key {}.", key)
                except RuntimeError:
                    # Lock was not acquired by this thread
                    pass
                if self._queues.get(key, 0) == 0:
                    self._locks.pop(key, None)


class StrategyOwnershipValidator:
    """Enforces strategy ownership constraints on orders and positions."""

    @staticmethod
    def validate_ownership(
        *,
        record_strategy_id: str,
        request_strategy_id: str,
        policy_matrix: object = None,
    ) -> None:
        """Verify strategy ownership constraints (TRD-FR-075).

        A strategy cannot close or modify another strategy's positions unless
        explicitly authorized by the policy matrix.
        """
        if record_strategy_id == request_strategy_id:
            return

        # Check policy matrix override permission
        authorized = False
        if policy_matrix is not None and hasattr(policy_matrix, "is_authorized"):
            # We check authorization on the untyped object
            auth_fn = policy_matrix.is_authorized
            authorized = auth_fn(
                request_strategy_id=request_strategy_id,
                record_strategy_id=record_strategy_id,
                action="cross_strategy_mutation",
            )

        if not authorized:
            logger.error(
                "Cross-strategy ownership violation: strategy {} attempted to modify "
                "record owned by strategy {}.",
                request_strategy_id,
                record_strategy_id,
            )
            msg = (
                f"Cross-strategy mutation not permitted by ownership constraints: "
                f"Strategy '{request_strategy_id}' cannot mutate record of "
                f"'{record_strategy_id}'."
            )
            raise TradingValidationError(msg)


class CrossStrategyPolicyEvaluator:
    """Detects and resolves opposing orders/positions across strategies."""

    @staticmethod
    def _has_conflict(
        is_buy_mutation: bool,
        records: list[JsonObject],
        side_key: str,
        request_strategy_id: str,
        conflicting_strategies: set[str],
    ) -> bool:
        """Helper to scan records and check direction conflicts."""
        has_conflict = False
        for rec in records:
            owner = rec.get("owner_strategy_id")
            if owner == request_strategy_id:
                continue

            side = str(rec.get(side_key, "")).lower()
            is_opposing = (is_buy_mutation and "sell" in side) or (
                not is_buy_mutation and "buy" in side
            )
            if is_opposing:
                has_conflict = True
                if isinstance(owner, str):
                    conflicting_strategies.add(owner)
        return has_conflict

    @staticmethod
    def detect_opposing_orders_or_positions(
        *,
        request_strategy_id: str,
        account_id: str,
        symbol: str,
        request_side: str,
        working_orders: list[JsonObject],
        active_positions: list[JsonObject],
        policy_matrix: object = None,
    ) -> str:
        """Detect when strategy A mutations oppose strategy B working orders/positions.

        Tracked requirements: TRD-FR-076.
        """
        req_direction = request_side.lower()
        is_buy_mutation = "buy" in req_direction
        conflicting_strategies: set[str] = set()

        order_conflict = CrossStrategyPolicyEvaluator._has_conflict(
            is_buy_mutation,
            working_orders,
            "side",
            request_strategy_id,
            conflicting_strategies,
        )

        pos_conflict = CrossStrategyPolicyEvaluator._has_conflict(
            is_buy_mutation,
            active_positions,
            "type",
            request_strategy_id,
            conflicting_strategies,
        )

        if not order_conflict and not pos_conflict:
            return "allow"

        # Lookup policy matrix for action
        policy_action = "block"
        if policy_matrix is not None and hasattr(policy_matrix, "get_cross_policy"):
            get_policy_fn = policy_matrix.get_cross_policy
            policy_action = get_policy_fn(
                account_id=account_id,
                symbol=symbol,
                request_strategy_id=request_strategy_id,
                conflicting_strategies=list(conflicting_strategies),
            )

        # Journal / Log the detection
        logger.warning(
            "Cross-strategy opposing order/position detected on {}:{}. "
            "Request strategy: {}, opposing strategies: {}. Policy action: {}.",
            account_id,
            symbol,
            request_strategy_id,
            conflicting_strategies,
            policy_action,
        )

        return policy_action


# Export a global instance helper
concurrency_lock_manager = ConcurrencyLockManager()
