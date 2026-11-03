<#-- ExitAtEndOfDay: close all positions at the end-of-day exit time and block new entries afterwards. -->
		private bool ExitAtEndOfDay = <@printTradingOptionBoolValue "ExitAtEndOfDay" "ExitAtEndOfDay" />;
		private int DayExitTime = <@printTradingOptionTimeValue "ExitAtEndOfDay" "EODExitTime" />;
		// The day of the last bar, whether one of its bars reached DayExitTime, and whether a position was
		// held at the last bar's close.
		private DateTime sqEodDay = DateTime.MinValue;
		private bool sqEodReached = false;
		private bool sqEodHeld = false;
