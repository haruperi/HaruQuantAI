# ruff: noqa: E501, BLE001, E402, PLW0603, ARG002
"""Unified usage example for generic Trade classes working with MT5 and cTrader."""

import sys
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.brokers import get_broker_module
from app.services.trader import Trade
from app.services.trading import (
    AccountInfo,
    AllocationVector,
    DealInfo,
    FixExecutionState,
    HistoryOrderInfo,
    JsonObject,
    MutationCapability,
    NormalizedTradeResult,
    OrderInfo,
    PositionInfo,
    PromotionStage,
    QuoteSnapshot,
    SymbolInfo,
    TerminalInfo,
    TradingAction,
    TradingRequestEnvelope,
    TradingRoute,
    TradingStatus,
    get_trading_public_catalog,
)
from app.services.trading.actions import (
    AccountMarginContext,
    DailyRailState,
    DefenseInDepthRailLimits,
    OrderValidationContext,
    SymbolTradingConstraints,
    TradingActionDependencies,
    buy,
    flatten_symbol,
    pause_strategy,
    trigger_symbol_kill_switch,
)
from app.services.trading.config import (
    NotificationChannel,
    NotificationConfig,
    build_config_change_event,
    build_notification_payload,
    load_trading_config,
)
from app.services.trading.config.models import RateLimitSettings
from app.services.trading.execution import (
    AmendmentKind,
    BrokerCapabilityProfile,
    ExecutionCoordinator,
    LifecycleKind,
    MultiLegExecutionCoordinator,
    OcoWatchdog,
    ProviderRateLimiterRegistry,
    TransactionCostFacts,
    apply_execution_report,
    begin_non_atomic_modify,
    build_client_order_id_mapping,
    build_execution_quality_event,
    build_trading_report,
    capture_transaction_cost,
    classify_broker_initiated_event,
    classify_broker_outcome,
    classify_corporate_action,
    compare_shadow_fill,
    evaluate_amendment,
    generate_client_order_id,
    initialize_transition_record,
    normalize_broker_response,
    record_cancel_confirmed,
    record_cancel_dispatched,
    record_replace_dispatched,
    record_shadow_intent,
    requires_cancel_on_disconnect_failsafe,
    resolve_replace_outcome,
    validate_broker_capabilities,
)
from app.services.trading.gates import (
    ApprovalScope,
    BrokerReadinessEvidence,
    ClockDriftEvidence,
    ComplianceEvidence,
    KillSwitchScope,
    KillSwitchState,
    MarketTurbulenceMonitor,
    OperatorApprovalToken,
    PolicyMatrix,
    PolicyMatrixEntry,
    compute_canonical_request_hash,
    evaluate_adapter_permission_gate,
    evaluate_compliance_gate,
    evaluate_kill_switches,
    record_pre_mutation_audit,
    resolve_policy,
    run_gate_pipeline,
    run_live_readiness_dry_run,
    validate_operator_approval,
)
from app.services.trading.gates._common import GateName
from app.services.trading.gates.pipeline import GatePipelineDecision
from app.services.trading.monitoring import (
    HeartbeatEmitter,
    MonitoringService,
    OperationalSignalsManager,
)
from app.services.trading.reconciliation import (
    AuthorityAndRetryGuard,
    ReconciliationService,
    evaluate_reconciliation_authority_gate,
)
from app.services.trading.security import (
    WriteAheadDeadLetterQueue,
    map_exception_to_trading_error,
    redact_for_boundary,
)
from app.services.trading.promotion import (
    PROMOTION_SEQUENCE,
    ROUTE_CAPABILITY_MATRIX,
    compute_canonical_promotion_hash,
    evaluate_promotion_stage_gate,
    validate_preactivation_conditions,
    validate_promotion_transition,
    validate_sim_metadata_lookup,
    validate_route_stage_capability,
)
from app.services.trading.runtime import (
    SessionManager,
    SessionState,
    OperationalMode,
    ConcurrencyLockManager,
    CostController,
    SignalProcessor,
)
from app.services.trading.state import (
    RNG,
    AppendOnlyEventJournal,
    Clock,
    EncryptionProvider,
    IdempotencyMaterial,
    JournalBuildMetadata,
    JsonlIdempotencyStore,
)
from app.utils.settings import settings

# Shared state across trading examples
trading_symbol = "GBPUSD"
pos_ticket = 0
ord_ticket = 0
buy_price = 0.0
limit_price = 0.0
used_filling_mode = 0


class ExampleClock:
    """Usage-example deterministic clock."""

    def now_utc(self) -> datetime:
        """Return a deterministic UTC timestamp."""
        return datetime(2026, 7, 9, 10, 0, tzinfo=UTC)

    def now_ptp(self) -> datetime:
        """Return a deterministic PTP-aligned timestamp."""
        return datetime(2026, 7, 9, 10, 0, tzinfo=UTC)

    def monotonic(self) -> float:
        """Return deterministic elapsed time."""
        return 10.0


class ExampleRNG:
    """Usage-example deterministic pseudo-random generator."""

    def random(self) -> float:
        """Return deterministic pseudo-random draw."""
        return 0.25

    def randint(self, lower_inclusive: int, upper_inclusive: int) -> int:
        """Return deterministic pseudo-random integer."""
        return lower_inclusive + (upper_inclusive - lower_inclusive) // 2


class ExampleEncryptionProvider:
    """Usage-example deterministic encryption provider."""

    def encrypt(self, plaintext: str) -> str:
        """Encrypt deterministic plaintext for usage output."""
        return f"enc:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt deterministic ciphertext for usage output."""
        return ciphertext.removeprefix("enc:")

    def sign(self, payload: str) -> str:
        """Return a deterministic detached signature."""
        return f"sig:{payload}"


def example_01_contracts() -> None:
    """Demonstrate creating a broker-independent trading request envelope."""
    print("\n" + "=" * 100)
    print("--- 0. Trading Runtime Contracts ---")
    print("=" * 100)

    request = TradingRequestEnvelope(
        route=TradingRoute.LIVE,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="usage-trd-001",
        correlation_id="usage-corr-001",
        symbol="EURUSD",
        allocation_vector=AllocationVector(weights={"child-a": Decimal("1.0")}),
        quote_snapshot=QuoteSnapshot(
            symbol="EURUSD",
            bid=Decimal("1.1000"),
            ask=Decimal("1.1002"),
            spread=Decimal("0.0002"),
            timestamp="2026-07-09T10:00:00Z",
            source="usage-example",
            freshness_age_ms=20,
            wire_timestamp="2026-07-09T10:00:00.000001Z",
        ),
    )
    catalog = get_trading_public_catalog()

    print(f"Request route:      {request.route.value}")
    print(f"Request action:     {request.action.value}")
    if request.quote_snapshot is not None:
        print(f"Quote source:       {request.quote_snapshot.source}")
    print(f"Registered tools:   {[tool.name for tool in catalog]}")


def example_02_state_ports() -> None:
    """Demonstrate injected Clock and RNG port conformance."""
    print("\n" + "=" * 100)
    print("--- 0. Trading Runtime State Ports ---")
    print("=" * 100)

    clock: Clock = ExampleClock()
    rng: RNG = ExampleRNG()

    print(f"UTC clock:          {clock.now_utc().isoformat()}")
    print(f"PTP clock:          {clock.now_ptp().isoformat()}")
    print(f"Monotonic:          {clock.monotonic()}")
    print(f"Random draw:        {rng.random()}")
    print(f"Random int:         {rng.randint(1, 5)}")


def example_03_configurations_security_controls() -> None:
    """Demonstrate config loading, hashing, and notification redaction."""
    print("\n" + "=" * 100)
    print("--- 3. Trading Runtime Configuration & Security Controls ---")
    print("=" * 100)

    config = load_trading_config(
        {
            "config_version": "1.0.0",
            "active_broker": "mt5",
            "store_targets": {
                "trade_store_ref": "store://trade",
                "state_store_ref": "store://state",
                "audit_sink_ref": "store://audit",
                "idempotency_store_ref": "store://idempotency",
                "event_journal_ref": "store://journal",
            },
            "secret_references": {
                "broker_credentials": {"reference": "vault://broker"},
                "database_credentials": {"reference": "vault://database"},
            },
        }
    )
    event = build_config_change_event(
        config=config,
        actor="usage-operator",
        effective_at="2026-07-09T10:00:00Z",
    )
    notifications = NotificationConfig(
        channels=(
            NotificationChannel(
                name="ops",
                kind="email",
                approved=True,
                target_ref="notify://ops",
            ),
        )
    )
    payload = build_notification_payload(
        config=notifications,
        channel_name="ops",
        event_type="config_loaded",
        payload={"api_key": "abcdefabcdefabcdefabcdefabcdef12", "status": "ok"},
    )

    print(f"Live side effect:   {config.live_mutation_side_effect().value}")
    print(f"Config hash:        {event.config_hash}")
    print(f"Redacted secret:    {event.redacted_config['secret_references']}")
    print(f"Notify payload:     {payload['payload']}")


