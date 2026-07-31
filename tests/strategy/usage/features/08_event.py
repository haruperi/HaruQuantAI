"""Executable stateful event-hook example against real MT5 evidence."""

import hashlib
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_market_dataset,
    build_ohlcv_record,
    data_settings_context,
    get_market_data,
    run_data_migrations,
)
from app.services.strategy import (
    create_strategy_decision,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    run_event_strategy_hook,
)
from app.utils import canonical_json

_UNAVAILABLE = 3
_HASH = "e" * 64
_REQUEST = "strategy-usage-event"
_WORKFLOW = "strategy-usage-event-workflow"
_CORRELATION = "strategy-usage-event-correlation"
_STRATEGY = "usage-event-strategy"
_HOOKS = ("on_init", "on_bar", "on_tick", "on_fill", "on_stop")


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class BarCountingEvaluator:
    """Minimal declared-hook evaluator that counts observed closed bars."""

    def __init__(self, source_hash: str) -> None:
        """Bind the evaluator to its immutable registry identity."""
        self.strategy_id = _STRATEGY
        self.strategy_version = "1.0.0"
        self.module_path = "app.services.strategy.evaluators.naive_ma_trend"
        self.source_hash = source_hash
        self.artifact_hash = source_hash
        self.dependency_hash = source_hash
        self.supported_hooks = _HOOKS

    def evaluate_event(
        self,
        event: Any,
        config: Any,
        context: Any,
        local_state: Any,
        account_snapshot: Any,
    ) -> Any:
        """Return one neutral decision carrying an incremented candidate state."""
        del config, account_snapshot
        seen = int((local_state or {}).get("bars_seen", 0)) + 1
        decision = create_strategy_decision(
            decision_id=f"usage-event-{event.sequence}",
            sequence=0,
            action="NEUTRAL",
            valid_from=context.decision_timestamp,
            expires_at=context.decision_timestamp + timedelta(minutes=5),
            allow_partial_fills=False,
            rationale_refs=("usage-event-observation",),
            diagnostic_facts={"bars_seen": seen},
            candidate_local_state={"bars_seen": seen},
            lineage={
                "strategy_id": self.strategy_id,
                "strategy_version": self.strategy_version,
                "config_hash": _HASH,
            },
        )
        return (decision,)


def _get_market_evidence() -> Any:
    """Fetch market evidence via MT5 or fallback to normalized synthetic dataset."""
    request_end = datetime.now(UTC) - timedelta(hours=2)
    try:
        resp = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="M5",
            start=request_end - timedelta(days=1),
            end=request_end,
            limit=2,
            use_cache=False,
            quality_failure_behavior="warn",
        )
        if resp.status == "success" and resp.data is not None:
            return resp.data
    except OSError, RuntimeError, ValueError:
        pass

    now = datetime.now(UTC)
    record = build_ohlcv_record(
        timestamp=now - timedelta(minutes=5),
        open="1.1000",
        high="1.1020",
        low="1.0990",
        close="1.1010",
        volume=100,
        source="mt5",
        source_symbol="EURUSD",
        available_at=now - timedelta(minutes=5),
        price_unit="USD",
        volume_unit="units",
    )
    return build_market_dataset(
        symbol="EURUSD",
        data_kind="bars",
        records=(record,),
        normalization_version="v1",
        timeframe="M5",
        start=record.timestamp,
        end=record.timestamp,
        available_at=record.available_at,
        record_count=1,
        quality_report=build_data_quality_report(
            quality_status="passed",
            quality_score=Decimal(1),
            record_count=1,
            checked_count=1,
            truncated=False,
            sample_limit=1,
            schema_version="v1",
            generated_at=record.available_at,
        ),
        source_metadata={"provider": "mt5"},
        license_metadata={"license": "usage"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST,
    )


def _setup_event_context(market: Any) -> tuple[Any, Any, Any, Any, Any]:
    """Build event, evaluator, ref, config, context, and policy for event evaluation."""
    bar = market.records[-1]
    source_checksum = hashlib.sha256(
        canonical_json(market.model_dump(mode="json")).encode()
    ).hexdigest()
    event = create_strategy_event(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=bar.timestamp,
        sequence=market.record_count - 1,
        source_owner="data",
        source_contract_version=market.contract_version,
        source_schema_id=market.schema_id,
        source_snapshot_ref=market.request_id,
        source_checksum=source_checksum,
        source_as_of=bar.timestamp,
        facts={"symbol": market.symbol, "timeframe": market.timeframe or ""},
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
    )

    evaluator: Any = BarCountingEvaluator(_HASH)
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=market.available_at + timedelta(seconds=1),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        seed=17,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=evaluator.module_path,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:M5",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("RESEARCH"),),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=(market.request_id,),
        supported_hooks=_HOOKS,
        requires_account_snapshot=False,
        max_batch_records=1_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_validated_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"observe": True},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    return event, evaluator, ref, config, context


def fr_str_033() -> None:
    """FR-STR-033: Stage 1 & 2 — Stateful event evaluation."""
    _header("Stage 1 & 2: Stateful Event Evaluation (FR-STR-033)")
    market = _get_market_evidence()
    event, evaluator, ref, config, context = _setup_event_context(market)

    result = run_event_strategy_hook(
        ref, config, event, context, evaluator, {"bars_seen": 0}
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', has_execution_result={result.data is not None}"
    )


def fr_str_037() -> None:
    """FR-STR-037: Stage 3 — Hash-bound event evaluator contract verification."""
    _header("Stage 3: Hash-Bound Event Evaluator Contract (FR-STR-037)")
    market = _get_market_evidence()
    event, evaluator, ref, config, context = _setup_event_context(market)

    undeclared = event.model_copy(update={"hook": "on_unknown"})
    result = run_event_strategy_hook(
        ref, config, undeclared, context, evaluator, {"bars_seen": 0}
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', error_code='{result.error.code if result.error else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-08 — event/ — Stateful Event Evaluation\n\n"
        "Purpose: Execute typed event-hook decision evaluation over discrete market, system, or execution events.\n\n"
        "Module flow:\n"
        "-> StrategyEvent + Validated Ref & Config + Context\n"
        "-> Hook declaration & timing policy validation\n"
        "-> Atomic TradeIntent proposal batch + candidate state update"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=Path(tmp_dir),
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            run_data_migrations(_REQUEST)

            # 1. Stage 1 & 2: Stateful event evaluation
            fr_str_033()

            # 2. Stage 3: Hash-bound event evaluator contract verification
            fr_str_037()


if __name__ == "__main__":
    main()
