<#-- Biggest bar range (High-Low) over #Period# bars from the installed SqBiggestRange indicator:
     rolling max of round(High-Low, 8), as BiggestRange.java computes it.
     Output e.g.: SqBiggestRange(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqBiggestRange(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
