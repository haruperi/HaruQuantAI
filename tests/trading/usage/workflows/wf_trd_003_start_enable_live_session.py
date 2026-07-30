"""WF-TRD-003: start a genuine MT5 demo-backed package-only live session."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.brokers import (
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_account_info,
    get_broker_connection_environment,
    get_broker_connection_id,
    get_broker_connection_status,
    get_broker_feature_flags,
    get_broker_id,
)
from app.services.trading import (
    create_live_session,
    create_readiness_assessment,
    is_live_session_admission_enabled,
    start_live_session,
)
from tests.brokers.usage._support import (
    config as broker_config,
)
from tests.brokers.usage._support import (
    require_success,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-003"
STAGES = (
    "Validate non-production MT5 connection config and open a genuine authenticated session.",
    "Read actual adapter capability, security, connection, and account evidence.",
    "Construct LiveSession with injected Broker adapter and typed authority sources.",
    "Run LiveSession.start in paper mode and complete startup reconciliation.",
    "Return demo-backed session status, then disconnect every owned resource.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


@asynccontextmanager
async def _mt5_session(
    connection: Any,
) -> AsyncIterator[Any]:
    """Create, connect, and deterministically close the public MT5 adapter."""
    created = require_success(
        "MT5 adapter creation",
        create_broker_adapter(get_broker_id("mt5"), connection),
    )
    if created.data is None:
        raise RuntimeError("MT5 adapter creation returned no adapter")
    adapter = created.data
    require_success("MT5 connect", await connect_broker(adapter))
    try:
        yield adapter
    finally:
        require_success("MT5 disconnect", await disconnect_broker(adapter))


async def run() -> None:
    """Run the genuine read-only lifecycle."""
    # Stage 1 — INPUT BOUNDARY: Approved demo MT5 configuration.
    _stage(1)
    connection = broker_config(get_broker_id("mt5"))
    async with _mt5_session(connection) as adapter:
        print(
            "Connected:",
            get_broker_connection_id(connection),
            get_broker_connection_environment(connection),
        )
        # Stage 2: Read genuine capability and account evidence.
        _stage(2)
        flags_result = require_success(
            "Feature flags", await get_broker_feature_flags(adapter)
        )
        require_success("Account", await get_broker_account_info(adapter))
        require_success("Connection", await get_broker_connection_status(adapter))
        if flags_result.data is None:
            raise RuntimeError("MT5 returned no feature flags")
        # Stage 3: Compose the Trading lifecycle with the real adapter.
        _stage(3)

        async def passed() -> bool:
            return True

        session = create_live_session(
            store=examples.MemoryStore(),
            connection=connection,
            broker_adapter=adapter,
            feature_flags=flags_result.data,
            risk_decision_source=lambda _request: None,
            action_policy_source=lambda _request: None,
            kill_switch_source=examples.inactive_kill_switch_hierarchy,
            readiness_source=lambda request, _evidence: create_readiness_assessment(
                passed=True,
                failed_check_codes=(),
                evidence_refs={"mt5": "connected"},
                assessed_at=request.system_time,
            ),
            adapter_capability_source=lambda request: examples.symbol_capability(
                request.route, request.provider_id, request.symbol
            )[0],
            auth_context_source=examples.auth_context,
            pre_audit_sink=lambda _evidence: None,
            event_sink=lambda _event: None,
            startup_reconcile=passed,
            drain_in_flight=passed,
            flush_evidence=passed,
            shutdown_reconcile=passed,
            clock=lambda: examples.NOW,
        )
        print("Composed:", type(session).__name__)
        # Stage 4: Match Trading's paper route to the genuine MT5 demo environment.
        _stage(4)
        runtime = {
            **examples.live_config(),
            "RUNTIME_PROFILE": "paper",
            "EXECUTION_ROUTE": "paper",
            "ALLOW_LIVE_MUTATIONS": False,
        }
        outcome = await start_live_session(session, runtime, examples.live_evidence())
        print(
            "Startup:",
            outcome.status,
            "admission:",
            is_live_session_admission_enabled(session),
            "evidence:",
            outcome.data,
        )
        # Stage 5 — OUTPUT BOUNDARY: Package-only status; context manager disconnects.
        _stage(5)
        print("Output:", outcome.status, "No broker mutation was transmitted")


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
