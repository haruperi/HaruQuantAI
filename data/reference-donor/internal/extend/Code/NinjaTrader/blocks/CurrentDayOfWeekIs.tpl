<#-- Current day of week equals #Day# (0=Sun..6=Sat) -> ((int)sqClock(Time[0]).DayOfWeek == Day) (current bar). See BarDayOfWeekIs. -->
((int)sqClock(Time[0]).DayOfWeek == <@printParam block "#Day#" />)
