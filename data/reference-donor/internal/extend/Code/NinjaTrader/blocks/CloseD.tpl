<#-- CloseD -> SqCalendarOHLC(chart, tf=1 Day/Week/Month).PeriodValue(ohlc=3 O/H/L/C, base=1 PRIOR completed calendar Day, plus the block #Shift#).
     BAR-DERIVED calendar period, mirrors CloseD.java via Chart.CloseD(Shift+relativeShift). -->
<@printMultiTfOhlcValueAt block "1" "3" "0" shift />
