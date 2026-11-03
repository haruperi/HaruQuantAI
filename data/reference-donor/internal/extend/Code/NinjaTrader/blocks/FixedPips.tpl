<#-- FixedPips -> a fixed pip distance as a real price = Value * SqPip. SQX pip = InstrumentInfo.tickSize
     (NOT NinjaScript TickSize = SQX tickStep); SqPip carries the correct pip distance.
     #Symbol# ignored (primary instrument). Mirrors FixedPips.java (convertPipsToRealPrice). -->
(<@printParam block "#Value#" /> * SqPip)
