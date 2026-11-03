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
 * COT Hedger/Speculator Convergence (Strategy 28).
 *
 * Detects when hedgers and speculators are converging toward similar positioning.
 * |H52 - S52| < ConvergenceThreshold.
 * 
 * When both groups agree, the COT signal is ambiguous. This is a filter block
 * to avoid trading during periods of positioning convergence (no edge).
 *
 * Sources: Briese COT Index [R2].
 */
@Help("Hedger/Speculator Convergence filter. |H52 - S52| < threshold means hedgers and speculators agree. No clear COT edge - avoid directional trades or use mean-reversion. (Strategy 28) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT38) H/S Convergence", display="COTConverge(#CotSymbol#, |h-s|<#ConvergenceThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(3800)
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTConvergence extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.15", minValue=0.05, maxValue=0.40, step=0.05, name="Convergence Threshold")
	public double ConvergenceThreshold;

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
				} catch(Exception e) { Log.error("COTConvergence OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		double spread = Math.abs(mapHedg52.getTime(barTime) - mapSpec52.getTime(barTime));
		return (spread < ConvergenceThreshold);
	}
}
