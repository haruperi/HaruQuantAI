<#-- ClosedPLInPips -> P/L of the TradesAgo-th most recent closed trade in SQX pips (0 = last),
     filtered by direction; 0 when no such trade. Order identification is ignored (NT Managed).      #Direction# is showIfDefault=false with defaultValue="0", so StrategyQuant OMITS it from the
     XML at its default. printParam would then emit NOTHING and the helper call would lose an
     argument (CS7036), so the default is supplied here.
-->
sqClosedPLInPips(<@printParam block "#Direction#" "0" />, <@printParam block "#TradesAgo#" "0" />)
