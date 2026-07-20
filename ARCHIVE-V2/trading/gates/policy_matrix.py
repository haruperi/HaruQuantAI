"""Trading gate policy matrix resolution primitives.

The policy matrix is the single injected source of permission, approval,
emergency, and side-effect ceiling rules consulted by the gate pipeline. If
an action has no configured entry, resolution fails closed with
``TRADING_POLICY_UNDEFINED`` (TRD-FR-089) rather than falling back to a
permissive default.
"""

from __future__ import annotations

from app.services.trading.contracts import (
    SideEffectMode,
    TradingAction,
    TradingContract,
)
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger
from pydantic import Field


class PolicyMatrixEntry(TradingContract):
    """Governed-action policy rule set.

    Attributes:
        action: Trading action this entry governs.
        requires_approval: Whether the action requires operator approval
            evidence before execution.
        requires_dual_approval: Whether the action requires two distinct
            authenticated operators' approval evidence.
        emergency_allowed_under_kill_switch: Whether this action may execute
            as an emergency/protective mutation while a kill switch is
            active.
        risk_increasing: Whether this action increases account/strategy risk
            exposure (used by the kill-switch gate).
        side_effect_ceiling: Maximum permitted side-effect mode for this
            action.
    """

    action: TradingAction
    requires_approval: bool = True
    requires_dual_approval: bool = False
    emergency_allowed_under_kill_switch: bool = False
    risk_increasing: bool = True
    side_effect_ceiling: SideEffectMode = SideEffectMode.BROKER_MUTATION_ATTEMPTED


class PolicyMatrix(TradingContract):
    """Injected registry of policy matrix entries keyed by action.

    Attributes:
        entries: Per-action policy rule sets.
    """

    entries: dict[TradingAction, PolicyMatrixEntry] = Field(default_factory=dict)


def resolve_policy(*, matrix: PolicyMatrix, action: TradingAction) -> PolicyMatrixEntry:
    """Resolve the policy matrix entry for a governed action (TRD-FR-089).

    Args:
        matrix: Injected policy matrix.
        action: Trading action to resolve.

    Returns:
        PolicyMatrixEntry: Resolved policy rule set.

    Raises:
        TradingMappedError: If no entry is defined for ``action``.
    """
    logger.info("Resolving policy matrix entry for action {}.", action.value)
    entry = matrix.entries.get(action)
    if entry is None:
        msg = f"No policy matrix entry is defined for action '{action.value}'."
        raise TradingMappedError(
            msg,
            code="TRADING_POLICY_UNDEFINED",
            details={"action": action.value},
        )
    logger.debug("Resolved policy matrix entry for {}.", action.value)
    return entry
