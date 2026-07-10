"""Concrete 16-step live gate pipeline with broker dispatch (BF-TRD-003).

This module assembles every gate in ``gates/_common.py::GateName`` order and
hands them to the existing ``gates/pipeline.py::run_gate_pipeline`` orchestrator,
which owns short-circuiting, deadline enforcement, and quote freshness. Nothing
here reimplements that logic.

:class:`LiveGatePipelineImpl` satisfies the ``LiveGatePipeline`` protocol in
``actions/_common.py``, so injecting one into ``TradingActionDependencies``
turns every ``actions/*`` primitive from ``packaged_only`` into a real dispatch.

The broker call itself is never made here. It arrives as an injected
``dispatch_callable_factory``, whose only production implementation lives in
``execution/broker_dispatch.py`` -- the single broker boundary in this package.

Several upstream helpers raise on failure instead of returning a
:class:`~app.services.trading.gates._common.GateStepResult`. The ``_*_step``
adapters below translate those exceptions into blocking gate results. They add
no policy of their own: a helper that raises must produce a blocked step, never
a passed one.
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from app.services.trading.contracts import (
    JsonObject,
    NormalizedTradeResult,
    RetrySafety,
    SideEffectMode,
    TradingAction,
    TradingError,
    TradingMetadata,
    TradingRequestEnvelope,
    TradingResponseEnvelope,
    TradingStatus,
)
from app.services.trading.execution.broker_dispatch import (
    is_success_retcode,
    snapshot_broker_state,
)
from app.services.trading.execution.coordinator import (
    ExecutionCoordinator,
    finalize_dispatch_outcome,
)
from app.services.trading.gates._common import (
    GateName,
    GateStepResult,
    blocked_step,
    passed_step,
)
from app.services.trading.gates.approval import (
    compute_canonical_request_hash,
    validate_operator_approval,
)
from app.services.trading.gates.audit_and_compensation import record_pre_mutation_audit
from app.services.trading.gates.kill_switch import (
    OperationalMode,
    evaluate_kill_switches,
)
from app.services.trading.gates.pipeline import (
    GateStep,
    compute_effective_deadline,
    evaluate_adapter_permission_gate,
    evaluate_compliance_gate,
    run_gate_pipeline,
)
from app.services.trading.gates.policy_matrix import resolve_policy
from app.services.trading.gates.readiness import (
    validate_broker_readiness,
    validate_clock_drift,
)
from app.services.trading.promotion.ladder import evaluate_promotion_stage_gate
from app.services.trading.reconciliation.authority_and_retry_guard import (
    evaluate_reconciliation_authority_gate,
)
from app.services.trading.runtime.session_manager import SessionState
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    map_exception_to_trading_error,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from app.services.trading.execution.broker_capability_validation import (
        BrokerCapabilityProfile,
    )
    from app.services.trading.execution.coordinator import AsyncDispatchExecutor
    from app.services.trading.gates.approval import ApprovalScope, OperatorApprovalToken
    from app.services.trading.gates.kill_switch import KillSwitchState
    from app.services.trading.gates.pipeline import (
        ComplianceEvidence,
        MarketTurbulenceMonitor,
    )
    from app.services.trading.gates.policy_matrix import PolicyMatrix
    from app.services.trading.gates.readiness import (
        BrokerReadinessEvidence,
        ClockDriftEvidence,
    )
    from app.services.trading.reconciliation.authority_and_retry_guard import (
        AuthorityAndRetryGuard,
    )
    from app.services.trading.runtime.coordination import ConcurrencyLockManager
    from app.services.trading.runtime.session_manager import SessionManager
    from app.services.trading.state.ports import (
        AuditSink,
        Clock,
        IdempotencyStore,
        TradeStore,
    )

DEFAULT_DISPATCH_TIMEOUT_SECONDS = 5.0
DEFAULT_GATE_BUDGET_MS = 2000

_MUTATION_BLOCKING_MODES = frozenset(
    {OperationalMode.READ_ONLY, OperationalMode.STOPPED}
)

# Session state must be RUNNING before any live mutation is admitted.
_ADMITTING_SESSION_STATES = frozenset({SessionState.RUNNING})

RISK_PASSTHROUGH_MESSAGE = (
    "RISK_DECISION passthrough: no pre-trade risk evaluation was performed."
)


def _optional_decimal(value: object) -> Decimal | None:
    """Coerce an optional JSON-safe payload value into a Decimal.

    Payload fields are genuinely optional, not zero-defaulted: a full position
    close carries ``volume=None`` and a market order carries ``price=None``.
    ``Decimal(str(None))`` raises ``ConversionSyntax``, so absence must be
    distinguished from zero.

    Args:
        value: Raw payload value.

    Returns:
        Decimal | None: The parsed decimal, or None when absent or unparseable.
    """
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        logger.warning("Could not parse {!r} as a Decimal payload value.", value)
        return None


def passthrough_risk_evaluator() -> GateStepResult:
    """Pass the RISK_DECISION gate without evaluating risk (BF-TRD-004).

    This exists to preserve exact behavioral parity with the retired
    ``app/services/trader`` package, which performed **no** pre-trade risk
    checks before dispatching to a broker. It is not a new gap; it is the
    existing gap, made visible.

    Wire ``app/services/risk`` into gate 7 and pass that evaluator instead
    before scaling live position size. Every live evaluation logs a warning
    containing the literal string ``RISK_DECISION passthrough`` so opted-in
    call sites are greppable and alertable.

    Returns:
        GateStepResult: An unconditionally passing RISK_DECISION step.
    """
    logger.warning(RISK_PASSTHROUGH_MESSAGE)
    return passed_step(
        gate=GateName.RISK_DECISION,
        message=RISK_PASSTHROUGH_MESSAGE,
    )


@dataclass
class DispatchOutcome:
    """Mutable holder for the result of the DISPATCH gate.

    ``run_gate_pipeline`` steps return only a ``GateStepResult``, so the
    normalized broker result is captured here for envelope construction after
    the pipeline completes.

    Attributes:
        result: Normalized broker result, when the broker responded.
        unknown_outcome: Whether the broker call timed out, leaving the true
            outcome unknown.
        attempted: Whether the broker mutation was actually issued.
        error: Structured public error, when dispatch raised.
    """

    result: NormalizedTradeResult | None = None
    unknown_outcome: bool = False
    attempted: bool = False
    error: TradingError | None = None


@dataclass
class LiveGateEvidence:
    """Caller-supplied evidence bundle for one live gate pipeline evaluation.

    Attributes:
        account_id: Broker account the request targets.
        strategy_id: Strategy originating the request.
        compliance_evidence: Compliance restricted-symbol evidence.
        broker_readiness: Broker connection and permission evidence.
        clock_drift: Clock synchronization evidence.
        capability_profile: Declared broker adapter capability profile.
        kill_switches: Current kill-switch states.
        approval_token: Operator approval token, when the policy requires one.
        approval_scope: Expected approval scope.
        order_type: Requested order type identifier for the capability gate.
        filling_mode: Requested filling mode identifier for the capability gate.
        idempotency_key: Idempotency key reserved for this request.
        idempotency_material_hash: Canonical material hash for the key.
        idempotency_expires_at: Lease expiry for the reservation.
    """

    account_id: str
    strategy_id: str
    compliance_evidence: ComplianceEvidence
    broker_readiness: BrokerReadinessEvidence
    clock_drift: ClockDriftEvidence
    capability_profile: BrokerCapabilityProfile
    kill_switches: tuple[KillSwitchState, ...] = ()
    approval_token: OperatorApprovalToken | None = None
    approval_scope: ApprovalScope | None = None
    order_type: str = "market"
    filling_mode: str = "IOC"
    idempotency_key: str = ""
    idempotency_material_hash: str = ""
    idempotency_expires_at: datetime | None = None
    _reserved: bool = field(default=False, init=False, repr=False)


class LiveGatePipelineImpl:
    """The canonical 16-step live gate pipeline with real broker dispatch.

    Satisfies the ``LiveGatePipeline`` protocol consumed by
    ``actions/_common.dispatch_or_package``.

    Args:
        clock: Injected clock for deterministic time and latency reads.
        tenant_id: Tenant or session namespace for store operations.
        evidence: Caller-supplied evidence bundle.
        policy_matrix: Governed-action policy matrix.
        session_manager: Live session state authority.
        turbulence_monitor: Market turbulence monitor.
        idempotency_store: Idempotency reservation store.
        lock_manager: Per-(account, symbol) concurrency lock manager.
        authority_guard: Reconciliation authority guard.
        audit_sink: Pre-mutation audit sink.
        trade_store: Trade projection store.
        dispatch_executor: Executor running the broker dispatch off-thread.
        dispatch_callable_factory: Builds the zero-argument broker dispatch
            callable from a JSON-safe payload and request ID.
        risk_evaluator: RISK_DECISION gate evaluator. Deliberately has no
            default: every caller must name its choice at the call site. Pass
            :func:`passthrough_risk_evaluator` for ``trader`` parity.
        dispatch_timeout_seconds: Broker call timeout before the outcome is
            classified as unknown.
        quote_ttl_ms: Quote freshness TTL enforced between gates.
        default_budget_ms: Pipeline deadline budget when the request carries no
            explicit deadline.
        reconciliation_hook: Called after an unknown outcome to force a
            reconciliation pass. Defaults to a broker state snapshot.
    """

    def __init__(
        self,
        *,
        clock: Clock,
        tenant_id: str,
        evidence: LiveGateEvidence,
        policy_matrix: PolicyMatrix,
        session_manager: SessionManager,
        turbulence_monitor: MarketTurbulenceMonitor,
        idempotency_store: IdempotencyStore,
        lock_manager: ConcurrencyLockManager,
        authority_guard: AuthorityAndRetryGuard,
        audit_sink: AuditSink,
        trade_store: TradeStore,
        dispatch_executor: AsyncDispatchExecutor,
        dispatch_callable_factory: Callable[
            [JsonObject, str], Callable[[], NormalizedTradeResult]
        ],
        risk_evaluator: Callable[[], GateStepResult],
        dispatch_timeout_seconds: float = DEFAULT_DISPATCH_TIMEOUT_SECONDS,
        quote_ttl_ms: int | None = None,
        default_budget_ms: int = DEFAULT_GATE_BUDGET_MS,
        reconciliation_hook: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the live gate pipeline composition root."""
        logger.info("Initializing live gate pipeline for tenant {}.", tenant_id)
        if not tenant_id.strip():
            raise ValueError("tenant_id must be non-empty.")
        self._clock = clock
        self._tenant_id = tenant_id
        self._evidence = evidence
        self._policy_matrix = policy_matrix
        self._session_manager = session_manager
        self._turbulence_monitor = turbulence_monitor
        self._idempotency_store = idempotency_store
        self._lock_manager = lock_manager
        self._authority_guard = authority_guard
        self._audit_sink = audit_sink
        self._trade_store = trade_store
        self._dispatch_executor = dispatch_executor
        self._dispatch_callable_factory = dispatch_callable_factory
        self._risk_evaluator = risk_evaluator
        self._dispatch_timeout_seconds = dispatch_timeout_seconds
        self._quote_ttl_ms = quote_ttl_ms
        self._default_budget_ms = default_budget_ms
        self._reconciliation_hook = reconciliation_hook
        self.coordinator = ExecutionCoordinator()
        self.audit_ref: str | None = None

    # ------------------------------------------------------------------
    # Gate adapters
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_symbol(request: TradingRequestEnvelope) -> str:
        """Resolve the symbol a request acts on, for locking and turbulence.

        Not every action carries a symbol: ``position_close`` addressed by
        ticket and account-scoped emergency flattens legitimately package
        ``symbol=None``. ``trader`` resolved the symbol from the ticket and fell
        back to a ``GLOBAL`` lock scope; the same fallback order applies here so
        an account-wide action takes one coherent lease instead of locking on an
        empty string.
        """
        if request.symbol and request.symbol.strip():
            return request.symbol
        payload_symbol = request.payload.get("symbol")
        if isinstance(payload_symbol, str) and payload_symbol.strip():
            return payload_symbol
        if request.quote_snapshot is not None:
            return request.quote_snapshot.symbol
        return "GLOBAL"

    def _local_schema_step(self, request: TradingRequestEnvelope) -> GateStepResult:
        """Verify the envelope is dispatch-ready (gate 1).

        ``actions/validation.py`` already validated the order intent before
        packaging. This gate re-asserts the envelope invariants the dispatch
        path itself depends on, so a hand-built envelope cannot bypass them.
        """
        logger.info("Evaluating local schema gate for {}.", request.request_id)
        if not request.payload:
            return blocked_step(
                gate=GateName.LOCAL_SCHEMA_VALIDATION,
                reason_code="VALIDATION_FAILED",
                message="A live mutation requires a non-empty dispatch payload.",
            )
        if request.action is TradingAction.SUBMIT_ORDER and not (
            request.symbol and request.symbol.strip()
        ):
            return blocked_step(
                gate=GateName.LOCAL_SCHEMA_VALIDATION,
                reason_code="VALIDATION_FAILED",
                message="Order submission requires an explicit target symbol.",
            )
        return passed_step(gate=GateName.LOCAL_SCHEMA_VALIDATION)

    def _session_status_step(self) -> GateStepResult:
        """Block unless the session is running and admits mutations (gate 4)."""
        logger.info("Evaluating session status gate.")
        state = self._session_manager.state
        mode = self._session_manager.mode
        if state not in _ADMITTING_SESSION_STATES:
            return blocked_step(
                gate=GateName.SESSION_STATUS,
                reason_code="SERVICE_UNAVAILABLE",
                message=f"Session is {state.value}; mutations are not admitted.",
            )
        if mode in _MUTATION_BLOCKING_MODES:
            return blocked_step(
                gate=GateName.SESSION_STATUS,
                reason_code="POLICY_BLOCKED",
                message=f"Session operational mode {mode.value} blocks mutations.",
            )
        return passed_step(gate=GateName.SESSION_STATUS)

    def _symbol_halted_step(self, symbol: str) -> GateStepResult | None:
        """Return a blocking step when the symbol is halted, else None."""
        if self._session_manager.is_symbol_halted(symbol):
            return blocked_step(
                gate=GateName.SESSION_STATUS,
                reason_code="POLICY_BLOCKED",
                message=f"Symbol {symbol} is halted for this session.",
            )
        return None

    def _kill_switch_step(self, request: TradingRequestEnvelope) -> GateStepResult:
        """Adapt ``evaluate_kill_switches`` to a gate step (gate 5)."""
        logger.info("Evaluating kill switch gate for {}.", request.request_id)
        try:
            policy_entry = resolve_policy(
                matrix=self._policy_matrix, action=request.action
            )
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.KILL_SWITCH,
                reason_code=exc.code,
                message=str(exc),
            )
        evaluation = evaluate_kill_switches(
            switches=self._evidence.kill_switches,
            action=request.action,
            policy_entry=policy_entry,
        )
        if evaluation.blocked:
            return blocked_step(
                gate=GateName.KILL_SWITCH,
                reason_code=evaluation.reason_code or "LIVE_KILL_SWITCH_ACTIVE",
                message=evaluation.message,
            )
        return passed_step(gate=GateName.KILL_SWITCH, message=evaluation.message)

    def _operator_approval_step(
        self, request: TradingRequestEnvelope
    ) -> GateStepResult:
        """Adapt the raising ``validate_operator_approval`` to a step (gate 6)."""
        logger.info("Evaluating operator approval gate for {}.", request.request_id)
        try:
            policy_entry = resolve_policy(
                matrix=self._policy_matrix, action=request.action
            )
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.OPERATOR_APPROVAL,
                reason_code=exc.code,
                message=str(exc),
            )
        if not policy_entry.requires_approval:
            return passed_step(
                gate=GateName.OPERATOR_APPROVAL,
                message="Approval not required by policy.",
            )
        token = self._evidence.approval_token
        if token is None or self._evidence.approval_scope is None:
            return blocked_step(
                gate=GateName.OPERATOR_APPROVAL,
                reason_code="APPROVAL_REQUIRED",
                message="Policy requires operator approval; no token supplied.",
            )
        try:
            validate_operator_approval(
                token=token,
                now=self._clock.now_utc(),
                expected_request_hash=self._canonical_request_hash(request),
                expected_scope=self._evidence.approval_scope,
            )
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.OPERATOR_APPROVAL,
                reason_code=exc.code,
                message=str(exc),
            )
        return passed_step(gate=GateName.OPERATOR_APPROVAL)

    def _canonical_request_hash(self, request: TradingRequestEnvelope) -> str:
        """Compute the approval-binding hash for a request envelope.

        ``actions/orders.py`` nests the validated order under ``payload["intent"]``
        rather than flattening it. Reading the flat keys would hash empty strings
        for every order, so an approval token issued for one order would validate
        against any other. The nested intent is the authoritative source; the flat
        payload is only a fallback for hand-built envelopes.
        """
        payload = request.payload
        intent = payload.get("intent")
        source: JsonObject = intent if isinstance(intent, dict) else payload

        def _opt(key: str) -> str | None:
            value = source.get(key)
            return None if value is None else str(value)

        return compute_canonical_request_hash(
            symbol=self._resolve_symbol(request),
            account_id=self._evidence.account_id,
            side=str(source.get("side", "")),
            volume=str(source.get("volume", "")),
            price=_opt("price"),
            sl=_opt("sl"),
            tp=_opt("tp"),
            route=request.route.value,
            strategy_id=self._evidence.strategy_id,
        )

    def _turbulence_step(self, request: TradingRequestEnvelope) -> GateStepResult:
        """Feed the quote mid-price into the turbulence monitor (gate 8)."""
        logger.info("Evaluating market turbulence gate for {}.", request.request_id)
        quote = request.quote_snapshot
        if quote is None:
            return blocked_step(
                gate=GateName.MARKET_TURBULENCE,
                reason_code="VALIDATION_FAILED",
                message="A live mutation requires a quote snapshot.",
            )
        mid_price = (quote.bid + quote.ask) / Decimal(2)
        return self._turbulence_monitor.observe(
            symbol=self._resolve_symbol(request), mid_price=mid_price
        )

    def _broker_readiness_step(self) -> GateStepResult:
        """Adapt the raising ``validate_broker_readiness`` to a step (gate 9)."""
        logger.info("Evaluating broker readiness gate.")
        try:
            validate_broker_readiness(evidence=self._evidence.broker_readiness)
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.BROKER_READINESS,
                reason_code=exc.code,
                message=str(exc),
            )
        return passed_step(gate=GateName.BROKER_READINESS)

    def _clock_drift_step(self) -> GateStepResult:
        """Adapt the raising ``validate_clock_drift`` to a step (gate 10)."""
        logger.info("Evaluating clock drift gate.")
        try:
            validate_clock_drift(evidence=self._evidence.clock_drift)
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.CLOCK_DRIFT,
                reason_code=exc.code,
                message=str(exc),
            )
        return passed_step(gate=GateName.CLOCK_DRIFT)

    def _idempotency_step(self, request: TradingRequestEnvelope) -> GateStepResult:
        """Reserve the idempotency key before any mutation (gate 11)."""
        logger.info("Evaluating idempotency gate for {}.", request.request_id)
        evidence = self._evidence
        if not evidence.idempotency_key:
            return passed_step(
                gate=GateName.IDEMPOTENCY,
                message="No idempotency key supplied; reservation skipped.",
            )
        expires_at = evidence.idempotency_expires_at or self._clock.now_utc()
        try:
            outcome = self._idempotency_store.reserve(
                route=request.route,
                tenant_id=self._tenant_id,
                key=evidence.idempotency_key,
                material_hash=evidence.idempotency_material_hash,
                expires_at=expires_at,
            )
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.IDEMPOTENCY,
                reason_code=exc.code,
                message=str(exc),
            )
        decision = str(outcome.get("decision", "reserved"))
        if decision != "reserved":
            return blocked_step(
                gate=GateName.IDEMPOTENCY,
                reason_code="LIVE_IDEMPOTENCY_CONFLICT",
                message=f"Idempotency key is already {decision}.",
            )
        evidence._reserved = True  # noqa: SLF001 -- own dataclass, single writer.
        return passed_step(gate=GateName.IDEMPOTENCY)

    def _concurrency_step(self, request: TradingRequestEnvelope) -> GateStepResult:
        """Acquire the per-(account, symbol) concurrency lease (gate 12)."""
        logger.info("Evaluating concurrency lease gate for {}.", request.request_id)
        symbol = self._resolve_symbol(request)
        try:
            acquired = self._lock_manager.acquire_lock(
                self._evidence.account_id, symbol
            )
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.CONCURRENCY_LEASE,
                reason_code=exc.code,
                message=str(exc),
            )
        if not acquired:
            return blocked_step(
                gate=GateName.CONCURRENCY_LEASE,
                reason_code="QUEUE_FULL",
                message=f"Could not acquire concurrency lease for {symbol}.",
            )
        self._lease_held = True
        return passed_step(gate=GateName.CONCURRENCY_LEASE)

    def _audit_step(self, request: TradingRequestEnvelope) -> GateStepResult:
        """Persist the pre-mutation audit record, blocking on failure (gate 14)."""
        logger.info("Evaluating pre-mutation audit gate for {}.", request.request_id)
        try:
            self.audit_ref = record_pre_mutation_audit(
                audit_sink=self._audit_sink,
                event={
                    "request_id": request.request_id,
                    "correlation_id": request.correlation_id,
                    "action": request.action.value,
                    "route": request.route.value,
                    "symbol": request.symbol,
                    "account_id": self._evidence.account_id,
                    "strategy_id": self._evidence.strategy_id,
                },
                recorded_at=self._clock.now_utc(),
            )
        except TradingMappedError as exc:
            return blocked_step(
                gate=GateName.AUDIT_PRE_RECORD,
                reason_code=exc.code,
                message=str(exc),
            )
        return passed_step(gate=GateName.AUDIT_PRE_RECORD)

    def _adapter_permission_step(
        self, request: TradingRequestEnvelope
    ) -> GateStepResult:
        """Validate broker capability for the requested order (gate 15).

        A full position close packages ``volume=None`` and a market order
        packages ``price=None``; both are absent, not zero-valued. The quote
        supplies the reference price when the payload omits one.
        """
        logger.info("Evaluating adapter permission gate for {}.", request.request_id)
        payload = request.payload
        quote = request.quote_snapshot
        source = payload.get("intent")
        if not isinstance(source, dict):
            source = payload

        resolved_price = _optional_decimal(source.get("price"))
        if resolved_price is None:
            resolved_price = quote.ask if quote is not None else Decimal(0)

        return evaluate_adapter_permission_gate(
            profile=self._evidence.capability_profile,
            order_type=self._evidence.order_type,
            filling_mode=self._evidence.filling_mode,
            price=resolved_price,
            volume=_optional_decimal(source.get("volume")) or Decimal(0),
        )

    def _dispatch_step(
        self, request: TradingRequestEnvelope, outcome: DispatchOutcome
    ) -> GateStepResult:
        """Issue the broker mutation under a hard timeout (gate 16).

        A timeout is not a failure with a known outcome -- the order may have
        reached the broker. It is classified as an unknown outcome and triggers
        a forced reconciliation pass, matching ``trader``'s behavior.
        """
        logger.info("Dispatching request {} to broker.", request.request_id)
        payload = request.to_broker_dispatch_payload()
        dispatch_callable = self._dispatch_callable_factory(payload, request.request_id)

        self.coordinator.in_flight.increment()
        outcome.attempted = True
        try:
            future = self._dispatch_executor.submit(dispatch_callable)
            result = future.result(timeout=self._dispatch_timeout_seconds)
        except concurrent.futures.TimeoutError:
            outcome.unknown_outcome = True
            logger.warning(
                "Broker call for {} timed out after {}s; unknown outcome.",
                request.request_id,
                self._dispatch_timeout_seconds,
            )
            self._force_reconciliation()
            return blocked_step(
                gate=GateName.DISPATCH,
                reason_code="LIVE_UNKNOWN_OUTCOME",
                message=(
                    f"Broker call timed out after {self._dispatch_timeout_seconds}s; "
                    "outcome unknown and flagged for reconciliation."
                ),
            )
        except Exception as exc:  # noqa: BLE001 -- mapped to a public error below.
            outcome.error = map_exception_to_trading_error(
                exc,
                request_id=request.request_id,
                correlation_id=request.correlation_id,
            )
            logger.warning(
                "Broker dispatch for {} raised: {}.", request.request_id, exc
            )
            return blocked_step(
                gate=GateName.DISPATCH,
                reason_code=outcome.error.code,
                message=outcome.error.details,
            )
        finally:
            self.coordinator.in_flight.decrement()

        outcome.result = result
        if not is_success_retcode(result.retcode):
            logger.info(
                "Broker rejected request {} with retcode {}.",
                request.request_id,
                result.retcode,
            )
            return blocked_step(
                gate=GateName.DISPATCH,
                reason_code="LIVE_BROKER_REJECTED",
                message=f"Broker rejected the request (retcode {result.retcode}).",
            )
        return passed_step(gate=GateName.DISPATCH)

    def _force_reconciliation(self) -> None:
        """Run a forced reconciliation pass after an unknown outcome."""
        hook = self._reconciliation_hook
        try:
            if hook is not None:
                hook()
            else:
                snapshot_broker_state()
        except Exception as exc:  # noqa: BLE001 -- reconciliation is best-effort here.
            logger.error("Forced reconciliation failed: {}.", exc)

    # ------------------------------------------------------------------
    # Pipeline assembly
    # ------------------------------------------------------------------

    def _build_steps(
        self, request: TradingRequestEnvelope, outcome: DispatchOutcome
    ) -> tuple[GateStep, ...]:
        """Assemble all 16 gates in canonical ``GateName`` order.

        Args:
            request: Packaged trading request envelope.
            outcome: Mutable holder receiving the dispatch result.

        Returns:
            tuple[GateStep, ...]: Ordered pipeline steps.
        """
        symbol = self._resolve_symbol(request)

        def _session_step() -> GateStepResult:
            base = self._session_status_step()
            if base.status.value != "passed":
                return base
            halted = self._symbol_halted_step(symbol)
            return halted or base

        return (
            (
                GateName.LOCAL_SCHEMA_VALIDATION,
                lambda: self._local_schema_step(request),
            ),
            (
                GateName.COMPLIANCE,
                lambda: evaluate_compliance_gate(
                    evidence=self._evidence.compliance_evidence,
                    symbol=request.symbol,
                ),
            ),
            (
                GateName.PROMOTION_STAGE,
                lambda: evaluate_promotion_stage_gate(request=request),
            ),
            (GateName.SESSION_STATUS, _session_step),
            (GateName.KILL_SWITCH, lambda: self._kill_switch_step(request)),
            (GateName.OPERATOR_APPROVAL, lambda: self._operator_approval_step(request)),
            (GateName.RISK_DECISION, self._risk_evaluator),
            (GateName.MARKET_TURBULENCE, lambda: self._turbulence_step(request)),
            (GateName.BROKER_READINESS, self._broker_readiness_step),
            (GateName.CLOCK_DRIFT, self._clock_drift_step),
            (GateName.IDEMPOTENCY, lambda: self._idempotency_step(request)),
            (GateName.CONCURRENCY_LEASE, lambda: self._concurrency_step(request)),
            (
                GateName.RECONCILIATION_AUTHORITY,
                lambda: evaluate_reconciliation_authority_gate(
                    guard=self._authority_guard,
                    account_id=self._evidence.account_id,
                    symbol=symbol,
                ),
            ),
            (GateName.AUDIT_PRE_RECORD, lambda: self._audit_step(request)),
            (
                GateName.ADAPTER_PERMISSION,
                lambda: self._adapter_permission_step(request),
            ),
            (GateName.DISPATCH, lambda: self._dispatch_step(request, outcome)),
        )

    def evaluate(self, request: TradingRequestEnvelope) -> TradingResponseEnvelope:
        """Run the 16-step live gate pipeline and dispatch when every gate passes.

        Args:
            request: Packaged trading request envelope.

        Returns:
            TradingResponseEnvelope: Confirmed, rejected, blocked, or
            unknown-outcome response.
        """
        logger.info("Evaluating live gate pipeline for {}.", request.request_id)
        outcome = DispatchOutcome()
        self._lease_held = False
        deadline = compute_effective_deadline(
            request=request,
            clock=self._clock,
            default_budget_ms=self._default_budget_ms,
        )
        try:
            decision = run_gate_pipeline(
                steps=self._build_steps(request, outcome),
                clock=self._clock,
                deadline=deadline,
                quote_snapshot=request.quote_snapshot,
                quote_ttl_ms=self._quote_ttl_ms,
            )
        finally:
            self._release_lease(request)

        if decision.status is TradingStatus.ACCEPTED and outcome.result is not None:
            return self._confirmed_envelope(request, decision, outcome)
        return self._blocked_envelope(request, decision, outcome)

    def _release_lease(self, request: TradingRequestEnvelope) -> None:
        """Release the concurrency lease when this evaluation acquired one."""
        if getattr(self, "_lease_held", False):
            symbol = self._resolve_symbol(request)
            self._lock_manager.release_lock(self._evidence.account_id, symbol)
            self._lease_held = False
            logger.debug("Released concurrency lease for {}.", symbol)

    def _finalize(
        self, request: TradingRequestEnvelope, outcome: DispatchOutcome
    ) -> None:
        """Persist order state and complete the idempotency lease."""
        result = outcome.result
        if result is None:
            return
        order_state: JsonObject = {
            "order_id": result.order or result.deal or request.request_id,
            "symbol": request.symbol,
            "retcode": result.retcode,
            "provider": result.provider,
            "total_volume": str(result.volume) if result.volume is not None else "0",
            "vwap": str(result.price) if result.price is not None else "0",
        }
        try:
            finalize_dispatch_outcome(
                trade_store=self._trade_store,
                route=request.route,
                tenant_id=self._tenant_id,
                order_state=order_state,
                expected_version=None,
                idempotency_store=self._idempotency_store,
                idempotency_key=self._evidence.idempotency_key,
                idempotency_outcome=result.model_dump(mode="json"),
                completed_at=self._clock.now_utc(),
            )
        except Exception as exc:  # noqa: BLE001 -- finalization must not mask a fill.
            logger.error(
                "Post-dispatch finalization failed for {}: {}.",
                request.request_id,
                exc,
            )

    def _confirmed_envelope(
        self,
        request: TradingRequestEnvelope,
        decision: object,
        outcome: DispatchOutcome,
    ) -> TradingResponseEnvelope:
        """Build the success envelope for a confirmed broker mutation."""
        if self._evidence.idempotency_key and self._evidence._reserved:  # noqa: SLF001
            self._finalize(request, outcome)
        result = outcome.result
        logger.info("Live dispatch confirmed for {}.", request.request_id)
        return TradingResponseEnvelope(
            status=TradingStatus.SUCCESS,
            message="Broker mutation confirmed.",
            data={
                "result": result.model_dump(mode="json") if result else {},
                "gate_decision": _decision_payload(decision),
            },
            metadata=TradingMetadata(
                writes=True, trades=True, requires_network=True, reads=True
            ),
            route=request.route,
            action=request.action,
            side_effect_mode=SideEffectMode.BROKER_MUTATION_CONFIRMED,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            audit_ref=self.audit_ref,
        )

    def _blocked_envelope(
        self,
        request: TradingRequestEnvelope,
        decision: object,
        outcome: DispatchOutcome,
    ) -> TradingResponseEnvelope:
        """Build the envelope for a blocked, rejected, or unknown outcome."""
        error_code = getattr(decision, "error_code", None) or "LIVE_GATE_FAILED"
        blocked_at = getattr(decision, "blocked_at_gate", None)

        if outcome.unknown_outcome:
            side_effect = SideEffectMode.UNKNOWN_OUTCOME
            retry_safety = RetrySafety.RETRY_AFTER_RECONCILIATION
            status = TradingStatus.ERROR
            message = "Broker outcome unknown; reconciliation required."
        elif outcome.attempted and outcome.result is not None:
            side_effect = SideEffectMode.BROKER_MUTATION_REJECTED
            retry_safety = RetrySafety.SAFE_TO_RETRY
            status = TradingStatus.REJECTED
            message = "Broker rejected the trade request."
        elif outcome.attempted:
            side_effect = SideEffectMode.BROKER_MUTATION_ATTEMPTED
            retry_safety = RetrySafety.RETRY_AFTER_RECONCILIATION
            status = TradingStatus.ERROR
            message = "Broker dispatch failed."
        else:
            side_effect = SideEffectMode.NONE
            retry_safety = RetrySafety.DO_NOT_RETRY
            status = TradingStatus.BLOCKED
            gate_label = blocked_at.value if blocked_at is not None else "unknown"
            message = f"Blocked at gate {gate_label}."

        logger.info(
            "Live pipeline for {} resolved to {} ({}).",
            request.request_id,
            status.value,
            error_code,
        )
        return TradingResponseEnvelope(
            status=status,
            message=message,
            data={"gate_decision": _decision_payload(decision)},
            error=outcome.error or TradingError(code=error_code, details=message),
            metadata=TradingMetadata(
                writes=outcome.attempted,
                trades=outcome.attempted,
                requires_network=outcome.attempted,
                reads=True,
            ),
            route=request.route,
            action=request.action,
            side_effect_mode=side_effect,
            retry_safety=retry_safety,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            audit_ref=self.audit_ref,
        )


