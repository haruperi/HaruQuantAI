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
 * COT Speculator Exhaustion — Long signal (Strategy 13 mirror).
 *
 * Spec was at extreme SHORT crowding and is now rising, hedgers high.
 *
 * Sources: Briese Movement Index [R3], Wang 2001 [R6], Wang 2004 [R7].
 */
@Help("Speculator Exhaustion (Long signal). Spec was crowded short, now rising with hedger at high levels confirming bullish. (Strategy 13 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT22) Spec Exhaustion Long", display="COTSpecExhaustL(#CotSymbol#, ext>#SpecExtreme#)", returnType = ReturnTypes.Boolean)
@SortOrder(2200)
@OppositeBlock(value="COTSpecExhaustionShort")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSpecExhaustionLong extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.90", minValue=0.80, maxValue=0.99, step=0.05, name="Spec Extreme Threshold (inverted: 1-this)")
	public double SpecExtreme;

	@Parameter(defaultValue="0.75", minValue=0.50, maxValue=0.95, step=0.05, name="Hedger High Threshold")
	public double HedgerThreshold;

	@Parameter(defaultValue="6", minValue=2, maxValue=12, step=1, name="Lookback Weeks")
	public int LookbackWeeks;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapSpec52, mapHedg52;
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
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
					}
					dataReady = (mapSpec52 != null && mapHedg52 != null);
				} catch(Exception e) { Log.error("COTSpecExhaustionLong OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;
		long prevBarTime = barTime - WEEK_MS;

		double specNow  = mapSpec52.getTime(barTime);
		double specPrev = mapSpec52.getTime(prevBarTime);
		double hedgNow  = mapHedg52.getTime(barTime);

		double shortExtreme = 1.0 - SpecExtreme; // e.g. 0.10

		// Must be rising and hedger confirming
		if(specNow <= specPrev || hedgNow <= HedgerThreshold) return false;

		// Check if spec was at short extreme recently
		for(int i = 1; i <= LookbackWeeks; i++) {
			long pastTime = barTime - i * WEEK_MS;
			if(mapSpec52.getTime(pastTime) < shortExtreme) return true;
		}

		return false;
	}
}
