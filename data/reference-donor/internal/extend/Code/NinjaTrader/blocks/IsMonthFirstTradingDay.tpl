<#-- Is month first trading day -> the current bar's day equals the month's first trading day
     (calendar 1st, shifted forward over the weekend when weekends are excluded).
     Mirrors SQ.Blocks.BarAndTime.IsMonthFirstTradingDay.java via the sqIsMonthFirstTradingDay helper.
     Day-granular, like the Java: TRUE for every bar of that day, not just the first one. A month-change
     test (Time[0].Month != Time[1].Month) answers a different question. -->
<#global sqUsesMonthDay = true>sqIsMonthFirstTradingDay(<@printChartIndex block />, <@printParam block "#IncludeWeekends#" "false" />)
