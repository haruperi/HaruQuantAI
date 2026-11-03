<#-- Heiken Ashi value from the installed SqHeikenAshi indicator. #Line# selects the output:
     0=HAOpen, 1=HAClose. NinjaTrader has no native Heiken Ashi.
     Output e.g.: SqHeikenAshi(Close).Values[1][0] -->
<#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqHeikenAshi(<@printInput block />).Values[<@printParam block "#Line#" />]</@printSeriesAt></@compress_single_line>
