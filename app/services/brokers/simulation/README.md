# Simulation Broker Channel

`FEAT-BRK-17` is the in-process, socket-free Brokers adapter. It delegates the
published MT5-mirroring intersection through a Brokers-owned structural
authority port and owns no matching, accounting, credentials, or transport.

The only admitted identity pair is `sim` / `simulation`. Lifecycle state and
events are authority-backed, mutations fail while disconnected, and all
unadmitted operations return `BROKER_CAPABILITY_UNSUPPORTED`.
