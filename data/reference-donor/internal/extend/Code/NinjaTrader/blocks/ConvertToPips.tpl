<#-- Convert a price distance to pips. SQX convertRealPriceToPips = SQUtils.round(value / tickSize, 2),
     and SQX "pip" IS the instrument tickSize (see StrategyBase + ChartServlet) - which is SqPip,
     NOT NinjaScript TickSize (= SQX tickStep, 10x smaller on odd-decimal forex).
     Rounded with sqRound, the exact mirror of SQUtils.round (half-up, same 1e-10 nudge), not with
     Math.Round: C#'s default is banker's, and MidpointRounding.AwayFromZero only matches half-up
     for POSITIVE values. A price distance is routinely negative
     (ConvertToPips(Close - Open)), and there the two disagree at a midpoint: -1.255 pips is -1.25 in
     StrategyQuant and -1.26 away-from-zero. #Symbol# is ignored (primary instrument). -->
sqRound(<@printBlockChild block "#Value#" shift /> / SqPip, 2)
