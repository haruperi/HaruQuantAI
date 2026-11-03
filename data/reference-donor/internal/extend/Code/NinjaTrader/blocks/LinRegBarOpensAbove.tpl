<#-- Bar opens above the LinReg line of the previous bar (Open[shift] > LinReg[shift+1 via literal 1]).
     Open via printSeries+printShift (honours #Chart#), LinReg fixed at "1". Parity with LinRegBarOpensAbove.java. -->
<@compress_single_line>(<@printSeriesAt block shift><@printSeries block "Open" /></@printSeriesAt> > sqRound(<@printLinRegValueAt block "1" />, 6))</@compress_single_line>