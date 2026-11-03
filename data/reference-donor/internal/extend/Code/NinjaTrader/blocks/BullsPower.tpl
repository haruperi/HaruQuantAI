<#-- Bulls Power -> High[shift] - EMA(price, period)[shift].
     SQX BullsPower.java: Input.High[0] - EMA(ComputedFrom, Period). The price term is always
     the bar High (independent of #ComputedFrom#, which selects only the EMA source). NT has
     native EMA(input, period), so this maps natively (no SQIndicators.inc).
     See printBullsBearsValueAt (Parameters.inc).
     Output e.g.: (High[0] - EMA(Close, 14)[0]) -->
<@printBullsBearsValueAt block "High" shift />
