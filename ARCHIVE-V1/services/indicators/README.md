# Indicators Service

The Indicators Service is a type-safe, modular, and pure-function based library designed for quantitative trading research and execution. It provides robust calculations for trend, momentum, volatility, volume, candlestick patterns, and advanced/custom indicators. All indicators are designed to be calculated on a `pd.DataFrame` containing financial timeseries data (OHLCV).

---

## 1. Directory Structure

```text
app/services/indicators/
├── __init__.py             # Public module interface exports
├── base.py                 # Base indicator abstract class
├── candles/                # Candlestick pattern indicators
│   ├── doji.py             # Doji star detection
│   ├── engulfing.py        # Bullish/Bearish engulfing detection
│   ├── inside_bar.py       # Inside bar structure detection
│   └── pinbar.py           # Pinbar price action detection
├── custom/                 # Custom advanced indicators
│   ├── hull_moving_average.py # Hull Moving Average (HMA)
│   └── smc.py              # Smart Money Concepts (FVG, Swing Levels, BOS/CHoCH)
├── momentum/               # Momentum oscillators
│   ├── macd.py             # Moving Average Convergence Divergence
│   ├── rsi.py              # Relative Strength Index
│   └── will_r.py           # Williams %R
├── trend/                  # Trend moving averages and envelopes
│   ├── bollinger_bands.py  # Bollinger Bands volatility bands
│   ├── ema.py              # Exponential Moving Average
│   ├── sma.py              # Simple Moving Average
│   └── wma.py              # Weighted Moving Average
├── volatility/             # Volatility metrics
│   ├── atr.py              # Average True Range
│   └── standard_deviation.py # Rolling Standard Deviation
└── volume/                 # Volume-based indicators
    ├── cmf.py              # Chaikin Money Flow
    ├── mfi.py              # Money Flow Index
    ├── obv.py              # On-Balance Volume
    └── price_volume_distribution.py # Price Volume Poc Distribution
```

---

## 2. Core Concepts & Abstractions

### `BaseIndicator`
All indicators in the service inherit from the `BaseIndicator` abstract class defined in `base.py` and implement the `calculate` method:

```python
from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

class BaseIndicator(ABC):
    """Base class for all technical indicators."""

    @abstractmethod
    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Calculate the indicator and return the DataFrame with the new columns added.

        Args:
            df: Input DataFrame containing financial data (e.g. open, high, low, close, volume).
            **kwargs: Configuration parameters for the calculation.

        Returns:
            pd.DataFrame: The input DataFrame with the computed indicator columns added.
        """
        pass
```

Each indicator takes a copy of the input DataFrame, performs its operations, appends the generated columns (e.g., `sma_10` or `rsi_14`), and returns the new DataFrame.

---

## 3. Built-In Indicators

| Indicator | Class | Category | Parameters | Description |
|---|---|---|---|---|
| **Simple Moving Average** | `SMA` | Trend | `period` (default: 10), `column` (default: 'close') | Simple average of the last $N$ prices. |
| **Exponential Moving Average** | `EMA` | Trend | `period` (default: 10), `column` (default: 'close') | Weighted moving average giving more weight to recent prices. |
| **Weighted Moving Average** | `WMA` | Trend | `period` (default: 10), `column` (default: 'close') | Linearly weighted moving average. |
| **Bollinger Bands** | `BollingerBands` | Trend | `period` (default: 20), `std_dev` (default: 2.0), `column` (default: 'close') | Volatility bands surrounding a middle SMA line. |
| **Relative Strength Index** | `RSI` | Momentum | `period` (default: 14), `column` (default: 'close') | Momentum oscillator measuring price speed and changes. |
| **MACD** | `MACD` | Momentum | `fast_period` (12), `slow_period` (26), `signal_period` (9), `column` ('close') | Trend-following momentum indicator displaying MA relationships. |
| **Williams %R** | `WilliamsR` | Momentum | `period` (default: 14) | Momentum indicator measuring overbought and oversold levels. |
| **Average True Range** | `ATR` | Volatility | `period` (default: 14) | Volatility metric based on High/Low/Close price spans. |
| **Standard Deviation** | `StandardDeviation` | Volatility | `period` (default: 20), `column` (default: 'close') | Standard deviation of close prices over period. |
| **On-Balance Volume** | `OBV` | Volume | None | Cumulative volume flow indicator relating price change to volume. |
| **Money Flow Index** | `MFI` | Volume | `period` (default: 14) | Volume-weighted RSI representing buying/selling pressure. |
| **Chaikin Money Flow** | `CMF` | Volume | `period` (default: 20) | Volume-weighted measure of accumulation and distribution. |
| **Candlestick Patterns** | `Doji`, `Engulfing`, `InsideBar`, `Pinbar` | Candles | Varies by pattern | Identifies key price action candlesticks (returning -1, 0, or 1). |
| **Smart Money Concepts** | `SMC` | Custom | `swing_length` (50), `join_consecutive_fvg` (False), `close_break` (True) | Identifies FVGs, Swing Levels, BOS/CHoCH. |
| **Hull Moving Average** | `HullMovingAverage` | Custom | `period` (default: 9), `column` (default: 'close') | Moving average with lag reduced significantly. |

---

## 4. Usage Examples

Complete examples utilizing both direct MT5 data fetching and unified Market Data Service routines are available in the integration script [03_indicator.py](file:///c:/Users/rharu/Documents/MyApplications/HaruQuantAI/tests/usage/app/services/03_indicator.py).

### 4.1 Simple Indicator Calculation
```python
import pandas as pd
from app.services.indicators import SMA, RSI

# Sample dataframe containing OHLCV
data = pd.DataFrame({
    "open": [1.12, 1.13, 1.12, 1.14, 1.15],
    "high": [1.13, 1.14, 1.13, 1.15, 1.16],
    "low": [1.11, 1.12, 1.11, 1.13, 1.14],
    "close": [1.12, 1.13, 1.12, 1.14, 1.15],
    "volume": [100.0, 150.0, 120.0, 200.0, 180.0]
}, index=pd.date_range("2026-06-16T10:00:00Z", periods=5, freq="5min"))

# Calculate SMA and RSI
df_with_sma = SMA().calculate(data, period=3)
df_with_both = RSI().calculate(df_with_sma, period=3)

print(df_with_both[["close", "sma_3", "rsi_3"]])
```

### 4.2 Handling Column Casing from MT5
MT5 data frames often use capitalized column names (`Open`, `High`, `Low`, `Close`, `Volume`). Standardize column headers before calling indicators that expect lowercase structures:

```python
# Mapped columns from MT5 format to lower case
df_mapped = df_raw.rename(
    columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
)
df_result = SMA().calculate(df_mapped, period=10)
```

---

## 5. Verification and Testing

To run the unit test suite:
```powershell
.venv\Scripts\pytest tests/unit/app/services/indicators/
```

To run lint checks and static type analysis:
```powershell
.venv\Scripts\python -m ruff check app/services/indicators/
.venv\Scripts\python -m mypy app/services/indicators/
```
