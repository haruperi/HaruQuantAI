<#-- WaveTrend main line crosses below the signal line. -->
(sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) > sqRound(<@printWaveTrendValueAt block "SIGNAL" "1" />, 6) && sqRound(<@printWaveTrendValueAt block "MAIN" "0" />, 6) < sqRound(<@printWaveTrendValueAt block "SIGNAL" "0" />, 6))
