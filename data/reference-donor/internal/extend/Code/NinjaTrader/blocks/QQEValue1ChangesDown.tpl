<#-- QQE Value1 changes direction down (local maximum): v[s+2] < v[s+1] && v[s+1] > v[s].
     Parity with QQEValue1ChangesDown.java. -->
<@compress_single_line>(sqRound(<@printQQEValue1At block "2" />, 6) < sqRound(<@printQQEValue1At block "1" />, 6) && sqRound(<@printQQEValue1At block "1" />, 6) > sqRound(<@printQQEValue1At block "0" />, 6))</@compress_single_line>