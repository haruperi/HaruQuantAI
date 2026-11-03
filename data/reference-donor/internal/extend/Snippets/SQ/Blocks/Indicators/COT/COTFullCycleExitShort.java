/*
 * Copyright (c) 2026, StrategyQuant - All rights reserved.
 */
package SQ.Blocks.Indicators.COT;

import SQ.Internal.ConditionBlock;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.data.CustomDataIndyMap;

@Help("COT Full-Cycle Exit Short (Strategy 39). Exit the short position when hedger CPI drops below the ExitLevel. " +
	"Recommended exit thresholds to test: 0.10, 0.20, 0.30, 0.40. " +
	"Designed to ride the entire COT normalization cycle from extreme high to low. " +
	"Pair with COTFullCycleLong for the complete cycle strategy. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Full-Cycle Exit Short", display="COTCycleExitShort(#CotSymbol#, exit=#ExitLevel#)", returnType = ReturnTypes.Boolean)
@SortOrder(123)
@OppositeBlock(value="COTFullCycleExitLong")
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTFullCycleExitShort extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.30", minValue=0.05, maxValue=0.50, step=0.05, name="Exit Level (COT drops below)")
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
				} catch(Exception e) { Log.error("COTFullCycleExitShort OnInit error", e); }
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		double cot = mapHedg.getTime(barTime);
		return (cot <= ExitLevel);
	}
}