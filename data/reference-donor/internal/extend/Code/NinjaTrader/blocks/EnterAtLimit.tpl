<#-- EnterAtLimit -> pending limit entry at a price level (NinjaScript EnterLongLimit / EnterShortLimit).
     The #Price# formula child renders the limit level. SL/PT are set before the entry (applied on fill
     via the signal name). Parity with EasyLanguage EnterAtLimit (Buy/SellShort N at <price> limit +
     initial SL/PT).

     Submitted with isLiveUntilCancelled = false (the NinjaScript DEFAULT lifetime - cancelled at
     the end of the next bar): the SQX pending dies one bar after its last signal bar because the
     signal rule re-places it on every signal bar (the CloseType Replaced chain), so the default
     lifetime IS the SQX lifetime; a live-until-cancelled pending would outlive it. The leading 0
     is barsInProgressIndex - entries always go on the primary series. A non-zero #BarsValid# is
     DELIBERATELY not modelled (StrategyQuant's own expiry never fires - BarCloseSimulator
     increments barsInTrade only when an order CLOSES, so a live pending order's count stays 0 and
     checkBarsValid can never trigger; see EnterAtStop.tpl).

     MaxDistanceFromMarket: when the trading option is present, the entry is additionally
     gated by sqMaxDistanceOk (percentage distance of the limit level from Close[0]) - mirror of the
     MT5 SQ.mqh pending-order gate. -->
<#-- #ReplaceExisting# false: while a pending entry of the direction exists the block places nothing - see
     EnterAtStop.tpl. -->
<#-- Not on a bar that already had a market entry. NinjaTrader ignores a pending behind it and
     so does the backtest, but the SL/PT resets below would still run and overwrite the
     stop and target that market entry was just submitted with. Nor, when the direction also has a stop
     entry block, after the bar queued a stop entry for it (printOtherPendingTypeGuard). -->
if (openingOrdersAllowed && !sqMarketEntryThisBar<@printOtherPendingTypeGuard block true /><@printNoDuplicateGuard block /><#if getParam(block, "#ReplaceExisting#", "true") == "false"> && !sqPendingEntryExists(<#if getParam(block, "#Direction#", "1") != "-1">true<#else>false</#if>)</#if><#if tradingOptionUsed("MaxDistanceFromMarket")> && sqMaxDistanceOk(<@printPrice block "#Price#" />)</#if>)
			{
				<#-- DEFERRED SL/PT: capture the creation-frame SL here, arm SL+PT one bar after the
				     fill - see EnterAtStop.tpl and printPendingSLPTArm. -->
				<@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode != ""><#if getParam(block, "#Direction#", "1") != "-1">sqLongPendSL<#else>sqShortPendSL</#if> = ${pendingSLValue(block)};</#if>
				<#-- Overwrite stale cross-trade Set configs before the entry can fill - see
				     EnterAtStop.tpl / printPreEntrySLPTReset. -->
				<@printPreEntrySLPTReset block />
				<#if getParam(block, "#Direction#", "1") != "-1">sqLongPendOrigin = true;<#else>sqShortPendOrigin = true;</#if>
				<@printSetTrailStop block "#TrailingStop.TrailingStop#" />
				<#-- sqRoundPrice + default (non-live-until-cancelled) lifetime: same
				     semantics as EnterAtStop.tpl (see the notes there).

				     ALREADY-CROSSED level (a buy limit AT/ABOVE the market, a sell limit AT/BELOW it):
				     SQX re-places the pending at the bar-open tick and processes THAT TICK against it -
				     it fills AT THE OPEN when the open is on the favourable side of the level, else it
				     WAITS and fills at the level on touch. The export models the crossed case with a
				     MARKET order under the F-suffixed signal name, the stale same-name pending parked
				     out of reach (NT's Managed rules swallow both a different-type entry and
				     CancelOrder while it works; EntryHandling.UniqueEntries admits the F entry).
				     A market submission is the ONLY in-update order the simulator processes at the
				     next bar's open point - a limit (fresh OR amended) only activates after the open
				     and fills at min(level, HIGH), never at the open. KNOWN RESIDUAL: when the open
				     GAPS past the level (level between the decision close and the next open), SQX
				     keeps waiting and fills on the touch while this market entry pays the open - the
				     error is bounded by the close-to-open gap and there is no NinjaTrader order type
				     that can decide on the open price. -->
				<#-- The test is the plain close side, with no depth threshold (only deep crossings
				     -> market): shallow and deep crossings overlap, so a threshold cannot separate
				     the open fills from the touch fills. -->
				<#if getParam(block, "#Direction#", "1") != "-1">if (sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5)) >= Close[0])
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
							sqLongEntryOrder = EnterLongLimit(0, false, <@printSizeMethod block "#Size#" />, sqRoundPrice(Close[0] * 0.5), <@printSignalName block />);
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
						sqLongPendIsLimit = true;
						<#-- The level first: the order is sized at it. -->
						sqLongPendLevel = sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5));
						sqLongPendQty = <@printSizeMethod block "#Size#" "sqLongPendLevel" />;
						sqLongPendTakenThisBar = true; sqLongPendRef = sqLongPendLevel; sqLongPendRefIsOrder = true;
					}
				}<#else>if (sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5)) <= Close[0])
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
							sqShortEntryOrder = EnterShortLimit(0, false, <@printSizeMethod block "#Size#" />, sqRoundPrice(Close[0] * 1.5), <@printSignalName block />);
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
						sqShortPendIsLimit = true;
						<#-- The level first: the order is sized at it. -->
						sqShortPendLevel = sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5));
						sqShortPendQty = <@printSizeMethod block "#Size#" "sqShortPendLevel" />;
						sqShortPendTakenThisBar = true; sqShortPendRef = sqShortPendLevel; sqShortPendRefIsOrder = true;
					}
				}</#if>
			}