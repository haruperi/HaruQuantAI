<#-- SuperTrend holds the same value (in range: value[0] == value[1]). The "hold the band" branch copies
     the previous value exactly, so '==' on doubles is a bit-for-bit match here. Inline over
     printSuperTrendValueAt. Matches EasyLanguage (ST[0]=ST[1]) / MT5 (value[0]==value[1]).      IGNORES #Mode#: values="Basic=1" - one declared value.
-->
(sqRound(<@printSuperTrendValueAt block "0" />, 6) == sqRound(<@printSuperTrendValueAt block "1" />, 6))
