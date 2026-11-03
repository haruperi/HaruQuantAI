<#--
  ============================================================================
  SQIndicators.inc - custom indicator runtime (NinjaTrader).
  ============================================================================
  Indicators that NinjaTrader's Managed approach does NOT provide natively, or provides
  with a different calculation, and that the installed StrategyQuant indicator package
  (custom_indicators/NinjaTrader) does not provide, are implemented here as private
  methods on the generated strategy class.

  Each method mirrors the corresponding SQX Java snippet exactly (functional parity
  with the other platforms). Rendered into the class body by Main.tpl, next to SQ.inc, after the
  blocks: sqRound always (SQ.inc calls it), every other group only when a block that
  calls it has set the group's flag (sqUsesMonthDay, sqUsesNthValue,
  sqUsesBlockMA). A block template that calls a group must set its flag on the call line.
  Recursive helpers keep their state in the SqIndyState store (SQ.inc), so a call only
  advances over the bars not yet computed; series-aware helpers take a leading data-series
  index and read their bars through sqHigh/sqLow/sqClose(ci, ...).
-->
		#region SQ custom indicators

		// ---- Rounding ----

<#--
  <summary>
  Half-up rounding to <paramref name="decimals"/> places, mirroring SQUtils.round and
  DataSeries.getRounded exactly (adds a 1e-10 epsilon, then floor(x+0.5) = Java Math.round).
  NaN rounds to 0 and the result saturates at the long range, as Java Math.round does.
  </summary>
-->
		/// <summary>Half-up rounding to decimals places, mirroring SQUtils.round and DataSeries.getRounded exactly.</summary>
		private double sqRound(double value, int decimals)
		{
			if (double.IsNaN(value))
				return 0;
			double p = Math.Pow(10, decimals);
			double r = Math.Floor((value + 1e-10) * p + 0.5);
			if (r > 9223372036854775807.0) r = 9223372036854775807.0;      // Java Math.round saturates at Long.MAX_VALUE
			if (r < -9223372036854775808.0) r = -9223372036854775808.0;    // and at Long.MIN_VALUE
			return r / p;
		}

		<#-- Emitted only when a block sets sqUsesMonthDay: the calendar trading-day tests of IsMonthFirstTradingDay / IsMonthLastTradingDay. -->
<#if sqUsesMonthDay??>
<#--
  <summary>
  True when the current bar's date is the FIRST trading day of its month: the calendar
  1st, shifted FORWARD over Saturday/Sunday when weekends are excluded, then compared by
  day-of-month. Mirrors IsMonthFirstTradingDay.java. Stateless, read from Time[0].
  </summary>
  <remarks>
  <para>The Java is stateful - it remembers the first date it has seen in the current month
  and returns <c>monthFirstTradingDay == date</c> - but the answer it produces is
  <b>day-granular</b>: true for EVERY bar of that day. A month-change test such as
  <c>Time[0].Month != Time[1].Month</c> is true for exactly ONE bar, so on an intraday
  timeframe it would disagree with StrategyQuant on every other bar of the first trading
  day.</para>
  <para>Calendar-based rather than a walk back through the bars, deliberately: it is the same
  approximation <see cref="sqIsMonthLastTradingDay"/> makes (both ignore holidays), and the
  two blocks are a pair, answered by the same mechanism.</para>
  </remarks>
  <param name="includeWeekends">When false, a weekend 1st is shifted forward to Monday.</param>
  <returns>True if the current bar falls on the month's first trading day.</returns>
-->
		/// <summary>True when the current bar's date is the FIRST trading day of its month.</summary>
		private bool sqIsMonthFirstTradingDay(int ci, bool includeWeekends)
		{
			DateTime t = sqClock(sqTime(ci, 0));
			DateTime first = new DateTime(t.Year, t.Month, 1);
			if (!includeWeekends)
			{
				if (first.DayOfWeek == DayOfWeek.Saturday) first = first.AddDays(2);
				else if (first.DayOfWeek == DayOfWeek.Sunday) first = first.AddDays(1);
			}
			return t.Day == first.Day;
		}

