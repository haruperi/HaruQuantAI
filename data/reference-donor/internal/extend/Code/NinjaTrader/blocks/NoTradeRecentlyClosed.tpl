<#-- NoTradeRecentlyClosed -> the exact negation of TradeRecentlyClosed, which is what the Java is:
     NoTradeRecentlyClosed extends TradeRecentlyClosed and returns !checkTradeClosedRecently()
     (the Tradestation short-circuit above it does not apply to NinjaTrader). It therefore INHERITS
     #CheckThisBar#/#CheckThisMinute# and must honour them.
     It reuses the positive block's sqTradeRecentlyClosed helper, edge trigger included, so it answers
     "no trade closed since the last evaluation, within the window the parameters define". Order
     identification is ignored (NT Managed single position). -->
(!sqTradeRecentlyClosed(<@printParam block "#CheckThisBar#" "true" />, <@printParam block "#CheckThisMinute#" "true" />))
