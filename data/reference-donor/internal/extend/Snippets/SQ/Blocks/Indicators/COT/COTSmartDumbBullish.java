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
 * COT Smart Money vs Dumb Money Divergence — Bullish (Strategy 19).
 *
 * Classic "fade the public" strategy. Detects when commercials (smart money)
 * are positioned opposite to small traders (dumb money) with high conviction.
 *
 * Bullish: H52 > HedgerThreshold AND Small52 < SmallThreshold
 * (Smart money bullish while dumb money bearish)
 *
 * Sources: CFTC [R1], Williams 2005 [R12], De Roon et al. 2000 [R10].
 */
@Help("Smart vs Dumb Money (Bullish). Hedgers (smart money) bullish above threshold AND small traders (dumb money) bearish below threshold. Classic fade-the-public signal. (Strategy 19) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT29) Smart vs Dumb Bullish", display="COTSmartDumbBull(#CotSymbol#, h>#HedgerThreshold#, sm<#SmallThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(2900)
@OppositeBlock(value="COTSmartDumbBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSmartDumbBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.80", minValue=0.60, maxValue=0.99, step=0.05, name="Hedger Threshold (52w)")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.20", minValue=0.01, maxValue=0.40, step=0.05, name="Small Trader Threshold (52w)")
	public double SmallThreshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSmall52;
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
						mapHedg52  = COTCompositeScore.loadMap(name52, 0);
						mapSmall52 = COTCompositeScore.loadMap(name52, 4);
					}
					dataReady = (mapHedg52 != null && mapSmall52 != null);
				} catch(Exception e) { Log.error("COTSmartDumbBullish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		return (mapHedg52.getTime(barTime) > HedgerThreshold && mapSmall52.getTime(barTime) < SmallThreshold);
	}
}
