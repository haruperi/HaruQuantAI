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
 * COT Rate of Change — Bullish (Strategy 26).
 *
 * Measures the percentage change of the H52-S52 spread over N weeks.
 * A large positive ROC means the hedger/speculator divergence is
 * widening rapidly in the bullish direction.
 *
 * Bullish: ROC = (spread_now - spread_prev) / |spread_prev| > ROCThreshold
 * With fallback to absolute difference when prev is near zero.
 *
 * Sources: Briese Movement Index [R3].
 */
@Help("Rate of Change (Bullish). H52-S52 spread ROC above threshold. Measures how rapidly the hedger-speculator divergence is widening in the bullish direction. (Strategy 26) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT36) ROC Bullish", display="COTRocBull(#CotSymbol#, roc>#ROCThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(3600)
@OppositeBlock(value="COTRocBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTRocBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.30", minValue=0.10, maxValue=1.00, step=0.10, name="ROC Threshold")
	public double ROCThreshold;

	@Parameter(defaultValue="4", minValue=1, maxValue=12, step=1, name="ROC Period (weeks)")
	public int RocPeriod;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52, mapHedg156, mapSpec156;
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
					String name156 = COTCompositeScore.findCotIndicatorName(CotSymbol, "156W");
					if(name52 != null) {
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
					if(name156 != null) {
						mapHedg156 = COTCompositeScore.loadMap(name156, 0);
						mapSpec156 = COTCompositeScore.loadMap(name156, 2);
					}
					dataReady = (mapHedg52 != null && mapSpec52 != null && mapHedg156 != null && mapSpec156 != null);
				} catch(Exception e) { Log.error("COTRocBullish OnInit error", e); }
	}

	private double calcScore(long t) {
		return ((mapHedg52.getTime(t) + mapHedg156.getTime(t)) / 2.0) - ((mapSpec52.getTime(t) + mapSpec156.getTime(t)) / 2.0);
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime     = Strategy.MarketData.Chart(0).Time(Shift);
		long prevBarTime = barTime - RocPeriod * 7L * 24 * 3600 * 1000;

		double scoreNow  = calcScore(barTime);
		double scorePast = calcScore(prevBarTime);

		return ((scoreNow - scorePast) > ROCThreshold);
	}
}
