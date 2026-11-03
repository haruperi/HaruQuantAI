<#-- Open price of the current position (-1 when flat). Order identification ignored
     (NT Managed single position). Mirrors OrderOpenPrice.java.      #Direction# is honoured on every block of this family. MagicNumber/Comment cannot be
     honoured (NT Managed keeps a single position), but the direction of that position can.
-->
(sqPositionMatches(<@printParam block "#Direction#" "0" />) ? Position.AveragePrice : -1)
