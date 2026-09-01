"""WF-INDI-SEC: calculate and consume decision-time-qualified indicators."""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import pandas as pd
from app.kernel.identity import generate_id
from app.services.indicators import rsi
from app.services.strategy import (
    create_strategy_evaluator,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_signal_evidence,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    evaluate_strategy_signals,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
)
from tests.indicators.usage.workflows._support import live_bars

WORKFLOW_ID = "WF-INDI-SEC"
STAGES = (
    "Accept current normalized Data evidence.",
    "Calculate the requested official indicator.",
    "Qualify values by source availability at decision time.",
    "Pass the typed IndicatorResult through Strategy's public boundary.",
    "Return the Strategy's typed response and concrete signal rows.",
)


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _strategy_runtime(dataset: object, indicator: object) -> tuple[object, object]:
    """Evaluate the concrete Decomposing Trade strategy against genuine RSI."""
    repository_root = Path(__file__).parents[4]
    module_path = "app.services.strategy.evaluators.decomposing_trade"
    source_path = (
        repository_root
        / "app"
        / "services"
        / "strategy"
        / "evaluators"
        / "decomposing_trade.py"
    )
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    dependency_hash = hashlib.sha256(b"indicators:rsi:1.0.0").hexdigest()
    artifact_hash = hashlib.sha256(
        f"{source_hash}:{dependency_hash}".encode()
    ).hexdigest()
    timing = get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE")
    environment = get_strategy_environment("RESEARCH")
    policy = create_strategy_validation_policy(
        policy_version="policy-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    manifest = create_strategy_manifest(
        strategy_id="decomposing_trade",
        strategy_version="1.0.0",
        module_path=module_path,
        owner_ref="strategy-domain",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={
            "type": "object",
            "properties": {
                "rsi_period": {"type": "integer", "minimum": 2},
                "oversold": {"type": "number"},
                "overbought": {"type": "number"},
            },
            "required": ("rsi_period", "oversold", "overbought"),
            "additionalProperties": False,
        },
        required_data=("bars",),
        required_indicators=("rsi",),
        timing_policy=timing,
        permitted_environments=(environment,),
        source_hash=source_hash,
        artifact_hash=artifact_hash,
        dependency_hash=dependency_hash,
        provenance_refs=(str(source_path.relative_to(repository_root)),),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=4_096,
        decision_timeout_seconds=5,
    )
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=environment,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=artifact_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    config = create_validated_strategy_config(
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        config_schema_version=manifest.config_schema_version,
        normalized_parameters={"rsi_period": 2, "oversold": 30, "overbought": 70},
        config_hash=hashlib.sha256(b"rsi=2;oversold=30;overbought=70").hexdigest(),
        policy_version=policy.policy_version,
        request_id=request_id,
    )
    context = create_strategy_execution_context(
        environment=environment,
        decision_timestamp=datetime.now(UTC),
        timing_policy=timing,
        seed=7,
        interface_version="v1",
        request_id=request_id,
        workflow_id=generate_id("wf"),
        correlation_id=correlation_id,
        dependency_status={},
        snapshot_refs=(dataset.request_id,),
        max_diagnostic_bytes=8_192,
    )
    evidence = create_strategy_signal_evidence(
        evidence_id=hashlib.sha256(
            f"{dataset.request_id}:{dataset.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=dataset,
        related_markets={},
        point_size=Decimal("0.00001"),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    evaluator = create_strategy_evaluator(
        "decomposing_trade",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        module_path=manifest.module_path,
        source_hash=manifest.source_hash,
        artifact_hash=manifest.artifact_hash,
        dependency_hash=manifest.dependency_hash,
    )
    return (
        evaluate_strategy_signals(
            ref,
            config,
            evidence,
            (indicator,),
            context,
            evaluator,
        ),
        timing,
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    _feature_header(
        "WF-INDI-SEC: Decision-Time Consumption\n\n"
        "Purpose: Consume Indicators output at decision time through Strategy, "
        "preserving availability boundaries and returning typed strategy signals.\n\n"
        "Module flow:\n"
        "-> dataset + indicator request\n"
        "-> indicator availability-aware calculation\n"
        "-> strategy signal envelope"
    )
    print(f"{WORKFLOW_ID} — Decision-Time Consumption")
    print("INPUT BOUNDARY — genuine MT5 bars and official RSI evidence")
    # Stage 1
    _stage(1)
    dataset = live_bars()
    print_market_evidence(dataset)
    # Stage 2
    _stage(2)
    indicator = unwrap_indicator_response(rsi(dataset, period=2))
    print(_format_result(indicator))
    print(
        f"Data -> indicator_rows={indicator.manifest.row_count}, available_at={dataset.available_at}"
    )
    print_indicator_evidence(indicator, label="Decision-time RSI rows")
    # Stage 3
    _stage(3)
    outcome, timing = _strategy_runtime(dataset, indicator)
    print(_format_result(outcome))
    print(f"Data -> timing_policy={timing.value}")
    # Stage 4
    _stage(4)
    signals = unwrap_indicator_response(outcome)
    print(_format_result(signals))
    signal_frame = pd.DataFrame(
        {
            "signal_name": [signal.signal_name for signal in signals],
            "side": [signal.side for signal in signals],
            "active": [signal.active for signal in signals],
            "timestamp": [signal.timestamp for signal in signals],
            "facts": [dict(signal.facts) for signal in signals],
        }
    )
    print(
        f"Data -> signal_rows={len(signal_frame)}, active_signals={signal_frame['active'].sum()}"
    )
    print(signal_frame.to_string(index=False))
    # Stage 5
    _stage(5)
    print("OUTPUT BOUNDARY — Strategy response carrying concrete signal rows")
    print(_format_result(outcome))
    print(f"Data -> output_rows={len(signal_frame)}")


if __name__ == "__main__":
    main()
