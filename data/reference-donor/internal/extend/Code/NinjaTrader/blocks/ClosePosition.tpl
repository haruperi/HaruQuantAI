<#-- ClosePosition -> close the position in the given direction at market (NinjaScript Managed:
     ExitLong()/ExitShort() close the whole position in that direction).
     #Direction# is Long=1 / Short=-1 / Any=0 and its DEFAULT is Any, which must close
     both directions - a binary long/short mapping would turn an unset direction into ExitLong()
     and never close a short.
     Magic/comment identification (MT) is ignored - Managed has one aggregated position per direction.
     Parity with EasyLanguage ClosePosition (Sell/BuyToCover next bar at market).      IGNORES #Size#: the only CloseSize formula StrategyQuant has is FullPosition, which is exactly what ExitLong()/ExitShort() do.
-->
<@printExitByDirection block "#Direction#" />