# Indicators — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `indicators`
* **Repository:** `haruperi/HaruQuant`
* **Repository snapshot:** default branch `main`, commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/indicators`
* **Requested tests path:** `ttests/unit/app/services/indicators`
* **Documented tests path:** `tests/unit/app/services/indicators`
* **Known usage/example path:** `tests/usage/app/services/03_indicator.py` (the repository contains the singular filename `03_indicator.py`, not `03_indicators.py`)
* **Files inspected inside the package:** 28 total:
  * `README.md`
  * `__init__.py`
  * `base.py`
  * `trend/__init__.py`, `trend/sma.py`, `trend/ema.py`, `trend/wma.py`, `trend/bollinger_bands.py`
  * `momentum/__init__.py`, `momentum/rsi.py`, `momentum/macd.py`, `momentum/will_r.py`
  * `volatility/__init__.py`, `volatility/atr.py`, `volatility/standard_deviation.py`
  * `volume/__init__.py`, `volume/obv.py`, `volume/mfi.py`, `volume/cmf.py`, `volume/price_volume_distribution.py`
  * `candles/__init__.py`, `candles/doji.py`, `candles/engulfing.py`, `candles/inside_bar.py`, `candles/pinbar.py`
  * `custom/__init__.py`, `custom/hull_moving_average.py`, `custom/smc.py`
* **Related packages searched:** the full indexed repository, including `app/services/indicator`, `app/services/strategy`, `app/services/research`, `app/services/data`, `app/services/brokers`, `app/api`, `data/strategies`, `tests/unit`, and `tests/usage`.
* **Search categories completed:** package imports; direct submodule imports; class names; helper-function names; instantiation/calls visible in indexed source; inheritance; `__init__.py` exports; examples; tests; API routes; strategy files; research files; configuration/string references containing the package path; obvious registries/decorators/callbacks inside the target package.
* **Audit limitations:**
  * The repository could not be cloned into the execution sandbox because outbound DNS was unavailable. Evidence was collected through the connected GitHub repository API and repository-wide code search.
  * No local checkout was available, so the repository's test suite, linting, and type checking were not executed.
  * The requested `ttests/...` path does not exist in the indexed repository. The documented `tests/unit/app/services/indicators/` path also produced no test files.
  * No production telemetry, runtime import tracing, coverage report, or deployment manifest was available.
  * Repository-wide static searches found no dynamic registration for this package, but external consumers outside this repository cannot be ruled out.

## 2. Executive Summary

The Version 1 `app/services/indicators` package is a class-based pandas indicator library. It contains one abstract base class, 19 concrete indicator classes, six general helper functions, seven export-only `__init__.py` files, and package documentation. Its calculations cover moving averages, Bollinger Bands, momentum oscillators, volatility measures, volume measures, candlestick patterns, Hull Moving Average, price-volume point-of-control, and Smart Money Concepts.

Three executable example workflows are present in `tests/usage/app/services/03_indicator.py`: a direct MT5 trend/momentum calculation flow, a Market Data Service volatility/volume/candlestick flow, and an SMC/HMA flow. These workflows demonstrate that 18 of the 19 concrete classes can be composed over OHLCV DataFrames. They are examples, not confirmed production/runtime integrations.

No production import or direct submodule consumer of `app.services.indicators` was found. In contrast, the separate singular package `app/services/indicator` exposes overlapping SMA, EMA, WMA, RSI, ATR, Bollinger Bands, and SMC capabilities; it has unit tests and repository consumers in strategy and research code. This makes the plural package appear largely superseded or disconnected, although that conclusion remains static-analysis based.

The most important correctness findings are:

* `MFI.calculate()` constructs intermediate Series with a fresh `RangeIndex`; assigning the result to a DataFrame with a `DatetimeIndex` aligns by labels and produces an all-`NaN` MFI column.
* `SMC.calculate()` contains retrospective lookahead: FVG detection reads the next candle and swing detection uses a centered future window. Its results are unsuitable as causal live signals unless delayed or treated strictly as retrospective labels.
* `OBV.calculate()`, `Engulfing.calculate()`, and `InsideBar.calculate()` index element zero without handling an empty DataFrame.
* The target package has no unit tests in its documented test directory.
* Six unrelated utility functions are publicly exported from `base.py`, but no caller was found.
* `custom/smc.py` combines several distinct calculations and validation behavior in one 354-line file.

**Audit metrics:** `Module folders: 6 | Files: 28 (27 Python + 1 README) | Public symbols: 46 unique classes/functions/methods | Symbols with confirmed external callers: 36 (78.3%; all example-only, 0 production) | Workflows found: 3`

**Evidence trustworthiness:** High for package contents, signatures, exports, and implementation behavior; medium for repository-wide non-usage conclusions because static code search cannot prove the absence of external or runtime-generated imports.

## 3. Actual Package Structure

```text
app/services/indicators
├── README.md
├── __init__.py
│   └── Re-exports: BaseIndicator; 19 indicator classes; 6 helper functions
├── base.py
│   ├── BaseIndicator
│   │   └── calculate(...)
│   ├── crossed_above(...)
│   ├── crossed_below(...)
│   ├── pips_to_price(...)
│   ├── balance_scaled_volume(...)
│   ├── arithmetic_average(...)
│   └── weighted_average(...)
├── trend
│   ├── __init__.py
│   │   └── Re-exports: SMA, EMA, WMA, BollingerBands
│   ├── sma.py
│   │   └── SMA
│   │       └── calculate(...)
│   ├── ema.py
│   │   └── EMA
│   │       └── calculate(...)
│   ├── wma.py
│   │   └── WMA
│   │       └── calculate(...)
│   └── bollinger_bands.py
│       └── BollingerBands
│           └── calculate(...)
├── momentum
│   ├── __init__.py
│   │   └── Re-exports: RSI, MACD, WilliamsR
│   ├── rsi.py
│   │   └── RSI
│   │       └── calculate(...)
│   ├── macd.py
│   │   └── MACD
│   │       └── calculate(...)
│   └── will_r.py
│       └── WilliamsR
│           └── calculate(...)
├── volatility
│   ├── __init__.py
│   │   └── Re-exports: ATR, StandardDeviation
│   ├── atr.py
│   │   └── ATR
│   │       └── calculate(...)
│   └── standard_deviation.py
│       └── StandardDeviation
│           └── calculate(...)
├── volume
│   ├── __init__.py
│   │   └── Re-exports: OBV, MFI, CMF, PriceVolumeDistribution
│   ├── obv.py
│   │   └── OBV
│   │       └── calculate(...)
│   ├── mfi.py
│   │   └── MFI
│   │       └── calculate(...)
│   ├── cmf.py
│   │   └── CMF
│   │       └── calculate(...)
│   └── price_volume_distribution.py
│       └── PriceVolumeDistribution
│           └── calculate(...)
├── candles
│   ├── __init__.py
│   │   └── Re-exports: Doji, Engulfing, InsideBar, Pinbar
│   ├── doji.py
│   │   └── Doji
│   │       └── calculate(...)
│   ├── engulfing.py
│   │   └── Engulfing
│   │       └── calculate(...)
│   ├── inside_bar.py
│   │   └── InsideBar
│   │       └── calculate(...)
│   └── pinbar.py
│       └── Pinbar
│           └── calculate(...)
└── custom
    ├── __init__.py
    │   └── Re-exports: HullMovingAverage, SMC
    ├── hull_moving_average.py
    │   └── HullMovingAverage
    │       └── calculate(...)
    └── smc.py
        └── SMC
            └── calculate(...)
