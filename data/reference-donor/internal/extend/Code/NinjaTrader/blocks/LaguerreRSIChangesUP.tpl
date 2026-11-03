<#-- LaguerreRSI changes direction up = local minimum (value[0] > value[1] && value[2] > value[1]).
     Matches EasyLanguage/MT5 LaguerreRSIChangesUP. -->
((sqRound(<@printLaguerreRSIValueAt block "0" />, 6) > sqRound(<@printLaguerreRSIValueAt block "1" />, 6)) && (sqRound(<@printLaguerreRSIValueAt block "2" />, 6) > sqRound(<@printLaguerreRSIValueAt block "1" />, 6)))
