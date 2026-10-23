# Core Helper Modules (`app/include`)

This package provides foundational utility modules for temporal features, market data contracts, trading proxies, and rule execution building blocks:
- `app.include.bar_time`: Provides `DateTime`, `BarTime`, and `TimeConditions` for high-precision epoch-millisecond calendar/session arithmetic, shift-indexed timestamp series, and bar/tick temporal rule predicates.
- `app.include.generators`: Provides `RandomGenerator` for reproducible simulation series (`XorShift`, `SplitMix`).
- `app.include.contracts`: Provides foundational data contracts, order records, and domain value objects.
- `app.include.enums`: Provides canonical trading enumerations, execution modes, and statuses.
- `app.include.trading`: Provides asynchronous trading proxy library, mutation builders, and master `Trading` facade.
- `app.include.data`: Provides historical market data readers (`get_historical_bars`, `get_ticks`), boundary validators (`validate_request`, `validate_rows`), DataFrame converters (`bars_to_dataframe`, `ticks_to_dataframe`), and provider protocols (`DataBackend`, `DataBrokerBackend`).
- `app.include.actions`: Provides side-effect action blocks, variable assignments, chart annotations, journal/file logging, and email notifications (`Actions`).
- `app.include.comparisons`: Provides arithmetic comparisons, bar-to-bar crossovers, trend persistence, percentile rankings, and moving average conditions (`Comparisons`).
- `app.include.functions`: Provides arithmetic operations, mathematical functions, date/time integers, rolling period rankings, and pip conversions (`Functions`).
- `app.include.price`: Provides single-bar OHLCV primitives (`BarPrice`), bid/ask spread metrics (`QuotePrice`), multi-timeframe bar resampling (`MTFPrice`), and session windows (`SessionPrice`).
- `app.include.types`: Provides generic mutable state container (`Variable`), strongly typed variables (`BooleanVariable`, `DoubleVariable`, `IntVariable`), constants, and types facade (`Types`).
