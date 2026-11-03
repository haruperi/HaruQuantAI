<#-- Linear Weighted Moving Average from the installed SqLWMA indicator (AverageCalculator LWMA).
     Mirrors LWMA.java, warm-up included.
     Output e.g.: SqLWMA(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqLWMA(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
