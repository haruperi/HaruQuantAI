<#-- Smoothed Moving Average (Wilder) from the installed SqSMMA indicator (AverageCalculator SMMA,
     seeded on bar 1). Mirrors SMMA.java.
     Output e.g.: SqSMMA(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqSMMA(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
