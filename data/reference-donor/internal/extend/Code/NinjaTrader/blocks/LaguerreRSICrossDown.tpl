<#-- LaguerreRSI crosses below #Level# (value[0] < Level && value[1] > Level). Threshold is #Level#
     (not 0). Matches EasyLanguage/JForex/MT5 LaguerreRSICrossDown. -->
((sqRound(<@printLaguerreRSIValueAt block "0" />, 6) < <@printParam block "#Level#" />) && (sqRound(<@printLaguerreRSIValueAt block "1" />, 6) > <@printParam block "#Level#" />))
