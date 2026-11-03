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
 * COT Spread Z-Score — Bearish (Strategy 25 mirror).
 * Bearish: ZScore(H52-S52) < -ZThreshold.
 */
@Help("Spread Z-Score (Bearish). Z-score below negative threshold indicates statistically extreme bearish divergence. (Strategy 25 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT35) Spread ZScore Bearish", display="COTZScoreBear(#CotSymbol#, z<-#ZThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(3500)
@OppositeBlock(value="COTSpreadZScoreBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSpreadZScoreBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="1.50", minValue=0.50, maxValue=3.00, step=0.25, name="Z-Score Threshold")
	public double ZThreshold;

	@Parameter(defaultValue="26", minValue=12, maxValue=52, step=1, name="Lookback Period (weeks)")
	public int Period;

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
				} catch(Exception e) { Log.error("COTSpreadZScoreBearish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		double sum = 0, sumSq = 0;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;
		double currentSpread = mapHedg52.getTime(barTime) - mapSpec52.getTime(barTime);

		for(int i = 0; i < Period; i++) {
			long t = barTime - i * WEEK_MS;
			double spread = mapHedg52.getTime(t) - mapSpec52.getTime(t);
			sum += spread;
			sumSq += spread * spread;
		}

		double mean = sum / Period;
		double variance = (sumSq / Period) - (mean * mean);
		if(variance <= 0) return false;

		double stdDev = Math.sqrt(variance);
		double zScore = (currentSpread - mean) / stdDev;

		return (zScore < -ZThreshold);
	}
}
