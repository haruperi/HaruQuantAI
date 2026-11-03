<#-- PendingOrderDoesntExist -> negation of PendingOrderExists (the Java loop returns true when
     no matching live pending entry order is found). Symbol/Magic/Comment identification degenerates to "this strategy's orders", as in PendingOrderExists.      #Direction# is showIfDefault=false with defaultValue="0", so StrategyQuant OMITS it from the
     XML at its default. printParam then emits NOTHING and the helper call loses an argument,
     which does not compile (CS7036). The default is supplied here.
-->
(!sqPendingOrderExists(<@printParam block "#Direction#" "0" />))
