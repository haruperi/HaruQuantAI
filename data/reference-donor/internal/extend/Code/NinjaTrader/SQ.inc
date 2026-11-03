<#--
  ============================================================================
  SQ.inc - runtime helper library (NinjaTrader), rendered into the strategy class.
  ============================================================================
  Single-file runtime: NinjaScript compiles only inside the NinjaScript Editor,
  so helpers are emitted directly into the generated .cs as private members of
  the strategy class (no #include / external DLL).

  Kept intentionally thin: NinjaScript's Managed Approach provides native order
  methods (EnterLong/SetStopLoss/SetProfitTarget...), so we only add what the
  native API cannot express directly.

  Contents:
  - sqAtrTicks / sqRoundPrice: ATR-based SL/PT distances and SQX-style price rounding.
  - pending-entry state and queue (sqFlushPendingEntries, parking, deferred SL/PT arming).
  - the register of live stop/target orders (sqTrackStopOrder, sqCurrentStop, ...).
  - account/P&L helpers (sqAccountBalance/sqAccountEquity/sqClosedPL).
  - money-management helpers (sqMMFixedAmount/sqMMRiskAccountPct/sqMMRiskBalancePct/sqMMMartingale,
    sqMMSizeByPrice/sqMMFixedAmountByPrice/sqMMBalancePctByPrice/sqMMAtrRisk + sqInitialBalance).
  - sqTradesToday (trading-options MaxTradesPerDay gate).
  - incremental indicator state (SqIndyState, sqState/sqSeriesState) and the series-aware bar
    accessors (sqBarCount, sqHigh/sqLow/sqClose).
  - order-info / strategy-control helpers (sqPositionMatches, sqOrderSL/PT, sqBarsSince*,
    draw/log/mail).

  Included by Main.tpl inside the class body (member indentation).
-->
		#region SQ runtime helpers
<#--
  sqAtrTicks and sqMMAtrRisk read the installed SqATR, so they are emitted only for a strategy whose
  SL/PT, range formulas or money management use the ATR: every caller sets sqUsesAtrRuntime (and with it
  sqUsesIndicatorPackage and sqUsesGuardedRead). A strategy without an ATR does not depend on the package
  through them.
-->
<#if sqUsesAtrRuntime!false>

<#-- ATR-based stop-loss / profit-target distance in ticks, for SetStopLoss/SetProfitTarget in
     CalculationMode.Ticks (an offset from the entry fill). The ATR is the installed SqATR - the
     replay of ATR.java - on the primary chart: an ATRBasedValue SL/PT carries no #Chart# parameter
     and the order is always on the primary instrument. It is rounded to 6 decimals, as StrategyQuant
     does, before the multiplier is applied. Returns atrMult * ATR / TickSize. -->
		// ATR-based SL/PT distance in ticks: atrMult * SqATR rounded to 6 decimals, divided by TickSize.
		private double sqAtrTicks(double atrMult, int atrPeriod)
		{
<#-- SLPT/ATRBasedValue.java: Value * SQUtils.round(atr, 6) - the ATR is rounded to 6
     decimals BEFORE the multiplier is applied, so the order here matters.
     The result is a price distance; divide by TickSize for CalculationMode.Ticks.
     barsAgo 1: the Java reads getATRValue(chart, period, 1), and at the rules StrategyQuant's
     bar[0] is the same just-closed bar as NinjaScript's [0], so the shift carries unchanged. -->
			// The ATR is rounded to 6 decimals before the multiplier, as ATRBasedValue.java.
			return sqAtrTicks(atrMult, atrPeriod, 1);
		}

<#-- ATR-based SL/PT tick distance with an explicit ATR bar shift. barsAgo 1 is the default (market
     entries, and every pending STOP LOSS - StrategyQuant evaluates the SL at order CREATION). barsAgo 0
     is the pending PROFIT TARGET case: StrategyQuant's ATRBasedValue caches the shift-1 ATR keyed to
     chartData.Bars(), and the PT formula is evaluated at the FILL - mid-bar, when Bars() has already
     advanced - so its effective frame is one bar fresher than the submit eval's. The pending blocks
     Set the PT with barsAgo 0 and refresh it per bar while the order works (printPendingSLPTRefresh).
     Returns a WHOLE number of ticks after the 5-decimal distance rounding. -->
		// ATR-based SL/PT tick distance with an explicit ATR bar shift (0 for a pending profit target).
		private double sqAtrTicks(double atrMult, int atrPeriod, int barsAgo)
		{
<#-- ATRBasedValue.java:54 rounds the finished DISTANCE to 5 decimals (SQUtils.round(value, 5)
     = whole ticks on a 5-digit instrument, half-up with the +1e-10 epsilon), so the SQX level
     is always on-tick by construction. Passing the raw fractional tick count instead would leave
     the final tick rounding to NinjaTrader, which resolves a half-tick DOWN.
     For the Price-mode (close-anchored) market path the two orders of rounding are
     equivalent - the anchor is on-tick, so sqRoundPrice(anchor + fractional) resolves the
     same fraction. -->
			// The distance is rounded to 5 decimals first, as ATRBasedValue.java, so the level lands on a tick.
<#global sqUsesIndicatorPackage = true>			double dist = sqRound(atrMult * sqRound(sqAt(0, SqATR(Close, atrPeriod).Values[0], barsAgo), 6), 5);
			return dist / TickSize;
		}
</#if>

<#--
  <summary>
  Rounds an absolute price level to the instrument's tick exactly like StrategyQuant
  rounds order levels (SQUtils.round): an epsilon of 1e-10 is added BEFORE Math.Floor(x+0.5),
  so a level landing exactly on half a tick rounds UP. NinjaTrader's own tick rounding
  resolves that tie differently, which leaves a profit target that lands exactly on half a
  tick one tick lower than StrategyQuant's.
  Used on the decision-close-anchored SL/PT prices (CalculationMode.Price), where the
  helper's pre-rounded result makes NinjaTrader's internal rounding a no-op.
  </summary>
  <param name="price">Raw price level.</param>
  <returns>Price rounded to the nearest tick, half-tick ties away from zero.</returns>
-->
		/// <summary>Rounds an absolute price level to the instrument's tick exactly like StrategyQuant rounds order levels.</summary>
		private double sqRoundPrice(double price)
		{
			if (price == 0)
				return 0;
			double f = Math.Round(1.0 / TickSize);
			return Math.Floor((price + 0.0000000001) * f + 0.5) / f;
		}

<#--
  <summary>The working pending LONG entry order (EnterLongLimit / EnterLongStopMarket), kept so
  the already-crossed market fallback can PARK it (amend it to an untouchable price) before
  entering at market under the F-suffixed signal name. While a same-name pending works, NinjaTrader's Managed rules silently swallow BOTH a
  different-type entry and CancelOrder in the same OnBarUpdate - only a same-type AMEND is
  processed, so parking is the one reliable way to neutralise the stale pending before its
  end-of-bar expiry. See EnterAtStop.tpl / EnterAtLimit.tpl.</summary>
-->
<#-- The working pending LONG entry order. -->
		private Order sqLongEntryOrder;

<#--
  <summary>The working pending SHORT entry order (EnterShortLimit / EnterShortStopMarket) -
  the short-side twin of sqLongEntryOrder, see there.</summary>
-->
<#-- The working pending SHORT entry order. -->
		private Order sqShortEntryOrder;

<#--
  <summary>A pending entry the rules asked for, held back until every rule has run and then
  submitted by sqFlushPendingEntries.
  
  A market fallback submitted while an entry order of the OPPOSITE direction is Working gets
  NO stop and NO target attached - silently, with nothing in the order log - and the position
  is then never closed. Such an opposite order can have been submitted earlier in the SAME
  OnBarUpdate, by a rule that runs before this one. It cannot be cancelled out of the way
  either - NinjaTrader swallows CancelOrder issued in the same OnBarUpdate as an entry - and
  parking it does not help because a parked order is still Working.
  
  So the placement waits instead: with every pending submitted after the last rule, a fallback
  firing in any rule sees no opposite order at all. NinjaTrader receives them in the same
  OnBarUpdate either way, so nothing about the orders themselves changes.</summary>
-->
<#-- A pending entry the rules asked for, held back until every rule has run and then submitted by sqFlushPendingEntries. -->
		private bool sqLongPendQueued;
		private bool sqLongPendIsLimit;
		private double sqLongPendLevel;
		private int sqLongPendQty;

<#-- Short-side twin of sqLongPendQueued, see there. -->
		private bool sqShortPendQueued;
		private bool sqShortPendIsLimit;
		private double sqShortPendLevel;
		private int sqShortPendQty;

<#--
  <summary>True once ClosePendingOrder / CloseAllPendingOrders closed the long pending entry on
  this bar, so the order of an earlier bar - Working until this OnBarUpdate returns - no longer
  counts as a pending entry. Cleared by sqFlushPendingEntries.</summary>
-->
<#-- True once ClosePendingOrder / CloseAllPendingOrders closed the long pending entry on this bar. -->
		private bool sqLongPendClosed;

<#-- Short-side twin of sqLongPendClosed, see there. -->
		private bool sqShortPendClosed;

<#--
  <summary>True once a pending entry block found its long level already through the market: the
  long entry order still held is the one StrategyQuant closes there (Replaced) - parked or about
  to expire - so the pending-order helpers no longer count it. A parked order is amended, which
  keeps it Working through the next bar as well. Cleared when a new long pending is submitted.</summary>
-->
<#-- True once a pending entry block found its long level already through the market. -->
		private bool sqLongEntryReplaced;

<#-- Short-side twin of sqLongEntryReplaced, see there. -->
		private bool sqShortEntryReplaced;

<#--
  <summary>True once a long pending entry was queued on this bar - it stays true when the entry
  is closed again, so the bar's pending slot stays taken. Cleared by sqFlushPendingEntries.</summary>
-->
<#-- True once a long pending entry was queued on this bar. -->
		private bool sqLongPendTakenThisBar;

<#-- Short-side twin of sqLongPendTakenThisBar, see there. -->
		private bool sqShortPendTakenThisBar;

<#-- True once a market entry was submitted on this bar. Cleared by sqFlushPendingEntries. -->
		private bool sqMarketEntryThisBar;

<#--
  <summary>
  Whether a pending entry of the given side may be queued on this bar.
  </summary>
  <remarks>
  NinjaTrader takes one pending entry per bar, the first one submitted, and ignores a pending
  submitted after a market entry of the bar. The queue changes the order in which the
  platform sees them - every pending goes out after the last rule - so without this a pending the
  platform would have ignored could take the place of one a later rule closed. Refusing it where
  the rule places it keeps the queue in the order the rules decided, which is also the order the
  StrategyQuant backtest judges. A second pending of the SAME side still replaces the queued one.
  The other side's pending of an EARLIER bar blocks it as well: it is still working while this
  bar's rules run, and the platform gives a pending of the other direction submitted beside it no
  order event - with or without a cancel of the earlier one first.
  </remarks>
  <param name="isLong">True for the long side, false for the short side.</param>
  <returns>True when neither a market entry nor a pending of the other side, of this bar or a working one of an earlier bar, came first.</returns>
