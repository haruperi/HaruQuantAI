<#-- QQE Value1 crosses below Value2: prev Value1 above Value2, current Value1 below Value2. Parity with
     QQEValue1CrossBelowValue2.java. -->
<@compress_single_line>(sqRound(<@printQQEValue1At block "1" />, 6) > sqRound(<@printQQEValue2At block "1" />, 6) && sqRound(<@printQQEValue1At block "0" />, 6) < sqRound(<@printQQEValue2At block "0" />, 6))</@compress_single_line>