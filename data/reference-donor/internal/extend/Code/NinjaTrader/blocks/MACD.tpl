<#-- MACD value from the installed SqMACD indicator: #Line# 0 selects the main line (EMA fast - EMA slow),
     1 the signal line (the simple moving average of the main line, as MACD.java computes it) and 2 the
     histogram (main - signal). Mapping in printMACDLine (Parameters.inc).
     Output e.g.: SqMACD(Close, 12, 26, 9).Values[0][0] -->
<@printMACDLine block shift />
