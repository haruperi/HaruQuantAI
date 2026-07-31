# ruff: noqa: E402
"""Homogeneous full-domain usage program for app.services.indicators.

Ties all registered Indicators features (FEAT-INDI-01 through FEAT-INDI-06) together
into a single, sequential, step-by-step pipeline matching real-world operational
execution order:
1. Core Contracts, Registry Discovery and Request Validation (FEAT-INDI-01)
2. Candlestick Pattern Labelling (FEAT-INDI-02)
3. Trend and Moving-Average Calculation (FEAT-INDI-03)
4. Momentum Oscillator Calculation (FEAT-INDI-04)
5. Volatility and Range Calculation (FEAT-INDI-05)
6. Volume-Flow and Price-Volume Calculation (FEAT-INDI-06)
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, TypeVar

_data_dir = str(Path(tempfile.gettempdir()) / "haruquant-data")
Path(_data_dir).mkdir(exist_ok=True, parents=True)
os.environ.setdefault("DATA_DIR", _data_dir)
os.environ.setdefault("DATABASE_URL", "sqlite:///usage.db")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("WRITE_LOCK_LEASE_SECONDS", "30")
os.environ.setdefault("SQLITE_BUSY_TIMEOUT_SECONDS", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data, unwrap_data_response
from app.services.indicators import (
    adr,
    adx,
    atr,
    bollinger_bands,
    build_indicator_config,
    cmf,
    doji,
    ema,
    engulfing,
    get_capability_matrix,
    get_indicator,
    get_indicator_result_metadata,
    get_indicator_result_values,
    get_warmup_requirement,
    hull_ma,
    inside_bar,
    join_indicator_result,
    list_indicators,
    mfi,
    obv,
    pinbar,
    price_volume_distribution,
    rolling_volatility,
    rsi,
    sma,
    standard_deviation,
    validate_indicator,
    williams_r,
    wma,
    zigzag,
)

_ResponseT = TypeVar("_ResponseT")
MarketDataset = Any
StandardResponse = Any


def _unwrap_indicator_response(
    response: StandardResponse[_ResponseT],
) -> _ResponseT:
    """Return successful Indicators data or fail with its safe error message."""
    if response.status != "success" or response.data is None:
        detail = response.message or "unknown indicator failure"
        raise RuntimeError(detail)
    return response.data


def _unwrap_market_data_response(
    response: StandardResponse[MarketDataset],
) -> MarketDataset:
    """Return Data's raw dataset while preserving DataError failures."""
    return unwrap_data_response(
        response,
        operation="indicators.features.get_market_data",
        request_id=response.metadata.request_id,
    )


def _stage_banner(stage_num: int, title: str) -> None:
    """Print one clean stage header banner."""
    banner = f"Stage {stage_num}: {title}"
    print(f"\n\n{'=' * 88}\n{banner}\n{'=' * 88}")


def _print_values(result: object, label: str, *, rows: int = 5) -> None:
    """Print bounded calculated result values."""
    values = get_indicator_result_values(result)
    print(f"\n[{label}] ({len(values)} rows):")
    print(values.tail(rows).to_string())


def _dataset() -> MarketDataset:
    """Retrieve EURUSD M5 bars from Data for demonstration."""
    response = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=50,
    )
    return _unwrap_market_data_response(response)


def run_stage_1_core(dataset: MarketDataset) -> None:
    """Stage 1: Indicator Contracts, Registry Discovery and Request Validation."""
    _stage_banner(
        1, "Core Contracts, Registry Discovery & Request Validation (FEAT-INDI-01)"
    )

    indicators_list = _unwrap_indicator_response(list_indicators())
    print(f"Registered official indicators count: {len(indicators_list)}")

    sma_spec = _unwrap_indicator_response(get_indicator("sma"))
    print(
        f"SMA Spec: ID={sma_spec.indicator_id}, name={sma_spec.name}, version={sma_spec.indicator_version}"
    )

    matrix = _unwrap_indicator_response(get_capability_matrix())
    print(f"Capability Matrix indicators count: {len(matrix)}")

    config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    print(f"Config built: indicator_id={config.indicator_id}, source={config.source}")

    is_valid = _unwrap_indicator_response(validate_indicator("sma", dataset, config))
    print(
        f"Validation result for dataset ({dataset.symbol} {dataset.timeframe}): {is_valid.indicator_id}"
    )

    warmup = _unwrap_indicator_response(get_warmup_requirement("sma", config))
    print(f"Warmup requirement for SMA(14): {warmup.minimum_observations} records")

    sma_res = _unwrap_indicator_response(sma(dataset, period=14))
    meta = get_indicator_result_metadata(sma_res)
    print(f"Result Manifest Checksum: {meta['manifest']['output_checksum']}")

    joined = _unwrap_indicator_response(join_indicator_result(sma_res, dataset))
    print(f"Joined Dataset DataFrame shape: {joined.shape}")


