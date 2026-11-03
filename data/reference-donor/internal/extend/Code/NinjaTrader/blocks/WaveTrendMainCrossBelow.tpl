<#-- WaveTrend main line crosses below #Level#. -->
(sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) > <@printParam block "#Level#" /> && sqRound(<@printWaveTrendValueAt block "MAIN" "0" />, 6) < <@printParam block "#Level#" />)
