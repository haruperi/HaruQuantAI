"""Authority and retry guard for state reconciliation.

Enforces mutation blocks on unresolved timeouts or event stream gaps,
and exposes the gate step evaluator.
"""

from __future__ import annotations

from app.services.trading.gates._common import (
    GateName,
    GateStepResult,
    blocked_step,
    passed_step,
)
from app.utils.logger import logger


class AuthorityAndRetryGuard:
    """Tracks unresolved authority scopes, stream gaps, and duplicate events."""

    def __init__(self) -> None:
        """Initialize the authority guard."""
        logger.info("Initializing AuthorityAndRetryGuard.")
        self._unresolved_scopes: dict[tuple[str, str], str] = {}
        self._stream_gaps: set[tuple[str, str]] = set()
        self._seen_event_ids: set[str] = set()
        self.duplicate_count: int = 0

    def transition_to_unresolved(
        self, account_id: str, symbol: str | None, request_id: str
    ) -> None:
        """Transition a scope to UNRESOLVED status due to an unknown outcome.

        Args:
            account_id: Account identifier.
            symbol: Symbol identifier (or None for account-wide block).
            request_id: Request identifier causing the timeout or gap.
        """
        sym = symbol or "*"
        logger.warning(
            "Scope ({}, {}) marked UNRESOLVED due to request {}.",
            account_id,
            sym,
            request_id,
        )
        self._unresolved_scopes[(account_id, sym)] = request_id

    def resolve_scope(self, account_id: str, symbol: str | None) -> None:
        """Resolve a previously blocked scope.

        Args:
            account_id: Account identifier.
            symbol: Symbol identifier (or None for account-wide resolution).
        """
        sym = symbol or "*"
        logger.info("Resolving blocked scope ({}, {}).", account_id, sym)
        self._unresolved_scopes.pop((account_id, sym), None)
        self._stream_gaps.discard((account_id, sym))
        if sym == "*":
            # If resolving account-wide, clean up symbol-specific stream gaps
            to_remove = [k for k in self._unresolved_scopes if k[0] == account_id]
            for k in to_remove:
                self._unresolved_scopes.pop(k, None)
            to_remove_gaps = [k for k in self._stream_gaps if k[0] == account_id]
            for k in to_remove_gaps:
                self._stream_gaps.discard(k)

    def is_blocked(self, account_id: str, symbol: str) -> bool:
        """Return whether mutations are blocked for the given scope.

        Args:
            account_id: Account identifier.
            symbol: Symbol identifier.

        Returns:
            bool: True if mutations are blocked.
        """
        # Check account-wide blocks
        if (account_id, "*") in self._unresolved_scopes:
            logger.warning("Mutation blocked: Account-wide block is active.")
            return True
        if (account_id, "*") in self._stream_gaps:
            logger.warning("Mutation blocked: Account-wide stream gap is active.")
            return True

        # Check symbol-specific blocks
        if (account_id, symbol) in self._unresolved_scopes:
            logger.warning("Mutation blocked: Symbol {} is unresolved.", symbol)
            return True
        if (account_id, symbol) in self._stream_gaps:
            logger.warning("Mutation blocked: Symbol {} has a stream gap.", symbol)
            return True

        return False

    def report_stream_gap(self, account_id: str, symbol: str | None) -> None:
        """Report a stream-gap incident, immediately halting mutations.

        Args:
            account_id: Account identifier.
            symbol: Symbol identifier (or None for account-wide gap).
        """
        sym = symbol or "*"
        logger.critical("Stream gap reported for scope ({}, {}).", account_id, sym)
        self._stream_gaps.add((account_id, sym))

    def process_event_id(self, broker_event_id: str) -> bool:
        """Record event ID and return whether it is a duplicate.

        Args:
            broker_event_id: Unique broker event ID.

        Returns:
            bool: True if the event was already seen.
        """
        if not broker_event_id:
            return False
        if broker_event_id in self._seen_event_ids:
            self.duplicate_count += 1
            logger.info(
                "Duplicate broker event ID {} ignored (total duplicates={}).",
                broker_event_id,
                self.duplicate_count,
            )
            return True
        self._seen_event_ids.add(broker_event_id)
        return False


def evaluate_reconciliation_authority_gate(
    *,
    guard: AuthorityAndRetryGuard,
    account_id: str,
    symbol: str,
) -> GateStepResult:
    """Evaluate the reconciliation authority gate step (Gate 13).

    Args:
        guard: Authority guard.
        account_id: Request account ID.
        symbol: Request symbol.

    Returns:
        GateStepResult: Gate step evaluation outcome.
    """
    logger.info("Evaluating reconciliation authority gate for symbol {}.", symbol)
    if guard.is_blocked(account_id, symbol):
        logger.warning(
            "Reconciliation authority gate blocked: scope {}:{} has locks.",
            account_id,
            symbol,
        )
        return blocked_step(
            gate=GateName.RECONCILIATION_AUTHORITY,
            reason_code="RECONCILIATION_REQUIRED",
            message=f"Scope {account_id}:{symbol} has active unresolved locks.",
        )
    logger.debug("Reconciliation authority gate passed for {}.", symbol)
    return passed_step(gate=GateName.RECONCILIATION_AUTHORITY)
