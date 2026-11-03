<#-- CloseAllPendingOrders -> close ALL matching pending entries (CloseAllPendingOrders.java), through
     the same sqClosePendingEntry as ClosePendingOrder.
     Direction Long=1/Short=-1/Any=0; Symbol/Magic/Comment identification degenerates in the
     single-strategy export.      #Direction# is showIfDefault=false with defaultValue="0", so StrategyQuant OMITS it from the
     XML at its default. printParam would then emit NOTHING and the helper call would lose an
     argument (CS7036), so the default is supplied here.
-->
sqCloseAllPendingOrders(<@printParam block "#Direction#" "0" />);
