"""Official synchronous governed Simulation backtest orchestration."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pydantic import ValidationError

from app.services.simulator.accounting import AccountLedger
from app.services.simulator.errors import SimulationError, unwrap_simulation_response
from app.services.simulator.execution import EventDrivenExecutionEngine
from app.services.simulator.journal import JournalWriter, resolve_idempotent_run
from app.services.simulator.reporting import (
    AccountingSummary,
    ClosedTradeRecord,
    RealismDisclosure,
    SimulationResult,
    build_artifact_manifest,
    build_json_report,
    build_markdown_report,
)
from app.services.simulator.run.audit import emit_simulation_audit
from app.services.simulator.timeline import APPROVED_TICK_MODELS, build_tick_timeline
from app.services.simulator.validation import (
    validate_market_data,
    validate_phase_one_scope,
    validate_run_inputs,
)
from app.services.simulator.validation.contracts import MarketDataValidationContext
from app.services.trading import create_execution_receipt, is_execution_receipt
from app.utils import canonical_digest, canonical_json, get_logger

type AuthContext = Any
ExecutionReceipt = Any
OrderIntent = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.simulator.run.contracts import (
        SimulationBacktestRequestV1,
        SimulationRunDependencies,
    )
    from app.services.simulator.timeline import Tick

_ENGINE_VERSION = "simulation-engine-v1"


def _canonical_hash(value: object) -> str:
    """Hash one deterministic JSON-safe value.

    Args:
        value: Value to identify.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing canonical Simulation orchestration material")
    return canonical_digest(value)


def _validate_auth(request: SimulationBacktestRequestV1, auth: AuthContext) -> None:
    """Validate authentication trace and simulation scope.

    Args:
        request: Governed Simulation request.
        auth: Authenticated principal context.

    Raises:
        SimulationError: If trace identity or permission is incompatible.
    """
    logger.info("Validating authentication for Simulation run")
    if (
        request.request_id != auth.request_id
        or request.workflow_id != auth.workflow_id
        or request.correlation_id != auth.correlation_id
    ):
        raise SimulationError(
            "SIM_INVALID_CONFIG", "Authentication trace does not match request"
        )
    if "simulation:run" not in auth.scopes and "simulation:run" not in auth.permissions:
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION", "Principal cannot run simulations"
        )


def _write_completed_text(path: Path, text: str) -> None:
    """Durably write one completed canonical text artifact.

    Args:
        path: Final approved artifact path.
        text: Complete artifact text.

    Raises:
        SimulationError: If writing or synchronization fails.
    """
    logger.info("Writing completed Simulation artifact %s", path.name)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except OSError as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Artifact write failed"
        ) from error


