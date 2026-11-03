<#-- ============================================================================
  SqCOTBlocks.inc - COT helper methods for NinjaTrader 8 (C#).
  ============================================================================
  These helper methods are emitted INSIDE the strategy class when the strategy
  uses COT blocks. They are called by the COT block templates.
  
  The methods read SqCOT(identifier, 0, "").Values[field][barsAgo] - the plots of the
  SqCOT indicator from SqCOT.cs - through SqCOTVal.
  
  This file is conditionally included from Main.tpl when usesCOT is true.
-->

<#-- Detect COT block usage by scanning strategy XML for mI="COT" blocks -->
<#macro _scanCOT_NT node><#list node?children as c><#if c?node_type == 'element'><#if (c.@mI[0]?? && c.@mI[0] == "COT")><#assign usesCOT = true><#else><@_scanCOT_NT c /></#if></#if></#list></#macro>
<#assign usesCOT = false>
<@_scanCOT_NT doc.StrategyFile.Strategy />

<#if usesCOT>
		#region COT Helper Methods

		// One COT field of a market at a bar: 0=cpihedg, 1=ctihedg, 2=cpispec, 3=ctispec, 4=cpismall.
		// The SqCOT indicator keeps every field in its own plot; its indexer alone would always give cpihedg.
		private double SqCOTVal(string id, int field, int barsAgo)
		{
			return SqCOT(id, 0, "").Values[field][barsAgo];
		}

		// The bar that holds the time weeks * 7 days before the bar at barsAgo, the nearest earlier one when there is
		// no exact match. The StrategyQuant COT blocks step back by weeks, not by chart bars.
		private int SqCOTWeeksAgo(int barsAgo, int weeks)
		{
			if (weeks <= 0) return barsAgo;
			DateTime target = Time[barsAgo].AddDays(-7 * weeks);
			int idx = Bars.GetBar(target);
			if (idx > 0 && Bars.GetTime(idx) > target) idx--;
			int ago = CurrentBar - idx;
			if (ago < barsAgo) ago = barsAgo;
			if (ago > CurrentBar) ago = CurrentBar;
			return ago;
		}

		/// <summary>COT composite score: avg(hedg52, hedg156) - avg(spec52, spec156)</summary>
		private double SqCOTScore(string sym, int barsAgo)
		{
			return ((SqCOTVal(sym + "_52W", 0, barsAgo) + SqCOTVal(sym + "_156W", 0, barsAgo)) / 2.0)
			     - ((SqCOTVal(sym + "_52W", 2, barsAgo) + SqCOTVal(sym + "_156W", 2, barsAgo)) / 2.0);
		}

		/// <summary>Accumulation bullish: hedger rising AND spec falling for N consecutive weeks</summary>
		private bool SqCOTAccumBull(string sym, int barsAgo, int minWeeks)
		{
			for (int i = 0; i < minWeeks; i++)
				if (SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i)) <= SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i + 1))
				 || SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i)) >= SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i + 1)))
					return false;
			return true;
		}

		/// <summary>Accumulation bearish: hedger falling AND spec rising for N consecutive weeks</summary>
		private bool SqCOTAccumBear(string sym, int barsAgo, int minWeeks)
		{
			for (int i = 0; i < minWeeks; i++)
				if (SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i)) >= SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i + 1))
				 || SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i)) <= SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i + 1)))
					return false;
			return true;
		}

		/// <summary>Extreme exit bullish: hedger was recently extreme but now below exit threshold</summary>
		private bool SqCOTExtExitBull(string sym, int barsAgo, int lookback, double exitThresh, double extremeThresh)
		{
			if (SqCOTVal(sym + "_52W", 0, barsAgo) >= exitThresh) return false;
			for (int i = 1; i <= lookback; i++)
				if (SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i)) > extremeThresh) return true;
			return false;
		}

		/// <summary>Extreme exit bearish</summary>
		private bool SqCOTExtExitBear(string sym, int barsAgo, int lookback, double exitThresh, double extremeThresh)
		{
			if (SqCOTVal(sym + "_52W", 2, barsAgo) >= exitThresh) return false;
			for (int i = 1; i <= lookback; i++)
				if (SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i)) > extremeThresh) return true;
			return false;
		}

		/// <summary>Extreme persistence: field stays above threshold for N consecutive weeks</summary>
		private bool SqCOTExtPersist(string sym, int field, int barsAgo, int minWeeks, double thresh)
		{
			for (int i = 0; i < minWeeks; i++)
				if (SqCOTVal(sym + "_52W", field, SqCOTWeeksAgo(barsAgo, i)) < thresh) return false;
			return true;
		}

		/// <summary>Extreme unwind bullish: spec dropping from crowded level</summary>
		private bool SqCOTExtUnwindBull(string sym, int barsAgo, int lookback, double normThresh, double crowdThresh)
		{
			double sNow = SqCOTVal(sym + "_52W", 2, barsAgo);
			double sPrev = SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, 1));
			if (sNow >= normThresh || sNow >= sPrev) return false;
			for (int i = 1; i <= lookback; i++)
				if (SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i)) > crowdThresh) return true;
			return false;
		}

		/// <summary>Extreme unwind bearish</summary>
		private bool SqCOTExtUnwindBear(string sym, int barsAgo, int lookback, double normThresh, double crowdThresh)
		{
			double hNow = SqCOTVal(sym + "_52W", 0, barsAgo);
			double hPrev = SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, 1));
			if (hNow >= normThresh || hNow >= hPrev) return false;
			for (int i = 1; i <= lookback; i++)
				if (SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i)) > crowdThresh) return true;
			return false;
		}

		/// <summary>Spec exhaustion long</summary>
		private bool SqCOTSpecExhLong(string sym, int barsAgo, int lookback, double specExtreme, double hedgThresh)
		{
			double sNow = SqCOTVal(sym + "_52W", 2, barsAgo);
			double sPrev = SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, 1));
			double hNow = SqCOTVal(sym + "_52W", 0, barsAgo);
			if (sNow <= sPrev || hNow <= hedgThresh) return false;
			double shortExt = 1.0 - specExtreme;
			for (int i = 1; i <= lookback; i++)
				if (SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i)) < shortExt) return true;
			return false;
		}

		/// <summary>Spec exhaustion short</summary>
		private bool SqCOTSpecExhShort(string sym, int barsAgo, int lookback, double specExtreme, double hedgThresh)
		{
			double sNow = SqCOTVal(sym + "_52W", 2, barsAgo);
			double sPrev = SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, 1));
			double hNow = SqCOTVal(sym + "_52W", 0, barsAgo);
			if (sNow >= sPrev || hNow >= hedgThresh) return false;
			for (int i = 1; i <= lookback; i++)
				if (SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i)) > specExtreme) return true;
			return false;
		}

		/// <summary>Seasonal bullish: current hedger above its lookback average + threshold</summary>
		private bool SqCOTSeasonBull(string sym, int barsAgo, int lookback, double thresh)
		{
			double curr = SqCOTVal(sym + "_52W", 0, barsAgo);
			double sum = 0;
			for (int i = 1; i <= lookback; i++) sum += SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i));
			return curr > sum / lookback + thresh;
		}

		/// <summary>Seasonal bearish</summary>
		private bool SqCOTSeasonBear(string sym, int barsAgo, int lookback, double thresh)
		{
			double curr = SqCOTVal(sym + "_52W", 0, barsAgo);
			double sum = 0;
			for (int i = 1; i <= lookback; i++) sum += SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i));
			return curr < sum / lookback - thresh;
		}

		/// <summary>Spread Z-Score bullish</summary>
		private bool SqCOTSpreadZBull(string sym, int barsAgo, int period, double zThresh)
		{
			double currSpread = SqCOTVal(sym + "_52W", 0, barsAgo) - SqCOTVal(sym + "_52W", 2, barsAgo);
			double sum = 0, sumSq = 0;
			for (int i = 0; i < period; i++)
			{
				double sp = SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i)) - SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i));
				sum += sp; sumSq += sp * sp;
			}
			double mean = sum / period;
			double variance = (sumSq / period) - (mean * mean);
			if (variance <= 0) return false;
			return (currSpread - mean) / Math.Sqrt(variance) > zThresh;
		}

		/// <summary>Spread Z-Score bearish</summary>
		private bool SqCOTSpreadZBear(string sym, int barsAgo, int period, double zThresh)
		{
			double currSpread = SqCOTVal(sym + "_52W", 0, barsAgo) - SqCOTVal(sym + "_52W", 2, barsAgo);
			double sum = 0, sumSq = 0;
			for (int i = 0; i < period; i++)
			{
				double sp = SqCOTVal(sym + "_52W", 0, SqCOTWeeksAgo(barsAgo, i)) - SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, i));
				sum += sp; sumSq += sp * sp;
			}
			double mean = sum / period;
			double variance = (sumSq / period) - (mean * mean);
			if (variance <= 0) return false;
			return (currSpread - mean) / Math.Sqrt(variance) < -zThresh;
		}

		/// <summary>Higher low in COT score</summary>
		private bool SqCOTHigherLow(string sym, int barsAgo, int shortWin, int longWin)
		{
			double shortMin = double.MaxValue, longMin = double.MaxValue;
			for (int i = 0; i < shortWin; i++) { double s = SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i)); if (s < shortMin) shortMin = s; }
			for (int i = shortWin; i < longWin; i++) { double s = SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i)); if (s < longMin) longMin = s; }
			return shortMin > longMin && longMin < 0;
		}

		/// <summary>Lower high in COT score</summary>
		private bool SqCOTLowerHigh(string sym, int barsAgo, int shortWin, int longWin)
		{
			double shortMax = double.MinValue, longMax = double.MinValue;
			for (int i = 0; i < shortWin; i++) { double s = SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i)); if (s > shortMax) shortMax = s; }
			for (int i = shortWin; i < longWin; i++) { double s = SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i)); if (s > longMax) longMax = s; }
			return shortMax < longMax && longMax > 0;
		}

		/// <summary>Crowding unwind</summary>
		private bool SqCOTCrowdUnwind(string sym, int barsAgo, int direction, double specExtreme, double hedgOpposing)
		{
			double sNow = SqCOTVal(sym + "_52W", 2, barsAgo);
			double sPrev = SqCOTVal(sym + "_52W", 2, SqCOTWeeksAgo(barsAgo, 1));
			double hNow = SqCOTVal(sym + "_52W", 0, barsAgo);
			if (direction > 0) return sPrev > specExtreme && sNow < sPrev && hNow < hedgOpposing;
			return sPrev < 1.0 - specExtreme && sNow > sPrev && hNow > 1.0 - hedgOpposing;
		}

		/// <summary>Regime shift bullish: the score average of the last shiftWeeks weeks is above the average of shiftWeeks * 3 weeks and above 0. The Java block does not use its Level.</summary>
		private bool SqCOTRegShiftBull(string sym, int barsAgo, double level, int shiftWeeks)
		{
			int longWin = shiftWeeks * 3;
			double shortSum = 0, longSum = 0;
			for (int i = 0; i < shiftWeeks; i++) shortSum += SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i));
			for (int i = 0; i < longWin; i++) longSum += SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i));
			return shortSum / shiftWeeks > longSum / longWin && shortSum / shiftWeeks > 0;
		}

		/// <summary>Regime shift bearish</summary>
		private bool SqCOTRegShiftBear(string sym, int barsAgo, double level, int shiftWeeks)
		{
			int longWin = shiftWeeks * 3;
			double shortSum = 0, longSum = 0;
			for (int i = 0; i < shiftWeeks; i++) shortSum += SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i));
			for (int i = 0; i < longWin; i++) longSum += SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, i));
			return shortSum / shiftWeeks < longSum / longWin && shortSum / shiftWeeks < 0;
		}

		/// <summary>Rate of change bullish: the score rose by more than rocThreshold over rocPeriod weeks</summary>
		private bool SqCOTRocBull(string sym, int barsAgo, int rocPeriod, double rocThreshold)
		{
			return SqCOTScore(sym, barsAgo) - SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, rocPeriod)) > rocThreshold;
		}

		/// <summary>Rate of change bearish</summary>
		private bool SqCOTRocBear(string sym, int barsAgo, int rocPeriod, double rocThreshold)
		{
			return SqCOTScore(sym, barsAgo) - SqCOTScore(sym, SqCOTWeeksAgo(barsAgo, rocPeriod)) < -rocThreshold;
		}

		#endregion

		#region COT symbol inputs

		<#-- One input per COT market (global/cotSymbols.inc). Their defaults are set in State.SetDefaults. -->
