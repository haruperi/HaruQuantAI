"""Composition adapter for current-state Risk governance."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import cast

from app.services.data import build_market_context_evidence
from app.services.risk.contracts import (
    create_kill_switch_state,
    create_portfolio_risk_snapshot,
    create_regime_assessment,
)
from app.services.risk.governor.orchestration import (
    RiskGovernor,
    run_portfolio_risk_governor,
)


def _mapping(body: Mapping[str, object], field: str) -> Mapping[str, object]:
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


def build_governance_runtime_operation(
    *,
    governor: RiskGovernor,
    clock: Callable[[], datetime],
) -> Callable[[dict[str, object], object], object]:
    """Build the API-compatible current-state governor operation.

    Returns:
        Callable that delegates complete typed evidence to Risk.
    """

    def _operation(body: dict[str, object], auth: object) -> object:
        """Delegate one governance evaluation to the authoritative governor.

        Returns:
            The authoritative current-state risk decision.

        Raises:
            TypeError: If kill-switch evidence is not structured data.
        """
        raw_states = body.get("kill_switch_states", ())
        if not isinstance(raw_states, list | tuple):
            raise TypeError("kill_switch_states must be an array")
        states = tuple(
            create_kill_switch_state(**cast("Mapping[str, object]", item))
            for item in raw_states
            if isinstance(item, Mapping)
        )
        if len(states) != len(raw_states):
            raise TypeError("kill_switch_states entries must be objects")
        return run_portfolio_risk_governor(
            governor,
            create_portfolio_risk_snapshot(**_mapping(body, "snapshot")),
            build_market_context_evidence(**_mapping(body, "market_context")),
            create_regime_assessment(**_mapping(body, "regime")),
            states,
            auth,
            now=clock(),
        )

    return _operation


__all__ = ("build_governance_runtime_operation",)
