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

/** COT Multi-Window — Bearish (Strategy 34 mirror). */
@Help("Multi-Window Confirmation (Bearish). Both 52w and 156w windows confirm bearish regime. (Strategy 34 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT46) Multi-Window Bearish", display="COTMultiWinBear(#CotSymbol#, h52<#HedgerThreshold#, h156<#Hedger156Threshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(4600)
@OppositeBlock(value="COTMultiWindowBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTMultiWindowBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.25", minValue=0.01, maxValue=0.50, step=0.05, name="Hedger Threshold (52w)")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.35", minValue=0.01, maxValue=0.60, step=0.05, name="Hedger Threshold (156w)")
	public double Hedger156Threshold;

	@Parameter(defaultValue="0.75", minValue=0.50, maxValue=0.99, step=0.05, name="Spec Threshold (52w)")
	public double SpecThreshold;

	@Parameter(defaultValue="0.65", minValue=0.40, maxValue=0.99, step=0.05, name="Spec Threshold (156w)")
	public double Spec156Threshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52, mapHedg156, mapSpec156;
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
					dataReady = (mapHedg52 != null && mapSpec52 != null && mapHedg156 != null && mapSpec156 != null);
				} catch(Exception e) { Log.error("COTMultiWindowBearish OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		return (mapHedg52.getTime(barTime) < HedgerThreshold && mapHedg156.getTime(barTime) < Hedger156Threshold
		     && mapSpec52.getTime(barTime) > SpecThreshold && mapSpec156.getTime(barTime) > Spec156Threshold);
	}
}
