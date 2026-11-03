<#-- BullishEngulfing (candle pattern) from the installed SqCandlePattern indicator (Values[0], 1 where found):
     bullish body engulfing the previous bearish one; pure OHLC over the current and previous bar. SqPip is the StrategyQuant pip the thresholds use. See BullishEngulfing.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[0][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[0]</@printSeriesAt> > 0.5)
