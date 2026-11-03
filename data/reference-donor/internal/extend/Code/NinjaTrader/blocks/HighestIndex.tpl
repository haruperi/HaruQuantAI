<#-- Bars-ago index of the highest value over #Period# bars from the installed SqHighestIndex
     indicator, as HighestIndex.java / HighestCalculator return it (the bar shift of the max within the
     window; MAX() would return the value). The cast keeps the integer the block returns.
     Output e.g.: ((int)SqHighestIndex(Close, 14).Values[0][0]) -->
<#global sqUsesIndicatorPackage = true>((int)<@printSeriesAt block shift>SqHighestIndex(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>)
