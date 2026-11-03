<#-- Average True Range from the installed SqATR indicator, NOT the native NinjaScript ATR().
     ATR.java seeds bar 0 with High-Low and divides by min(CurrentBar+1, period) over the warm-up.
     The 6-decimal rounding SQX applies is added where the ATR feeds an SL/PT or range distance
     (sqAtrTicks, printRangeLevelPrice).
     ATR.java declares only Chart and Period - there is no #ComputedFrom#; printInput only binds the
     indicator to the block's chart.
     Output e.g.: SqATR(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqATR(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
