<#-- Risk fixed % of account via sqMMRiskAccountPct (equity, SL distance, StopLossInPips fallback).
     Both the SL distance (printSLTicks) and the StopLossInPips fallback are passed in real ticks: the
     fallback is in SQX pips, so it is scaled by SqPipFactor to match the helper's
     tick*TickSize money calc. Mirrors RiskFixedPctOfAccount.java. -->
sqMMRiskAccountPct(<@printSLTicks block sqMMPriceRef />, mmRiskPercent, mmDecimals, mmStopLossPips * SqPipFactor, mmLotsIfNoMM, mmMaxLots)