-->
		/// <summary>Whether a pending entry of the given side may be queued on this bar.</summary>
		private bool sqPendingSlotFree(bool isLong)
		{
			Order opposite = isLong ? sqShortEntryOrder : sqLongEntryOrder;
			bool oppositeWorking = opposite != null
				&& (opposite.OrderState == OrderState.Working || opposite.OrderState == OrderState.Accepted);

			return !sqMarketEntryThisBar && !oppositeWorking
				&& !(isLong ? sqShortPendTakenThisBar : sqLongPendTakenThisBar);
		}

<#--
  <summary>
  Records a market entry about to be submitted and withdraws the pending entries queued on this
  bar before it: the queue would submit them after the market entry, where NinjaTrader ignores
  them anyway, and the StrategyQuant backtest withdraws them at the market entry.
  </summary>
-->
		/// <summary>Records a market entry about to be submitted and withdraws the pending entries queued on this bar before it.</summary>
		private void sqNoteMarketEntry()
		{
			sqMarketEntryThisBar = true;
			sqLongPendQueued = false;
			sqShortPendQueued = false;
		}

<#--
  <summary>Submits the pending entries the rules queued this bar. Called once, at the end of
  OnBarUpdate - see sqLongPendQueued for why they are not submitted where they are decided.</summary>
-->
		/// <summary>Submits the pending entries the rules queued this bar.</summary>
		private void sqFlushPendingEntries()
		{
			sqLongPendClosed = false;
			sqShortPendClosed = false;
			sqLongPendTakenThisBar = false;
			sqShortPendTakenThisBar = false;
			sqMarketEntryThisBar = false;

			if (sqLongPendQueued)
			{
				sqLongEntryOrder = sqLongPendIsLimit
					? EnterLongLimit(0, false, sqLongPendQty, sqLongPendLevel, "LE")
					: EnterLongStopMarket(0, false, sqLongPendQty, sqLongPendLevel, "LE");
				sqLongPendQueued = false;
				sqLongEntryReplaced = false;
			}

			if (sqShortPendQueued)
			{
				sqShortEntryOrder = sqShortPendIsLimit
					? EnterShortLimit(0, false, sqShortPendQty, sqShortPendLevel, "SE")
					: EnterShortStopMarket(0, false, sqShortPendQty, sqShortPendLevel, "SE");
				sqShortPendQueued = false;
				sqShortEntryReplaced = false;
			}
		}

<#--
  <summary>
  Parks the working long pending entry so a market entry block can enter under "LEF".
  </summary>
  <remarks>
  A market entry under "LE" while the pending of that name works is swallowed by the Managed
  approach, and so is a CancelOrder in the same OnBarUpdate; an amend of the SAME order type is the
  one change it processes. So the pending is amended to a price the market cannot reach - a buy
  stop far above, a buy limit far below - and expires unfilled, as the pending blocks' fallback
  does it. The amend keeps it Working through the next bar as well, while
  the pending StrategyQuant placed has expired by then, so it is marked replaced and the
  pending-order helpers stop counting it.
  </remarks>
  <returns>True when a working long pending was parked, false when there was none.</returns>
-->
		/// <summary>Parks the working long pending entry so a market entry block can enter under "LEF".</summary>
		private bool sqParkLongEntry()
		{
			Order o = sqLongEntryOrder;
			if (o == null || o.OrderState != OrderState.Working)
				return false;

			sqLongEntryOrder = o.OrderType == OrderType.Limit
				? EnterLongLimit(0, false, o.Quantity, sqRoundPrice(Close[0] * 0.5), "LE")
				: EnterLongStopMarket(0, false, o.Quantity, sqRoundPrice(Close[0] * 1.5), "LE");
			sqLongEntryReplaced = true;
			return true;
		}

<#--
  <summary>Short-side twin of sqParkLongEntry: a sell stop far below, a sell limit far above.</summary>
  <returns>True when a working short pending was parked, false when there was none.</returns>
-->
		/// <summary>Short-side twin of sqParkLongEntry: a sell stop far below, a sell limit far above.</summary>
		private bool sqParkShortEntry()
		{
			Order o = sqShortEntryOrder;
			if (o == null || o.OrderState != OrderState.Working)
				return false;

			sqShortEntryOrder = o.OrderType == OrderType.Limit
				? EnterShortLimit(0, false, o.Quantity, sqRoundPrice(Close[0] * 1.5), "SE")
				: EnterShortStopMarket(0, false, o.Quantity, sqRoundPrice(Close[0] * 0.5), "SE");
			sqShortEntryReplaced = true;
			return true;
		}

<#--
  <summary>Whether an entry order in the direction OPPOSITE to the one being asked for is
  working right now.
  
  A market entry that FILLS while an opposite entry order is working gets no protective
  orders at all: the Managed approach creates neither the SetStopLoss nor the SetProfitTarget
  declared for its signal name, and the position then runs unbounded.
  
  The opposite order cannot be got rid of in time - CancelOrder in the same OnBarUpdate is
  swallowed, and parking an order leaves it Working - so the fallback is skipped instead.
  Skipping an entry costs a trade; taking one that cannot be stopped out costs without a
  bound, and it is not something a backtest would ever show the user.</summary>
-->
		/// <summary>Whether an entry order in the direction OPPOSITE to the one being asked for is working right now.</summary>
		private bool sqOppositeEntryWorking(bool forLong)
		{
			Order opposite = forLong ? sqShortEntryOrder : sqLongEntryOrder;

			return opposite != null && opposite.OrderState == OrderState.Working;
		}

<#--
  <summary>Stop-loss of the pending LONG entry - a tick distance (a price level as its distance from the order price) or a percent fraction - captured at its last placement
  eval (the ORDER-CREATION frame - SQX evaluates the SL formula when the order is created,
  ATRBasedValue caches per Bars()). Applied by the deferred arming block one bar after the
  fill (printPendingSLPTArm): SQX does not exit a pending fill inside its ENTRY bar, so a
  same-bar touch must not exit here either.</summary>
-->
<#-- Stop-loss of the pending LONG entry. -->
		private double sqLongPendSL;

<#-- Short-side twin of sqLongPendSL. -->
		private double sqShortPendSL;

<#--
  <summary>The price a pending LONG entry's percent stop and target are computed from after the fill:
  the order price for a resting order (sqLongPendRefIsOrder), the decision close for its market
  fallback.</summary>
-->
<#-- The price a pending LONG entry's percent stop and target are computed from after the fill. -->
		private double sqLongPendRef;
		private bool sqLongPendRefIsOrder;

<#-- Short-side twins of sqLongPendRef and sqLongPendRefIsOrder. -->
		private double sqShortPendRef;
		private bool sqShortPendRefIsOrder;

<#--
  <summary>Stop level written by the "Move SL" ACTION block, applied one bar later
  (printMoveSLPTApply). SQX's SetStopLoss.OnAction only calls order.setSL() - the simulator
  materializes the exit order on the NEXT bar, so a level the rule computes on bar T can first
  be taken on T+1, whereas NinjaTrader handed the same level at T's close would fill it INSIDE T.
  Same deferral, same reason as the pending SL/PT arming above.
  NaN means the action has not run for the open position yet.</summary>
-->
<#-- Stop level written by the "Move SL" ACTION block, applied one bar later. -->
		private double sqMoveSL = double.NaN;

<#-- Target twin of sqMoveSL, written by the "Move PT" action block. -->
		private double sqMovePT = double.NaN;

<#--
  <summary>True when the next LONG fill originates from a pending entry (set at every pending
  placement and fallback submission, cleared by the market-entry blocks and after arming) -
  gates the deferred SL/PT arming to pending-origin positions only; market-rule entries keep
  their fill-attached same-bar Set() semantics.</summary>
-->
<#-- True when the next LONG fill originates from a pending entry. -->
		private bool sqLongPendOrigin;

<#-- Short-side twin of sqLongPendOrigin. -->
		private bool sqShortPendOrigin;

<#--
  <summary>True once the deferred SL/PT of the open pending-origin LONG position have been
  armed; reset when the position is flat (printPendingSLPTArm).</summary>
-->
<#-- True once the deferred SL/PT of the open pending-origin LONG position have been armed. -->
		private bool sqLongSLPTArmed;

<#-- Short-side twin of sqLongSLPTArmed. -->
		private bool sqShortSLPTArmed;
<#if hasPendingLevelStop()>

<#-- The bar on which the arming read a LONG pending entry's price-level stop again after the fill; the break-even
     move leaves that bar alone, as StrategyQuant overwrites its break-even with the stop it sets from the fill. -->
		private int sqLongLevelRereadBar = -1;

<#-- Short-side twin of sqLongLevelRereadBar. -->
		private int sqShortLevelRereadBar = -1;
</#if>
<#-- Needed by the per-bar trailing stop, the timed exit and everything that reads the order register - each
     addresses the stop by holder name, so a strategy with any one of them needs the fields. -->
<#if (emTrailResetDone!false) || ((emSeenExitAfterBars![])?size > 0) || needsOrderRegister()>

<#--
  <summary>Name of the entry signal that opened the live LONG position, written by
  OnExecutionUpdate from the execution that filled. The per-bar trailing stop and the timed exit address this
  instead of a literal: SetStopLoss binds to a signal NAME, and a pending entry block owns
  two ("LE" and the "LEF" market fallback), so a literal manages the wrong position whenever
  the other one filled. Seeded with the base name for the bars before the first fill.</summary>
-->
<#-- Name of the entry signal that opened the live LONG position, written by OnExecutionUpdate from the execution that filled. -->
		private string sqLongEntrySignal = "LE";

<#-- Short-side twin of sqLongEntrySignal. -->
		private string sqShortEntrySignal = "SE";
</#if>
<#if timedExitReentry("1")>

<#--
  <summary>The bar the LONG timed exit last fired on; a long market entry on that bar re-enters
  under the second signal name while the pushed stop closes the old position.</summary>
-->
<#-- The bar the LONG timed exit last fired on. -->
		private int sqLongTimedExitBar = -1;
</#if>
<#if timedExitReentry("-1")>

<#-- Short-side twin of sqLongTimedExitBar. -->
		private int sqShortTimedExitBar = -1;
</#if>
<#-- The bar of the last market entry of each direction, for strategies with more than one EnterAtMarket
     block of that direction (printSameBarMarketGuard in Parameters.inc). -->
<#if (countMarketEntries("1") > 1)>

<#--
  <summary>CurrentBar on which a long EnterAtMarket block last submitted its entry; a later long
  market block of the same bar enters nothing, as NinjaScript would ignore it anyway.</summary>
-->
<#-- CurrentBar on which a long EnterAtMarket block last submitted its entry. -->
		private int sqLongMarketEntryBar = -1;
</#if>
<#if (countMarketEntries("-1") > 1)>

<#-- Short-side twin of sqLongMarketEntryBar. -->
		private int sqShortMarketEntryBar = -1;
</#if>
<#if entryOwnerMode("1")>

<#--
  <summary>Which long EnterAtMarket block opened the position (its 1-based position among the long
  market blocks); the exit-method blocks act only on their own block's position.</summary>
-->
<#-- Which long EnterAtMarket block opened the position. -->
		private int sqLongEntryOwner = 0;
</#if>
<#if entryOwnerMode("-1")>

<#-- Short-side twin of sqLongEntryOwner. -->
		private int sqShortEntryOwner = 0;
