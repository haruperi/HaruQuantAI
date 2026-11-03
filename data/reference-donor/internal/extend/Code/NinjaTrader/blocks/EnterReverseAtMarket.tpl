<#-- EnterReverseAtMarket -> market entry that reverses any opposite position. In NinjaScript Managed,
     EnterLong()/EnterShort() automatically close an opposite position and open the new one (and
     EntriesPerDirection=1 prevents pyramiding), so this maps to the same shape as EnterAtMarket.
     SL/PT/Trail are set before the entry (applied on fill via the signal name). Parity with EasyLanguage
     EnterReverseAtMarket (if MarketPosition <= 0 then Buy at market + initial SL/PT).

     The same-direction guard is load-bearing: without it a persisting entry signal re-executes
     SetStopLoss on every bar while the position is open, and NinjaScript MOVES the working stop of
     the open position each time, so the trade exits at the LAST re-armed level where StrategyQuant,
     which fixes the level once at entry, exits at the entry-time level.
     StrategyQuant's reverse entry is also a no-op while a same-direction position is open, so the
     guard changes no entries - only stops the level drift. -->
if (openingOrdersAllowed && Position.MarketPosition != MarketPosition.<@printDirectionValue block "#Direction#" "Long" "Short" />)
			{
				<@printEntrySLPT block "close" />
				<@printLevelSLAtCloseOff block />
				<@printSetTrailStop block "#TrailingStop.TrailingStop#" />
				<#-- Market fill: keep fill-attached Set() semantics, clear the pending-origin flag
				     (see EnterAtMarket.tpl / printPendingSLPTArm). -->
				<#if getParam(block, "#Direction#", "1") != "-1">sqLongPendOrigin = false;<#else>sqShortPendOrigin = false;</#if>
<#-- A working pending of this direction carries the same signal name, and NinjaTrader's
     Managed rules swallow a market entry under it. When the direction has a pending block, a working
     pending is parked (sqParkLongEntry, an amend of its own type) and the entry goes under the
     F-suffixed name with its own stop and target - the pending blocks' fallback does the same. A
     strategy without a pending block in the direction generates the plain entry below. -->
<#if hasPendingEntryBlock(marketEntryDir(block))>
				if (sqPark<@printDirectionValue block "#Direction#" "Long" "Short" />Entry())
				{
					<@printEntrySLPT block "close" "F" />
					<@printLevelSLAtCloseOff block "F" />
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
<@printTimedExitReentry block />