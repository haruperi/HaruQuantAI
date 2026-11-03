/*
 * Copyright (c) 2026, StrategyQuant - All rights reserved.
 */
package SQ.Blocks.Indicators.COT;

import SQ.Internal.ConditionBlock;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.data.CustomDataIndyMap;

@Help("COT Full-Cycle Exit Long (Strategy 39). Exit the long position when hedger CPI reaches the ExitLevel. " +
	"Recommended exit thresholds to test: 0.60, 0.70, 0.80, 0.90. " +
	"Designed to ride the entire COT normalization cycle from extreme low to high. " +
	"Pair with COTFullCycleLong for the complete cycle strategy. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Full-Cycle Exit Long", display="COTCycleExitLong(#CotSymbol#, exit=#ExitLevel#)", returnType = ReturnTypes.Boolean)
@SortOrder(122)
@OppositeBlock(value="COTFullCycleExitShort")
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTFullCycleExitLong extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.70", minValue=0.50, maxValue=0.95, step=0.05, name="Exit Level (COT reaches high)")
	public double ExitLevel;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg;
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
					String name = COTCompositeScore.findCotIndicatorName(CotSymbol, Period.toUpperCase());
					if(name != null) mapHedg = COTCompositeScore.loadMap(name, 0);
					dataReady = (mapHedg != null);
				} catch(Exception e) { Log.error("COTFullCycleExitLong OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		double cot = mapHedg.getTime(barTime);
		return (cot >= ExitLevel);
	}
}