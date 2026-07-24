# Indicators Core

This module owns `FEAT-INDI-01`: immutable calculation contracts, deterministic
errors and results, official registry discovery, warmup resolution, and
whole-request validation.

The canonical feature status, requirements, public signatures, workflow mapping,
and usage evidence remain in the package
[`README.md`](../README.md#41-core--contracts-results-validation-and-discovery).
This file does not define a second Feature Registry.

Production files:

- `errors.py`: deterministic public error boundary.
- `contracts.py`: immutable calculation and result-shape contracts.
- `results.py`: manifest, checksums, projections, and copied joins.
- `registry.py`: immutable official indicator metadata.
- `validation.py`: request validation and exact warmup resolution.

Public consumers import all approved names through `app.services.indicators`.
The module performs no acquisition, persistence, network, broker, or execution
work.
