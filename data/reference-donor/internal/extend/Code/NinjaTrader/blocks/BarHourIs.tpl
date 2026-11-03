<#-- Bar hour equals #Hour# -> (sqClock(Time[barsAgo]).Hour == Hour). -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Hour == <@printParam block "#Hour#" />)
