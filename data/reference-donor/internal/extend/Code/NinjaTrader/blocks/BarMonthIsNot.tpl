<#-- Bar month not equal #Month# (1-12) -> (sqClock(Time[barsAgo]).Month != Month). See BarMonthIs. -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Month != <@printParam block "#Month#" />)
