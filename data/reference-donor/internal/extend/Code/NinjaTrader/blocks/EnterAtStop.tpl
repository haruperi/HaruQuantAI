<#-- EnterAtStop -> pending stop-market entry at a price level (NinjaScript EnterLongStopMarket /
     EnterShortStopMarket). The #Price# formula child renders the stop level. SL/PT are set before the
     entry (applied on fill via the signal name). Parity with EasyLanguage EnterAtStop (Buy/SellShort
     N at <price> stop + initial SL/PT).

     The order is submitted with isLiveUntilCancelled = FALSE - i.e. NinjaScript's default managed
     lifetime, which cancels an unfilled entry at the end of the next bar. The SQX pending dies one
     bar after the last signal bar (each firing bar re-places it, the final placement is cancelled a
     bar later); with isLiveUntilCancelled = true the NT pending would survive for days and fill
     where SQX has no order at all. The default lifetime IS the SQX lifetime. The leading 0 is barsInProgressIndex: entries always go on the primary series,
     even in a multi-timeframe strategy.

     A non-zero #BarsValid# is DELIBERATELY not modelled. The block DOES look like it implements
     expiry - EnterAtMarket.handleBarsValid registers a BarOpen listener that calls checkBarsValid,
     which closes the order as Expired once getBarsInTrade() >= barsValid. But BarCloseSimulator
     increments barsInTrade in exactly one place, addToClosedTrades, i.e. once when the order is
     CLOSED; a live pending order's count is 0 forever, so the condition can never be true. Only the
     stockpicker's StockBroker maintains that counter per bar, and it is also the sole reader of
     getBarsValid(). A BarsValid of 3 backtests identically to BarsValid=0 and no order closes as Expired.
     So the SQX-side expiry is inert for every BarsValid value, and modelling it would diverge
     from the reference - which is what the MT5 export does (sqManageOrderExpirations). Guarded by testBarsValidIsHonouredBySimulator.

     MaxDistanceFromMarket: when the trading option is present, the entry is additionally
     gated by sqMaxDistanceOk (percentage distance of the stop level from Close[0]) - mirror of the
     MT5 SQ.mqh pending-order gate.      #ReplaceExisting# false: while a pending entry of the direction exists the block places nothing - StrategyQuant keeps that order, and NinjaTrader lets it expire at the end of the bar when it is not submitted again, which is when StrategyQuant's expires too.
     IGNORES #BarsValid#: it cannot matter - StrategyQuant's own expiry never fires (see above).
-->
<#-- Not on a bar that already had a market entry. NinjaTrader ignores a pending behind it and
     so does the backtest, but the SL/PT resets below would still run and overwrite the
     stop and target that market entry was just submitted with. Nor, when the direction also has a limit
     entry block, after the bar queued a limit entry for it (printOtherPendingTypeGuard). -->
