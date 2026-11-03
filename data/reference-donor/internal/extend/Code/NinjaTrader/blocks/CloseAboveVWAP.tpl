<#-- Close above VWAP: Close[Shift] > VWAP(VWAPPeriod)[Shift]. Reuses printVWAPValueAt (the installed SqVWAP).
     Parity with CloseAboveVWAP.java (close > VWAP.getRounded(Shift)). -->
<@compress_single_line>(<@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printVWAPValueAt block "0" />, 6))</@compress_single_line>