<#-- Exit at end of day -> close positions at/after DayExitTime and block entries afterwards. Mirrors
     EasyLanguage ExitAtEndOfDay_code (non-LimitTimeRange path). DayExitTime=0 -> handled by the default
     IsExitOnSessionCloseStrategy. The LimitTimeRange combination is not replicated. -->
			if (ExitAtEndOfDay && DayExitTime != 0)
			{
<#-- The first bar of a new day closes a position the previous day left open because none of its
     bars reached the exit time (an early close), as StrategyQuant's ExitAtEndOfDay does. Only a
     position already held at the previous bar's close: one filled at this bar's open belongs to
     the new day. -->
				// A new day closes a position the previous day left open (an early close), as ExitAtEndOfDay.
				if (sqClock(Time[0]).Date != sqEodDay)
				{
					if (sqEodDay != DateTime.MinValue && !sqEodReached && sqEodHeld)
					{
						if (Position.MarketPosition == MarketPosition.Long) ExitLong();
						if (Position.MarketPosition == MarketPosition.Short) ExitShort();
					}
					sqEodDay = sqClock(Time[0]).Date;
					sqEodReached = false;
				}
				int t = sqClock(Time[0]).Hour * 100 + sqClock(Time[0]).Minute;
				if (t >= DayExitTime)
				{
					if (Position.MarketPosition == MarketPosition.Long) ExitLong();
					if (Position.MarketPosition == MarketPosition.Short) ExitShort();
					openingOrdersAllowed = false;
					sqEodReached = true;
				}
				sqEodHeld = Position.MarketPosition != MarketPosition.Flat;
			}
