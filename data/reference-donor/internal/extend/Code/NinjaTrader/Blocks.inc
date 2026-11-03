<#--
  ============================================================================
  Blocks.inc - strategy-XML traversal and block-template dispatch (NinjaTrader).
  ============================================================================
  This file turns the strategy XML tree into NinjaScript source code. It walks
  the <Rules>/<Events> tree, emits one C# rule per <Rule>, and for every building
  block invokes the matching blocks/<key>.tpl template.

  Pattern: ported from EasyLanguage/Blocks.inc, rewritten to C# control flow
  (if (cond) { actions }) instead of EasyLanguage (if cond then begin ... end).

  Supported rule types: IfThen, IfThenElse, ActionOnly, Signal. A building block
  without a blocks/<key>.tpl REFUSES the export, naming the block - see printBlock
  below.
-->

<#-------------------------------------------------------------->
<#--
  Emit all rules of a single strategy event (e.g. "OnBarUpdate").
  @param eventName  XML event key to render (matches <Event key="...">).
  Generates: the concatenated C# of every <Rule> in that event (or nothing
  if the event is absent / empty).
-->
<#macro printRulesForEvent eventName>
<#-- Scan every <Event> and render only the one whose key matches. -->
<#list doc.StrategyFile.Strategy.Rules.Events.* as event>
	<#if event.@key == eventName>
		<#list event.* as rule>
<@printRule rule />
		</#list>
	</#if>
</#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  Render one <Rule> as a C# statement, dispatching on its @type attribute.
  @param rule  the <Rule> XML node.
  Generates (per type):
    IfThen / IfThenElse -> if (<conditions>) { <actions> } [else { ... }]
    ActionOnly          -> <actions> (no guarding condition)
    Signal              -> <var> = <condition>;   (assignment of a boolean signal)
  Empty rules (isNonemptyRule == false) are skipped.
-->
<#macro printRule rule>
<#if (rule.@type == "IfThen" || rule.@type == "IfThenElse") && isNonemptyRule(rule) == true>
			// Rule: ${rule.@name}
