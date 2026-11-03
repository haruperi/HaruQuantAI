<#--
  ============================================================================
  TradingOptions.inc - trading-options subsystem (NinjaTrader).
  ============================================================================
  Time/count-based constraints on entries (don't trade on weekends, only in a
  time window, ...). Modelled on EasyLanguage/TradingOptions.inc (inline _code
  model): each option emits a C# block in OnBarUpdate (before the rules) that may
  set `openingOrdersAllowed = false` (gate) and/or close positions. Entry actions
  are guarded by `if (openingOrdersAllowed)` (EnterAtMarket.tpl).

  Contract:
    - printTradingOptionsVariables : class fields for the selected options
    - printTradingOptionsCode      : per-bar gate/exit code (OnBarUpdate, pre-rules)
    - printTradingOptionBoolValue / IntValue / TimeValue : read TradingOptions params
  Time params are stored in SECONDS from midnight -> converted to an HHMM int
  (convertSecondsToHHMM), compared against Time[0].Hour*100 + Time[0].Minute.
  Graceful: an option without a _variables/_code .tpl emits nothing via
  <#attempt> (so strategies using other options still generate).
-->
<@tradingOptionsLoad />

<#-------------------------------------------------------------->
<#-- Load the available trading options (names) from the strategy XML. -->
<#macro tradingOptionsLoad>
	<#assign tradingOptions = [] />
	<#if doc.StrategyFile.AvailableTradingOptions[0]??>
		<#list doc.StrategyFile.AvailableTradingOptions.* as option>
			<#if option?string?trim != "StockpickerOptions">
				<#assign tradingOptions = tradingOptions + [option?string?trim] />
			</#if>
		</#list>
	</#if>
</#macro>

<#-------------------------------------------------------------->
<#-- True when the strategy carries the given trading option (by class name). -->
<#function tradingOptionUsed name><#return tradingOptions?seq_contains(name) /></#function>

<#-------------------------------------------------------------->
<#-- True when the given trading-option parameter key is present in the strategy XML.
     Needed for dual-schema options (MinMaxSLPT stores either the legacy combined
     MinimumSLPT/MaximumSLPT keys or the split MinimumSL/MaximumSL/MinimumPT/MaximumPT keys). -->
<#function tradingOptionKeyExists className keyName>
	<#list doc.StrategyFile.TradingOptions.Params.* as option>
		<#if option.@className == className && option.@key == keyName><#return true /></#if>
	</#list>
	<#return false />
</#function>

<#-------------------------------------------------------------->
<#-- Emit the selected options' C# field declarations into the class body. -->
<#macro printTradingOptionsVariables><#list tradingOptions as option><#attempt>
<#include "/NinjaTrader/TradingOptions/" + option + "_variables.tpl">
<#recover></#attempt></#list></#macro>

<#-------------------------------------------------------------->
<#-- Emit the selected options' per-bar gate/exit code (OnBarUpdate, before rules). -->
<#macro printTradingOptionsCode><#list tradingOptions as option><#attempt>
<#include "/NinjaTrader/TradingOptions/" + option + "_code.tpl">
<#recover></#attempt></#list></#macro>

<#-------------------------------------------------------------->
<#-- Read a boolean trading-option parameter (className/key); default false. -->
<#macro printTradingOptionBoolValue className keyName><@compress_single_line>
<#local found = false />
<#list doc.StrategyFile.TradingOptions.Params.* as option>
	<#if option.@className == className && option.@key == keyName>${option}<#local found = true /></#if>
</#list>
<#if !found>false</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- Read an integer trading-option parameter (className/key); default 0. -->
<#macro printTradingOptionIntValue className keyName><@compress_single_line>
<#local found = false />
<#list doc.StrategyFile.TradingOptions.Params.* as option>
	<#if option.@className == className && option.@key == keyName>${option}<#local found = true /></#if>
