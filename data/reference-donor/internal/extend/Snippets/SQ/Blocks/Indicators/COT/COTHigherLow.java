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
 * COT Higher Low (Price/COT Divergence — COT part) (Strategies 15 + 32 bullish).
 *
 * Detects when the COTScore is making a higher low compared to its recent
 * minimum. This is the COT portion of a classical bullish divergence:
 * while price may be making a lower low, COT positioning is making a
 * higher low, suggesting improving institutional sentiment.
 *
 * Condition: Current COTScore low > Previous COTScore low
 *   min(COTScore, ShortWindow) > min(COTScore, LongWindow)
 *
 * User should add price conditions (e.g. price at new low) separately.
 *
 * Sources: Briese Chart Pattern Validation [R4], Getting Technical [R5].
 */
@Help("COT Higher Low (Institutional Divergence). COTScore is making a higher low compared to a recent trough. Pair with price making a lower low for a classic COT divergence setup. (Strategy 15+32) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT25) Higher Low (COT Div)", display="COTHigherLow(#CotSymbol#, short=#ShortWindow#, long=#LongWindow#)", returnType = ReturnTypes.Boolean)
@SortOrder(2500)
@OppositeBlock(value="COTLowerHigh")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTHigherLow extends ConditionBlock {

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
				} catch(Exception e) { Log.error("COTHigherLow OnInit error", e); }
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

		// Find min COTScore in the short window (recent)
		double shortMin = Double.MAX_VALUE;
		for(int i = 0; i < ShortWindow; i++) {
			long t = barTime - i * WEEK_MS;
			shortMin = Math.min(shortMin, calcScore(t));
		}

		// Find min COTScore in the older part of the long window
		double longMin = Double.MAX_VALUE;
		for(int i = ShortWindow; i < LongWindow; i++) {
			long t = barTime - i * WEEK_MS;
			longMin = Math.min(longMin, calcScore(t));
		}

		// Higher low: recent minimum is above the older minimum
		return (shortMin > longMin && longMin < 0);
	}
}
