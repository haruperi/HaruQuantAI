<#-- OpenPLInPips -> open P/L of the position in SQX pips (price distance / SqPip, size-independent
     like ILiveOrder.getPLInPips). Direction filter Long=1/Short=-1/Any=0; the Symbol/Magic/Comment
     identification degenerates to "my position" (NT Managed single position).      #Direction# is showIfDefault=false with defaultValue="0", so StrategyQuant OMITS it from the
     XML at its default. printParam then emits NOTHING and the helper call loses an argument,
     which does not compile (CS7036). The default is supplied here.
-->
sqOpenPLInPips(<@printParam block "#Direction#" "0" />)
