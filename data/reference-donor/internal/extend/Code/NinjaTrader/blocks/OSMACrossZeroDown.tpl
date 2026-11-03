<#-- OSMA crosses below zero (value[1] > 0 && value[0] < 0). Threshold is 0 (not #Level#).
     Matches JForex/EasyLanguage OSMACrossZeroDown (MT5: crossesDown(..., 0)). -->
((sqRound(<@printOSMAValueAt block "1" />, 6) > 0) && (sqRound(<@printOSMAValueAt block "0" />, 6) < 0))
