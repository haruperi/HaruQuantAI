<#-- Bar Close is above the Anchored VWAP. -->
(<@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printAnchoredVWAPValueAt block "VWAP" "0" />, 6))
