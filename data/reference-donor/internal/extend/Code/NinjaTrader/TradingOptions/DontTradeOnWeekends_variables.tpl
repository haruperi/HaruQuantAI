<#-- DontTradeOnWeekends: block entries after Friday close time, all Saturday, before Sunday open. -->
		private bool DontTradeOnWeekends = <@printTradingOptionBoolValue "DontTradeOnWeekends" "DontTradeOnWeekends" />;
		private int FridayCloseTime = <@printTradingOptionTimeValue "DontTradeOnWeekends" "FridayCloseTime" />;
		private int SundayOpenTime = <@printTradingOptionTimeValue "DontTradeOnWeekends" "SundayOpenTime" />;
