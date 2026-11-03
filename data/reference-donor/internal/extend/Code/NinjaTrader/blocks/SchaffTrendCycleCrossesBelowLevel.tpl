<#-- Schaff Trend Cycle crosses below Level: previous above, current below. Parity with
     SchaffTrendCycleCrossesBelowLevel.java (Value < Level && Value[1] > Level). -->
<@compress_single_line>(sqRound(<@printSTCValueAt block "0" />, 6) < <@printParam block "#Level#" /> && sqRound(<@printSTCValueAt block "1" />, 6) > <@printParam block "#Level#" />)</@compress_single_line>