<#-- Max trades per day -> block entries once today's trade count reaches the limit. Mirrors EasyLanguage
     MaxTradesPerDay_code (sqTradesToday counts today's entries + the open position). -->
			if (MaxTradesPerDay != 0 && sqTradesToday() >= MaxTradesPerDay)
				openingOrdersAllowed = false;
