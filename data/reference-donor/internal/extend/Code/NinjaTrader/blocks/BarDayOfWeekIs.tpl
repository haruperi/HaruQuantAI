<#-- Bar day of week equals #Day# (0=Sun..6=Sat) -> ((int)sqClock(Time[barsAgo]).DayOfWeek == Day). Java/MT5/EL
     use 0=Sun (getDayOfWeekOriginal, editor Sunday=0) = C# DayOfWeek. (JForex .tpl uses 1-7 by mistake.) -->
((int)sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).DayOfWeek == <@printParam block "#Day#" />)
