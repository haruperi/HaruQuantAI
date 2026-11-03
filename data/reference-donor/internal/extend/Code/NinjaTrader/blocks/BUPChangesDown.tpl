<#-- BullsPower changes direction down = local maximum (value[2] < value[1] && value[1] > value[0]). -->
((sqRound(<@printBullsBearsValueAt block "High" "2" />, 6) < sqRound(<@printBullsBearsValueAt block "High" "1" />, 6)) && (sqRound(<@printBullsBearsValueAt block "High" "1" />, 6) > sqRound(<@printBullsBearsValueAt block "High" "0" />, 6)))
