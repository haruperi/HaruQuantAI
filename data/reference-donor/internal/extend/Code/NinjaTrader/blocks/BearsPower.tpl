<#-- Bears Power -> Low[shift] - EMA(price, period)[shift].
     SQX BearsPower.java: Input.Low[0] - EMA(ComputedFrom, Period). The price term is always
     the bar Low (independent of #ComputedFrom#, which selects only the EMA source). NT has
     native EMA(input, period), so this maps natively (no SQIndicators.inc).
     @OppositeBlock of BullsPower (High vs Low). See printBullsBearsValueAt (Parameters.inc).
     Output e.g.: (Low[0] - EMA(Close, 14)[0]) -->
<@printBullsBearsValueAt block "Low" shift />
