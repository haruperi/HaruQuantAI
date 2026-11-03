<#-- Bars since the last position was exited (-1 if none). Order identification ignored
     (NT Managed). Mirrors BarsSinceOrderClosed.java.      #Direction# is honoured via sqBarsSinceOrderClosed - it filters on the
     last CLOSED trade, since after an exit the position is flat.
-->
sqBarsSinceOrderClosed(<@printParam block "#Direction#" "0" />)
