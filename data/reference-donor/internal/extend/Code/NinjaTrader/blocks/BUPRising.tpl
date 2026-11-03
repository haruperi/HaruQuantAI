<#-- BullsPower is rising (value[1] < value[0]). Inline over printBullsBearsValueAt (price="High"). -->
(sqRound(<@printBullsBearsValueAt block "High" "1" />, 6) < sqRound(<@printBullsBearsValueAt block "High" "0" />, 6))
