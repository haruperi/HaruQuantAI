<#-- SuperTrend from the installed SqSuperTrend indicator; NinjaTrader has no native Managed
     SuperTrend. Stateful band machine (mid +/- ATRMult*ATR) flipping on Close vs the previous value,
     ATR = the simple-mean MetaTrader ATR rounded to 6 decimals, as SuperTrend.java's MetaTrader branch
     reads it. IGNORES #Mode#: SuperTrend.java declares values="Basic=1" - one value, nothing to branch on.
     See printSuperTrendValueAt (Parameters.inc).
     Output e.g.: SqSuperTrend(Close, 24, 3).Values[0][0] -->
sqRound(<@printSuperTrendValueAt block shift />, 6)