```

No package-level constants, decorators, registries, callbacks, CLI entry points, scheduled tasks, event subscribers, persistence adapters, API routes, or broker-mutating functions exist inside the target package.

## 4. Module and File Inventory

Files are ordered from foundational dependencies to leaf implementations and then export/documentation layers.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| root | `base.py` | Defines the abstract indicator contract and six general utilities. | `BaseIndicator`, six helpers | Stdlib: `abc`, `collections.abc`, `math`, `typing`; Third-party: `pandas`; Local: type-only `AccountSnapshot` | Mixed: internal inheritance; helpers unused | Supporting overall; helpers have no demonstrated value |
| trend | `trend/sma.py` | Adds a rolling arithmetic mean column. | `SMA` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| trend | `trend/ema.py` | Adds an exponentially weighted mean column. | `EMA` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| trend | `trend/wma.py` | Adds a linearly weighted rolling mean column. | `WMA` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| trend | `trend/bollinger_bands.py` | Adds middle, upper, and lower rolling bands. | `BollingerBands` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| momentum | `momentum/rsi.py` | Adds Wilder-style RSI. | `RSI` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| momentum | `momentum/macd.py` | Adds MACD line, signal line, and histogram. | `MACD` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| momentum | `momentum/will_r.py` | Adds Williams %R from rolling highs/lows. | `WilliamsR` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| volatility | `volatility/atr.py` | Adds Wilder-smoothed Average True Range. | `ATR` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| volatility | `volatility/standard_deviation.py` | Adds rolling pandas sample standard deviation. | `StandardDeviation` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| volume | `volume/obv.py` | Adds cumulative signed volume. | `OBV` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| volume | `volume/mfi.py` | Adds rolling Money Flow Index. | `MFI` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only; defective for non-RangeIndex input | Questionable |
| volume | `volume/cmf.py` | Adds rolling Chaikin Money Flow. | `CMF` | Stdlib: `typing`; Third-party: `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| volume | `volume/price_volume_distribution.py` | Computes rolling close-binned volume point of control. | `PriceVolumeDistribution` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Unused | No demonstrated value |
| candles | `candles/doji.py` | Labels doji candles. | `Doji` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| candles | `candles/engulfing.py` | Labels bullish/bearish engulfing patterns. | `Engulfing` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| candles | `candles/inside_bar.py` | Labels inside bars. | `InsideBar` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| candles | `candles/pinbar.py` | Labels bullish/bearish pinbars. | `Pinbar` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| custom | `custom/hull_moving_average.py` | Adds Hull Moving Average using three internal WMA stages. | `HullMovingAverage` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| custom | `custom/smc.py` | Computes FVG, mitigation index, swing points, BOS, CHoCH, and break indexes. | `SMC` | Stdlib: `typing`; Third-party: `numpy`, `pandas`; Local: `BaseIndicator` | Test-only/example-only | Questionable |
| trend | `trend/__init__.py` | Alternate trend re-export surface. | Four trend classes | Stdlib: none; Third-party: indirect; Local: four trend modules | Unused | No demonstrated value |
| momentum | `momentum/__init__.py` | Alternate momentum re-export surface. | Three momentum classes | Stdlib: none; Third-party: indirect; Local: three momentum modules | Unused | No demonstrated value |
| volatility | `volatility/__init__.py` | Alternate volatility re-export surface. | Two volatility classes | Stdlib: none; Third-party: indirect; Local: two volatility modules | Unused | No demonstrated value |
| volume | `volume/__init__.py` | Alternate volume re-export surface. | Four volume classes | Stdlib: none; Third-party: indirect; Local: four volume modules | Unused | No demonstrated value |
| candles | `candles/__init__.py` | Alternate candlestick re-export surface. | Four candle classes | Stdlib: none; Third-party: indirect; Local: four candle modules | Unused | No demonstrated value |
| custom | `custom/__init__.py` | Alternate custom re-export surface. | Two custom classes | Stdlib: none; Third-party: indirect; Local: two custom modules | Unused | No demonstrated value |
| root | `__init__.py` | Canonical plural-package import surface. | 26 names in `__all__` | Stdlib: none; Third-party: indirect; Local: all implementation modules | Test-only/example-only | Supporting |
| root | `README.md` | Describes structure, classes, basic usage, and test commands. | Documentation only | None | Possibly used | Questionable |

### File-level responsibility flags

* `base.py` contains unrelated responsibilities: indicator inheritance, crossover detection, pip conversion, account/broker volume scaling, and averaging.
* `custom/smc.py` contains multiple separate analytical capabilities—FVG, mitigation, swing extraction, BOS/CHoCH classification, and structural-break confirmation—in one file.
* All other implementation files have one clear calculation responsibility.

## 5. Public Behaviour Inventory

All calculation methods return a copy of the input DataFrame and do not mutate the caller's DataFrame. Side effects are therefore labelled **None**.

### `base.py`

