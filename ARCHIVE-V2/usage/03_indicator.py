# ruff: noqa: E501, BLE001, E402
"""Usage examples for technical indicators using real MT5 data.

This script demonstrates how to fetch historical rates from MetaTrader 5 (MT5),
map the columns to lowercase format, and run various indicators:
1. Trend (SMA, EMA, WMA, Bollinger Bands)
2. Momentum (RSI, MACD, Williams %R)
3. Volatility/Volume (ATR, Standard Deviation, OBV, MFI, CMF)
4. Candlestick Patterns (Doji, Engulfing, Inside Bar, Pinbar)
5. Custom/Advanced Indicators (SMC - Smart Money Concepts, Hull Moving Average)
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.brokers.mt5 import get_mt5_client
from app.services.data import get_data
from app.services.indicators import (
    atr,
    bollinger_bands,
    cmf,
    doji,
    ema,
    engulfing,
    hull_moving_average,
    inside_bar,
    macd,
    mfi,
    obv,
    pinbar,
    rsi,
    sma,
    smc,
    standard_deviation,
    williams_r,
    wma,
)
from app.utils.logger import logger
from app.utils.settings import settings


def print_header(title: str) -> None:
    """Print the header for an example section."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def run_trend_and_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute and print trend and momentum indicators on mapped data.

    Args:
        df: Input DataFrame with lowercase OHLCV columns.

    Returns:
        pd.DataFrame: DataFrame with calculated columns.
    """
    print_header("1. Trend and Momentum Indicators")
    logger.info("Calculating Trend and Momentum indicators...")

    # 1. Simple Moving Average (SMA)
    df["sma_10"] = sma.calculate(df, period=10)

    # 2. Exponential Moving Average (EMA)
    df["ema_20"] = ema.calculate(df, period=20)

    # 3. Weighted Moving Average (WMA)
    df["wma_15"] = wma.calculate(df, period=15)

    # 4. Bollinger Bands (returns DataFrame of bands)
    df = pd.concat([df, bollinger_bands.calculate(df, period=20, std_dev=2.0)], axis=1)

    # 5. Relative Strength Index (RSI)
    df["rsi_14"] = rsi.calculate(df, period=14)

    # 6. Moving Average Convergence Divergence (MACD) (returns DataFrame of MACD columns)
    df = pd.concat(
        [
            df,
            macd.calculate(df, fast_period=12, slow_period=26, signal_period=9),
        ],
        axis=1,
    )

    # 7. Williams %R
    df["will_r_14"] = williams_r.calculate(df, period=14)

    logger.info("Trend and Momentum calculation complete.")
    logger.info(
        "Columns added: sma_10, ema_20, wma_15, bb_middle_20, rsi_14, macd_12_26"
    )
    return df


def run_volatility_volume_and_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Compute volatility, volume, and candlestick pattern indicators.

    Args:
        df: Input DataFrame with lowercase OHLCV columns.

    Returns:
        pd.DataFrame: DataFrame with calculated columns.
    """
    print_header("2. Volatility, Volume, and Candlestick Indicators")
    logger.info("Calculating Volatility, Volume, and Candlestick indicators...")

    # 1. Average True Range (ATR)
    df["atr_14"] = atr.calculate(df, period=14)

    # 2. Standard Deviation (Volatility)
    df["std_20"] = standard_deviation.calculate(df, period=20)

    # 3. On Balance Volume (OBV)
    df["obv"] = obv.calculate(df)

    # 4. Money Flow Index (MFI)
    df["mfi_14"] = mfi.calculate(df, period=14)

    # 5. Chaikin Money Flow (CMF)
    df["cmf_20"] = cmf.calculate(df, period=20)

    # 6. Candlestick patterns
    df["candle_doji"] = doji.calculate(df, threshold=0.1)
    df["candle_engulfing"] = engulfing.calculate(df)
    df["candle_inside_bar"] = inside_bar.calculate(df)
    df["candle_pinbar"] = pinbar.calculate(df)

    logger.info("Volatility, Volume, and Candlestick calculation complete.")
    return df


