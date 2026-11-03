<#-- Close above SuperTrend (not a cross - just current Close > SuperTrend). Reuses printSuperTrendValueAt.
     Parity with BarClosesAboveSuperTrend.java (curClose > curSTValue).      IGNORES #Mode#: values="Basic=1" - one declared value.
-->
<@compress_single_line>(<@printSeriesAt block "0"><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printSuperTrendValueAt block "0" />, 6))</@compress_single_line>