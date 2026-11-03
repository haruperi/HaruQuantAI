<#-- Doji (candle pattern) from the installed SqCandlePattern indicator (Values[2], 1 where found):
     body < 0.6 pip, rounded to the instrument decimals. SqPip is the StrategyQuant pip the thresholds use. See Doji.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[2][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[2]</@printSeriesAt> > 0.5)
