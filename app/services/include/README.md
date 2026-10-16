# Core Helper Modules (`app/services/include`)

This package provides foundational utility modules for time arithmetic, bar time calculations, and random number generation:
- `app.services.include.time`: Defines `HQTime` for high-precision timestamp handling and formatting.
- `app.services.include.bar_time`: Provides `BarTime`, `DateTimeSeries`, and `TimeConditions` for bar/tick temporal alignment.
- `app.services.include.generators`: Provides `RandomGenerator` for reproducible simulation series.
- `app.services.include.contracts`: Provides foundational data contracts and domain value objects.
- `app.services.include.enums`: Provides canonical trading enumerations and statuses.

> [!NOTE]
> Trading primitives, proxies, and facades have been modularized into `app.services.trading`.
> Market data primitives, readers, and simulators have been modularized into `app.workspace.data_manager`.
