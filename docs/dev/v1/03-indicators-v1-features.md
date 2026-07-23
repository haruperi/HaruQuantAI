## FEAT-INDI-01: Base Indicator Class (app.services.indicators.base)

| Function | Purpose |
|----------|---------|
| `BaseIndicator.calculate(df: pd.DataFrame, **kwargs: Any) -> pd.Series \| pd.DataFrame` | Calculate the indicator and return the DataFrame with the new columns added. |
| `crossed_above(previous_left: float, previous_right: float, current_left: float, current_right: float) -> bool` | Return a strict upward crossover using two fully completed observations. |
| `crossed_below(previous_left: float, previous_right: float, current_left: float, current_right: float) -> bool` | Return a strict downward crossover using two fully completed observations. |
| `pips_to_price(pips: float, point_size: float, pip_multiplier: float = 10.0) -> float` | Convert MQL-style pips using an explicit point-to-pip multiplier. |
| `balance_scaled_volume(balance: float, balance_increase: float, volume_increase: float, account: AccountSnapshot \| None) -> float` | Translate common MQL balance-scaled lot formulas and clamp to broker bounds. |
| `arithmetic_average(values: Sequence[float]) -> float` | Calculate the arithmetic average of a sequence of values. |
| `weighted_average(prices: Sequence[float], quantities: Sequence[float]) -> float` | Calculate the weighted average of prices and quantities. |


## FEAT-INDI-02: Doji Candlestick Pattern Indicator (app.services.indicators.candles.doji)

| Function | Purpose |
|----------|---------|
| `Doji.calculate(df: pd.DataFrame, threshold: float = 0.1, **kwargs: Any) -> pd.DataFrame` | Doji Pattern |


## FEAT-INDI-03: Engulfing Candle Pattern Indicator (app.services.indicators.candles.engulfing)

| Function | Purpose |
|----------|---------|
| `Engulfing.calculate(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame` | Engulfing Pattern |


## FEAT-INDI-04: Inside Bar Candlestick Pattern Indicator (app.services.indicators.candles.inside_bar)

| Function | Purpose |
|----------|---------|
| `InsideBar.calculate(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame` | Inside Bar Pattern |


## FEAT-INDI-05: Pinbar Candlestick Pattern Indicator (app.services.indicators.candles.pinbar)

| Function | Purpose |
|----------|---------|
| `Pinbar.calculate(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame` | Pinbar Pattern |


## FEAT-INDI-06: Hull Moving Average (HMA) Indicator (app.services.indicators.custom.hull_moving_average)

| Function | Purpose |
|----------|---------|
| `HullMovingAverage.calculate(df: pd.DataFrame, period: int = 9, column: str = 'close', **kwargs: Any) -> pd.DataFrame` | Hull Moving Average (HMA) |


## FEAT-INDI-07: Smart Money Concepts (SMC) Indicator (app.services.indicators.custom.smc)

| Function | Purpose |
|----------|---------|
| `SMC.calculate(df: pd.DataFrame, swing_length: int = 50, join_consecutive_fvg: bool = False, close_break: bool = True, **kwargs: Any) -> pd.DataFrame` | Smart Money Concepts (SMC) |


## FEAT-INDI-08: Deterministic error-code mapping for the indicators service boundary (app.services.indicators.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `to_indicators_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Indicators error payload. |
| `IndicatorError` (exception) | Base error type for all indicator calculations and registry operations. |
| `IndicatorConfigError` (exception) | Raised when configuration combination checks fail. |
| `IndicatorParameterError` (exception) | Raised when formula parameter checks fail (e.g. period <= 0). |
| `UnsupportedIndicatorError` (exception) | Raised when an unrecognized indicator ID is requested. |
| `UnsupportedTimeframeError` (exception) | Raised when timeframe is invalid or missing. |
| `UnsupportedDtypeError` (exception) | Raised when inputs contain unsupported float or integer precision. |
| `InvalidInputSchemaError` (exception) | Raised when DataFrame structure or column types fail validation. |
| `MissingRequiredColumnError` (exception) | Raised when required columns (e.g. 'close') are missing. |
| `InvalidOutputColumnError` (exception) | Raised when output column naming is malformed or invalid. |
| `OutputColumnConflictError` (exception) | Raised when output column names conflict with input columns. |
| `InvalidOutputModeError` (exception) | Raised when output modes are mutually exclusive or invalid. |
| `InputMutationError` (exception) | Raised when indicator calculations modify input data in place. |
| `DuplicateTimestampError` (exception) | Raised when duplicate timestamps are found in a single symbol dataset. |
| `NonMonotonicTimeError` (exception) | Raised when timestamps are not strictly ascending. |
| `AmbiguousTimestampError` (exception) | Raised when naive local time transitions make timestamps ambiguous. |
| `InvalidTimezoneError` (exception) | Raised when naive local timezone calculations are rejected. |
| `InvalidOHLCError` (exception) | Raised when prices violate physical boundaries (e.g. low > high). |
| `InsufficientDataError` (exception) | Raised when input row count is lower than indicator warmup requirements. |
| `LookaheadRiskError` (exception) | Raised when strategy attempts to consume data before it is closed/available. |
| `UnknownAdjustmentStatusError` (exception) | Raised when adjustment status of input prices is unknown. |
| `StateIncompatibleError` (exception) | Raised when state serialization does not match current specifications. |
| `StateCorruptedError` (exception) | Raised when state payload cannot be parsed. |
| `ResourceLimitExceededError` (exception) | Raised when calculations exceed memory budget or time limit. |
| `UnsupportedIntraBarAdjustmentError` (exception) | Raised when intra-bar corporate-action adjustments are unsupported. |
| `SymbolMappingRequiredError` (exception) | Raised when symbol mapping contract is required but missing. |
| `StubQuoteRejectedError` (exception) | Raised when bid/ask values represent stub quotes and are rejected. |
| `InvertedMarketError` (exception) | Raised when ask is less than bid. |
| `SpreadThresholdExceededError` (exception) | Raised when bid/ask spread exceeds the configured threshold. |
| `FormulaVersionMismatchError` (exception) | Raised when calculation uses incompatible formula versions. |
| `DeprecatedIndicatorError` (exception) | Raised when a deprecated indicator is requested under strict deprecation phase. |
| `UnsupportedOutOfCoreError` (exception) | Raised when indicator requires full context and out-of-core is unsupported. |
| `AccelerationBackendUnavailableError` (exception) | Raised when requested acceleration backend is not available. |
| `IndicatorTimeoutError` (exception) | Raised when calculation times out. |
| `CalculationCancelledError` (exception) | Raised when calculation is cancelled before completion. |
| `PartialResultError` (exception) | Raised when only a partial result is returned in strict modes. |
| `UnsupportedIncrementalModeError` (exception) | Raised when incremental calculation mode is not supported by the indicator. |
| `CustomIndicatorRejectedError` (exception) | Raised when conformance or side-effect checks reject custom indicators. |
| `AccessDeniedError` (exception) | Raised when actor/workflow lacks basic access to indicator services. |
| `ProprietaryUnauthorizedError` (exception) | Raised when access control blocks proprietary/licensed indicators. |
| `SLOViolationError` (exception) | Raised when SLO monitoring policy triggers synchronous rejection. |


