"""Canonical single-asset backtest pipeline.

This is the production form of ``example_07_backtest_simulation`` from
``tests/legacy/08_simulator.py``: retrieve genuine provider bars including
warm-up, slice the measurement window, generate the exact tick stream, assemble
one canonical ``SimulationBacktestRequest``, run it through Simulation
authority, and build the Analytics performance report.

The pipeline owns no provider connectivity. Verified provider facts arrive from
the composition root, which keeps Brokers out of the Simulation domain.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from app.services.analytics import (
    build_performance_report,
    create_analytics_value,
    get_analytics_value_field,
)
from app.services.data import build_market_data_request, get_market_data
from app.services.simulator import (
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    run_backtest_async,
    unwrap_simulation_response,
)
from app.services.simulator.backtest_recipe.dependencies import (
    ExecutionSettings,
    ProviderFacts,
    StrategyBacktestDependencies,
    build_run_tick_dataset,
    dataset_hash,
)
from app.services.simulator.backtest_recipe.descriptors import (
    get_backtest_strategy_descriptor,
    resolve_strategy_parameters,
)
from app.utils import canonical_digest, create_auth_context, generate_id

#: Ordered metric keys reported for a completed run, mirroring the legacy
#: catalogue's printed performance report.
REPORT_METRIC_KEYS: tuple[tuple[str, str], ...] = (
    ("starting_equity", "Equity Start"),
    ("ending_equity", "Equity Final"),
    ("net_pnl", "Net PnL"),
    ("cagr", "CAGR"),
    ("volatility", "Volatility (Ann.)"),
    ("sharpe_ratio", "Sharpe Ratio"),
    ("sortino_ratio", "Sortino Ratio"),
    ("calmar_ratio", "Calmar Ratio"),
    ("max_drawdown", "Max. Drawdown"),
    ("max_drawdown_duration", "Max. Drawdown Duration"),
    ("trade_count", "# Trades"),
    ("win_rate", "Win Rate"),
    ("profit_factor", "Profit Factor"),
    ("payoff_ratio", "Payoff Ratio"),
    ("expectancy", "Expectancy"),
    ("average_trade_duration", "Avg. Trade Duration"),
    ("total_commission", "Commission"),
    ("total_swap", "Swap"),
    ("total_cost_drag", "Total Cost Drag"),
    ("benchmark_alpha", "Alpha"),
    ("benchmark_beta", "Beta"),
    ("benchmark_correlation", "Benchmark Correlation"),
    ("tracking_error", "Tracking Error"),
    ("information_ratio", "Information Ratio"),
)

#: Pipeline stages reported as progress, in execution order.
RUN_STAGES: tuple[str, ...] = (
    "market_retrieval",
    "tick_generation",
    "simulation",
    "analytics",
)

_DEFAULT_BAR_LIMIT = 10_000
_MAX_BAR_LIMIT = 1_000_000


@dataclass(frozen=True, slots=True)
class BacktestRunConfig:
    """Complete operator-chosen configuration for one backtest run."""

    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    strategy_id: str
    parameters: Mapping[str, object] = field(default_factory=dict)
    initial_balance: Decimal = Decimal("10000.00")
    account_currency: str = "USD"
    volume: Decimal = Decimal("0.1")
    commission_per_lot_per_side: Decimal = Decimal(7)
    spread_points: Decimal = Decimal(10)
    slippage_points: Decimal = Decimal(1)
    seed: int = 7
    bar_limit: int = _DEFAULT_BAR_LIMIT
    source_id: str = "mt5"
    account_id: str = "backtest-recipe"

    def validate(self) -> dict[str, object]:
        """Validate bounded, self-consistent run configuration.

        The strategy is resolved here so an unregistered, unrunnable, or
        misconfigured selection is refused before any provider is contacted.

        Returns:
            Resolved strategy parameters for this run.

        Raises:
            ValueError: If any declared bound, ordering, or strategy rule is
                violated.
        """
        if self.start >= self.end:
            raise ValueError("start must be earlier than end")
        if self.initial_balance <= 0:
            raise ValueError("initial_balance must be positive")
        if self.volume <= 0:
            raise ValueError("volume must be positive")
        if self.commission_per_lot_per_side < 0:
            raise ValueError("commission_per_lot_per_side cannot be negative")
        if self.spread_points < 0 or self.slippage_points < 0:
            raise ValueError("spread and slippage points cannot be negative")
        if not 0 < self.bar_limit <= _MAX_BAR_LIMIT:
            message = f"bar_limit must be between 1 and {_MAX_BAR_LIMIT}"
            raise ValueError(message)
        descriptor = get_backtest_strategy_descriptor(self.strategy_id)
        if not descriptor.runnable:
            raise ValueError(
                descriptor.unavailable_reason
                or "strategy is unavailable for backtesting"
            )
        return resolve_strategy_parameters(descriptor, dict(self.parameters))


type ProgressCallback = Callable[[str, str], None]


def _noop_progress(stage: str, detail: str) -> None:
    """Discard progress when the caller supplies no sink.

    Args:
        stage: Current pipeline stage name.
        detail: Human-readable stage detail.
    """
    del stage, detail


def _warmup_start(config: BacktestRunConfig, warmup_bars: int) -> datetime:
    """Return the retrieval start covering the strategy's warm-up window.

    Args:
        config: Operator-chosen run configuration.
        warmup_bars: Bars the strategy must see before its first decision.

    Returns:
        UTC instant from which bars must be retrieved.
    """
    minutes = _timeframe_minutes(config.timeframe)
    # Widen generously for non-trading hours and weekends so the measurement
    # window itself is never consumed by warm-up.
    span = timedelta(minutes=minutes * warmup_bars * 3)
    return config.start - max(span, timedelta(days=1))


_TIMEFRAME_MINUTES: Mapping[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1_440,
    "W1": 10_080,
    "MN1": 43_200,
}


def _timeframe_minutes(timeframe: str) -> int:
    """Return the canonical minute span of one timeframe bucket.

    Args:
        timeframe: Canonical Data timeframe identifier.

    Returns:
        Minutes covered by one bar.

    Raises:
        ValueError: If the timeframe is not a canonical Data timeframe.
    """
    minutes = _TIMEFRAME_MINUTES.get(timeframe)
    if minutes is None:
        message = f"unsupported timeframe: {timeframe}"
        raise ValueError(message)
    return minutes


def _analytics_config(created_at: datetime) -> object:
    """Build bounded Analytics settings for the run report.

    Args:
        created_at: UTC evidence timestamp for the explicit zero-rate model.

    Returns:
        Opaque Analytics run configuration.
    """
    risk_free_rate = create_analytics_value(
        "RiskFreeRateEvidence",
        rate=Decimal(0),
        unit="annual_decimal",
        source="backtest-recipe-zero-rate-assumption",
        as_of=created_at,
    )
    statistics = create_analytics_value(
        "StatisticalValidationConfig",
        seed=7,
        bootstrap_iterations=100,
        permutation_iterations=100,
        confidence=0.95,
        alpha=0.05,
    )
    return create_analytics_value(
        "AnalyticsRunConfig",
        max_warning_detail_bytes=4_096,
        max_trades=10_000,
        max_equity_points=10_000,
        max_benchmark_points=10_000,
        max_statistical_observations=10_000,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=2_000_000,
        risk_free_rate=risk_free_rate,
        statistics=statistics,
    )


def _authority(request: object) -> object:
    """Build simulation-only authority aligned with one request.

    Args:
        request: Canonical Simulation request.

    Returns:
        Validated simulation-scoped authorization context.
    """
    typed = cast("Any", request)
    return create_auth_context(
        principal_id="backtest-recipe",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="dev",
        request_id=typed.request_id,
        workflow_id=typed.workflow_id,
        correlation_id=typed.correlation_id,
        issued_at=typed.start - timedelta(days=1),
    )


def _retrieve_bars(config: BacktestRunConfig, warmup_bars: int) -> object:
    """Retrieve genuine provider bars covering warm-up and measurement.

    Args:
        config: Operator-chosen run configuration.
        warmup_bars: Bars required before the first decision.

    Returns:
        Canonical Data-owned bar dataset.

    Raises:
        ValueError: If the provider returns insufficient history.
    """
    request = build_market_data_request(
        source_id=config.source_id,
        symbol=config.symbol,
        data_kind="bars",
        timeframe=config.timeframe,
        start=_warmup_start(config, warmup_bars),
        end=config.end,
        limit=config.bar_limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    dataset = get_market_data(request).data
    if dataset is None or len(cast("Any", dataset).records) < warmup_bars:
        message = (
            f"{config.source_id} returned insufficient {config.symbol} "
            f"{config.timeframe} history for a {warmup_bars}-bar warm-up"
        )
        raise ValueError(message)
    return dataset


def _measurement_dataset(dataset: object, config: BacktestRunConfig) -> object:
    """Slice the measurement window out of the retrieved dataset.

    Args:
        dataset: Retrieved dataset including warm-up history.
        config: Operator-chosen run configuration.

    Returns:
        Dataset restricted to the measurement window.

    Raises:
        ValueError: If no record falls inside the measurement window.
    """
    typed = cast("Any", dataset)
    records = tuple(
        record
        for record in typed.records
        if config.start <= record.timestamp <= config.end
    )
    if not records:
        raise ValueError("provider returned no records in the measurement period")
    quality = typed.quality_report.model_copy(
        update={"record_count": len(records), "checked_count": len(records)}
    )
    return typed.model_copy(
        update={
            "records": records,
            "record_count": len(records),
            "start": records[0].timestamp,
            "end": records[-1].timestamp,
            "available_at": records[-1].available_at,
            "quality_report": quality,
        }
    )


def _canonical_request(
    *,
    measurement: object,
    tick_dataset: object,
    config: BacktestRunConfig,
    parameters: Mapping[str, object],
    facts: ProviderFacts,
    descriptor_version: str,
) -> object:
    """Assemble one canonical ``SimulationBacktestRequest``.

    Args:
        measurement: Measurement-window bar dataset.
        tick_dataset: Exact generated tick dataset.
        config: Operator-chosen run configuration.
        parameters: Resolved strategy parameters.
        facts: Verified provider facts.
        descriptor_version: Registered strategy version.

    Returns:
        Canonical Simulation backtest request value.
    """
    typed_measurement = cast("Any", measurement)
    typed_ticks = cast("Any", tick_dataset)
    specification = facts.specification
    initial_authority_state = {
        "account": {
            "balance": config.initial_balance,
            "currency": config.account_currency,
        },
        "orders": (),
        "positions": (),
        "deals": (),
        "ownership": {"mode": "exclusive"},
    }
    values: dict[str, Any] = {
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "strategy_id": config.strategy_id,
        "strategy_version": descriptor_version,
        "strategy_config_ref": "backtest-recipe-config",
        "strategy_config_hash": canonical_digest(dict(parameters)),
        "data_ref": f"{config.source_id}:{config.symbol}:{config.timeframe}",
        "data_version": "v1",
        "data_hash": dataset_hash(tick_dataset),
        "tick_generation_ref": "tick-profile",
        "tick_generation_version": "v1",
        "tick_generation_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "risk-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": config.symbol,
        "timeframe": config.timeframe,
        "start": typed_ticks.start,
        "end": typed_ticks.end,
        "parameters": dict(parameters),
        "initial_balance": config.initial_balance,
        "account_currency": config.account_currency,
        "asset_class": "FX",
        "seed": config.seed,
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "canonical": True,
        "execution_model_ref": "execution-model-v1",
        "execution_model_hash": "e" * 64,
        "calculation_model_hash": "f" * 64,
        "calculation_artifact_checksum": "1" * 64,
        "calibration_artifact_checksum": "2" * 64,
        "realism_stream_identity_hash": "3" * 64,
        "source_lineage_hash": "4" * 64,
        "tick_lineage_hash": "5" * 64,
        "market_evidence_class": "genuine_bid_ask_ticks",
        "decision_instant_policy": "point_in_time_available_at",
        "provider_specification_revisions": (
            {
                "revision_id": f"{config.source_id}-current-"
                f"{specification['checksum']}",
                "checksum": specification["checksum"],
                "provider": specification["broker"],
                "server": specification["server"],
                "environment": specification["environment"],
                "account_digest": specification["account_digest"],
                "symbol": specification["provider_symbol"],
                "observed_at": datetime.fromisoformat(
                    str(specification["observed_at"])
                ),
                "effective_from": typed_ticks.start,
                "effective_to": None,
                "historical_provenance": {
                    "specification_basis": "current_provider_snapshot",
                    "session_basis": "exact_generated_tick_dataset",
                    "historical_schedule_authority": False,
                },
            },
        ),
        "initial_authority_state_hash": canonical_digest(initial_authority_state),
        "certification_target": "demo",
        "close_open_positions_at_end": True,
    }
    del typed_measurement
    values["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_config_hash(values),
        operation="calculate_simulation_backtest_config_hash",
    )
    return create_simulation_value("SimulationBacktestRequest", **values)


def _report_metrics(report: object) -> dict[str, str]:
    """Extract calculated Analytics metrics from one performance report.

    Args:
        report: Canonical Analytics performance report.

    Returns:
        Mapping from metric key to its rendered calculated value.

    Note:
        Analytics reports many metrics once per source context (``all``,
        ``long``, ``short``). The portfolio-level ``all`` context always wins, so
        a figure like ``trade_count`` describes the whole run rather than
        whichever directional section happened to be evaluated last. Metrics that
        exist in no ``all`` context — the cost totals among them — are still
        reported from the context that does define them.
    """
    preferred: dict[str, str] = {}
    fallback: dict[str, str] = {}
    for section in get_analytics_value_field(report, "sections"):
        for metric in get_analytics_value_field(section, "metrics"):
            if get_analytics_value_field(metric, "status") != "calculated":
                continue
            key = str(get_analytics_value_field(metric, "metric_key"))
            value = str(get_analytics_value_field(metric, "value"))
            if str(get_analytics_value_field(metric, "source_context")) == "all":
                preferred[key] = value
            else:
                fallback.setdefault(key, value)
    return {**fallback, **preferred}


def _render_entry(value: object) -> str:
    """Render one owner value as its stable code, or its full text.

    Args:
        value: Owner-supplied warning, flag, or plain value.

    Returns:
        The value's ``code`` when it declares one, else its rendered text.
    """
    code = getattr(value, "code", None)
    return str(code) if code is not None else str(value)


def _text_tuple(values: object) -> tuple[str, ...]:
    """Render an owner-domain sequence as bounded, de-duplicated text.

    Two problems are solved here. Owner values may be dataclasses holding
    ``MappingProxyType``, which cannot be deep-copied and therefore cannot cross
    a JSON boundary. They also repeat heavily — one report emitted the same
    warning code ninety times, once per trade per section. Entries are rendered
    to their stable code and collapsed with an explicit count, so nothing is
    hidden and the payload stays bounded.

    Args:
        values: Any owner-supplied sequence, or a non-sequence.

    Returns:
        Rendered entries in first-seen order, empty when there is nothing to
        render. A repeated entry carries an explicit ``xN`` count.
    """
    if values is None:
        return ()
    if isinstance(values, str):
        return (values,)
    try:
        rendered = [_render_entry(value) for value in cast("Any", values)]
    except TypeError:
        return (_render_entry(values),)
    counts: dict[str, int] = {}
    for entry in rendered:
        counts[entry] = counts.get(entry, 0) + 1
    return tuple(
        entry if count == 1 else f"{entry} x{count}" for entry, count in counts.items()
    )


def _public_quality(dataset: object) -> dict[str, Any]:
    """Build the JSON-safe quality projection returned to the caller.

    Args:
        dataset: Retrieved dataset including warm-up history.

    Returns:
        Plain-text quality evidence safe to serialize at the boundary.
    """
    metadata = _quality_metadata(dataset)
    return {
        "status": str(metadata["status"]),
        "decision": str(metadata["decision"]),
        "score": str(metadata["score"]),
        "flags": _text_tuple(metadata["flags"]),
        "warnings": _text_tuple(metadata["warnings"]),
        "calendar_closure_provenance": _text_tuple(
            metadata["calendar_closure_provenance"]
        ),
    }


def _quality_metadata(dataset: object) -> dict[str, Any]:
    """Build bounded Data quality evidence for the report source.

    Args:
        dataset: Retrieved dataset including warm-up history.

    Returns:
        Quality status, decision, score, flags, warnings, and provenance.
    """
    report = cast("Any", dataset).quality_report
    return {
        "status": report.quality_status,
        "decision": report.quality_decision,
        "score": str(report.quality_score),
        "flags": tuple(issue.code for issue in report.issues),
        "warnings": report.warnings,
        "calendar_closure_provenance": tuple(
            sample
            for issue in report.issues
            if issue.code == "CALENDAR_SUPPORTED_CLOSURE"
            for sample in issue.samples
        ),
    }


async def run_strategy_backtest(
    config: BacktestRunConfig,
    *,
    facts: ProviderFacts,
    progress: ProgressCallback = _noop_progress,
    root: Path | None = None,
) -> dict[str, Any]:
    """Run one canonical single-asset backtest and build its report.

    Args:
        config: Operator-chosen run configuration.
        facts: Verified provider facts for this run.
        progress: Sink receiving ``(stage, detail)`` updates.
        root: Isolated run directory; a temporary directory when absent.

    Returns:
        Complete run evidence: metrics, quality, trades, and identities.

    Raises:
        ValueError: If configuration, evidence, or the strategy is unusable.
    """
    parameters = config.validate()
    descriptor = get_backtest_strategy_descriptor(config.strategy_id)
    warmup_bars = descriptor.warmup_bars(parameters)

    progress("market_retrieval", f"retrieving {config.symbol} {config.timeframe} bars")
    dataset = _retrieve_bars(config, warmup_bars)
    measurement = _measurement_dataset(dataset, config)
    measurement_count = len(cast("Any", measurement).records)
    progress(
        "market_retrieval",
        f"retrieved {len(cast('Any', dataset).records)} bars "
        f"({measurement_count} in the measurement window)",
    )

    progress("tick_generation", "generating the canonical tick stream")
    tick_dataset = build_run_tick_dataset(
        measurement,
        timeframe=config.timeframe,
        spread_points=config.spread_points,
    )
    request = _canonical_request(
        measurement=measurement,
        tick_dataset=tick_dataset,
        config=config,
        parameters=parameters,
        facts=facts,
        descriptor_version=descriptor.strategy_version,
    )
    progress("tick_generation", "canonical request assembled")

    with tempfile.TemporaryDirectory() as temporary:
        run_root = root or Path(temporary)
        dependencies = StrategyBacktestDependencies(
            root=run_root,
            dataset=dataset,
            tick_dataset=tick_dataset,
            descriptor=descriptor,
            parameters=parameters,
            facts=facts,
            execution=ExecutionSettings(
                volume=config.volume,
                commission_per_lot_per_side=config.commission_per_lot_per_side,
                spread_points=config.spread_points,
                slippage_points=config.slippage_points,
            ),
            account_id=config.account_id,
        )
        progress("simulation", f"running {measurement_count} bars through Simulation")
        response = await run_backtest_async(request, _authority(request), dependencies)
        result = cast(
            "Any",
            unwrap_simulation_response(response, operation="run_backtest_async"),
        )
        progress(
            "simulation",
            f"simulation complete with {len(result.closed_trades)} closed trades",
        )

        progress("analytics", "building the performance report")
        typed_request = cast("Any", request)
        source = {
            "contract_version": result.contract_version,
            "schema_id": result.schema_id,
            "source_id": result.run_id,
            "phase": "backtest",
            "window_start": config.start,
            "window_end": config.end,
            "strategy_id": typed_request.strategy_id,
            "strategy_version": typed_request.strategy_version,
            "symbols": (typed_request.symbol,),
            "timeframe": typed_request.timeframe,
            "closed_trades": tuple(
                trade.model_dump(mode="python", warnings=False)
                for trade in result.closed_trades
            ),
            "quality_metadata": _quality_metadata(dataset),
            "source_metadata": {"provider": config.source_id, "route": "sim"},
        }
        report = unwrap_simulation_response(
            build_performance_report(
                source,
                source_contract="simulation.result",
                request_id=generate_id("req"),
                correlation_id=typed_request.correlation_id,
                created_at=cast("Any", measurement).end,
                initial_balance=typed_request.initial_balance,
                account_currency=typed_request.account_currency,
                config=_analytics_config(cast("Any", measurement).end),
                benchmark=measurement,
            ),
            operation="build_performance_report",
        )
        progress("analytics", "performance report ready")

    return {
        "run_id": result.run_id,
        "engine_version": result.engine_version,
        "config_hash": typed_request.config_hash,
        "strategy_id": descriptor.strategy_id,
        "strategy_version": descriptor.strategy_version,
        "strategy_label": descriptor.label,
        "parameters": {key: str(value) for key, value in parameters.items()},
        "symbol": config.symbol,
        "timeframe": config.timeframe,
        "start": config.start,
        "end": config.end,
        "initial_balance": str(config.initial_balance),
        "account_currency": config.account_currency,
        "bar_count": measurement_count,
        "warmup_bars": warmup_bars,
        "closed_trade_count": len(result.closed_trades),
        "metrics": _report_metrics(report),
        "quality": _public_quality(dataset),
        "quality_flags": _text_tuple(
            get_analytics_value_field(report, "quality_flags")
        ),
        "caveats": _text_tuple(get_analytics_value_field(report, "caveats")),
    }


def utc_now() -> datetime:
    """Return the current UTC instant.

    Returns:
        Timezone-aware current instant.
    """
    return datetime.now(UTC)


__all__ = (
    "REPORT_METRIC_KEYS",
    "RUN_STAGES",
    "BacktestRunConfig",
    "ProgressCallback",
    "run_strategy_backtest",
    "utc_now",
)
