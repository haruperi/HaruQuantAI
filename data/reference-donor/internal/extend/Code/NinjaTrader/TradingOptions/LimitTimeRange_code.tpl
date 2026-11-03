<#-- Limit time range -> block entries outside [From, To) (with wraparound), optionally close at range
     end. Mirrors EasyLanguage LimitTimeRange_code. Time as HHMM of the bar time read through sqClock;
     MarketPosition -> Position.MarketPosition; close -> ExitLong/ExitShort.
     OrderTypeToExit (mirror of MT5 LimitTimeRange_class): what the range end closes -
     0 = All (live position + pending entries), 1 = Live only, 2 = Pending only. Pending entry
     orders are cancelled via sqCloseAllPendingOrders(0) (direction 0 = both). Under Pending only a
     pending that fills on the range-end bar is closed too - it is the pending the range end cancels,
     which having filled carries the close, as SQX does. -->
			if (LimitSignalsTimeRange)
			{
				int t = sqClock(Time[0]).Hour * 100 + sqClock(Time[0]).Minute;
				if ((SignalTimeRangeFrom < SignalTimeRangeTo && (t < SignalTimeRangeFrom || t >= SignalTimeRangeTo))
					|| (SignalTimeRangeFrom >= SignalTimeRangeTo && (t < SignalTimeRangeFrom && t >= SignalTimeRangeTo)))
					openingOrdersAllowed = false;

				if (ExitAtEndOfRange)
				{
					bool sqLtrRangeEnd = (SignalTimeRangeFrom < SignalTimeRangeTo && t >= SignalTimeRangeTo)
						|| (SignalTimeRangeFrom >= SignalTimeRangeTo && t >= SignalTimeRangeTo && t < SignalTimeRangeFrom);
					if (sqLtrRangeEnd)
					{
						if (OrderTypeToExit != 2)   // not "Pending only": close the live position
						{
							if (Position.MarketPosition == MarketPosition.Long) ExitLong();
							if (Position.MarketPosition == MarketPosition.Short) ExitShort();
						}
						if (OrderTypeToExit != 1)   // not "Live only": cancel pending entry orders
							sqCloseAllPendingOrders(0);
<#-- Pending only: a pending entry that filled on the range-end bar is the pending the range end was to
     cancel; SQX closes the resulting position (the cancelled pending, having filled, carries the close), so
     the export closes it too. BarsSinceEntryExecution == 0 scopes it to a fill on this bar; an older live
     position is left, as Pending only means. -->
<#if hasPendingEntryBlock("1") || hasPendingEntryBlock("-1")>
						if (OrderTypeToExit == 2)   // Pending only: close a pending entry that filled on the range-end bar
						{
<#if hasPendingEntryBlock("1")>							if (sqLongPendOrigin && Position.MarketPosition == MarketPosition.Long && ${barsSinceEntryCall()} == 0) ExitLong();
</#if><#if hasPendingEntryBlock("-1")>							if (sqShortPendOrigin && Position.MarketPosition == MarketPosition.Short && ${barsSinceEntryCall()} == 0) ExitShort();
</#if>						}
</#if>
					}
				}
			}
