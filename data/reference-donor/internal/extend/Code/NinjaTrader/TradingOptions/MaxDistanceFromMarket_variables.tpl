<#-- MaxDistanceFromMarket: skip a PENDING entry whose price level lies further from the
     market than the configured percentage - mirror of MT5 SQ.mqh (the gate guards only pending
     order types there too; market entries are never gated). The gate itself is emitted in
     EnterAtStop.tpl / EnterAtLimit.tpl via sqMaxDistanceOk below. -->
<#-- MaxDistanceFromMarket trading option enabled. -->
		private bool MaxDistanceFromMarket = <@printTradingOptionBoolValue "MaxDistanceFromMarket" "MaxDistanceFromMarket" />;
<#-- Maximum pending-entry distance from the market price, in percent. -->
		private double MaxDistancePct = <@printTradingOptionIntValue "MaxDistanceFromMarket" "MaxDistancePct" />;

<#--
  <summary>
  True when a pending entry at <paramref name="price"/> is within the
  MaxDistanceFromMarket limit (mirrors MT5 SQ.mqh: percentage distance from the
  market price, both sides rounded to 2 decimals - sqRound matches NormalizeDouble on
  the positive values involved). The market reference is Close[0], the bar-close model's
  market price. Logs the skip so a silently missing trade is explainable from the output.
  </summary>
  <param name="price">The pending entry's stop/limit price level.</param>
  <returns>True to allow the entry, false to skip it.</returns>
-->
		/// <summary>True when a pending entry at price is within the MaxDistanceFromMarket limit.</summary>
		private bool sqMaxDistanceOk(double price)
		{
			if (!MaxDistanceFromMarket) return true;
			double market = Close[0];
			double pctDistance = sqRound(Math.Abs(price - market) / market * 100, 2);
			if (pctDistance > sqRound(MaxDistancePct, 2))
			{
				Print(string.Format("Order skipped - too far from market price. Open price: {0}, Market price: {1}, Max distance: {2}%", price, market, MaxDistancePct));
				return false;
			}
			return true;
		}
