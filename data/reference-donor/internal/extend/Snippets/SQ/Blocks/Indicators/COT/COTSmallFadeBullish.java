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
 * COT Small Trader Consensus Fade — Bullish (Strategy 22).
 *
 * Fades the small traders: when small traders are at extreme pessimism,
 * go long (contrarian signal). Small traders are considered the least
 * informed group.
 *
 * Bullish: Small52 < SmallThreshold (small traders extremely bearish = contrarian bullish)
 *
 * Sources: Williams 2005 [R12], CFTC [R1].
 */
@Help("Small Trader Fade (Bullish). Small traders at extreme pessimism = contrarian bullish. Retail crowd is maximally bearish, historically a good time to be long. (Strategy 22) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT32) Small Fade Bullish", display="COTSmallFadeBull(#CotSymbol#, sm<#SmallThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(3200)
@OppositeBlock(value="COTSmallFadeBearish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSmallFadeBullish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.10", minValue=0.01, maxValue=0.30, step=0.05, name="Small Low Threshold (52w)")
	public double SmallThreshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapSmall52;
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
					if(name52 != null) mapSmall52 = COTCompositeScore.loadMap(name52, 4);
					dataReady = (mapSmall52 != null);
				} catch(Exception e) { Log.error("COTSmallFadeBullish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		return (mapSmall52.getTime(barTime) < SmallThreshold);
	}
}
