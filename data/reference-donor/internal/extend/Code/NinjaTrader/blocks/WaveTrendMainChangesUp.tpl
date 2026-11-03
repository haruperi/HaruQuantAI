<#-- WaveTrend main line changes direction upwards (local min). -->
(sqRound(<@printWaveTrendValueAt block "MAIN" "2" />, 6) > sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) && sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) < sqRound(<@printWaveTrendValueAt block "MAIN" "0" />, 6))