</#list>
<#if !found>0</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- NinjaTrader's warm-up gate, taken from the SQX "Reserved bars" trading option.

     BarsRequiredToTrade is NinjaTrader's own equivalent of reserved bars: the strategy does not trade
     until the series has that many bars. SQX shifts its backtest starting bar by the same value
     (TradingSetup.initInternalSettings via Engines.hasReservedBarsOption), so emitting it here is what
     keeps the exported strategy and the SQX simulation warming up over the same window - without it
     the platform would wait 20 bars while SQX waited for whatever the user set.

     No other engine exports this option: there is no ReservedBars template anywhere under Code/, and
     EasyLanguage emits no MaxBarsBack, so on TradeStation/MultiCharts the setting stays advisory (its
     help text asks the user to mirror it by hand). NinjaTrader is the one platform that can close that
     loop, so this macro has no sibling to be diffed against.

     Default 20 = NinjaTrader's own default, used when the strategy carries no Reserved bars option.
     Clamped to >= 1: NinjaTrader rejects 0, and a hand-edited .sqx can carry anything.

     The value is emitted UNCHANGED: SQX and NinjaTrader count the warm-up window the same way, so
     any offset would move NinjaTrader's first fill off the bar SQX first trades on. -->
<#macro printBarsRequiredToTrade><@compress_single_line>${sqReservedBars()?c}</@compress_single_line></#macro>

<#-- The BarsRequiredToTrade value as a number. The read macros (printSeriesAtOffset, Parameters.inc)
     use it too: an offset within it is always in range where the rules run.
     Returns: the ReservedBars trading option, 20 without one, at least 1; e.g. 250. -->
<#function sqReservedBars>
<#local barsRequired = 20 />
<#list doc.StrategyFile.TradingOptions.Params.* as option>
	<#if option.@className == "ReservedBars" && option.@key == "ReservedBars">
		<#attempt><#local barsRequired = option?string?trim?number?round /><#recover></#attempt>
	</#if>
</#list>
<#if barsRequired < 1><#local barsRequired = 1 /></#if>
<#return barsRequired>
</#function>

<#-------------------------------------------------------------->
<#--
  Emit the NinjaScript session-close settings, derived from the strategy's trading options.
  Both lines are produced here so the flag and its companion
  can never disagree.

  StrategyQuant NEVER force-closes a position at a session boundary: the Session trading
  option only names a session (SessionOption.java carries nothing else) and no simulator
  reads it for exits. So the only setting that legitimately wants NinjaTrader's own
  session-close exit is ExitAtEndOfDay with NO exit time - the case ExitAtEndOfDay_code.tpl
  itself delegates ("DayExitTime=0 -> handled by the default IsExitOnSessionCloseStrategy").
  Everything else must emit false; NinjaTrader's own default is true, so it has to be
  written out explicitly.

  The time is read with the SAME macro ExitAtEndOfDay_variables.tpl uses, so this decision
  and the emitted DayExitTime can never diverge (both default to 0800 when the parameter is
  absent, which correctly keeps the flag false).
-->
<#macro printSessionCloseSettings>
<#local eod><@printTradingOptionBoolValue "ExitAtEndOfDay" "ExitAtEndOfDay" /></#local>
<#local exitTime><@printTradingOptionTimeValue "ExitAtEndOfDay" "EODExitTime" /></#local>
<#if eod?trim == "true" && exitTime?trim == "0">
IsExitOnSessionCloseStrategy	= true;
				ExitOnSessionCloseSeconds	= 30;
<#else>
IsExitOnSessionCloseStrategy	= false;
</#if>
</#macro>

<#-------------------------------------------------------------->
<#-- Read a time trading-option parameter (seconds from midnight) as an HHMM int; default 0800. -->
<#macro printTradingOptionTimeValue className keyName><@compress_single_line>
<#local found = false /><#local value = "" />
<#list doc.StrategyFile.TradingOptions.Params.* as option>
	<#if option.@className == className && option.@key == keyName><#local found = true /><#local value = option /></#if>
</#list>
<#if !found>800<#else><@convertSecondsToHHMM value /></#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- Convert seconds-from-midnight to an HHMM integer (e.g. 28800 -> 800, 81000 -> 2230). -->
<#macro convertSecondsToHHMM value><@compress_single_line>
<#if value == "" || value == "NaN">0<#else>
<#local hh = (value?number / 3600)?floor />
<#local mm = ((value?number - (hh * 3600)) / 60)?floor />
${(hh * 100 + mm)?c}
</#if>
</@compress_single_line></#macro>
