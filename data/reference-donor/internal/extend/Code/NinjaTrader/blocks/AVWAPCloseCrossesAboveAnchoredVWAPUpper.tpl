<#-- Bar Close crosses above the Anchored VWAP Upper band. -->
(<@printSeriesAt block "1"><@printSeries block "Close" /></@printSeriesAt> < sqRound(<@printAnchoredVWAPValueAt block "UPPER" "1" />, 6) && <@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printAnchoredVWAPValueAt block "UPPER" "0" />, 6))