def example_04_security_boundaries_error_redaction() -> None:
    """Demonstrate public error mapping and write-ahead DLQ redaction."""
    print("\n" + "=" * 100)
    print("--- 3. Trading Security Boundaries & Error Redaction ---")
    print("=" * 100)

    mapped_error = map_exception_to_trading_error(
        TimeoutError("broker timeout token=abcdefabcdefabcdefabcdefabcdef12"),
        request_id="usage-trd-004",
        correlation_id="usage-corr-004",
        provider="mt5",
    )
    boundary = redact_for_boundary(
        {
            "event": "broker_audit_failure",
            "account": {"login": "123456", "password": "raw-password"},
            "authorization": "Bearer abcdefabcdefabcdefabcdefabcdef12",
        },
        blocked_live_scopes=("strategy:example",),
        alert_message="critical broker payload moved to DLQ",
    )
    dlq_path = Path("build/trading_usage_dlq.jsonl")
    manual_path = Path("build/trading_usage_manual_dlq.jsonl")
    dlq = WriteAheadDeadLetterQueue(
        path=dlq_path,
        manual_review_path=manual_path,
        clock=ExampleClock(),
        max_retries=2,
    )
    write_result = dlq.write_failed_event(
        source="usage",
        reason="audit persistence failed password=hidden",
        payload=boundary.payload,
        affected_live_scopes=boundary.blocked_live_scopes,
    )

    print(f"Mapped error:       {mapped_error.code}")
    print(f"Error details:      {mapped_error.details}")
    print(f"Redacted payload:   {boundary.payload}")
    print(f"DLQ event:          {write_result.record.event_id}")
    print(f"Blocked scopes:     {write_result.blocked_live_scopes}")


def example_05_persistence_implementations() -> None:
    """Demonstrate idempotency leases and append-only journal replay."""
    print("\n" + "=" * 100)
    print("--- 4. Trading Persistence Implementations ---")
    print("=" * 100)

    clock = ExampleClock()
    encryption: EncryptionProvider = ExampleEncryptionProvider()
    material = IdempotencyMaterial(
        account_id="usage-account",
        strategy_id="usage-strategy",
        route=TradingRoute.PAPER,
        promotion_stage=PromotionStage.PAPER_TRADING.value,
        broker="mt5",
        symbol="EURUSD",
        action=TradingAction.SUBMIT_ORDER,
        side="buy",
        volume="0.10",
        price="1.1000",
    )
    store = JsonlIdempotencyStore(
        path=Path("build/trading_usage_idempotency.jsonl"),
        clock=clock,
    )
    reservation = store.reserve(
        route=TradingRoute.PAPER,
        tenant_id="usage-tenant",
        material=material,
        ttl=timedelta(minutes=5),
    )
    journal = AppendOnlyEventJournal(
        path=Path("build/trading_usage_journal.jsonl"),
        snapshot_path=Path("build/trading_usage_snapshots.jsonl"),
        signature_path=Path("build/trading_usage_signatures.jsonl"),
        clock=clock,
        encryption_provider=encryption,
        build_metadata=JournalBuildMetadata(
            software_version="usage-1.0.0",
            vcs_commit_hash="usage-commit",
            dirty_tree=False,
            active_config_hash="usage-config-hash",
        ),
    )
    event = journal.append_event(
        event_type="TradingCommandAccepted",
        request_id="usage-trd-005",
        correlation_id="usage-corr-005",
        route=TradingRoute.PAPER,
        account_id="usage-account",
        symbol="EURUSD",
        actor="usage",
        payload={"idempotency_key": reservation.record.key},
    )
    snapshot = journal.write_snapshot(
        route=TradingRoute.PAPER,
        account_id="usage-account",
        state={"orders": [], "positions": []},
    )
    seal = journal.seal_segment()

    print(f"Reservation:        {reservation.decision.value}")
    print(f"Idempotency key:    {reservation.record.key}")
    print(f"Journal sequence:   {event.sequence_id}")
    print(f"Snapshot sequence:  {snapshot.sequence_id}")
    print(f"Segment signature:  {seal.signature[:24]}...")


def example_06_read_only_info_facades() -> None:
    """Demonstrate read-only MQL5-compatible information facades."""
    print("\n" + "=" * 100)
    print("--- 5. Trading Read-Only Info Facades ---")
    print("=" * 100)

    terminal = TerminalInfo()
    account = AccountInfo()
    symbol = SymbolInfo("EURUSD")
    order = OrderInfo()
    position = PositionInfo()
    deal = DealInfo()
    history = HistoryOrderInfo()

    print(f"Terminal connected: {terminal.connected()}")
    print(f"Account balance:    {account.balance():.2f}")
    print(f"Account leverage:   {account.leverage()}")
    print(f"Symbol refreshed:   {symbol.refresh()}")
    print(f"Symbol tick size:   {symbol.tick_size()}")
    print(f"Symbol min/max vol: {symbol.volume_min()} / {symbol.volume_max()}")
    print(f"Order ticket:       {order.ticket()}")
    print(f"Position ticket:    {position.ticket()}")
    print(f"Deal ticket:        {deal.ticket()}")
    print(f"History ticket:     {history.ticket()}")
    print(f"Redacted account:   {account.payload()}")


class ExampleIdempotencyStore:
    """Usage-example in-memory idempotency store port."""

    def __init__(self) -> None:
        """Initialize the empty in-memory reservation table."""
        self._seen: set[str] = set()

    def reserve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        material_hash: str,
        expires_at: datetime,
    ) -> JsonObject:
        """Reserve a key, reporting whether it was already seen."""
        first = key not in self._seen
        self._seen.add(key)
        return {"decision": "reserved" if first else "duplicate"}

    def resolve(self, **_: object) -> JsonObject | None:
        """Return no cached resolution for this usage-example double."""
        return None

    def complete(self, **_: object) -> None:
        """No-op completion for this usage-example double."""
        return