**File responsibility:** Abstract indicator contract plus general calculation/trading helpers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `BaseIndicator` | Abstract class | Requires subclasses to provide `calculate`. | Construction → abstract instance contract | None | Abstract instantiation error if instantiated directly | Inherited by all 19 concrete classes | No target-package unit test found | Used internally; no external production caller | Supporting |
| `BaseIndicator.calculate(self, df, **kwargs)` | Abstract method | Defines DataFrame-in/DataFrame-out interface. | `DataFrame`, arbitrary kwargs → `DataFrame` | None | Subclass-defined | Implemented by 19 subclasses | No target-package unit test found | Internally implemented | Supporting |
| `crossed_above(previous_left, previous_right, current_left, current_right)` | Function | Detects strict upward crossover between two completed observations. | Four floats → `bool` | None | None explicitly | No caller found | None found | Unused | No demonstrated value |
| `crossed_below(previous_left, previous_right, current_left, current_right)` | Function | Detects strict downward crossover. | Four floats → `bool` | None | None explicitly | No caller found | None found | Unused | No demonstrated value |
| `pips_to_price(pips, point_size, pip_multiplier=10.0)` | Function | Converts MQL-style pips to a price distance. | Floats → `float` | None | None explicitly | No caller found; `app/api/routes/live.py:MT5Utils.add_pips_to_price` implements a separate conversion | None found | Unused | No demonstrated value |
| `balance_scaled_volume(balance, balance_increase, volume_increase, account)` | Function | Computes balance-scaled volume and optionally clamps/steps it to account limits. | Floats and optional `AccountSnapshot` → `float` | None | `ValueError` for non-positive scale inputs; account attribute/step errors are not normalized | No caller found | None found | Unused | No demonstrated value |
| `arithmetic_average(values)` | Function | Computes arithmetic mean. | Non-empty float sequence → `float` | None | `ValueError` for empty sequence | No caller found | None found | Unused | No demonstrated value |
| `weighted_average(prices, quantities)` | Function | Computes quantity-weighted price. | Aligned sequences → `float` | None | `ValueError` for empty/misaligned input or non-positive total quantity | No target-package caller found; strategy package has a separate `weighted_average_price` implementation | None found | Unused | No demonstrated value |

**Evidence:** `app/services/indicators/base.py:BaseIndicator`, `crossed_above`, `crossed_below`, `pips_to_price`, `balance_scaled_volume`, `arithmetic_average`, `weighted_average`; repository searches for each helper found only definition/export hits or unrelated similarly named implementations.

### `trend/sma.py`

**File responsibility:** Simple moving average.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SMA` | Class | Provides SMA calculation object. | Construction → `SMA` | None | None | Instantiated in `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `SMA.calculate(df, period=10, column="close", **kwargs)` | Method | Adds `sma_{period}` using `rolling().mean()`. | DataFrame + period/column → copied DataFrame | None | `ValueError` for missing column or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `trend/ema.py`

**File responsibility:** Exponential moving average.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `EMA` | Class | Provides EMA calculation object. | Construction → `EMA` | None | None | `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `EMA.calculate(df, period=10, column="close", **kwargs)` | Method | Adds `ema_{period}` using `ewm(span, adjust=False)`. | DataFrame + period/column → copied DataFrame | None | `ValueError` for missing column or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `trend/wma.py`

**File responsibility:** Linearly weighted moving average.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `WMA` | Class | Provides WMA calculation object. | Construction → `WMA` | None | None | `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `WMA.calculate(df, period=10, column="close", **kwargs)` | Method | Adds `wma_{period}` using rolling dot products and weights `1..period`. | DataFrame + period/column → copied DataFrame | None | `ValueError` for missing column or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `trend/bollinger_bands.py`

**File responsibility:** Bollinger Band envelope.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `BollingerBands` | Class | Provides band calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `BollingerBands.calculate(df, period=20, std_dev=2.0, column="close", **kwargs)` | Method | Adds middle SMA and upper/lower sample-standard-deviation bands. | DataFrame + parameters → copied DataFrame | None | `ValueError` for missing column or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `momentum/rsi.py`

**File responsibility:** Wilder-smoothed RSI.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `RSI` | Class | Provides RSI calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `RSI.calculate(df, period=14, column="close", **kwargs)` | Method | Adds `rsi_{period}` from EWMA gains and losses. | DataFrame + period/column → copied DataFrame | None | `ValueError` for missing column or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `momentum/macd.py`

**File responsibility:** MACD line, signal, and histogram.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `MACD` | Class | Provides MACD calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `MACD.calculate(df, fast_period=12, slow_period=26, signal_period=9, column="close", **kwargs)` | Method | Adds MACD, signal, and histogram columns. | DataFrame + periods/column → copied DataFrame | None | `ValueError` for missing column or any period < 1; does not require fast < slow | Same usage function | No unit test found | Test-only | Questionable |

### `momentum/will_r.py`

**File responsibility:** Williams %R.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `WilliamsR` | Class | Provides Williams %R object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_trend_and_momentum_indicators` | No unit test found | Test-only | Questionable |
| `WilliamsR.calculate(df, period=14, **kwargs)` | Method | Adds `will_r_{period}` from rolling high/low range. | OHLC DataFrame + period → copied DataFrame | None | `ValueError` for missing high/low/close or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `volatility/atr.py`

**File responsibility:** Average True Range.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ATR` | Class | Provides ATR calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `ATR.calculate(df, period=14, **kwargs)` | Method | Adds Wilder-smoothed `atr_{period}` and masks initial warmup rows. | OHLC DataFrame + period → copied DataFrame | None | `ValueError` for missing high/low/close or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `volatility/standard_deviation.py`

**File responsibility:** Rolling standard deviation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `StandardDeviation` | Class | Provides rolling standard deviation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `StandardDeviation.calculate(df, period=20, column="close", **kwargs)` | Method | Adds pandas rolling sample standard deviation `std_{period}`. | DataFrame + period/column → copied DataFrame | None | `ValueError` for missing column or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

**Documentation mismatch:** The class docstring describes division by `period`, but pandas `rolling().std()` defaults to sample standard deviation (`ddof=1`).

### `volume/obv.py`

