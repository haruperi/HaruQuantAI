<#-- Bar hour (0-23) -> native NinjaScript sqClock(Time[barsAgo]).Hour. SQX BarHour: SQTime.getHour(Chart.Time(shift)). -->
sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Hour
