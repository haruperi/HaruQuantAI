<#-- Fast VWAP below slow VWAP: VWAP(FastPeriod) < VWAP(SlowPeriod), two SqVWAP indicators.
     Parity with FastVWAPBelowSlowVWAP.java. -->
<#global sqUsesIndicatorPackage = true><@compress_single_line>(sqRound(<@printSeriesAt block "0">SqVWAP(<@printInput block />, <@printParam block "#FastPeriod#" />).Values[0]</@printSeriesAt>, 6) < sqRound(<@printSeriesAt block "0">SqVWAP(<@printInput block />, <@printParam block "#SlowPeriod#" />).Values[0]</@printSeriesAt>, 6))</@compress_single_line>
