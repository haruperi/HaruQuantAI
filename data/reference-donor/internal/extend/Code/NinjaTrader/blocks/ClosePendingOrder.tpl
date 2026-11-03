<#-- ClosePendingOrder -> close ONE matching pending entry, the long side first when both match
     (ClosePendingOrder.java closes one order). The helper drops the queued entry and marks an earlier
     bar's one closed; see sqClosePendingEntry (SQ.inc) for why it issues no CancelOrder.
     Direction Long=1/Short=-1/Any=0; Symbol/Magic/Comment identification degenerates in the
     single-strategy export. -->
sqClosePendingOrder(<@printParam block "#Direction#" />);
