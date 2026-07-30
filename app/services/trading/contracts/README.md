# Trading Canonical Contracts and Registries

This feature module implements `FEAT-TRD-01`. The authoritative contract,
public-export, and requirement definitions are in
[`../README.md`](../README.md), Section 4.1.

`models.py` owns immutable Trading boundary models, `errors.py` owns the finite
error and redaction boundary, `factories.py` exposes their package-root
`create_*`, `get_*`, and `is_*` functions, and `registry.py` owns the stable
function catalog. Classes and constants remain internal. External consumers
must import documented functions only from `app.services.trading`.

This module performs no provider, filesystem, persistence, or network work at
import time.
