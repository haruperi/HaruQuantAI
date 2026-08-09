# ruff: noqa: DOC201
"""Fail-closed reconciliation across durable and process-local execution state."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from app.services.trading.reconciliation.compare import compare_authority_state

if TYPE_CHECKING:
    from app.services.trading.reconciliation.snapshots import AuthoritySnapshot
    from app.services.trading.state.projections import TradingProjection


def reconcile_execution_state(
    authority: object, projection: object, *, positions: Mapping[str, Any]
) -> object:
    """Compare complete known Trading state with route-authority evidence."""
    return compare_authority_state(
        cast("AuthoritySnapshot", authority),
        cast("TradingProjection", projection),
        positions,
    )


__all__ = ["reconcile_execution_state"]
