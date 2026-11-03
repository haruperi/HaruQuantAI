<#-- BullsPower crosses above #Level# (value[1] < Level && value[0] > Level). -->
((sqRound(<@printBullsBearsValueAt block "High" "1" />, 6) < <@printParam block "#Level#" />) && (sqRound(<@printBullsBearsValueAt block "High" "0" />, 6) > <@printParam block "#Level#" />))
