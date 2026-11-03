<#-- TradeRecentlyClosed -> a trade closed since the last evaluation AND within the current bar /
     minute (edge trigger over the closed-trade count, mirroring the Java lastIndexChecked field). -->
sqTradeRecentlyClosed(<@printParam block "#CheckThisBar#" />, <@printParam block "#CheckThisMinute#" />)
