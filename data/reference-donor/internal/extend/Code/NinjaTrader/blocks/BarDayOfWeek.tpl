<#-- Bar day of week (0=Sun..6=Sat) -> (int)sqClock(Time[barsAgo]).DayOfWeek. SQX getDayOfWeekOriginal (0=Sun) ==
     C# DateTime.DayOfWeek (0=Sun). (JForex .tpl uses the 1-7 getDayOfWeek by mistake; Java/MT5/EL use 0=Sun.) -->
(int)sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).DayOfWeek
