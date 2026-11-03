<#-- DarkCloud (candle pattern) from the installed SqCandlePattern indicator (Values[4], 1 where found):
     bearish reversal, mirror of piercing line. SqPip is the StrategyQuant pip the thresholds use. See DarkCloud.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[4][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[4]</@printSeriesAt> > 0.5)