def _decision_payload(decision: object) -> JsonObject:
    """Render a gate pipeline decision as a JSON-safe payload."""
    steps = getattr(decision, "steps", ())
    blocked_at = getattr(decision, "blocked_at_gate", None)
    return {
        "blocked_at_gate": blocked_at.value if blocked_at is not None else None,
        "error_code": getattr(decision, "error_code", None),
        "steps": [
            {
                "gate": step.gate.value,
                "status": step.status.value,
                "reason_code": step.reason_code,
            }
            for step in steps
        ],
    }


def build_live_gate_pipeline(
    *,
    clock: Clock,
    tenant_id: str,
    evidence: LiveGateEvidence,
    policy_matrix: PolicyMatrix,
    session_manager: SessionManager,
    turbulence_monitor: MarketTurbulenceMonitor,
    idempotency_store: IdempotencyStore,
    lock_manager: ConcurrencyLockManager,
    authority_guard: AuthorityAndRetryGuard,
    audit_sink: AuditSink,
    trade_store: TradeStore,
    dispatch_executor: AsyncDispatchExecutor,
    risk_evaluator: Callable[[], GateStepResult],
    dispatch_callable_factory: Callable[
        [JsonObject, str], Callable[[], NormalizedTradeResult]
    ]
    | None = None,
    **kwargs: object,
) -> LiveGatePipelineImpl:
    """Build a live gate pipeline wired to the active broker by default.

    Args:
        clock: Injected clock.
        tenant_id: Tenant or session namespace.
        evidence: Caller-supplied evidence bundle.
        policy_matrix: Governed-action policy matrix.
        session_manager: Live session state authority.
        turbulence_monitor: Market turbulence monitor.
        idempotency_store: Idempotency reservation store.
        lock_manager: Concurrency lock manager.
        authority_guard: Reconciliation authority guard.
        audit_sink: Pre-mutation audit sink.
        trade_store: Trade projection store.
        dispatch_executor: Executor running the broker dispatch off-thread.
        risk_evaluator: RISK_DECISION evaluator; no default by design.
        dispatch_callable_factory: Override for the broker dispatch binding.
            Defaults to the real broker boundary.
        **kwargs: Forwarded to :class:`LiveGatePipelineImpl`.

    Returns:
        LiveGatePipelineImpl: Configured pipeline.
    """
    if dispatch_callable_factory is None:
        from app.services.trading.execution.broker_dispatch import (
            build_broker_dispatch_callable,
        )

        def dispatch_callable_factory(
            payload: JsonObject, request_id: str
        ) -> Callable[[], NormalizedTradeResult]:
            return build_broker_dispatch_callable(
                payload=payload, request_id=request_id
            )

    return LiveGatePipelineImpl(
        clock=clock,
        tenant_id=tenant_id,
        evidence=evidence,
        policy_matrix=policy_matrix,
        session_manager=session_manager,
        turbulence_monitor=turbulence_monitor,
        idempotency_store=idempotency_store,
        lock_manager=lock_manager,
        authority_guard=authority_guard,
        audit_sink=audit_sink,
        trade_store=trade_store,
        dispatch_executor=dispatch_executor,
        dispatch_callable_factory=dispatch_callable_factory,
        risk_evaluator=risk_evaluator,
        **kwargs,  # type: ignore[arg-type]
    )


__all__ = [
    "DEFAULT_DISPATCH_TIMEOUT_SECONDS",
    "DEFAULT_GATE_BUDGET_MS",
    "RISK_PASSTHROUGH_MESSAGE",
    "DispatchOutcome",
    "LiveGateEvidence",
    "LiveGatePipelineImpl",
    "build_live_gate_pipeline",
    "passthrough_risk_evaluator",
]
