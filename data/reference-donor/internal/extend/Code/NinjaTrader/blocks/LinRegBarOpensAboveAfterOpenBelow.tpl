<#-- Opens above the LinReg line after the previous open was below it. Previous open (literal 1) below
     the line; current open (shift) above it. Both lines fixed at "1". Parity with
     LinRegBarOpensAboveAfterOpenBelow.java. -->
<@compress_single_line>(<@printSeriesAt block "1"><@printSeries block "Open" /></@printSeriesAt> < sqRound(<@printLinRegValueAt block "1" />, 6) && <@printSeriesAt block shift><@printSeries block "Open" /></@printSeriesAt> > sqRound(<@printLinRegValueAt block "1" />, 6))</@compress_single_line>