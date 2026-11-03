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
 * COT Score Acceleration — Bullish (Strategy 35).
 *
 * Detects when the COTScore momentum is itself accelerating (2nd derivative).
 * Momentum is increasing: mom_now > mom_prev.
 *
 * AccelBullish = MomentumNow > MomentumPrev AND MomentumNow > MomentumThreshold
 * Where Momentum = COTScore[now] - COTScore[MomPeriod]
 *
 * Sources: Briese Movement Index [R3].
 */
@Help("Score Acceleration (Bullish). COTScore momentum is accelerating upward (2nd derivative positive). Current momentum exceeds previous momentum. Institutional conviction is strengthening. (Strategy 35) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT47) Score Accel Bullish", display="COTScoreAccelBull(#CotSymbol#, per=#MomPeriod#)", returnType = ReturnTypes.Boolean)
@SortOrder(4700)
@OppositeBlock(value="COTScoreAccelBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTScoreAccelBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="4", minValue=1, maxValue=12, step=1, name="Momentum Period")
	public int MomPeriod;

	@Parameter(defaultValue="0.05", minValue=0.00, maxValue=0.30, step=0.05, name="Min Momentum")
	public double MomentumThreshold;

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
				} catch(Exception e) { Log.error("COTScoreAccelBullish OnInit error", e); }
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

		double momNow  = calcScore(barTime) - calcScore(barTime - MomPeriod * WEEK_MS);
		double momPrev = calcScore(barTime - WEEK_MS) - calcScore(barTime - (1 + MomPeriod) * WEEK_MS);

		return (momNow > momPrev && momNow > MomentumThreshold);
	}
}
