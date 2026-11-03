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
 * COT Triple Positioning Divergence — Bullish (Strategy 14).
 *
 * The strongest form of COT divergence: all THREE trader groups confirm
 * the same directional bias. Hedgers bullish, speculators bearish,
 * AND small traders bearish.
 *
 * Bullish conditions:
 *   H52 > HedgerThreshold (commercials heavily hedging = bullish)
 *   S52 < SpecThreshold (large specs bearish)
 *   Small52 < SmallThreshold (small traders also bearish)
 *
 * When all three groups align, the positioning signal is at maximum strength.
 * Requires cpismall data (buffer index 4).
 *
 * Sources: CFTC definitions [R1], Wang 2001 [R6], Williams 2005 [R12].
 */
@Help("Triple Positioning Divergence (Bullish). All 3 trader groups confirm: hedgers high, specs low, small traders low. Maximum conviction signal - rare but powerful. (Strategy 14) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT23) Triple Div Bullish", display="COTTripleBull(#CotSymbol#, h>#HedgerThreshold#, s<#SpecThreshold#, sm<#SmallThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(2300)
@OppositeBlock(value="COTTripleDivBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTTripleDivBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.85", minValue=0.70, maxValue=0.99, step=0.05, name="Hedger Threshold (52w)")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.15", minValue=0.01, maxValue=0.30, step=0.05, name="Speculator Threshold (52w)")
	public double SpecThreshold;

	@Parameter(defaultValue="0.25", minValue=0.05, maxValue=0.40, step=0.05, name="Small Trader Threshold (52w)")
	public double SmallThreshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52, mapSmall52;
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
						mapHedg52  = COTCompositeScore.loadMap(name52, 0); // cpihedg
						mapSpec52  = COTCompositeScore.loadMap(name52, 2); // cpispec
						mapSmall52 = COTCompositeScore.loadMap(name52, 4); // cpismall
					}
					dataReady = (mapHedg52 != null && mapSpec52 != null && mapSmall52 != null);
				} catch(Exception e) { Log.error("COTTripleDivBullish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);

		double hedg52  = mapHedg52.getTime(barTime);
		double spec52  = mapSpec52.getTime(barTime);
		double small52 = mapSmall52.getTime(barTime);

		return (hedg52 > HedgerThreshold && spec52 < SpecThreshold && small52 < SmallThreshold);
	}
}
