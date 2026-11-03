<#-- MaxDistanceFromMarket: applied at order placement, not per bar - EnterAtStop.tpl /
     EnterAtLimit.tpl gate the pending entry with sqMaxDistanceOk (declared next to the option
     fields in MaxDistanceFromMarket_variables.tpl), mirroring the MT5 SQ.mqh pending-order gate. -->
			// MaxDistanceFromMarket: applied at pending-entry placement via sqMaxDistanceOk (see the Enter*Stop/Limit gates).
