<#-- MinMaxSLPT: min/max clamp on the SL/PT distance, in SQX pips (0 = no limit).
     SQX stores either the legacy combined MinimumSLPT/MaximumSLPT keys (one limit applied to both
     SL and PT) or the split MinimumSL/MaximumSL/MinimumPT/MaximumPT keys - mirror of the MT5
     variables template, which handles both schemas the same way. The clamp itself is applied at
     SL/PT placement (printSetSLPT -> sqClampSLPT below), exactly where MT5 SQ.mqh clamps the
     order's SL/PT price. -->
<#if tradingOptionKeyExists("MinMaxSLPT", "MinimumSLPT")>
<#-- Minimum SL distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MinimumSL = <@printTradingOptionIntValue "MinMaxSLPT" "MinimumSLPT" />;
<#-- Minimum PT distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MinimumPT = <@printTradingOptionIntValue "MinMaxSLPT" "MinimumSLPT" />;
<#else>
<#-- Minimum SL distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MinimumSL = <@printTradingOptionIntValue "MinMaxSLPT" "MinimumSL" />;
<#-- Minimum PT distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MinimumPT = <@printTradingOptionIntValue "MinMaxSLPT" "MinimumPT" />;
</#if>
<#if tradingOptionKeyExists("MinMaxSLPT", "MaximumSLPT")>
<#-- Maximum SL distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MaximumSL = <@printTradingOptionIntValue "MinMaxSLPT" "MaximumSLPT" />;
<#-- Maximum PT distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MaximumPT = <@printTradingOptionIntValue "MinMaxSLPT" "MaximumSLPT" />;
<#else>
<#-- Maximum SL distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MaximumSL = <@printTradingOptionIntValue "MinMaxSLPT" "MaximumSL" />;
<#-- Maximum PT distance in SQX pips (MinMaxSLPT trading option; 0 = no limit). -->
		private int MaximumPT = <@printTradingOptionIntValue "MinMaxSLPT" "MaximumPT" />;
</#if>

<#--
  <summary>
  Clamps a stop-loss / profit-target tick distance to the MinMaxSLPT trading-option
  limits (mirrors the MT5 SQ.mqh min/max SL/PT clamp applied at order
  placement). The limits are in SQX pips (0 = no limit) and convert to ticks via
  SqPipFactor. NinjaScript CalculationMode.Ticks distances are positive and
  direction-independent, so this positive-distance clamp is exactly the MT5
  per-direction price clamp.
  </summary>
  <param name="distTicks">SL/PT distance in ticks, as passed to SetStopLoss/SetProfitTarget.</param>
  <param name="isSL">True for the stop-loss limits, false for the profit-target limits.</param>
  <returns>The clamped distance in ticks.</returns>
-->
		/// <summary>Clamps a stop-loss / profit-target tick distance to the MinMaxSLPT trading-option limits.</summary>
		private double sqClampSLPT(double distTicks, bool isSL)
		{
			int min = isSL ? MinimumSL : MinimumPT;
			int max = isSL ? MaximumSL : MaximumPT;
			if (min > 0) distTicks = Math.Max(distTicks, (double)min * SqPipFactor);
			if (max > 0) distTicks = Math.Min(distTicks, (double)max * SqPipFactor);
			return distTicks;
		}