class ExampleEventJournal:
    """Usage-example in-memory append-only event journal port."""

    def __init__(self) -> None:
        """Initialize the empty in-memory event list."""
        self.events: list[JsonObject] = []

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Append an event and return a synthetic reference."""
        self.events.append(event)
        return f"usage-journal-{len(self.events)}"

    def scan_unresolved(self, **_: object) -> tuple[JsonObject, ...]:
        """Return no unresolved entries for this usage-example double."""
        return ()


def example_07_actions_and_validation() -> None:
    """Demonstrate validated order, control, and emergency action primitives."""
    print("\n" + "=" * 100)
    print("--- 6. Trading Action Primitives & Validation ---")
    print("=" * 100)

    constraints = SymbolTradingConstraints(
        symbol=trading_symbol,
        digits=5,
        volume_min=Decimal("0.01"),
        volume_max=Decimal(100),
        volume_step=Decimal("0.01"),
        tick_size=Decimal("0.00001"),
        min_stop_distance=Decimal("0.0005"),
        contract_size=Decimal(100000),
        quote_currency="USD",
    )
    account = AccountMarginContext(
        account_currency="USD", leverage=100, free_margin=Decimal(10000)
    )
    context = OrderValidationContext(
        route=TradingRoute.SIM,
        reference_price=Decimal("1.10000"),
        constraints=constraints,
        account_margin=account,
        fat_finger_ceiling=Decimal(50000),
        rail_limits=DefenseInDepthRailLimits(
            max_mutation_attempts_per_window=10,
            window_seconds=60,
            max_open_positions=5,
            daily_notional_ceiling=Decimal(1000000),
        ),
        rail_state=DailyRailState(
            mutation_attempts_in_window=0,
            open_positions_count=0,
            cumulative_daily_notional=Decimal(0),
        ),
    )
    idempotency_store = ExampleIdempotencyStore()
    event_journal = ExampleEventJournal()
    deps = TradingActionDependencies(
        clock=ExampleClock(),
        rng=ExampleRNG(),
        tenant_id="usage-tenant",
        idempotency_store=idempotency_store,
        event_journal=event_journal,
    )

    buy_response = buy(
        symbol=trading_symbol,
        volume=Decimal("0.10"),
        sl=Decimal("1.09000"),
        tp=Decimal("1.11000"),
        deviation_points=10,
        route=TradingRoute.SIM,
        promotion_stage=PromotionStage.SIMULATION,
        mutation_capability=MutationCapability.PACKAGED_ONLY,
        request_id="usage-action-001",
        correlation_id="usage-corr-006",
        context=context,
        deps=deps,
    )
    pause_response = pause_strategy(
        strategy_id="usage-strategy",
        reason="usage example pause",
        route=TradingRoute.SIM,
        promotion_stage=PromotionStage.SIMULATION,
        mutation_capability=MutationCapability.PACKAGED_ONLY,
        request_id="usage-action-002",
        correlation_id="usage-corr-006",
        deps=deps,
    )
    kill_switch_response = trigger_symbol_kill_switch(
        symbol=trading_symbol,
        reason="usage example incident",
        actor="usage-operator",
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        request_id="usage-action-003",
        correlation_id="usage-corr-006",
        deps=deps,
        idempotency_store=idempotency_store,
        event_journal=event_journal,
    )
    flatten_response = flatten_symbol(
        symbol=trading_symbol,
        route=TradingRoute.SIM,
        promotion_stage=PromotionStage.SIMULATION,
        mutation_capability=MutationCapability.PACKAGED_ONLY,
        request_id="usage-action-004",
        correlation_id="usage-corr-006",
        deps=deps,
    )

    print(
        f"Buy status:          {buy_response.status.value} / {buy_response.side_effect_mode.value}"
    )
    print(f"Pause status:        {pause_response.status.value}")
    print(f"Kill switch status:  {kill_switch_response.status.value}")
    print(f"Kill switch journal: {kill_switch_response.audit_ref}")
    print(f"Flatten status:      {flatten_response.status.value}")


def example_08_execution_primitives() -> None:
    """Demonstrate state machine, response classification, rate limiting,
    capability validation, and shadow comparison execution primitives.
    """
    print("\n" + "=" * 100)
    print("--- 7. Trading Execution Primitives & State Machine ---")
    print("=" * 100)

    record = initialize_transition_record(
        entity_id="usage-order-1", kind=LifecycleKind.ORDER, volume=Decimal("1.0")
    )
    fill_result = apply_execution_report(
        record=record,
        report_state=FixExecutionState.PARTIALLY_FILLED,
        broker_event_id="usage-evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        request_id="usage-exec-001",
        correlation_id="usage-corr-007",
        dedup_window_size=10,
        filled_volume_delta=Decimal("0.40"),
        vwap=Decimal("1.10000"),
    )
    amendment = evaluate_amendment(
        record=fill_result.record,
        expected_state_version=1,
        amendment_kind=AmendmentKind.CANCEL,
    )

    normalized = normalize_broker_response(
        provider="mt5",
        raw_response={
            "retcode": "10009",
            "deal": "9001",
            "volume": "0.40",
            "comment": "stop out",
        },
        request_id="usage-exec-001",
    )
    outcome = classify_broker_outcome(normalized=normalized)
    broker_event = classify_broker_initiated_event(normalized=normalized)
    corporate_action = classify_corporate_action(
        raw_event={
            "action_type": "split",
            "symbol": trading_symbol,
            "ratio": "2",
            "effective_at": "2026-07-09",
        },
    )

    registry = ProviderRateLimiterRegistry(clock=ExampleClock())
    registry.configure_provider(
        provider="mt5",
        settings=RateLimitSettings(max_requests=5, per_seconds=Decimal("1.0"), burst=2),
    )
    acquisitions = [registry.try_acquire(provider="mt5") for _ in range(3)]

    profile = BrokerCapabilityProfile(
        provider="mt5",
        supported_order_types=("market", "limit", "stop"),
        supported_filling_modes=("IOC", "FOK"),
        price_precision_digits=5,
        volume_precision_step=Decimal("0.01"),
        max_requests_per_second=Decimal(10),
        supports_cancel_on_disconnect=False,
    )
    capability_result = validate_broker_capabilities(
        profile=profile,
        order_type="market",
        filling_mode="IOC",
        price=Decimal("1.10000"),
        volume=Decimal("0.10"),
    )
    needs_cod_failsafe = requires_cancel_on_disconnect_failsafe(profile=profile)

    shadow_intent = record_shadow_intent(
        request_id="usage-shadow-001",
        symbol=trading_symbol,
        side="buy",
        volume=Decimal("0.10"),
        expected_price=Decimal("1.10000"),
        recorded_at="2026-07-09T10:00:00Z",
    )
    shadow_comparison = compare_shadow_fill(
        intent=shadow_intent,
        live_reference_price=Decimal("1.10050"),
        expected_balance_after=Decimal("10000.00"),
        live_balance=Decimal("9999.50"),
    )

    print(
        f"Fill version/state:  {fill_result.record.version} / {fill_result.record.state.value}"
    )
    print(
        f"Amendment outcome:   {amendment.outcome.value} / {amendment.retry_safety.value}"
    )
    print(f"Normalized retcode:  {normalized.retcode}")
    print(f"Broker outcome:      {outcome.status.value}")
    print(
        f"Broker event kind:   {broker_event.kind.value} "
        f"critical={broker_event.requires_critical_incident}"
    )
    print(
        f"Corporate action:    {corporate_action.kind.value} ratio={corporate_action.ratio}"
    )
    print(f"Rate limit attempts: {[decision.allowed for decision in acquisitions]}")
    print(
        f"Capability passed:   {capability_result.passed}, needs CoD failsafe={needs_cod_failsafe}"
    )
    print(f"Shadow price drift:  {shadow_comparison.price_drift_bps} bps")


class ExampleAuditSink:
    """Usage-example in-memory audit sink port."""

    def __init__(self) -> None:
        """Initialize the empty in-memory audit event list."""
        self.events: list[JsonObject] = []

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Append an audit event and return a synthetic reference."""
        self.events.append(event)
        return f"usage-audit-{len(self.events)}"

    def flush(self) -> None:
        """No-op flush for this usage-example double."""
        return


class ExampleSyncExecutor:
    """Usage-example synchronous AsyncDispatchExecutor double."""

    def submit(self, dispatch_callable):
        """Run the dispatch callable immediately and wrap it in a Future."""
        from concurrent.futures import Future

        future: Future = Future()
        try:
            result = dispatch_callable()
        except Exception as exc:
            future.set_exception(exc)
        else:
            future.set_result(result)
        return future