</#if>
<#if (emTrailResetDone!false) || ((emSeenExitAfterBars![])?size > 0)>
<#--
  The stop and target levels the timed exit and the trailing stop write under an entry name. NinjaTrader keeps a
  signal name's Set configuration after its position closes and applies it to the next entry under that name, so
  an entry without a stop or target of its own would inherit a level of a closed trade. Each noted level is put
  out of reach once the position of its side is closed: a long stop at one tick, a short stop at 1e9, a long
  target at 1e9, a short target at one tick - accepted and never filled.
-->

		// The entry names whose Set stop was written by the timed exit or the trailing stop, with their direction.
		private readonly Dictionary<string, bool> sqExitLevelStops = new Dictionary<string, bool>();

		// The entry names whose Set target was written by the timed exit, with their direction.
		private readonly Dictionary<string, bool> sqExitLevelTargets = new Dictionary<string, bool>();

		/// <summary>Notes that the timed exit or the trailing stop wrote the stop, and with target the target, of an entry name.</summary>
		private void sqNoteExitLevel(string name, bool isLong, bool target)
		{
			sqExitLevelStops[name] = isLong;
			if (target)
				sqExitLevelTargets[name] = isLong;
		}

		/// <summary>Puts the noted stops and targets of one side out of reach once that side's position is closed.</summary>
		private void sqReleaseExitLevels(bool isLong)
		{
			foreach (KeyValuePair<string, bool> s in new List<KeyValuePair<string, bool>>(sqExitLevelStops))
				if (s.Value == isLong)
				{
					sqExitLevelStops.Remove(s.Key);
					SetStopLoss(s.Key, CalculationMode.Price, isLong ? TickSize : 1e9, false);
				}
			foreach (KeyValuePair<string, bool> t in new List<KeyValuePair<string, bool>>(sqExitLevelTargets))
				if (t.Value == isLong)
				{
					sqExitLevelTargets.Remove(t.Key);
					SetProfitTarget(t.Key, CalculationMode.Price, isLong ? 1e9 : TickSize);
				}
		}
</#if>
<#-- The register of live stop and target orders and its readers, for the break-even move, the Move SL
     action and the OrderSL/OrderPT blocks. Emitted together with the OnOrderUpdate in Main.tpl that
     feeds it (needsOrderRegister). -->
<#if needsOrderRegister()>

<#--
  <summary>Exit orders that can close the open position at a level: the Managed "Stop loss" and
  "Profit target" orders of each entry signal and the "MoveSL" / "MovePT" exit orders of the Move
  SL/PT actions. Filled, cancelled and rejected orders are dropped as their final update arrives.</summary>
-->
<#-- Exit orders that can close the open position at a level. -->
		private readonly List<Order> sqStopOrders = new List<Order>();
<#--
  The Move SL action's hand-over to the Set stops (printMoveSLPTApply sets sqUsesMoveSetStops). StrategyQuant
  moves the stop of every open position the action matches, so with two entries of one direction open (LE and
  LEF) both Set stops move; each entry name keeps its own last level, so an unchanged level is not re-issued
  over a stop that moved on since, and an entry that opened after the last move gets the level too.
-->
<#--
  The open-entry register behind every stop move (Move SL, break-even, trailing stop): StrategyQuant moves the
  stop of every open position, including one that has no stop of its own, so the moves reach the open entry
  names, not only the names with a live Set stop.
-->
<#if (sqUsesMoveSetStops!false) || (sqUsesSetEveryStop!false) || (sqLendsStopLoss!false)>

		// The open quantity of each long and each short entry name, kept by OnExecutionUpdate, so a stop move
		// reaches an entry that has no Set stop while another entry of its direction has one.
		private readonly Dictionary<string, int> sqOpenLongEntries = new Dictionary<string, int>();
		private readonly Dictionary<string, int> sqOpenShortEntries = new Dictionary<string, int>();

		// The entry names whose Set stop exists only because a stop move gave it one, with their direction.
		private readonly Dictionary<string, bool> sqMoveOnlyStops = new Dictionary<string, bool>();

		// The entry names a stop move has given a Set stop they had no stop of their own for.
		private readonly HashSet<string> sqMoveOnlyNames = new HashSet<string>();

		// Books one execution into the open-entry register: an entry adds its quantity to its name, an exit
		// takes it from the entry it names, and an exit that names no entry closes every entry of its side.
		private void sqNoteEntryExecution(Order order, int quantity)
		{
			if (order.OrderAction == OrderAction.Buy || order.OrderAction == OrderAction.SellShort)
			{
				Dictionary<string, int> open = order.OrderAction == OrderAction.Buy ? sqOpenLongEntries : sqOpenShortEntries;
				int held;
				open.TryGetValue(order.Name, out held);
				open[order.Name] = held + quantity;
				return;
			}
			Dictionary<string, int> side = order.OrderAction == OrderAction.Sell ? sqOpenLongEntries : sqOpenShortEntries;
			if (string.IsNullOrEmpty(order.FromEntrySignal))
			{
				foreach (string name in new List<string>(side.Keys))
					sqReleaseMoveOnlyStop(name);
				side.Clear();
				return;
			}
			int left;
			if (side.TryGetValue(order.FromEntrySignal, out left))
			{
				left -= quantity;
				if (left > 0)
					side[order.FromEntrySignal] = left;
				else
				{
					side.Remove(order.FromEntrySignal);
					sqReleaseMoveOnlyStop(order.FromEntrySignal);
				}
			}
		}

<#-- A Set stop stays with its entry name for every later entry of that name, so a level a stop move gave
     an unprotected entry is put out of reach once that entry is closed: the next entry of the name
     opens as unprotected as the strategy defines it. A long stop at one tick and a short stop at 1e9
     are accepted and never trigger. -->
		// A stop a move gave an unprotected entry goes out of reach once that entry closes.
		private void sqReleaseMoveOnlyStop(string name)
		{
			bool isLong;
<#if sqLendsTarget!false>
			// A lent profit target outlives its entry the same way; a long target at 1e9 and a short one at
			// one tick are accepted and never fill.
			if (sqLentTargets.TryGetValue(name, out isLong))
			{
				sqLentTargets.Remove(name);
				SetProfitTarget(name, CalculationMode.Price, isLong ? 1e9 : TickSize);
			}
</#if>
			if (!sqMoveOnlyStops.TryGetValue(name, out isLong))
				return;
			sqMoveOnlyStops.Remove(name);
<#if sqUsesMoveSetStops!false>
			sqMoveSLSetBy.Remove(name);
</#if>
<#if sqLendsStopLoss!false>
			sqLentStops.Remove(name);
</#if>
			SetStopLoss(name, CalculationMode.Price, isLong ? TickSize : 1e9, false);
		}
<#if sqLendsStopLoss!false>

		// The open entries that hold a lent stop loss, so each takes it once, at the close of its fill bar.
		private readonly HashSet<string> sqLentStops = new HashSet<string>();

<#-- Gives every open entry of a direction that has no stop of its own the lent stop loss, as a
     distance in ticks NinjaTrader measures from that entry's fill. A stop released to its
     never-triggering level does not count as one. -->
		// Lends the stop loss to every open entry of a direction without one, as a tick distance from its fill.
		private void sqLendStopLoss(bool isLong, double ticks)
		{
			OrderAction exitAction = isLong ? OrderAction.Sell : OrderAction.BuyToCover;
			foreach (string name in new List<string>((isLong ? sqOpenLongEntries : sqOpenShortEntries).Keys))
			{
				if (sqLentStops.Contains(name))
					continue;
				bool own = false;
				for (int i = 0; i < sqStopOrders.Count; i++)
				{
					Order o = sqStopOrders[i];
					if (o.Name == "Stop loss" && o.OrderAction == exitAction && o.FromEntrySignal == name
						&& (isLong ? o.StopPrice > TickSize : o.StopPrice < 1e9))
						own = true;
				}
				if (own)
					continue;
				SetStopLoss(name, CalculationMode.Ticks, ticks, false);
				sqLentStops.Add(name);
				sqMoveOnlyNames.Add(name);
				sqMoveOnlyStops[name] = isLong;
			}
		}
</#if>
<#if sqLendsTarget!false>

		// The open entries that hold a lent profit target, with their direction.
		private readonly Dictionary<string, bool> sqLentTargets = new Dictionary<string, bool>();

<#-- Gives every open entry of a direction that has no profit target of its own the lent one, as a
     distance in ticks from that entry's fill. A target released to its never-filling level does not
     count as one. -->
		// Lends the profit target to every open entry of a direction without one, as a tick distance from its fill.
		private void sqLendTarget(bool isLong, double ticks)
		{
			OrderAction exitAction = isLong ? OrderAction.Sell : OrderAction.BuyToCover;
			foreach (string name in new List<string>((isLong ? sqOpenLongEntries : sqOpenShortEntries).Keys))
			{
				if (sqLentTargets.ContainsKey(name))
					continue;
				bool own = false;
				for (int i = 0; i < sqStopOrders.Count; i++)
				{
					Order o = sqStopOrders[i];
					if (o.Name == "Profit target" && o.OrderAction == exitAction && o.FromEntrySignal == name
						&& (isLong ? o.LimitPrice < 1e9 : o.LimitPrice > TickSize))
						own = true;
				}
				if (own)
					continue;
				SetProfitTarget(name, CalculationMode.Ticks, ticks);
				sqLentTargets[name] = isLong;
			}
		}
</#if>

<#-- The open entries of one direction that a stop move has to reach besides the names with a live Set
     stop, marking those that hold a stop only because of a move. Empty unless one of the names has a
     Set stop: without any, the caller's single-order path covers the whole position. -->
		// The open entries a stop move has to reach besides the names with a live Set stop.
		private List<string> sqUnprotectedOpenEntries(bool isLong, ICollection<string> withStop)
		{
			List<string> extra = new List<string>();
			if (withStop.Count == 0)
				return extra;
			foreach (string open in (isLong ? sqOpenLongEntries : sqOpenShortEntries).Keys)
				if (!withStop.Contains(open))
				{
					extra.Add(open);
					sqMoveOnlyNames.Add(open);
				}
			// A name released once keeps its never-triggering stop, so it shows a live Stop loss when it opens
			// again; it is still an entry the strategy leaves unprotected.
			foreach (string name in withStop)
				if (sqMoveOnlyNames.Contains(name))
					sqMoveOnlyStops[name] = isLong;
			foreach (string name in extra)
				sqMoveOnlyStops[name] = isLong;
			return extra;
		}
</#if>
<#if sqUsesMoveSetStops!false>

		// The Move SL level last handed to SetStopLoss for each entry name.
		private readonly Dictionary<string, double> sqMoveSLSetBy = new Dictionary<string, double>();

<#-- Moves the Set stop of every open entry of the position to level, each name only when its last
     handed-over level differs: the names with a live Set stop and the open entries without one, which
     StrategyQuant moves as well. Returns false when no entry of the position has a Set stop and none is
     registered open, so the caller submits the level as a MoveSL exit order instead. -->
		// Moves the Set stop of every open entry of the position to level; false when none has one.
		private bool sqMoveSetStops(bool isLong, double level)
		{
			OrderAction exitAction = isLong ? OrderAction.Sell : OrderAction.BuyToCover;
			List<string> names = new List<string>();
			for (int i = 0; i < sqStopOrders.Count; i++)
			{
				Order o = sqStopOrders[i];
				if (o.Name == "Stop loss" && o.OrderAction == exitAction && !names.Contains(o.FromEntrySignal))
					names.Add(o.FromEntrySignal);
			}
			names.AddRange(sqUnprotectedOpenEntries(isLong, names));
			// SetStopLoss updates sqStopOrders through OnOrderUpdate, so the names are collected first.
			foreach (string name in names)
			{
				double last;
				if (sqMoveSLSetBy.TryGetValue(name, out last) && last == level)
					continue;
				SetStopLoss(name, CalculationMode.Price, level, false);
				sqMoveSLSetBy[name] = level;
			}
			return names.Count > 0;
		}
