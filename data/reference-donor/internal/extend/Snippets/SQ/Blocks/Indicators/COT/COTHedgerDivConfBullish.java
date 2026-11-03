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
 * COT Hedger Divergence Confirmed — Bullish (Strategy 38).
 *
 * Combines hedger extreme with speculator opposing AND momentum confirmation.
 * This is the "full package" — level + divergence + momentum all in one block.
 *
 * Bullish: H52 > HedgerThreshold (level)
 *       AND S52 < SpecThreshold (divergence)
 *       AND H52 > H52[MomLookback] (hedger improving = momentum)
 *
 * Sources: Briese COT Index [R2], Movement Index [R3], Wang 2001 [R6].
 */
@Help("Hedger Divergence Confirmed (Bullish). Full-package signal: hedger H52 above threshold + speculator S52 below threshold + COTScore momentum positive. Combines level, opposition, and direction. (Strategy 38) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT49) Hedger Div Confirmed Bull", display="COTHedgDivBull(#CotSymbol#, h>#HedgerThreshold#, s<#SpecThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(4900)
@OppositeBlock(value="COTHedgerDivConfBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTHedgerDivConfBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.80", minValue=0.60, maxValue=0.99, step=0.05, name="Hedger Threshold (52w)")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.20", minValue=0.01, maxValue=0.40, step=0.05, name="Spec Threshold (52w)")
	public double SpecThreshold;

	@Parameter(defaultValue="4", minValue=1, maxValue=12, step=1, name="Momentum Lookback")
	public int MomLookback;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52;
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
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
					dataReady = (mapHedg52 != null && mapSpec52 != null);
				} catch(Exception e) { Log.error("COTHedgerDivConfBullish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long momTime = Strategy.MarketData.Chart(0).Time(Shift + MomLookback);

		double hedgNow  = mapHedg52.getTime(barTime);
		double specNow  = mapSpec52.getTime(barTime);
		double hedgPrev = mapHedg52.getTime(momTime);

		return (hedgNow > HedgerThreshold && specNow < SpecThreshold && hedgNow > hedgPrev);
	}
}