def example_09_gates_pipeline() -> None:
    """Demonstrate policy matrix, approval, readiness, kill-switch, audit,
    and the composed 16-step live gate pipeline orchestration.
    """
    print("\n" + "=" * 100)
    print("--- 8. Trading Gate Pipeline & Policy Matrix ---")
    print("=" * 100)

    matrix = PolicyMatrix(
        entries={
            TradingAction.SUBMIT_ORDER: PolicyMatrixEntry(
                action=TradingAction.SUBMIT_ORDER
            ),
            TradingAction.CANCEL_ALL_ORDERS: PolicyMatrixEntry(
                action=TradingAction.CANCEL_ALL_ORDERS,
                emergency_allowed_under_kill_switch=True,
            ),
        }
    )
    policy_entry = resolve_policy(matrix=matrix, action=TradingAction.SUBMIT_ORDER)

    request_hash = compute_canonical_request_hash(
        symbol=trading_symbol,
        account_id="usage-account",
        side="buy",
        volume="0.10",
        price=None,
        sl=None,
        tp=None,
        route="live",
        strategy_id="usage-strategy",
    )
    approval = OperatorApprovalToken(
        approval_id="usage-appr-001",
        operator_id="usage-operator",
        governed_action_id="submit_order",
        scope=ApprovalScope(),
        canonical_request_hash=request_hash,
        issued_at="2026-07-09T09:00:00Z",
        expires_at="2026-07-09T23:00:00Z",
    )
    validate_operator_approval(
        token=approval,
        now=ExampleClock().now_utc(),
        expected_request_hash=request_hash,
        expected_scope=ApprovalScope(),
    )

    kill_switch_evaluation = evaluate_kill_switches(
        switches=(KillSwitchState(scope=KillSwitchScope.GLOBAL, active=False),),
        action=TradingAction.SUBMIT_ORDER,
        policy_entry=policy_entry,
    )

    readiness_result = run_live_readiness_dry_run(
        broker_evidence=BrokerReadinessEvidence(
            connected=True,
            trade_allowed=True,
            account_permissions_ok=True,
            rate_limit_available=True,
        ),
        clock_evidence=ClockDriftEvidence(offset_ms=Decimal(10)),
        symbol_metadata_present=True,
        stores_durable=True,
    )

    audit_sink = ExampleAuditSink()
    audit_ref = record_pre_mutation_audit(
        audit_sink=audit_sink,
        event={"action": "submit_order", "symbol": trading_symbol},
        recorded_at=ExampleClock().now_utc(),
    )

    turbulence_monitor = MarketTurbulenceMonitor(
        window_size=5, velocity_threshold_bps=Decimal(50)
    )
    turbulence_monitor.observe(symbol=trading_symbol, mid_price=Decimal("1.10000"))

    capability_profile = BrokerCapabilityProfile(
        provider="mt5",
        supported_order_types=("market",),
        supported_filling_modes=("IOC",),
        price_precision_digits=5,
        volume_precision_step=Decimal("0.01"),
        max_requests_per_second=Decimal(10),
    )

    clock = ExampleClock()
    steps = (
        (
            GateName.COMPLIANCE,
            lambda: evaluate_compliance_gate(
                evidence=ComplianceEvidence(), symbol=trading_symbol
            ),
        ),
        (
            GateName.MARKET_TURBULENCE,
            lambda: turbulence_monitor.observe(
                symbol=trading_symbol, mid_price=Decimal("1.10010")
            ),
        ),
        (
            GateName.ADAPTER_PERMISSION,
            lambda: evaluate_adapter_permission_gate(
                profile=capability_profile,
                order_type="market",
                filling_mode="IOC",
                price=Decimal("1.10000"),
                volume=Decimal("0.10"),
            ),
        ),
    )
    decision = run_gate_pipeline(
        steps=steps,
        clock=clock,
        deadline=clock.now_utc() + timedelta(seconds=1),
    )

    print(f"Policy entry:        approval_required={policy_entry.requires_approval}")
    print(f"Kill switch check:   blocked={kill_switch_evaluation.blocked}")
    print(f"Readiness dry run:   passed={readiness_result.passed}")
    print(f"Audit reference:     {audit_ref}")
    print(f"Pipeline status:     {decision.status.value}")
    print(f"Pipeline steps:      {[step.gate.value for step in decision.steps]}")


def example_10_execution_coordinator_and_reporting() -> None:
    """Demonstrate asynchronous dispatch coordination, client-order-id
    propagation, OCO/multi-leg watchdogs, non-atomic modify safety, and
    structured trading report / execution-quality event construction.
    """
    print("\n" + "=" * 100)
    print("--- 9. Execution Coordinator & Reporting ---")
    print("=" * 100)

    coordinator = ExecutionCoordinator()
    rng = ExampleRNG()
    client_order_id = generate_client_order_id(request_id="usage-req-010", rng=rng)
    client_order_id_mapping = build_client_order_id_mapping(
        client_order_id=client_order_id,
        comment_max_length=26,
        external_id_max_length=12,
    )

    completions: list[object] = []

    def dispatch_callable() -> NormalizedTradeResult:
        return NormalizedTradeResult(
            retcode="10009", request_id="usage-req-010", provider="mt5"
        )

    accepted = coordinator.dispatch_async(
        request_id="usage-req-010",
        action=TradingAction.SUBMIT_ORDER,
        accepted_at=ExampleClock().now_utc().isoformat(),
        executor=ExampleSyncExecutor(),
        dispatch_callable=dispatch_callable,
        on_complete=completions.append,
    )

    watchdog = OcoWatchdog()
    watchdog.register_group(group_id="usage-oco-1", order_ids=("ord-1", "ord-2"))
    siblings_to_cancel = watchdog.on_execution_report(
        group_id="usage-oco-1", order_id="ord-1", execution_state="Filled"
    )

    multi_leg = MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("0.1"))
    multi_leg.register_legs(group_id="usage-spread-1", leg_order_ids=("leg-1", "leg-2"))
    rollback_decision = multi_leg.on_leg_outcome(
        group_id="usage-spread-1",
        leg_order_id="leg-1",
        rejected=True,
        unfilled_fraction=Decimal(0),
    )

    modify_state = begin_non_atomic_modify(order_id="usage-ord-mod-1")
    modify_state = record_cancel_dispatched(state=modify_state)
    modify_state = record_cancel_confirmed(state=modify_state)
    modify_state = record_replace_dispatched(state=modify_state)
    modify_resolution = resolve_replace_outcome(
        state=modify_state, replace_succeeded=True, reentry_allowed=True
    )

    cost_facts = TransactionCostFacts(commission=Decimal("0.35"), swap=Decimal("0.05"))
    cost_event = capture_transaction_cost(
        order_id="usage-ord-mod-1",
        cost_facts=cost_facts,
        recorded_at=ExampleClock().now_utc().isoformat(),
    )

    quote_snapshot = QuoteSnapshot(
        symbol=trading_symbol,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10020"),
        spread=Decimal("0.00020"),
        timestamp=ExampleClock().now_utc().isoformat(),
        source="mt5",
        freshness_age_ms=5,
    )
    quality_event = build_execution_quality_event(
        order_id="usage-ord-mod-1",
        symbol=trading_symbol,
        quote_snapshot=quote_snapshot,
        executed_price=Decimal("1.10025"),
        decision_price=Decimal("1.10015"),
        side="buy",
        fill_latency_ms=Decimal(85),
        partial_fill_count=0,
        cost_facts=cost_facts,
    )

    report = build_trading_report(
        report_id="usage-report-1",
        generated_at=ExampleClock().now_utc().isoformat(),
        tenant_id="usage-tenant",
        cost_entries=(cost_event,),
    )

    print(f"Client order id:      {client_order_id_mapping.client_order_id}")
    print(f"Broker comment field: {client_order_id_mapping.comment}")
    print(f"Dispatch accepted:    command_id={accepted.command_id}")
    print(f"In-flight after done: {coordinator.in_flight.current()}")
    print(f"OCO siblings to cancel: {siblings_to_cancel}")
    print(f"Multi-leg rollback:   {rollback_decision.rollback_required}")
    print(f"Modify resolution:    {modify_resolution.state.stage.value}")
    print(f"Realized slippage:    {quality_event.realized_slippage_bps} bps")
    print(f"Report cost entries:  {len(report.cost_entries)}")


