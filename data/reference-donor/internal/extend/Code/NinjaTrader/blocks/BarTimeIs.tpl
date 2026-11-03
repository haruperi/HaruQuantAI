<#-- Bar time equals #Hour#:#Minute# -> (sqClock(Time[barsAgo]).Hour == Hour && sqClock(Time[barsAgo]).Minute == Minute).
     SQX compares HH:MM of the bar time to the param HH:MM. -->
(sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Hour == <@printParam block "#Hour#" /> && sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Minute == <@printParam block "#Minute#" />)
