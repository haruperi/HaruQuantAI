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
 * COT Accumulation — Bullish (Strategies 17 + 31).
 *
 * Detects improving COT structure: hedger CPI rising for N consecutive weeks
 * while speculator CPI is falling. This suggests commercials are gradually
 * building positions while speculators are unwinding -- accumulation.
 *
 * Bullish: H52 rising for MinWeeks AND S52 falling for MinWeeks.
 * User should add price confirmation (breakout, SMA cross) separately.
 *
 * Sources: Briese Movement Index [R3], Chart Pattern Validation [R4].
 */
@Help("Accumulation (Bullish). H52 rising AND S52 falling for N consecutive weeks - classic institutional accumulation pattern. Hedgers building longs while specs sell. (Strategy 17+31) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT27) Accumulation Bullish", display="COTAccumBull(#CotSymbol#, weeks=#MinWeeks#)", returnType = ReturnTypes.Boolean)
@SortOrder(2700)
@OppositeBlock(value="COTAccumulationBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTAccumulationBullish extends ConditionBlock {

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
				} catch(Exception e) { Log.error("COTAccumulationBullish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;

		// Check N consecutive weeks of H52 rising AND S52 falling
		for(int i = 0; i < MinWeeks; i++) {
			long t0 = barTime - i * WEEK_MS;
			long t1 = barTime - (i + 1) * WEEK_MS;

			double hedgNow = mapHedg52.getTime(t0);
			double hedgPrev = mapHedg52.getTime(t1);
			double specNow = mapSpec52.getTime(t0);
			double specPrev = mapSpec52.getTime(t1);

			if(hedgNow <= hedgPrev || specNow >= specPrev) return false;
		}

		return true;
	}
}