</#if>
<#--
  The break-even move and the trailing stop's hand-over to the Set stops (their macros in ExitMethods.inc set
  sqUsesSetEveryStop). StrategyQuant moves the stop of every open position, so with two entries of one
  direction open each entry name's Set stop moves.
-->
<#if sqUsesSetEveryStop!false>

<#-- Moves the Set stop of every open entry of the position to level: the names with a live Set stop and
     the open entries without one, which StrategyQuant moves as well. With onlyIfTighter a name whose stop
     already sits at the level or tighter - its own Set stop, or the position's MoveSL order when that is
     tighter - is left alone, as the break-even move requires. Returns false when no entry of the position
     has a Set stop, so the caller sets the stop of the position's entry signal instead. -->
		// Moves the Set stop of every open entry to level (with onlyIfTighter only where it tightens); false when none has one.
		private bool sqSetEveryStop(bool isLong, double level, bool onlyIfTighter)
		{
			OrderAction exitAction = isLong ? OrderAction.Sell : OrderAction.BuyToCover;
			double moveSL = double.NaN;
			Dictionary<string, double> stops = new Dictionary<string, double>();
			for (int i = 0; i < sqStopOrders.Count; i++)
			{
				Order o = sqStopOrders[i];
				if (o.OrderAction != exitAction)
					continue;
				if (o.Name == "MoveSL")
					moveSL = o.StopPrice;
				else if (o.Name == "Stop loss" && !stops.ContainsKey(o.FromEntrySignal))
					stops[o.FromEntrySignal] = o.StopPrice;
			}
			// An open entry without a stop of its own has nothing tighter than the level.
			foreach (string open in sqUnprotectedOpenEntries(isLong, stops.Keys))
				stops[open] = isLong ? double.MinValue : double.MaxValue;
			// SetStopLoss updates sqStopOrders through OnOrderUpdate, so the stops are collected first.
			foreach (KeyValuePair<string, double> s in stops)
			{
				if (onlyIfTighter)
				{
					double current = s.Value;
					if (!double.IsNaN(moveSL) && (isLong ? moveSL > current : moveSL < current))
						current = moveSL;
					if (isLong ? current >= level : current <= level)
						continue;
				}
				SetStopLoss(s.Key, CalculationMode.Price, level, false);
			}
			return stops.Count > 0;
		}
</#if>

<#--
  <summary>
  Records a level exit order from OnOrderUpdate, or drops it once it can no longer act.
  </summary>
  <param name="order">The order the update is about; orders other than level exits are ignored.</param>
-->
		/// <summary>Records a level exit order from OnOrderUpdate, or drops it once it can no longer act.</summary>
		private void sqTrackStopOrder(Order order)
		{
			if (order == null || (order.Name != "Stop loss" && order.Name != "MoveSL"
				&& order.Name != "Profit target" && order.Name != "MovePT"))
				return;

			if (order.OrderState == OrderState.Filled || order.OrderState == OrderState.Cancelled
				|| order.OrderState == OrderState.Rejected)
				sqStopOrders.Remove(order);
			else if (!sqStopOrders.Contains(order))
				sqStopOrders.Add(order);
		}

<#--
  <summary>
  The price of the stop currently protecting the open position - StrategyQuant's order SL.
  </summary>
  <remarks>
  A "Stop loss" order counts only when it belongs to the entry signal that opened the position
  (sqLongEntrySignal / sqShortEntrySignal); a "MoveSL" order counts for its side. When both are
  live, the tighter one is the stop: the higher for a long position, the lower for a short.
  </remarks>
  <param name="isLong">True for the long position's stop, false for the short position's.</param>
  <returns>The stop price, or double.NaN when no stop order is live.</returns>
-->
		/// <summary>The price of the stop currently protecting the open position - StrategyQuant's order SL.</summary>
		private double sqCurrentStop(bool isLong)
		{
			string entry = isLong ? sqLongEntrySignal : sqShortEntrySignal;
			OrderAction exitAction = isLong ? OrderAction.Sell : OrderAction.BuyToCover;
			double stop = double.NaN;

			for (int i = 0; i < sqStopOrders.Count; i++)
			{
				Order o = sqStopOrders[i];
				if (o.OrderAction != exitAction || (o.Name != "Stop loss" && o.Name != "MoveSL"))
					continue;
				if (o.Name == "Stop loss" && o.FromEntrySignal != entry)
					continue;
				if (double.IsNaN(stop) || (isLong ? o.StopPrice > stop : o.StopPrice < stop))
					stop = o.StopPrice;
			}
			return stop;
		}

<#--
  <summary>
  The price of the target currently working for the open position - StrategyQuant's order PT.
  </summary>
  <remarks>
  A "Profit target" order counts only when it belongs to the entry signal that opened the
  position; a "MovePT" order counts for its side. When both are live, the nearer one is the
  target: the lower for a long position, the higher for a short.
  </remarks>
  <param name="isLong">True for the long position's target, false for the short position's.</param>
  <returns>The target price, or double.NaN when no target order is live.</returns>
-->
		/// <summary>The price of the target currently working for the open position.</summary>
		private double sqCurrentTarget(bool isLong)
		{
			string entry = isLong ? sqLongEntrySignal : sqShortEntrySignal;
			OrderAction exitAction = isLong ? OrderAction.Sell : OrderAction.BuyToCover;
			double target = double.NaN;

			for (int i = 0; i < sqStopOrders.Count; i++)
			{
				Order o = sqStopOrders[i];
				if (o.OrderAction != exitAction || (o.Name != "Profit target" && o.Name != "MovePT"))
					continue;
				if (o.Name == "Profit target" && o.FromEntrySignal != entry)
					continue;
				if (double.IsNaN(target) || (isLong ? o.LimitPrice < target : o.LimitPrice > target))
					target = o.LimitPrice;
			}
			return target;
		}
</#if>

<#--
  <summary>
  Realized profit of every trade this strategy has closed, in account currency.
  </summary>
  <remarks>
  <para>Net of commissions - the "net" in NinjaTrader's own <c>Cum. net profit</c> column, which
  this series reproduces exactly on a zero-commission run. On a commissioned instrument the
  balance derived from it is therefore the after-cost balance, which is what StrategyQuant's
  account balance also is.</para>
  </remarks>
  <returns>Cumulative realized P/L, 0 before the first trade closes.</returns>
-->
		/// <summary>Realized profit of every trade this strategy has closed, in account currency.</summary>
		private double sqRealizedPL()
		{
			return SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit;
		}

<#--
  <summary>
  Balance the strategy started from. Mirrors StrategyBase.getInitialBalance (the run's
  initial capital).
  </summary>
  <remarks>
  <para><b>In a backtest the account's cash value IS the starting balance</b>, because it never
  moves: NinjaTrader keeps the simulated P/L in <c>SystemPerformance</c> and leaves the
  account alone.</para>
  <para><b>Live, the account is the truth</b> - it already contains every fill - so the starting
  balance is the cash value minus what this strategy has realized.</para>
  <para><b>Known limit:</b> a live run replays history as State.Historical before switching to
  Realtime, and those replayed trades land in SystemPerformance too, so during the warm-up the
  historical branch adds simulated P/L to real cash. It affects warm-up bars only; the
  alternative - identifying a backtest account by name or provider - is guesswork about the
  user's connection.</para>
  </remarks>
  <returns>The balance the run started from.</returns>
-->
		/// <summary>Balance the strategy started from.</summary>
		private double sqInitialBalance()
		{
			double cash = Account.Get(AccountItem.CashValue, Account.Denomination);
			return State == State.Historical ? cash : cash - sqRealizedPL();
		}

<#--
  <summary>
  Account balance: the starting balance plus everything realized since. Mirrors
  AccountBalance.java (getAccountBalance).
  </summary>
  <remarks>
  <para>Expressed through <see cref="sqInitialBalance"/> rather than reading the account
  directly, so that the three account helpers cannot drift apart: there is ONE state check, and
  <c>balance - initial == realized</c> holds by construction. In State.Realtime the composition
  collapses to <c>(cash - realized) + realized = cash</c>.</para>
  <para>The raw cash value alone would not do: in a backtest it is a constant, so every trade
  would be sized from the initial capital and nothing would compound.</para>
  </remarks>
  <returns>Starting balance + realized P/L.</returns>
-->
		/// <summary>Account balance: the starting balance plus everything realized since.</summary>
		private double sqAccountBalance()
		{
			return sqInitialBalance() + sqRealizedPL();
		}

<#--
  <summary>
  Account equity: balance plus the open position's unrealized P/L. Mirrors
  AccountEquity.java (getAccountEquity).
  </summary>
  <remarks>
  The position is NinjaTrader's one merged position per direction.
  </remarks>
  <returns>Account equity (balance + open unrealized P/L).</returns>
-->
		/// <summary>Account equity: balance plus the open position's unrealized P/L.</summary>
		private double sqAccountEquity()
		{
			return sqAccountBalance()
				+ Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);
		}

<#--
  <summary>
  Closed P/L in money for the <paramref name="tradesAgo"/>-th most recent closed trade
  (0 = the last one). Order identification (symbol/magic/direction/comment) is not honored -
  NT's Managed approach keeps one merged position per direction. Mirrors
  ClosedPLInMoney.java; returns 0 when there is no such trade.
  </summary>
  <param name="tradesAgo">0 = last closed trade, 1 = the one before, etc.</param>
  <returns>The trade's profit in account currency, or 0.</returns>
-->
		/// <summary>Closed P/L in money for the tradesAgo-th most recent closed trade (0 = the last one).</summary>
		private double sqClosedPL(int direction, int tradesAgo)
		{
			// Walk the closed trades newest-first, counting only those matching the direction filter -
			// the same shape sqClosedPLInPips uses.
			int index = 0;
			for (int i = SystemPerformance.AllTrades.Count - 1; i >= 0; i--)
			{
				Trade tr = SystemPerformance.AllTrades[i];
				bool trLong = tr.Entry.MarketPosition == MarketPosition.Long;
				if (direction == 1 && !trLong) continue;
				if (direction == -1 && trLong) continue;
				if (index == tradesAgo) return tr.ProfitCurrency;
				index++;
			}
			return 0;
		}

		<#-- ------------------------------------------------------------------
		     Money-management size rounding: sqRound, NOT C# Math.Round.

		     MoneyManagementMethod.round(value, step, decimals) ends in SQUtils.round(value, decimals),
		     which is HALF-UP (Math.round = floor(x+0.5) after a 1e-10 nudge). C#'s two-argument
		     Math.Round is BANKER'S rounding - it goes to the nearest EVEN digit at a midpoint - so the
		     two disagree on every exact .5. That is not an edge case here: the block's own Help text
		     says to use Decimals = 0 for stocks and futures, where the midpoints are whole halves and a
		     computed size of 2.5 would become 2 contracts instead of StrategyQuant's 3.

		     sqRound mirrors SQUtils.round exactly, including the nudge.

		     The step floor matters too: the final (int) cast cannot replace it, because Math.Round
		     ROUNDS where StrategyQuant FLOORS. Both halves live in sqMMQuantize below.

		     The floor is CONDITIONAL: StrategyQuant floors only when the instrument declares a positive
		     size step. On a stock, whose step is 0, "always floor" and "floor when the step is positive"
		     are one whole share apart.
		     ------------------------------------------------------------------ -->
