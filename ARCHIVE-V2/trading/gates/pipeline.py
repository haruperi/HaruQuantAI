"""Canonical live-route gate pipeline orchestrator.

This module owns the two gates whose logic is specific to this file
(``ComplianceGate``, TRD-FR-084, and ``MarketTurbulenceGate``, TRD-FR-085), a
thin wrapper exposing broker adapter capability validation as gate 15
(reusing ``execution/broker_capability_validation.py``), and the generic
:func:`run_gate_pipeline` orchestration engine that sequences an arbitrary
ordered set of gate steps with short-circuit-on-failure (TRD-FR-086),
explicit diagnostic-skip marking for steps that never ran
(TRD-FR-087), and deadline/quote-staleness enforcement with per-gate latency
stamping (TRD-FR-088).

Callers compose the full 16-step pipeline (TRD-FR-083) by building an
ordered tuple of ``(GateName, Callable[[], GateStepResult])`` steps using
this module's gates alongside ``gates/policy_matrix.py``,
``gates/approval.py``, ``gates/readiness.py``, ``gates/kill_switch.py``,
``gates/audit_and_compensation.py``, and the injected ``IdempotencyStore``
port. Steps whose backing module is not yet implemented (route/promotion
compatibility, session status, concurrency lease, reconciliation authority)
use :func:`evaluate_seam_gate`, which fails closed until a real evaluator is
injected — the pipeline can never silently skip a safety-critical step.
"""
# ruff: noqa: SIM102 -- nested ifs kept flat and explicit for 100% branch coverage.

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.trading.contracts import TradingContract, TradingStatus
from app.services.trading.execution.broker_capability_validation import (
    validate_broker_capabilities,
)
from app.services.trading.gates._common import (
    GateName,
    GateStepResult,
    GateStepStatus,
    blocked_step,
    diagnostic_skipped_step,
    passed_step,
)
from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger
from pydantic import Field

if TYPE_CHECKING:
    from app.services.trading.contracts import QuoteSnapshot, TradingRequestEnvelope
    from app.services.trading.execution.broker_capability_validation import (
        BrokerCapabilityProfile,
    )
    from app.services.trading.state.ports import Clock

BPS_DENOMINATOR = Decimal(10_000)
MIN_TURBULENCE_WINDOW_SIZE = 2
MILLISECONDS_PER_SECOND = Decimal(1000)

GateStep = tuple[GateName, Callable[[], GateStepResult]]


class ComplianceEvidence(TradingContract):
    """Compliance restricted-symbol list evidence.

    Attributes:
        restricted_symbols: Symbols currently on the compliance restricted
            list.
    """

    restricted_symbols: tuple[str, ...] = Field(default_factory=tuple)


class GatePipelineDecision(TradingContract):
    """Aggregate outcome of one gate pipeline evaluation.

    Attributes:
        status: ``accepted`` when every gate passed, ``blocked`` otherwise.
        steps: Per-gate step results, in evaluation order.
        blocked_at_gate: Gate that produced the first blocking result, if
            any.
        error_code: Stable public error code from the blocking gate, if any.
        total_latency_ms: Total pipeline evaluation latency.
    """

    status: TradingStatus
    steps: tuple[GateStepResult, ...]
    blocked_at_gate: GateName | None = None
    error_code: str | None = None
    total_latency_ms: Decimal = Field(default=Decimal(0), ge=0)


def evaluate_compliance_gate(
    *,
    evidence: ComplianceEvidence,
    symbol: str | None,
) -> GateStepResult:
    """Evaluate the compliance restricted-symbol gate (TRD-FR-084).

    Args:
        evidence: Compliance restricted-symbol list evidence.
        symbol: Requested trading symbol, if any.

    Returns:
        GateStepResult: Passing or blocking compliance gate result.
    """
    logger.info("Evaluating compliance gate for symbol {}.", symbol)
    if symbol is not None and symbol in evidence.restricted_symbols:
        logger.info("Symbol {} is on the compliance restricted list.", symbol)
        return blocked_step(
            gate=GateName.COMPLIANCE,
            reason_code="POLICY_BLOCKED",
            message=f"Symbol {symbol} is on the compliance restricted list.",
        )
    logger.debug("Compliance gate passed for symbol {}.", symbol)
    return passed_step(gate=GateName.COMPLIANCE)


