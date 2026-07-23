## FEAT-INDC-01: Public indicator tools for HaruQuant (app.services.indicator._common)

| Function | Purpose |
|----------|---------|
| `list_indicators(pattern: str = '*', request_id: str \| None = None) -> dict` | List indicators matching a pattern. |
| `indicator(name: str, request_id: str \| None = None) -> dict` | Resolve an indicator by name. |
| `run_indicators(data: Any, selection: str = 'native', period: Any = 20, request_id: str \| None = None, **kwargs: Any) -> dict` | Run a group or pattern of indicators over market data. |


## FEAT-INDC-02: Currency Strength Indicator (app.services.indicator.custom.currency_strength)

| Function | Purpose |
|----------|---------|
| `calculate_pair_strength(data: pd.DataFrame, timeframe_weights: dict[str, float] \| None = None, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the calculate_pair_strength indicator. |
| `calculate_currency_strength(pair_data: dict[str, pd.DataFrame], timeframe_weights: dict[str, float] \| None = None, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the calculate_currency_strength indicator. |
| `get_top_pairs(currency_strength: pd.DataFrame, n_pairs: int = 10, min_strength_diff: float = 0.0, request_id: str \| None = None) -> dict[str, Any]` | Calculate the get_top_pairs indicator. |
| `currency_strength_indicator(pair_data: dict[str, pd.DataFrame], timeframe_weights: dict[str, float] \| None = None, price_col: str = 'close', include_pairs: bool = True, n_top_pairs: int = 10, request_id: str \| None = None) -> dict[str, Any]` | Calculate the currency_strength_indicator indicator. |


## FEAT-INDC-03: Smart Money Concepts indicator tools (app.services.indicator.custom.smc)

| Function | Purpose |
|----------|---------|
| `smc.fvg(ohlc: DataFrame, join_consecutive=False) -> DataFrame` | FVG - Fair Value Gap |
| `smc.swing_highs_lows(ohlc: DataFrame, swing_length: int = 50) -> DataFrame` | Swing Highs and Lows |
| `smc.bos_choch(ohlc: DataFrame, swing_length: int = 50, close_break: bool = True) -> DataFrame` | BOS - Break of Structure CHoCH - Change of Character |
| `smc.ob(ohlc: DataFrame, swing_length: int = 50, close_mitigation: bool = False) -> DataFrame` | OB - Order Blocks |
| `smc.previous_high_low(ohlc: DataFrame, timeframe: str = '1D') -> DataFrame` | Previous High Low |
| `fvg(ohlc: Any, request_id: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Calculate the fvg indicator. |
| `swing_highs_lows(ohlc: Any, request_id: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Calculate the swing_highs_lows indicator. |
| `bos_choch(ohlc: Any, request_id: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Calculate the bos_choch indicator. |
| `ob(ohlc: Any, request_id: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Calculate the ob indicator. |
| `previous_high_low(ohlc: Any, request_id: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Calculate the previous_high_low indicator. |


## FEAT-INDC-04: Indicator template for HaruQuant (app.services.indicator.indicator_template)

| Function | Purpose |
|----------|---------|
| `indicator_name(data: pd.DataFrame, period: int = 14, price_col: str = 'close') -> pd.DataFrame` | Compute the [Indicator Name] ([ABBR]) indicator. |


## FEAT-INDC-05: Relative Strength Index (RSI) indicator (app.services.indicator.momentum.rsi)

| Function | Purpose |
|----------|---------|
| `rsi(data: pd.DataFrame, period: int = 14, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the rsi indicator. |


## FEAT-INDC-06: Standard response helpers for indicator tools (app.services.indicator.standard)

| Function | Purpose |
|----------|---------|
| `serialize_indicator_result(value: Any) -> Any` | Serialize indicator output into JSON-safe data. |
| `run_indicator_tool(tool_name: str, operation: Callable[[], Any], *, request_id: str \| None = None, message: str \| None = None) -> dict[str, Any]` | Run an indicator operation and return the standard AI tool schema. |


## FEAT-INDC-07: Hurst Exponent indicator (app.services.indicator.statistical.hurst)

| Function | Purpose |
|----------|---------|
| `calculate_hurst(series: np.ndarray, request_id: str \| None = None) -> dict[str, Any]` | Calculate the calculate_hurst indicator. |
| `hurst(data: pd.DataFrame, period: int = 100, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the hurst indicator. |


## FEAT-INDC-08: Exponential moving average indicator (app.services.indicator.trend.ema)

| Function | Purpose |
|----------|---------|
| `ema(data: pd.DataFrame, span: int, price_col: str = 'close', adjust: bool = False, request_id: str \| None = None) -> dict[str, Any]` | Calculate the ema indicator. |


## FEAT-INDC-09: Simple moving average indicator (app.services.indicator.trend.sma)

| Function | Purpose |
|----------|---------|
| `sma(data: pd.DataFrame, window: int, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the sma indicator. |


## FEAT-INDC-10: Weighted moving average indicator (app.services.indicator.trend.wma)

| Function | Purpose |
|----------|---------|
| `wma(data: pd.DataFrame, window: int, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the wma indicator. |


## FEAT-INDC-11: Input validation helpers for deterministic indicator tools (app.services.indicator.validation)

| Function | Purpose |
|----------|---------|
| `require_dataframe(data: pd.DataFrame) -> pd.DataFrame` | Require a non-empty pandas DataFrame for indicator computation. |
| `require_columns(data: pd.DataFrame, columns: Iterable[str]) -> None` | Require columns to be present before computing an indicator. |
| `require_positive_int(value: int, *, name: str) -> None` | Require positive integer periods/windows for lookback-based indicators. |
| `require_positive_float(value: float, *, name: str) -> None` | Require positive floating parameters such as Bollinger standard deviations. |


## FEAT-INDC-12: Average True Range (ATR) indicator (app.services.indicator.volatility.atr)

| Function | Purpose |
|----------|---------|
| `atr(data: pd.DataFrame, period: int = 14, request_id: str \| None = None) -> dict[str, Any]` | Calculate the atr indicator. |


## FEAT-INDC-13: Bollinger Bands indicator (app.services.indicator.volatility.bbands)

| Function | Purpose |
|----------|---------|
| `bbands(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0, price_col: str = 'close', request_id: str \| None = None) -> dict[str, Any]` | Calculate the bbands indicator. |


## FEAT-INDC-14: Accumulation/Distribution indicator (app.services.indicator.volume.accumulation_distribution)

| Function | Purpose |
|----------|---------|
| `accumulation_distribution(data: pd.DataFrame, request_id: str \| None = None) -> dict[str, Any]` | Calculate the accumulation_distribution indicator. |