def _completed_result(
    request: SimulationBacktestRequestV1,
    request_hash: str,
    run_id: str,
    journal_ref: str,
    receipts: tuple[object, ...],
    ledger: AccountLedger,
    closed_trades: tuple[ClosedTradeRecord, ...],
    profile_slippage: str,
    profile_liquidity: str,
    tick_model: str,
) -> SimulationResult:
    """Construct the immutable completed result envelope.

    Every monetary field is read from the completed ledger; none is a constant.

    Args:
        request: Canonical run request.
        request_hash: Full request identity.
        run_id: Stable run identity.
        journal_ref: Finalized journal reference.
        receipts: Trading-owned execution receipts.
        ledger: Completed authoritative account ledger.
        closed_trades: Ordered engine-observed closed-trade ledger.
        profile_slippage: Disclosed slippage model.
        profile_liquidity: Disclosed liquidity model.
        tick_model: Data-owned tick model.

    Returns:
        Validated completed Simulation result.

    Raises:
        SimulationError: If the published accounting identity does not hold.
    """
    logger.info("Constructing completed SimulationResult for %s", run_id)
    typed_receipts = tuple(item for item in receipts if is_execution_receipt(item))
    snapshot = unwrap_simulation_response(
        ledger.snapshot(), operation="simulation.run.ledger_snapshot"
    )
    final_balance = Decimal(str(snapshot["balance"]))
    used_margin = Decimal(str(snapshot["used_margin"]))
    free_margin = Decimal(str(snapshot["free_margin"]))
    commission = Decimal(str(snapshot["commission"]))
    swap = Decimal(str(snapshot["swap"]))
    gross_profit = Decimal(str(snapshot["gross_profit"]))
    net_profit = gross_profit + commission + swap
    if net_profit != final_balance - request.initial_balance:
        raise SimulationError(
            "SIM_ACCOUNT_INVARIANT_BROKEN",
            "Published accounting does not reconcile with the ledger balance",
        )
    accounting = AccountingSummary(
        final_balance=final_balance,
        final_equity=Decimal(str(snapshot["equity"])),
        used_margin=used_margin,
        free_margin=free_margin,
        gross_profit=gross_profit,
        commission=commission,
        swap=swap,
        net_profit=net_profit,
    )
    return SimulationResult(
        run_id=run_id,
        request_hash=request_hash,
        config_hash=request.config_hash,
        data_hash=request.data_hash,
        engine_version=_ENGINE_VERSION,
        status="completed",
        journal_ref=journal_ref,
        artifact_manifest_ref=f"{run_id}/manifest.json",
        fills=typed_receipts,
        closed_trades=closed_trades,
        initial_balance=request.initial_balance,
        account_currency=request.account_currency,
        accounting=accounting,
        diagnostics=(),
        realism=RealismDisclosure(
            tick_model=tick_model,
            slippage_model=profile_slippage,
            liquidity_model=profile_liquidity,
            session_model="explicit_utc_intervals",
            data_quality="passed",
            assumptions=("Trading-owned intents are the sole executable input.",),
            limitations=("Terminal liquidation uses the final observed bid or ask.",),
        ),
    )


def _publish_result(
    result: SimulationResult,
    artifact_root: Path,
    created_at: datetime,
) -> None:
    """Publish result/report artifacts and their acyclic manifest.

    Args:
        result: Completed immutable result.
        artifact_root: Approved global artifact root.
        created_at: Deterministic final UTC tick timestamp.

    Raises:
        SimulationError: If artifact publication fails.
    """
    logger.info("Publishing canonical Simulation artifacts for %s", result.run_id)
    run_root = artifact_root.resolve() / result.run_id
    result_path = run_root / "result.json"
    report_path = run_root / "report.md"
    journal_path = run_root / "journal.jsonl"
    _write_completed_text(
        result_path,
        build_json_report(result),
    )
    _write_completed_text(
        report_path,
        build_markdown_report(result),
    )
    manifest = build_artifact_manifest(
        run_root,
        (journal_path, result_path, report_path),
        created_at=created_at,
    )
    _write_completed_text(
        run_root / "manifest.json",
        canonical_json(
            manifest.model_dump(mode="python", warnings=False), max_items=None
        ),
    )


def _require_nonempty_timeline(timeline: tuple[Tick, ...]) -> None:
    """Require one non-empty deterministic execution timeline.

    Args:
        timeline: Data-owned ordered tick sequence.

    Raises:
        SimulationError: If no executable tick exists.
    """
    logger.debug("Checking that the Simulation timeline is non-empty")
    if not timeline:
        raise SimulationError(
            "SIM_DATA_COVERAGE_INSUFFICIENT", "Tick timeline is empty"
        )


@dataclass(frozen=True, slots=True)
class RunContext:
    """Everything one prepared run needs before its timeline is advanced.

    Assembling this is the deterministic half of a backtest: market data, tick
    timeline, journal writer, ledger, engine, and the approved order intents.
    Advancing the timeline is the other half. Separating them lets a caller
    prepare once and advance in increments, which is what a live what-if
    session does, without duplicating the preparation logic or letting it drift
    from the official run.
    """

    timeline: tuple[Tick, ...]
    evidence: Any
    writer: Any
    ledger: AccountLedger
    profile: Any
    engine: Any
    order_intents: tuple[OrderIntent, ...]