<#list cotSymbols as cotSymbol>
		[NinjaScriptProperty]
		[Display(Name="${cotSymbolInput(cotSymbol)}", GroupName="COT Data", Order=${cotSymbol?index})]
		public string ${cotSymbolInput(cotSymbol)} { get; set; }

</#list>
<#-- The license input and the downloader exist only when a COT market is read. -->
<#if cotCheckedSymbols?has_content>
		[NinjaScriptProperty]
		[Display(Name="COTLicenseCode", Description="Your valid StrategyQuant X license key, the strategy downloads the COT data with it", GroupName="COT Data", Order=${cotSymbols?size})]
		public string COTLicenseCode { get; set; }

		private NinjaTrader.NinjaScript.Indicators.StrategyQuant.SqCOTDownloader sqCOTDownloader;
		private DateTime sqCOTLastUpdateCheck = DateTime.MinValue;

		/// <summary>Starts the SqCOTDownloader indicator with COTLicenseCode, as the MetaTrader export starts the SqCOTDownloader EA: it downloads the COT data when it is missing or older than 7 days. Without a license the strategy only says so.</summary>
		private void SqCOTStartDownloader()
		{
			if (string.IsNullOrEmpty(COTLicenseCode))
			{
				if (SqCOTIsStale())
				{
					Print("SqCOT: COT data is missing or older than 7 days. Fill the COTLicenseCode input so the strategy downloads it, or run the SqCOTDownloader indicator.");
				}
				return;
			}
			// UpdateHours 0: the downloader does not download again by itself, SqCOTCheckForUpdate decides when
			sqCOTDownloader = SqCOTDownloader(COTLicenseCode, "https://cdn.strategyquantcdn.com/cot.php", 0, false);
		}

		/// <summary>Once a day in real time: COT data older than 7 days is downloaded again, and the SqCOT indicators reload it.</summary>
		private void SqCOTCheckForUpdate()
		{
			if (sqCOTDownloader == null || State != State.Realtime || (DateTime.Now - sqCOTLastUpdateCheck).TotalHours < 24)
			{
				return;
			}
			sqCOTLastUpdateCheck = DateTime.Now;
			// above 0 the downloader's next bar update downloads; stale data means its last download is more than 24 h old
			sqCOTDownloader.UpdateHours = SqCOTIsStale() ? 24 : 0;
			sqCOTDownloader.Update();
		}

		/// <summary>Whether the COT data the SqCOTDownloader keeps in Documents\NinjaTrader 8\SqCOT is missing or older than 7 days.</summary>
		private static bool SqCOTIsStale()
		{
			string manifest = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "NinjaTrader 8", "SqCOT", "manifest.dat");
			try
			{
				string[] lines = System.IO.File.ReadAllLines(manifest);
				long seconds;
				if (lines.Length >= 2 && long.TryParse(lines[1].Trim(), out seconds))
				{
					return (DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).AddSeconds(seconds)).TotalDays > 7;
				}
			}
			catch (Exception)
			{
			}
			return true;
		}

</#if>
		/// <summary>Stops the strategy when a COTSymbol input names a market without a COT data file: a mistyped symbol would otherwise read empty COT values and trade on them.</summary>
		private void SqCOTCheckSymbols()
		{
<#list cotCheckedSymbols as cotSymbol>
<#assign cotInput = cotSymbolInput(cotSymbol)>
			if (!SqCOTDataExists(${cotInput} + "_52W"))
			{
				throw new Exception(${cotMissingSymbolMessage(cotInput)});
			}
</#list>
		}

		/// <summary>Whether a COT data file exists in the folder the SqCOT indicator reads: Documents\NinjaTrader 8\SqCOT, else ProgramData\StrategyQuant\COT.</summary>
		private static bool SqCOTDataExists(string identifier)
		{
			string ntDir = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "NinjaTrader 8", "SqCOT");
			string commonDir = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "StrategyQuant", "COT");
			string dir = System.IO.Directory.Exists(ntDir) ? ntDir : commonDir;
			return System.IO.File.Exists(System.IO.Path.Combine(dir, identifier + ".bin"))
				|| System.IO.File.Exists(System.IO.Path.Combine(dir, identifier + ".csv"));
		}

		#endregion
</#if>
