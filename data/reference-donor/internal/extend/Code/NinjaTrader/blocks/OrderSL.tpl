<#-- OrderSL -> price of the working managed "Stop loss" order (0 when none). With the per-bar
     trailing manage this reads the CURRENT effective stop. Order identification is ignored (NT Managed single position).      #Direction# is honoured on every block of this family. MagicNumber/Comment cannot be
     honoured (NT Managed keeps a single position), but the direction of that position can.
     The level comes from the register of live orders (sqStopOrders), which a backtest needs because
     the strategy's Orders collection is empty there; sqUsesOrderLevels asks Main.tpl to emit it.
-->
<#assign sqUsesOrderLevels = true />sqOrderSL(<@printParam block "#Direction#" "0" />)
