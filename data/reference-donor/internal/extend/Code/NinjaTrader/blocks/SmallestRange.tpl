<#-- Smallest bar range (High-Low) over #Period# bars from the installed SqSmallestRange indicator:
     rolling min of round(High-Low, 8), as SmallestRange.java computes it.
     Output e.g.: SqSmallestRange(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqSmallestRange(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
