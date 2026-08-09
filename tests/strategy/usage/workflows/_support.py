"""Shared genuine-evidence builders for Strategy workflow programs."""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    data_settings_context,
    get_market_data,
    run_data_migrations,
    to_ohlcv_dataframe,
    unwrap_data_response,
)
from app.services.strategy import (
    create_strategy_config,
    create_strategy_decision,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_signal,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.utils import create_auth_context, generate_id

HASH = "a" * 64
CONFIG_HASH = "b" * 64
REQ = "req-11111111-1111-4111-8111-111111111111"
WF = "wf-22222222-2222-4222-8222-222222222222"
COR = "cor-33333333-3333-4333-8333-333333333333"
STRATEGY_ID = "mean-reversion"
STRATEGY_VERSION = "1.0.0"
MODULE_PATH = "approved.strategies.mean_reversion"


def policy() -> object:
    """Build the explicit workflow validation policy.

    Returns:
        Immutable Strategy validation policy.
    """
    return create_strategy_validation_policy(
        policy_version="policy-v1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )


def manifest(
    *,
    timing_name: str = "EVENT_DRIVEN",
    required_indicators: tuple[str, ...] = (),
    supported_hooks: tuple[str, ...] = ("on_bar",),
) -> object:
    """Build one complete workflow Strategy manifest.

    Args:
        timing_name: Public timing-policy value.
        required_indicators: Ordered official indicator identities.
        supported_hooks: Declared event hooks.

    Returns:
        Immutable Strategy manifest.
    """
    return create_strategy_manifest(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        module_path=MODULE_PATH,
        owner_ref="strategy-workflow",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={
            "type": "object",
            "properties": {"period": {"type": "integer", "minimum": 1}},
            "required": ("period",),
            "additionalProperties": False,
        },
        required_data=("EURUSD:M1",),
        required_indicators=required_indicators,
        timing_policy=get_strategy_timing_policy(timing_name),
        permitted_environments=(get_strategy_environment("RESEARCH"),),
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
        provenance_refs=("strategy-workflow-source",),
        supported_hooks=supported_hooks,
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=4_096,
        decision_timeout_seconds=5,
    )


def validated_ref(
    *,
    timing_name: str = "EVENT_DRIVEN",
    required_indicators: tuple[str, ...] = (),
    supported_hooks: tuple[str, ...] = ("on_bar",),
) -> object:
    """Build one exact approved workflow Strategy reference.

    Args:
        timing_name: Public timing-policy value.
        required_indicators: Ordered official indicator identities.
        supported_hooks: Declared event hooks.

    Returns:
        Exact validated Strategy reference.
    """
    active_policy = policy()
    return create_validated_strategy_ref(
        manifest=manifest(
            timing_name=timing_name,
            required_indicators=required_indicators,
            supported_hooks=supported_hooks,
        ),
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=active_policy.policy_version,
        validation_policy=active_policy,
        registry_record_hash=CONFIG_HASH,
        request_id=REQ,
        correlation_id=COR,
    )


def validated_config(
    parameters: Mapping[str, object] | None = None,
) -> object:
    """Build one normalized immutable workflow configuration.

    Args:
        parameters: Optional normalized parameter values.

    Returns:
        Validated Strategy configuration.
    """
    return create_validated_strategy_config(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        config_schema_version="v1",
        normalized_parameters=dict(parameters or {"period": 5}),
        config_hash=CONFIG_HASH,
        policy_version="policy-v1",
        request_id=REQ,
    )


def current_context(
    timing_name: str = "EVENT_DRIVEN",
    *,
    market: object | None = None,
) -> object:
    """Build a fixed execution clock after genuine market availability.

    Args:
        timing_name: Public timing-policy value.
        market: Optional genuine Data market evidence.

    Returns:
        Immutable Strategy execution context.
    """
    available_at = getattr(market, "available_at", None)
    decision_time = (
        available_at + timedelta(seconds=1)
        if isinstance(available_at, datetime)
        else datetime.now(UTC)
    )
    request_id = getattr(market, "request_id", REQ)
    return create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=decision_time,
        timing_policy=get_strategy_timing_policy(timing_name),
        seed=7,
        interface_version="v1",
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=(str(request_id),),
        max_diagnostic_bytes=8_192,
    )


def proposal_decision(context: object, market: object | None = None) -> object:
    """Build a proposal from the genuine latest market observation.

    Args:
        context: Fixed Strategy execution context.
        market: Optional genuine market evidence.

    Returns:
        Canonical Strategy proposal decision.
    """
    records = getattr(market, "records", ())
    last_bar = records[-1] if records else None
    close = getattr(last_bar, "close", None)
    symbol = str(getattr(market, "symbol", "EURUSD"))
    return create_strategy_decision(
        decision_id="workflow-market-entry",
        sequence=0,
        action="PROPOSE",
        symbol=symbol,
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        requested_sizing_mode="quantity",
        quantity_hint=Decimal("0.01"),
        valid_from=context.decision_timestamp - timedelta(seconds=1),
        expires_at=context.decision_timestamp + timedelta(minutes=5),
        allow_partial_fills=False,
        rationale_refs=("latest-genuine-market-observation",),
        diagnostic_facts={"observed_close": None if close is None else str(close)},
        lineage={
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "config_hash": CONFIG_HASH,
        },
    )


def event_from_market(market: object, context: object) -> object:
    """Build one typed bar-close event from genuine market evidence.

    Args:
        market: Genuine Data market evidence.
        context: Fixed Strategy execution context.

    Returns:
        Immutable Strategy event.
    """
    bar = market.records[-1]
    checksum = hashlib.sha256(
        f"{market.request_id}:{bar.timestamp.isoformat()}:{bar.close}".encode()
    ).hexdigest()
    return create_strategy_event(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=bar.timestamp,
        sequence=market.record_count - 1,
        source_owner="data",
        source_contract_version=market.contract_version,
        source_schema_id=market.schema_id,
        source_snapshot_ref=market.request_id,
        source_checksum=checksum,
        source_as_of=bar.available_at,
        facts={"symbol": market.symbol, "close": str(bar.close)},
        request_id=context.request_id,
        workflow_id=context.workflow_id,
        correlation_id=context.correlation_id,
    )


def auth_context(*, checkpoint: bool = False) -> object:
    """Build an authenticated workflow principal.

    Args:
        checkpoint: Whether checkpoint permission and scope are required.

    Returns:
        Immutable Utils authentication context.
    """
    permissions = ("strategy:register", "strategy:update")
    scopes: tuple[str, ...] = ()
    if checkpoint:
        permissions += ("strategy:checkpoint",)
        scopes = ("checkpoint-auth",)
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="builder",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=permissions,
        scopes=scopes,
        tenant_or_environment="dev",
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        issued_at=datetime.now(UTC),
    )


