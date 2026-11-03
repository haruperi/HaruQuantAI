<#-- Convert pips to a real price distance = value * SqPip (inverse of ConvertToPips). SQX pip =
     InstrumentInfo.tickSize, carried by SqPip (NOT NinjaScript TickSize).
     #Symbol# ignored (primary instrument). Mirrors ConvertToRealPips.java. -->
(<@printBlockChild block "#Value#" shift /> * SqPip)