**File responsibility:** On-Balance Volume.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `OBV` | Class | Provides cumulative signed-volume object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `OBV.calculate(df, **kwargs)` | Method | Adds `obv`; first value forced to zero. | Close/volume DataFrame → copied DataFrame | None | `ValueError` for missing close/volume; `IndexError` for empty DataFrame | Same usage function | No unit test found | Test-only | Questionable |

### `volume/mfi.py`

**File responsibility:** Money Flow Index.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `MFI` | Class | Provides MFI calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `MFI.calculate(df, period=14, **kwargs)` | Method | Adds `mfi_{period}` from typical price and volume. | OHLCV DataFrame + period → copied DataFrame | None | `ValueError` for missing columns or period < 1 | Same usage function | No unit test found | Test-only; broken for non-RangeIndex input | Questionable |

**Confirmed defect:** `pd.Series(pos_flow)` and `pd.Series(neg_flow)` receive a new integer index. The computed MFI Series is label-aligned when assigned to `result_df`; a `DatetimeIndex` input therefore receives no matching labels and the output column is all `NaN`. Evidence: `app/services/indicators/volume/mfi.py:MFI.calculate`, intermediate Series creation and assignment.

### `volume/cmf.py`

**File responsibility:** Chaikin Money Flow.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `CMF` | Class | Provides CMF calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `CMF.calculate(df, period=20, **kwargs)` | Method | Adds rolling money-flow-volume divided by rolling volume. | OHLCV DataFrame + period → copied DataFrame | None | `ValueError` for missing columns or period < 1 | Same usage function | No unit test found | Test-only | Questionable |

### `volume/price_volume_distribution.py`

**File responsibility:** Rolling close-binned volume profile point of control.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `PriceVolumeDistribution` | Class | Provides rolling POC calculation object. | Construction → object | None | None | No caller found | No unit test found | Unused | No demonstrated value |
| `PriceVolumeDistribution.calculate(df, period=20, bins=10, **kwargs)` | Method | For each completed window, bins close prices across the high/low range and returns the center of the maximum-volume bin. | OHLCV DataFrame + period/bins → copied DataFrame | None | `ValueError` for missing columns, period < 1, or bins < 1 | No caller found | No unit test found | Unused | No demonstrated value |

### `candles/doji.py`

**File responsibility:** Doji detection.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Doji` | Class | Provides doji detector. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `Doji.calculate(df, threshold=0.1, **kwargs)` | Method | Adds binary `candle_doji` based on body/range ratio. | OHLC DataFrame + threshold → copied DataFrame | None | `ValueError` for missing columns or non-positive threshold | Same usage function | No unit test found | Test-only | Questionable |

### `candles/engulfing.py`

**File responsibility:** Bullish/bearish engulfing detection.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Engulfing` | Class | Provides engulfing detector. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `Engulfing.calculate(df, **kwargs)` | Method | Adds `candle_engulfing`: 1 bullish, -1 bearish, 0 otherwise. | Open/close DataFrame → copied DataFrame | None | `ValueError` for missing columns; `IndexError` for empty DataFrame | Same usage function | No unit test found | Test-only | Questionable |

### `candles/inside_bar.py`

**File responsibility:** Inside-bar detection.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `InsideBar` | Class | Provides inside-bar detector. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `InsideBar.calculate(df, **kwargs)` | Method | Adds binary `candle_inside_bar`. | High/low DataFrame → copied DataFrame | None | `ValueError` for missing columns; `IndexError` for empty DataFrame | Same usage function | No unit test found | Test-only | Questionable |

### `candles/pinbar.py`

**File responsibility:** Pinbar detection.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Pinbar` | Class | Provides pinbar detector. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_volatility_volume_and_candles` | No unit test found | Test-only | Questionable |
| `Pinbar.calculate(df, **kwargs)` | Method | Adds `candle_pinbar`: 1 bullish, -1 bearish, 0 otherwise. | OHLC DataFrame → copied DataFrame | None | `ValueError` for missing columns | Same usage function | No unit test found | Test-only | Questionable |

### `custom/hull_moving_average.py`

**File responsibility:** Hull Moving Average.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `HullMovingAverage` | Class | Provides HMA calculation object. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_custom_and_advanced_indicators` | No unit test found | Test-only | Questionable |
| `HullMovingAverage.calculate(df, period=9, column="close", **kwargs)` | Method | Adds `hma_{period}` from half/full-period WMA and square-root-period smoothing. | DataFrame + period/column → copied DataFrame | None | `ValueError` for missing column or period < 2 | Same usage function | No unit test found | Test-only | Questionable |

### `custom/smc.py`

**File responsibility:** Retrospective Smart Money Concepts labelling.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SMC` | Class | Provides aggregate FVG, swing, BOS, and CHoCH calculation. | Construction → object | None | None | `tests/usage/app/services/03_indicator.py:run_custom_and_advanced_indicators` | No target-package unit test found | Test-only | Questionable |
| `SMC.calculate(df, swing_length=50, join_consecutive_fvg=False, close_break=True, **kwargs)` | Method | Adds ten FVG/swing/structure columns by invoking private calculation stages. | OHLC DataFrame + options → copied DataFrame | None | `LookupError` for missing OHLC; pandas/numpy errors for invalid lengths are not normalized | Same usage function | No target-package unit test found | Test-only; non-causal | Questionable |

**Non-causal behavior evidence:**

* `_fvg()` reads `shift(-1)`, so a label at the current row depends on the following candle.
* `_swing_highs_lows()` shifts by half the doubled swing window before rolling, so the selected swing uses future observations.
* The class docstring says the input requires volume, but `calculate()` validates only `"ohlc"` and the implementation does not use volume.

## 6. Actual Workflows

### `V1-WF-INDICATORS-001` — Direct MT5 Trend and Momentum Enrichment