def run_custom_and_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute custom and advanced indicators (SMC and Hull Moving Average).

    Args:
        df: Input DataFrame with lowercase OHLCV columns.

    Returns:
        pd.DataFrame: DataFrame with calculated columns.
    """
    print_header("3. Custom and Advanced Indicators")
    logger.info("Calculating Custom and Advanced indicators...")

    # 1. Smart Money Concepts (SMC) (returns DataFrame of SMC columns)
    # Note: SMC requires at least swing_length (default 50) bars
    df = pd.concat(
        [
            df,
            smc.calculate(
                df,
                swing_length=30,
                join_consecutive_fvg=False,
                close_break=True,
            ),
        ],
        axis=1,
    )

    # 2. Hull Moving Average (HMA)
    df["hma_9"] = hull_moving_average.calculate(df, period=9)

    logger.info("Custom and Advanced calculation complete.")
    return df


def example_01_direct_mt5_indicators() -> None:
    """Show how to fetch rates directly from MT5Client and run indicators."""
    print_header("1. Direct MT5 Client Indicator Execution")

    # Retrieve settings configuration
    mt5_enabled = settings.mt5_enabled
    client = get_mt5_client()

    df_raw = None
    if mt5_enabled:
        try:
            logger.info("Connecting to MT5 terminal...")
            client.connect()
            logger.info("Fetching real rates from MT5 terminal for EURUSD M5...")
            # Fetch 120 bars to satisfy indicator warmups (e.g. SMC swing length)
            df_raw = client.get_bars("EURUSD", "M5", count=120)
            logger.info("Fetched {} bars from MT5.", len(df_raw))
        except Exception as e:
            logger.warning("Could not fetch real MT5 data due to: {}", e)

    if df_raw is None or df_raw.empty:
        msg = "Failed to fetch EURUSD M5 bars from MT5 (no data retrieved)"
        logger.error(msg)
        raise ValueError(msg)

    # Mapped columns from MT5 format to lower case expected by indicator modules
    df_mapped = df_raw.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    # Run indicators
    df_indicators = run_trend_and_momentum_indicators(df_mapped)

    # Print final output sample
    logger.info("Sample Indicator Results (Direct MT5):")
    sample_cols = ["open", "close", "sma_10", "ema_20", "rsi_14", "macd_12_26"]
    print(df_indicators[sample_cols].tail(5).to_string())


def example_02_data_service_indicators() -> None:
    """Show how to use Market Data Service to fetch data and run indicators."""
    logger.info("\n" + "=" * 100)
    logger.info("--- Example 2: Market Data Service Indicator Execution ---")
    logger.info("=" * 100)

    records = None
    try:
        logger.info("Querying Market Data Service for EURUSD M5 bars...")
        # Get start/end times for query
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=10)

        # Fetches unified data schema (lowercase fields)
        records = get_data(
            symbol="EURUSD",
            timeframe="M5",
            data_kind="ohlcv",
            source="mt5",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )
        logger.info("Retrieved {} bars from Data Service.", len(records))
    except Exception as e:
        logger.warning("Could not fetch data from Market Data Service due to: {}", e)

    if not records:
        msg = "Failed to fetch EURUSD M5 bars from Market Data Service (MT5)"
        logger.error(msg)
        raise ValueError(msg)

    # Load into DataFrame
    df = pd.DataFrame(records)

    # Run Volume, Volatility, Candlestick, and SMC/HMA
    df = run_volatility_volume_and_candles(df)
    df = run_custom_and_advanced_indicators(df)

    # Log specific outputs
    logger.info("Sample Volatility & Candlestick Results:")
    sample_cols = [
        "close",
        "atr_14",
        "candle_doji",
        "candle_engulfing",
        "candle_inside_bar",
        "hma_9",
    ]
    print(df[sample_cols].tail(5).to_string())

    # Log advanced SMC structure
    logger.info("Sample Smart Money Concepts (SMC) Structure Results:")
    smc_cols = ["close", "fvg", "swing_high_low", "swing_level", "bos", "choch"]
    print(df[smc_cols].tail(10).to_string())


if __name__ == "__main__":
    try:
        example_01_direct_mt5_indicators()
        example_02_data_service_indicators()
    except Exception as exc:
        logger.exception("Usage examples execution failed: {}", exc)
        sys.exit(1)
