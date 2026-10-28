# Core Helper Modules (`app/include`)

This package provides foundational utility modules for temporal features, market data contracts and rule execution building blocks:
- `app.include.blocks.bar_time`: Provides independently maintained temporal strategy blocks (bar date/time extractors, current broker clock accessors, calendar/session conditions, and trading-day predicates) with `BlockSpec` metadata alongside `DateTime`, `BarTime`, and `TimeConditions` facades.
- `app.include.generators`: Provides `RandomGenerator` for reproducible simulation series (`XorShift`, `SplitMix`).
- `app.include.contracts`: Provides foundational data contracts, order records, and domain value objects.
- `app.include.enums`: Provides canonical trading enumerations, execution modes, and statuses.
- `app.include.actions`: Provides side-effect action blocks, variable assignments, chart annotations, journal/file logging, and email notifications (`Actions`).
- `app.include.blocks.comparisons`: Provides independently maintained comparative condition strategy blocks (arithmetic relations, bar-to-bar crossovers, trend persistence, percentile rankings, moving average conditions, and boolean logic) with `BlockSpec` metadata and `Comparisons` facade.
- `app.include.blocks.indicators`: Provides canonical single-class indicators with validated parameters, named outputs, and strategy metadata. Indicator-specific helpers remain in their indicator files.
- `app.include.blocks.functions`: Provides arithmetic operations, mathematical functions, date/time integers, rolling period rankings, and pip conversions (`Functions`).
- `app.include.price`: Provides single-bar OHLCV primitives (`BarPrice`), bid/ask spread metrics (`QuotePrice`), multi-timeframe bar resampling (`MTFPrice`), and session windows (`SessionPrice`).
- `app.include.types`: Provides generic mutable state container (`Variable`), strongly typed variables (`BooleanVariable`, `DoubleVariable`, `IntVariable`), constants, and types facade (`Types`).
- `app.include.calculators`: Provides stateless batch kernels (`sma_kernel`, `ema_kernel`, `smma_kernel`, `lwma_kernel`, `tema_kernel`, `rsi_kernel`) and streaming stateful rolling-window calculators (`AbstractCalculator`, `AverageCalculator`, `HighestCalculator`, `LowestCalculator`, `RSICalculator`, `StdDevCalculator`, `SumCalculator`) supporting tick-level intra-bar recalculation and bar-advance transitions for indicator execution.

Market-history reads and record conversion live in `app.workspace.data_manager.data.history` and `app.workspace.data_manager.data.conversions`. Import them directly; this foundational package does not re-export workspace operations.

Trading APIs live in `app.workspace.trading`; this package owns their shared contracts and enums.

Batch functions process complete arrays directly; streaming classes update rolling
state one bar or tick at a time. Batch calculations never replay history through
`on_bar_update`. Their existing initialization and warmup contracts are preserved;
placing both execution modes here does not imply batch/stream output parity.
MACD and Bollinger composition stays in the respective indicator modules.
