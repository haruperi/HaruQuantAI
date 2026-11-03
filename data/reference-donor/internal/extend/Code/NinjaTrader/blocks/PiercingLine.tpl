<#-- PiercingLine (candle pattern) from the installed SqCandlePattern indicator (Values[3], 1 where found):
     bullish reversal, body ratio > 0.5, range >= 10 pips. SqPip is the StrategyQuant pip the thresholds use. See PiercingLine.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[3][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[3]</@printSeriesAt> > 0.5)
