<#-- OrderPT -> price of the working managed "Profit target" order (0 when none). Order
     identification is ignored (NT Managed single position).      #Direction# is honoured on every block of this family. MagicNumber/Comment cannot be
     honoured (NT Managed keeps a single position), but the direction of that position can.
     The level comes from the register of live orders (sqStopOrders), which a backtest needs because
     the strategy's Orders collection is empty there; sqUsesOrderLevels asks Main.tpl to emit it.
-->
<#assign sqUsesOrderLevels = true />sqOrderPT(<@printParam block "#Direction#" "0" />)