def prepare_run_context(
    request: SimulationBacktestRequestV1,
    dependencies: SimulationRunDependencies,
    run_id: str,
) -> RunContext:
    """Assemble one run's deterministic execution context.

    This is exactly the preparation `run_backtest` has always performed, in the
    same order, extracted so a live session can reuse it. It appends the
    ``run_started`` journal entry, so a caller that prepares a context owns the
    resulting journal.

    Args:
        request: Exact receiver-owned backtest request.
        dependencies: Explicit cross-domain and persistence composition.
        run_id: Canonical run identity for journal attribution.

    Returns:
        Prepared context ready for timeline advancement.
    """
    source_dataset = unwrap_simulation_response(
        dependencies.load_market_data(request),
        operation="simulation.run.load_market_data",
    )
    tick_dataset = unwrap_simulation_response(
        dependencies.generate_tick_series(source_dataset, request),
        operation="simulation.run.generate_tick_series",
    )
    context = MarketDataValidationContext(
        expected_data_hash=request.data_hash,
        requested_start=request.start,
        requested_end=request.end,
        evaluated_at=tick_dataset.available_at,
        maximum_staleness=timedelta(0),
        allowed_tick_models=APPROVED_TICK_MODELS,
    )
    evidence = validate_market_data(tick_dataset, context)
    timeline = build_tick_timeline(tick_dataset)
    _require_nonempty_timeline(timeline)
    writer = JournalWriter(
        dependencies.state_store,
        run_id,
        request.request_id,
        request.correlation_id,
    )
    unwrap_simulation_response(
        writer.append(
            "run_started",
            {
                "config_hash": request.config_hash,
                "data_hash": evidence.data_hash,
                "engine_version": _ENGINE_VERSION,
            },
            timeline[0].timestamp,
        ),
        operation="simulation.run.journal_append",
    )
    specification = unwrap_simulation_response(
        dependencies.resolve_symbol_specification(request),
        operation="simulation.run.resolve_symbol_specification",
    )
    cost_model = unwrap_simulation_response(
        dependencies.resolve_cost_model(request),
        operation="simulation.run.resolve_cost_model",
    )
    profile = unwrap_simulation_response(
        dependencies.resolve_execution_profile(request),
        operation="simulation.run.resolve_execution_profile",
    )
    ledger = AccountLedger(
        request.initial_balance,
        request.account_currency,
        specification,
        cost_model,
    )
    engine = EventDrivenExecutionEngine(ledger, writer, profile, _ENGINE_VERSION)
    indicators = unwrap_simulation_response(
        dependencies.calculate_indicators(source_dataset, request),
        operation="simulation.run.calculate_indicators",
    )
    strategy_intents = unwrap_simulation_response(
        dependencies.evaluate_strategy(source_dataset, indicators, request),
        operation="simulation.run.evaluate_strategy",
    )
    risk_decisions = unwrap_simulation_response(
        dependencies.review_risk(strategy_intents, request),
        operation="simulation.run.review_risk",
    )
    approved_order_intents: tuple[OrderIntent, ...] = unwrap_simulation_response(
        dependencies.build_order_intents(risk_decisions, request),
        operation="simulation.run.build_order_intents",
    )
    order_intents = tuple(
        sorted(
            approved_order_intents,
            key=lambda item: (item.created_at, item.client_order_id),
        )
    )
    return RunContext(
        timeline=timeline,
        evidence=evidence,
        writer=writer,
        ledger=ledger,
        profile=profile,
        engine=engine,
        order_intents=order_intents,
    )


def submit_orders_before(
    engine: object,
    unsent: list[OrderIntent],
    receipts: list[object],
    boundary: datetime,
) -> None:
    """Submit every intent created strictly before one timeline instant.

    Args:
        engine: Event-driven execution engine.
        unsent: Ordered pending intents, drained in place.
        receipts: Accumulated execution receipts, appended in place.
        boundary: Exclusive upper bound on intent creation time.
    """
    while unsent and unsent[0].created_at < boundary:
        receipts.append(
            unwrap_simulation_response(
                cast("Any", engine).submit_order(unsent.pop(0)),
                operation="simulation.run.engine_submit_order",
            )
        )


