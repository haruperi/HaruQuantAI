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
 * COT Score Zero Cross Down (Strategy 11 mirror).
 *
 * Detects when the COTScore crosses below zero -- regime transitions
 * from bullish to bearish.
 *
 * Condition: COTScore[now] < 0 AND COTScore[prev] >= 0
 *
 * Sources: Briese Movement Index [R3], Getting Technical [R5].
 */
@Help("COTScore Zero Cross Down. COTScore crosses below zero - regime transition from bullish to bearish. (Strategy 11 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT20) Score Zero Cross Down", display="COTZeroCrossDown(#CotSymbol#)", returnType = ReturnTypes.Boolean)
@SortOrder(2000)
@OppositeBlock(value="COTScoreZeroCrossUp")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTScoreZeroCrossDown extends ConditionBlock {

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
				} catch(Exception e) { Log.error("COTScoreZeroCrossDown OnInit error", e); }
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
		return (calcScore(barTime) < 0 && calcScore(prevBarTime) >= 0);
	}
}
