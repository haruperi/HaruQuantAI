# Python bridge symbol snapshots

`Experts/PythonBridge.mq5` serializes `SymbolInfo` snapshots using the nested
contract in `app/include/contracts.py`: `price`, `spread`, `margin`, `volume`,
`trade`, `swap`, `session`, and `state`. The individual native `CSymbolInfo`
property commands remain independent of the snapshot format.

`price.tick_size` carries `SYMBOL_POINT`; `price.tick_step` carries
`SYMBOL_TRADE_TICK_SIZE`. Broker commission rules remain available as JSON in
`trade.commission_settings`; they are not reduced to a claimed fixed commission.
Trading sessions come from `SymbolInfoSessionTrade`.

After changing the source, compile it with the target terminal's MetaEditor.
Replace the terminal's installed Expert with the rebuilt `PythonBridge.ex5` and
reload the Expert on its chart to use the new snapshot format. The compiled
artifact in this directory accompanies the source; an already running Expert
continues executing the version loaded by the terminal.