def advance_run_timeline(
    engine: object,
    timeline: tuple[Tick, ...],
    unsent: list[OrderIntent],
    receipts: list[object],
    *,
    start_index: int = 0,
    max_ticks: int | None = None,
) -> int:
    """Advance one engine across a bounded slice of its tick timeline.

    This is the exact loop `run_backtest` has always executed, extracted so a
    caller can drive it in bounded increments instead of only to completion.
    Default arguments run the whole timeline in one call, which is what an
    uninterrupted backtest does — the per-tick order of `execute_tick` followed
    by due-order submission is unchanged, so a completed run produces the same
    receipts, journal, and result hash regardless of how many calls were used
    to get there.

    Args:
        engine: Event-driven execution engine.
        timeline: Complete ordered tick timeline.
        unsent: Ordered pending intents, drained in place.
        receipts: Accumulated execution receipts, appended in place.
        start_index: Index of the first tick to execute.
        max_ticks: Maximum ticks to execute, or ``None`` for the remainder.

    Returns:
        Index of the next unexecuted tick; equals ``len(timeline)`` when the
        timeline is exhausted.
    """
    stop = (
        len(timeline)
        if max_ticks is None
        else min(len(timeline), start_index + max_ticks)
    )
    index = start_index
    while index < stop:
        tick = timeline[index]
        receipts.extend(
            cast(
                "Iterable[object]",
                unwrap_simulation_response(
                    cast("Any", engine).execute_tick(tick),
                    operation="simulation.run.engine_execute_tick",
                ),
            )
        )
        while unsent and unsent[0].created_at <= tick.timestamp:
            receipts.append(
                unwrap_simulation_response(
                    cast("Any", engine).submit_order(unsent.pop(0)),
                    operation="simulation.run.engine_submit_order",
                )
            )
        index += 1
    return index


def _run_backtest_with_evidence(  # noqa: PLR0915 - governed lifecycle.
    request: SimulationBacktestRequestV1,
    auth_context: AuthContext,
    dependencies: SimulationRunDependencies,
) -> tuple[SimulationResult, tuple[tuple[datetime, Decimal], ...]]:
    """Execute one governed run and retain internal equity evidence.

    Args:
        request: Exact receiver-owned backtest request.
        auth_context: Authenticated matching trace context.
        dependencies: Explicit cross-domain and persistence composition.

    Returns:
        Completed canonical result and ordered mark-to-market equity evidence.

    Raises:
        SimulationError: For any controlled or safely mapped run failure.
        TypeError: If persisted replay material is structurally invalid.
    """
    logger.info("Starting official Simulation backtest %s", request.request_id)
    _validate_auth(request, auth_context)
    payload = request.model_dump(mode="python", warnings=False)
    validate_run_inputs(payload)
    validate_phase_one_scope(payload)
    request_hash = _canonical_hash(payload)
    run_id = f"sim-{request_hash[:32]}"
    emit_simulation_audit(
        dependencies,
        auth_context,
        "simulation.run_started",
        request.start,
        {"request_hash": request_hash, "run_id": run_id},
    )
    completed_run = resolve_idempotent_run(
        request.request_id,
        request_hash,
        lambda request_id: unwrap_simulation_response(
            dependencies.state_store.load_run(request_id),
            operation="simulation.run.load_run",
        ),
    )
    if completed_run is not None:
        existing = unwrap_simulation_response(
            dependencies.state_store.load_run(request.request_id),
            operation="simulation.run.load_run",
        )
        stored = None if existing is None else existing.get("result_payload")
        if not isinstance(stored, dict):
            raise SimulationError(
                "SIM_CHECKPOINT_INCOMPATIBLE", "Stored result is unavailable"
            )
        try:
            stored_result = dict(stored)
            stored_fills = stored_result.get("fills")
            if not isinstance(stored_fills, list):
                raise TypeError("stored fills are invalid")  # noqa: TRY301
            stored_result["fills"] = tuple(
                create_execution_receipt(**item)
                for item in stored_fills
                if isinstance(item, dict)
            )
            if len(stored_result["fills"]) != len(stored_fills):
                raise TypeError("stored fills are invalid")  # noqa: TRY301
            result = SimulationResult.model_validate(stored_result)
        except (TypeError, ValidationError) as error:
            raise SimulationError(
                "SIM_CHECKPOINT_INCOMPATIBLE", "Stored result is invalid"
            ) from error
        emit_simulation_audit(
            dependencies,
            auth_context,
            "simulation.run_replayed",
            request.end,
            {"request_hash": request_hash, "run_id": result.run_id},
        )
        return result, ()
    unwrap_simulation_response(
        dependencies.state_store.record_idempotency(
            request.request_id,
            request_hash,
            run_id,
            "started",
        ),
        operation="simulation.run.record_idempotency",
    )
    try:
        context = prepare_run_context(request, dependencies, run_id)
        timeline = context.timeline
        evidence = context.evidence
        writer = context.writer
        ledger = context.ledger
        profile = context.profile
        engine = context.engine
        order_intents = context.order_intents
        unsent = list(order_intents)
        receipts: list[object] = []
        submit_orders_before(engine, unsent, receipts, timeline[0].timestamp)
        advance_run_timeline(engine, timeline, unsent, receipts)
        terminal_state = unwrap_simulation_response(
            engine.snapshot(),
            operation="simulation.run.engine_snapshot",
        )
        positions = cast("Iterable[Mapping[str, object]]", terminal_state["positions"])
        for position in positions:
            unwrap_simulation_response(
                engine.close_position(
                    str(position["position_id"]), cast("Decimal", position["volume"])
                ),
                operation="simulation.run.engine_close_position",
            )
        unwrap_simulation_response(
            writer.append(
                "run_completed",
                {"receipt_count": len(receipts)},
                timeline[-1].timestamp,
            ),
            operation="simulation.run.journal_append",
        )
        unwrap_simulation_response(
            writer.finalize(), operation="simulation.run.journal_finalize"
        )
        result = _completed_result(
            request,
            request_hash,
            run_id,
            f"{run_id}/journal.jsonl",
            tuple(receipts),
            ledger,
            engine.closed_trades,
            profile.slippage_mode,
            profile.liquidity_mode,
            evidence.tick_model,
        )
        _publish_result(result, dependencies.artifact_root, timeline[-1].timestamp)
        unwrap_simulation_response(
            dependencies.state_store.record_idempotency(
                request.request_id,
                request_hash,
                run_id,
                "completed",
                result.model_dump(mode="python", warnings=False),
            ),
            operation="simulation.run.record_idempotency",
        )
        emit_simulation_audit(
            dependencies,
            auth_context,
            "simulation.run_completed",
            timeline[-1].timestamp,
            {"request_hash": request_hash, "run_id": run_id},
        )
        return result, engine.equity_observations
    except SimulationError:
        unwrap_simulation_response(
            dependencies.state_store.record_idempotency(
                request.request_id,
                request_hash,
                run_id,
                "failed",
            ),
            operation="simulation.run.record_idempotency",
        )
        raise
    except Exception as error:
        logger.exception("Mapping unexpected Simulation run failure safely")
        unwrap_simulation_response(
            dependencies.state_store.record_idempotency(
                request.request_id,
                request_hash,
                run_id,
                "failed",
            ),
            operation="simulation.run.record_idempotency",
        )
        raise SimulationError(
            "SIM_INTERNAL_ERROR",
            "Simulation failed safely",
            request_id=request.request_id,
        ) from error


