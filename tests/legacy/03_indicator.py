# ruff: noqa: BLE001
"""Direct, copyable usage catalogue for the Indicators service public API using real MT5 data.

This supplemental catalogue preserves the scenarios from the legacy Indicator example
using only real MT5 market data retrieved through the ``app.services.data`` public API
and computed via ``app.services.indicators`` package-root boundaries.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.services.data import (
    build_market_data_request,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    get_market_data,
)
from app.services.indicators import (
    atr,
    bollinger_bands,
    cmf,
    doji,
    ema,
    engulfing,
    get_capability_matrix,
    get_indicator_result_metadata,
    get_indicator_result_values,
    hull_ma,
    inside_bar,
    join_indicator_result,
    list_indicators,
    macd,
    mfi,
    obv,
    pinbar,
    pivots,
    rsi,
    sma,
    standard_deviation,
    williams_r,
    wma,
)
from app.utils import generate_id, load_broker_provider_settings

_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = _START + timedelta(hours=1000)
_PROVIDER_FIELDS = {
    "MT5_ENABLED": "mt5_enabled",
    "MT5_TERMINAL_PATH": "mt5_terminal_path",
}


def _header(title: str) -> None:
    """Print a bounded example heading.

    Args:
        title: Human-readable example title.

    Returns:
        None.
    """
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


@contextmanager
def _provider_runtime_context(*, offline: bool) -> Iterator[bool]:
    """Inject database-backed provider settings for a verified usage run.

    Args:
        offline: Whether to suppress external provider reads.

    Yields:
        Whether provider reads are enabled for this run.

    Raises:
        ValueError: If persisted settings do not prove a dev/demo boundary.
    """
    if offline:
        yield False
        return
    from app.services.api import (
        build_system_broker_connection_config,
        get_api_settings,
        get_system_settings,
    )

    record = get_system_settings(request_id=generate_id("req"))
    environment = record.settings.get("ENVIRONMENT", get_api_settings().environment)
    if environment != "dev":
        raise ValueError(
            "provider reads require the effective API environment to be dev"
        )
    mt5_config = build_system_broker_connection_config(
        "mt5",
        request_id=generate_id("req"),
    )
    if getattr(mt5_config, "environment", None) != "demo":
        raise ValueError("MT5 provider reads require a composed demo environment")
    explicit_values = {
        field: record.settings[key]
        for key, field in _PROVIDER_FIELDS.items()
        if key in record.settings
    }
    provider_settings = load_broker_provider_settings(explicit_values)
    with (
        data_provider_settings_context(provider_settings),
        data_provider_connection_resolver_context(
            lambda broker_id, request_id: (
                mt5_config
                if broker_id == "mt5"
                else build_system_broker_connection_config(
                    broker_id,
                    request_id=request_id,
                )
            )
        ),
    ):
        yield True


def _get_dataset(*, timeframe: str = "M5", limit: int = 120) -> Any:
    """Retrieve MT5 dataset through the Data public API.

    Args:
        timeframe: Assigned canonical timeframe.
        limit: Number of records to retrieve.

    Returns:
        Canonical market dataset if available, else None.
    """
    req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe=timeframe,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    return get_market_data(req).data


def example_01_trend_indicators() -> None:
    """Evaluate trend moving averages and Bollinger Bands using real MT5 EURUSD M5 data."""
    dataset = _get_dataset(timeframe="M5", limit=120)
    if dataset is None:
        print("\nUnavailable -> MT5 EURUSD M5 bars offline or disabled")
        return
    try:
        _header("01 Trend Indicators: sma, ema, wma, hull_ma, bollinger_bands")
        sma_res = sma(dataset, period=10)
        ema_res = ema(dataset, period=20)
        wma_res = wma(dataset, period=15)
        hma_res = hull_ma(dataset, period=9)
        bb_res = bollinger_bands(dataset, period=20, std_dev=2.0)

        if sma_res.data is not None:
            print("\nSMA (period=10):")
            print(get_indicator_result_values(sma_res.data).tail(3))
        if ema_res.data is not None:
            print("\nEMA (period=20):")
            print(get_indicator_result_values(ema_res.data).tail(3))
        if wma_res.data is not None:
            print("\nWMA (period=15):")
            print(get_indicator_result_values(wma_res.data).tail(3))
        if hma_res.data is not None:
            print("\nHull MA (period=9):")
            print(get_indicator_result_values(hma_res.data).tail(3))
        if bb_res.data is not None:
            print("\nBollinger Bands (period=20, std_dev=2.0):")
            print(get_indicator_result_values(bb_res.data).tail(3))
    except Exception as exc:
        print(f"\nError: {exc}")


def example_02_momentum_indicators() -> None:
    """Evaluate momentum oscillators (rsi, macd, williams_r) using real MT5 EURUSD M5 data."""
    dataset = _get_dataset(timeframe="M5", limit=120)
    if dataset is None:
        print("\nUnavailable -> MT5 EURUSD M5 bars offline or disabled")
        return
    try:
        _header("02 Momentum Indicators: rsi, macd, williams_r")
        rsi_res = rsi(dataset, period=14)
        macd_res = macd(dataset, fast_period=12, slow_period=26, signal_period=9)
        will_res = williams_r(dataset, period=14)

        if rsi_res.data is not None:
            print("\nRSI (period=14):")
            print(get_indicator_result_values(rsi_res.data).tail(3))
        if macd_res.data is not None:
            print("\nMACD (12, 26, 9):")
            print(get_indicator_result_values(macd_res.data).tail(3))
        if will_res.data is not None:
            print("\nWilliams %R (period=14):")
            print(get_indicator_result_values(will_res.data).tail(3))
    except Exception as exc:
        print(f"\nError: {exc}")


def example_03_volatility_and_volume_indicators() -> None:
    """Evaluate volatility and volume indicators (atr, standard_deviation, obv, mfi, cmf) using MT5 data."""
    dataset = _get_dataset(timeframe="M5", limit=120)
    if dataset is None:
        print("\nUnavailable -> MT5 EURUSD M5 bars offline or disabled")
        return
    try:
        _header("03 Volatility & Volume: atr, standard_deviation, obv, mfi, cmf")
        atr_res = atr(dataset, period=14)
        std_res = standard_deviation(dataset, period=20)
        obv_res = obv(dataset)
        mfi_res = mfi(dataset, period=14)
        cmf_res = cmf(dataset, period=20)

        if atr_res.data is not None:
            print("\nATR (period=14):")
            print(get_indicator_result_values(atr_res.data).tail(3))
        if std_res.data is not None:
            print("\nStandard Deviation (period=20):")
            print(get_indicator_result_values(std_res.data).tail(3))
        if obv_res.data is not None:
            print("\nOn Balance Volume (OBV):")
            print(get_indicator_result_values(obv_res.data).tail(3))
        if mfi_res.data is not None:
            print("\nMoney Flow Index (MFI, period=14):")
            print(get_indicator_result_values(mfi_res.data).tail(3))
        if cmf_res.data is not None:
            print("\nChaikin Money Flow (CMF, period=20):")
            print(get_indicator_result_values(cmf_res.data).tail(3))
    except Exception as exc:
        print(f"\nError: {exc}")


def example_04_patterns_and_structure_indicators() -> None:
    """Evaluate pattern and structural indicators (doji, engulfing, inside_bar, pinbar, pivots) using MT5 data."""
    dataset = _get_dataset(timeframe="M5", limit=120)
    if dataset is None:
        print("\nUnavailable -> MT5 EURUSD M5 bars offline or disabled")
        return
    try:
        _header("04 Patterns & Structure: doji, engulfing, inside_bar, pinbar, pivots")
        doji_res = doji(dataset, threshold=0.1)
        engulf_res = engulfing(dataset)
        ib_res = inside_bar(dataset)
        pin_res = pinbar(dataset)
        pivots_res = pivots(dataset, left=5, right=5)

        if doji_res.data is not None:
            print("\nDoji Pattern:")
            print(get_indicator_result_values(doji_res.data).tail(3))
        if engulf_res.data is not None:
            print("\nEngulfing Pattern:")
            print(get_indicator_result_values(engulf_res.data).tail(3))
        if ib_res.data is not None:
            print("\nInside Bar Pattern:")
            print(get_indicator_result_values(ib_res.data).tail(3))
        if pin_res.data is not None:
            print("\nPinbar Pattern:")
            print(get_indicator_result_values(pin_res.data).tail(3))
        if pivots_res.data is not None:
            print("\nPivots (left=5, right=5):")
            print(get_indicator_result_values(pivots_res.data).tail(3))
    except Exception as exc:
        print(f"\nError: {exc}")


def example_05_discovery_and_joining() -> None:
    """Demonstrate indicator registry discovery and joining indicator results onto real MT5 MarketDataset."""
    dataset = _get_dataset(timeframe="M5", limit=120)
    try:
        _header(
            "05 Discovery & Joining: list_indicators, get_capability_matrix, join_indicator_result"
        )
        indicators = list_indicators().data
        print(
            f"\nAvailable registered indicators count: {len(indicators) if indicators else 0}"
        )

        matrix = get_capability_matrix().data
        print(
            f"\nCapability Matrix official formulas count: {len(matrix) if matrix else 0}"
        )

        if dataset is not None:
            sma_res = sma(dataset, period=10)
            if sma_res.data is not None:
                joined_res = join_indicator_result(sma_res.data, dataset)
                if joined_res.data is not None:
                    meta = get_indicator_result_metadata(sma_res.data)
                    print(f"\nJoined DataFrame shape: {joined_res.data.shape}")
                    print(f"Indicator Metadata symbol: {meta.get('symbol')}")
                    print(
                        f"Indicator Metadata indicator_id: {meta.get('indicator_id')}"
                    )
                    print("\nJoined Dataset Tail:")
                    print(joined_res.data.tail(3))
        else:
            print(
                "\nUnavailable -> MT5 EURUSD M5 bars offline or disabled for dataset join"
            )
    except Exception as exc:
        print(f"\nError: {exc}")


def main() -> None:
    """Execute all Indicators public boundary usage examples.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Direct, copyable usage catalogue for the Indicators service public API using real MT5 data."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip external provider reads for deterministic validation.",
    )
    args = parser.parse_args()

    with _provider_runtime_context(offline=args.offline):
        example_01_trend_indicators()
        example_02_momentum_indicators()
        example_03_volatility_and_volume_indicators()
        example_04_patterns_and_structure_indicators()
        example_05_discovery_and_joining()


if __name__ == "__main__":
    main()
