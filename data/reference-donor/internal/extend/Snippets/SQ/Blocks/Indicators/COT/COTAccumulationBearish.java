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
 * COT Accumulation — Bearish (Strategy 17+31 mirror).
 * Distribution: H52 falling while S52 rising for N weeks.
 */
@Help("Distribution (Bearish). H52 falling AND S52 rising for N consecutive weeks - institutional distribution. (Strategy 17+31 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT28) Accumulation Bearish", display="COTAccumBear(#CotSymbol#, weeks=#MinWeeks#)", returnType = ReturnTypes.Boolean)
@SortOrder(2800)
@OppositeBlock(value="COTAccumulationBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTAccumulationBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="3", minValue=2, maxValue=8, step=1, name="Min Consecutive Weeks")
	public int MinWeeks;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52;
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
					if(name52 != null) {
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
					dataReady = (mapHedg52 != null && mapSpec52 != null);
				} catch(Exception e) { Log.error("COTAccumulationBearish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;

		for(int i = 0; i < MinWeeks; i++) {
			long t0 = barTime - i * WEEK_MS;
			long t1 = barTime - (i + 1) * WEEK_MS;

			if(mapHedg52.getTime(t0) >= mapHedg52.getTime(t1) || mapSpec52.getTime(t0) <= mapSpec52.getTime(t1))
				return false;
		}
		return true;
	}
}