<#--
  <summary>
  Quantises a computed order size the way StrategyQuant does: floor to the size step FIRST,
  then round to <paramref name="decimals"/>.
  </summary>
  <remarks>
  <para>Mirrors <c>MoneyManagementMethod.round(value, step, decimals)</c>, which is
  <c>SQUtils.round(Math.floor(value / step) * step, decimals)</c> - every money-management method
  ends there. Both halves matter: 4.9 shares floor to 4 but round to 5.</para>
  <para>The floor is <b>conditional</b>, because StrategyQuant's own is: <c>round</c> reads
  <c>if (step > 0) value = Math.floor(value / step) * step;</c> and skips the floor entirely when
  the instrument declares no size step - 609.68 then rounds up to 610 where an unconditional
  floor would give 609.</para>
  <para>Which branch applies is decided from the instrument at runtime rather than baked in at
  generation time, and that is deliberate. The step is known to the generator - it sits in the
  FreeMarker root as <c>orderSizeStep</c> - but only when the export runs from the GUI:
  <c>SourceCode.generate</c>, the CLI path behind <c>-sourcecode action=generate</c>, calls the
  two-argument overload and always passes 0. A baked value therefore cannot tell "this instrument
  really has no step" from "nobody told me", and those two need opposite branches. The instrument
  type can be read on the chart the strategy is actually attached to, which is also the more
  robust place to read it: one exported file stays correct on every instrument it is run on.</para>
  <para>The correspondence:</para>
  <list type="bullet">
  <item><description><c>Stock</c> - a stock instrument (e.g. AAPLUSUSD) declares step <c>0.0</c>.</description></item>
  <item><description><c>Forex</c> - a forex instrument (e.g. EURUSD) declares step <c>0.01</c>, a hundredth of
  a lot; the final <c>(int)</c> cast subsumes a step that small, so not flooring to a whole unit
  is the closer of the two behaviours.</description></item>
  <item><description><c>CryptoCurrency</c> - <c>CryptoSizeByPrice</c> passes
  <c>decimals = 4</c>, which is StrategyQuant's own statement that these sizes are
  fractional.</description></item>
  </list>
  <para>Everything else floors - e.g. the index USATECH.IDX declares a whole-unit step
  (<c>1.0</c>). Listing the exceptions rather than the rule is deliberate - it keeps
  <c>Unknown</c>, and any type NinjaTrader adds later, on the flooring behaviour instead of
  silently opting them into rounding.</para>
  </remarks>
  <param name="size">The raw computed size.</param>
  <param name="decimals">Decimal places the method rounds to.</param>
  <returns>The size quantised exactly as StrategyQuant quantises it.</returns>
-->
		/// <summary>Quantises a computed order size the way StrategyQuant does.</summary>
		private double sqMMQuantize(double size, int decimals)
		{
			return sqRound(sqTradesFractionalUnits() ? size : Math.Floor(size), decimals);
		}

<#--
  <summary>
  Whether StrategyQuant gives this instrument class a size step below one whole unit, and so
  quantises its computed sizes by rounding rather than by flooring. See
  <see cref="sqMMQuantize"/> for the correspondence and for why it is read from the instrument at
  runtime instead of baked in at generation time.
  </summary>
  <returns><c>true</c> for stocks, forex and crypto; <c>false</c> for everything else, including
  <c>Unknown</c>.</returns>
-->
		/// <summary>Whether StrategyQuant gives this instrument class a size step below one whole unit.</summary>
		private bool sqTradesFractionalUnits()
		{
			InstrumentType t = Instrument.MasterInstrument.InstrumentType;
			return t == InstrumentType.Stock || t == InstrumentType.Forex
					|| t == InstrumentType.CryptoCurrency;
		}

<#--
  <summary>
  Money value of a full price point for ONE LOT - the unit StrategyQuant's money management
  divides by.
  
  NinjaTrader's own PointValue is per QUANTITY UNIT, and for forex a quantity of 100,000 is one
  lot, so dividing risk money by it would yield a size in units while StrategyQuant's mirror of
  the same method yields lots - a factor of 100,000 on a forex pair. SqPointValue carries
  StrategyQuant's figure; when the instrument could not be resolved it is 0 and this falls back
  to NinjaTrader's, which is correct wherever the two agree (E-mini: both 50).
  </summary>
-->
		/// <summary>Money value of a full price point for ONE LOT.</summary>
		private double sqLotPointValue()
		{
<#if (pointValue??) && pointValue?number gt 0>			return SqPointValue > 0 ? SqPointValue : Instrument.MasterInstrument.PointValue;
<#else>			return Instrument.MasterInstrument.PointValue;
</#if>		}

<#if sqUsesSLTicksAtLevel!false>
		/// <summary>Stop-loss distance in ticks to the tick-rounded stop level, as money management sizes with it.</summary>
		private double sqSLTicksAtLevel(double slTicks, bool isLong)
		{
			if (slTicks <= 0) return slTicks;
			return isLong ? Math.Ceiling(slTicks - 0.5 - 1e-9) : Math.Floor(slTicks + 0.5 + 1e-9);
		}
</#if>

<#--
  <summary>
  Money management - Fixed amount: risk a fixed money amount per trade. Size =
  riskedMoney / (slTicks * TickSize * PointValue). When the SL distance is unknown (slTicks &lt;= 0)
  returns min(lotsIfNoMM, maxLots). Mirrors FixedAmount.java.
  </summary>
-->
		/// <summary>Money management - Fixed amount: risk a fixed money amount per trade.</summary>
		private double sqMMFixedAmount(double slTicks, double riskedMoney, int decimals, double lotsIfNoMM, double maxLots)
		{
			if (slTicks <= 0) return Math.Min(lotsIfNoMM, maxLots);
			double slInMoney = slTicks * TickSize * sqLotPointValue();
			double size = sqMMQuantize(sqRound(riskedMoney / slInMoney, 7), decimals);
			if (size <= 0) size = lotsIfNoMM;
			return Math.Min(size, maxLots);
		}

<#--
  <summary>
  Money management - Risk fixed % of account: size = (equity * risk% / 100) / slInMoney.
  When the order SL is unknown, falls back to stopLossPips. Both slTicks and stopLossPips are passed
  as real tick distances (the caller scales the SQX-pip StopLossInPips by SqPipFactor),
  so slInMoney = sl * TickSize * PointValue is correct for either. Mirrors RiskFixedPctOfAccount.java.
  </summary>
-->
		/// <summary>Money management - Risk fixed % of account: size = (equity * risk% / 100) / slInMoney.</summary>
		private double sqMMRiskAccountPct(double slTicks, double riskPct, int decimals, double stopLossPips, double lotsIfNoMM, double maxLots)
		{
			double sl = slTicks > 0 ? slTicks : stopLossPips;
			if (sl <= 0) return lotsIfNoMM;
			double slInMoney = sqRound(sl * TickSize * sqLotPointValue(), 7);
			double maxRisk = sqRound(sqAccountEquity() * (Math.Min(riskPct, 100.0) / 100.0), 7);
			double size = sqMMQuantize(sqRound(maxRisk / slInMoney, 7), decimals);
			if (size <= 0) size = lotsIfNoMM;
			return Math.Min(size, maxLots);
		}

<#--
  <summary>
  Money management - Risk fixed % of balance: size = (balance * risk% / 100) / slInMoney.
  Needs a known SL (slTicks &gt; 0), else returns lotsIfNoMM. Mirrors RiskFixedBalancePct.java.
  </summary>
-->
		/// <summary>Money management - Risk fixed % of balance: size = (balance * risk% / 100) / slInMoney.</summary>
		private double sqMMRiskBalancePct(double slTicks, double riskPct, int decimals, double lotsIfNoMM, double maxLots)
		{
			if (slTicks <= 0) return lotsIfNoMM;
			double moneyToRisk = sqRound(sqAccountBalance() * (Math.Min(riskPct, 100.0) / 100.0), 7);
			double oneLotSLDrawdown = sqRound(slTicks * TickSize * sqLotPointValue(), 7);
			double size = sqMMQuantize(sqRound(moneyToRisk / oneLotSLDrawdown, 7), decimals);
			if (size <= 0) size = lotsIfNoMM;
			return Math.Min(size, maxLots);
		}

<#--
  <summary>
  Money management - Simple Martingale: after a losing last trade, multiply its size by
  lotsMult; after a win / no trade, reset to lotsStart; if the result exceeds lotsReset, reset.
  separateByDirection compares the last trade's direction with the current position (NT Managed
  approximation). Mirrors SimpleMartingaleMM.java.
  </summary>
-->
		/// <summary>Money management - Simple Martingale.</summary>
		private double sqMMMartingale(double lotsStart, double lotsMult, double lotsReset, int decimals, bool separateByDirection)
		{
			int n = SystemPerformance.AllTrades.Count;
			Trade last = null;
			for (int i = n - 1; i >= 0; i--)
			{
				Trade tr = SystemPerformance.AllTrades[i];
				if (separateByDirection)
				{
					bool wantLong = Position.MarketPosition != MarketPosition.Short;
					bool trLong = tr.Entry.MarketPosition == MarketPosition.Long;
					if (wantLong != trLong) continue;
				}
				last = tr; break;
			}
			if (last == null || last.ProfitCurrency > 0) return sqMMQuantize(lotsStart, decimals);
			double newSize = sqMMQuantize(last.Quantity * lotsMult, decimals);
			if (newSize > lotsReset) return sqMMQuantize(lotsStart, decimals);
			return newSize;
		}

		<#-- sqInitialBalance lives next to sqAccountBalance/sqAccountEquity: the three are defined in
		     terms of one another so they cannot drift apart. -->

<#--
  <summary>
  Money management - Stocks/Crypto size by price: size = (balance or initialBalance) / price.
  Mirrors StocksSizeByPrice.java / CryptoSizeByPrice.java (Stocks uses decimals = 0). openPrice = Close[0].
  </summary>
-->
		/// <summary>Money management - Stocks/Crypto size by price.</summary>
		private double sqMMSizeByPrice(bool useBalance, double maxSize, int decimals)
		{
			double price = Close[0];
			double bal = useBalance ? sqAccountBalance() : sqInitialBalance();
			double size = sqMMQuantize(bal / price, decimals);
			if (size <= 0) size = 1;
			return Math.Min(size, maxSize);
		}

<#--
  <summary>
  Money management - Crypto fixed amount: size = riskedMoney / price. Mirrors CryptoFixedAmount.java.
  </summary>
-->
		/// <summary>Money management - Crypto fixed amount: size = riskedMoney / price.</summary>
		private double sqMMFixedAmountByPrice(double riskedMoney, int decimals)
		{
			return sqMMQuantize(riskedMoney / Close[0], decimals);
		}

