<#-- Bar opens below the LinReg line of the previous bar (Open[shift] < LinReg literal 1).
     Parity with LinRegBarOpensBelow.java. -->
<@compress_single_line>(<@printSeriesAt block shift><@printSeries block "Open" /></@printSeriesAt> < sqRound(<@printLinRegValueAt block "1" />, 6))</@compress_single_line>