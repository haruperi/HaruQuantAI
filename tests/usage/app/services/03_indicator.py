# ruff: noqa: E501, BLE001, E402, I001
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

import numpy as np
import pandas as pd

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.brokers.mt5 import get_mt5_client
from app.services.data import get_data
from app.services.indicators import (
    ATR,
    CMF,
    EMA,
    MFI,
    OBV,
    RSI,
    SMC,
    WMA,
    Doji,
    InsideBar,
    Pinbar,
    SMA,
    BollingerBands,
    Engulfing,
    HullMovingAverage,
    MACD,
    StandardDeviation,
    WilliamsR,
)
from app.utils.logger import logger
from app.utils.settings import settings


def generate_mock_data() -> pd.DataFrame:
    """Generate mock OHLCVS dataframe for offline indicator calculations.

    Returns:
        pd.DataFrame: A DataFrame with capitalized MT5 column format.
    """
    logger.info("Generating mock OHLCVS data for fallback execution.")
    rng = np.random.default_rng(42)
    rows = 120
    dates = pd.date_range(
        start="2026-06-01T00:00:00Z", periods=rows, freq="5min"
    )
    close = np.cumprod(1.0 + rng.normal(0, 0.002, rows)) * 1.1200
    open_val = close + rng.normal(0, 0.001, rows)
    high = np.maximum(open_val, close) + rng.uniform(0.0005, 0.002, rows)
    low = np.minimum(open_val, close) - rng.uniform(0.0005, 0.002, rows)
    volume = rng.uniform(100, 1000, rows)

    df_mt5 = pd.DataFrame(
        {
            "Timestamp": dates,
            "Open": open_val,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
            "Spread": [2] * rows,
        }
    )
    return df_mt5


def run_trend_and_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute and print trend and momentum indicators on mapped data.

    Args:
        df: Input DataFrame with lowercase OHLCV columns.

    Returns:
        pd.DataFrame: DataFrame with calculated columns.
    """
    logger.info("Calculating Trend and Momentum indicators...")

    # 1. Simple Moving Average (SMA)
    sma_calc = SMA()
    df = sma_calc.calculate(df, period=10)

    # 2. Exponential Moving Average (EMA)
    ema_calc = EMA()
    df = ema_calc.calculate(df, period=20)

    # 3. Weighted Moving Average (WMA)
    wma_calc = WMA()
    df = wma_calc.calculate(df, period=15)

    # 4. Bollinger Bands
    bb_calc = BollingerBands()
    df = bb_calc.calculate(df, period=20, std_dev=2.0)

    # 5. Relative Strength Index (RSI)
    rsi_calc = RSI()
    df = rsi_calc.calculate(df, period=14)

    # 6. Moving Average Convergence Divergence (MACD)
    macd_calc = MACD()
    df = macd_calc.calculate(
        df, fast_period=12, slow_period=26, signal_period=9
    )

    # 7. Williams %R
    will_r_calc = WilliamsR()
    df = will_r_calc.calculate(df, period=14)

    logger.info("Trend and Momentum calculation complete.")
    logger.info("Columns added: sma_10, ema_20, wma_15, bb_middle_20, rsi_14, macd_12_26")
    return df


def run_volatility_volume_and_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Compute volatility, volume, and candlestick pattern indicators.

    Args:
        df: Input DataFrame with lowercase OHLCV columns.

    Returns:
        pd.DataFrame: DataFrame with calculated columns.
    """
    logger.info("Calculating Volatility, Volume, and Candlestick indicators...")

    # 1. Average True Range (ATR)
    atr_calc = ATR()
    df = atr_calc.calculate(df, period=14)

    # 2. Standard Deviation (Volatility)
    std_calc = StandardDeviation()
    df = std_calc.calculate(df, period=20)

    # 3. On Balance Volume (OBV)
    obv_calc = OBV()
    df = obv_calc.calculate(df)

    # 4. Money Flow Index (MFI)
    mfi_calc = MFI()
    df = mfi_calc.calculate(df, period=14)

    # 5. Chaikin Money Flow (CMF)
    cmf_calc = CMF()
    df = cmf_calc.calculate(df, period=20)

    # 6. Candlestick patterns
    doji_calc = Doji()
    df = doji_calc.calculate(df, threshold=0.1)

    engulfing_calc = Engulfing()
    df = engulfing_calc.calculate(df)

    inside_bar_calc = InsideBar()
    df = inside_bar_calc.calculate(df)

    pinbar_calc = Pinbar()
    df = pinbar_calc.calculate(df)

    logger.info("Volatility, Volume, and Candlestick calculation complete.")
    return df


def run_custom_and_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute custom and advanced indicators (SMC and Hull Moving Average).

    Args:
        df: Input DataFrame with lowercase OHLCV columns.

    Returns:
        pd.DataFrame: DataFrame with calculated columns.
    """
    logger.info("Calculating Custom and Advanced indicators...")

    # 1. Smart Money Concepts (SMC)
    smc_calc = SMC()
    # Note: SMC requires at least swing_length (default 50) bars
    df = smc_calc.calculate(
        df, swing_length=30, join_consecutive_fvg=False, close_break=True
    )

    # 2. Hull Moving Average (HMA)
    hma_calc = HullMovingAverage()
    df = hma_calc.calculate(df, period=9)

    logger.info("Custom and Advanced calculation complete.")
    return df


def example_01_direct_mt5_indicators() -> None:
    """Show how to fetch rates directly from MT5Client and run indicators."""
    logger.info("\n" + "=" * 100)
    logger.info("--- Example 1: Direct MT5 Client Indicator Execution ---")
    logger.info("=" * 100)

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
        logger.info("Falling back to synthetic MT5 data.")
        df_raw = generate_mock_data()

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
        logger.warning(
            "Could not fetch data from Market Data Service due to: {}", e
        )

    if not records:
        logger.info("Falling back to synthetic records.")
        # Create records from synthetic mock data
        df_mock = generate_mock_data()
        df_mock.columns = [c.lower() for c in df_mock.columns]
        records = df_mock.to_dict(orient="records")

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
