<#-- Bar month equals #Month# (1-12) -> (sqClock(Time[barsAgo]).Month == Month). Java/MT5/EL use 1-12
     (getMonthOriginal, editor January=1); C# .Month is 1-12. (JForex .tpl uses 0-11 getMonth by mistake.) -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Month == <@printParam block "#Month#" />)
