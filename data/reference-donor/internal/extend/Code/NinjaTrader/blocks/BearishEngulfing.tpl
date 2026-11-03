<#-- BearishEngulfing (candle pattern) from the installed SqCandlePattern indicator (Values[1], 1 where found):
     bearish body engulfing the previous bullish one; pure OHLC over the current and previous bar. SqPip is the StrategyQuant pip the thresholds use. See BearishEngulfing.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[1][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[1]</@printSeriesAt> > 0.5)
