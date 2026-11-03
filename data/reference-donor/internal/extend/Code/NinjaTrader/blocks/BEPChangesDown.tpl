<#-- BearsPower changes direction down = local maximum (value[2] < value[1] && value[1] > value[0]). -->
((sqRound(<@printBullsBearsValueAt block "Low" "2" />, 6) < sqRound(<@printBullsBearsValueAt block "Low" "1" />, 6)) && (sqRound(<@printBullsBearsValueAt block "Low" "1" />, 6) > sqRound(<@printBullsBearsValueAt block "Low" "0" />, 6)))
