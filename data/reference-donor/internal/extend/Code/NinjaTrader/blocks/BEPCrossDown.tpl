<#-- BearsPower crosses below #Level# (value[1] > Level && value[0] < Level). -->
((sqRound(<@printBullsBearsValueAt block "Low" "1" />, 6) > <@printParam block "#Level#" />) && (sqRound(<@printBullsBearsValueAt block "Low" "0" />, 6) < <@printParam block "#Level#" />))
