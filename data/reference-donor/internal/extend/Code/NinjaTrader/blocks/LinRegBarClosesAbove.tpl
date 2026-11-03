<#-- Bar closes above the LinReg line (Close[shift] > LinReg[shift]). Close via printSeries+printShift (honours #Chart#),
     LinReg uses #ComputedFrom# input. Parity with LinRegBarClosesAbove.java. -->
<@compress_single_line>(<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printLinRegValueAt block shift />, 6))</@compress_single_line>