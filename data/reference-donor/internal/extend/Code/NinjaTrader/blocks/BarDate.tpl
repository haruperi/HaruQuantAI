<#-- Bar date -> (Year-1900)*10000 + Month*100 + Day. SQX BarDate: SQTime.getYmd, where getYmd uses
     getYear() = fullYear - 1900, so the year carries the -1900 offset (e.g. 11.6.2026 -> 1260611). -->
((sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Year - 1900) * 10000 + sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Month * 100 + sqClock(<@printSeriesAt block shift><@printSeries block "Time" /></@printSeriesAt>).Day)
