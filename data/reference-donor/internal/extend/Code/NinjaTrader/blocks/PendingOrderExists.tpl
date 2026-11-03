<#-- PendingOrderExists -> any pending ENTRY (queued this bar, or an earlier bar's still working)
     in the given direction (Long=1, Short=-1, Any=0). Symbol/Magic/Comment identification (MT)
     degenerates to "this strategy's orders" in the single-strategy export.
     Mirrors PendingOrderExists.java via the sqPendingOrderExists helper (SQ.inc).      #Direction# is showIfDefault=false with defaultValue="0", so StrategyQuant OMITS it from the
     XML at its default. printParam then emits NOTHING and the helper call loses an argument,
     which does not compile (CS7036). The default is supplied here.
-->
sqPendingOrderExists(<@printParam block "#Direction#" "0" />)
