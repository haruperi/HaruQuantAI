<#-- Is month last trading day -> current bar's day equals the month's last trading
     day (calendar last day, shifted back over the weekend when weekends excluded).
     Mirrors SQ.Blocks.BarAndTime.IsMonthLastTradingDay.java via the sqIsMonthLastTradingDay helper. -->
<#global sqUsesMonthDay = true>sqIsMonthLastTradingDay(<@printChartIndex block />, <@printParam block "#IncludeWeekends#" "false" />)
