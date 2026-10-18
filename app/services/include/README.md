# Core Helper Modules (`app/services/include`)

This package provides foundational utility modules for time arithmetic, bar time calculations, and random number generation:
- `app.services.include.time`: Defines `HQTime` for high-precision timestamp handling and formatting.
- `app.services.include.bar_time`: Provides `BarTime`, `DateTimeSeries`, and `TimeConditions` for bar/tick temporal alignment.
- `app.services.include.generators`: Provides `RandomGenerator` for reproducible simulation series.
- `app.services.include.contracts`: Provides foundational data contracts and domain value objects.
- `app.services.include.enums`: Provides canonical trading enumerations and statuses.
- `app.services.include.trading`: Provides MQL5 asynchronous trading proxy library, mutation builders, and master `Trading` facade.
- `app.services.include.data`: Provides historical market data readers (`get_historical_bars`, `get_ticks`), boundary validators (`validate_request`, `validate_rows`), DataFrame converters (`bars_to_dataframe`, `ticks_to_dataframe`), and provider protocols (`DataBackend`, `DataBrokerBackend`).
