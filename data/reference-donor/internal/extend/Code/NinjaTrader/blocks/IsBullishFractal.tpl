<#-- Bullish fractal -> a down (low) pivot exists, line 1 > 0. Mirrors IsBullishFractal.java. -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block "0">SqFractal(<@printInput block />, <@printParam block "#Fractal#" />).Values[1]</@printSeriesAt> > 0)
