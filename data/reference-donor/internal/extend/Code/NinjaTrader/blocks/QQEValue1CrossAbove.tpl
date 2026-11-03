<#-- QQE Value1 crosses above Level: prev (Shift+1) below Level, current (Shift) above. Parity with
     QQEValue1CrossAbove.java. -->
<@compress_single_line>(sqRound(<@printQQEValue1At block "1" />, 6) < <@printParam block "#Level#" /> && sqRound(<@printQQEValue1At block "0" />, 6) > <@printParam block "#Level#" />)</@compress_single_line>