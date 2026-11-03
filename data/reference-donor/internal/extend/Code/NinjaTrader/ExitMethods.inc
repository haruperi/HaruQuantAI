<#--
  ============================================================================
  ExitMethods.inc - manage-based exit methods (NinjaTrader).
  ============================================================================
  StopLoss / ProfitTarget are emitted at entry (printSetSLPT). The remaining exit
  methods need per-bar management of the open position:
    - TrailingStop  : ratchet the stop behind the price (printTrailStopManage).
    - ExitAfterBars : close the position after N bars in trade (BarsSinceEntryExecution).
    - MoveSL2BE     : move the StopLoss to break-even (+/- pips) once price reaches a threshold.

  printExitMethodsCode scans the OnBarUpdate rules' entry actions and emits the
  per-bar manage code (single-position model). Called by Main.tpl in
  OnBarUpdate after the trading-options gate, before the trading rules. Mirrors the
  EasyLanguage inline _init model.
-->

<#-------------------------------------------------------------->
<#-- True when an exit-method parameter carries a RangeLevel.PriceLevel formula, which returns an
     ABSOLUTE price rather than a distance - RangeLevel/PriceLevel.java is `return
     Value.evaluateBlock()`. printRangeLevelPrice renders it as the price itself, and the caller decides
     what the price means: the trailing stop uses it as the new stop, the break-even compares the entry
     against it. Only RangeLevel parameters can carry it (#TrailingStop#, #MoveSL2BE#); the Range
     parameters (#TrailingActivation#, #SL2BEAddPips#) have no PriceLevel formula. -->
<#function isPriceLevelFormula block paramKey>
  <#list block.* as p>
    <#if p.@key == paramKey && p.Formula[0]??>
      <#if p.Formula[0].@key == "SQ.Formulas.RangeLevel.PriceLevel"><#return true /></#if>
    </#if>
  </#list>
  <#return false />
</#function>

<#-------------------------------------------------------------->
<#-- True when the strategy needs the register of live stop and target orders (sqStopOrders, fed by
     OnOrderUpdate): the break-even move and the Move SL/PT actions read it, and so do the OrderSL /
     OrderPT blocks, whose templates set sqUsesOrderLevels when they are rendered. Every caller sits
     after the OnBarUpdate rules in Main.tpl, so the rules have already been rendered when it is asked. -->
<#function needsOrderRegister>
  <#return ((emSeenMoveSL2BE![])?size > 0) || ((emSeenMoveApply![])?size > 0) || ((emSeenTrailStop![])?size > 0) || (sqUsesOrderLevels!false) || (sqLendsStopLoss!false) />
</#function>

<#-------------------------------------------------------------->
<#-- The formula key of an exit-method parameter (e.g. "SQ.Formulas.RangeLevel.FixedValue"), or "" when
     the parameter is absent or carries no formula. -->
<#function formulaKeyOf block paramKey>
  <#list block.* as p>
    <#if p.@key == paramKey && p.Formula[0]??><#return "" + p.Formula[0].@key /></#if>
  </#list>
  <#return "" />
</#function>

<#-------------------------------------------------------------->
<#-- True when an action carries an exit method that is set (formula present and not None,
     or a non-zero plain value). -->
<#function hasExitMethod block paramKey>
  <#list block.* as p>
    <#if p.@key == paramKey>
      <#if p.Formula[0]?? && !p.Formula[0].@key?contains(".None")><#return true /></#if>
      <#if !(p.Formula[0]??) && p?string?trim != "" && p?string?trim != "0"><#return true /></#if>
    </#if>
  </#list>
  <#return false />
</#function>

<#-------------------------------------------------------------->
<#-- Entry ownership inside the exit-method passes (see entryOwnerMode in Parameters.inc). Each pass
     counts the EnterAtMarket actions of a direction in document order - the order EnterAtMarket.tpl
     counts them in when it records the owner - and emOwner is the position of the current action, 0
     for any other block. emOwnerCond is the owner test an exit-method block adds to its position test,
     or "" when the direction does not track ownership. -->
<#macro emResetOwner><#assign emIdxLong = 0 /><#assign emIdxShort = 0 /><#assign emOwner = 0 /></#macro>

<#macro emTrackOwner a><#assign emOwner = 0 /><#if a.@key?string == "EnterAtMarket"><#if marketEntryDir(a) == "-1"><#assign emIdxShort = emIdxShort + 1 /><#assign emOwner = emIdxShort /><#else><#assign emIdxLong = emIdxLong + 1 /><#assign emOwner = emIdxLong /></#if></#if></#macro>

<#function emOwnerCond a>
  <#local d = marketEntryDir(a) />
  <#if (emOwner > 0) && entryOwnerMode(d)><#return " && " + entryOwnerField(d) + " == " + emOwner /></#if>
  <#return "" />
</#function>

<#-------------------------------------------------------------->
<#-- Emit per-bar manage code for ExitAfterBars / MoveSL2BE found on OnBarUpdate entry actions.

     The manage code is POSITION-AGNOSTIC (it tests Position.MarketPosition itself), so a single copy
     handles both directions. Emitted blocks are de-duplicated, so a strategy with a long entry
     action and a short entry action does not carry the identical block twice. -->
