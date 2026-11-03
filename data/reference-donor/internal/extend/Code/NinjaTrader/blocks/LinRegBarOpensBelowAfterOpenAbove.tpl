<#-- Opens below the LinReg line after the previous open was above it. Previous open (literal 1) above
     the line; current open (shift) below it. Both lines fixed at "1". Parity with
     LinRegBarOpensBelowAfterOpenAbove.java. -->
<@compress_single_line>(<@printSeriesAt block "1"><@printSeries block "Open" /></@printSeriesAt> > sqRound(<@printLinRegValueAt block "1" />, 6) && <@printSeriesAt block shift><@printSeries block "Open" /></@printSeriesAt> < sqRound(<@printLinRegValueAt block "1" />, 6))</@compress_single_line>