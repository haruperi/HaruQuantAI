"""Composition adapter for the stateful Risk allocation boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import TYPE_CHECKING, cast

from app.services.data import build_market_context_evidence
from app.services.risk.allocation.budget import review_allocation_proposal
from app.services.risk.config import create_risk_config
from app.services.risk.contracts import (
    create_allocation_review_request,
    create_portfolio_risk_snapshot,
)

if TYPE_CHECKING:
    from app.services.risk.audit.chain import RiskAuditChain
    from app.services.risk.audit.storage import _AllocationDecisionStore

type _Body = Mapping[str, object]


def _mapping(body: _Body, field: str) -> Mapping[str, object]:
    """Read one required nested request object.

    Returns:
        Validated nested mapping.

    Raises:
        TypeError: If the field is not an object.
    """
    value = body.get(field)
    if not isinstance(value, Mapping):
        message = f"{field} must be an object"
        raise TypeError(message)
    return cast("Mapping[str, object]", value)


def build_allocation_runtime_operation(
    *,
    store: _AllocationDecisionStore,
    audit: RiskAuditChain,
    clock: Callable[[], datetime],
) -> Callable[[dict[str, object], object], object]:
    """Build the API-compatible allocation operation over Risk-owned state.

    Returns:
        Callable that validates boundary fields and delegates to Risk.
    """

    def _operation(body: dict[str, object], _auth: object) -> object:
        """Delegate one allocation review to the authoritative Risk function.

        Returns:
            The authoritative allocation risk decision.
        """
        return review_allocation_proposal(
            create_allocation_review_request(**_mapping(body, "request")),
            create_portfolio_risk_snapshot(**_mapping(body, "snapshot")),
            build_market_context_evidence(**_mapping(body, "market_context")),
            create_risk_config(**_mapping(body, "config")),
            store,
            audit,
            now=clock(),
        )

    return _operation


__all__ = ("build_allocation_runtime_operation",)
