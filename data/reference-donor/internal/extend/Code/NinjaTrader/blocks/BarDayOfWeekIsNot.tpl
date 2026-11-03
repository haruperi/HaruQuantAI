<#-- Bar day of week not equal #Day# (0=Sun..6=Sat) -> ((int)sqClock(Time[barsAgo]).DayOfWeek != Day). See BarDayOfWeekIs. -->
((int)sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).DayOfWeek != <@printParam block "#Day#" />)