def example_11_reconciliation() -> None:
    """Demonstrate state reconciliation sync coordination, snapshots comparison,
    and unknown outcome authority lockout guards.
    """
    print("\n" + "=" * 100)
    print("--- 10. State Reconciliation & Authority Guard ---")
    print("=" * 100)

    config = load_trading_config(
        {
            "config_version": "1.0.0",
            "active_broker": "mt5",
            "store_targets": {
                "trade_store_ref": "store://trade",
                "state_store_ref": "store://state",
                "audit_sink_ref": "sink://audit",
                "idempotency_store_ref": "store://idempotency",
                "event_journal_ref": "journal://event",
            },
            "secret_references": {
                "broker_credentials": {"reference": "vault://broker"},
                "database_credentials": {"reference": "vault://db"},
            },
            "reconciliation": {
                "price_drift_threshold": "0.01",
                "volume_drift_threshold": "0.001",
                "balance_drift_threshold": "0.10",
                "margin_drift_threshold": "0.10",
                "orphan_deal_policy": "block",
            },
        }
    )

    class DummyClock:
        def now_utc(self) -> datetime:
            return datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

        def monotonic(self) -> float:
            return 123.45

    class DummyTradeStore:
        def list_order_states(
            self, *, route: TradingRoute, tenant_id: str
        ) -> list[JsonObject]:
            return [
                {
                    "order_id": "ord-1",
                    "symbol": "EURUSD",
                    "state": "NEW",
                    "remaining_volume": "1.0",
                    "vwap": "1.10",
                }
            ]

        def list_position_states(
            self, *, route: TradingRoute, tenant_id: str
        ) -> list[JsonObject]:
            return [
                {
                    "position_id": "pos-1",
                    "symbol": "EURUSD",
                    "volume": "1.5",
                    "vwap": "1.10",
                }
            ]

        def save_position_state(
            self,
            *,
            route: TradingRoute,
            tenant_id: str,
            position_state: JsonObject,
            expected_version: int | None,
        ) -> str:
            return "pos-ref"

    class DummyStateStore:
        def load_state(
            self, *, route: TradingRoute, tenant_id: str, snapshot_id: str
        ) -> JsonObject | None:
            return {"balance": "1000.00", "margin": "200.00"}

    guard = AuthorityAndRetryGuard()
    clock = ExampleClock()
    encryption = ExampleEncryptionProvider()

    journal = AppendOnlyEventJournal(
        path=Path("build/trading_reconciliation_journal.jsonl"),
        snapshot_path=Path("build/trading_reconciliation_snapshots.jsonl"),
        signature_path=Path("build/trading_reconciliation_signatures.jsonl"),
        clock=clock,
        encryption_provider=encryption,
        build_metadata=JournalBuildMetadata(
            software_version="usage-1.0.0",
            vcs_commit_hash="usage-commit",
            dirty_tree=False,
            active_config_hash="usage-config-hash",
        ),
    )

    service = ReconciliationService(
        trade_store=DummyTradeStore(),
        state_store=DummyStateStore(),
        journal=journal,
        authority_guard=guard,
        clock=DummyClock(),
        config=config,
    )

    try:
        report = service.run_reconciliation(
            route=TradingRoute.LIVE,
            tenant_id="tenant-1",
            account_id="acct-1",
            run_type="periodic",
        )
        print(f"Reconciliation run:   status={report.status}")
    except Exception as e:
        print(f"Reconciliation run:   failed ({e})")

    gate_passed_before = evaluate_reconciliation_authority_gate(
        guard=guard, account_id="acct-1", symbol="EURUSD"
    )

    guard.report_stream_gap("acct-1", "EURUSD")
    gate_blocked_after = evaluate_reconciliation_authority_gate(
        guard=guard, account_id="acct-1", symbol="EURUSD"
    )

    guard.resolve_scope("acct-1", "EURUSD")
    gate_passed_after = evaluate_reconciliation_authority_gate(
        guard=guard, account_id="acct-1", symbol="EURUSD"
    )

    print(f"Gate status before gap:  {gate_passed_before.status.value}")
    print(
        f"Gate status after gap:   {gate_blocked_after.status.value} (Reason: {gate_blocked_after.reason_code})"
    )
    print(f"Gate status after clear:  {gate_passed_after.status.value}")


def example_12_monitoring() -> None:
    """Demonstrate Trading Runtime state monitoring and circuit breaker triggers."""
    print("\n" + "=" * 100)
    print("--- 12. State Monitoring & Health Controls ---")
    print("=" * 100)

    config = load_trading_config(
        {
            "config_version": "1.0.0",
            "active_broker": "mt5",
            "store_targets": {
                "trade_store_ref": "store://trade",
                "state_store_ref": "store://state",
                "audit_sink_ref": "sink://audit",
                "idempotency_store_ref": "store://idempotency",
                "event_journal_ref": "journal://event",
            },
            "secret_references": {
                "broker_credentials": {"reference": "vault://broker"},
                "database_credentials": {"reference": "vault://db"},
            },
            "monitoring": {
                "consecutive_rejects_limit": 5,
                "unknown_outcomes_limit": 3,
                "unknown_outcomes_window_seconds": 300,
                "latency_p95_limit_ms": 500.0,
                "latency_window_samples": 10,
                "latency_downgrade_duration_seconds": 60,
                "life_to_live_seconds": 120,
                "heartbeat_interval_seconds": 30,
                "runbook_registry": {
                    "stale_order": "RB-STALE-ORDER-001",
                    "circuit_breaker": "RB-CB-001",
                },
                "escalation_chain": {
                    "high": ["pagerduty", "ops-channel"],
                    "critical": ["pagerduty", "telephony", "slack-emergency"],
                },
            },
        }
    )

    class DummyClock:
        def __init__(self) -> None:
            self._now = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
            self._monotonic = 100.0

        def now_utc(self) -> datetime:
            return self._now

        def now_ptp(self) -> datetime:
            return self._now

        def monotonic(self) -> float:
            return self._monotonic

        def advance(self, seconds: float) -> None:
            self._now += timedelta(seconds=seconds)
            self._monotonic += seconds

    clock = DummyClock()

    signals_manager = OperationalSignalsManager(
        runbook_registry=config.monitoring.runbook_registry,
        escalation_chain=config.monitoring.escalation_chain,
        clock=clock,
    )

    # Heartbeat emitter
    heartbeat_emitter = HeartbeatEmitter(
        watchdog_url="http://localhost:8080/hb",
        clock=clock,
    )

    # Initialize the orchestrator service
    service = MonitoringService(
        config=config,
        clock=clock,
        signals_manager=signals_manager,
        heartbeat_emitter=heartbeat_emitter,
    )

    # Record some successful latencies
    print("Recording execution latencies...")
    for latency in [
        120.0,
        150.0,
        110.0,
        130.0,
        140.0,
        115.0,
        125.0,
        135.0,
        105.0,
        122.0,
    ]:
        service.record_broker_success(latency)

    status = service.get_monitoring_status()
    print(
        f"Monitoring status: p95_latency_ms={status['metrics']['p95_latency_ms']}ms, capability={status['current_capability']}"
    )

    # Simulating consecutive rejects limit breach
    print("\nSimulating consecutive rejects limit breach...")
    for _ in range(5):
        service.record_broker_reject()

    status = service.get_monitoring_status()
    print(
        f"Circuit breaker tripped? {status['circuit_breaker_tripped']} (Reason: {status['circuit_breaker_reason']})"
    )

    # Reset breaker
    print("Resetting circuit breaker...")
    service.reset_circuit_breaker()
    status = service.get_monitoring_status()
    print(f"Circuit breaker tripped? {status['circuit_breaker_tripped']}")


