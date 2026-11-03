<#-- Bar minute equals #Minute# -> (sqClock(Time[barsAgo]).Minute == Minute). -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Minute == <@printParam block "#Minute#" />)