<#-- Conditions are wrapped in compress_single_line so the boolean expression
     stays on one line; actions below keep their own lines. -->
			if (<@compress_single_line><#list rule.If.* as block><@printBlock block /></#list></@compress_single_line>)
			{
				<#list rule.Then.* as block><@printBlock block />
				</#list>
			}
<#if rule.@type == "IfThenElse">
			else
			{
				<#list rule.Else.* as block><@printBlock block />
				</#list>
			}
</#if>
<#elseif rule.@type == "ActionOnly" && isNonemptyRule(rule) == true>
			// Rule: ${rule.@name}
			<#list rule.Then.* as block><@printBlock block />
			</#list>
<#elseif rule.@type == "Signal">
			// Rule: ${rule.@name}
<#-- Each signal assigns the result of its condition block to a strategy variable. -->
			<#list rule.signals.* as signal>
			<@printVariableName signal.@variable /> = <#if signal?children[0]??><@printBlock signal?children[0] /><#else>false</#if>;
			</#list>
</#if>
</#macro>

<#--
  Blocks whose NinjaTrader template routes #Chart# to the selected data series - either
  through printInput/printComputedFrom (native-indicator family) or through printSeries
  (price/time primitives), or through an sq* helper that takes a leading data-series index,
  reads its bars through sqHigh/sqLow/sqClose(ci, ...) and keeps its state per series. Any
  OTHER block asked to read a secondary series (#Chart# != 0) emits a LOUD marker identifier
  instead of silently computing from the primary chart. When a template gains proper routing,
  add it here - the CodeGen marker test guards the negative path.

  A block belongs on this list for one of two reasons:
    - ROUTED: it computes over the series its #Chart# names. For a composite template this
      includes every price term next to the indicator (e.g. the Bar Opens/Closes variants read
      their Open/Close through printSeries), and every sq* helper it reaches, directly or
      through another helper, must be series-aware.
    - CHART-AGNOSTIC: its value does not depend on a chart at all, so it deliberately keeps reading
      the primary series. These are AccountEquity, OpenPLInMoney/InPips, TradeRecentlyClosed,
      LogToFile, DrawUp/DownArrow and the Current* time family. Routing them would make them WORSE,
      not better: account P/L needs the freshest price and Current* means "now", whereas a secondary
      series only offers its last COMPLETED bar. Contrast the Bar* time family, which means
      "bar N of THIS chart" and IS routed.

  The loud marker is the guard for any NEW block whose helper is not series-aware.
-->
<#assign CHART_ROUTED_BLOCKS = {
  "ADX":1, "ADXChangesDown":1, "ADXChangesUp":1, "ADXCrossDown":1, "ADXCrossUp":1, "ADXFalling":1,
  "ADXHigher":1, "ADXLower":1, "ADXRising":1, "AND":1, "ATR":1, "ATRChangesDown":1,
  "ATRChangesUp":1, "ATRCrossDown":1, "ATRCrossUp":1, "ATRFalling":1, "ATRHigher":1, "ATRLower":1,
  "ATRRising":1, "AVWAPCloseAboveAnchoredVWAP":1, "AVWAPCloseAboveAnchoredVWAPUpper":1, "AVWAPCloseBelowAnchoredVWAP":1, "AVWAPCloseBelowAnchoredVWAPLower":1, "AVWAPCloseCrossesAboveAnchoredVWAPLower":1,
  "AVWAPCloseCrossesAboveAnchoredVWAPUpper":1, "AVWAPCloseCrossesBelowAnchoredVWAPLower":1, "AVWAPCloseCrossesBelowAnchoredVWAPUpper":1, "AVWAPFastAnchoredVWAPAboveSlowAnchoredVWAP":1, "AVWAPFastAnchoredVWAPBelowSlowAnchoredVWAP":1, "AWOChangesDown":1,
  "AWOChangesUp":1, "AWOCrossDown":1, "AWOCrossUp":1, "AWOFalling":1, "AWOHigher":1, "AWOLower":1,
  "AWORising":1, "Abs":1, "AccountBalance":1, "AccountEquity":1, "AlwaysFalse":1, "AlwaysTrue":1,
  "AnchoredVWAP":1, "AnchoredVWAPFalling":1, "AnchoredVWAPRising":1, "Aroon":1, "AroonCrossesAbove":1, "AroonCrossesBelow":1,
  "AroonDownRiseFromBottom":1, "AroonFallFromTop":1, "AroonRiseFromBottom":1, "AroonUpFallFromTop":1, "Ask":1, "AssignVariable":1,
  "AvgVolume":1, "AvgVolumeFalling":1, "AvgVolumeRising":1, "AwesomeOscillator":1, "BBBarClosesAboveDown":1, "BBBarClosesAboveUp":1,
  "BBBarClosesBelowDown":1, "BBBarClosesBelowUp":1, "BBBarOpensAboveDown":1, "BBBarOpensAboveDownAfterOpenBelow":1, "BBBarOpensAboveUp":1, "BBBarOpensAboveUpAfterOpenBelow":1,
  "BBBarOpensBelowDown":1, "BBBarOpensBelowDownAfterOpenAbove":1, "BBBarOpensBelowUp":1, "BBBarOpensBelowUpAfterOpenAbove":1, "BBLowerFalling":1, "BBLowerRising":1,
  "BBRange":1, "BBUpperFalling":1, "BBUpperRising":1, "BBWidthRatio":1, "BEPChangesDown":1, "BEPChangesUp":1,
  "BEPCrossDown":1, "BEPCrossUp":1, "BEPFalling":1, "BEPHigher":1, "BEPLower":1, "BEPRising":1,
  "BUPChangesDown":1, "BUPChangesUp":1, "BUPCrossDown":1, "BUPCrossUp":1, "BUPFalling":1, "BUPHigher":1,
  "BUPLower":1, "BUPRising":1, "BarClosesAboveKAMA":1, "BarClosesAboveSuperTrend":1, "BarClosesBelowKAMA":1, "BarClosesBelowSuperTrend":1,
  "BarDate":1, "BarDayOfMonth":1, "BarDayOfWeek":1, "BarDayOfWeekIs":1, "BarDayOfWeekIsNot":1, "BarHour":1,
  "BarHourIs":1, "BarHourIsBigger":1, "BarHourIsSmaller":1, "BarMinute":1, "BarMinuteIs":1, "BarMonth":1,
  "BarMonthIs":1, "BarMonthIsNot":1, "BarOpensAboveHighestAfterOpenBelow":1, "BarOpensAboveLowestAfterOpenBelow":1, "BarOpensBelowHighestAfterOpenAbove":1, "BarOpensBelowLowestAfterOpenAbove":1,
  "BarRange":1, "BarTime":1, "BarTimeIs":1, "BarsSinceOrderClosed":1, "BarsSinceOrderOpen":1, "BearishEngulfing":1,
  "BearsPower":1, "Bid":1, "BiggestRange":1, "BollingerBands":1, "Boolean":1, "BooleanVariable":1,
  "BullishEngulfing":1, "BullsPower":1, "CBlock":1, "CCI":1, "CCIChangesDown":1, "CCIChangesUp":1,
  "CCICrossDown":1, "CCICrossUp":1, "CCIFalling":1, "CCIHigher":1, "CCILower":1, "CCIRising":1,
  "COT52vs156ShiftBearish":1, "COT52vs156ShiftBullish":1, "COTAccumulationBearish":1, "COTAccumulationBullish":1,
  "COTBearishExtreme":1, "COTBullishExtreme":1, "COTCompositeScore":1, "COTConvergence":1,
  "COTCpihedg":1, "COTCpispec":1, "COTCpismall":1, "COTCrossFieldSpread":1, "COTCrowdingUnwind":1, "COTCtihedg":1, "COTCtispec":1, "COTExtremePersistence":1,
  "COTEmergencyExitLong":1, "COTExtremeExitBearish":1, "COTExtremeExitBullish":1, "COTExtremeUnwindBearish":1, "COTExtremeUnwindBullish":1,
  "COTFieldValue":1, "COTFullCycleExitLong":1, "COTFullCycleExitShort":1, "COTFullCycleLong":1, "COTFullCycleShort":1,
  "COTHedgerAccelBearish":1, "COTHedgerAccelBullish":1, "COTHedgerDivConfBearish":1, "COTHedgerDivConfBullish":1, "COTHedgerSpecSpread":1,
  "COTHigherLow":1, "COTLowerHigh":1, "COTMomentum":1, "COTMomentumRevBearish":1, "COTMomentumRevBullish":1,
  "COTMultiFieldCombo":1, "COTMultiWindowBearish":1, "COTMultiWindowBullish":1, "COTNeutralZone":1,
  "COTRegimeShiftBearish":1, "COTRegimeShiftBullish":1, "COTRocBearish":1, "COTRocBullish":1,
  "COTScoreAbove":1, "COTScoreAccelBearish":1, "COTScoreAccelBullish":1, "COTScoreBelow":1,
  "COTScoreMomentumAbove":1, "COTScoreMomentumBelow":1, "COTScoreZeroCrossDown":1, "COTScoreZeroCrossUp":1,
  "COTSeasonalBearish":1, "COTSeasonalBullish":1, "COTSmallFadeBearish":1, "COTSmallFadeBullish":1,
  "COTSmartDumbBearish":1, "COTSmartDumbBullish":1, "COTSpecExhaustionLong":1, "COTSpecExhaustionShort":1,
  "COTSpecTrendLong":1, "COTSpecTrendShort":1, "COTSpreadZScoreBearish":1, "COTSpreadZScoreBullish":1,
  "COTTripleDivBearish":1, "COTTripleDivBullish":1, "COTVixProxyBearish":1, "COTVixProxyBullish":1,
  "CDataIndy":1, "Close":1, "CloseAboveVWAP":1, "CloseAllPendingOrders":1, "CloseAllPositions":1, "CloseBelowVWAP":1,
  "CloseBestPosition":1, "CloseD":1, "CloseM":1, "ClosePendingOrder":1, "ClosePosition":1, "CloseW":1,
  "CloseWorstPosition":1, "ClosedPLInMoney":1, "ClosedPLInPips":1, "ConvertToPips":1, "ConvertToRealPips":1, "CrossesAbove":1,
  "CrossesBelow":1, "CurrentBar":1, "CurrentDate":1, "CurrentDayOfWeek":1, "CurrentDayOfWeekIs":1, "CurrentHour":1,
  "CurrentHourIs":1, "CurrentMinute":1, "CurrentMinuteIs":1, "CurrentMonth":1, "CurrentMonthIs":1, "CurrentTime":1,
  "CurrentTimeIs":1, "CustomAction":1, "CustomFunction":1, "DEMChangesDown":1, "DEMChangesUp":1, "DEMCrossDown":1,
  "DEMCrossUp":1, "DEMFalling":1, "DEMHigher":1, "DEMLower":1, "DEMRising":1, "DICrossDown":1,
  "DICrossUp":1, "DIMinusChangesDown":1, "DIMinusChangesUp":1, "DIMinusFalling":1, "DIMinusRising":1, "DIPlusChangesDown":1,
  "DIPlusChangesUp":1, "DIPlusFalling":1, "DIPlusHigher":1, "DIPlusLower":1, "DIPlusRising":1, "DarkCloud":1,
  "DataLoggingIndy":1, "DeMarker":1, "Division":1, "Doji":1, "DoubleVariable":1, "DrawDownArrow":1,
  "DrawUpArrow":1, "DrawVerticalLine":1, "EMA":1, "EnterAtLimit":1, "EnterAtMarket":1, "EnterAtStop":1,
  "EnterReverseAtMarket":1, "Equals":1, "Exponential":1, "FastKAMAAboveSlowKAMA":1, "FastKAMABelowSlowKAMA":1, "FastReflexCrossDownSlowReflex":1,
  "FastReflexCrossUPSlowReflex":1, "FastVWAPAboveSlowVWAP":1, "FastVWAPBelowSlowVWAP":1, "FasterHMAIsAboveSlowerHMA":1, "FasterHMAIsBelowSlowerHMA":1, "Fibo":1,
  "FixedPips":1, "Fractal":1, "GannHiLo":1, "GannHiLoDownTrend":1, "GannHiLoUPTrend":1, "GetDate":1,
  "GetTime":1, "HMAChangesDown":1, "HMAChangesUP":1, "HMAFalling":1, "HMARising":1, "Hammer":1,
  "HeikenAshi":1, "HeikenAshiClose":1, "HeikenAshiHigh":1, "HeikenAshiLow":1, "HeikenAshiOpen":1, "High":1,
  "HighD":1, "HighM":1, "HighW":1, "Highest":1, "HighestInRange":1, "HighestIndex":1,
  "HullMovingAverage":1, "Ichimoku":1, "IchimokuKijunSenCrossBearish":1, "IchimokuKijunSenCrossBullish":1, "IchimokuKumoBreakoutBearish":1, "IchimokuKumoBreakoutBullish":1,
  "IchimokuSenkouSpanCrossBearish":1, "IchimokuSenkouSpanCrossBullish":1, "IchimokuTenkanKijunCrossBearish":1, "IchimokuTenkanKijunCrossBullish":1, "IndicatorHighest":1, "IndicatorLowest":1,
  "IntVariable":1, "IsBarOpen":1, "IsBearishFractal":1, "IsBullishFractal":1, "IsDowntrend":1, "IsFalling":1,
  "IsGreater":1, "IsGreaterCount":1, "IsGreaterOrEqual":1, "IsGreaterPercentil":1, "IsLower":1, "IsLowerCount":1,
  "IsLowerOrEqual":1, "IsLowerPercentil":1, "IsMonthFirstTradingDay":1, "IsMonthLastTradingDay":1, "IsRising":1, "IsUptrend":1,
  "KAMA":1, "KAMAFalling":1, "KAMARising":1, "KCBarClosesAboveLower":1, "KCBarClosesAboveUpper":1, "KCBarClosesBelowLower":1,
  "KCBarClosesBelowUpper":1, "KCBarOpensAboveLower":1, "KCBarOpensAboveLowerAfterOpenBelow":1, "KCBarOpensAboveUpper":1, "KCBarOpensAboveUpperAfterOpenBelow":1, "KCBarOpensBelowLower":1,
  "KCBarOpensBelowLowerAfterOpenAbove":1, "KCBarOpensBelowUpper":1, "KCBarOpensBelowUpperAfterOpenAbove":1, "KCLowerFalling":1, "KCLowerRising":1, "KCUpperFalling":1,
  "KCUpperRising":1, "KERaboveLevel":1, "KERbelowLevel":1, "KaufmanEfficiencyRatio":1, "KeltnerChannel":1, "LWMA":1,
  "LaguerreRSI":1, "LaguerreRSIChangesDown":1, "LaguerreRSIChangesUP":1, "LaguerreRSICrossDown":1, "LaguerreRSICrossUP":1, "LaguerreRSIFalling":1,
  "LaguerreRSIRising":1, "LastOrderWas":1, "LastOrderWasNot":1, "LinRegBarClosesAbove":1, "LinRegBarClosesBelow":1, "LinRegBarOpensAbove":1,
  "LinRegBarOpensAboveAfterOpenBelow":1, "LinRegBarOpensBelow":1, "LinRegBarOpensBelowAfterOpenAbove":1, "LinRegFalling":1, "LinRegRising":1, "LinearRegression":1,
  "LogToFile":1, "LogToJournal":1, "Logarithm":1, "Low":1, "LowD":1, "LowM":1,
  "LowW":1, "Lowest":1, "LowestInRange":1, "LowestIndex":1, "MABarClosesAbove":1, "MABarClosesBelow":1,
  "MABarOpensAbove":1, "MABarOpensAboveAfterOpenBelow":1, "MABarOpensBelow":1, "MABarOpensBelowAfterOpenAbove":1, "MACD":1, "MACDMainChangesDown":1,
  "MACDMainChangesUp":1, "MACDMainCrossAbove":1, "MACDMainCrossAboveSignal":1, "MACDMainCrossAboveZero":1, "MACDMainCrossBelow":1, "MACDMainCrossBelowSignal":1,
  "MACDMainCrossBelowZero":1, "MACDMainFalling":1, "MACDMainHigher":1, "MACDMainHigherSignal":1, "MACDMainHigherZero":1, "MACDMainLower":1,
  "MACDMainLowerSignal":1, "MACDMainLowerZero":1, "MACDMainRising":1, "MACDSignalFalling":1, "MACDSignalRising":1, "MAFalling":1,
  "MARising":1, "MTATR":1, "MTKeltnerChannel":1, "MarketPosition":1, "MarketPositionIsFlat":1, "MarketPositionIsLong":1,
  "MarketPositionIsNotLong":1, "MarketPositionIsNotShort":1, "MarketPositionIsShort":1, "MarketPositionSize":1, "MarketPositionsCount":1, "Maximum":1,
  "Minimum":1, "Minus":1, "MomChangesDown":1, "MomChangesUp":1, "MomCrossDown":1, "MomCrossUp":1,
  "MomFalling":1, "MomHigher":1, "MomLower":1, "MomRising":1, "Momentum":1, "MovingAverage":1,
  "Multiplication":1, "NoTradeRecentlyClosed":1, "Not":1, "NotEquals":1, "Number":1, "OR":1,
  "OSMA":1, "OSMAChangesDown":1, "OSMAChangesUp":1, "OSMACrossZeroDown":1, "OSMACrossZeroUp":1, "OSMAFalling":1,
  "OSMAHigherZero":1, "OSMALowerZero":1, "OSMARising":1, "Open":1, "OpenD":1, "OpenM":1,
  "OpenPLInMoney":1, "OpenPLInPips":1, "OpenW":1, "OrderOpenPrice":1, "OrderPT":1, "OrderSL":1,
  "PSARBarHigher":1, "PSARBarLower":1, "ParabolicSAR":1, "PendingOrderDoesntExist":1, "PendingOrderExists":1, "PiercingLine":1,
  "Pivots":1, "Plus":1, "QQE":1, "QQEValue1ChangesDown":1, "QQEValue1ChangesUp":1, "QQEValue1CrossAbove":1,
  "QQEValue1CrossAboveValue2":1, "QQEValue1CrossBelow":1, "QQEValue1CrossBelowValue2":1, "QQEValue1Falling":1, "QQEValue1Higher":1, "QQEValue1HigherValue2":1,
  "QQEValue1Lower":1, "QQEValue1LowerValue2":1, "QQEValue1Rising":1, "QQEValue2Falling":1, "QQEValue2Rising":1, "ROC":1,
  "ROCAboveLevel":1, "ROCBelowLevel":1, "ROCCrossesAboveLevel":1, "ROCCrossesBelowLevel":1, "ROCFalling":1, "ROCRising":1,
  "RSI":1, "RSIChangesDown":1, "RSIChangesUp":1, "RSICrossDown":1, "RSICrossUp":1, "RSIFalling":1,
  "RSIHigher":1, "RSILower":1, "RSIRising":1, "Reflex":1, "ReflexChangesDirectionDown":1, "ReflexChangesDirectionUP":1,
  "ReflexFalling":1, "ReflexRising":1, "Round":1, "SMA":1, "SMMA":1, "SRPercRankAboveLevel":1,
  "SRPercRankAboveLevelXBars":1, "SRPercRankBelowLevel":1, "SRPercRankBelowLevelXBars":1, "SRPercentRank":1, "SchaffTrendCycle":1, "SchaffTrendCycleAboveLevel":1,
  "SchaffTrendCycleBelowLevel":1, "SchaffTrendCycleCrossesAboveLevel":1, "SchaffTrendCycleCrossesBelowLevel":1, "SendEmail":1, "SessionClose":1, "SessionHigh":1,
  "SessionLow":1, "SessionOpen":1, "SetProfitTarget":1, "SetStopLoss":1, "ShootingStar":1, "SmallestRange":1,
  "Spread":1, "SpreadInPips":1, "SquareRoot":1, "StdDev":1, "StdDevChangesDown":1, "StdDevChangesUp":1,
  "StdDevCrossDown":1, "StdDevCrossUp":1, "StdDevFalling":1, "StdDevHigher":1, "StdDevLower":1, "StdDevRising":1,
  "StochFastKCrossDown":1, "StochFastKCrossUp":1, "StochFastKDown":1, "StochFastKUp":1, "StochSlowDChangesDown":1, "StochSlowDChangesUp":1,
  "StochSlowDCrossDown":1, "StochSlowDCrossUp":1, "StochSlowDFalling":1, "StochSlowDHigher":1, "StochSlowDLower":1, "StochSlowDRising":1,
  "Stochastic":1, "String":1, "SuperTrend":1, "SuperTrendDownTrend":1, "SuperTrendInRange":1, "SuperTrendUPTrend":1,
  "TEMA":1, "TPOProfile":1, "TradeRecentlyClosed":1, "TrueRange":1, "UlcerIndex":1, "UlcerIndexDownBelowSafeLevel":1,
  "UlcerIndexDownRising":1, "UlcerIndexUPBelowSafeLevel":1, "UlcerIndexUPRising":1, "VPBearAboveBull":1, "VPBottomHeavyPOC":1, "VPBullAboveBear":1,
  "VPExcessReversalLong":1, "VPExcessReversalShort":1, "VPFallingPOC":1, "VPHighDelta":1, "VPHighNegDelta":1, "VPIBBreakoutDown":1,
  "VPIBBreakoutUp":1, "VPIBRejectionLong":1, "VPIBRejectionShort":1, "VPLateAcceptanceFailureLong":1, "VPLateAcceptanceFailureShort":1, "VPNarrowValueArea":1,
  "VPOpenDriveLong":1, "VPOpenDriveShort":1, "VPPOCAtEdgeLong":1, "VPPOCAtEdgeShort":1, "VPPOCMagnetLong":1, "VPPOCMagnetShort":1,
  "VPPriceAbovePOC":1, "VPPriceBelowPOC":1, "VPPriceInsideVA":1, "VPPriceOutsideVA":1, "VPRisingPOC":1, "VPTopHeavyPOC":1,
  "VPVAHTestRejection":1, "VPVALTestRejection":1, "VPVWAPCrossDown":1, "VPVWAPCrossUp":1, "VPValueReturnLong":1, "VPValueReturnShort":1,
  "VPValueShiftDown":1, "VPValueShiftUp":1, "VPWideValueArea":1, "VWAP":1, "VWAPFalling":1, "VWAPRising":1,
  "Volume":1, "VolumeFalling":1, "VolumeProfile":1, "VolumeRising":1, "Vortex":1, "VortexChangesTrendDown":1,
  "VortexChangesTrendUP":1, "VortexDowntrend":1, "VortexUptrend":1, "WPRChangesDown":1, "WPRChangesUp":1, "WPRCrossDown":1,
  "WPRCrossUp":1, "WPRFalling":1, "WPRHigher":1, "WPRLower":1, "WPRRising":1, "WaveTrend":1,
  "WaveTrendMainChangesDown":1, "WaveTrendMainChangesUp":1, "WaveTrendMainCrossAbove":1, "WaveTrendMainCrossAboveSignal":1, "WaveTrendMainCrossAboveZero":1, "WaveTrendMainCrossBelow":1,
  "WaveTrendMainCrossBelowSignal":1, "WaveTrendMainCrossBelowZero":1, "WaveTrendMainFalling":1, "WaveTrendMainHigher":1, "WaveTrendMainHigherSignal":1, "WaveTrendMainHigherZero":1,
  "WaveTrendMainLower":1, "WaveTrendMainLowerSignal":1, "WaveTrendMainLowerZero":1, "WaveTrendMainRising":1, "WaveTrendSignalFalling":1, "WaveTrendSignalRising":1,
  "WilliamsPR":1, "WoodiesCCIZeroLineBreakDown":1, "WoodiesCCIZeroLineBreakUP":1, "WoodiesFamirDown":1, "WoodiesFamirUP":1, "WoodiesTrendDown":1,
  "WoodiesTrendUP":1, "WoodiesVegasTradeDown":1, "WoodiesVegasTradeUP":1, "WoodiesZLRDown":1, "WoodiesZLRUP":1
} />

<#-------------------------------------------------------------->
<#--
  Render a single building block to NinjaScript.
  @param block  the block XML node (either a wrapper <Block> or a leaf <Item>).
  @param shift  bar-offset propagated to the block (default "0" = current bar).
  Behaviour:
    - <Block> wrapper -> descend into its first child.
    - unresolved placeholder (#Value#/#Left#/#Right#) -> "/* undefined value */".
    - leaf <Item> -> include blocks/<key>.tpl. If that template does not exist the include
      THROWS, exactly as it does for MetaTrader 4/5, EasyLanguage, JForex and PseudoCode.
      The other five wrap it in <#if blockFileExists(key)>, which looks like a guard but is
      not - blockFileExists is a stub whose body is <#return true>, so the else branch that
      would print "!!! Template file missing !!!" is dead and the include throws there too.

      MissingBlockMessage turns that into "This strategy contains block '<key>' that is not
      implemented in NinjaScript." for the GUI, the CLI and the Save-to-files task alike.

      The export must refuse rather than degrade: a placeholder comment is not an expression,
      so a strategy carrying an unsupported block would come back as a .cs file that does not
      compile.

      Note this is NOT a coverage gap: every block the Builder offers for NinjaTrader has a
      template (testForEngineOfferCoverage). It happens when a strategy built for another
      engine - a block with @ForEngine("MT4,MT5,TS,MC") - is exported to NinjaScript, which
      is a legitimate thing for a user to try.
  Note: <#include> shares the enclosing macro's locals, so blocks/*.tpl can read
  the `block` and `shift` variables set here.
-->
<#--
  The blocks whose Java class extends IndicatorBlock. IndicatorBlock.evaluateBlock returns its value through
  SQUtils.round6, so inside an order price formula StrategyQuant sees every indicator already rounded to 6
  decimals, while value blocks (prices, numbers, arithmetic) stay unrounded. printPrice turns
  sqRound6Indicators on, and printBlock then wraps these blocks in sqRound(..., 6). Kept in step with the
  snippets by NinjaTraderIndicatorPackageTest.testRoundedIndicatorBlocksAreTheIndicatorBlockSnippets.
-->
<#assign INDICATOR_BLOCKS = {
  "ADX":1, "AnchoredVWAP":1, "Aroon":1, "ATR":1, "AvgVolume":1, "AwesomeOscillator":1, "BarRange":1, "BBRange":1,
  "BBWidthRatio":1, "BearsPower":1, "BiggestRange":1, "BollingerBands":1, "BullsPower":1, "CCI":1, "COTCompositeScore":1, "COTCpihedg":1,
  "COTCpismall":1, "COTCpispec":1, "COTCrossFieldSpread":1, "COTCtihedg":1, "COTCtispec":1, "COTFieldValue":1, "COTHedgerSpecSpread":1, "COTMomentum":1,
  "COTMultiFieldCombo":1, "DeMarker":1, "EMA":1, "Fibo":1, "Fractal":1, "GannHiLo":1, "HeikenAshi":1, "Highest":1,
  "HighestIndex":1, "HighestInRange":1, "HullMovingAverage":1, "Ichimoku":1, "KAMA":1, "KaufmanEfficiencyRatio":1, "KeltnerChannel":1, "LaguerreRSI":1,
  "LinearRegression":1, "Lowest":1, "LowestIndex":1, "LowestInRange":1, "LWMA":1, "MACD":1, "Momentum":1, "MovingAverage":1,
  "MTATR":1, "MTKeltnerChannel":1, "OSMA":1, "ParabolicSAR":1, "Pivots":1, "QQE":1, "Reflex":1, "ROC":1,
  "RSI":1, "SchaffTrendCycle":1, "SMA":1, "SmallestRange":1, "SMMA":1, "SRPercentRank":1, "StdDev":1, "Stochastic":1,
  "SuperTrend":1, "TEMA":1, "TrueRange":1, "UlcerIndex":1, "Vortex":1, "VWAP":1, "WaveTrend":1, "WilliamsPR":1
} />

<#macro printBlock block shift="0">
<#if block?node_name == "Block">
<@printBlock block?children[0] shift />
<#elseif (sqRound6Indicators!false) && INDICATOR_BLOCKS[block.@key]??>
<#-- The indicator's own inputs are series, not order prices: they are rendered unrounded. -->
<#global sqRound6Indicators = false>sqRound(<@printBlock block shift />, 6)<#global sqRound6Indicators = true>
<#else>
<#if block.@key == "#Value#" || block.@key == "#Left#" || block.@key == "#Right#">
/* undefined value */<#else>
<#local blockKey = block.@key />
<#-- Custom block / custom-data-indicator keys carry an id suffix (CBlock_<id>,
     CDataIndy_<id>); normalize to the bare template name. -->