async def run_backtest_async(
    request: SimulationBacktestRequestV1,
    auth_context: AuthContext,
    dependencies: SimulationRunDependencies,
) -> SimulationResult:
    """Execute and publish one governed deterministic canonical FX run asynchronously.

    Args:
        request: Exact receiver-owned backtest request.
        auth_context: Authenticated matching trace context.
        dependencies: Explicit cross-domain and persistence composition.

    Returns:
        Completed canonical result; partial results are never returned.

    Raises:
        SimulationError: For any controlled or safely mapped run failure.
    """
    try:
        result, _ = _run_backtest_with_evidence(request, auth_context, dependencies)
    except SimulationError:
        emit_simulation_audit(
            dependencies,
            auth_context,
            "simulation.run_failed",
            request.end,
            {"config_hash": request.config_hash},
        )
        raise
    return result


def run_backtest(
    request: SimulationBacktestRequestV1,
    auth_context: AuthContext,
    dependencies: SimulationRunDependencies,
) -> SimulationResult:
    """Execute the async run bridge outside an active event loop.

    Returns:
        Completed canonical result.

    Raises:
        SimulationError: If called inside an active event loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_backtest_async(request, auth_context, dependencies))
    raise SimulationError(
        "SIM_UNSUPPORTED_OPERATION",
        "Synchronous backtest cannot run inside an active event loop",
    )


__all__ = ["run_backtest", "run_backtest_async"]
