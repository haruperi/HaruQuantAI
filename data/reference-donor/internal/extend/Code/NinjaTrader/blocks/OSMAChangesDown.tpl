<#-- OSMA changes direction down = local maximum (value[2] < value[1] && value[1] > value[0]).
     Matches JForex/EasyLanguage OSMAChangesDown (MT5: changesDown). -->
((sqRound(<@printOSMAValueAt block "2" />, 6) < sqRound(<@printOSMAValueAt block "1" />, 6)) && (sqRound(<@printOSMAValueAt block "1" />, 6) > sqRound(<@printOSMAValueAt block "0" />, 6)))
