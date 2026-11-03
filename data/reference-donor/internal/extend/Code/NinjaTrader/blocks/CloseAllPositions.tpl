<#-- CloseAllPositions -> exit the position in the requested direction at market.
     ExitLong()/ExitShort() with no arguments close the entire current position in that
     direction (NinjaScript Managed Approach). #Direction# is Long=1 / Short=-1 / Any=0
     (default Any); Any emits both.
     Magic/comment identification (MT) is ignored - Managed has one aggregated position
     per direction.
     Docs: https://ninjatrader.com/support/helpguides/nt8/exitlong.htm
     Output (Any): ExitLong();
                   ExitShort(); -->
<@printExitByDirection block "#Direction#" />