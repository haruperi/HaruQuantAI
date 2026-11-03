<#-- Bearish fractal -> an up (high) pivot exists, line 0 > 0. Mirrors IsBearishFractal.java. -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block "0">SqFractal(<@printInput block />, <@printParam block "#Fractal#" />).Values[0]</@printSeriesAt> > 0)
