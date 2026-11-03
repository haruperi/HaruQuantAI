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
 * COT Lower High (Price/COT Divergence — COT part) (Strategy 15+32 mirror).
 * COTScore making a lower high. Sources: [R4], [R5].
 */
@Help("COT Lower High. COTScore making a lower high while price potentially makes a higher high - bearish COT divergence. (Strategy 15+32 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT26) Lower High (COT Div)", display="COTLowerHigh(#CotSymbol#, short=#ShortWindow#, long=#LongWindow#)", returnType = ReturnTypes.Boolean)
@SortOrder(2600)
@OppositeBlock(value="COTHigherLow")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTLowerHigh extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="6", minValue=2, maxValue=12, step=1, name="Short Window (weeks)")
	public int ShortWindow;

	@Parameter(defaultValue="12", minValue=6, maxValue=26, step=1, name="Long Window (weeks)")
	public int LongWindow;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapHedg156, mapSpec52, mapSpec156;
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
		
					String name52  = COTCompositeScore.findCotIndicatorName(CotSymbol, "52W");
					String name156 = COTCompositeScore.findCotIndicatorName(CotSymbol, "156W");
					if(name52 != null) { mapHedg52 = COTCompositeScore.loadMap(name52, 0); mapSpec52 = COTCompositeScore.loadMap(name52, 2); }
					if(name156 != null) { mapHedg156 = COTCompositeScore.loadMap(name156, 0); mapSpec156 = COTCompositeScore.loadMap(name156, 2); }
					dataReady = (mapHedg52 != null && mapHedg156 != null && mapSpec52 != null && mapSpec156 != null);
				} catch(Exception e) { Log.error("COTLowerHigh OnInit error", e); }
	}

	private double calcScore(long barTime) {
		return ((mapHedg52.getTime(barTime) + mapHedg156.getTime(barTime)) / 2.0) - ((mapSpec52.getTime(barTime) + mapSpec156.getTime(barTime)) / 2.0);
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;

		double shortMax = -Double.MAX_VALUE;
		for(int i = 0; i < ShortWindow; i++) {
			long t = barTime - i * WEEK_MS;
			shortMax = Math.max(shortMax, calcScore(t));
		}

		double longMax = -Double.MAX_VALUE;
		for(int i = ShortWindow; i < LongWindow; i++) {
			long t = barTime - i * WEEK_MS;
			longMax = Math.max(longMax, calcScore(t));
		}

		return (shortMax < longMax && longMax > 0);
	}
}