* **Scope:** Cross-domain
* **Trigger:** Running `tests/usage/app/services/03_indicator.py` as a script invokes `example_01_direct_mt5_indicators()`.
* **Input boundary:** MT5 bars from `app.services.brokers.mt5.get_mt5_client().get_bars()` or synthetic fallback data; MT5-style capitalized columns are renamed to lowercase.
* **Functions and methods used:** `run_trend_and_momentum_indicators`; `SMA.calculate`; `EMA.calculate`; `WMA.calculate`; `BollingerBands.calculate`; `RSI.calculate`; `MACD.calculate`; `WilliamsR.calculate`.
* **Files involved:** `tests/usage/app/services/03_indicator.py` plus seven target implementation files.
* **External dependencies:** MT5 broker client, pandas, numpy, logger, settings.
* **Output boundary:** Enriched DataFrame; selected columns are printed.
* **Failure behaviour:** MT5 connection/data exceptions are caught and replaced by synthetic data. Indicator validation/calculation errors escape to the script-level handler, are logged, and cause exit code 1.
* **Operational status:** Unverified. The call path is complete, but it was not executed in this audit and is an example rather than a production route.
* **Evidence:** `tests/usage/app/services/03_indicator.py:example_01_direct_mt5_indicators`, `run_trend_and_momentum_indicators`.

```text
Script entry
→ example_01_direct_mt5_indicators()
→ MT5 get_bars() or generate_mock_data()
→ lowercase OHLCV mapping
→ SMA → EMA → WMA → BollingerBands → RSI → MACD → WilliamsR
→ enriched DataFrame sample printed
```

### `V1-WF-INDICATORS-002` — Data-Service Volatility, Volume, and Candle Enrichment

* **Scope:** Cross-domain
* **Trigger:** `example_02_data_service_indicators()` in the usage script.
* **Input boundary:** OHLCV records from `app.services.data.get_data()` or synthetic-record fallback.
* **Functions and methods used:** `run_volatility_volume_and_candles`; `ATR.calculate`; `StandardDeviation.calculate`; `OBV.calculate`; `MFI.calculate`; `CMF.calculate`; `Doji.calculate`; `Engulfing.calculate`; `InsideBar.calculate`; `Pinbar.calculate`.
* **Files involved:** `tests/usage/app/services/03_indicator.py` plus nine target implementation files.
* **External dependencies:** Market Data Service, pandas, numpy, logger.
* **Output boundary:** Enriched DataFrame passed onward to the custom workflow and later printed.
* **Failure behaviour:** Data-service exceptions are caught and replaced by synthetic records. Indicator exceptions escape to the script-level handler. Empty DataFrames can fail in OBV/Engulfing/InsideBar. Non-RangeIndex input can invalidate MFI output.
* **Operational status:** Partial. The call path is complete, but MFI has an index-sensitive defect and the workflow was not executed during the audit.
* **Evidence:** `tests/usage/app/services/03_indicator.py:example_02_data_service_indicators`, `run_volatility_volume_and_candles`; `app/services/indicators/volume/mfi.py:MFI.calculate`.

```text
example_02_data_service_indicators()
→ get_data() or synthetic records
→ DataFrame
→ ATR → StandardDeviation → OBV → MFI → CMF
→ Doji → Engulfing → InsideBar → Pinbar
→ enriched DataFrame
```

### `V1-WF-INDICATORS-003` — SMC and Hull Moving Average Enrichment

* **Scope:** Internal calculation stage invoked by a cross-domain example
* **Trigger:** `example_02_data_service_indicators()` calls `run_custom_and_advanced_indicators()`.
* **Input boundary:** DataFrame already enriched by `V1-WF-INDICATORS-002`.
* **Functions and methods used:** `SMC.calculate`; `HullMovingAverage.calculate`.
* **Files involved:** `tests/usage/app/services/03_indicator.py`, `custom/smc.py`, `custom/hull_moving_average.py`.
* **External dependencies:** pandas, numpy.
* **Output boundary:** DataFrame with FVG, swing, BOS/CHoCH, break-index, and HMA columns; selected columns are printed.
* **Failure behaviour:** Missing OHLC raises `LookupError`; invalid swing lengths can produce unnormalized pandas errors; other failures escape to the script-level handler.
* **Operational status:** Partial. The flow is complete for retrospective analysis, but SMC uses future observations and is not causal for live decision-making.
* **Evidence:** `tests/usage/app/services/03_indicator.py:run_custom_and_advanced_indicators`; `app/services/indicators/custom/smc.py:SMC.calculate`, `_fvg`, `_swing_highs_lows`.

```text
enriched OHLCV DataFrame
→ SMC.calculate()
   → FVG and mitigation
   → swing points
   → BOS/CHoCH and break index
→ HullMovingAverage.calculate()
→ enriched DataFrame sample printed
```

No workflow was found for `PriceVolumeDistribution`, the six public helpers, or the six subpackage re-export surfaces.

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `BaseIndicator` | All 19 concrete indicator classes | Inheritance | Internal package dependency | Every implementation declares `class ... (BaseIndicator)` |
| `BaseIndicator.calculate` | Implemented by all 19 subclasses | Override/contract | Internal package dependency | Each concrete class defines `calculate` |
| `SMA`, `SMA.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | `tests/usage/app/services/03_indicator.py` |
| `EMA`, `EMA.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | Same |
| `WMA`, `WMA.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | Same |
| `BollingerBands`, `BollingerBands.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | Same |
| `RSI`, `RSI.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | Same |
| `MACD`, `MACD.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | Same |
| `WilliamsR`, `WilliamsR.calculate` | `run_trend_and_momentum_indicators` | Instantiation and method call | Example | Same |
| `ATR`, `ATR.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | `tests/usage/app/services/03_indicator.py` |
| `StandardDeviation`, `StandardDeviation.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `OBV`, `OBV.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `MFI`, `MFI.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `CMF`, `CMF.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `Doji`, `Doji.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `Engulfing`, `Engulfing.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `InsideBar`, `InsideBar.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `Pinbar`, `Pinbar.calculate` | `run_volatility_volume_and_candles` | Instantiation and method call | Example | Same |
| `SMC`, `SMC.calculate` | `run_custom_and_advanced_indicators` | Instantiation and method call | Example | `tests/usage/app/services/03_indicator.py` |
| `HullMovingAverage`, `HullMovingAverage.calculate` | `run_custom_and_advanced_indicators` | Instantiation and method call | Example | Same |
| `PriceVolumeDistribution`, `PriceVolumeDistribution.calculate` | None found | — | — | Exact symbol and package-path searches returned only definition/export files |
| `crossed_above` | None found | — | — | Exact symbol search returned only `base.py` and root export |
| `crossed_below` | None found | — | — | Exact symbol search returned only `base.py` and root export |
| `pips_to_price` | None found | — | — | Exact symbol search produced a false-positive substring match to `MT5Utils.add_pips_to_price`; no import/call of the target function exists |
| `balance_scaled_volume` | None found | — | — | Exact symbol search returned only definition/export |
| `arithmetic_average` | None found | — | — | Exact symbol search returned only definition/export |
| `weighted_average` | None found | — | — | Direct-import searches returned no consumer; generic hits are separate strategy implementations |
| Root `app.services.indicators` exports | `tests/usage/app/services/03_indicator.py` | Multi-symbol import | Example | Usage script imports 18 classes from the root package |
| Subpackage `__init__.py` exports | None found | — | — | Category import-path searches returned only root/own initializer files |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `pandas` | DataFrame copying, rolling windows, EWM, shifts, concatenation, Series construction | All 19 implementation files and `base.py` type contract | Imports in each file |
| `numpy` | Weighted arrays, conditional labels, NaN handling, binning, dot products | WMA, ATR, OBV, MFI, PVD, candle patterns, HMA, SMC | Imports in corresponding modules |
| `app.services.contracts.strategies` | `AccountSnapshot` type only | `base.py:balance_scaled_volume` under `TYPE_CHECKING` | No runtime import |
| Internal target package | `BaseIndicator` | Every concrete class | All 19 implementation imports |
| Other HaruQuant domains | None at runtime | Target implementation files | No runtime local-domain import found beyond internal modules |

