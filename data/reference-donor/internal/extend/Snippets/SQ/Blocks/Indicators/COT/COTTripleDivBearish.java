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
 * COT Triple Positioning Divergence — Bearish (Strategy 14 mirror).
 *
 * All three groups confirm bearish: hedgers low, specs high, small traders high.
 *
 * Sources: CFTC definitions [R1], Wang 2001 [R6], Williams 2005 [R12].
 */
@Help("Triple Positioning Divergence (Bearish). All 3 groups confirm bearish: hedgers low, specs high, small traders high. (Strategy 14 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT24) Triple Div Bearish", display="COTTripleBear(#CotSymbol#, h<#HedgerThreshold#, s>#SpecThreshold#, sm>#SmallThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(2400)
@OppositeBlock(value="COTTripleDivBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTTripleDivBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.15", minValue=0.01, maxValue=0.30, step=0.05, name="Hedger Threshold (52w)")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.85", minValue=0.70, maxValue=0.99, step=0.05, name="Speculator Threshold (52w)")
	public double SpecThreshold;

	@Parameter(defaultValue="0.75", minValue=0.60, maxValue=0.95, step=0.05, name="Small Trader Threshold (52w)")
	public double SmallThreshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52, mapSmall52;
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
						mapSpec52  = COTCompositeScore.loadMap(name52, 2);
						mapSmall52 = COTCompositeScore.loadMap(name52, 4);
					}
					dataReady = (mapHedg52 != null && mapSpec52 != null && mapSmall52 != null);
				} catch(Exception e) { Log.error("COTTripleDivBearish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);

		double hedg52  = mapHedg52.getTime(barTime);
		double spec52  = mapSpec52.getTime(barTime);
		double small52 = mapSmall52.getTime(barTime);

		return (hedg52 < HedgerThreshold && spec52 > SpecThreshold && small52 > SmallThreshold);
	}
}
