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
 * COT Small Trader Consensus Fade — Bearish (Strategy 22 mirror).
 * Small traders at extreme optimism = contrarian bearish.
 */
@Help("Small Trader Fade (Bearish). Small traders at extreme optimism = contrarian bearish. (Strategy 22 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT33) Small Fade Bearish", display="COTSmallFadeBear(#CotSymbol#, sm>#SmallThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(3300)
@OppositeBlock(value="COTSmallFadeBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSmallFadeBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.90", minValue=0.70, maxValue=0.99, step=0.05, name="Small High Threshold (52w)")
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
				} catch(Exception e) { Log.error("COTSmallFadeBearish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		return (mapSmall52.getTime(barTime) > SmallThreshold);
	}
}