<#if blockKey?starts_with("CBlock")><#local blockKey = "CBlock" /><#elseif blockKey?starts_with("CDataIndy")><#local blockKey = "CDataIndy" /></#if>
<#-- Legacy keys "And"/"Or": the Java block classes - and thus every Builder strategy - use
     upper-case AND/OR, and the template files are named after the Java classes (AND.tpl/OR.tpl).
     The lower-case forms are mapped so the include also resolves on a case-sensitive file
     system. -->
<#if blockKey == "And"><#local blockKey = "AND" /><#elseif blockKey == "Or"><#local blockKey = "OR" /></#if>
<#local chartIdx = getParam(block, "#Chart#", "0") />
<#if chartIdx != "0" && !CHART_ROUTED_BLOCKS[blockKey]??>SQ_SECONDARY_SERIES_NOT_SUPPORTED_${blockKey}<#else><#include "blocks/"+blockKey+".tpl"></#if>
</#if>
</#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  Render a named child operand of a block (used by comparison/cross blocks).
  @param block      the parent block whose children are searched.
  @param childName  the <Block key="..."> to render (e.g. "#Left#" / "#Right#").
  @param shift      bar-offset for the rendered operand (default "0").
  Generates: the NinjaScript of the matching operand, e.g. "SMA(Close, 10)[0]".
