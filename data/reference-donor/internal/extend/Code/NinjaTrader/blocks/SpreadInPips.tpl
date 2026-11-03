<#-- Spread in pips = |Ask - Bid| / SqPip. SQX pip = InstrumentInfo.tickSize, carried by SqPip (NOT
     NinjaScript TickSize). In historical backtest Ask~=Bid so spread ~= 0.
     #Symbol# ignored (primary instrument). Mirrors SpreadInPips.java. -->
<#-- Math.Round(..., AwayFromZero) rather than sqRound with ConvertToPips: the argument is wrapped in Math.Abs, so it can never be negative, and for non-negative
     values away-from-zero IS half-up. Exact here, not an approximation. If the Math.Abs ever goes, this
     has to become sqRound(..., 2) - that is the whole reason the guarantee holds. -->
Math.Round(Math.Abs(GetCurrentAsk(0) - GetCurrentBid(0)) / SqPip, 2, MidpointRounding.AwayFromZero)
