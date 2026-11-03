/*
 * Copyright (c) 2026, StrategyQuant - All rights reserved.
 * This code can be used only within StrategyQuant products.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
 */
package SQ.Blocks.Indicators.COT;

import SQ.Internal.ConditionBlock;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.data.CustomDataIndyMap;

/**
 * COT Seasonal Positioning — Bullish (Strategy 27).
 *
 * Detects when the current hedger CPI exceeds the historical seasonal
 * average for the same week-of-year by a threshold. This identifies
 * when positioning is UNUSUALLY bullish for this time of year.
 *
 * Simplified implementation: compares current H52 to the average H52
 * over the trailing SeasonalLookback weeks. If current is significantly
 * above the recent average, it's a seasonal bullish positioning event.
 *
 * Sources: Seasonal analysis in commodity markets, Briese [R2].
 */
@Help("Seasonal Filter (Bullish). Current hedger CPI is unusually above its seasonal average for this week-of-year. Filters out normal seasonal patterns to identify genuine positioning shifts. (Strategy 27) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT41) Seasonal Bullish", display="COTSeasonBull(#CotSymbol#, above avg+#SeasonalThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(4100)
@OppositeBlock(value="COTSeasonalBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSeasonalBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.15", minValue=0.05, maxValue=0.40, step=0.05, name="Seasonal Threshold (above avg)")
	public double SeasonalThreshold;

	@Parameter(defaultValue="52", minValue=26, maxValue=104, step=1, name="Seasonal Lookback (weeks)")
	public int SeasonalLookback;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52;
	private boolean dataReady = false;

	@Override
	protected void OnInit() {
		// No-op: Strategy not yet available during initialize()
	}

	//------------------------------------------------------------------------

	private boolean initialized = false;

	private void lazyInit() {
		if(initialized) return;
		initialized = true;

		if(Strategy == null) return;

		CotSymbol = COTCompositeScore.resolveBlockSymbol(Strategy, CotSymbol);

		try {
		
					String name52 = COTCompositeScore.findCotIndicatorName(CotSymbol, "52W");
					if(name52 != null) mapHedg52 = COTCompositeScore.loadMap(name52, 0);
					dataReady = (mapHedg52 != null);
				} catch(Exception e) { Log.error("COTSeasonalBullish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;
		double current = mapHedg52.getTime(barTime);

		double sum = 0;
		for(int i = 1; i <= SeasonalLookback; i++) {
			long t = barTime - i * WEEK_MS;
			sum += mapHedg52.getTime(t);
		}
		double avg = sum / SeasonalLookback;

		return (current > avg + SeasonalThreshold);
	}
}
