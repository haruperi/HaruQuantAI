# FEAT-BRK-02 MetaTrader Direct Broker Channel

This folder is the sole production owner of this focused Brokers feature. Current status is `Partial` until the validation gates in the package README complete. Public API, contracts, requirements, and usage evidence are registered only in `app/services/brokers/README.md`.

Live market presentation uses `snapshot_protocol.py` and
`snapshot_gateway.py`: one MQL5 EA exchanges revisioned symbol-demand commands,
acknowledgments, and one-second multi-symbol snapshots over a persistent local
TCP connection. Active Data consumers define a bounded 200-symbol union; the
gateway restores it after reconnect, accepts snapshots only for the latest
acknowledged revision, and retains a 30-second grace only for partial demand
changes. Final-consumer release immediately sends an empty complete set; the EA
then performs no quote reads or snapshot publication, retaining only a bounded
idle heartbeat on the authenticated control connection until non-empty demand
is acknowledged. The official MT5 Python
package remains the request/response control and history channel and is not a
live-stream producer.

API composition supplies the listener's database-backed connection settings
and decrypted authentication token. Brokers validates the EA declaration and
keeps the token in memory only; it never persists or exposes credential values.

`InpSymbols` is bootstrap-only. After authentication, protocol v2 commands are
the runtime authority. Public demand operations are exposed only through
`app.services.brokers`; no UI or API module communicates with the EA directly.
