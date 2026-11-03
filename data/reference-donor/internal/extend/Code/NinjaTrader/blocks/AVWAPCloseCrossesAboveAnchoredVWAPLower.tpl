<#-- Bar Close crosses above the Anchored VWAP Lower band. -->
(<@printSeriesAt block "1"><@printSeries block "Close" /></@printSeriesAt> < sqRound(<@printAnchoredVWAPValueAt block "LOWER" "1" />, 6) && <@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printAnchoredVWAPValueAt block "LOWER" "0" />, 6))