class MarketTurbulenceMonitor:
    """Bounded per-symbol mid-price velocity circuit breaker (TRD-FR-085).

    Args:
        window_size: Number of recent mid-prices retained per symbol.
        velocity_threshold_bps: Maximum allowed absolute price change across
            the retained window, in basis points.
    """

    def __init__(self, *, window_size: int, velocity_threshold_bps: Decimal) -> None:
        """Initialize the turbulence monitor with an empty price history.

        Args:
            window_size: Number of recent mid-prices retained per symbol.
            velocity_threshold_bps: Maximum allowed absolute price change
                across the retained window, in basis points.

        Raises:
            ValueError: If ``window_size`` is smaller than 2.
        """
        logger.info(
            "Initializing market turbulence monitor, window_size={}.", window_size
        )
        if window_size < MIN_TURBULENCE_WINDOW_SIZE:
            raise ValueError("window_size must be at least 2.")
        self._window_size = window_size
        self._velocity_threshold_bps = velocity_threshold_bps
        self._history: dict[str, deque[Decimal]] = {}
        self._suspended: set[str] = set()

    def is_suspended(self, *, symbol: str) -> bool:
        """Return whether a symbol is currently suspended for turbulence.

        Args:
            symbol: Instrument symbol.

        Returns:
            bool: True when the symbol is suspended.
        """
        logger.debug("Checking turbulence suspension for {}.", symbol)
        return symbol in self._suspended

    def resume(self, *, symbol: str) -> None:
        """Resume a previously suspended symbol.

        Args:
            symbol: Instrument symbol.
        """
        logger.info("Resuming symbol {} from turbulence suspension.", symbol)
        self._suspended.discard(symbol)

    def observe(self, *, symbol: str, mid_price: Decimal) -> GateStepResult:
        """Observe a new mid-price and evaluate the turbulence gate.

        Args:
            symbol: Instrument symbol.
            mid_price: Latest observed mid-price.

        Returns:
            GateStepResult: Passing or blocking turbulence gate result.
        """
        logger.info("Observing turbulence mid-price {} for {}.", mid_price, symbol)
        if symbol in self._suspended:
            return blocked_step(
                gate=GateName.MARKET_TURBULENCE,
                reason_code="CIRCUIT_OPEN",
                message=f"{symbol} is suspended for market turbulence.",
            )
        history = self._history.setdefault(symbol, deque(maxlen=self._window_size))
        history.append(mid_price)
        if len(history) < MIN_TURBULENCE_WINDOW_SIZE:
            logger.debug("Insufficient turbulence history for {} yet.", symbol)
            return passed_step(gate=GateName.MARKET_TURBULENCE)

        oldest = history[0]
        change_bps = abs(mid_price - oldest) / oldest * BPS_DENOMINATOR
        if change_bps > self._velocity_threshold_bps:
            self._suspended.add(symbol)
            logger.info(
                "Symbol {} suspended: velocity {} bps exceeds threshold {}.",
                symbol,
                change_bps,
                self._velocity_threshold_bps,
            )
            return blocked_step(
                gate=GateName.MARKET_TURBULENCE,
                reason_code="CIRCUIT_OPEN",
                message=f"{symbol} velocity {change_bps} bps exceeds threshold.",
            )
        logger.debug("Turbulence gate passed for {}.", symbol)
        return passed_step(gate=GateName.MARKET_TURBULENCE)


def evaluate_adapter_permission_gate(
    *,
    profile: BrokerCapabilityProfile,
    order_type: str,
    filling_mode: str,
    price: Decimal,
    volume: Decimal,
) -> GateStepResult:
    """Evaluate adapter permission/capability as gate 15.

    Args:
        profile: Declared broker adapter capability profile.
        order_type: Requested order type identifier.
        filling_mode: Requested filling mode identifier.
        price: Requested order price.
        volume: Requested order volume.

    Returns:
        GateStepResult: Passing or blocking adapter permission gate result.
    """
    logger.info("Evaluating adapter permission gate for {}.", profile.provider)
    try:
        validate_broker_capabilities(
            profile=profile,
            order_type=order_type,
            filling_mode=filling_mode,
            price=price,
            volume=volume,
        )
    except TradingValidationError as exc:
        logger.info("Adapter permission gate blocked: {}.", exc)
        return blocked_step(
            gate=GateName.ADAPTER_PERMISSION,
            reason_code="VALIDATION_FAILED",
            message=str(exc),
        )
    logger.debug("Adapter permission gate passed for {}.", profile.provider)
    return passed_step(gate=GateName.ADAPTER_PERMISSION)


def evaluate_seam_gate(
    *,
    gate: GateName,
    evaluator: Callable[[], GateStepResult] | None,
) -> GateStepResult:
    """Evaluate a gate whose backing module is future work.

    Fails closed with ``LIVE_GATE_FAILED`` when no evaluator has been
    injected yet, so an incomplete pipeline can never silently pass a
    safety-critical step it does not yet implement.

    Args:
        gate: Gate identifier.
        evaluator: Injected evaluator callable, once its backing module is
            implemented and wired in.

    Returns:
        GateStepResult: The evaluator's result, or a fail-closed block.
    """
    logger.info("Evaluating seam gate {}.", gate.value)
    if evaluator is None:
        logger.warning(
            "Seam gate {} has no injected evaluator; failing closed.", gate.value
        )
        return blocked_step(
            gate=gate,
            reason_code="LIVE_GATE_FAILED",
            message=f"{gate.value} evaluator is not yet configured.",
        )
    return evaluator()


