<#-- LaguerreRSI changes direction down = local maximum (value[0] < value[1] && value[2] < value[1]).
     Matches EasyLanguage/MT5 LaguerreRSIChangesDown. -->
((sqRound(<@printLaguerreRSIValueAt block "0" />, 6) < sqRound(<@printLaguerreRSIValueAt block "1" />, 6)) && (sqRound(<@printLaguerreRSIValueAt block "2" />, 6) < sqRound(<@printLaguerreRSIValueAt block "1" />, 6)))