## FEAT-INDI-09: Moving Average Convergence Divergence (MACD) Indicator (app.services.indicators.momentum.macd)

| Function | Purpose |
|----------|---------|
| `MACD.calculate(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, column: str = "close", **kwargs: Any) -> pd.DataFrame` | Moving Average Convergence Divergence (MACD) |


## FEAT-INDI-10: Relative Strength Index (RSI) Indicator (app.services.indicators.momentum.rsi)

| Function | Purpose |
|----------|---------|
| `RSI.calculate(df: pd.DataFrame, period: int = 14, column: str = 'close', **kwargs: Any) -> pd.DataFrame` | Relative Strength Index (RSI) |


## FEAT-INDI-11: Williams %R Indicator (app.services.indicators.momentum.will_r)

| Function | Purpose |
|----------|---------|
| `WilliamsR.calculate(df: pd.DataFrame, period: int = 14, **kwargs: Any) -> pd.DataFrame` | Williams %R |


## FEAT-INDI-12: Bollinger Bands Indicator (app.services.indicators.trend.bollinger_bands)

| Function | Purpose |
|----------|---------|
| `BollingerBands.calculate(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, column: str = "close", **kwargs: Any) -> pd.DataFrame` | Bollinger Bands |


## FEAT-INDI-13: Exponential Moving Average (EMA) Indicator (app.services.indicators.trend.ema)

| Function | Purpose |
|----------|---------|
| `EMA.calculate(df: pd.DataFrame, period: int = 10, column: str = 'close', **kwargs: Any) -> pd.DataFrame` | Exponential Moving Average (EMA) |


## FEAT-INDI-14: Simple Moving Average (SMA) Indicator (app.services.indicators.trend.sma)

| Function | Purpose |
|----------|---------|
| `SMA.calculate(df: pd.DataFrame, period: int = 10, column: str = 'close', **kwargs: Any) -> pd.DataFrame` | Simple Moving Average (SMA) |


## FEAT-INDI-15: Weighted Moving Average (WMA) Indicator (app.services.indicators.trend.wma)

| Function | Purpose |
|----------|---------|
| `WMA.calculate(df: pd.DataFrame, period: int = 10, column: str = 'close', **kwargs: Any) -> pd.DataFrame` | Weighted Moving Average (WMA) |


## FEAT-INDI-16: Average True Range (ATR) Indicator (app.services.indicators.volatility.atr)

| Function | Purpose |
|----------|---------|
| `ATR.calculate(df: pd.DataFrame, period: int = 14, **kwargs: Any) -> pd.DataFrame` | Average True Range (ATR) |


## FEAT-INDI-17: Standard Deviation Indicator (app.services.indicators.volatility.standard_deviation)

| Function | Purpose |
|----------|---------|
| `StandardDeviation.calculate(df: pd.DataFrame, period: int = 20, column: str = 'close', **kwargs: Any) -> pd.DataFrame` | Standard Deviation |


## FEAT-INDI-18: Chaikin Money Flow (CMF) Indicator (app.services.indicators.volume.cmf)

| Function | Purpose |
|----------|---------|
| `CMF.calculate(df: pd.DataFrame, period: int = 20, **kwargs: Any) -> pd.DataFrame` | Chaikin Money Flow (CMF) |


## FEAT-INDI-19: Money Flow Index (MFI) Indicator (app.services.indicators.volume.mfi)

| Function | Purpose |
|----------|---------|
| `MFI.calculate(df: pd.DataFrame, period: int = 14, **kwargs: Any) -> pd.DataFrame` | Money Flow Index (MFI) |


## FEAT-INDI-20: On-Balance Volume (OBV) Indicator (app.services.indicators.volume.obv)

| Function | Purpose |
|----------|---------|
| `OBV.calculate(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame` | On-Balance Volume (OBV) |


## FEAT-INDI-21: Price Volume Distribution (PVD) / Volume-by-Price Indicator (app.services.indicators.volume.price_volume_distribution)

| Function | Purpose |
|----------|---------|
| `PriceVolumeDistribution.calculate(df: pd.DataFrame, period: int = 20, bins: int = 10, **kwargs: Any) -> pd.DataFrame` | Price Volume Distribution (PVD) |
