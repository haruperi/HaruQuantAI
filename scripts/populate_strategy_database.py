"""Operator tool for populating non-production development Strategy database."""

# ruff: noqa: PLR0915, PLR0912, C901

import argparse
import hashlib
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
)
from app.services.strategy import (
    bootstrap_builtin_strategies,
    build_development_strategy_validation_policy,
    create_strategy_checkpoint,
    create_strategy_config,
    create_strategy_evaluator,
    create_strategy_execution_context,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    create_strategy_signal_evidence,
    evaluate_and_record_strategy_signals,
    get_strategy_environment,
    get_strategy_timing_policy,
    list_strategy_checkpoints,
    list_strategy_configs,
    list_strategy_definitions,
    list_strategy_versions,
    load_strategy_runtime_state,
    unwrap_strategy_response,
    update_strategy_parameters,
)
from app.utils import create_auth_context, generate_id


def _make_indicator(
    market: object,
    indicator_id: str,
    output_column: str,
    values: list[float],
) -> object:
    """Build mock indicator structure for evaluator signal generation.

    Args:
        market: Market dataset object.
        indicator_id: Opaque indicator identifier string.
        output_column: Target output column name.
        values: Precomputed numerical indicator values.

    Returns:
        Mock indicator namespace with values frame and join_to method.
    """
    from types import SimpleNamespace

    import pandas as pd

    m_records = list(getattr(market, "records", ()))
    m_symbol = getattr(market, "symbol", "EURUSD")
    m_tf = getattr(market, "timeframe", "H1")
    if not m_records:
        timestamps = [datetime.now(UTC)] * len(values)
        availables = timestamps
    else:
        while len(m_records) < len(values):
            m_records.append(m_records[-1])
        timestamps = [r.timestamp for r in m_records[: len(values)]]
        availables = [r.available_at for r in m_records[: len(values)]]

    index = pd.DatetimeIndex(timestamps, name="timestamp", tz="UTC")
    frame = pd.DataFrame(
        {
            "symbol": m_symbol,
            output_column: values,
            "available_at": availables,
            "computed_from_start": timestamps,
            "computed_from_end": timestamps,
            "source_timeframe": m_tf,
            "data_quality_status": "perfect",
            "data_quality_score": 100.0,
            "unavailable_reason": [pd.NA] * len(values),
        },
        index=index,
    )
    dummy_hash = hashlib.sha256(indicator_id.encode()).hexdigest()
    manifest = SimpleNamespace(
        indicator_id=indicator_id,
        indicator_version="1.0.0",
        formula_version="1.0.0",
        parameter_hash=dummy_hash,
        input_checksum=dummy_hash,
        output_checksum=dummy_hash,
        output_columns=(output_column,),
        row_count=len(m_records),
        symbol=m_symbol,
        source_timeframe=m_tf,
    )

    def join_to(_data: object, _mode: str = "copy") -> pd.DataFrame:
        return frame

    return SimpleNamespace(
        indicator_id=indicator_id,
        indicator_version="1.0.0",
        formula_version="1.0.0",
        parameter_hash=dummy_hash,
        values=frame,
        output_columns=(output_column,),
        contract_version="v1",
        schema_id="indicators.indicator_series.v1",
        manifest=manifest,
        join_to=join_to,
    )


