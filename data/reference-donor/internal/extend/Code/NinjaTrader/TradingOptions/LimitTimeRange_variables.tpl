<#-- LimitTimeRange: allow entries only within [From, To); optionally close at range end. -->
		private bool LimitSignalsTimeRange = <@printTradingOptionBoolValue "LimitTimeRange" "LimitTimeRange" />;
		private int SignalTimeRangeFrom = <@printTradingOptionTimeValue "LimitTimeRange" "SignalTimeRangeFrom" />;
		private int SignalTimeRangeTo = <@printTradingOptionTimeValue "LimitTimeRange" "SignalTimeRangeTo" />;
		private bool ExitAtEndOfRange = <@printTradingOptionBoolValue "LimitTimeRange" "ExitAtEndOfRange" />;
<#-- What to close at the range end: 0 = All, 1 = Live only, 2 = Pending only. -->
		private int OrderTypeToExit = <@printTradingOptionIntValue "LimitTimeRange" "OrderTypeToExit" />;
