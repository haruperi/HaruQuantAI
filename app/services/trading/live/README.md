# Trading Live and Paper Session Lifecycle

This feature module implements `FEAT-TRD-07`. The authoritative lifecycle,
configuration, gate-order, and requirement definitions are in
[`../README.md`](../README.md), Section 4.7.

`config.py` validates mutation-safe runtime configuration, `session.py` owns
admission/startup/recovery/shutdown state and typed authority ports, and
`gates.py` executes the canonical mandatory gate order. `facade.py` exposes
function-only construction, lifecycle, status, and state inspection; the
internal `LiveSession` class is not public. External consumers use documented
functions through `app.services.trading`.

The feature cannot create provider dependencies at import time and cannot
enable mutation before startup reconciliation and pre-mutation audit succeed.