def registration_request() -> object:
    """Build one governed immutable registration request.

    Returns:
        Complete Strategy registration request.
    """
    active_manifest = manifest()
    return create_strategy_registration_request(
        command_id="strategy-workflow-register",
        strategy_id=active_manifest.strategy_id,
        strategy_version=active_manifest.strategy_version,
        module_path=active_manifest.module_path,
        manifest=active_manifest,
        config_schema=active_manifest.config_schema,
        source_hash=active_manifest.source_hash,
        artifact_hash=active_manifest.artifact_hash,
        dependency_hash=active_manifest.dependency_hash,
        provenance_refs=active_manifest.provenance_refs,
        principal_id="builder",
        reason="approved Strategy workflow registration",
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        authorization_ref="strategy-workflow-approval",
        requested_at=datetime.now(UTC),
        request_id=REQ,
        correlation_id=COR,
    )


def unresolved_ref() -> object:
    """Build one exact unresolved Strategy reference.

    Returns:
        Exact immutable Strategy reference.
    """
    return create_strategy_ref(
        strategy_id=STRATEGY_ID,
        exact_version=STRATEGY_VERSION,
        environment=get_strategy_environment("RESEARCH"),
        request_id=REQ,
        correlation_id=COR,
    )


def caller_config(period: int = 5) -> object:
    """Build one caller-supplied Strategy configuration.

    Args:
        period: Positive demonstration period.

    Returns:
        Declarative Strategy configuration.
    """
    return create_strategy_config(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        config_schema_version="v1",
        parameters={"period": period},
        request_id=REQ,
    )


def live_bars(timeframe: str = "M1", limit: int = 80) -> object:
    """Read bounded genuine MT5 bars through Data's package root.

    Args:
        timeframe: Canonical provider timeframe.
        limit: Maximum returned records.

    Returns:
        Genuine normalized Data market evidence.
    """
    end = datetime.now(UTC) - timedelta(hours=2)
    request = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe=timeframe,
        start=end - timedelta(days=5),
        end=end,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )
    # Directly launched workflow programs do not inherit pytest's storage
    # fixture. Keep the genuine provider read inside its own migrated,
    # recoverable Data context and return only the detached typed dataset.
    with temporary_storage():
        response = get_market_data(request)
        return unwrap_data_response(
            response,
            operation="strategy.usage.workflow.live_bars",
            request_id=response.metadata.request_id,
        )


def print_market_frame(market: object, rows: int = 8) -> None:
    """Print a bounded analytical frame from genuine market evidence.

    Args:
        market: Genuine normalized Data market evidence.
        rows: Number of latest observations to print.
    """
    response = to_ohlcv_dataframe(market)
    frame = unwrap_data_response(
        response,
        operation="strategy.usage.workflow.to_ohlcv_dataframe",
        request_id=response.metadata.request_id,
    )
    print(frame.tail(rows).to_string())


