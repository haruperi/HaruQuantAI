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
 * COT Speculator Exhaustion — Short signal (Strategy 13).
 *
 * Detects when speculators WERE at extreme long crowding and are now
 * falling, while hedgers are positioned low (opposing). This is distinct
 * from CrowdingUnwind because it explicitly looks for the spec DECELERATION
 * pattern — the spec was extreme AND is now falling over multiple weeks.
 *
 * Short conditions:
 *   S52 was > SpecExtreme within LookbackWeeks
 *   S52 is now falling (S52 < S52[1])
 *   H52 < HedgerThreshold (hedgers are bearishly positioned, confirming)
 *
 * Sources: Briese Movement Index [R3], Wang 2001 [R6], Wang 2004 [R7].
 */
@Help("Speculator Exhaustion (Short signal). Spec was crowded long recently, now falling with hedger at opposing low levels. Fading exhausted speculative longs. (Strategy 13) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT21) Spec Exhaustion Short", display="COTSpecExhaustS(#CotSymbol#, ext>#SpecExtreme#)", returnType = ReturnTypes.Boolean)
@SortOrder(2100)
@OppositeBlock(value="COTSpecExhaustionLong")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSpecExhaustionShort extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.90", minValue=0.80, maxValue=0.99, step=0.05, name="Spec Extreme Threshold")
	public double SpecExtreme;

	@Parameter(defaultValue="0.25", minValue=0.05, maxValue=0.50, step=0.05, name="Hedger Opposing Threshold")
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
				} catch(Exception e) { Log.error("COTSpecExhaustionShort OnInit error", e); }
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

		// Must be falling and hedger opposing
		if(specNow >= specPrev || hedgNow >= HedgerThreshold) return false;

		// Check if spec was extreme recently
		for(int i = 1; i <= LookbackWeeks; i++) {
			long pastTime = barTime - i * WEEK_MS;
			if(mapSpec52.getTime(pastTime) > SpecExtreme) return true;
		}

		return false;
	}
}