The usage script depends on Broker/Data/Utils domains, but those dependencies belong to the example harness rather than the target package itself.

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
|---|---|---|---|
| `tests/usage/app/services/03_indicator.py` | 18 concrete classes | Demonstrate indicator enrichment with MT5/Data Service inputs | Root import and method calls in the usage script |
| Production/runtime packages | None confirmed | — | Root and direct-submodule import searches found no runtime consumer |
| Unit tests for the target package | None confirmed | — | No files found under documented `tests/unit/app/services/indicators` |
| External repositories/deployments | Unknown | Unknown | Not accessible in this audit |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `app/services/indicators/trend/{sma,ema,wma}.py` | `app/services/indicator/trend/{sma,ema,wma}.py` | Same moving-average capabilities and similar DataFrame output columns | Both package trees and singular `__init__.py`; singular package is imported by strategy files | Two APIs and implementations can diverge; callers may select different semantics |
| `app/services/indicators/momentum/rsi.py` | `app/services/indicator/momentum/rsi.py` | RSI calculation | Both exports; singular package has tests and strategy callers | Duplicate numerical behavior and validation contracts |
| `app/services/indicators/volatility/atr.py` | `app/services/indicator/volatility/atr.py` | ATR calculation | Both exports; singular package unit tests | Divergent warmup/smoothing behavior can create inconsistent risk signals |
| `app/services/indicators/trend/bollinger_bands.py` | `app/services/indicator/volatility/bbands.py` | Bollinger Bands | Both exports; singular package used by strategy files | Same concept appears in different category paths and APIs |
| `app/services/indicators/custom/smc.py` | `app/services/indicator/custom/smc.py` | FVG, swing, and BOS/CHoCH capabilities | Plural aggregate class; singular package exports focused SMC functions | Duplicate logic and different output/response contracts |
| `base.py:pips_to_price` | `app/api/routes/live.py:MT5Utils.add_pips_to_price` | Pip-to-price conversion | Both implement pip conversion independently; no shared call | Symbol digit handling can differ across execution paths |
| `base.py:weighted_average` | `app/services/strategy/stateful_common.py:weighted_average_price` | Volume-weighted price | Separate implementations; strategy helper operates on positions | Duplicate arithmetic and edge-case behavior |
| `SMA.calculate` and `RSI.calculate` | `app/services/strategy/stateful_common.py:rolling_sma`, `rolling_rsi` | Latest-value rolling indicator calculations | Strategy package contains local implementations | Production strategy behavior can bypass both indicator services |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `PriceVolumeDistribution` and `.calculate` | No caller, test, example, registry, or configuration reference found. | Exact symbol; package-path imports; root imports; tests/examples | Medium | Only definition and export files were returned |
| `crossed_above` | Publicly exported but no caller found. | Exact symbol; root/direct imports; strategy/API search | Medium | Only `base.py` and root `__init__.py` |
| `crossed_below` | Publicly exported but no caller found. | Exact symbol; root/direct imports; strategy/API search | Medium | Only definition/export |
| `pips_to_price` | Publicly exported but no target-function caller found. A separate API helper implements similar behavior. | Exact symbol; direct-import query; API inspection | Medium | `base.py`; `app/api/routes/live.py:MT5Utils.add_pips_to_price` is independent |
| `balance_scaled_volume` | Publicly exported but no caller found. | Exact symbol; direct-import search; strategy/risk-related search | Medium | Only definition/export |
| `arithmetic_average` | Publicly exported but no caller found. | Exact symbol; direct-import search | Medium | Only definition/export |
| `weighted_average` | No target-function caller found; generic repository hits refer to separate strategy functions. | Exact symbol; direct imports from root/base; inspected strategy helper | Medium | `base.py`; no import in `stateful_common.py` |
| Six subpackage `__init__.py` files | No external import of category packages found; root initializer imports leaf modules directly. | Category package-path searches | Medium | Searches returned only root and the category's own initializer |
| 18 example-used concrete classes | Demonstrated only by the usage script; no production consumer found. | Root import; direct category import; class-name searches; strategy/research/API searches | Medium | `tests/usage/app/services/03_indicator.py` is the only consumer |
| Root plural package | The only confirmed consumer is an example script. | Root import and package-path search across repository | Medium | No production path returned |
| `README.md` testing instructions | Points to a unit-test directory with no indexed tests. Usage hyperlink is a machine-local `file:///c:/...` URI. | Path search; README inspection | High for repository state | `app/services/indicators/README.md` |