-->
<#--
  Comparison operand, rounded the way StrategyQuant rounds it.

  Every comparison block in SQ.Blocks.Comparisons puts its operands through
  SQUtils.round(value, 6) - IsGreater, IsLower, CrossesAbove/Below, Equals, IsRising/IsFalling and
  the rest; the Count and Percentil variants use 5. Comparing raw doubles instead would resolve any
  pair of values agreeing to within a rounding step differently on the two sides, which creates
  crossings StrategyQuant never sees.

  sqRound mirrors SQUtils.round exactly, including the 1e-10 epsilon before the half-up step.
-->
<#-- returnType of a child block's Item, or "" when there is none. Used to keep string operands out
     of sqRound: Equals/NotEquals also compare string constants, and sqRound("x", 6) is not C#. -->
<#function childReturnType block childName>
  <#list block?children as c>
    <#if c?node_name == "Block" && c.@key == childName>
      <#list c?children as g>
        <#if g?node_name == "Item"><#return (g.@returnType[0])!"" /></#if>
      </#list>
    </#if>
  </#list>
  <#return "" />
</#function>

<#macro printCmpOperand block childName shift="0" decimals="6"><@compress_single_line><#if childReturnType(block, childName) == "string"><@printBlockChild block childName shift /><#else>sqRound(<@printBlockChild block childName shift />, ${decimals})</#if></@compress_single_line></#macro>

<#macro printBlockChild block childName shift="0"><@compress_single_line>
<#list block?children as c>
	<#if c?node_name == "Block" && c.@key == childName>
		<@printBlock c shift />
	</#if>
</#list>
</@compress_single_line></#macro>
