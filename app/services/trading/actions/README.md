# Trading Route-Aware Public Actions

This feature module implements `FEAT-TRD-08`. The authoritative action,
dependency-port, workflow, and requirement definitions are in
[`../README.md`](../README.md), Section 4.8.

`dependencies.py` defines immutable injected ports; `orders.py`,
`positions.py`, and `controls.py` own focused public actions; `emergency.py`
owns gated batch controls; `rebalance.py` executes receiver-owned authorized
reductions; `runtime.py` composes one evaluation cycle; and `_shared.py`
contains private identity helpers. External consumers use documented exports
through `app.services.trading`.

The package-root surface is function-only: `create_trading_dependencies` builds
the internal dependency container, while the action functions execute its
documented operations. The internal `TradingDependencies` class is not public.

Every mutation follows validation, exact Risk authority, kill-switch,
idempotency, persisted-attempt, dispatch, receipt, and reconciliation rules.
