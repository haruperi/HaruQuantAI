<#-- Bar minute (0-59) -> sqClock(Time[barsAgo]).Minute. SQX BarMinute: SQTime.getMinute(Chart.Time(Shift)) - only the
     block's own #Shift#; the caller's bar offset (a count comparison stepping over bars) is not applied, as
     BarMinute.java ignores its relativeShift. -->
sqClock(<@printSeriesAt block "0"><@printSeries block "Time" /></@printSeriesAt>).Minute
