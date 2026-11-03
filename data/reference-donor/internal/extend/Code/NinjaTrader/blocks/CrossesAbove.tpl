<#-- Crosses-above: Left was below Right on the previous bar [1] and is above on
     the current bar [0]. Emitted as an explicit C# expression for precise bar
     control; equivalent to native NT CrossAbove(series1, series2, lookback).
     Docs (native CrossAbove): find via alphabetical reference
     https://ninjatrader.com/support/helpguides/nt8/alphabetical_reference.htm
     Output e.g.:
     ((SMA(Close,10)[1] < SMA(Close,20)[1]) && (SMA(Close,10)[0] > SMA(Close,20)[0])) -->
((<@printCmpOperand block "#Left#" "1" "6" /> < <@printCmpOperand block "#Right#" "1" "6" />) && (<@printCmpOperand block "#Left#" "0" "6" /> > <@printCmpOperand block "#Right#" "0" "6" />))