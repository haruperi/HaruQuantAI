<#-- RSI crosses below #Level# (value[1] > Level && value[0] < Level). -->
((sqRound(<@printRSIValueAt block "1" />, 6) > <@printParam block "#Level#" />) && (sqRound(<@printRSIValueAt block "0" />, 6) < <@printParam block "#Level#" />))
