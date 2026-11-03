<#-- Session delta below -#MinDelta#. -->
<#global sqUsesIndicatorPackage = true>(sqRound(<@printSeriesAt block "0">SqVolumeProfile(<@printInput block />, <@printParam block "#SessionType#" />, <@printParam block "#ProfileRows#" />, 2, 3, <@printParam block "#ValueAreaPct#" />, 0).Values[10]</@printSeriesAt>, 6) < -(<@printParam block "#MinDelta#" />))
