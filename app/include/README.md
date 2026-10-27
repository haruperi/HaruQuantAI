# Core Helper Modules (`app/include`)

This package provides foundational utility modules for temporal features, market data contracts and rule execution building blocks:
- `app.include.bar_time`: Provides `DateTime`, `BarTime`, and `TimeConditions` for high-precision epoch-millisecond calendar/session arithmetic, shift-indexed timestamp series, and bar/tick temporal rule predicates.
- `app.include.generators`: Provides `RandomGenerator` for reproducible simulation series (`XorShift`, `SplitMix`).
- `app.include.contracts`: Provides foundational data contracts, order records, and domain value objects.
- `app.include.enums`: Provides canonical trading enumerations, execution modes, and statuses.
- `app.include.actions`: Provides side-effect action blocks, variable assignments, chart annotations, journal/file logging, and email notifications (`Actions`).
- `app.include.comparisons`: Provides arithmetic comparisons, bar-to-bar crossovers, trend persistence, percentile rankings, and moving average conditions (`Comparisons`).
- `app.include.indicators`: Provides technical indicator families (momentum, trend, volatility, volume, price action, regime) built on `BaseIndicator`; outputs are `IndicatorSeries` (alias of `contracts.DataframeSeries`). Restored from commit `013b40e^` (formerly `app/services/indicators`).
- `app.include.functions`: Provides arithmetic operations, mathematical functions, date/time integers, rolling period rankings, and pip conversions (`Functions`).
- `app.include.price`: Provides single-bar OHLCV primitives (`BarPrice`), bid/ask spread metrics (`QuotePrice`), multi-timeframe bar resampling (`MTFPrice`), and session windows (`SessionPrice`).
- `app.include.types`: Provides generic mutable state container (`Variable`), strongly typed variables (`BooleanVariable`, `DoubleVariable`, `IntVariable`), constants, and types facade (`Types`).

Market-history reads and record conversion live in `app.workspace.data_manager.data.history` and `app.workspace.data_manager.data.conversions`. Import them directly; this foundational package does not re-export workspace operations.

Trading APIs live in `app.workspace.trading`; this package owns their shared contracts and enums.
