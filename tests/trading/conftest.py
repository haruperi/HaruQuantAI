"""Shared public builders for Trading unit and workflow-integration tests."""

# ruff: noqa: INP001

import pytest
from app.services.risk.contracts import KillSwitchState
from tests.trading.unit.actions.test_controls import switch as kill_switch
from tests.trading.unit.actions.test_dependencies import (
    NOW,
    MemoryStore,
    account_snapshot,
    symbol_capability,
)
from tests.trading.unit.actions.test_dependencies import (
    dependencies as trading_dependencies,
)
from tests.trading.unit.actions.test_dependencies import (
    policy as action_policy,
)
from tests.trading.unit.actions.test_dependencies import (
    request as trading_request,
)
from tests.trading.unit.actions.test_emergency import (
    emergency_dependencies,
    unknown_dispatch,
)
from tests.trading.unit.actions.test_rebalance import (
    allocation as rebalance_allocation,
)
from tests.trading.unit.actions.test_rebalance import (
    budget as rebalance_budget,
)
from tests.trading.unit.actions.test_rebalance import (
    rebalance_data,
    rebalance_dependencies,
    rebalance_request,
)
from tests.trading.unit.actions.test_runtime import (
    evaluation_dependencies,
    trade_intent,
)
from tests.trading.unit.actions.test_runtime import (
    evidence as evaluation_evidence,
)
from tests.trading.unit.actions.test_runtime import (
    risk_decision as evaluation_risk_decision,
)
from tests.trading.unit.live.test_gates import (
    _capability as live_adapter_capability,
)
from tests.trading.unit.live.test_gates import (
    _inactive_switch as _gate_inactive_switch,
)
from tests.trading.unit.live.test_gates import _policy as live_action_policy
from tests.trading.unit.live.test_gates import _request as live_gate_request
from tests.trading.unit.live.test_gates import _risk_decision as live_risk_decision
from tests.trading.unit.live.test_gates import _session as live_gate_session
from tests.trading.unit.live.test_session import _config as live_config
from tests.trading.unit.live.test_session import _evidence as live_evidence
from tests.trading.unit.live.test_session import _session as live_session
from tests.trading.unit.monitoring.test_budgets import (
    _allocation as monitoring_allocation,
)
from tests.trading.unit.monitoring.test_budgets import _request as monitoring_request
from tests.trading.unit.monitoring.test_budgets import _verdict as monitoring_verdict
from tests.trading.unit.reconciliation.test_authority import (
    _projection as authority_projection,
)
from tests.trading.unit.reconciliation.test_authority import (
    _receipt as authority_receipt,
)
from tests.trading.unit.reconciliation.test_authority import (
    _snapshot as authority_snapshot,
)
from tests.trading.unit.reconciliation.test_authority import _Store as AuthorityStore
from tests.trading.unit.reporting.test_evidence import ReportStore
from tests.trading.unit.routing.test_dispatcher import _Adapter as CountingAdapter
from tests.trading.unit.routing.test_dispatcher import (
    _connection as broker_connection,
)
from tests.trading.unit.validation.test_readiness import _request as readiness_request
from tests.trading.unit.validation.test_readiness import _risk as readiness_risk
from tests.trading.unit.validation.test_readiness import _snapshot as readiness_snapshot
from tests.trading.unit.validation.test_readiness import _switch as readiness_switch


def inactive_kill_switch() -> KillSwitchState:
    """Build inactive kill-switch evidence observed at the shared clock.

    The gate module's own builder is anchored to that module's clock. Shared
    fixtures must agree with the shared ``NOW`` so kill-switch evidence is
    current against the configured ``kill_switch`` staleness bound.
    """
    return _gate_inactive_switch().model_copy(update={"updated_at": NOW})


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


__all__ = [
    "NOW",
    "AuthorityStore",
    "CountingAdapter",
    "MemoryStore",
    "ReportStore",
    "account_snapshot",
    "action_policy",
    "anyio_backend",
    "authority_projection",
    "authority_receipt",
    "authority_snapshot",
    "broker_connection",
    "emergency_dependencies",
    "evaluation_dependencies",
    "evaluation_evidence",
    "evaluation_risk_decision",
    "inactive_kill_switch",
    "kill_switch",
    "live_action_policy",
    "live_adapter_capability",
    "live_config",
    "live_evidence",
    "live_gate_request",
    "live_gate_session",
    "live_risk_decision",
    "live_session",
    "monitoring_allocation",
    "monitoring_request",
    "monitoring_verdict",
    "readiness_request",
    "readiness_risk",
    "readiness_snapshot",
    "readiness_switch",
    "rebalance_allocation",
    "rebalance_budget",
    "rebalance_data",
    "rebalance_dependencies",
    "rebalance_request",
    "symbol_capability",
    "trade_intent",
    "trading_dependencies",
    "trading_request",
    "unknown_dispatch",
]
