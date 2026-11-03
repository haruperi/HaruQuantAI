<#-- SetProfitTarget (standalone "Move PT") -> update the open position's profit target.
     Same NinjaScript Managed approach as SetStopLoss: re-calling SetProfitTarget for the
     entry signal in OnBarUpdate updates the existing target; NinjaScript handles the side.
     The SQX RangeLevel formula is mapped to a CalculationMode by printMoveSLPT
     (RANGE/FixedValue/ATR -> Ticks from entry, PriceLevel -> Price).
     The PT parameter is the direct #ProfitTarget# key when present, else the nested
     #ProfitTarget.ProfitTarget# (matches JForex; resolved via childWithKeyExists).
     Docs: https://ninjatrader.com/support/helpguides/nt8/setprofittarget.htm -->
<#if childWithKeyExists(block, "#ProfitTarget#")><@printMoveSLPT block "PT" "#ProfitTarget#" /><#else><@printMoveSLPT block "PT" "#ProfitTarget.ProfitTarget#" /></#if>