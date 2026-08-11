# Indicators Core

This module owns `FEAT-INDI-01`: immutable calculation contracts, deterministic
errors and results, official registry discovery, warmup resolution,
whole-request validation, and closed-input enforcement.

The canonical feature status, requirements, public signatures, workflow mapping,
and usage evidence remain in the package
[`README.md`](../README.md#41-core--contracts-results-validation-and-discovery).
This file does not define a second Feature Registry.

Production files:

- `errors.py`: deterministic public error boundary and response metadata.
- `error_catalog.py`: immutable catalogue of the twenty-two approved
  Indicators error definitions.
- `contracts.py`: immutable calculation and result-shape contracts.
- `results.py`: manifest, checksums, projections, and copied joins.
- `registry.py`: immutable official indicator metadata.
- `validation.py`: request validation and exact warmup resolution.
- `closed_input.py`: fail-closed interval, availability, and timeframe checks.

Public consumers import all approved names through `app.services.indicators`.
Every Core operation returns `StandardResponse[T]`; successful `T` is stored
directly in `data`, while deterministic `IND_*` failures use the error branch.
The module performs no acquisition, persistence, network, broker, or execution
work.
