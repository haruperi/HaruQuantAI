<#-- Bar time -> Hour*100 + Minute. SQX BarTime: SQTime.getHHMM (hour*100+minute, e.g. 14:30 -> 1430). -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Hour * 100 + sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Minute)
