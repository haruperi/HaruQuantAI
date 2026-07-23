"""Executable example of the concrete signal evaluation boundary.

This program demonstrates the *mechanism* that runs catalogue content: the
``SignalEvaluator`` structural contract and the hash-bound
``evaluate_strategy_signals`` boundary, including its fail-closed paths.
"""

import hashlib
import inspect
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data, get_symbol_metadata
from app.services.data.contracts import DataError
from app.services.strategy import (
    SignalEvaluator,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategySignal,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    evaluate_strategy_signals,
)

_UNAVAILABLE = 3
_MODULE = "app.services.strategy.evaluators.naive_ma_trend"
_STRATEGY = "usage-signal-boundary"


class ConstantSignalEvaluator:
    """Minimal evaluator satisfying the SignalEvaluator structural contract."""

    def __init__(self, source_hash: str) -> None:
        """Bind the evaluator to its immutable registry identity.

        Args:
            source_hash: Approved source, artifact, and dependency hash.
        """
        self.strategy_id = _STRATEGY
        self.strategy_version = "1.0.0"
        self.module_path = _MODULE
        self.source_hash = source_hash
        self.artifact_hash = source_hash
        self.dependency_hash = source_hash

    def evaluate_signals(self, evidence, indicators, config, context):
        """Return one explicit inactive signal for the evaluated bar.

        Args:
            evidence: Point-in-time signal evidence.
            indicators: Ordered precomputed indicator results.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            One deterministic inactive signal.
        """
        del indicators, context
        bar = evidence.primary_market.records[-1]
        identity = hashlib.sha256(
            f"{config.config_hash}:{bar.timestamp.isoformat()}:BOUNDARY_DEMO".encode()
        ).hexdigest()
        return (
            StrategySignal(
                signal_id=identity,
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                symbol=evidence.primary_market.symbol,
                timestamp=bar.timestamp,
                signal_name="BOUNDARY_DEMO",
                side=None,
                active=False,
                facts={"close": str(bar.close)},
                lineage={"config_hash": config.config_hash},
            ),
        )


def main() -> int:
    """Run one evaluator through the boundary and show its fail-closed path.

    Returns:
        ``0`` on success, or ``3`` when real MT5 evidence is unavailable.
    """
    print("\nCONCRETE SIGNAL EVALUATION BOUNDARY")
    print("=" * 88)
    try:
        market = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            limit=100,
            use_cache=False,
            quality_failure_behavior="warn",
        )
        metadata = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    except DataError as error:
        print("Live MT5 evidence unavailable:", error.code)
        return _UNAVAILABLE
    if not isinstance(metadata.point, int | float):
        print("MT5 point-size evidence unavailable:", metadata.point)
        return _UNAVAILABLE

    source_hash = hashlib.sha256(
        inspect.getsource(ConstantSignalEvaluator).encode()
    ).hexdigest()
    evaluator: SignalEvaluator = ConstantSignalEvaluator(source_hash)
    policy = StrategyValidationPolicy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    context = StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=datetime.now(UTC),
        timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
        seed=29,
        interface_version="v1",
        request_id="strategy-usage-signals",
        workflow_id="strategy-usage-signals-workflow",
        correlation_id="strategy-usage-signals-correlation",
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = StrategyManifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=(),
        timing_policy=context.timing_policy,
        permitted_environments=(context.environment,),
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
        provenance_refs=(market.request_id,),
        supported_hooks=(),
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=context.environment,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=source_hash,
        request_id=context.request_id,
        correlation_id=context.correlation_id,
    )
    config = ValidatedStrategyConfig(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"demo": True},
        config_hash=source_hash,
        policy_version=policy.policy_version,
        request_id=context.request_id,
    )
    evidence = StrategySignalEvidence(
        evidence_id=hashlib.sha256(
            f"{market.request_id}:{market.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=market,
        related_markets={},
        point_size=Decimal(str(metadata.point)),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )

    print("\n-- Registry-bound execution --")
    outcome = evaluate_strategy_signals(
        ref, config, evidence, (), context, evaluator
    )
    if outcome.data is None:
        print("Boundary rejected the evaluation:", outcome.error)
        return _UNAVAILABLE
    for signal in outcome.data:
        print(
            f"  {signal.signal_name}: active={signal.active} "
            f"side={signal.side} id={signal.signal_id[:16]}"
        )
    print("Evaluated bar:", market.records[-1].timestamp)

    print("\n-- Hash binding fails closed --")
    unbound = ConstantSignalEvaluator("0" * 64)
    rejected = evaluate_strategy_signals(
        ref, config, evidence, (), context, unbound
    )
    print("Status:", rejected.status)
    if rejected.error is not None:
        print("Error code:", rejected.error.code)
    print("\nSignals are evidence only; they authorize no execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
