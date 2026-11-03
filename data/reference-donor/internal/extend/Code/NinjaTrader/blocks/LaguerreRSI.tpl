<#-- Laguerre RSI from the installed SqLaguerreRSI indicator: four chained Laguerre filters of Close with
     decay #Gamma#, then CU / (CU + CD). See printLaguerreRSIValueAt (Parameters.inc).
     Output e.g.: SqLaguerreRSI(Close, 0.5).Values[0][0] -->
<@printLaguerreRSIValueAt block shift />
