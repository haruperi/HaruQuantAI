<#-- Open P/L of the current position (order identification ignored - NT Managed single
     position). Mirrors OpenPLInMoney.java.      #Direction# is honoured on every block of this family. MagicNumber/Comment cannot be
     honoured (NT Managed keeps a single position), but the direction of that position can.
-->
(sqPositionMatches(<@printParam block "#Direction#" "0" />) ? Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]) : 0)
