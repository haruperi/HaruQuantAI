<#-- Exit on Friday -> close positions on Friday at/after FridayExitTime and block entries Friday-after-time
     and Saturday. Mirrors EasyLanguage ExitOnFriday_code. Time as HHMM (sqClock(Time[0]).Hour*100 + Minute, a bar ending at midnight on its own day). -->
			if (ExitOnFriday)
			{
				int t = sqClock(Time[0]).Hour * 100 + sqClock(Time[0]).Minute;
				if (sqClock(Time[0]).DayOfWeek == DayOfWeek.Friday && FridayExitTime != 0 && t >= FridayExitTime)
				{
					if (Position.MarketPosition == MarketPosition.Long) ExitLong();
					if (Position.MarketPosition == MarketPosition.Short) ExitShort();
					openingOrdersAllowed = false;
				}
				else if (sqClock(Time[0]).DayOfWeek == DayOfWeek.Saturday)
				{
					openingOrdersAllowed = false;
				}
			}