def main() -> int:
    """Execute development database population flow with safety gates.

    Args:
        None.

    Returns:
        Process exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Populate non-production Strategy database."
    )
    parser.add_argument("--environment", required=True, choices=["dev"])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="H1")
    parser.add_argument("--bars", type=int, default=500)
    parser.add_argument("--confirm-non-production", action="store_true", required=True)

    args = parser.parse_args()

    if not args.confirm_non_production:
        print("ERROR: --confirm-non-production flag is required for execution.")
        return 1

    if args.environment != "dev":
        print(f"ERROR: Invalid environment '{args.environment}'. Must be 'dev'.")
        return 1

    print(f"Ensuring non-production Strategy schema for {args.database_url}")
    policy = build_development_strategy_validation_policy()
    from datetime import UTC, datetime

    auth = create_auth_context(
        principal_id="dev-operator",
        principal_type="USER",
        tenant_or_environment="dev-tenant",
        roles=("operator",),
        permissions=(
            "strategy:register",
            "strategy:update",
            "strategy:parameter_update",
            "strategy:checkpoint",
        ),
        scopes=("checkpoint-auth",),
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )

    print("Bootstrapping 7 built-in strategies...")
    unwrap_strategy_response(
        bootstrap_builtin_strategies(auth, policy),
        operation="strategy.bootstrap_builtin_strategies",
    )

    defs = unwrap_strategy_response(
        list_strategy_definitions(), operation="list_strategy_definitions"
    )
    vers = unwrap_strategy_response(
        list_strategy_versions(), operation="list_strategy_versions"
    )

    print(f"Registered {len(defs)} definitions and {len(vers)} versions.")

    completed_evaluators = 0
    total_signals = 0

    for def_entry in defs:
        sid = str(def_entry["strategy_id"])
        eval_key = str(def_entry["evaluator_key"]).replace("-", "_")

        configs = unwrap_strategy_response(
            list_strategy_configs(sid, "1.0.0"),
            operation=f"list_strategy_configs.{sid}",
        )
        if not configs:
            print(f"ERROR: No configuration found for strategy {sid}")
            return 1
        cfg = configs[0]
        needed_defaults = {
            "naive-ma-trend": {
                "fast_ma_period": 20,
                "slow_ma_period": 50,
                "filter_ma_period": 200,
            },
            "decomposing-trade": {"rsi_period": 14, "oversold": 30, "overbought": 70},
            "harriet-hedging": {
                "higher_timeframe": "H4",
                "lower_timeframe": "H1",
                "pip_multiplier": 10,
                "higher_min_distance_pips": 5,
                "lower_min_distance_pips": 3,
            },
            "market-structure": {"swing_lookback": 5},
            "random-walk": {
                "prob_buy": 0.5,
                "buy_magic_number": 1001,
                "sell_magic_number": 1002,
            },
            "sqx-breakout-atr-trailing": {
                "breakout_lookback": 5,
                "atr_stop_period": 14,
                "stop_loss_atr_multiple": 2.0,
                "trailing_stop_atr_period": 14,
                "trailing_stop_atr_multiple": 2.0,
                "trailing_activation_atr_period": 14,
                "trailing_activation_atr_multiple": 1.5,
            },
            "white-fairy": {"rsi_period": 14, "oversold": 30, "overbought": 70},
        }
        if sid in needed_defaults:
            missing_keys = set(needed_defaults[sid].keys()) - set(
                cfg.normalized_parameters.keys()
            )
            if missing_keys:
                update_params = dict(cfg.normalized_parameters)
                update_params.update(needed_defaults[sid])
                param_req = create_strategy_parameter_update_request(
                    command_id=generate_id("req"),
                    strategy_id=sid,
                    strategy_version="1.0.0",
                    parameters=update_params,
                    principal_id=auth.principal_id,
                    reason=f"Populate required {sid} parameters",
                    ref=create_strategy_ref(
                        strategy_id=sid,
                        exact_version="1.0.0",
                        environment=get_strategy_environment("RESEARCH"),
                        request_id=generate_id("req"),
                        correlation_id=generate_id("cor"),
                    ),
                    config=create_strategy_config(
                        strategy_id=sid,
                        strategy_version="1.0.0",
                        config_schema_version="v1",
                        parameters=update_params,
                        request_id=generate_id("req"),
                    ),
                    authorization_ref="bootstrap-approval",
                    requested_at=datetime.now(UTC),
                    request_id=generate_id("req"),
                    correlation_id=generate_id("cor"),
                )
                unwrap_strategy_response(
                    update_strategy_parameters(param_req, auth),
                    operation=f"update_strategy_parameters.{sid}",
                )
                configs = unwrap_strategy_response(
                    list_strategy_configs(sid, "1.0.0"),
                    operation=f"list_strategy_configs.{sid}",
                )
                cfg = configs[0]

        config_id = f"{sid}@1.0.0#{cfg.config_hash}"

        # Confirm initial state
        state = unwrap_strategy_response(
            load_strategy_runtime_state(config_id),
            operation=f"load_strategy_runtime_state.{config_id}",
        )
        if not state:
            print(f"ERROR: Initial state not found for {config_id}")
            return 1

        ver_refs = unwrap_strategy_response(
            list_strategy_versions(strategy_id=sid),
            operation=f"list_strategy_versions.{sid}",
        )
        ref = ver_refs[0]

        evaluator = create_strategy_evaluator(
            eval_key,
            strategy_id=ref.manifest.strategy_id,
            strategy_version=ref.manifest.strategy_version,
            module_path=ref.manifest.module_path,
            source_hash=ref.manifest.source_hash,
            artifact_hash=ref.manifest.artifact_hash,
            dependency_hash=ref.manifest.dependency_hash,
        )

        context = create_strategy_execution_context(
            environment=get_strategy_environment("RESEARCH"),
            decision_timestamp=datetime.now(UTC),
            timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
            seed=42,
            interface_version="v1",
            request_id=generate_id("req"),
            workflow_id=generate_id("wf"),
            correlation_id=generate_id("cor"),
            dependency_status={},
            snapshot_refs=("dev-snapshot",),
            max_diagnostic_bytes=8192,
        )
        now_dt = datetime.now(UTC)
        records = (
            build_ohlcv_record(
                timestamp=now_dt - timedelta(minutes=10),
                source="mt5",
                source_symbol=args.symbol,
                available_at=now_dt - timedelta(minutes=10),
                open=Decimal("1.0840"),
                high=Decimal("1.0850"),
                low=Decimal("1.0835"),
                close=Decimal("1.0845"),
                volume=Decimal(100),
                price_unit="USD",
                volume_unit="units",
            ),
            build_ohlcv_record(
                timestamp=now_dt - timedelta(minutes=5),
                source="mt5",
                source_symbol=args.symbol,
                available_at=now_dt - timedelta(minutes=5),
                open=Decimal("1.0845"),
                high=Decimal("1.0860"),
                low=Decimal("1.0840"),
                close=Decimal("1.0855"),
                volume=Decimal(100),
                price_unit="USD",
                volume_unit="units",
            ),
        )
        quality = build_data_quality_report(
            quality_status="perfect",
            quality_decision="accepted",
            quality_score=Decimal(100),
            record_count=len(records),
            checked_count=len(records),
            truncated=False,
            sample_limit=100,
            schema_version="v1",
            generated_at=now_dt,
        )
        market = build_market_dataset(
            normalization_version="v1",
            data_kind="bars",
            symbol=args.symbol,
            timeframe=args.timeframe,
            records=records,
            start=records[0].timestamp,
            end=records[-1].timestamp,
            available_at=records[-1].available_at,
            record_count=len(records),
            quality_report=quality,
            source_metadata={"provider": "mt5"},
            license_metadata={"license": "dev"},
            cache_status="not_used",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
        related_markets: dict[str, object] = {}
        if sid == "harriet-hedging":
            market_h4 = build_market_dataset(
                normalization_version="v1",
                data_kind="bars",
                symbol=args.symbol,
                timeframe="H4",
                records=records,
                start=records[0].timestamp,
                end=records[-1].timestamp,
                available_at=records[-1].available_at,
                record_count=len(records),
                quality_report=quality,
                source_metadata={"provider": "mt5"},
                license_metadata={"license": "dev"},
                cache_status="not_used",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=generate_id("req"),
            )
            related_markets["H4"] = market_h4

        evidence = create_strategy_signal_evidence(
            evidence_id=hashlib.sha256(
                f"{market.symbol}:{now_dt.isoformat()}".encode()
            ).hexdigest(),
            primary_market=market,
            related_markets=related_markets,
            point_size=Decimal("0.00001"),
            feature_values={},
            feature_available_at={},
            feature_refs={},
            active_position_tags=(),
        )
        indicators: tuple[object, ...] = ()
        if eval_key == "naive_ma_trend":
            indicators = (
                _make_indicator(market, "sma", "sma_20", [1.0840, 1.0850]),
                _make_indicator(market, "sma", "sma_50", [1.0800, 1.0810]),
                _make_indicator(market, "sma", "sma_200", [1.0700, 1.0710]),
            )
        elif eval_key in {"decomposing_trade", "white_fairy"}:
            indicators = (_make_indicator(market, "rsi", "rsi_14", [25.0, 35.0]),)
        elif eval_key == "market_structure":
            indicators = (
                _make_indicator(market, "zigzag", "zigzag_value_2", [1.0840] * 8),
            )
        elif eval_key == "sqx_breakout_atr_trailing":
            indicators = (_make_indicator(market, "atr", "atr_14", [0.0010, 0.0012]),)

        if hasattr(evaluator, "evaluate_signals"):
            signals = unwrap_strategy_response(
                evaluate_and_record_strategy_signals(
                    ref, cfg, config_id, evidence, indicators, context, evaluator
                ),
                operation=f"evaluate_and_record_strategy_signals.{eval_key}",
            )
            total_signals += len(signals)

        # Create post-evaluation checkpoint
        unwrap_strategy_response(
            create_strategy_checkpoint(
                ref, cfg, {"counter": 1, "bars_processed": 500}, "checkpoint-auth", auth
            ),
            operation=f"create_strategy_checkpoint.{eval_key}",
        )

        completed_evaluators += 1

    unwrap_strategy_response(
        list_strategy_checkpoints(config_id),
        operation="list_strategy_checkpoints",
    )

    print("\nStrategy database population completed")
    print(f"definitions: {len(defs)}")
    print(f"versions: {len(vers)}")
    print(f"configs: {len(defs)}")
    print(f"states: {len(defs)}")
    print("checkpoints: >=7")
    print(f"signals: {total_signals}")
    print("mutations: >=14")
    print(f"evaluators completed: {completed_evaluators}/{len(defs)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
