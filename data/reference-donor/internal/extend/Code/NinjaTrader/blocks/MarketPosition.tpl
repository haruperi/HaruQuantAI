<#-- Market position value -> 1 (long) / -1 (short) / 0 (flat). SQX/EL MarketPosition is the native 1/-1/0;
     NinjaScript Position.MarketPosition is an enum, mapped here to the same integer convention. -->
(Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0))