<#macro printExitMethodsCode>
  <#assign emSeenExitAfterBars = [] />
  <#assign emSeenTrailStop = [] />
  <#assign emSeenDeferredSLPT = [] />
  <#assign emSeenPendingSLPT = [] />
  <#assign emSeenMoveApply = [] />
  <#assign emSeenMoveSL2BE = [] />
  <#assign emTrailResetDone = false />
  <#-- The trailing stop first. StrategyQuant trails on BarOpen, ahead of the rules, and on the bar a pending
       entry fills it trails before the fill, whose SL/PT (armed by the passes below) then takes the stop. -->
  <@emResetOwner />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#assign emAction = action />
            <#if emAction?node_name == "Block"><#assign emAction = emAction?children[0] /></#if>
            <@emTrackOwner emAction />
            <#if hasExitMethod(emAction, "#TrailingStop.TrailingStop#")><@printTrailStopManage emAction /></#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <#-- Separate passes, not one, and the split is the point. What has to hold is an ORDER - arm the
       entry's own SL/PT, then move it to breakeven, then push it through the market for the timed
       exit - and one pass per action cannot hold it: the order would then follow the order of the
       strategy's ACTIONS, and a breakeven emitted from an earlier action would be undone by the
       arming of a later one on the entry bar.
       Emitting each stage over every action keeps the order independent of direction: ExitAfterBars
       stays last, MoveSL2BE stays after the arming. -->
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#assign emAction = action />
            <#if emAction?node_name == "Block"><#assign emAction = emAction?children[0] /></#if>
            <#if tradingOptionUsed("UseInitialSLPT")><@printDeferredSLPTManage emAction /></#if>
            <#if emAction.@key?string == "EnterAtStop" || emAction.@key?string == "EnterAtLimit"><@printPendingSLPTArm emAction /></#if>
            <#if emAction.@key?string == "EnterReverseAtMarket"><@printDeferredLevelSLArm emAction /></#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <@printLentStopLoss />
  <#-- Move SL/PT actions hand their level over here, one bar after the rule computed it. After the
       arming of the entries' own SL/PT, which would otherwise reset a moved stop on the bar after the
       fill (StrategyQuant's moved level stands there), and before the breakeven and the timed exit, so
       the level is on the order before any exit can act on it. -->
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#assign emAction = action />
            <#if emAction?node_name == "Block"><#assign emAction = emAction?children[0] /></#if>
            <#if emAction.@key?string == "SetStopLoss" || emAction.@key?string == "SetProfitTarget"><@printMoveSLPTApply emAction /></#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <#-- The breakeven after the arming, which would otherwise overwrite it on the fill bar. StrategyQuant runs
       MoveSL2BE before TrailingStop on BarOpen, so where the trail moved the stop on this bar the breakeven
       gives way to it (sqTrailMovedThisBar): the trail's level is the one that stands. -->
  <@emResetOwner />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#assign emAction = action />
            <#if emAction?node_name == "Block"><#assign emAction = emAction?children[0] /></#if>
            <@emTrackOwner emAction />
            <#if hasExitMethod(emAction, "#MoveSL2BE.MoveSL2BE#")><@printMoveSL2BEManage emAction /></#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <#-- LAST pass, and it has to stay last: ExitAfterBars implements the timed exit by pushing the
       stop THROUGH the market so the next bar gaps through it. Any SetStopLoss emitted after it
       (e.g. a MoveSL2BE) replaces that pushed level and disarms the exit.
       MoveSL2BE cannot go into the trailing-stop pass either: it would then run before the deferred
       and pending SL/PT arming, which overwrites the breakeven. -->
  <@emResetOwner />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#assign emAction = action />
            <#if emAction?node_name == "Block"><#assign emAction = emAction?children[0] /></#if>
            <@emTrackOwner emAction />
            <#if hasExitMethod(emAction, "#ExitAfterBars.ExitAfterBars#")><@printExitAfterBarsManage emAction /></#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  The stop loss one entry block lends the open positions of another.

  On the NinjaTrader engine StrategyQuant applies the exit methods of every entry action to every open
  order of its direction, magic number and comment (EnterAtMarket.OnApplyExits, run at the end of each
  rule on every bar). StopLoss.setExit sets a level only on an order that has none, from that order's own
  fill, so a position opened by a block without a stop loss takes the stop loss of the first block of its
  direction, in rule order, that has one - at the close of the bar it filled on. The export binds a
  block's exit methods to the block's entry names, so the lending is emitted here: every open entry name
  of the direction without a stop of its own gets the lender's distance in ticks, which NinjaTrader
  measures from that name's fill. Only a distance can be lent this way; a percent or price-level stop
  loss is not.

  One lender per direction: the Managed approach has neither magic numbers nor comments and the entry
  names carry only the direction, so the open entries of a direction cannot be told apart by group at
  run time. A strategy whose bare entries of one direction belong to two groups with different lenders
  gets the lender of the first group for both.
-->
<#function enterDirection a>
  <#return getParam(a, "#Direction#", "1") />
</#function>

<#function isEntryAction a>
  <#local k = a.@key?string />
  <#return k == "EnterAtMarket" || k == "EnterAtStop" || k == "EnterAtLimit" />
</#function>

<#-- The block that lends its stop loss or profit target (paramKey) to the entries of direction d, as a
     one-element sequence, or an empty one when no block of d lacks it or none has one to lend.

     Only an If-Then rule applies its entries' exit methods (IfThen.applyExits); If-Then-Else does not, in
     either branch. So a lender is an entry in the Then of an If-Then rule, while the entry that borrows can
     sit in any branch of any rule. -->
<#function exitLender d paramKey>
  <#local lenders = [] />
  <#local entries = [] />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#list ["Then", "Else"] as branch>
          <#if rule[branch][0]??>
            <#list rule[branch].* as action>
              <#local a = action />
              <#if a?node_name == "Block"><#local a = a?children[0] /></#if>
              <#if isEntryAction(a) && enterDirection(a) == d>
                <#local entries = entries + [a] />
                <#if branch == "Then" && rule.@type == "IfThen"><#local lenders = lenders + [a] /></#if>
              </#if>
            </#list>
          </#if>
        </#list>
      </#list>
    </#if>
  </#list>
  <#-- The first block with the exit that shares its magic number and comment with a block lacking it: an
       earlier block of another group lends nothing to this one, so the search goes on past it. -->
  <#list lenders as lender>
    <#if hasExitMethod(lender, paramKey)>
      <#list entries as bare>
        <#if !hasExitMethod(bare, paramKey) && getParam(bare, "#MagicNumber#", "") == getParam(lender, "#MagicNumber#", "")
            && getParam(bare, "#Comment#", "") == getParam(lender, "#Comment#", "")>
          <#return [lender] />
        </#if>
      </#list>
    </#if>
  </#list>
  <#return [] />
</#function>

<#macro printLentStopLoss>
  <#list ["1", "-1"] as d>
    <#local lender = exitLender(d, "#StopLoss.StopLoss#") />
    <#if lender?size == 1>
      <@resolveSLPT lender[0] "SL" "#StopLoss.StopLoss#" />
      <#if slptMode == "CalculationMode.Ticks">
        <#global sqLendsStopLoss = true>
<#-- An entry of this direction without a stop loss of its own takes the first stop loss its
     direction has, from its own fill, as StrategyQuant applies every entry's exit methods to
     every position of the direction. -->
			// An entry without a stop loss of its own takes its direction's first stop loss, from its own fill.
			if (<#if tradingOptionUsed("UseInitialSLPT")>UseInitialSLPT && </#if>Position.MarketPosition == MarketPosition.<#if d == "-1">Short<#else>Long</#if>)
				sqLendStopLoss(<#if d == "-1">false<#else>true</#if>, ${slptVal});
      </#if>
    </#if>
    <#local ptLender = exitLender(d, "#ProfitTarget.ProfitTarget#") />
    <#if ptLender?size == 1>
      <@resolveSLPT ptLender[0] "PT" "#ProfitTarget.ProfitTarget#" />
      <#if slptMode == "CalculationMode.Ticks">
        <#global sqLendsStopLoss = true>
        <#global sqLendsTarget = true>
			// The same for the profit target.
			if (<#if tradingOptionUsed("UseInitialSLPT")>UseInitialSLPT && </#if>Position.MarketPosition == MarketPosition.<#if d == "-1">Short<#else>Long</#if>)
				sqLendTarget(<#if d == "-1">false<#else>true</#if>, ${slptVal});
      </#if>
    </#if>
  </#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  UseInitialSLPT = false -> set the entry's SL/PT on the bar AFTER the fill.

  The option is a pure EXPORT directive: StrategyQuant's own backtest ignores it
  (UseInitialSLPT.isUsedInTrading() returns false). Its help text defines the behaviour instead: "Sets StopLoss and
  ProfitTarget immediately after the order gets filled. Otherwise SL/PT is set on next bar."

  So with the option present, the entry emits its calls under `if (UseInitialSLPT)` (printEntrySLPT)
  and this macro emits the other half: the same calls, re-issued on the first bar after the fill.
  NinjaScript accepts SetStopLoss/SetProfitTarget on an open position - that is how the standalone
  "Move SL" block works - and CalculationMode.Ticks still measures from the entry fill, so only the
  MOMENT OF EVALUATION moves. For an ATR distance that means the ATR of a later bar, which is the
  whole point of the option.

  DELIBERATE DIVERGENCE: under `false` the exported strategy does not match its own StrategyQuant
  backtest, because the backtest always behaves as `true`.

  Emitted per signal name and de-duplicated, like the trailing/exit-after-bars blocks: a strategy with
  a long and a short entry action yields one block for "LE" and one for "SE".
-->
<#--
  A reversing market entry whose price-level stop is the close of the decision bar enters without a stop
  (printLevelSLAtCloseOff) and records the level. StrategyQuant sets that level at the fill (StopLoss.setExit) and it
  takes effect from the next bar, except on the fill price itself, where a stop at zero distance stays inactive, and
  on the wrong side of the fill bar's close, where the simulator drops it as NinjaTrader rejects such a stop. At the
  close of the fill bar the recorded level becomes the entry's stop when neither applies; the record is cleared after
  that one bar either way.
  @param block  the EnterReverseAtMarket block.
-->
<#macro printDeferredLevelSLArm block><@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price"><#global sqUsesDeferredLevelSL = true><#local side><@printDirectionValue block "#Direction#" "Long" "Short" /></#local>
            // A reversing entry's stop on the decision close starts on the bar after the fill, if it is off the fill price and on its side of the close.
            if (!double.IsNaN(sq${side}DeferSL))
            {
                if (Position.MarketPosition == MarketPosition.${side} && BarsSinceEntryExecution() == 0 && sq${side}DeferSL != Position.AveragePrice
                    && sq${side}DeferSL <#if side == "Long"><<#else>></#if> Close[0])
                    SetStopLoss(sq${side}DeferSLName, CalculationMode.Price, sq${side}DeferSL, false);
                sq${side}DeferSL = double.NaN;
            }
</#if></#macro>

<#macro printDeferredSLPTManage block>
  <#local signal><@printSignalName block /></#local>
  <#local isLong><@printDirectionValue block "#Direction#" "true" "false" /></#local>
  <#local slpt><@printSetSLPT block "SL" "#StopLoss.StopLoss#" /><@printSetSLPT block "PT" "#ProfitTarget.ProfitTarget#" /></#local>
  <#if slpt?trim != "" && !emSeenDeferredSLPT?seq_contains(signal)>
    <#assign emSeenDeferredSLPT = emSeenDeferredSLPT + [signal] />
			if (!UseInitialSLPT && Position.MarketPosition == MarketPosition.<#if isLong?trim == "true">Long<#else>Short</#if> && ${barsSinceEntryCall()} == 1)
			{
				<@printSetSLPT block "SL" "#StopLoss.StopLoss#" />
				<@printSetSLPT block "PT" "#ProfitTarget.ProfitTarget#" />
			}
  </#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  Hands the Move SL/PT action's stored level to NinjaTrader, one bar after the rule computed it.

  The action itself only writes sqMoveSL / sqMovePT (printMoveSLPT). Submitting at the moment of the
  rule would let NinjaTrader fill inside that same bar, which StrategyQuant cannot: its
  SetStopLoss.OnAction calls order.setSL() and the simulator materializes the exit order on the
  following bar. This block runs at the top of OnBarUpdate, so a level written on bar T reaches the
  order before T+1 is evaluated and can first be taken there - the same shape and the same reason as
  printPendingSLPTArm.

  Gated on BarsSinceEntryExecution() >= 1, not merely on an open position, and the else-branch clears
  the levels. Clearing on FLAT alone is not enough: when one position closes and the next opens
  without a flat bar between them, the previous position's level would survive into the new
  position's ENTRY bar, be submitted at its top and fill inside it. The age gate says what the
  semantic actually is: a level the action computed for one position cannot act before the next has lived a
  bar. De-duplicated per Move signal name, so several Move rules emit the block once.

  How the stop is moved depends on what protects the position. While Managed "Stop loss" orders do,
  NinjaTrader ignores a stop exit order for the same position, so the level goes through SetStopLoss
  on every entry name that has one (sqMoveSetStops, SQ.inc): StrategyQuant moves the stop of every
  open position the action matches, and with two entries of one direction open (LE and LEF) each
  name has its own Set stop. An open entry without a Set stop next to one that has it (the open-entry
  register kept by OnExecutionUpdate) is moved the same way. A name is moved only when its level changed, because re-issuing a stored
  level every bar would undo a later trailing or break-even move. Without a Set stop the level is its
  own "MoveSL" exit order for the whole position, re-submitted every bar.
-->
<#macro printMoveSLPTApply block>
  <#local sig><@printMoveSignalName block /></#local>
  <#if !emSeenMoveApply?seq_contains(sig)>
    <#assign emSeenMoveApply = emSeenMoveApply + [sig] />
    <#global sqUsesMoveSetStops = true>
			if (Position.MarketPosition == MarketPosition.Long && ${barsSinceEntryCall()} >= 1)
			{
				if (!double.IsNaN(sqMoveSL) && !sqMoveSetStops(true, sqMoveSL))
					ExitLongStopMarket(0, true, Position.Quantity, sqMoveSL, "MoveSL", "");
				if (!double.IsNaN(sqMovePT)) ExitLongLimit(0, true, Position.Quantity, sqMovePT, "MovePT", "");
			}
			else if (Position.MarketPosition == MarketPosition.Short && ${barsSinceEntryCall()} >= 1)
			{
				if (!double.IsNaN(sqMoveSL) && !sqMoveSetStops(false, sqMoveSL))
					ExitShortStopMarket(0, true, Position.Quantity, sqMoveSL, "MoveSL", "");
				if (!double.IsNaN(sqMovePT)) ExitShortLimit(0, true, Position.Quantity, sqMovePT, "MovePT", "");
			}
			else if (Position.MarketPosition == MarketPosition.Flat)
			{
				sqMoveSL = double.NaN;
				sqMovePT = double.NaN;
				sqMoveSLSetBy.Clear();
				sqOpenLongEntries.Clear();
				sqOpenShortEntries.Clear();
			}
  </#if>
</#macro>

<#-------------------------------------------------------------->
<#-- ExitAfterBars -> close the open position once it has been in the market for >= N bars.

     A DISABLED "exit after bars" must emit NOTHING. hasExitMethod screens the parameter at the XML
     level, but a value can still render as 0 - and `BarsSinceEntryExecution() >= 0` holds on the
     entry bar itself, so every position would close the moment it opened. Rendering the bar count
     first and refusing to emit on "0" (or on an empty render) closes that off whatever the reason
     the parameter survived the XML screen. -->
<#macro printExitAfterBarsManage block>
  <#local bars><@printParam block "#ExitAfterBars.ExitAfterBars#" /></#local>
  <#local bars = bars?trim />
  <#local eabDir = getParam(block, "#Direction#", "1") />
  <#local eabPos><#if eabDir != "-1">Long<#else>Short</#if></#local>
  <#-- Scoped to the emitting ACTION's direction, not != Flat. The exit methods are a property
       of the entry action, and the two directions carry independent values - a long action may
       say 5 while the short action says 0 (disabled), and StrategyQuant then leaves every short
       running. The dedup key carries the direction for the same reason. -->
  <#local own = emOwnerCond(block) />
  <#if bars != "" && bars != "0" && !emSeenExitAfterBars?seq_contains(eabDir + "|" + bars + own)>
    <#assign emSeenExitAfterBars = emSeenExitAfterBars + [eabDir + "|" + bars + own] />
			if (Position.MarketPosition == MarketPosition.${eabPos}${own} && ${barsSinceEntryCall()} >= ${bars})
			{
<#-- The timed exit must NOT be a market Exit method. ExitLong() fills at the next bar's
     open, which is the right price, but the fill cancels the position's protective orders -
     and NinjaTrader then holds the entry submitted on that next bar inside its managed layer
     for ever: the order sits at Working while Account.Orders holds nothing, so it can never
     fill, and with EntriesPerDirection = 1 it counts as a live entry, after which every
     EnterLong returns null and the strategy stops trading for good.
     
     A Set order filling is the case NinjaTrader handles cleanly, so the close goes through
     the Set family. The profit target is moved out of reach first, or it wins the bar the
     timed exit belongs to, exiting inside the bar where StrategyQuant exits at that bar's
     open. Then the stop is pushed THROUGH the market, so the next bar opens beyond it, is
     gapped through, and fills AT THAT OPEN - the same bar and the same price the market exit
     would have got. A profit target dropped through the market instead is a resting limit
     and fills at the bar's worst price, which is why this is the stop and not the target.
     
     The distances are fractions of price, not tick counts, so they hold on any instrument
     and price scale: 10 % is past any bar's open, 50 % is unreachable within a bar.
     
     Both are addressed to the entry name that filled: a pending entry block owns the resting
     order's name and its market fallback's, and a literal misses a position the fallback opened. -->
				// Timed exit through the Set family: the stop is pushed through the market and fills at the next bar's open.
				<#if timedExitReentry((eabDir == "-1")?then("-1", "1"))>sq${eabPos}TimedExitBar = CurrentBar;
				</#if><#if eabDir != "-1">SetProfitTarget(sqLongEntrySignal, CalculationMode.Price, sqRoundPrice(Close[0] * 1.50));
				SetStopLoss(sqLongEntrySignal, CalculationMode.Price, sqRoundPrice(Close[0] * 1.10), false);
				sqNoteExitLevel(sqLongEntrySignal, true, true);
				<#else>SetProfitTarget(sqShortEntrySignal, CalculationMode.Price, sqRoundPrice(Close[0] * 0.50));
				SetStopLoss(sqShortEntrySignal, CalculationMode.Price, sqRoundPrice(Close[0] * 0.90), false);
				sqNoteExitLevel(sqShortEntrySignal, false, true);</#if>
			}
  </#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  TrailingStop -> per-bar stop management.

  It does NOT emit SetTrailStop. NinjaTrader refuses to run SetStopLoss and SetTrailStop against the
  same signal name: the stop loss wins and the trail never fires at all, whatever the call order.

  Instead the stop is moved by hand, which is what StrategyQuant itself does
  (TrailingStopHandler.checkTrailingStop, evaluated on each BarOpen while the order is live):

    * trail only once profit reaches the activation level (0 by default, i.e. immediately),
    * the new level must be BETTER than the current stop loss - never widen it,
    * and better than the level already trailed to, so it only ratchets one way.

  That third-and-second condition is why the fixed stop distance is rendered too: without it the
  first trail update could push the stop further from entry than the stop loss the strategy asked
  for, turning a trailing stop into a risk increase. With no stop loss configured the floor drops to
  double.MinValue/MaxValue, matching StrategyQuant's "SL == NOT_DEFINED" branch.

  Runs at the top of OnBarUpdate, before the entry rules, so a bar is evaluated against the stop
  before it can open anything - the same ordering StrategyQuant's BarOpen event gives.

  The stop is addressed through sqLongEntrySignal / sqShortEntrySignal, written by OnExecutionUpdate
  from the execution that actually FILLED (Main.tpl). SetStopLoss binds to a signal NAME, and a
  pending entry block owns two of them - the resting order ("LE"/"SE") and the market fallback it
  submits when its level is already through the close ("LEF"/"SEF"). The holder cannot be derived
  from submission-side state:

    * A literal base name leaves every position opened by the fallback on its entry stop for the
      whole trade.
    * Arming BOTH names is worse: SetStopLoss arms a level for a name whether or not that name holds
      the position, and the level survives the trade, so the trailed level reaches the NEXT entry
      under the other name, which then starts with a stop already through the market.
    * A field written at entry SUBMISSION records the last name submitted, not the one that filled:
      a pending order fills bars after it was submitted, and the entry block may submit the market
      fallback in between.

  execution.Order.Name at the fill is authoritative - do not go back to a literal or to a field
  written next to an Enter* call.
-->
<#macro printTrailStopManage block>
  <#local dist><@printRangeLevelPrice block "#TrailingStop.TrailingStop#" /></#local>
  <#local act><@printRangeLevelPrice block "#TrailingStop.TrailingActivation#" /></#local>
  <#-- A PriceLevel trailing stop IS the new stop price; every other RangeLevel formula is a distance
       from Close[0]. Emitting Close[0] - level for a PriceLevel would put the candidate near zero,
       the floor test would refuse it on every bar and the trailing stop would never arm. -->
  <#local trailIsLevel = isPriceLevelFormula(block, "#TrailingStop.TrailingStop#") />
  <#-- A "Range in pips" trailing stop is reported as not supported by printSetTrailStop, so no per-bar
       trailing is emitted for it either. -->
  <#if formulaKeyOf(block, "#TrailingStop.TrailingStop#") == "SQ.Formulas.RangeLevel.PriceRange"><#return></#if>
  <#local hasSL = hasExitMethod(block, "#StopLoss.StopLoss#") />
  <#local sl><#if hasSL><@printRangeLevelPrice block "#StopLoss.StopLoss#" /></#if></#local>
  <#local dir><@printDirectionValue block "#Direction#" "Long" "Short" /></#local>
  <#local dir = dir?trim />
  <#local own = emOwnerCond(block) />
  <#local key = dir + "|" + dist?trim + own />
  <#if dist?trim != "" && dist?trim != "0" && !emSeenTrailStop?seq_contains(key)>
    <#assign emSeenTrailStop = emSeenTrailStop + [key] />
    <#global sqUsesSetEveryStop = true>
    <#-- The reset is direction-agnostic, so it is emitted once however many entry actions trail. It runs
         whenever the side of the position changes, not only when it is flat: a reversal closes one side
         and opens the other within one bar, and the new position must not keep the old side's level. -->
    <#if !emTrailResetDone>
      <#assign emTrailResetDone = true />
			if (Position.MarketPosition != sqTrailSide)
			{
				sqTrailStop = double.NaN;
				sqTrailSide = Position.MarketPosition;
			}
			sqTrailMovedThisBar = false;
    </#if>
    <#-- Emitted per DIRECTION, not once for both. A strategy whose long and short entries carry
         different trailing distances would otherwise have the second one dropped by the de-duplication
         and the first one silently applied to both sides. -->
    <#if dir == "Long">
			if (Position.MarketPosition == MarketPosition.Long${own})
			{
				double sqTrailNewLong = <#if trailIsLevel>${dist}<#else>Close[0] - (${dist})</#if>;
				double sqTrailFloorLong = <#if hasSL>Position.AveragePrice - (${sl})<#else>double.MinValue</#if>;
				<#-- A trailing stop may never sit on the wrong side of the market. TrailingStopHandler.
				     isTrailingStopValid enforces it on the StrategyQuant side against referencePrice - the
				     completed bar's close, which is Close[0] here. A PriceLevel can land on the wrong side
				     of the market, and NinjaTrader would then fill the stop on the bar after entry, at a
				     price better than the entry.

				     Emitted for PriceLevel ONLY, though StrategyQuant applies it to every trailing stop. For
				     a DISTANCE formula the test is `Close[0] - dist < Close[0]`, true whenever dist is
				     positive, and every distance formula here is - ATR and Pct by construction, FixedValue
				     because a zero distance emits no trailing block at all.

				     StrategyQuant also allows MinDistance here, which these templates do not model. -->
				if (Close[0] - Position.AveragePrice >= ${act}
					&& sqTrailNewLong > sqTrailFloorLong<#if trailIsLevel>
					&& sqTrailNewLong < Close[0]</#if>
					&& (double.IsNaN(sqTrailStop) || sqTrailNewLong > sqTrailStop))
				{
					sqTrailStop = sqTrailNewLong;
					sqTrailMovedThisBar = true;
					if (!sqSetEveryStop(true, sqTrailStop, false))
						SetStopLoss(sqLongEntrySignal, CalculationMode.Price, sqTrailStop, false);
					sqNoteExitLevel(sqLongEntrySignal, true, false);
				}
			}
    <#else>
			if (Position.MarketPosition == MarketPosition.Short${own})
			{
				double sqTrailNewShort = <#if trailIsLevel>${dist}<#else>Close[0] + (${dist})</#if>;
				double sqTrailFloorShort = <#if hasSL>Position.AveragePrice + (${sl})<#else>double.MaxValue</#if>;
				<#-- A trailing stop may never sit on the wrong side of the market. TrailingStopHandler.
				     isTrailingStopValid enforces it on the StrategyQuant side against referencePrice - the
				     completed bar's close, which is Close[0] here. A PriceLevel can land on the wrong side
				     of the market, and NinjaTrader would then fill the stop on the bar after entry, at a
				     price better than the entry.

				     Emitted for PriceLevel ONLY, though StrategyQuant applies it to every trailing stop. For
				     a DISTANCE formula the test is `Close[0] - dist < Close[0]`, true whenever dist is
				     positive, and every distance formula here is - ATR and Pct by construction, FixedValue
				     because a zero distance emits no trailing block at all.

				     StrategyQuant also allows MinDistance here, which these templates do not model. -->
				if (Position.AveragePrice - Close[0] >= ${act}
					&& sqTrailNewShort < sqTrailFloorShort<#if trailIsLevel>
					&& sqTrailNewShort > Close[0]</#if>
					&& (double.IsNaN(sqTrailStop) || sqTrailNewShort < sqTrailStop))
				{
					sqTrailStop = sqTrailNewShort;
					sqTrailMovedThisBar = true;
					if (!sqSetEveryStop(false, sqTrailStop, false))
						SetStopLoss(sqShortEntrySignal, CalculationMode.Price, sqTrailStop, false);
					sqNoteExitLevel(sqShortEntrySignal, false, false);
				}
			}
    </#if>
  </#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  Deferred pending-entry SL/PT arming.

  StrategyQuant's simulator does not exit a pending fill inside its ENTRY bar, whereas NinjaTrader's
  fill-attached Set() can take the stop in the entry bar itself. So pending entries are submitted
  WITHOUT pre-Set SL/PT, and this block - at the top of OnBarUpdate, i.e. the first eval after the
  fill - arms them on the open position:

    * SL = the value CAPTURED at the last placement eval (sq*PendSL): SQX evaluates the stop-loss
      formula when the order is CREATED (ATRBasedValue caches per Bars()).
    * PT = resolved HERE with the default shift: SQX evaluates the profit target at the FILL, and
      this eval's shift-1 frame is exactly the fill frame - for same-bar and lifetime-tail fills
      alike.

  Both signal names (plain + F fallback) are armed - the one matching the position's entry applies,
  the other becomes a template the next placement overwrites. Gated on sq*PendOrigin so a position
  opened by a MARKET rule keeps its fill-attached same-bar Set() semantics; the market entry blocks
  clear the flag. De-duplicated per direction + rendered body.
-->
<#--
  Pre-entry SL/PT reset.

  NinjaTrader keeps every Set* configuration ALIVE ACROSS TRADES under its signal name, and attaches
  a bracket to the next entry under that name already at submission, re-anchoring Ticks distances to
  the fill. Without a reset the deferred arming (one bar after the fill) would be defeated for every
  trade after the first: the pre-arm window would run on whatever the PREVIOUS trade left behind.
  Ticks leftovers are near-correct; a PRICE leftover - the trailing stop, the timed exit, MoveSL2BE
  all write one - is an absolute level from a dead trade and can exit the new position instantly at
  its entry price.

  This macro overwrites the configuration of BOTH signal names with the values of THIS entry, right
  before the Enter* call, so nothing stale can reach the fill. The gate it is called from only runs
  flat (printNoDuplicateGuard), so it can never touch a live position's orders. The arm macro below
  still re-Sets after the fill, which re-anchors the PT to its fill-frame ATR.
-->
<#--
  The value a pending entry's stop loss is captured as at placement, from the globals resolveSLPT left: a
  tick distance and a percent fraction as they are. A price level becomes its distance in ticks from the
  order's own price - StrategyQuant keeps a pending entry's stop as a distance from the order price and
  measures it from the fill - or 0 when the level is not a price (the block read 0), in which case
  StrategyQuant sets no stop at placement and reads the level again after the fill (printPendingSLLines).
  @param block  the EnterAtStop / EnterAtLimit block.
-->
<#function pendingSLValue block>
  <#if slptMode != "CalculationMode.Price"><#return slptVal /></#if>
  <#local orderPrice><@printPrice block "#Price#" /></#local>
  <#return "(" + slptVal + " > 0 ? Math.Round(Math.Abs(sqRoundPrice(sqRound(" + orderPrice?trim + ", 5)) - sqRoundPrice(" + slptVal + ")) / TickSize) : 0)" />
</#function>

<#--
  The SetStopLoss lines of a pending entry's stop, from the globals resolveSLPT left, for both signal names.
  A captured distance is set in its own mode; a price level was captured as a tick distance. A price level
  captured as 0 gives the entry no stop: NinjaTrader keeps a signal name's stop from its previous trade and
  has no call that removes it, so before the entry it is overwritten with a level that never triggers - one
  tick for a long, 1e9 for a short. Not 0: NinjaTrader does not submit a long stop at 0, and a stop that was
  never submitted is not created by a later SetStopLoss either. With arm set (after the fill) such
  a level is read again and, when it is a price now, set as that absolute level - what StrategyQuant does
  on the first bar after the fill.
  @param block  the EnterAtStop / EnterAtLimit block.
  @param pfx    "sqLong" or "sqShort".
  @param arm    true after the fill, false before the entry.
-->
<#--
  The Set lines of a pending entry's PERCENT stop or target, for both signal names. The market fallback
  (the F name) gets its level at the entry, as a market entry does: the distance from the decision close
  to its percent level, measured from the fill. The resting order gets nothing live at the entry (the
  percent of price 0 is 0) - its leftover level is overwritten with one that never triggers - and after
  the fill the level from the fill price (sq*PendRefIsOrder, written by the entry block, tells the two
  apart; sq*PendRef holds the decision close of the fallback).
  @param block  the EnterAtStop / EnterAtLimit block.
  @param pfx    "sqLong" or "sqShort".
  @param kind   "SL" or "PT".
  @param pct    the percent as a fraction, e.g. "sqLongPendSL" or "(1) / 100.0".
  @param arm    true after the fill, false before the entry.
-->
<#macro printPendingPercentLines block pfx kind pct arm><#local isLong = getParam(block, "#Direction#", "1") != "-1" /><#local call><#if kind == "SL">SetStopLoss<#else>SetProfitTarget</#if></#local><#local tail><#if kind == "SL">, false</#if></#local><#local up = (kind == "SL") != isLong /><#local lvl>${pfx}PendRef * (1 <#if up>+<#else>-</#if> (${pct}))</#local><#local fillLvl>Position.AveragePrice * (1 <#if up>+<#else>-</#if> (${pct}))</#local><#local closeLvl>Close[0] * (1 <#if up>+<#else>-</#if> (${pct}))</#local><#if !arm><#local never><#if up>1e9<#else>TickSize</#if></#local>${call}(<@printSignalName block />, CalculationMode.Price, ${never}${tail});
				${call}(<@printSignalName block "F" />, CalculationMode.Ticks, Math.Round(Math.Abs(Close[0] - sqRoundPrice(${closeLvl})) / TickSize)${tail});<#else>if (${pfx}PendRefIsOrder)
				{
					${call}(<@printSignalName block />, CalculationMode.Price, sqRoundPrice(${fillLvl})${tail});
					${call}(<@printSignalName block "F" />, CalculationMode.Price, sqRoundPrice(${fillLvl})${tail});
				}
				else
				{
					${call}(<@printSignalName block />, CalculationMode.Ticks, Math.Round(Math.Abs(${pfx}PendRef - sqRoundPrice(${lvl})) / TickSize)${tail});
					${call}(<@printSignalName block "F" />, CalculationMode.Ticks, Math.Round(Math.Abs(${pfx}PendRef - sqRoundPrice(${lvl})) / TickSize)${tail});
				}</#if></#macro>


<#macro printPendingSLLines block pfx arm><#if slptMode == "CalculationMode.Percent"><@printPendingPercentLines block pfx "SL" pfx + "PendSL" arm /><#elseif slptMode == "CalculationMode.Price">if (${pfx}PendSL > 0)
				{
					SetStopLoss(<@printSignalName block />, CalculationMode.Ticks, ${pfx}PendSL, false);
					SetStopLoss(<@printSignalName block "F" />, CalculationMode.Ticks, ${pfx}PendSL, false);
				}<#if !arm><#local never><#if getParam(block, "#Direction#", "1") != "-1">TickSize<#else>1e9</#if></#local>
				else
				{
					SetStopLoss(<@printSignalName block />, CalculationMode.Price, ${never}, false);
					SetStopLoss(<@printSignalName block "F" />, CalculationMode.Price, ${never}, false);
				}</#if><#if arm>
				else if (${slptVal} > 0)
				{
					SetStopLoss(<@printSignalName block />, CalculationMode.Price, sqRoundPrice(${slptVal}), false);
					SetStopLoss(<@printSignalName block "F" />, CalculationMode.Price, sqRoundPrice(${slptVal}), false);
					${pfx}LevelRereadBar = CurrentBar;
				}</#if><#else>SetStopLoss(<@printSignalName block />, ${slptMode}, ${pfx}PendSL, false);
				SetStopLoss(<@printSignalName block "F" />, ${slptMode}, ${pfx}PendSL, false);</#if></#macro>

<#--
  The stop of a pending entry's market fallback (the F name) when the stop loss is a price level. StrategyQuant
  enters such a fallback as a market order: it takes the level's distance from the decision close, whichever
  side of the entry the level is on, and measures it from the fill. The resting order keeps the distance from
  its own price that pendingSLValue captured. The captured distance is overwritten here, so the arming after
  the fill sets the fallback's own distance. A level that is not a price (0) keeps the resting order's handling.
  @param block  the EnterAtStop / EnterAtLimit block.
  @param pfx    "sqLong" or "sqShort".
-->
<#macro printFallbackLevelSL block pfx><@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price">if (${slptVal} > 0)
					{
						${pfx}PendSL = Math.Round(Math.Abs(Close[0] - sqRoundPrice(${slptVal})) / TickSize);
						if (${pfx}PendSL > 0) SetStopLoss(<@printSignalName block "F" />, CalculationMode.Ticks, ${pfx}PendSL, false);
					}</#if></#macro>

<#macro printPreEntrySLPTReset block>
  <#local pfx><#if getParam(block, "#Direction#", "1") != "-1">sqLong<#else>sqShort</#if></#local>
  <@resolveSLPT block "SL" "#StopLoss.StopLoss#" />
  <#local slLine = "" />
  <#if slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode != "">
    <#local slLine><@printPendingSLLines block pfx false /></#local>
  </#if>
  <@resolveSLPT block "PT" "#ProfitTarget.ProfitTarget#" />
  <#local ptLine = "" />
  <#if slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode == "CalculationMode.Percent">
    <#local ptLine><@printPendingPercentLines block pfx "PT" slptVal false /></#local>
  <#elseif slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode != "">
    <#local ptLine>SetProfitTarget(<@printSignalName block />, ${slptMode}, ${slptVal});${slptMmNote}
				SetProfitTarget(<@printSignalName block "F" />, ${slptMode}, ${slptVal});</#local>
  </#if>
  <#if slLine?trim != "" || ptLine?trim != "">
    <#if tradingOptionUsed("UseInitialSLPT")>if (UseInitialSLPT)
				{
				${slLine?trim}
				${ptLine?trim}
				}
    <#else>${slLine?trim}
				${ptLine?trim}</#if>
  </#if>
</#macro>

<#macro printPendingSLPTArm block>
  <#local dir = getParam(block, "#Direction#", "1") />
  <#local pos><#if dir != "-1">Long<#else>Short</#if></#local>
  <#local pfx><#if dir != "-1">sqLong<#else>sqShort</#if></#local>
  <@resolveSLPT block "SL" "#StopLoss.StopLoss#" />
  <#local slLine = "" />
  <#if slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode != "">
    <#local slLine><@printPendingSLLines block pfx true /></#local>
  </#if>
  <@resolveSLPT block "PT" "#ProfitTarget.ProfitTarget#" />
  <#local ptLine = "" />
  <#if slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode == "CalculationMode.Percent">
    <#local ptLine><@printPendingPercentLines block pfx "PT" slptVal true /></#local>
  <#elseif slptFkey != "" && slptFkey != "SQ.Formulas.SLPT.None" && slptMode != "">
    <#local ptLine>SetProfitTarget(<@printSignalName block />, ${slptMode}, ${slptVal});${slptMmNote}
					SetProfitTarget(<@printSignalName block "F" />, ${slptMode}, ${slptVal});</#local>
  </#if>
  <#local key = dir + "|" + slLine?trim + "|" + ptLine?trim />
  <#if (slLine?trim != "" || ptLine?trim != "") && !emSeenPendingSLPT?seq_contains(key)>
    <#assign emSeenPendingSLPT = emSeenPendingSLPT + [key] />
			if (${pfx}PendOrigin && Position.MarketPosition == MarketPosition.${pos} && !${pfx}SLPTArmed)
			{
				<#if tradingOptionUsed("UseInitialSLPT")>if (UseInitialSLPT)
				{
					${slLine?trim}
					${ptLine?trim}
				}
				<#else>${slLine?trim}
				${ptLine?trim}</#if>
				${pfx}SLPTArmed = true;
				${pfx}PendOrigin = false;
			}
			if (Position.MarketPosition == MarketPosition.Flat)
			{
				${pfx}SLPTArmed = false;
			}
  </#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  MoveSL2BE -> moves the stop of the open position to break-even (entry +/- add-pips), the rule of
  StrategyQuant's MoveSL2BE.checkSL2BE evaluated on the completed bar:

    long : trigger && Close[0] >= newSL && (no stop || current stop < newSL)
    short: trigger && Close[0] <= newSL && (no stop || current stop > newSL)
    newSL = entry +/- add-pips, rounded to the tick

  The trigger depends on the formula of #MoveSL2BE#. A PriceLevel formula is an absolute price and the
  move is allowed once the ENTRY is at or beyond it (long: entry <= level). Every other formula is a
  distance, and the move is allowed once the close is that far in profit.

  The two guards keep the move from placing a stop on the wrong side of the market (add-pips larger
  than the trigger) and from pulling back a stop that already protects more than break-even (a
  trailing stop or a Move SL action). The current stop comes from sqCurrentStop, which reads the live
  stop orders tracked by OnOrderUpdate.

  Emitted once per distinct (formula kind, level, offset): the block handles both directions itself,
  and a second copy would land after the timed-exit push in the last pass and undo it.

  The stop is addressed through sqLongEntrySignal / sqShortEntrySignal - the entry signal that filled -
  because a pending entry block owns two signal names and a literal would miss the market fallback.

  Generates, for a FixedValue trigger of 40 pips and no add-pips:

    if (Position.MarketPosition == MarketPosition.Long)
    {
        double sqBeNewLong = sqRoundPrice(Position.AveragePrice + (0));
        if (Close[0] - Position.AveragePrice >= 40 * SqPip
            && Close[0] >= sqBeNewLong
            && !(sqCurrentStop(true) >= sqBeNewLong))
            SetStopLoss(sqLongEntrySignal, CalculationMode.Price, sqBeNewLong, false);
    }
    (and the mirrored short branch)
-->
<#-- The break-even settings of an entry action, as a comparable signature ("none" without a break-even). -->
<#function beSignature a>
  <#if !hasExitMethod(a, "#MoveSL2BE.MoveSL2BE#")><#return "none" /></#if>
  <#local s = "" />
  <#list a.* as p>
    <#if p.@key == "#MoveSL2BE.MoveSL2BE#" || p.@key == "#MoveSL2BE.SL2BEAddPips#">
      <#if p.Formula[0]??>
        <#local s = s + p.@key + "=" + p.Formula[0].@key + ":" + leafValues(p.Formula[0]) + ";" />
      <#else>
        <#local s = s + p.@key + "=" + leafValues(p) + ";" />
      </#if>
    </#if>
  </#list>
  <#return s />
</#function>

<#-- The text of every leaf element under a node, in document order, as one string. -->
<#function leafValues node>
  <#local s = "" />
  <#local leaf = true />
  <#list node?children as c>
    <#if c?node_type == "element">
      <#local leaf = false />
      <#if c.@key[0]??><#local s = s + c.@key[0] /><#else><#local s = s + c?node_name /></#if>
      <#local s = s + "(" + leafValues(c) + ")" />
    </#if>
  </#list>
  <#if leaf><#return node?string?trim /></#if>
  <#return s />
</#function>

<#-- True when an entry action of the other direction carries a different break-even (or none). The block
     then acts on its own action's direction only; when both directions carry the same break-even one block
     serves both. -->
<#function beIsDirectional a>
  <#local dir = marketEntryDir(a) />
  <#local sig = beSignature(a) />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#local x = action />
            <#if x?node_name == "Block"><#local x = x?children[0] /></#if>
            <#if hasParamKey(x, "#MoveSL2BE.MoveSL2BE#") && marketEntryDir(x) != dir && beSignature(x) != sig>
              <#return true />
            </#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <#return false />
</#function>

<#-- True when a pending entry block has a price-level stop loss, which the arming reads again after the fill. -->
<#function hasPendingLevelStop>
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#list ["Then", "Else"] as branch>
          <#if rule[branch][0]??>
            <#list rule[branch].* as action>
              <#local a = action />
              <#if a?node_name == "Block"><#local a = a?children[0] /></#if>
              <#if (a.@key?string == "EnterAtStop" || a.@key?string == "EnterAtLimit")
                  && formulaKeyOf(a, "#StopLoss.StopLoss#") == "SQ.Formulas.SLPT.PriceLevel">
                <#return true />
              </#if>
            </#list>
          </#if>
        </#list>
      </#list>
    </#if>
  </#list>
  <#return false />
</#function>

<#function hasParamKey a key>
  <#list a.* as p><#if p.@key == key><#return true /></#if></#list>
  <#return false />
</#function>

<#macro printMoveSL2BEManage block>
  <#local lvl><@printRangeLevelPrice block "#MoveSL2BE.MoveSL2BE#" /></#local>
  <#local add><@printRangeLevelPrice block "#MoveSL2BE.SL2BEAddPips#" /></#local>
  <#local isLevel = isPriceLevelFormula(block, "#MoveSL2BE.MoveSL2BE#") />
  <#local own = emOwnerCond(block) />
  <#local isShortAction = marketEntryDir(block) == "-1" />
  <#local directional = own != "" || beIsDirectional(block) />
  <#local key = isLevel?string("level", "distance") + "|" + lvl?trim + "|" + add?trim + own + directional?string(isShortAction?string("|S", "|L"), "") />
  <#if !emSeenMoveSL2BE?seq_contains(key)>
    <#assign emSeenMoveSL2BE = emSeenMoveSL2BE + [key] />
    <#global sqUsesSetEveryStop = true>
    <#-- StrategyQuant attaches the break-even to the order the entry action opened, never to a position of
         the other direction. With ownership tracked, or when the two directions carry different break-evens,
         the block acts on its own action's direction only. -->
    <#if !directional || !isShortAction>
			if (Position.MarketPosition == MarketPosition.Long${own})
			{
				double sqBeNewLong = sqRoundPrice(Position.AveragePrice + (${add}));
				<#-- StrategyQuant tests the entry against the break-even LEVEL, rounded to the tick (checkSL2BE:
				     fixPrice(price - distance)), not the raw distance: an ATR distance a fraction of a tick above the
				     profit still triggers. -->
				if (<#if isLevel>Position.AveragePrice <= sqRoundPrice(${lvl})<#else>Position.AveragePrice <= sqRoundPrice(Close[0] - (${lvl}))</#if>
					&& Close[0] >= sqBeNewLong
					&& !sqTrailMovedThisBar<#if hasPendingLevelStop()>
					&& sqLongLevelRereadBar != CurrentBar</#if>
					&& !sqSetEveryStop(true, sqBeNewLong, true)
					&& !(sqCurrentStop(true) >= sqBeNewLong))
					SetStopLoss(sqLongEntrySignal, CalculationMode.Price, sqBeNewLong, false);
			}
    </#if>
    <#if !directional || isShortAction>
			<#if !directional>else </#if>if (Position.MarketPosition == MarketPosition.Short${own})
			{
				double sqBeNewShort = sqRoundPrice(Position.AveragePrice - (${add}));
				if (<#if isLevel>Position.AveragePrice >= sqRoundPrice(${lvl})<#else>Position.AveragePrice >= sqRoundPrice(Close[0] + (${lvl}))</#if>
					&& Close[0] <= sqBeNewShort
					&& !sqTrailMovedThisBar<#if hasPendingLevelStop()>
					&& sqShortLevelRereadBar != CurrentBar</#if>
					&& !sqSetEveryStop(false, sqBeNewShort, true)
					&& !(sqCurrentStop(false) <= sqBeNewShort))
					SetStopLoss(sqShortEntrySignal, CalculationMode.Price, sqBeNewShort, false);
			}
    </#if>
  </#if>
</#macro>