class MarketProposalEvaluator:
    """Hash-bound evaluator deriving one proposal from genuine market evidence."""

    strategy_id = STRATEGY_ID
    strategy_version = STRATEGY_VERSION
    module_path = MODULE_PATH
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def evaluate_signals(
        self,
        evidence: object,
        indicators: tuple[object, ...],
        config: object,
        context: object,
    ) -> tuple[object, ...]:
        """Derive one directional signal from the latest genuine closed bar.

        Args:
            evidence: Genuine point-in-time Strategy evidence.
            indicators: Ordered official Indicator evidence.
            config: Validated immutable Strategy configuration.
            context: Fixed Strategy execution context.

        Returns:
            One canonical signal whose direction follows the observed bar.
        """
        del indicators, config, context
        market = evidence.primary_market
        bar = market.records[-1]
        side = "BUY" if bar.close >= bar.open else "SELL"
        signal_id = hashlib.sha256(
            (
                f"{market.request_id}:{bar.timestamp.isoformat()}:"
                f"{bar.open}:{bar.close}:{side}"
            ).encode()
        ).hexdigest()
        return (
            create_strategy_signal(
                signal_id=signal_id,
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                symbol=market.symbol,
                timestamp=bar.available_at,
                signal_name="latest_closed_bar_direction",
                side=side,
                active=True,
                lineage={
                    "dataset_request_id": market.request_id,
                    "bar_timestamp": bar.timestamp.isoformat(),
                },
                facts={
                    "observed_open": str(bar.open),
                    "observed_close": str(bar.close),
                },
            ),
        )

    def evaluate_vectorized(
        self,
        market: object,
        indicators: object,
        config: object,
        context: object,
        account_snapshot: object,
    ) -> tuple[object, ...]:
        """Derive one proposal from the latest genuine closed bar.

        Args:
            market: Genuine normalized Data evidence.
            indicators: Ordered official indicator evidence.
            config: Validated immutable configuration.
            context: Fixed Strategy execution context.
            account_snapshot: Optional Data account evidence.

        Returns:
            One canonical proposal decision.
        """
        del indicators, config, account_snapshot
        return (proposal_decision(context, market),)


class MarketEventEvaluator:
    """Hash-bound evaluator deriving state from one genuine bar event."""

    strategy_id = STRATEGY_ID
    strategy_version = STRATEGY_VERSION
    module_path = MODULE_PATH
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH
    supported_hooks = ("on_bar",)

    def evaluate_event(
        self,
        ref: object,
        config: object,
        event: object,
        context: object,
        account_snapshot: object | None = None,
        local_state: Mapping[str, object] | None = None,
    ) -> tuple[object, ...]:
        """Derive one neutral state update from genuine event evidence.

        Args:
            ref: Validated exact Strategy reference.
            config: Validated immutable configuration.
            event: Typed genuine market event.
            context: Fixed Strategy execution context.
            local_state: Prior bounded Strategy-local state.
            account_snapshot: Optional Data account evidence.

        Returns:
            One neutral decision carrying the observed bar state.
        """
        del ref, config, account_snapshot
        seen = int((local_state or {}).get("bars_seen", 0)) + 1
        return (
            create_strategy_decision(
                decision_id=f"workflow-event-{event.sequence}",
                sequence=0,
                action="NEUTRAL",
                valid_from=context.decision_timestamp - timedelta(seconds=1),
                expires_at=context.decision_timestamp + timedelta(minutes=5),
                allow_partial_fills=False,
                rationale_refs=("genuine-bar-close-event",),
                diagnostic_facts={"close": event.facts["close"], "bars_seen": seen},
                candidate_local_state={
                    "bars_seen": seen,
                    "last_close": event.facts["close"],
                },
                lineage={
                    "strategy_id": STRATEGY_ID,
                    "strategy_version": STRATEGY_VERSION,
                    "config_hash": CONFIG_HASH,
                },
            ),
        )

    on_bar = evaluate_event


@contextmanager
def temporary_storage() -> Iterator[Path]:
    """Activate bounded Data-migrated Strategy registry persistence.

    Yields:
        Temporary storage root.
    """
    with TemporaryDirectory(prefix="strategy-workflow-") as raw:
        path = Path(raw)
        (path / "data" / "raw").mkdir(parents=True)
        settings = build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=path,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            migration = run_data_migrations(generate_id("req"))
            unwrap_data_response(
                migration,
                operation="strategy.usage.workflow.run_data_migrations",
                request_id=migration.metadata.request_id,
            )
            yield path


__all__ = [
    "CONFIG_HASH",
    "COR",
    "HASH",
    "MODULE_PATH",
    "REQ",
    "STRATEGY_ID",
    "STRATEGY_VERSION",
    "WF",
    "MarketEventEvaluator",
    "MarketProposalEvaluator",
    "auth_context",
    "caller_config",
    "current_context",
    "event_from_market",
    "live_bars",
    "manifest",
    "policy",
    "print_market_frame",
    "proposal_decision",
    "registration_request",
    "temporary_storage",
    "unresolved_ref",
    "validated_config",
    "validated_ref",
]