<#--
  <summary>
  True when the current bar's date is the last trading day of its month: the
  calendar last day of the month, shifted back over Saturday/Sunday when weekends
  are excluded, then compared by day-of-month. Mirrors IsMonthLastTradingDay.java
  (DaysInMonth + setDayOfMonth + weekend back-shift). Stateless, read from Time[0].
  </summary>
  <param name="includeWeekends">When false, a weekend last day is shifted back to Friday.</param>
  <returns>True if the current bar falls on the month's last trading day.</returns>
-->
		/// <summary>True when the current bar's date is the last trading day of its month.</summary>
		private bool sqIsMonthLastTradingDay(int ci, bool includeWeekends)
		{
			DateTime t = sqClock(sqTime(ci, 0));
			int daysInMonth = DateTime.DaysInMonth(t.Year, t.Month);
			DateTime last = new DateTime(t.Year, t.Month, daysInMonth);
			if (!includeWeekends)
			{
				if (last.DayOfWeek == DayOfWeek.Saturday) last = last.AddDays(-1);
				else if (last.DayOfWeek == DayOfWeek.Sunday) last = last.AddDays(-2);
			}
			return t.Day == last.Day;
		}
</#if>

		<#-- Emitted only when a block sets sqUsesNthValue: the Nth-value ranking of IndicatorHighest / IndicatorLowest. -->
<#if sqUsesNthValue??>
<#--
  <summary>
  Nth highest value of an array (0 = highest, 1 = second highest, ...). Returns -1 when
  nth is out of range. Mirrors IndicatorHighest.java.
  </summary>
  <param name="vals">The values to rank.</param>
  <param name="nth">Rank from the top (0 = highest).</param>
  <returns>The nth-highest value, or -1.</returns>
-->
		/// <summary>Nth highest value of an array (0 = highest, 1 = second highest, ...).</summary>
		private double sqNthHighest(double[] vals, int nth)
		{
			if (nth < 0 || nth >= vals.Length) return -1;
			Array.Sort(vals);
			return vals[vals.Length - 1 - nth];
		}

<#--
  <summary>
  Nth lowest value of an array (0 = lowest, 1 = second lowest, ...). Returns -1 when
  nth is out of range. Mirrors IndicatorLowest.java.
  </summary>
  <param name="vals">The values to rank.</param>
  <param name="nth">Rank from the bottom (0 = lowest).</param>
  <returns>The nth-lowest value, or -1.</returns>
-->
		/// <summary>Nth lowest value of an array (0 = lowest, 1 = second lowest, ...).</summary>
		private double sqNthLowest(double[] vals, int nth)
		{
			if (nth < 0 || nth >= vals.Length) return -1;
			Array.Sort(vals);
			return vals[nth];
		}
</#if>

		<#-- Emitted only when a block sets sqUsesBlockMA: the moving average of a nested block, for the Indicator*MA comparison blocks. -->
<#if sqUsesBlockMA??>
<#--
  <summary>
  The nested block at <paramref name="barsAgo"/>, or 0 when it reads a bar before the first one: a
  StrategyQuant DataSeries reads 0 there, while an installed indicator's series throws. The block adds
  its own #Shift# to the offset, so the read can reach further back than <paramref name="barsAgo"/>
  and only the read itself can tell.
  </summary>
  <param name="f">the nested block, evaluated at a bar offset</param>
  <param name="barsAgo">bar offset of the read</param>
  <returns>The block's value, or 0 before the first bar.</returns>
-->
		/// <summary>The nested block at barsAgo, or 0 when it reads a bar before the first one.</summary>
		private double sqBlockAt(Func<int, double> f, int barsAgo)
		{
			if (barsAgo > CurrentBar)
				return 0;
			try
			{
				return f(barsAgo);
			}
			catch (ArgumentOutOfRangeException)
			{
				return 0;
			}
		}

<#--
  <summary>
  Moving average OF AN ARBITRARY BLOCK EXPRESSION, mirroring
  IndicatorMAComparisonBlockAbstract.calculateMA. Serves the four
  Indicator*MA comparison blocks.
  
  The block being averaged arrives as <c>Func&lt;int, double&gt;</c> - a lambda over the bar
  offset - because the Java calls Indicator.evaluateBlock(shift + i) for i = 0..period-1,
  i.e. it evaluates a NESTED expression at a RUNTIME-VARIABLE shift. Baking the shift in at
  generation time, which is what every other NinjaTrader template does, cannot express that.
  MetaTrader solves the same problem by passing the indicator as a STRING and keeping a
  runtime table of expressions; in C# a lambda says it directly and costs nothing.
  
  Every read is rounded to 6 decimals before use, exactly as the Java does - the rounding is
  inside the loop, not applied to the result, and the values depend on it.
  </summary>
  <param name="f">the nested block, evaluated at a bar offset</param>
  <param name="maType">1 = Simple, 2 = Exponential, 3 = Weighted, 4 = Hull</param>
