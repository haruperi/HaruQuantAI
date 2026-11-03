<#-- Schaff Trend Cycle crosses above Level: previous below, current above. Parity with
     SchaffTrendCycleCrossesAboveLevel.java (Value > Level && Value[1] < Level). -->
<@compress_single_line>(sqRound(<@printSTCValueAt block "0" />, 6) > <@printParam block "#Level#" /> && sqRound(<@printSTCValueAt block "1" />, 6) < <@printParam block "#Level#" />)</@compress_single_line>