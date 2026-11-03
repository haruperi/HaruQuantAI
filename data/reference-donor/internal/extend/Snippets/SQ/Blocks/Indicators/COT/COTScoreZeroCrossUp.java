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
 * COT Score Zero Cross Up (Strategy 11).
 *
 * Detects when the COTScore crosses above zero -- the regime transitions
 * from bearish to bullish. This is a positioning regime shift event, not
 * an extreme reading. It captures the moment when the hedger/speculator
 * balance tips from net-bearish to net-bullish.
 *
 * Condition: COTScore[now] > 0 AND COTScore[prev] <= 0
 *
 * Sources: Briese Movement Index [R3], Getting Technical [R5].
 */
@Help("COTScore Zero Cross Up. COTScore crosses above zero - regime transition from bearish to bullish. A simple but effective regime change signal. (Strategy 11) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT19) Score Zero Cross Up", display="COTZeroCrossUp(#CotSymbol#)", returnType = ReturnTypes.Boolean)
@SortOrder(1900)
@OppositeBlock(value="COTScoreZeroCrossDown")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTScoreZeroCrossUp extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

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
				} catch(Exception e) { Log.error("COTScoreZeroCrossUp OnInit error", e); }
	}

	private double calcScore(long barTime) {
		return ((mapHedg52.getTime(barTime) + mapHedg156.getTime(barTime)) / 2.0) - ((mapSpec52.getTime(barTime) + mapSpec156.getTime(barTime)) / 2.0);
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long prevBarTime = barTime - 7L * 24 * 3600 * 1000;
		return (calcScore(barTime) > 0 && calcScore(prevBarTime) <= 0);
	}
}