<#--
  <summary>
  Money management - Crypto fixed % of balance: size = (balance * risk% / 100) / price.
  Mirrors CryptoFixedBalancePct.java.
  </summary>
-->
		/// <summary>Money management - Crypto fixed % of balance: size = (balance * risk% / 100) / price.</summary>
		private double sqMMBalancePctByPrice(double riskPct, int decimals)
		{
			double moneyToRisk = sqAccountBalance() * (Math.Min(riskPct, 100.0) / 100.0);
			return sqMMQuantize(moneyToRisk / Close[0], decimals);
		}

<#if sqUsesAtrRuntime!false>
<#-- Money management - ATR risk-based sizing: size = (equity * risk% / 100) /
     (ATR * mult * lot point value). Mirrors ATRRiskBasedSizing.java, which reads Indicators.ATR - the
     ATR.java replay the installed SqATR carries - and applies no rounding. The ATR is read at
     barsAgo 1, the bar the ATR-based SL/PT reads through sqAtrTicks: the Java calls
     getATRValue(chart, ATRPeriod, 1), and sizing runs at the same moment as the SL/PT formula. -->
		// ATR risk-based sizing, as ATRRiskBasedSizing.java: equity * risk% / (ATR[1] * mult * point value).
		private double sqMMAtrRisk(double riskPct, int atrPeriod, double atrMult, int decimals, double lotsIfNoMM, double maxLots)
		{
<#global sqUsesIndicatorPackage = true>			double slInMoney = sqRound(sqAt(0, SqATR(Close, atrPeriod).Values[0], 1) * atrMult * sqLotPointValue(), 7);
			double maxRisk = sqRound(sqAccountEquity() * (Math.Min(riskPct, 100.0) / 100.0), 7);
			double size = sqMMQuantize(sqRound(maxRisk / slInMoney, 7), decimals);
			if (size <= 0) size = lotsIfNoMM;
			return Math.Min(size, maxLots);
		}
</#if>

<#--
  <summary>
  Number of trades opened today: closed trades whose entry bar STARTS today, plus the current
  open position when its entry bar does. Used by the MaxTradesPerDay trading option.
  
  The day is taken from the bar's start, like every other calendar bucketing in this export:
  NinjaScript stamps Time[] with the bar's END, so a trade entered on a day's last bar carries
  the next day's stamp and would count against the next day's cap. A closed trade is dated from
  its entry stamp minus one bar, the open position from sqBarStart at BarsSinceEntryExecution(),
  so both are dated by the same rule.
  </summary>
-->
		/// <summary>Number of trades opened today: closed trades whose entry bar STARTS today, plus the current open position.</summary>
		private int sqTradesToday()
		{
			int count = 0;
			DateTime today = sqClock(Time[0]).Date;
			double barMinutes = sqBarPeriodMinutes(0);
			for (int i = 0; i < SystemPerformance.AllTrades.Count; i++)
				if (SystemPerformance.AllTrades[i].Entry.Time.AddMinutes(-barMinutes).Date == today) count++;
			if (Position.MarketPosition != MarketPosition.Flat)
			{
				int barsSinceEntry = ${barsSinceEntryCall()};
				if (barsSinceEntry >= 0 && barsSinceEntry <= CurrentBar && sqBarStart(0, barsSinceEntry).Date == today) count++;
			}
			return count;
		}

		#endregion

		#region SQ indicator state
		<#--
		  Incremental-state store for the sqXXX indicator helpers in SQIndicators.inc.

		  Replaying a recursion from bar 0 on every call would cost O(bars) per call and O(bars^2) per
		  backtest. The store below lets each (helper, source series, parameters) combination keep its
		  recursion scalars and the full history of produced values, so a call only advances the
		  recursion over the not-yet-computed bars (normally exactly one per bar) and reads everything
		  else from the history. Each bar is computed ONCE, by the same per-bar recurrence.

		  CONTRACT (every stateful helper follows it):
		    1. key   = "<HELPER>|<seriesId>|<p1>|<p2>|..." - one state per distinct call signature.
		    2. state = sqState(key, scalars, outputs); state.S holds the helper-specific recursion
		       scalars, state.Out[i] the per-output value history indexed by ABSOLUTE bar number
		       (0 = the oldest bar). Multi-output helpers (MACD main/signal, ADX/DI+/DI-, QQE
		       Value1/Value2, HeikenAshi O/C) advance ALL outputs in one pass.
		    3. advance: for b in state.LastBar+1 .. evalBar run the original per-bar recurrence,
		       append to Out, set LastBar = b. Reads use the original barsAgo-style indexing
		       (series[CurrentBar - b]), legal all the way back because Main.tpl sets
		       MaximumBarsLookBack.Infinite.
		    4. return state.Out[which][evalBar].

		  ASSUMES Calculate.OnBarClose (Main.tpl default): CurrentBar only grows and a bar's series
		  values are final when the helper first sees them, so repeated calls within one bar are
		  idempotent cache reads. OnEachTick would break that assumption and is out of scope.
		-->

<#--
  <summary>
  Per-instance state of one sqXXX indicator call signature: the recursion scalars
  (<see cref="S"/>, helper-specific meaning), the produced value history per output
  (<see cref="Out"/>, indexed by absolute bar number) and the highest absolute bar
  already computed (<see cref="LastBar"/>, -1 = nothing yet).
  </summary>
-->
		/// <summary>Per-instance state of one sqXXX indicator call signature.</summary>
		private sealed class SqIndyState
		{
<#-- Highest absolute bar number already computed (-1 = nothing yet). -->
			public int LastBar = -1;
<#-- Helper-specific recursion scalars (meaning documented per helper). -->
			public double[] S;
<#-- Value history per output, indexed by absolute bar number (0 = oldest bar). -->
			public List<double>[] Out;

			public SqIndyState(int scalars, int outputs)
			{
				S = new double[scalars];
				Out = new List<double>[outputs];
				for (int i = 0; i < outputs; i++)
					Out[i] = new List<double>();
			}
		}

<#-- Indicator states keyed by call signature ("HELPER|seriesId|params..."). -->
		private readonly Dictionary<string, SqIndyState> sqStates = new Dictionary<string, SqIndyState>();

<#--
  <summary>
  Returns the state for the given call-signature key, creating it on first use with
  <paramref name="scalars"/> recursion scalars and <paramref name="outputs"/> output histories.
  </summary>
  <param name="key">Call-signature key ("HELPER|seriesId|params...").</param>
  <param name="scalars">Number of recursion scalars the helper needs.</param>
  <param name="outputs">Number of output value histories the helper produces.</param>
  <returns>The (possibly new) state object.</returns>
-->
		/// <summary>Returns the state for the given call-signature key, creating it on first use with scalars recursion scalars and outputs output histories.</summary>
		private SqIndyState sqState(string key, int scalars, int outputs)
		{
			SqIndyState st;
			if (!sqStates.TryGetValue(key, out st))
			{
				st = new SqIndyState(scalars, outputs);
				sqStates[key] = st;
			}
			return st;
		}