No item is labelled “dead code”; static evidence supports “unused” or “questionable,” but runtime-generated/external imports remain possible.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Entire plural indicator service | No production strategy, research pipeline, API route, simulator, live runtime, or agent tool imports it. | Calculations exist but do not contribute confirmed runtime value. | Package-path searches; singular `app/services/indicator` has the actual production callers |
| `PriceVolumeDistribution` | Not included in the usage script and has no other caller. | Capability has no demonstrated execution path. | Exact symbol search |
| Unit-test workflow | Documented test directory contains no indexed tests. | Numerical correctness, warmup behavior, index preservation, and edge cases are unprotected. | README test command and repository search |
| MFI on timestamp-indexed OHLCV | Intermediate Series lose the caller's index. | Valid timestamp-indexed input produces all-`NaN` output. | `volume/mfi.py:MFI.calculate` |
| SMC as a live indicator | No causality boundary or delayed-emission rule exists. | Current-row labels can incorporate future candles, creating lookahead if consumed as a live signal. | `custom/smc.py:_fvg`, `_swing_highs_lows` |
| Empty-input handling | OBV, Engulfing, and InsideBar force index zero without checking length. | Empty but schema-valid inputs raise `IndexError`. | Corresponding `calculate` methods |
| Shared helpers | No workflow consumes the six functions. | Public API surface is larger than demonstrated behavior and mixes trading utilities into indicators. | Exact helper searches |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-INDICATORS-001` | Duplicate plural and singular indicator services coexist. | `app/services/indicators` vs `app/services/indicator` | Conflicting APIs, duplicate numerical logic, unclear ownership, and drift risk. | Both export overlapping SMA/EMA/WMA/RSI/ATR/Bollinger/SMC capabilities; singular package has tests and production callers. |
| `V1-ISSUE-INDICATORS-002` | No confirmed production caller of the plural package. | Entire target package | Current runtime value is not demonstrated. | Only `tests/usage/app/services/03_indicator.py` imports the package. |
| `V1-ISSUE-INDICATORS-003` | Target unit tests are absent despite README instructions. | `tests/unit/app/services/indicators` | Correctness regressions and edge cases are not verified. | Repository path search found only the README reference; existing indicator tests target the singular package. |
| `V1-ISSUE-INDICATORS-004` | MFI loses non-default indexes. | `volume/mfi.py:MFI.calculate` | Datetime-indexed output aligns to no labels and becomes all `NaN`. | Intermediate `pd.Series` objects use `RangeIndex`; final assignment is label-aligned. |
| `V1-ISSUE-INDICATORS-005` | SMC uses future candles. | `custom/smc.py:_fvg`, `_swing_highs_lows` | Lookahead bias if interpreted as a current/live signal. | `shift(-1)` and centered future-window logic. |
| `V1-ISSUE-INDICATORS-006` | `base.py` combines unrelated domains and publicly exports uncalled helpers. | `base.py` and root `__init__.py` | Indicator boundary includes pip conversion, account sizing, and generic averages with no demonstrated workflow. | Six helper definitions and `__all__`; exact searches found no target callers. |
| `V1-ISSUE-INDICATORS-007` | SMC file contains several independent analytical responsibilities. | `custom/smc.py` | Harder isolation, testing, and caller understanding; one public call emits ten outputs with mixed semantics. | `calculate` orchestrates FVG, mitigation, swings, BOS, CHoCH, and break detection. |
| `V1-ISSUE-INDICATORS-008` | Empty DataFrames are not consistently supported. | `volume/obv.py`, `candles/engulfing.py`, `candles/inside_bar.py` | Schema-valid empty inputs raise `IndexError` instead of returning an empty enriched frame or a normalized validation error. | Each method writes array element `[0]`. |
| `V1-ISSUE-INDICATORS-009` | Error contracts are inconsistent. | Most modules vs `custom/smc.py` | Callers must handle `ValueError`, `LookupError`, raw pandas errors, and `IndexError`. | Most files validate with `ValueError`; SMC uses `LookupError`; invalid/empty edge cases leak lower-level errors. |
| `V1-ISSUE-INDICATORS-010` | Arbitrary unknown keyword arguments are silently ignored. | Every concrete `calculate(..., **kwargs)` | Misspelled configuration can appear successful while having no effect. | Subclasses accept `**kwargs` and do not inspect it. |
| `V1-ISSUE-INDICATORS-011` | Multiple unused export layers exist. | Six subpackage `__init__.py` files | Larger import surface without confirmed callers; more maintenance points. | Root imports leaves directly; category import searches found no external consumer. |
| `V1-ISSUE-INDICATORS-012` | Documentation does not fully match actual behavior/repository state. | `README.md`, `standard_deviation.py`, `custom/smc.py` | Users can run invalid test commands or assume incorrect formulas/input requirements. | Missing test directory; local file URI; sample-vs-population std mismatch; SMC claims volume requirement but does not use it. |
| `V1-ISSUE-INDICATORS-013` | No canonical output schema exists across indicators. | All concrete classes | Callers must know file-specific column names, parameter suffix formats, and warmup conventions. | Outputs vary between fixed names, integer suffixes, float suffixes, and multi-column structures. |
| `V1-ISSUE-INDICATORS-014` | Semantic parameter relationships are not fully validated. | `MACD.calculate`, `SMC.calculate` | Invalid but type-correct configurations can run or fail with lower-level errors. | MACD allows fast period >= slow period; SMC does not validate positive swing length. |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-INDICATORS-001` | Common indicator class contract | `base.py:BaseIndicator`, `calculate` | All three workflows | Internal | Supporting | Used only as inheritance/typing convention |
| `V1-CAP-INDICATORS-002` | Simple moving average | `trend/sma.py:SMA.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | Duplicated by singular package |
| `V1-CAP-INDICATORS-003` | Exponential moving average | `trend/ema.py:EMA.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | Duplicated by singular package |
| `V1-CAP-INDICATORS-004` | Weighted moving average | `trend/wma.py:WMA.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | Duplicated by singular package |
| `V1-CAP-INDICATORS-005` | Bollinger Bands | `trend/bollinger_bands.py:BollingerBands.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | Duplicated by singular package |
| `V1-CAP-INDICATORS-006` | Relative Strength Index | `momentum/rsi.py:RSI.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | Duplicated by singular package and strategy helper |
| `V1-CAP-INDICATORS-007` | MACD | `momentum/macd.py:MACD.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | No production caller found |
| `V1-CAP-INDICATORS-008` | Williams %R | `momentum/will_r.py:WilliamsR.calculate` | `V1-WF-INDICATORS-001` | Test-only | Questionable | No production caller found |
| `V1-CAP-INDICATORS-009` | Average True Range | `volatility/atr.py:ATR.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Duplicated by singular package |
| `V1-CAP-INDICATORS-010` | Rolling standard deviation | `volatility/standard_deviation.py:StandardDeviation.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Doc formula differs from pandas default |
| `V1-CAP-INDICATORS-011` | On-Balance Volume | `volume/obv.py:OBV.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Empty input fails |
| `V1-CAP-INDICATORS-012` | Money Flow Index | `volume/mfi.py:MFI.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Broken for non-RangeIndex input |
| `V1-CAP-INDICATORS-013` | Chaikin Money Flow | `volume/cmf.py:CMF.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | No production caller found |
| `V1-CAP-INDICATORS-014` | Rolling volume-profile point of control | `volume/price_volume_distribution.py:PriceVolumeDistribution.calculate` | None | Unused | No demonstrated value | Not present in usage workflow |
| `V1-CAP-INDICATORS-015` | Doji detection | `candles/doji.py:Doji.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Binary label |
| `V1-CAP-INDICATORS-016` | Engulfing detection | `candles/engulfing.py:Engulfing.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Empty input fails |
| `V1-CAP-INDICATORS-017` | Inside-bar detection | `candles/inside_bar.py:InsideBar.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Empty input fails |
| `V1-CAP-INDICATORS-018` | Pinbar detection | `candles/pinbar.py:Pinbar.calculate` | `V1-WF-INDICATORS-002` | Test-only | Questionable | Fixed thresholds are not parameters |
| `V1-CAP-INDICATORS-019` | Hull Moving Average | `custom/hull_moving_average.py:HullMovingAverage.calculate` | `V1-WF-INDICATORS-003` | Test-only | Questionable | No production caller found |
| `V1-CAP-INDICATORS-020` | Fair Value Gap and mitigation labelling | `custom/smc.py:SMC.calculate`, `_fvg` | `V1-WF-INDICATORS-003` | Test-only | Questionable | Uses next candle |
| `V1-CAP-INDICATORS-021` | Swing-high/low labelling | `custom/smc.py:SMC.calculate`, `_swing_highs_lows` | `V1-WF-INDICATORS-003` | Test-only | Questionable | Centered/future window |
| `V1-CAP-INDICATORS-022` | BOS/CHoCH and break-index labelling | `custom/smc.py:SMC.calculate`, `_bos_choch` | `V1-WF-INDICATORS-003` | Test-only | Questionable | Retrospective structure output |
| `V1-CAP-INDICATORS-023` | Up/down crossover detection | `base.py:crossed_above`, `crossed_below` | None | Unused | No demonstrated value | Public but disconnected |
| `V1-CAP-INDICATORS-024` | Pip-distance conversion | `base.py:pips_to_price` | None | Unused | No demonstrated value | Overlaps live API helper |
| `V1-CAP-INDICATORS-025` | Balance-scaled broker volume | `base.py:balance_scaled_volume` | None | Unused | No demonstrated value | Depends on account contract only for typing |
| `V1-CAP-INDICATORS-026` | Arithmetic and weighted averaging | `base.py:arithmetic_average`, `weighted_average` | None | Unused | No demonstrated value | Strategy package implements its own basket average |

