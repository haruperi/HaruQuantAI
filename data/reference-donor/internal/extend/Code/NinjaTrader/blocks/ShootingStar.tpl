<#-- ShootingStar (candle pattern) from the installed SqCandlePattern indicator (Values[6], 1 where found):
     long upper wick, small body, at a 3-bar high (4-bar lookback). SqPip is the StrategyQuant pip the thresholds use. See ShootingStar.java.
     Output e.g.: (SqCandlePattern(Close, SqPip).Values[6][0] > 0.5) -->
<#global sqUsesIndicatorPackage = true>(<@printSeriesAt block shift>SqCandlePattern(<@printInput block />, SqPip).Values[6]</@printSeriesAt> > 0.5)
