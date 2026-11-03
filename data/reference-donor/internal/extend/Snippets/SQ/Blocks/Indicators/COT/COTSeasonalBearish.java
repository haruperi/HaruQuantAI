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

/** COT Seasonal — Bearish (Strategy 27 mirror). Current H52 unusually below avg. */
@Help("Seasonal Filter (Bearish). Hedger CPI unusually below its seasonal average. (Strategy 27 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT42) Seasonal Bearish", display="COTSeasonBear(#CotSymbol#, below avg-#SeasonalThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(4200)
@OppositeBlock(value="COTSeasonalBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSeasonalBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.15", minValue=0.05, maxValue=0.40, step=0.05, name="Seasonal Threshold (below avg)")
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
				} catch(Exception e) { Log.error("COTSeasonalBearish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;
		double current = mapHedg52.getTime(barTime);
		double sum = 0;
		for(int i = 1; i <= SeasonalLookback; i++) { sum += mapHedg52.getTime(barTime - i * WEEK_MS); }
		double avg = sum / SeasonalLookback;
		return (current < avg - SeasonalThreshold);
	}
}
