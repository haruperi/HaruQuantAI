# Simulation Broker Channel

`FEAT-BRK-17` is the in-process, socket-free Brokers adapter. It delegates the
published MT5-mirroring intersection through a Brokers-owned structural
authority port and owns no matching, accounting, credentials, or transport.

The only admitted identity pair is `sim` / `simulation`. Lifecycle state and
events are authority-backed. Read envelopes carry exact canonical payloads plus
source sequence and aware-UTC observation, receipt, availability, and simulated
clock evidence. Reversed/future time, stale observations, duplicate/missing/gapped/
out-of-order delivery, and unbound authority reads fail closed. The adapter never
recalculates account, position, or order values and never silently sorts delivery.

Admitted reads cover symbols/current specification, revision-bound trading
sessions, quotes/spreads/ticks/bars, permissions, account/balances, positions,
open orders, and order history. Deal and transaction reads remain unsupported.
Weekly sessions alone do not certify dated exceptions. Admitted mutations cover
check/place/modify/cancel order and modify/reduce/close position. Each delegates
one immutable request through a request-bound provider-shaped envelope, reuses
the verified MT5 retcode/mapping path, and rejects route, environment, tamper,
duplicate-idempotency, malformed-result, and unseeded-timeout evidence. The
adapter never matches, fills, accounts, or derives position state. Every other
unadmitted operation returns `BROKER_CAPABILITY_UNSUPPORTED`.