<#--
  <summary>
  Stable identity of a source price series for state keying. Reference-based: NinjaScript's
  Close/Open/High/Low/Median/... properties return the same series instance for the lifetime
  of the strategy, so the reference hash distinguishes the sources without allocating.
  </summary>
  <param name="series">The source series (#ComputedFrom#).</param>
  <returns>A stable id string for the series instance.</returns>
-->
		/// <summary>Stable identity of a source price series for state keying.</summary>
		private string sqSeriesId(ISeries<double> series)
		{
			return System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(series).ToString();
		}

		<#--
		  ============================================================
		  SERIES-AWARE REPLAY CORE
		  ============================================================
		  A helper that computes evalBar = CurrentBar - barsAgo, walks from st.LastBar to evalBar and
		  indexes SqIndyState.Out[] by absolute PRIMARY bar number can only read the primary series -
		  pointed at a Subchart it would silently compute from the main chart, which is why printBlock
		  emits the loud SQ_SECONDARY_SERIES_NOT_SUPPORTED marker for a block whose helper is not
		  series-aware.

		  These three pieces are what a helper needs to compute over ANY series:
		    - sqBarCount(ci)   the bar clock of series ci (what CurrentBar is for the primary)
		    - sqHigh/sqLow/... the bars of series ci, barsAgo counted on ITS bars
		    - sqSeriesState(key, ci) state kept per series, so two charts do not share one replay

		  The rule that keeps this honest: a helper takes ONE ci and uses it for all three. Reading one
		  series' bars on another's clock produces values from the wrong bar, so there must be no path
		  that mixes them.

		  Known, accepted divergence: NinjaScript's Closes[ci][0] is the LAST COMPLETED bar of that
		  series, while StrategyQuant and MetaTrader 5 read the bar being built. These accessors inherit
		  NinjaTrader's reading - they are about WHICH SERIES, not about which bar of it.
		-->

<#--
  <summary>
  Bar clock of a data series: the number of the most recent bar of series <paramref name="ci"/>.
  This is what <c>CurrentBar</c> is for the primary series, and it is what a helper computing
  over a secondary series must use in place of it.
  </summary>
  <param name="ci">Data-series index (0 = primary, 1+ = the AddDataSeries order).</param>
  <returns>The absolute bar number of the series' latest bar, or -1 before it has any.</returns>
-->
		/// <summary>Bar clock of a data series: the number of the most recent bar of series ci.</summary>
		private int sqBarCount(int ci)
		{
			return ci == 0 ? CurrentBar : CurrentBars[ci];
		}
<#--
  sqAt is the read printSeriesAtOffset (Parameters.inc) emits for an offset that can reach past the
  first bar of the chart. Emitted only when a template set sqUsesGuardedRead, so a strategy whose reads
  all stay within the Reserved bars does not carry it.
-->
<#if sqUsesGuardedRead!false>

<#-- Reads series barsAgo bars back, on the bars of data series ci. Before the first bar of that
     series it returns default(T) - 0 for a price or an indicator value - as StrategyQuant does;
     the plain indexer would throw there and NinjaTrader would terminate the strategy. -->
		// Reads series barsAgo bars back on data series ci; default(T) before its first bar, as StrategyQuant.
		private T sqAt<T>(int ci, ISeries<T> series, int barsAgo)
		{
			return barsAgo > sqBarCount(ci) ? default(T) : series[barsAgo];
		}

<#-- The time-series form of sqAt (Time and Times[ci] are a TimeSeries, which is not an ISeries):
     before the first bar StrategyQuant reads time 0, the Unix epoch, so the day of week, hour and
     date blocks see 1970-01-01 00:00 (a Thursday), not DateTime.MinValue. -->
		// sqAt for a TimeSeries; before the first bar the Unix epoch, as StrategyQuant.
		private DateTime sqAt(int ci, TimeSeries series, int barsAgo)
		{
			return barsAgo > sqBarCount(ci) ? new DateTime(1970, 1, 1) : series[barsAgo];
		}
</#if>

		<#--
		  Six bar accessors, one per series NinjaScript exposes. Each mirrors the template-side
		  printSeries macro: the primary uses the scalar accessor, a secondary series
		  MUST use the indexed collection. `barsAgo` counts bars of series `ci`, NOT primary bars -
		  on a 60-minute series barsAgo 1 is an hour back, not a minute.
		-->

		/// <summary>High of series <paramref name="ci"/>, <paramref name="barsAgo"/> of ITS bars back.</summary>
		private double sqHigh(int ci, int barsAgo)
		{
			return ci == 0 ? High[barsAgo] : Highs[ci][barsAgo];
		}

		/// <summary>Low of series <paramref name="ci"/>, <paramref name="barsAgo"/> of ITS bars back.</summary>
		private double sqLow(int ci, int barsAgo)
		{
			return ci == 0 ? Low[barsAgo] : Lows[ci][barsAgo];
		}

		/// <summary>Close of series <paramref name="ci"/>, <paramref name="barsAgo"/> of ITS bars back.</summary>
		private double sqClose(int ci, int barsAgo)
		{
			return ci == 0 ? Close[barsAgo] : Closes[ci][barsAgo];
		}

		/// <summary>Open of series <paramref name="ci"/>, <paramref name="barsAgo"/> of ITS bars back.</summary>
		private double sqOpen(int ci, int barsAgo)
		{
			return ci == 0 ? Open[barsAgo] : Opens[ci][barsAgo];
		}

		/// <summary>Volume of series <paramref name="ci"/>, <paramref name="barsAgo"/> of ITS bars back.</summary>
		private double sqVolume(int ci, int barsAgo)
		{
			return ci == 0 ? Volume[barsAgo] : Volumes[ci][barsAgo];
		}

		/// <summary>Timestamp of series <paramref name="ci"/>, <paramref name="barsAgo"/> of ITS bars back.</summary>
		private DateTime sqTime(int ci, int barsAgo)
		{
			return ci == 0 ? Time[barsAgo] : Times[ci][barsAgo];
		}

<#--
  <summary>
  A bar stamp as StrategyQuant's clock reads it. StrategyQuant closes a day's last bar at 23:59:59
  of that day, where NinjaTrader stamps a bar ending at midnight 00:00 of the next one; every
  time-of-day and calendar decision (the trading options, the bar and current time blocks) has
  to see the old day's 23:59:59 there, or it acts on the wrong day.
  </summary>
  <param name="stamp">A NinjaTrader bar stamp.</param>
  <returns>The stamp, one second earlier when it falls exactly on midnight.</returns>
-->
		/// <summary>A bar stamp as StrategyQuant's clock reads it.</summary>
		private DateTime sqClock(DateTime stamp)
		{
			return stamp.TimeOfDay == TimeSpan.Zero ? stamp.AddSeconds(-1) : stamp;
		}

<#--
  <summary>
  The series' bar period in minutes, for translating NinjaScript's END-stamped Time[] into
  the bar's start. Returns 0 for bar types without a fixed time period (tick/range/volume) -
  the caller then applies no shift.
  </summary>
  <param name="ci">Series index.</param>
  <returns>Bar period in minutes, or 0 when the type has none.</returns>
-->
		/// <summary>The series' bar period in minutes, for translating NinjaScript's END-stamped Time[] into the bar's start.</summary>
		private double sqBarPeriodMinutes(int ci)
		{
			BarsPeriod bp = BarsPeriods[ci];
			if (bp.BarsPeriodType == BarsPeriodType.Minute) return bp.Value;
			if (bp.BarsPeriodType == BarsPeriodType.Day) return bp.Value * 1440.0;
			if (bp.BarsPeriodType == BarsPeriodType.Week) return bp.Value * 10080.0;
			return 0;
		}

<#--
  <summary>
  The bar's START label in the chart's own zone - NinjaScript's Time[] carries the bar's END,
  the StrategyQuant chart labels bars by their start, and every calendar bucketing
  (day/week/month grouping, minute-of-day session matching, Pivots session matching,
  anchored-VWAP session resets) must run on this frame or the boundary bar lands in the wrong
  period.
  
  The chart zone, not UTC: StrategyQuant rolls its day/week/month records on the DATA-LOCAL
  midnight and the runner feeds NinjaTrader the same data-local stamps, so the boundary has to
  be read off the display label.
  </summary>
  <param name="ci">Series index.</param>
  <param name="barsAgo">Bar offset (0 = current bar).</param>
  <returns>The bar's start time in the chart zone.</returns>
-->
		/// <summary>The bar's START label in the chart's own zone.</summary>
		private DateTime sqBarStart(int ci, int barsAgo)
		{
			return sqTime(ci, barsAgo).AddMinutes(-sqBarPeriodMinutes(ci));
		}

<#--
  <summary>
  The bar's label as the SOURCE data wrote it: <c>Time[]</c> on end-of-bar data, the bar's start
  otherwise. For helpers whose StrategyQuant counterpart compares a raw bar label against a
  clock - a session window, a pivot boundary - rather than grouping bars into periods.
  </summary>
  <param name="ci">Series index.</param>
  <param name="barsAgo">Bar offset (0 = current bar).</param>
  <returns>The bar's label in the source data's frame.</returns>
-->
		/// <summary>The bar's label as the SOURCE data wrote it.</summary>
		private DateTime sqLabel(int ci, int barsAgo)
		{
			return SqSourceEndOfBar ? sqTime(ci, barsAgo) : sqBarStart(ci, barsAgo);
		}

<#--
  <summary>
  The CLOSE SERIES of <paramref name="ci"/> as an ISeries, for handing to a native NinjaTrader
  indicator. The bar accessors above return one value; a native indicator needs the whole series,
  and passing the scalar <c>Close</c> would silently compute it on the primary chart.
  </summary>
  <remarks>
  A native SMA(Close, period) middle line next to a range computed over series ci would mix two
  charts in one value. Any helper that feeds a native indicator must use this, not the scalar.
  </remarks>
  <param name="ci">Data-series index (0 = primary).</param>
  <returns>The series' close prices.</returns>
-->
		/// <summary>The CLOSE SERIES of ci as an ISeries, for handing to a native NinjaTrader indicator.</summary>
		private ISeries<double> sqCloseSeries(int ci)
		{
			return ci == 0 ? (ISeries<double>)Close : Closes[ci];
		}

<#--
  <summary>
  State for a helper computing over data series <paramref name="ci"/>. Two charts running the
  same indicator must not share one replay - their bar clocks and their histories differ - so
  the series index becomes part of the cache key.
  </summary>
  <param name="key">Call-signature key ("HELPER|params..."), without the series component.</param>
  <param name="ci">Data-series index the helper computes over.</param>
  <param name="scalars">Number of recursion scalars the helper needs.</param>
  <param name="outputs">Number of output value histories the helper produces.</param>
  <returns>The (possibly new) state object for this (key, series) pair.</returns>
  <remarks>
  Deliberately NOT an overload of sqState: the drift guard
  (NinjaTraderCodeGenTest.testExporterHelperCopiesMatchRuntime) matches verbatim helper copies
  BY MEMBER NAME, so a second sqState would make it compare against the wrong declaration.
  </remarks>
-->
		/// <summary>State for a helper computing over data series ci.</summary>
		private SqIndyState sqSeriesState(string key, int ci, int scalars, int outputs)
		{
			return sqState(string.Concat(key, "|s", ci.ToString(System.Globalization.CultureInfo.InvariantCulture)),
				scalars, outputs);
		}

		#endregion

		#region SQ order info + util helpers
		<#--
		  Runtime for the StrategyControl / Order.Close / OtherActions blocks.

		  APPROXIMATION NOTE: the SQX blocks identify orders by
		  (Symbol, MagicNumber, Comment) via OrderFunctions.identify. NinjaTrader's Managed
		  approach keeps ONE aggregated position per direction and has neither per-order
		  comments nor magic numbers, and the export is single-symbol/single-strategy - so the
		  identification degenerates to "this strategy's orders" and only the Direction filter
		  (SQX Editors.Selection: Long=1, Short=-1, Any=0) is honoured. This loses no
		  information compared to what the SQX backtest itself evaluates for a strategy that
		  holds one position (the default #AllowDuplicateTrades# = false).
		-->

<#--
  <summary>
  True when the strategy has a pending entry on the given side: one the rules queued on this bar,
  or the one submitted on an earlier bar while it is still working, was not closed on this bar and
  was not replaced by a market fallback (sqLongEntryReplaced).
  </summary>
  <remarks>
  Read from the export's own entry state, not from the strategy's Orders collection, which a
  backtest leaves empty for pending entries. A pending entry of an earlier bar is still Working
  while this bar's rules run, and expires after them unless the rules submit it again.
  </remarks>
  <param name="isLong">True for the long side, false for the short side.</param>
  <returns>True when a pending entry of that side exists.</returns>
-->
		/// <summary>True when the strategy has a pending entry on the given side.</summary>
		private bool sqPendingEntryExists(bool isLong)
		{
			if (isLong ? sqLongPendQueued : sqShortPendQueued)
				return true;
			if (isLong ? sqLongPendClosed || sqLongEntryReplaced : sqShortPendClosed || sqShortEntryReplaced)
				return false;

			Order order = isLong ? sqLongEntryOrder : sqShortEntryOrder;
			return order != null && (order.OrderState == OrderState.Working || order.OrderState == OrderState.Accepted);
		}

<#--
  <summary>
  Closes the pending entry of the given side: a queued one is dropped before it is submitted, and
  one of an earlier bar no longer counts for the rest of this bar.
  </summary>
  <remarks>
  No CancelOrder is issued, because it cannot do more than the platform already does: a pending
  entry the rules do not submit again is cancelled after this OnBarUpdate returns, at the same
  point a CancelOrder would land, and a CancelOrder issued after a submission of the same bar is
  swallowed.
  </remarks>
  <param name="isLong">True for the long side, false for the short side.</param>
-->
		/// <summary>Closes the pending entry of the given side.</summary>
		private void sqClosePendingEntry(bool isLong)
		{
			if (isLong)
			{
				sqLongPendQueued = false;
				sqLongPendClosed = true;
			}
			else
			{
				sqShortPendQueued = false;
				sqShortPendClosed = true;
			}
		}

<#--
  <summary>Any pending entry in the given direction? Mirrors PendingOrderExists.java.</summary>
  <param name="direction">1 = long, -1 = short, 0 = any.</param>
  <returns>True when a pending entry matching the direction exists.</returns>
-->
		/// <summary>Any pending entry in the given direction? Mirrors PendingOrderExists.java.</summary>
		private bool sqPendingOrderExists(int direction)
		{
			return (direction != -1 && sqPendingEntryExists(true))
				|| (direction != 1 && sqPendingEntryExists(false));
		}

<#--
  <summary>Closes ONE pending entry matching the direction, the long side first when both match.
  Mirrors ClosePendingOrder.java.</summary>
  <param name="direction">1 = long, -1 = short, 0 = any.</param>
-->
		/// <summary>Closes ONE pending entry matching the direction, the long side first when both match.</summary>
		private void sqClosePendingOrder(int direction)
		{
			if (direction != -1 && sqPendingEntryExists(true))
				sqClosePendingEntry(true);
			else if (direction != 1 && sqPendingEntryExists(false))
				sqClosePendingEntry(false);
		}

<#--
  <summary>Closes EVERY pending entry matching the direction. Mirrors CloseAllPendingOrders.java.</summary>
  <param name="direction">1 = long, -1 = short, 0 = any.</param>
-->
		/// <summary>Closes EVERY pending entry matching the direction.</summary>
		private void sqCloseAllPendingOrders(int direction)
		{
			if (direction != -1 && sqPendingEntryExists(true))
				sqClosePendingEntry(true);
			if (direction != 1 && sqPendingEntryExists(false))
				sqClosePendingEntry(false);
		}

<#--
  <summary>
  Bars since the last position matching the direction filter was exited, or -1 when there is
  none. Unlike the other order-info blocks this cannot use the OPEN position - after an exit the
  strategy is flat - so the filter is applied to the last CLOSED trade instead.
  
  <para>Approximation, stated deliberately: NinjaTrader's BarsSinceExitExecution() reports the
  most recent exit of any direction, so when the last closed trade does not match the filter this
  returns -1 rather than reaching further back. With one aggregated position and no duplicate
  trades (the StrategyQuant default) the last closed trade IS the relevant one.</para>
  </summary>
  <param name="direction">1 = long, -1 = short, 0 = any.</param>
  <returns>Bars since that exit, or -1.</returns>
-->
		/// <summary>Bars since the last position matching the direction filter was exited, or -1.</summary>
		private int sqBarsSinceOrderClosed(int direction)
		{
			int n = SystemPerformance.AllTrades.Count;
			if (n == 0) return -1;
			if (direction != 0)
			{
				bool lastLong = SystemPerformance.AllTrades[n - 1].Entry.MarketPosition == MarketPosition.Long;
				if (direction == 1 ? !lastLong : lastLong) return -1;
			}
			return ${barsSinceExitCall()};
		}

<#--
  <summary>
  True when the single aggregated position matches the block's #Direction# filter
  (1 = long, -1 = short, 0 = any). Flat never matches.
  
  <para>MagicNumber and Comment cannot be honoured - NinjaTrader keeps one aggregated position
  and there is nothing to identify. The DIRECTION of that one position still can be, because
  Position.MarketPosition states it outright; this is the shared test the order-info family
  uses.</para>
  </summary>
  <param name="direction">1 = long, -1 = short, 0 = any.</param>
  <returns>True when the open position satisfies the filter.</returns>
-->
		/// <summary>True when the single aggregated position matches the block's #Direction# filter.</summary>
		private bool sqPositionMatches(int direction)
		{
			if (Position.MarketPosition == MarketPosition.Flat) return false;
			if (direction == 0) return true;
			bool isLong = Position.MarketPosition == MarketPosition.Long;
			return direction == 1 ? isLong : !isLong;
		}

<#-- sqOrderSL / sqOrderPT read the order register when it is emitted (needsOrderRegister): the
     strategy's Orders collection is empty in a backtest. Without the register nothing calls them,
     and they keep the plain Orders scan. -->
<#--
  <summary>
  Price of the working managed stop-loss order, 0 when none. Mirrors OrderSL.java (the SL of
  the identified live order); with the per-bar trailing manage the working stop order
  is re-pointed every bar, so this reads the CURRENT effective stop.
  </summary>
-->
		/// <summary>Price of the working managed stop-loss order, 0 when none.</summary>
		private double sqOrderSL(int direction)
		{
			if (!sqPositionMatches(direction)) return 0;
<#if needsOrderRegister()>
			double stop = sqCurrentStop(Position.MarketPosition == MarketPosition.Long);
			return double.IsNaN(stop) ? 0 : stop;
<#else>
			for (int i = 0; i < Orders.Count; i++)
			{
				Order o = Orders[i];
				if ((o.OrderState == OrderState.Working || o.OrderState == OrderState.Accepted) && o.Name == "Stop loss")
					return o.StopPrice;
			}
			return 0;
</#if>
		}

		/// <summary>Price of the working managed profit-target order, 0 when none. Mirrors OrderPT.java.</summary>
		private double sqOrderPT(int direction)
		{
			if (!sqPositionMatches(direction)) return 0;
<#if needsOrderRegister()>
			double target = sqCurrentTarget(Position.MarketPosition == MarketPosition.Long);
			return double.IsNaN(target) ? 0 : target;
<#else>
			for (int i = 0; i < Orders.Count; i++)
			{
				Order o = Orders[i];
				if ((o.OrderState == OrderState.Working || o.OrderState == OrderState.Accepted) && o.Name == "Profit target")
					return o.LimitPrice;
			}
			return 0;
</#if>
		}

<#--
  <summary>
  Open P/L of the position in SQX pips (price distance / SqPip, size-independent - exactly
  what ILiveOrder.getPLInPips() returns per order). 0 when flat or when the direction filter
  does not match. Mirrors OpenPLInPips.java under the single-position approximation.
  </summary>
-->
		/// <summary>Open P/L of the position in SQX pips.</summary>
		private double sqOpenPLInPips(int direction)
		{
			if (Position.MarketPosition == MarketPosition.Flat) return 0;
			bool isLong = Position.MarketPosition == MarketPosition.Long;
			if (direction == 1 && !isLong) return 0;
			if (direction == -1 && isLong) return 0;
			double diff = isLong ? Close[0] - Position.AveragePrice : Position.AveragePrice - Close[0];
			return diff / SqPip;
		}

<#--
  <summary>
  Closed P/L of the tradesAgo-th most recent closed trade in SQX pips (0 = the last one),
  filtered by direction; 0 when there is no such trade. Mirrors ClosedPLInPips.java.
  </summary>
-->
		/// <summary>Closed P/L of the tradesAgo-th most recent closed trade in SQX pips.</summary>
		private double sqClosedPLInPips(int direction, int tradesAgo)
		{
			int index = 0;
			for (int i = SystemPerformance.AllTrades.Count - 1; i >= 0; i--)
			{
				Trade tr = SystemPerformance.AllTrades[i];
				bool trLong = tr.Entry.MarketPosition == MarketPosition.Long;
				if (direction == 1 && !trLong) continue;
				if (direction == -1 && trLong) continue;
				if (index == tradesAgo)
				{
					double diff = trLong ? tr.Exit.Price - tr.Entry.Price : tr.Entry.Price - tr.Exit.Price;
					return diff / SqPip;
				}
				index++;
			}
			return 0;
		}

<#--
  <summary>
  Direction of the last closed trade: 1 = long, -1 = short, 0 = no trade yet. Serves
  LastOrderWas (== direction) and LastOrderWasNot (== -direction; both are false while
  no trade exists, exactly like the Java loops that fall through to false).
  </summary>
-->
		/// <summary>Direction of the last closed trade: 1 = long, -1 = short, 0 = no trade yet.</summary>
		private int sqLastOrderType()
		{
			int n = SystemPerformance.AllTrades.Count;
			if (n == 0) return 0;
			return SystemPerformance.AllTrades[n - 1].Entry.MarketPosition == MarketPosition.Long ? 1 : -1;
		}

<#-- Closed-trade count already inspected by sqTradeRecentlyClosed (edge trigger). -->
		private int sqTradeRecentlyClosedChecked = 0;

<#--
  <summary>
  True when a trade closed since the last evaluation AND its exit falls into the current
  bar (checkThisBar) or the current minute (checkThisMinute). Mirrors
  TradeRecentlyClosed.java including the edge-trigger over the closed-order count
  ("no new orders since last check" returns false).
  </summary>
-->
		/// <summary>True when a trade closed since the last evaluation AND its exit falls into the current bar.</summary>
		private bool sqTradeRecentlyClosed(bool checkThisBar, bool checkThisMinute)
		{
			int n = SystemPerformance.AllTrades.Count;
			if (n == sqTradeRecentlyClosedChecked) return false;
			int from = sqTradeRecentlyClosedChecked;
			sqTradeRecentlyClosedChecked = n;
			DateTime barStart = CurrentBar > 0 ? Time[1] : Time[0];   // bar window = (Time[1], Time[0]]
			DateTime minuteStart = new DateTime(Time[0].Year, Time[0].Month, Time[0].Day,
					Time[0].Hour, Time[0].Minute, 0);
			for (int i = n - 1; i >= from; i--)
			{
				DateTime exitTime = SystemPerformance.AllTrades[i].Exit.Time;
				if (checkThisBar && exitTime > barStart) return true;
				if (checkThisMinute && exitTime >= minuteStart) return true;
			}
			return false;
		}

<#--
  <summary>
  Close the most/least profitable open position matching the direction filter. With NT's ONE
  aggregated position per strategy the best and the worst position are the same one, so both
  blocks degenerate to "exit the position" - correct exactly when one position exists, which
  is also the SQX default (#AllowDuplicateTrades# = false). Mirrors CloseBest/WorstPosition.java.
  </summary>
-->
		/// <summary>Close the most/least profitable open position matching the direction filter.</summary>
		private void sqCloseBestOrWorstPosition(int direction)
		{
			if (Position.MarketPosition == MarketPosition.Long && direction != -1) ExitLong();
			else if (Position.MarketPosition == MarketPosition.Short && direction != 1) ExitShort();
		}

<#--
  <summary>
  Appends a timestamped line to the given file (relative names land in the NinjaTrader user
  data dir). Mirrors LogToFile; failures are printed, never thrown (an IO problem must not
  kill the strategy).
  </summary>
-->
		/// <summary>Appends a timestamped line to the given file.</summary>
		private void sqLogToFile(string fileName, string message)
		{
			try
			{
				string path = System.IO.Path.IsPathRooted(fileName)
					? fileName
					: System.IO.Path.Combine(NinjaTrader.Core.Globals.UserDataDir, fileName);
				System.IO.File.AppendAllText(path, string.Concat(
					Time[0].ToString("yyyy-MM-dd HH:mm:ss"), "  ", message, Environment.NewLine));
			}
			catch (Exception e) { Print("sqLogToFile failed: " + e.Message); }
		}

<#--
  <summary>
  Sends a mail via the configured Mail share service. MT parity: only in live trading
  (the MT tester ignores SendMail too); failures are printed, never thrown.
  </summary>
-->
		/// <summary>Sends a mail via the configured Mail share service.</summary>
		private void sqSendEmail(string subject, string message)
		{
			if (State != State.Realtime) return;
			try { SendMail("", subject, message); }
			catch (Exception e) { Print("sqSendEmail failed: " + e.Message); }
		}

		/// <summary>Draws an up arrow below the bar shift bars back (DrawUpArrow block).</summary>
		private void sqDrawUpArrow(int barsAgo)
		{
			NinjaTrader.NinjaScript.DrawingTools.Draw.ArrowUp(this, string.Concat("sqUpArrow", CurrentBar - barsAgo),
				false, barsAgo, Low[barsAgo] - SqPip, System.Windows.Media.Brushes.LimeGreen);
		}

		/// <summary>Draws a down arrow above the bar shift bars back (DrawDownArrow block).</summary>
		private void sqDrawDownArrow(int barsAgo)
		{
			NinjaTrader.NinjaScript.DrawingTools.Draw.ArrowDown(this, string.Concat("sqDownArrow", CurrentBar - barsAgo),
				false, barsAgo, High[barsAgo] + SqPip, System.Windows.Media.Brushes.Red);
		}

		/// <summary>Draws a vertical line at the bar shift bars back (DrawVerticalLine block).</summary>
		private void sqDrawVerticalLine(int barsAgo)
		{
			NinjaTrader.NinjaScript.DrawingTools.Draw.VerticalLine(this, string.Concat("sqVLine", CurrentBar - barsAgo),
				barsAgo, System.Windows.Media.Brushes.DimGray);
		}

		#endregion