if (openingOrdersAllowed && !sqMarketEntryThisBar<@printOtherPendingTypeGuard block false /><@printNoDuplicateGuard block /><#if getParam(block, "#ReplaceExisting#", "true") == "false"> && !sqPendingEntryExists(<#if getParam(block, "#Direction#", "1") != "-1">true<#else>false</#if>)</#if><#if tradingOptionUsed("MaxDistanceFromMarket")> && sqMaxDistanceOk(<@printPrice block "#Price#" />)</#if>)
			{
				<#-- DEFERRED SL/PT: a pending fill's SL/PT are NOT pre-Set - SQX creates
				     them at the fill and its simulator only processes them from the NEXT bar, so a
				     fill-attached Set() would exit in the entry bar where SQX cannot. The SL distance
				     is captured HERE, at the placement eval (the order-CREATION frame - SQX's
				     ATRBasedValue caches per Bars(), so stops use the creation-frame ATR); the
				     PT is computed at the arming eval, whose shift-1 frame IS the fill frame.
				     Both are armed one bar after the fill by printPendingSLPTArm. -->
				<@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode != ""><#if getParam(block, "#Direction#", "1") != "-1">sqLongPendSL<#else>sqShortPendSL</#if> = ${pendingSLValue(block)};</#if>
				<#-- Overwrite any Set config a previous trade left under these names BEFORE the entry
				     can fill - NinjaTrader persists them across trades and attaches them at submission
				     (printPreEntrySLPTReset). -->
				<@printPreEntrySLPTReset block />
				<#if getParam(block, "#Direction#", "1") != "-1">sqLongPendOrigin = true;<#else>sqShortPendOrigin = true;</#if>
				<@printSetTrailStop block "#TrailingStop.TrailingStop#" />
				<#-- sqRoundPrice: the pending level must round to the tick the way SQUtils.round does
				     (+1e-10 epsilon, half-tick UP) - the same tie-break as SL/PT levels;
				     otherwise an entry can land a tick apart from SQX.

				     ALREADY-CROSSED level -> market entry: StrategyQuant fills a stop entry whose
				     level the market has already passed AT THE NEXT OPEN (e.g. after a weekend gap);
				     NinjaTrader REJECTS a buy stop below the market / sell stop above it, so the
				     export must fall back to a market order in that case.

				     isLiveUntilCancelled is FALSE: the SQX pending dies one bar after the last signal
				     bar (each firing bar re-places it; the last placement is cancelled one bar later),
				     which is exactly NinjaScript's DEFAULT managed lifetime - a live-until-cancelled
				     NT pending would survive and fill days later where SQX has none. -->
				<#-- The market fallback runs under the F-suffixed signal name with the previous bar's
				     pending PARKED at an untouchable price (amended; it expires unfilled at the end of
				     this bar, exactly when SQX's replaced pending dies): while a same-name pending is
				     still working, NinjaTrader's Managed rules silently swallow BOTH a different-type
				     entry and CancelOrder in the same OnBarUpdate, entering one bar after SQX;
				     see EnterAtLimit.tpl. The F name's SL/PT are declared
				     above; EntryHandling.UniqueEntries makes the F entry acceptable alongside the
				     parked pending. -->
				<#if getParam(block, "#Direction#", "1") != "-1">if (sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5)) <= Close[0])
				{
					<#-- A market entry that fills while an opposite entry order is working
					     gets NO protective orders from the Managed approach - see sqOppositeEntryWorking.
					     Skip rather than open a position that cannot be stopped out. -->
					<#-- StrategyQuant closes this side's earlier pending here (Replaced), fallback or not, so the
					     pending-order helpers stop counting it - see sqLongEntryReplaced (SQ.inc). -->
					sqLongEntryReplaced = true; sqLongPendRef = Close[0]; sqLongPendRefIsOrder = false;
					<@printFallbackLevelSL block "sqLong" />
					if (!sqOppositeEntryWorking(true))
					{
						if (sqLongEntryOrder != null && sqLongEntryOrder.OrderState == OrderState.Working)
						{
							sqLongEntryOrder = EnterLongStopMarket(0, false, <@printSizeMethod block "#Size#" />, sqRoundPrice(Close[0] * 1.5), <@printSignalName block />);
						}
						sqNoteMarketEntry();
						EnterLong(<@printSizeMethod block "#Size#" />, <@printSignalName block "F" />);
					}
				}
				else
				{
					<#-- QUEUED, not submitted here - see sqLongPendQueued. -->
					if (sqPendingSlotFree(true))
					{
						sqLongPendQueued = true;
						sqLongPendIsLimit = false;
						<#-- The level first: the order is sized at it. -->
						sqLongPendLevel = sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5));
						sqLongPendQty = <@printSizeMethod block "#Size#" "sqLongPendLevel" />;
						sqLongPendTakenThisBar = true; sqLongPendRef = sqLongPendLevel; sqLongPendRefIsOrder = true;
					}
				}<#else>if (sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5)) >= Close[0])
				{
					<#-- A market entry that fills while an opposite entry order is working
					     gets NO protective orders from the Managed approach - see sqOppositeEntryWorking.
					     Skip rather than open a position that cannot be stopped out. -->
					<#-- StrategyQuant closes this side's earlier pending here (Replaced), fallback or not, so the
					     pending-order helpers stop counting it - see sqShortEntryReplaced (SQ.inc). -->
					sqShortEntryReplaced = true; sqShortPendRef = Close[0]; sqShortPendRefIsOrder = false;
					<@printFallbackLevelSL block "sqShort" />
					if (!sqOppositeEntryWorking(false))
					{
						if (sqShortEntryOrder != null && sqShortEntryOrder.OrderState == OrderState.Working)
						{
							sqShortEntryOrder = EnterShortStopMarket(0, false, <@printSizeMethod block "#Size#" />, sqRoundPrice(Close[0] * 0.5), <@printSignalName block />);
						}
						sqNoteMarketEntry();
						EnterShort(<@printSizeMethod block "#Size#" />, <@printSignalName block "F" />);
					}
				}
				else
				{
					<#-- QUEUED, not submitted here - see sqLongPendQueued. -->
					if (sqPendingSlotFree(false))
					{
						sqShortPendQueued = true;
						sqShortPendIsLimit = false;
						<#-- The level first: the order is sized at it. -->
						sqShortPendLevel = sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5));
						sqShortPendQty = <@printSizeMethod block "#Size#" "sqShortPendLevel" />;
						sqShortPendTakenThisBar = true; sqShortPendRef = sqShortPendLevel; sqShortPendRefIsOrder = true;
					}
				}</#if>
			}