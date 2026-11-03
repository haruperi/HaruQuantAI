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
 * COT Regime Shift — Bullish (Strategy 29).
 *
 * Detects a rapid COT regime shift: the COTScore moved from negative
 * territory to above a bullish threshold within N weeks. This identifies
 * when positioning structure transforms quickly from bearish to bullish.
 *
 * Condition: COTScore_now > Level AND COTScore[ShiftWeeks] < 0
 *
 * Sources: Briese Movement Index [R3].
 */
@Help("Rapid Regime Shift (Bullish). COTScore was negative (bearish) within N weeks but is now above Level. Detects fast turnarounds in institutional positioning. (Strategy 29) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT39) Regime Shift Bullish", display="COTRegimeBull(#CotSymbol#, now>#Level#, was<0)", returnType = ReturnTypes.Boolean)
@SortOrder(3900)
@OppositeBlock(value="COTRegimeShiftBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTRegimeShiftBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.40", minValue=0.10, maxValue=0.80, step=0.10, name="Bullish Level")
	public double Level;

	@Parameter(defaultValue="6", minValue=2, maxValue=12, step=1, name="Shift Window (weeks)")
	public int ShiftWeeks;

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
				} catch(Exception e) { Log.error("COTRegimeShiftBullish OnInit error", e); }
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

		// Compute short-window average (ShiftWeeks weeks, default 6)
		double shortSum = 0;
		for(int k = 0; k < ShiftWeeks; k++) {
			shortSum += calcScore(barTime - k * WEEK_MS);
		}
		double shortAvg = shortSum / ShiftWeeks;

		// Compute long-window average (ShiftWeeks * 3 weeks, default 18)
		int longWin = ShiftWeeks * 3;
		double longSum = 0;
		for(int k = 0; k < longWin; k++) {
			longSum += calcScore(barTime - k * WEEK_MS);
		}
		double longAvg = longSum / longWin;

		return (shortAvg > longAvg && shortAvg > 0);
	}
}