def example_13_promotion() -> None:
    """Demonstrate the Promotion Submodule validations and checks."""
    print("\n" + "=" * 100)
    print("--- 13. Promotion Submodule: Ladder & Preconditions ---")
    print("=" * 100)

    # 1. Compatibility Matrix Check
    print("\n[Matrix compatibility checks]")
    try:
        validate_route_stage_capability(
            TradingRoute.SIM, PromotionStage.OFFLINE_TEST, MutationCapability.READ_ONLY
        )
        print("OK: (sim, offline_test, read_only) compatibility validation passed.")
    except Exception as e:
        print(f"FAIL: Compatibility check failed: {e}")

    try:
        validate_route_stage_capability(
            TradingRoute.LIVE, PromotionStage.MICRO_LIVE, MutationCapability.FULL_LIVE
        )
        print("OK: (live, micro_live, full_live) compatibility validation passed.")
    except Exception as e:
        print(f"Expected Failure: (live, micro_live, full_live) is invalid: {e}")

    # 2. Gate 3 (evaluate_promotion_stage_gate)
    print("\n[Gate 3: evaluate_promotion_stage_gate]")
    valid_req = TradingRequestEnvelope(
        route=TradingRoute.LIVE,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-promo-1",
        correlation_id="corr-promo-1",
        symbol="EURUSD",
        quote_snapshot=QuoteSnapshot(
            symbol="EURUSD",
            bid=Decimal("1.1000"),
            ask=Decimal("1.1002"),
            spread=Decimal("0.0002"),
            timestamp="2026-07-09T10:00:00Z",
            source="test",
            freshness_age_ms=10,
        ),
    )
    result = evaluate_promotion_stage_gate(request=valid_req)
    print(f"Valid request Gate 3 status: {result.status} (Reason: {result.reason_code})")

    # 3. Transitions
    print("\n[Promotion Transition checks]")
    class SimpleClock:
        def now_utc(self):
            return datetime.now(UTC)
    clock = SimpleClock()

    # Generate Operator approval tokens
    r_hash = compute_canonical_promotion_hash(
        strategy_id="strat-promo-1",
        current_stage=PromotionStage.OFFLINE_TEST,
        target_stage=PromotionStage.SIMULATION,
    )
    app_token = OperatorApprovalToken(
        approval_id="app-p-1",
        operator_id="op-p-1",
        governed_action_id="promote_to_simulation",
        scope=ApprovalScope(strategy_id="strat-promo-1"),
        canonical_request_hash=r_hash,
        issued_at=datetime.now(UTC).isoformat(),
        expires_at=(datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
    )

    try:
        # Promotion with proper approvals and healthy prerequisites
        validate_promotion_transition(
            strategy_id="strat-promo-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(app_token,),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )
        print("OK: Strategy promotion transition (offline_test -> simulation) validated successfully.")
    except Exception as e:
        print(f"FAIL: Strategy promotion failed: {e}")

    try:
        # Self promotion
        validate_promotion_transition(
            strategy_id="strat-promo-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )
        print("FAIL: Self-promotion succeeded (Unexpected).")
    except Exception as e:
        print(f"OK: Self-promotion blocked (Expected): {e}")

    # 4. Preactivation Conditions
    print("\n[Preactivation checks]")
    try:
        # MicroLive promotion check with active kill switches
        validate_preactivation_conditions(
            route=TradingRoute.LIVE,
            stage=PromotionStage.MICRO_LIVE,
            active_kill_switches=True,
            reconciliation_blocked=False,
            context_is_stale=False,
            security_profile_missing=False,
        )
        print("FAIL: Preactivation with kill switches passed (Unexpected).")
    except Exception as e:
        print(f"OK: Preactivation blocked by active kill switch (Expected): {e}")

    # 5. Metadata Lookups
    print("\n[Metadata lookup checks]")
    try:
        validate_sim_metadata_lookup(mode="historical_backtest", has_captured_snapshot=False)
        print("FAIL: Historical backtest lookup without snapshot succeeded (Unexpected).")
    except Exception as e:
        print(f"OK: Historical backtest without snapshot blocked (Expected): {e}")

    try:
        validate_sim_metadata_lookup(mode="historical_backtest", has_captured_snapshot=True)
        print("OK: Historical backtest with snapshot allowed successfully.")
    except Exception as e:
        print(f"FAIL: Historical backtest with snapshot failed: {e}")


def example_14_runtime_coordination() -> None:
    """Demonstrate Session Runtime Coordination module services."""
    print("\n" + "=" * 100)
    print("--- 14. SESSION RUNTIME COORDINATION ---")
    print("=" * 100)

    class StubStateStore:
        def save_state(self, route: Any, tenant_id: str, snapshot: JsonObject, expected_version: int | None) -> str:
            return "snap-usage-1"
        def load_state(self, route: Any, tenant_id: str, snapshot_id: str) -> JsonObject | None:
            return {"mode": "normal", "halted_symbols": ["USDJPY"]}

    class UsageClock:
        def now_utc(self) -> datetime:
            return datetime.now(UTC)
        def monotonic(self) -> float:
            return time.monotonic()

    clock = UsageClock()
    store = StubStateStore()

    # 1. Session Manager
    print("\n[Session Manager Demo]")
    mgr = SessionManager(
        scope="usage-acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )
    mgr.start_session()
    print(f"Session started. State: {mgr.state}, Mode: {mgr.mode}")
    print(f"Is USDJPY halted initially? {mgr.is_symbol_halted('USDJPY')}")
    mgr.halt_symbol("EURUSD")
    print(f"Is EURUSD halted? {mgr.is_symbol_halted('EURUSD')}")
    mgr.resume_symbol("EURUSD")

    print("\n[Reconnection Resync Demo]")
    # Reconnection auto-resync triggers read-only paused mode
    mgr.update_connection_state(True)
    print(f"Reconnected. State: {mgr.state}, Mode: {mgr.mode}")
    mgr.complete_reconciliation()
    print(f"Reconciliation completed. State: {mgr.state}, Mode: {mgr.mode}")

    # 2. Concurrency Locks
    print("\n[Concurrency Lock Manager Demo]")
    lock_mgr = ConcurrencyLockManager()
    acq1 = lock_mgr.acquire_lock("acct-1", "GBPUSD", timeout=0.1)
    print(f"First lock acquisition on GBPUSD: {acq1}")
    acq2 = lock_mgr.acquire_lock("acct-1", "GBPUSD", timeout=0.05)
    print(f"Second (duplicate) lock acquisition: {acq2} (Expected: False)")
    lock_mgr.release_lock("acct-1", "GBPUSD")
    acq3 = lock_mgr.acquire_lock("acct-1", "GBPUSD", timeout=0.1)
    print(f"Re-acquiring after release: {acq3}")
    lock_mgr.release_lock("acct-1", "GBPUSD")

    # 3. Cost Control
    print("\n[Cost Controller Demo]")
    cost_ctrl = CostController()
    req = TradingRequestEnvelope(
        route=TradingRoute.SIM,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.SIMULATION,
        mutation_capability=MutationCapability.READ_ONLY,
        request_id="req-1",
        correlation_id="wf-1",
        payload={"strategy_id": "strat-1", "tenant_id": "acct-1"},
    )
    limits = {
        "request_max": Decimal("50.0"),
        "strategy_max": Decimal("100.0"),
        "session_max": Decimal("200.0"),
    }
    print("Validating budget under limit...")
    cost_ctrl.validate_pre_dispatch_budget(request=req, estimated_cost=Decimal("20.0"), limits=limits)
    print("Pre-dispatch budget validation passed.")

    # 4. Signal Processor
    print("\n[Signal Processor Demo]")
    sig_proc = SignalProcessor()
    
    def dummy_pipeline_runner(envelope: TradingRequestEnvelope) -> GatePipelineDecision:
        print(f"Gating pipeline executed for request: {envelope.request_id}")
        return GatePipelineDecision(
            status=TradingStatus.ACCEPTED,
            steps=(),
            total_latency_ms=Decimal("0.5"),
        )

    signal = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "sig-req-999",
        "correlation_id": "sig-corr-999",
        "symbol": "GBPUSD",
        "strategy_id": "strat-1",
    }
    envelope, decision = sig_proc.process_strategy_signal(
        signal=signal,
        gate_pipeline_runner=dummy_pipeline_runner,
    )
    print(f"Processed signal to envelope request_id: {envelope.request_id}, Decision status: {decision.status.value}")


def get_client() -> Any:
    """Helper to fetch the underlying broker client."""
    broker = get_broker_module()
    return (
        broker.get_ctrader_client()
        if hasattr(broker, "get_ctrader_client")
        else broker.get_mt5_client()
    )


def example_01_connect() -> None:
    """Demonstrate connection to the active broker."""
    print("\n" + "=" * 100)
    print(f"--- 1. Connecting to Active Broker: {settings.active_broker.upper()} ---")
    print("=" * 100)

    client = get_client()
    try:
        client.connect()
    except Exception as e:
        print(f"Exception during connection: {e}")

    if client.is_connected():
        print(f"Successfully connected to {settings.active_broker.upper()}.")
    else:
        print(f"Failed to connect to {settings.active_broker.upper()}.")


def example_02_terminal() -> None:
    """Demonstrate printing terminal information using TerminalInfo."""
    print("\n" + "=" * 100)
    print("--- 2. Fetching Terminal Info ---")
    print("=" * 100)

    term = TerminalInfo()
    try:
        print(f"Name:             {term.name()}")
        print(f"Company:          {term.company()}")
        print(f"Build:            {term.build()}")
        print(f"Language:         {term.language()}")
        print(f"Connected:        {'Yes' if term.connected() else 'No'}")
        print(f"Trade Allowed:    {'Yes' if term.trade_allowed() else 'No'}")
        print(f"DLLs Allowed:     {'Yes' if term.dlls_allowed() else 'No'}")
        print(f"Ping Last (us):   {term.ping_last()}")
        print(f"Path:             {term.path()}")
        print(f"Data Path:        {term.data_path()}")
        print(f"Common Data Path: {term.common_data_path()}")
    except Exception as e:
        print(f"Failed to fetch terminal info: {e}")


def example_03_account() -> None:
    """Demonstrate printing account information using AccountInfo."""
    print("\n" + "=" * 100)
    print("--- 3. Fetching Account Information ---")
    print("=" * 100)

    acc = AccountInfo()
    try:
        print(f"Login:            {acc.login()}")
        print(f"Name:             {acc.name()}")
        print(f"Server:           {acc.server()}")
        print(f"Company:          {acc.company()}")
        print(f"Currency:         {acc.currency()}")
        print(f"Leverage:         1:{acc.leverage()}")
        print()
        print("ACCOUNT MODE")
        print("-" * 60)
        print(f"Trade Mode:       {acc.trade_mode()} ({acc.trade_mode_description()})")
        print(
            f"Margin Mode:      {acc.margin_mode()} ({acc.margin_mode_description()})"
        )
        print()
        print("PERMISSIONS")
        print("-" * 60)
        print(f"Trade Allowed:    {'Yes' if acc.trade_allowed() else 'No'}")
        print(f"Expert Allowed:   {'Yes' if acc.trade_expert() else 'No'}")
        print(f"Limit Orders:     {acc.limit_orders()} (0 = unlimited)")
        print()
        print("BALANCE & EQUITY")
        print("-" * 60)
        print(f"Balance:          {acc.balance():.2f} {acc.currency()}")
        print(f"Credit:           {acc.credit():.2f} {acc.currency()}")
        print(f"Profit:           {acc.profit():.2f} {acc.currency()}")
        print(f"Equity:           {acc.equity():.2f} {acc.currency()}")
        print()
        print("MARGIN INFORMATION")
        print("-" * 60)
        print(f"Margin Used:      {acc.margin():.2f} {acc.currency()}")
        print(f"Free Margin:      {acc.free_margin():.2f} {acc.currency()}")
        if acc.margin() > 0:
            print(f"Margin Level:     {acc.margin_level():.2f}%")
        else:
            print("Margin Level:     N/A (no open positions)")
        print(f"Margin Stopout:   {acc.margin_so_level()}")
    except Exception as e:
        print(f"Failed to fetch account info: {e}")


def example_04_symbol() -> None:
    """Demonstrate printing symbol specification info using SymbolInfo."""
    print("\n" + "=" * 100)
    print(f"--- 4. Fetching Symbol Information for {trading_symbol} ---")
    print("=" * 100)

    sym = SymbolInfo(trading_symbol)
    try:
        if sym.refresh():
            print(f"Symbol:           {sym.name()}")
            print(f"Digits:           {sym.digits()}")
            print(f"Point:            {sym.point()}")
            print(f"Tick Size:        {sym.tick_size()}")
            print("\nCURRENT PRICES")
            print("-" * 60)
            print(f"Bid:              {sym.bid():.{sym.digits()}f}")
            print(f"Ask:              {sym.ask():.{sym.digits()}f}")
            print(f"Last:             {sym.last():.{sym.digits()}f}")
            print(f"Spread:           {sym.spread()} points")
            print("\nTRADING INFORMATION")
            print("-" * 60)
            print(
                f"Trade Mode:       {sym.trade_mode()} ({sym.trade_mode_description()})"
            )
            print("\nLOT PARAMETERS")
            print("-" * 60)
            print(f"Contract Size:    {sym.contract_size():.2f}")
            print(f"Min Lot:          {sym.volume_min():.2f}")
            print(f"Max Lot:          {sym.volume_max():.2f}")
            print(f"Lot Step:         {sym.volume_step():.2f}")
            print("\nSWAP INFORMATION")
            print("-" * 60)
            print(f"Swap Mode:        {sym.swap_mode()}")
            print(f"Swap Long:        {sym.swap_long():.2f}")
            print(f"Swap Short:       {sym.swap_short():.2f}")
        else:
            print(f"Failed to refresh symbol specifications for {trading_symbol}")
    except Exception as e:
        print(f"Failed to fetch symbol info: {e}")


def example_05_position() -> None:
    """Demonstrate printing open position list using PositionInfo."""
    print("\n" + "=" * 100)
    print("--- 5. Fetching Active Positions ---")
    print("=" * 100)

    try:
        broker = get_broker_module()
        positions = broker.get_position_info() or ()
        print(f"Active positions count: {len(positions)}")

        pos = PositionInfo()
        for i, raw_pos in enumerate(positions):
            if pos.select_by_ticket(raw_pos.ticket):
                print(f"{i + 1}. Ticket {pos.ticket()}")
                print(f"   Symbol:        {pos.symbol()}")
                print(f"   Type:          {pos.type()} ({pos.type_description()})")
                print(f"   Volume:        {pos.volume()}")
                print(f"   Open Price:    {pos.price_open()}")
                print(f"   Current Price: {pos.price_current()}")
                print(f"   Profit:        ${pos.profit():.2f}")
                print(f"   Swap:          ${pos.swap():.2f}")
                print(f"   SL / TP:       {pos.stop_loss()} / {pos.take_profit()}")
                print(f"   Comment:       {pos.comment()}")
                print("-" * 30)

        print("\nSelecting position by symbol 'EURUSD'...")
        eur_pos = PositionInfo()
        if eur_pos.select("EURUSD"):
            print("Successfully selected EURUSD position:")
            print(f"  Ticket:         {eur_pos.ticket()}")
            print(f"  Profit:         ${eur_pos.profit():.2f}")
        else:
            print("No active EURUSD position found.")
    except Exception as e:
        print(f"Failed to select positions: {e}")


def example_06_order() -> None:
    """Demonstrate printing pending orders list using OrderInfo."""
    print("\n" + "=" * 100)
    print("--- 6. Fetching Active Pending Orders ---")
    print("=" * 100)

    try:
        broker = get_broker_module()
        orders = broker.get_order_info() or ()
        print(f"Active pending orders count: {len(orders)}")

        ord_info = OrderInfo()
        for i, raw_ord in enumerate(orders):
            if ord_info.select(raw_ord.ticket):
                print(f"{i + 1}. Ticket {ord_info.ticket()}")
                print(f"   Symbol:        {ord_info.symbol()}")
                print(
                    f"   Type:          {ord_info.type()} ({ord_info.type_description()})"
                )
                print(f"   Volume Init:   {ord_info.volume_initial()}")
                print(f"   Volume Curr:   {ord_info.volume_current()}")
                print(f"   Open Price:    {ord_info.price_open()}")
                print(f"   Current Price: {ord_info.price_current()}")
                print(
                    f"   SL / TP:       {ord_info.stop_loss()} / {ord_info.take_profit()}"
                )
                print(f"   Comment:       {ord_info.comment()}")
                print("-" * 30)
    except Exception as e:
        print(f"Failed to select pending orders: {e}")


def example_07_history_order() -> None:
    """Demonstrate listing historical orders using HistoryOrderInfo."""
    print("\n" + "=" * 100)
    print("--- 7. Fetching History Orders ---")
    print("=" * 100)

    try:
        start = datetime(1990, 1, 1, tzinfo=UTC)
        end = datetime.now(UTC)
        broker = get_broker_module()
        orders = broker.get_history_order_info(date_from=start, date_to=end) or ()
        print(f"Total historical orders found: {len(orders)}")

        hist = HistoryOrderInfo()
        for i, raw_ord in enumerate(orders[:5]):  # Print up to 5 orders
            if hist.select(raw_ord.ticket):
                print(f"{i + 1}. Ticket #{hist.ticket()} {hist.symbol()}")
                print(f"   Type:          {hist.type()} ({hist.type_description()})")
                print(f"   State:         {hist.state()} ({hist.state_description()})")
                print(
                    f"   Volume:        {hist.volume_current()}/{hist.volume_initial()}"
                )
                print(f"   Open Price:    {hist.price_open()}")
                print(f"   SL / TP:       {hist.stop_loss()} / {hist.take_profit()}")
                print(
                    f"   Done Time:     {datetime.fromtimestamp(hist.time_done(), tz=UTC)}"
                )
                print("-" * 30)
    except Exception as e:
        print(f"Failed to query history orders: {e}")


def example_08_history_deal() -> None:
    """Demonstrate listing deals using DealInfo."""
    print("\n" + "=" * 100)
    print("--- 8. Fetching Historical Deals ---")
    print("=" * 100)

    try:
        start = datetime(1990, 1, 1, tzinfo=UTC)
        end = datetime.now(UTC)
        broker = get_broker_module()
        deals = broker.get_history_deal_info(date_from=start, date_to=end) or ()
        print(f"Total deals found: {len(deals)}")

        deal = DealInfo()
        for i, raw_deal in enumerate(deals[:5]):  # Print up to 5 deals
            if deal.select(raw_deal.ticket):
                print(f"{i + 1}. Ticket #{deal.ticket()} {deal.symbol()}")
                print(f"   Type:          {deal.type()} ({deal.type_description()})")
                print(f"   Entry:         {deal.entry()} ({deal.entry_description()})")
                print(f"   Price:         {deal.price()}")
                print(f"   Volume:        {deal.volume()}")
                print(f"   Profit:        ${deal.profit():.2f}")
                print(f"   Commission:    ${deal.commission():.2f}")
                print(f"   Swap:          ${deal.swap():.2f}")
                print(f"   Comment:       {deal.comment()}")
                print("-" * 30)
    except Exception as e:
        print(f"Failed to query history deals: {e}")


def example_09_open_position() -> None:
    """Demonstrate opening a position using generic Trade class."""
    global pos_ticket, buy_price, used_filling_mode
    print("\n" + "=" * 100)
    print(f"--- 9. Opening Position (Buy 0.02 {trading_symbol}) ---")
    print("=" * 100)

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    client = get_client()
    used_filling_mode = client.ORDER_FILLING_FOK
    if hasattr(sym, "_data") and sym._data:
        filling_val = getattr(sym._data, "filling_mode", 3)
        if filling_val & 2:  # IOC
            used_filling_mode = client.ORDER_FILLING_IOC
        elif filling_val & 1:  # FOK
            used_filling_mode = client.ORDER_FILLING_FOK

    trade = Trade()
    trade.set_symbol(trading_symbol)
    trade.set_expert_magic_number(99999)
    trade.set_deviation_in_points(20)
    trade.set_order_filling(used_filling_mode)

    try:
        buy_price = sym.ask()
        success = trade.buy(0.02, price=buy_price, comment="Unified Usage Buy")
        if success:
            pos_ticket = trade.result_order()
            print(f"Position opened successfully! Ticket: {pos_ticket}")
            print(f"  Execution Price: {trade.result_price()}")
            print(f"  Deal Ticket:     {trade.result_deal()}")
        else:
            print("Failed to open position.")
            print(f"  Result Code:     {trade.result_retcode()}")
            print(f"  Comment:         {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during buy trade order: {e}")


def example_10_calc_profit_margin() -> None:
    """Demonstrate calculating expected profit and required margin."""
    print("\n" + "=" * 100)
    print("--- 10. Pre-trade Profit and Margin Calculation ---")
    print("=" * 100)

    client = get_client()
    if not client.is_connected():
        print("Client is not connected.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    try:
        # 1. Calculate margin
        margin = client.order_calc_margin(
            client.ORDER_TYPE_BUY, trading_symbol, 0.02, sym.ask()
        )
        if margin is not None:
            print(f"Required Margin for Buy 0.02 {trading_symbol}: ${margin:.2f}")
        else:
            print(f"Failed to calculate margin. Error: {client.last_error()}")

        # 2. Calculate profit
        pip_val = sym.point() * 10
        target_price = round(sym.ask() + (100 * pip_val), sym.digits())
        profit = client.order_calc_profit(
            client.ORDER_TYPE_BUY, trading_symbol, 0.02, sym.ask(), target_price
        )
        if profit is not None:
            print(
                f"Expected Profit for Buy 0.02 {trading_symbol} (+100 pips): ${profit:.2f}"
            )
        else:
            print(f"Failed to calculate profit. Error: {client.last_error()}")
    except Exception as e:
        print(f"Exception during calculation: {e}")


def example_11_modify_position() -> None:
    """Demonstrate modifying the Stop Loss / Take Profit of an active position."""
    print("\n" + "=" * 100)
    print("--- 11. Modifying Active Position SL/TP ---")
    print("=" * 100)

    if pos_ticket == 0:
        print("No active position from Example 9. Skipping modification.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        pip_val = sym.point() * 10
        sl = round(buy_price - 1000 * pip_val, sym.digits())
        tp = round(buy_price + 1000 * pip_val, sym.digits())

        trade = Trade()
        success = trade.position_modify(pos_ticket, sl=sl, tp=tp)
        if success:
            print(f"Position SL/TP modified successfully. SL: {sl}, TP: {tp}")
        else:
            print(f"Failed to modify position. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during position modification: {e}")


def example_12_close_partial_position() -> None:
    """Demonstrate partial close of an active position (Closing 0.01 lot)."""
    print("\n" + "=" * 100)
    print("--- 12. Partial Closing Active Position (0.01 lot) ---")
    print("=" * 100)

    if pos_ticket == 0:
        print("No active position from Example 9. Skipping partial close.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        trade = Trade()
        trade.set_order_filling(used_filling_mode)
        # cTrader closed deals need sell type close for buys
        client = get_client()
        request = {
            "action": client.TRADE_ACTION_DEAL,
            "symbol": trading_symbol,
            "volume": 0.01,
            "type": client.ORDER_TYPE_SELL,
            "position": pos_ticket,
            "price": sym.bid(),
            "deviation": 20,
            "magic": 99999,
            "comment": "Partial Close",
            "type_time": client.ORDER_TIME_GTC,
            "type_filling": used_filling_mode,
        }
        success = trade._send_request(request)
        if success:
            print(f"Partial close executed! Deal Ticket: {trade.result_deal()}")
        else:
            print(f"Failed partial close. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during partial close: {e}")


def example_13_close_position() -> None:
    """Demonstrate closing the remaining active position fully."""
    print("\n" + "=" * 100)
    print("--- 13. Closing Remaining Position Fully ---")
    print("=" * 100)

    if pos_ticket == 0:
        print("No active position from Example 9. Skipping close.")
        return

    time.sleep(1)

    try:
        trade = Trade()
        trade.set_order_filling(used_filling_mode)
        success = trade.position_close(pos_ticket)
        if success:
            print(
                f"Remaining position closed fully! Deal Ticket: {trade.result_deal()}"
            )
        else:
            print(f"Failed to close position. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during position close: {e}")


def example_14_pending_orders() -> None:
    """Demonstrate placing a Buy Limit pending order."""
    global ord_ticket, limit_price
    print("\n" + "=" * 100)
    print("--- 14. Placing Pending Order (Buy Limit) ---")
    print("=" * 100)

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        pip_val = sym.point() * 10
        limit_price = round(sym.bid() - 200 * pip_val, sym.digits())

        trade = Trade()
        trade.set_symbol(trading_symbol)
        trade.set_order_filling(used_filling_mode)

        success = trade.buy_limit(
            0.01, price=limit_price, comment="Unified Pending Limit"
        )
        if success:
            ord_ticket = trade.result_order()
            print(f"Pending Buy Limit placed successfully! Ticket: {ord_ticket}")
        else:
            print(f"Failed to place pending order. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception placing pending order: {e}")


def example_15_modify_pending_orders() -> None:
    """Demonstrate modifying a placed pending order."""
    print("\n" + "=" * 100)
    print("--- 15. Modifying Pending Order ---")
    print("=" * 100)

    if ord_ticket == 0:
        print("No active pending order from Example 14. Skipping modification.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        pip_val = sym.point() * 10
        new_limit_price = round(limit_price - 50 * pip_val, sym.digits())

        trade = Trade()
        success = trade.order_modify(ord_ticket, price=new_limit_price, sl=0.0, tp=0.0)
        if success:
            print(f"Pending order modified successfully! New Price: {new_limit_price}")
        else:
            print(f"Failed to modify pending order. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception modifying pending order: {e}")


def example_16_delete_pending_orders() -> None:
    """Demonstrate deleting / cancelling a pending order."""
    print("\n" + "=" * 100)
    print("--- 16. Deleting/Cancelling Pending Order ---")
    print("=" * 100)

    if ord_ticket == 0:
        print("No active pending order from Example 14. Skipping deletion.")
        return

    time.sleep(1)

    try:
        trade = Trade()
        success = trade.order_delete(ord_ticket)
        if success:
            print(f"Pending order deleted successfully! Ticket: {ord_ticket}")
        else:
            print(f"Failed to delete pending order. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception deleting pending order: {e}")


def example_17_shutdown() -> None:
    """Demonstrate shutting down connection to active broker."""
    print("\n" + "=" * 100)
    print(f"--- 17. Shutting down connection to {settings.active_broker.upper()} ---")
    print("=" * 100)

    client = get_client()
    try:
        if hasattr(client, "shutdown"):
            client.shutdown()
        else:
            client.disconnect()
        print("Broker connection shut down successfully.")
    except Exception as e:
        print(f"Exception during shutdown: {e}")


if __name__ == "__main__":
    example_01_contracts()
    example_02_state_ports()
    example_03_configurations_security_controls()
    example_04_security_boundaries_error_redaction()
    example_05_persistence_implementations()
    example_06_read_only_info_facades()
    example_07_actions_and_validation()
    example_08_execution_primitives()
    example_09_gates_pipeline()
    example_10_execution_coordinator_and_reporting()
    example_11_reconciliation()
    example_12_monitoring()
    example_13_promotion()
    example_14_runtime_coordination()
    example_01_connect()
    example_02_terminal()
    example_03_account()
    example_04_symbol()
    example_05_position()
    example_06_order()
    example_07_history_order()
    example_08_history_deal()
    example_09_open_position()
    example_10_calc_profit_margin()
    example_11_modify_position()
    example_12_close_partial_position()
    example_13_close_position()
    example_14_pending_orders()
    example_15_modify_pending_orders()
    example_16_delete_pending_orders()
    example_17_shutdown()
