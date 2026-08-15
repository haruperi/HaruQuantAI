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
Weekly sessions alone do not certify dated exceptions. Mutations remain unavailable
until their owning phase, and every unadmitted operation returns
`BROKER_CAPABILITY_UNSUPPORTED`.
