<#-- MinMaxSLPT: applied at SL/PT placement, not per bar - printSetSLPT wraps every
     CalculationMode.Ticks distance in sqClampSLPT (declared next to the option fields in
     MinMaxSLPT_variables.tpl), mirroring where MT5 SQ.mqh clamps the order's SL/PT price.
     Percent/Price SL/PT modes are not clamped (there is no pre-entry fill price to measure the
     pip distance from) - the placement site emits an explanatory comment for those modes. -->
