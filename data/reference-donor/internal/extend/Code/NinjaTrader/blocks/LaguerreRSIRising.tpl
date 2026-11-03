<#-- LaguerreRSI is rising (value[0] > value[1]). Inline over printLaguerreRSIValueAt.
     Matches EasyLanguage/MT5 LaguerreRSIRising. -->
(sqRound(<@printLaguerreRSIValueAt block "0" />, 6) > sqRound(<@printLaguerreRSIValueAt block "1" />, 6))
