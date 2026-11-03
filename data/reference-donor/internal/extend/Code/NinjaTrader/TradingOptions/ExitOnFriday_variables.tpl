<#-- ExitOnFriday: close all positions on Friday at the exit time and block new entries over the weekend. -->
		private bool ExitOnFriday = <@printTradingOptionBoolValue "ExitOnFriday" "ExitOnFriday" />;
		private int FridayExitTime = <@printTradingOptionTimeValue "ExitOnFriday" "FridayExitTime" />;
