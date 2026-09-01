# FEAT-BRK-CONNECT_DUKASCOPY — Dukascopy Provider

Read-only, sandbox-only Dukascopy provider feature. Readiness probes use the caller's
explicit configured provider symbol; the old hard-coded EURUSD readiness probe is not
used by the feature boundary. Account and order operations fail closed.

Provides only `broker.provider.dukascopy@1`.
