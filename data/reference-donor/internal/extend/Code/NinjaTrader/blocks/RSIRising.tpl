<#-- RSI is rising (value[1] < value[0]). Inline over printRSIValueAt. Matches JForex (same pattern as OSMARising). -->
(sqRound(<@printRSIValueAt block "1" />, 6) < sqRound(<@printRSIValueAt block "0" />, 6))