-->
		/// <summary>Moving average OF AN ARBITRARY BLOCK EXPRESSION, mirroring IndicatorMAComparisonBlockAbstract.calculateMA.</summary>
		private double sqBlockMA(Func<int, double> f, int period, int maType, int shift)
		{
			switch (maType)
			{
				case 2:
				{
					// Seeded with the OLDEST value and walked forward, like the Java: the loop runs
					// from period-2 down to 0, so it is not the usual "EMA from bar 0" recursion.
					double alpha = 2.0 / (period + 1.0);
					double prevEMA = sqRound(sqBlockAt(f, shift + period - 1), 6);
					for (int i = period - 2; i >= 0; i--)
						prevEMA = sqRound(sqBlockAt(f, shift + i), 6) * alpha + prevEMA * (1 - alpha);
					return prevEMA;
				}
				case 3:
					return sqBlockWMA(f, period, shift);
				case 4:
					// Hull = 2*WMA(n/2) - WMA(n). The Java also computes sqrt(period) and never uses
					// it, so the usual third WMA smoothing is absent there - and absent here too.
					return 2 * sqBlockWMA(f, period / 2, shift) - sqBlockWMA(f, period, shift);
				default:
				{
					double sum = 0;
					for (int i = 0; i < period; i++)
						sum += sqRound(sqBlockAt(f, shift + i), 6);
					return sum / period;
				}
			}
		}

<#--
  <summary>
  Linearly weighted MA of a block expression, mirroring
  IndicatorMAComparisonBlockAbstract.calculateWMA: weight period-i, newest bar heaviest.
  </summary>
-->
		/// <summary>Linearly weighted MA of a block expression, mirroring IndicatorMAComparisonBlockAbstract.calculateWMA.</summary>
		private double sqBlockWMA(Func<int, double> f, int period, int shift)
		{
			double weightedSum = 0, weightSum = 0;
			for (int i = 0; i < period; i++)
			{
				double weight = period - i;
				weightedSum += sqRound(sqBlockAt(f, shift + i), 6) * weight;
				weightSum += weight;
			}
			return weightedSum / weightSum;
		}

		/// <summary>IndicatorAboveMA: the block is above its own moving average.</summary>
		private bool sqIndicatorAboveMA(Func<int, double> f, int period, int maType, int shift)
		{
			return sqRound(sqBlockAt(f, shift), 6) > sqBlockMA(f, period, maType, shift);
		}

		/// <summary>IndicatorBelowMA: the block is below its own moving average.</summary>
		private bool sqIndicatorBelowMA(Func<int, double> f, int period, int maType, int shift)
		{
			return sqRound(sqBlockAt(f, shift), 6) < sqBlockMA(f, period, maType, shift);
		}

		/// <summary>IndicatorCrossesAboveMA: below on the previous bar, above on this one.</summary>
		private bool sqIndicatorCrossesAboveMA(Func<int, double> f, int period, int maType, int shift)
		{
			double prev = sqRound(sqBlockAt(f, shift + 1), 6);
			double prevMa = sqBlockMA(f, period, maType, shift + 1);
			return prev < prevMa && sqRound(sqBlockAt(f, shift), 6) > sqBlockMA(f, period, maType, shift);
		}

		/// <summary>IndicatorCrossesBelowMA: above on the previous bar, below on this one.</summary>
		private bool sqIndicatorCrossesBelowMA(Func<int, double> f, int period, int maType, int shift)
		{
			double prev = sqRound(sqBlockAt(f, shift + 1), 6);
			double prevMa = sqBlockMA(f, period, maType, shift + 1);
			return prev > prevMa && sqRound(sqBlockAt(f, shift), 6) < sqBlockMA(f, period, maType, shift);
		}
</#if>

		#endregion
