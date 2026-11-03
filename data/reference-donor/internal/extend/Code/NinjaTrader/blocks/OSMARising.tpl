<#-- OSMA is rising (value[1] < value[0]). Inline over printOSMAValueAt (composite value; cannot
     reuse generic printIndRising). Matches JForex/EasyLanguage OSMARising. -->
(sqRound(<@printOSMAValueAt block "1" />, 6) < sqRound(<@printOSMAValueAt block "0" />, 6))
