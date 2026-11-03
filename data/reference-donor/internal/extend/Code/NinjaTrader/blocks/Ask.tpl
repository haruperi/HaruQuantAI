<#-- Ask price -> NinjaScript GetCurrentAsk(0) at shift 0, Close[shift] above it. Parity with Ask.java, which on the
     NinjaTrader engine reads Chart.Close(relativeShift). A parent evaluates this block at a shift (a cross
     reads [1] and [0]); GetCurrentAsk(0) has no bars-ago, so a shifted ask is the bar close the backtest reads.
     In a historical backtest GetCurrentAsk(0) is the bar close as well; in real time it is the live quote. -->
<@compress_single_line><#if shift?string == "0">GetCurrentAsk(0)<#else><@printSeriesAt block shift>Close</@printSeriesAt></#if></@compress_single_line>