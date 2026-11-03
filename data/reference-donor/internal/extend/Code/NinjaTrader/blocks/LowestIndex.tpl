<#-- Bars-ago index of the lowest value over #Period# bars from the installed SqLowestIndex
     indicator, as LowestIndex.java / LowestCalculator return it (the bar shift of the min within the
     window; MIN() would return the value). The cast keeps the integer the block returns.
     Output e.g.: ((int)SqLowestIndex(Close, 14).Values[0][0]) -->
<#global sqUsesIndicatorPackage = true>((int)<@printSeriesAt block shift>SqLowestIndex(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>)