## 14. Audit Conclusions

### Valuable behaviour worth preserving as observed facts

The package contains straightforward, mostly side-effect-free DataFrame calculations with explicit output columns and basic input validation. The common copy-and-enrich behavior is clear. The usage script demonstrates that 18 concrete classes can be chained over one DataFrame and can consume either MT5-derived or Market Data Service-derived OHLCV data.

The following calculations are independently understandable and operational at code level: SMA, EMA, WMA, Bollinger Bands, RSI, MACD, Williams %R, ATR, standard deviation, OBV, CMF, four candlestick labels, HMA, rolling price-volume POC, and retrospective SMC labels. This statement describes existing behavior only; it is not a Version 2 preservation recommendation.

### Behaviour that exists but is disconnected

* All 18 classes used by the example script have no confirmed production consumer.
* `PriceVolumeDistribution` has no confirmed caller at all.
* Six public helpers have no confirmed caller.
* Six category-level export surfaces have no confirmed caller.
* The target package's documented unit-test workflow is disconnected because its test directory is absent.

### Likely dead weight, without declaring dead code

Static evidence makes the root plural package, the category re-export files, `PriceVolumeDistribution`, and the six helper functions strong candidates for manual confirmation. They are not labelled dead code because external imports, unindexed generated code, and runtime string construction cannot be completely excluded.

### Duplicated responsibilities

The strongest duplication is the coexistence of `app/services/indicators` and `app/services/indicator`. The singular package overlaps on the most common indicators, has unit tests, and is consumed by strategy/research code. Additional local duplicates exist for pip conversion, weighted basket price, rolling SMA, and rolling RSI.

### Important uncertainties

* Whether any external deployment, notebook, local-only script, plugin, or generated strategy imports the plural package.
* Whether the usage script is executed in CI or manually as part of a release process.
* Whether SMC outputs are intentionally retrospective labels rather than intended causal indicators.
* Whether a non-indexed or deleted test suite for the plural package exists outside the inspected commit.
* Whether the duplicate plural package is intentionally retained as a compatibility API.

### Areas requiring manual confirmation

1. Runtime/import telemetry for `app.services.indicators`.
2. Any external consumers not stored in `haruperi/HaruQuant`.
3. Intended ownership boundary between singular `indicator` and plural `indicators`.
4. Intended causality semantics for SMC.
5. Expected DataFrame index contract, especially for MFI.
6. Whether helper functions in `base.py` belong to an undocumented strategy/execution workflow.

## Final Validation

* Every indexed Python file under `app/services/indicators` is represented.
* Every root and category `__init__.py` export was checked against its implementation.
* All 26 root `__all__` names exist.
* Repository-wide static callers were searched through root imports, direct category imports, class names, helper names, and related runtime packages.
* Inbound and outbound dependency surfaces are summarized.
* Workflows are based on actual usage-script call paths.
* Production usage is distinguished from example-only usage.
* Uncertain non-usage conclusions are labelled medium confidence.
* No Version 2 requirement or redesign is included.
* No repository code was changed.
