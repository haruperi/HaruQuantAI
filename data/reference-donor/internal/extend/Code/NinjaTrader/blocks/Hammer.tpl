<#-- Hammer (candle pattern) from the installed SqCandlePattern indicator (Values[5], 1 where found):
     long lower wick, small body, at a 3-bar low (4-bar lookback). SqPip is the StrategyQuant pip the thresholds use. See Hammer.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[5][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[5]</@printSeriesAt> > 0.5)
