# Core Helper Libraries (`app/services/libs`)

This package provides foundational utility modules for time arithmetic, bar time calculations, and random number generation:
- `app.services.libs.time`: Defines `HQTime` for high-precision timestamp handling and formatting.
- `app.services.libs.bar_time`: Provides `BarTime`, `DateTimeSeries`, and `TimeConditions` for bar/tick temporal alignment.
- `app.services.libs.generators`: Provides `RandomGenerator` for reproducible simulation series.

> [!NOTE]
> Trading primitives, proxies, and facades have been modularized into `app.services.trading`.
> Market data primitives, readers, and simulators have been modularized into `app.workspace.data_manager`.
