<#-- LastOrderWasNot -> the last closed trade exists AND has the OPPOSITE direction. The Java loop
     returns false when no order exists, so the comparison is == -Direction (0 never matches). -->
(sqLastOrderType() == -(<@printParam block "#Direction#" />))
