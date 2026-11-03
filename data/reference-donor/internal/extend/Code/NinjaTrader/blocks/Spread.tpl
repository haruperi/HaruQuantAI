<#-- Spread -> |Ask - Bid| via NinjaScript GetCurrentAsk/Bid. Parity with Spread.java (|Ask() - Bid()|).
     NOTE: in historical backtest both return the bar Close, so spread approx 0 - documented caveat. -->
<@compress_single_line>Math.Abs(GetCurrentAsk(0) - GetCurrentBid(0))</@compress_single_line>