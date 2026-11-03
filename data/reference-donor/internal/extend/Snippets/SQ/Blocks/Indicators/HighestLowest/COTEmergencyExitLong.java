/*
 * Copyright (c) 2026, StrategyQuant - All rights reserved.
 */
package SQ.Blocks.Indicators.HighestLowest;

import SQ.Internal.ConditionBlock;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.*;

@Help("COT Emergency Exit Long — price-based safety exit for COT cycle strategies. " +
	"Exit when the weekly close drops below the low of the previous month. " +
	"This provides catastrophic risk protection for the slow COT Full-Cycle strategy. " +
	"Pavel's recommendation: Always have a price-based emergency exit when holding positions for weeks/months based on COT cycles. " +
	"The MonthLookback parameter controls how many bars to look back for the monthly low (default 20 = ~1 month of daily bars, or 4 weekly bars). — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Emergency Exit Long", display="COTEmergencyExitLong(lookback=#MonthLookback#)", returnType = ReturnTypes.Boolean)
@OppositeBlock(value="COTEmergencyExitShort")
@SortOrder(124)
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTEmergencyExitLong extends ConditionBlock {

	@Parameter(defaultValue="20", minValue=4, maxValue=60, step=1, name="Month Lookback (bars for monthly low)")
	public int MonthLookback;

	@Parameter
	public int Shift;

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		double currentClose = Strategy.MarketData.Chart(0).Close(Shift);

		// Find the lowest low over the previous 'month' period
		double monthLow = Double.MAX_VALUE;
		for(int i = Shift + 1; i <= Shift + MonthLookback; i++) {
			double low = Strategy.MarketData.Chart(0).Low(i);
			if(low < monthLow) monthLow = low;
		}

		// Emergency exit: current close below previous month's low
		return (currentClose < monthLow);
	}
}