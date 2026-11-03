<#-- EnterAtMarket -> native NinjaScript market entry (EnterLong / EnterShort) with
     optional inline StopLoss / ProfitTarget. SetStopLoss/SetProfitTarget MUST be emitted
     BEFORE Enter* - NinjaScript submits them (OCO) upon the entry fill, offset from the
     fill price. Signal name pairs the SL/PT/exit with this entry.
     Docs: https://ninjatrader.com/support/helpguides/nt8/enterlong.htm
           https://ninjatrader.com/support/helpguides/nt8/setstoploss.htm
     The TrailingStop exit method emits no Set call here; it is managed per bar in OnBarUpdate
     (printTrailStopManage).
     Output e.g.:
       SetStopLoss("LE", CalculationMode.Ticks,20, false);
       SetProfitTarget("LE", CalculationMode.Ticks,sqAtrTicks(2, 14));
       SetTrailStop("LE", CalculationMode.Ticks, 20, false);
       EnterLong(1, "LE");

     IGNORES #AllowDuplicateTrades#: it cannot matter on this engine. NinjaTraderSimulator extends
     BarCloseSimulator, whose supportsDuplicateTrades() returns false, so EnterAtMarket.OnAction refuses
     a second entry while a live order exists whatever the flag says - there is never more than one
     concurrent position with the flag set or unset. The flat-position guard is therefore emitted
     unconditionally (printNoDuplicateGuard); keying it on this parameter would drop it exactly when a
     user asks for duplicates and let the exported strategy enter while a position is open when
     StrategyQuant would not.
     The flag's other StrategyQuant effect - cloning the exit methods per order - cannot produce a second
     position and has nothing to express here.
     With more than one EnterAtMarket block of a direction, only the first one to fire on a bar enters
     and sets its levels (printSameBarMarketGuard / printSameBarMarketRecord). -->
if (openingOrdersAllowed<@printNoDuplicateGuard block /><@printSameBarMarketGuard block /><@printLevelSLGuard block />)
			{
				<@printEntrySLPT block "close" />
				<@printSetTrailStop block "#TrailingStop.TrailingStop#" />
				<#-- A market fill keeps NinjaTrader's fill-attached Set() semantics (same-bar SL/PT
				     exits are correct here); clear the pending-origin flag
				     so the deferred arming block never overrides them (printPendingSLPTArm). -->
				<#if getParam(block, "#Direction#", "1") != "-1">sqLongPendOrigin = false;<#else>sqShortPendOrigin = false;</#if>
				<@printSameBarMarketRecord block />
<#-- A working pending of this direction carries the same signal name, and NinjaTrader's
     Managed rules swallow a market entry under it. When the direction has a pending block, a working
     pending is parked (sqParkLongEntry, an amend of its own type) and the entry goes under the
     F-suffixed name with its own stop and target - the pending blocks' fallback does the same. A
     strategy without a pending block in the direction generates the plain entry below. -->
<#if hasPendingEntryBlock(marketEntryDir(block))>
				if (sqPark<@printDirectionValue block "#Direction#" "Long" "Short" />Entry())
				{
					<@printEntrySLPT block "close" "F" />
					sqNoteMarketEntry();
					Enter<@printDirectionValue block "#Direction#" "Long" "Short" />(<@printSizeMethod block "#Size#" />, <@printSignalName block "F" />);
				}
				else
				{
					sqNoteMarketEntry();
					Enter<@printDirectionValue block "#Direction#" "Long" "Short" />(<@printSizeMethod block "#Size#" />, <@printSignalName block />);
				}
<#else>
				sqNoteMarketEntry();
				Enter<@printDirectionValue block "#Direction#" "Long" "Short" />(<@printSizeMethod block "#Size#" />, <@printSignalName block />);
</#if>
			}