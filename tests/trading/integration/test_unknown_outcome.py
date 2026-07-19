"""Workflow integration for uncertain authority outcomes."""

# ruff: noqa: ARG005, INP001

from app.services.trading.reconciliation import resolve_unknown_outcome
from tests.trading.conftest import (
    AuthorityStore,
    authority_projection,
    authority_receipt,
    authority_snapshot,
)


def test_unknown_outcome_blocks_retry() -> None:
    """An unresolved authority comparison retains the retry lock."""
    store = AuthorityStore(
        authority_projection(orders={"order-internal": {"state": "pending"}})
    )
    result = resolve_unknown_outcome(
        authority_receipt(), store, lambda route: authority_snapshot()
    )
    assert result.transition == "retry_locked"
    assert not result.retry_allowed
