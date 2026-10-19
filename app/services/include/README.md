# Core Helper Modules (`app/services/include`)

This package provides foundational utility modules for temporal features, market data contracts, trading proxies, and rule execution building blocks:
- `app.services.include.time`: Defines `HQTime` for high-precision timestamp handling, calendar sessions, and timezone conversion.
- `app.services.include.bar_time`: Provides `BarTime`, `DateTimeSeries`, and `TimeConditions` for bar/tick temporal alignment.
- `app.services.include.generators`: Provides `RandomGenerator` for reproducible simulation series (`XorShift`, `SplitMix`).
- `app.services.include.contracts`: Provides foundational data contracts, order records, and domain value objects.
- `app.services.include.enums`: Provides canonical trading enumerations, execution modes, and statuses.
- `app.services.include.trading`: Provides asynchronous trading proxy library, mutation builders, and master `Trading` facade.
- `app.services.include.data`: Provides historical market data readers (`get_historical_bars`, `get_ticks`), boundary validators (`validate_request`, `validate_rows`), DataFrame converters (`bars_to_dataframe`, `ticks_to_dataframe`), and provider protocols (`DataBackend`, `DataBrokerBackend`).
- `app.services.include.actions`: Provides side-effect action blocks, variable assignments, chart annotations, journal/file logging, and email notifications (`Actions`).
- `app.services.include.comparisons`: Provides arithmetic comparisons, bar-to-bar crossovers, trend persistence, percentile rankings, and moving average conditions (`Comparisons`).
- `app.services.include.functions`: Provides arithmetic operations, mathematical functions, date/time integers, rolling period rankings, and pip conversions (`Functions`).
- `app.services.include.price`: Provides single-bar OHLCV primitives (`BarPrice`), bid/ask spread metrics (`QuotePrice`), multi-timeframe bar resampling (`MTFPrice`), session windows (`SessionPrice`), and smoothed candles (`HeikenAshiPrice`).
- `app.services.include.types`: Provides generic mutable state container (`Variable`), strongly typed variables (`BooleanVariable`, `DoubleVariable`, `IntVariable`), constants, and types facade (`Types`).
