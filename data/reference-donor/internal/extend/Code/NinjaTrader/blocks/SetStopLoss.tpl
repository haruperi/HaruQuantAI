<#-- SetStopLoss (standalone "Move SL") -> update the open position's stop loss.
     In NinjaScript (Managed Approach) moving the stop = re-calling SetStopLoss for the
     entry signal inside OnBarUpdate; NinjaScript updates the existing stop and places it
     on the correct side of the position itself (no sign handling).
     The SQX RangeLevel formula is mapped to a CalculationMode by printMoveSLPT
     (RANGE/FixedValue/ATR -> Ticks from entry, PriceLevel -> Price).
     The SL parameter is the direct #StopLoss# key when present, else the nested
     #StopLoss.StopLoss# (matches JForex; resolved via childWithKeyExists).
     Docs: https://ninjatrader.com/support/helpguides/nt8/setstoploss.htm -->
<#if childWithKeyExists(block, "#StopLoss#")><@printMoveSLPT block "SL" "#StopLoss#" /><#else><@printMoveSLPT block "SL" "#StopLoss.StopLoss#" /></#if>