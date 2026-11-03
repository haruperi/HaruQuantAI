<#-- Don't trade on weekends -> block entries (gate). Mirrors EasyLanguage DontTradeOnWeekends_code:
     Friday after FridayCloseTime, all Saturday, Sunday before SundayOpenTime. DayOfWeek 0=Sun..6=Sat,
     time as HHMM of the bar time read through sqClock (a bar ending at midnight belongs to its own day). -->
			if (DontTradeOnWeekends)
			{
				int dow = (int)sqClock(Time[0]).DayOfWeek;
				int t = sqClock(Time[0]).Hour * 100 + sqClock(Time[0]).Minute;
				if (dow == 5 && FridayCloseTime != 0 && t >= FridayCloseTime) openingOrdersAllowed = false;
				else if (dow == 6) openingOrdersAllowed = false;
				else if (dow == 0 && t < SundayOpenTime) openingOrdersAllowed = false;
			}
