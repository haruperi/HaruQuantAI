# Durable Execution Session Registry

This module owns `FEAT-TRD-12`: durable logical SIM, DEMO, and LIVE execution
sessions. A registry record is not a permanently open network connection. It
persists identity, mode, credential references, defaults, lifecycle, recovery
and audit history while Brokers owns provider connections and Simulator owns
virtual engines and account ledgers.

Exactly one default may exist per principal/environment/mode and exactly one
foreground session may be active per principal/environment. Credentials are
never stored; only opaque references cross this boundary. Deletion is
recoverable archival and is refused for active, running, or default sessions.

Start requires injected authority evidence whose provider-authored mode exactly
matches the record. Stop requires positive reconciliation evidence. Unknown or
conflicting authority state fails closed.
