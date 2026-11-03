<#-- Market position size (contracts) -> Position.Quantity. NinjaScript Managed Approach has a single
     aggregated position per instrument, so #Symbol#/#MagicNumber# filters are ignored
     (same limitation as the order blocks). Full multi-position parity needs the Account API.      #Direction# is honoured.
-->
(sqPositionMatches(<@printParam block "#Direction#" "0" />) ? Position.Quantity : 0)