def run_stage_2_candles(dataset: MarketDataset) -> None:
    """Stage 2: Candlestick Pattern Labelling."""
    _stage_banner(2, "Candlestick Pattern Labelling (FEAT-INDI-02)")

    doji_res = _unwrap_indicator_response(doji(dataset, threshold=0.1))
    _print_values(doji_res, "Doji Pattern")

    engulfing_res = _unwrap_indicator_response(engulfing(dataset))
    _print_values(engulfing_res, "Engulfing Pattern")

    pinbar_res = _unwrap_indicator_response(pinbar(dataset))
    _print_values(pinbar_res, "Pinbar Pattern")

    inside_res = _unwrap_indicator_response(inside_bar(dataset))
    _print_values(inside_res, "Inside Bar Pattern")


def run_stage_3_trend(dataset: MarketDataset) -> None:
    """Stage 3: Trend and Moving-Average Calculation."""
    _stage_banner(3, "Trend & Moving-Average Calculation (FEAT-INDI-03)")

    ema_res = _unwrap_indicator_response(ema(dataset, period=10))
    _print_values(ema_res, "EMA (10)")

    sma_res = _unwrap_indicator_response(sma(dataset, period=10))
    _print_values(sma_res, "SMA (10)")

    wma_res = _unwrap_indicator_response(wma(dataset, period=10))
    _print_values(wma_res, "WMA (10)")

    hull_res = _unwrap_indicator_response(hull_ma(dataset, period=10))
    _print_values(hull_res, "Hull MA (10)")

    bb_res = _unwrap_indicator_response(
        bollinger_bands(dataset, period=20, std_dev=2.0)
    )
    _print_values(bb_res, "Bollinger Bands (20, 2.0)")

    adx_res = _unwrap_indicator_response(adx(dataset, period=14))
    _print_values(adx_res, "ADX (14)")

    zigzag_res = _unwrap_indicator_response(zigzag(dataset, depth=5))
    _print_values(zigzag_res, "ZigZag (0.01)")


def run_stage_4_momentum(dataset: MarketDataset) -> None:
    """Stage 4: Momentum Oscillator Calculation."""
    _stage_banner(4, "Momentum Oscillator Calculation (FEAT-INDI-04)")

    rsi_res = _unwrap_indicator_response(rsi(dataset, period=14))
    _print_values(rsi_res, "RSI (14)")

    will_r_res = _unwrap_indicator_response(williams_r(dataset, period=14))
    _print_values(will_r_res, "Williams %R (14)")


def run_stage_5_volatility(dataset: MarketDataset) -> None:
    """Stage 5: Volatility and Range Calculation."""
    _stage_banner(5, "Volatility & Range Calculation (FEAT-INDI-05)")

    atr_res = _unwrap_indicator_response(atr(dataset, period=14))
    _print_values(atr_res, "ATR (14)")

    d1_dataset = _unwrap_market_data_response(
        get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="D1",
            limit=20,
        )
    )
    adr_res = _unwrap_indicator_response(adr(d1_dataset, period=5))
    _print_values(adr_res, "ADR (5, D1)")

    rvol_res = _unwrap_indicator_response(rolling_volatility(dataset, period=20))
    _print_values(rvol_res, "Rolling Volatility (20)")

    std_res = _unwrap_indicator_response(standard_deviation(dataset, period=20))
    _print_values(std_res, "Standard Deviation (20)")


def run_stage_6_volume(dataset: MarketDataset) -> None:
    """Stage 6: Volume-Flow and Price-Volume Calculation."""
    _stage_banner(6, "Volume-Flow & Price-Volume Calculation (FEAT-INDI-06)")

    cmf_res = _unwrap_indicator_response(cmf(dataset, period=20))
    _print_values(cmf_res, "CMF (20)")

    obv_res = _unwrap_indicator_response(obv(dataset))
    _print_values(obv_res, "OBV")

    mfi_res = _unwrap_indicator_response(mfi(dataset, period=14))
    _print_values(mfi_res, "MFI (14)")

    pvd_res = _unwrap_indicator_response(
        price_volume_distribution(dataset, period=20, bins=5)
    )
    _print_values(pvd_res, "Price-Volume Distribution (20, 5 bins)")


def main() -> None:
    """Execute the full domain pipeline in sequential operational order."""
    print(
        f"\n{'=' * 88}\nExecuting Full-Domain Indicators Pipeline (FEAT-INDI-01 through 06)\n{'=' * 88}"
    )
    dataset = _dataset()
    print(
        f"Loaded input dataset: symbol={dataset.symbol}, timeframe={dataset.timeframe}, records={dataset.record_count}"
    )

    run_stage_1_core(dataset)
    run_stage_2_candles(dataset)
    run_stage_3_trend(dataset)
    run_stage_4_momentum(dataset)
    run_stage_5_volatility(dataset)
    run_stage_6_volume(dataset)

    print(
        f"\n\n{'=' * 88}\nFull-Domain Indicators Pipeline Completed Successfully!\n{'=' * 88}\n"
    )


if __name__ == "__main__":
    main()
