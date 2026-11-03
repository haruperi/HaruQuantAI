<#-- LastOrderWas -> direction of the last CLOSED trade equals #Direction# (Long=1/Short=-1).
     sqLastOrderType returns 0 while no trade exists -> false, exactly like the Java loop.
     Open-position trades are not part of AllTrades (approximation). -->
(sqLastOrderType() == <@printParam block "#Direction#" />)
