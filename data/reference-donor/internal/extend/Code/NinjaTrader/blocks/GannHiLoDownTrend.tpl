<#-- Gann HiLo downtrend: Close below the activator. Parity with GannHiLoDownTrend.java (Close < GHA).
     Compared at 6 decimals, as the Java reads getRounded(). -->
<@compress_single_line>(<@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> < sqRound(<@printGannHiLoValueAt block "0" />, 6))</@compress_single_line>