<#-- RSI changes direction down = local maximum (value[2] < value[1] && value[1] > value[0]). -->
((sqRound(<@printRSIValueAt block "2" />, 6) < sqRound(<@printRSIValueAt block "1" />, 6)) && (sqRound(<@printRSIValueAt block "1" />, 6) > sqRound(<@printRSIValueAt block "0" />, 6)))
