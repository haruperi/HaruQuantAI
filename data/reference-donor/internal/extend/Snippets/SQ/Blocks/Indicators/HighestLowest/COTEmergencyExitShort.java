/*
 * Copyright (c) 2026, StrategyQuant - All rights reserved.
 */
package SQ.Blocks.Indicators.HighestLowest;

import SQ.Internal.ConditionBlock;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.*;

@Help("COT Emergency Exit Short — price-based safety exit for COT cycle strategies. " +
	"Exit when the weekly close rises above the high of the previous month. " +
	"This provides catastrophic risk protection for the slow COT Full-Cycle strategy. " +
	"Pavel's recommendation: Always have a price-based emergency exit when holding positions for weeks/months based on COT cycles. " +
	"The MonthLookback parameter controls how many bars to look back for the monthly high (default 20 = ~1 month of daily bars, or 4 weekly bars). — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Emergency Exit Short", display="COTEmergencyExitShort(lookback=#MonthLookback#)", returnType = ReturnTypes.Boolean)
@OppositeBlock(value="COTEmergencyExitLong")
@SortOrder(125)
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTEmergencyExitShort extends ConditionBlock {

	@Parameter(defaultValue="20", minValue=4, maxValue=60, step=1, name="Month Lookback (bars for monthly high)")
	public int MonthLookback;

	@Parameter
	public int Shift;

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		double currentClose = Strategy.MarketData.Chart(0).Close(Shift);

		// Find the highest high over the previous 'month' period
		double monthHigh = Double.MIN_VALUE;
		for(int i = Shift + 1; i <= Shift + MonthLookback; i++) {
			double high = Strategy.MarketData.Chart(0).High(i);
			if(high > monthHigh) monthHigh = high;
		}

		// Emergency exit: current close above previous month's high
		return (currentClose > monthHigh);
	}
}
