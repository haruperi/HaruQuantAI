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
 * COT Neutral/Flat Zone (Strategy 20).
 *
 * Detects when COT positioning is in a neutral zone — no strong directional
 * signal from either hedgers or speculators. This is a FILTER block:
 * when true, there is no clear COT regime, so the user might want to
 * avoid trading or use mean-reversion strategies.
 *
 * Neutral: |COTScore| < NeutralBand (both H52 and S52 near 50)
 *
 * Sources: Briese COT Index [R2].
 */
@Help("Neutral Zone filter. |COTScore| < NeutralBand indicates no strong COT signal. Use to AVOID trading when positioning is ambiguous, or apply mean-reversion logic. (Strategy 20) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT31) Neutral Zone", display="COTNeutral(#CotSymbol#, band<#NeutralBand#)", returnType = ReturnTypes.Boolean)
@SortOrder(3100)
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTNeutralZone extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.20", minValue=0.05, maxValue=0.50, step=0.05, name="Neutral Band (|COTScore| <)")
	public double NeutralBand;

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
				} catch(Exception e) { Log.error("COTNeutralZone OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		double score = ((mapHedg52.getTime(barTime) + mapHedg156.getTime(barTime)) / 2.0) - ((mapSpec52.getTime(barTime) + mapSpec156.getTime(barTime)) / 2.0);
		return (Math.abs(score) < NeutralBand);
	}
}
