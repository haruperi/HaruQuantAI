<#-- Bars since the current position was entered (-1 if none). Order identification ignored
     (NT Managed). Mirrors BarsSinceOrderOpen.java.      #Direction# is honoured.
-->
(sqPositionMatches(<@printParam block "#Direction#" "0" />) ? ${barsSinceEntryCall()} : -1)
