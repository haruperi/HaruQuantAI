"""Explicit isolated non-canonical fast-research execution."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.simulator.errors import SimulationError
from app.services.simulator.reporting import FastResearchResult
from app.services.simulator.run.audit import emit_simulation_audit
from app.services.simulator.run.orchestrator import _canonical_hash, _validate_auth
from app.services.simulator.timeline import build_tick_timeline
from app.services.simulator.validation import (
    validate_phase_one_scope,
    validate_run_inputs,
)
from app.utils import AuthContext, logger

if TYPE_CHECKING:
    from app.services.simulator.run.contracts import (
        SimulationBacktestRequestV1,
        SimulationRunDependencies,
    )


def _run_fast_research(
    request: SimulationBacktestRequestV1,
    auth_context: AuthContext,
    dependencies: SimulationRunDependencies,
) -> FastResearchResult:
    """Run one explicitly enabled approximation without canonical evidence.

    Args:
        request: Explicit ``fast_research`` non-canonical request.
        auth_context: Authenticated matching trace context.
        dependencies: Read-only Data/Indicator composition and feature flag.

    Returns:
        Disclosed non-canonical approximation.

    Raises:
        SimulationError: If disabled, unsupported, or evidence is unavailable.
    """
    logger.info("Starting non-canonical fast research %s", request.request_id)
    _validate_auth(request, auth_context)
    payload = request.model_dump(mode="python", warnings=False)
    validate_run_inputs(payload)
    validate_phase_one_scope(payload)
    if request.runtime_profile != "fast_research" or request.canonical:
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION", "Request is not fast research"
        )
    if not dependencies.fast_research_enabled:
        raise SimulationError("SIM_UNSUPPORTED_OPERATION", "Fast research is disabled")
    source = dependencies.load_market_data(request)
    tick_dataset = dependencies.generate_tick_series(source, request)
    timeline = build_tick_timeline(tick_dataset)
    if not timeline:
        raise SimulationError(
            "SIM_DATA_COVERAGE_INSUFFICIENT", "Research timeline is empty"
        )
    observations: list[Decimal] = []
    previous_mid: Decimal | None = None
    for tick in timeline:
        mid = (tick.bid + tick.ask) / Decimal(2)
        if previous_mid is not None:
            observations.append((mid - previous_mid) / previous_mid)
        previous_mid = mid
    return FastResearchResult(
        request_hash=_canonical_hash(payload),
        config_hash=request.config_hash,
        data_hash=request.data_hash,
        observations=tuple(observations),
        assumptions=("Mid-quote changes are an approximate research observation.",),
        limitations=(
            "No fills, closed trades, journal, canonical report, "
            "or promotion evidence.",
        ),
        generated_at=timeline[-1].timestamp,
    )


def run_fast_research(
    request: SimulationBacktestRequestV1,
    auth_context: AuthContext,
    dependencies: SimulationRunDependencies,
) -> FastResearchResult:
    """Run and audit one explicitly non-canonical approximation.

    Args:
        request: Explicit ``fast_research`` non-canonical request.
        auth_context: Authenticated matching trace context.
        dependencies: Read-only composition and audit persistence.

    Returns:
        Disclosed non-canonical approximation.

    Raises:
        SimulationError: If validation, audit, or execution fails.
    """
    emit_simulation_audit(
        dependencies,
        auth_context,
        "simulation.research_started",
        request.start,
        {"config_hash": request.config_hash},
    )
    try:
        result = _run_fast_research(request, auth_context, dependencies)
    except Exception:
        emit_simulation_audit(
            dependencies,
            auth_context,
            "simulation.research_failed",
            request.end,
            {"config_hash": request.config_hash},
        )
        raise
    emit_simulation_audit(
        dependencies,
        auth_context,
        "simulation.research_completed",
        result.generated_at,
        {"request_hash": result.request_hash},
    )
    return result


__all__ = ["run_fast_research"]
