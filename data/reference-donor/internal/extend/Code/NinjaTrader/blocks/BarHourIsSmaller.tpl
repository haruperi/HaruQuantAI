<#-- Bar hour less than #Hour# -> (sqClock(Time[barsAgo]).Hour < Hour). -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Hour < <@printParam block "#Hour#" />)
