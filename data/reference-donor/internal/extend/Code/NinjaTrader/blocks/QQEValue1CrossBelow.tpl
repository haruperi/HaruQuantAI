<#-- QQE Value1 crosses below Level: prev (Shift+1) above Level, current (Shift) below. Parity with
     QQEValue1CrossBelow.java. -->
<@compress_single_line>(sqRound(<@printQQEValue1At block "1" />, 6) > <@printParam block "#Level#" /> && sqRound(<@printQQEValue1At block "0" />, 6) < <@printParam block "#Level#" />)</@compress_single_line>