<#-- SR percent rank above level for #Bars# bars, from the installed SqSRPercentRankLevelBars indicator
     (1 when the condition holds). Mirrors SRPercRankAboveLevelXBars.java.
     Output e.g.: (SqSRPercentRankLevelBars(Close, 1, 120, 12, 80, 2, 1).Values[0][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqSRPercentRankLevelBars(<@printInput block />, <@printParam block "#Mode#" />, <@printParam block "#Length#" />, <@printParam block "#ATRPeriod#" />, <@printParam block "#Level#" />, <@printParam block "#Bars#" />, 1).Values[0]</@printSeriesAt> > 0.5)