def compute_effective_deadline(
    *,
    request: TradingRequestEnvelope,
    clock: Clock,
    default_budget_ms: Decimal,
) -> datetime:
    """Resolve the effective pipeline deadline (TRD-FR-088).

    Args:
        request: Trading request envelope.
        clock: Injected clock.
        default_budget_ms: Default gate budget used when the request does
            not carry an explicit ``deadline_utc``.

    Returns:
        datetime: Effective UTC deadline for this pipeline evaluation.
    """
    logger.info(
        "Computing effective gate pipeline deadline for {}.", request.request_id
    )
    if request.deadline_utc is not None:
        return datetime.fromisoformat(request.deadline_utc)
    return clock.now_utc() + timedelta(milliseconds=float(default_budget_ms))


def run_gate_pipeline(
    *,
    steps: tuple[GateStep, ...],
    clock: Clock,
    deadline: datetime,
    quote_snapshot: QuoteSnapshot | None = None,
    quote_ttl_ms: int | None = None,
) -> GatePipelineDecision:
    """Run an ordered sequence of gate steps with short-circuit enforcement.

    Downstream steps never execute once a gate blocks (TRD-FR-086); they are
    recorded as explicit diagnostic-skipped results instead (TRD-FR-087).
    Before each gate, the pipeline checks the deadline and, when a quote
    snapshot and TTL are supplied, its freshness age plus elapsed pipeline
    time against that TTL (TRD-FR-088).

    Args:
        steps: Ordered ``(GateName, evaluator)`` pipeline steps.
        clock: Injected clock for deterministic time and latency reads.
        deadline: Effective UTC deadline for this pipeline evaluation.
        quote_snapshot: Mandatory-quote evidence, when applicable.
        quote_ttl_ms: Configured quote freshness TTL, when applicable.

    Returns:
        GatePipelineDecision: Aggregate pipeline outcome.
    """
    logger.info("Running gate pipeline with {} step(s).", len(steps))
    pipeline_start = clock.monotonic()
    results: list[GateStepResult] = []
    blocked_at: GateName | None = None
    error_code: str | None = None
    short_circuited = False

    for gate_name, evaluator in steps:
        if short_circuited:
            results.append(diagnostic_skipped_step(gate=gate_name))
            continue

        if clock.now_utc() > deadline:
            logger.warning("Gate pipeline deadline exceeded at {}.", gate_name.value)
            results.append(
                blocked_step(
                    gate=gate_name,
                    reason_code="DEADLINE_EXCEEDED",
                    message="Gate pipeline deadline exceeded.",
                )
            )
            blocked_at = gate_name
            error_code = "DEADLINE_EXCEEDED"
            short_circuited = True
            continue

        if quote_snapshot is not None:
            if quote_ttl_ms is not None:
                elapsed_ms = (
                    Decimal(str(clock.monotonic() - pipeline_start))
                    * MILLISECONDS_PER_SECOND
                )
                total_age_ms = Decimal(quote_snapshot.freshness_age_ms) + elapsed_ms
                if total_age_ms > quote_ttl_ms:
                    logger.warning(
                        "Quote snapshot stale mid-pipeline at {}.", gate_name.value
                    )
                    results.append(
                        blocked_step(
                            gate=gate_name,
                            reason_code="QUOTE_STALE",
                            message="Quote snapshot aged beyond its freshness TTL mid-pipeline.",  # noqa: E501
                        )
                    )
                    blocked_at = gate_name
                    error_code = "QUOTE_STALE"
                    short_circuited = True
                    continue

        step_start = clock.monotonic()
        result = evaluator()
        step_latency_ms = (
            Decimal(str(clock.monotonic() - step_start)) * MILLISECONDS_PER_SECOND
        )
        result = result.model_copy(update={"latency_ms": step_latency_ms})
        results.append(result)
        if result.status is GateStepStatus.BLOCKED:
            blocked_at = gate_name
            error_code = result.reason_code
            short_circuited = True

    total_latency_ms = (
        Decimal(str(clock.monotonic() - pipeline_start)) * MILLISECONDS_PER_SECOND
    )
    status = TradingStatus.BLOCKED if short_circuited else TradingStatus.ACCEPTED
    logger.info(
        "Gate pipeline result {} (blocked_at={}).",
        status.value,
        blocked_at.value if blocked_at is not None else None,
    )
    return GatePipelineDecision(
        status=status,
        steps=tuple(results),
        blocked_at_gate=blocked_at,
        error_code=error_code,
        total_latency_ms=total_latency_ms,
    )
