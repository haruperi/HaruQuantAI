<#-- Close above the session POC. -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printSeriesAt block "0">SqVolumeProfile(<@printInput block />, <@printParam block "#SessionType#" />, <@printParam block "#ProfileRows#" />, 2, 3, <@printParam block "#ValueAreaPct#" />, 0).Values[0]</@printSeriesAt>, 6))
