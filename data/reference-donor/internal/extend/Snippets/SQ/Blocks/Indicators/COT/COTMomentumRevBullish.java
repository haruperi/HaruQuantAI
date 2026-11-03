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
 * COT Momentum Reversal — Bullish (Strategy 30).
 *
 * Detects when COTScore momentum reverses from negative to positive.
 * The momentum was declining (bearish) and has now started improving.
 * 
 * MomentumNow  = COTScore[0] - COTScore[MomPeriod]
 * MomentumPrev = COTScore[1] - COTScore[1+MomPeriod]
 * Bullish reversal: MomentumNow > 0 AND MomentumPrev <= 0
 *
 * Sources: Briese Movement Index [R3].
 */
@Help("Momentum Reversal (Bullish). COTScore momentum crosses from negative to positive. The rate of change of institutional positioning flips from deteriorating to improving. (Strategy 30) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT43) Momentum Rev Bullish", display="COTMomRevBull(#CotSymbol#, per=#MomPeriod#)", returnType = ReturnTypes.Boolean)
@SortOrder(4300)
@OppositeBlock(value="COTMomentumRevBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTMomentumRevBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="4", minValue=1, maxValue=12, step=1, name="Momentum Period")
	public int MomPeriod;

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
				} catch(Exception e) { Log.error("COTMomentumRevBullish OnInit error", e); }
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

		double scoreNow = calcScore(barTime);
		double scoreMomAgo = calcScore(barTime - MomPeriod * WEEK_MS);
		double scorePrev = calcScore(barTime - WEEK_MS);
		double scorePrevMomAgo = calcScore(barTime - (1 + MomPeriod) * WEEK_MS);

		double momNow  = scoreNow - scoreMomAgo;
		double momPrev = scorePrev - scorePrevMomAgo;

		return (momNow > 0 && momPrev <= 0);
	}
}
