<#-- WaveTrend main line changes direction downwards (local max). -->
(sqRound(<@printWaveTrendValueAt block "MAIN" "2" />, 6) < sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) && sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) > sqRound(<@printWaveTrendValueAt block "MAIN" "0" />, 6))
