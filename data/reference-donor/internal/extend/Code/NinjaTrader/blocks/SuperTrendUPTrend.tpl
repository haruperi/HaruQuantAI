<#-- SuperTrend is in an up-trend (line rising: value[0] > value[1]). Inline over printSuperTrendValueAt.
     Matches EasyLanguage (ST[0]>ST[1]) / MT5 (sqIsRising).      IGNORES #Mode#: values="Basic=1" - one declared value.
-->
(sqRound(<@printSuperTrendValueAt block "0" />, 6) > sqRound(<@printSuperTrendValueAt block "1" />, 6))
