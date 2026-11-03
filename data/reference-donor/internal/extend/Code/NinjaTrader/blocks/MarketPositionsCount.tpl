<#-- Number of open positions -> 0 (flat) or 1 (open). NinjaScript Managed Approach has a single
     aggregated position per instrument, so the count is 0/1 (not N). Symbol filters ignored;
     full multi-position parity needs the Account API.      #Direction# is honoured on every block of this family. MagicNumber/Comment cannot be
     honoured (NT Managed keeps a single position), but the direction of that position can.
-->
(sqPositionMatches(<@printParam block "#Direction#" "0" />) ? 1 : 0)
