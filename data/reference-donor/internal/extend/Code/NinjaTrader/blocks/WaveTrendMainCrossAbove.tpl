<#-- WaveTrend main line crosses above #Level#. -->
(sqRound(<@printWaveTrendValueAt block "MAIN" "1" />, 6) < <@printParam block "#Level#" /> && sqRound(<@printWaveTrendValueAt block "MAIN" "0" />, 6) > <@printParam block "#Level#" />)
