<#-- OSMA changes direction up = local minimum (value[2] > value[1] && value[1] < value[0]).
     Matches JForex/EasyLanguage OSMAChangesUp (MT5: changesUp). -->
((sqRound(<@printOSMAValueAt block "2" />, 6) > sqRound(<@printOSMAValueAt block "1" />, 6)) && (sqRound(<@printOSMAValueAt block "1" />, 6) < sqRound(<@printOSMAValueAt block "0" />, 6)))
