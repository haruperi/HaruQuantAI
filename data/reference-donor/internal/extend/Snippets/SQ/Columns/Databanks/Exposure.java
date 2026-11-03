/*
 * Copyright (c) 2017-2018, StrategyQuant - All rights reserved.
 *
 * Code in this file was made in a good faith that it is correct and does what it should.
 * If you found a bug in this code OR you have an improvement suggestion OR you want to include
 * your own code snippet into our standard library please contact us at:
 * https://roadmap.strategyquant.com
 *
 * This code can be used only within StrategyQuant products.
 * Every owner of valid (free, trial or commercial) license of any StrategyQuant product
 * is allowed to freely use, copy, modify or make derivative work of this code without limitations,
 * to be used in all StrategyQuant products and share his/her modifications or derivative work
 * with the StrategyQuant community.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
 * PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES
 * OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 */
package SQ.Columns.Databanks;

import com.strategyquant.lib.SQTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.SettingsKeys;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.ValueTypes;

public class Exposure extends DatabankColumn {
	public static final Logger Log = LoggerFactory.getLogger("Exposure");
	
	static final long MILLIS_IN_HOUR = 3600L * 1000L;
	
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------

	public Exposure() {
		super(L.tsq("Exposure"), Decimal2Pct, ValueTypes.Minimize, 0, 0, 100);

		setTooltip(L.tsq("Exposure = # bars in all positions / total # bars in the sample"));
		
		// restrict Exposure computation only for money PL Type (we'll not compute separate Exposure for % or pips results, it is as same as for money)
		setPLTypeRestrictions(PlTypes.Money); 		
	}
	
	//------------------------------------------------------------------------

	@SuppressWarnings("java:S3776") // Cognitive Complexity of methods should not be too high
	@Override
	public double compute(SQStats stats, StatsTypeCombination combination, OrdersList ordersList, SettingsMap settings, SQStats statsLong, SQStats statsShort) throws Exception {
		try {
			long dateFrom = Long.MAX_VALUE;
			long dateTo = Long.MIN_VALUE;
			
			ChartSetup chartSetup = (ChartSetup) settings.get(SettingsKeys.BacktestChart);
			if(chartSetup != null) {
				ChartDef mainChart = chartSetup.getMainChart();
				if(mainChart != null) {
					dateFrom = mainChart.getHistoryFrom();
					dateTo = mainChart.getHistoryTo();
				}
			} else {
				dateFrom = settings.getLong(SettingsKeys.PortfolioDataStart, Long.MAX_VALUE);
				dateTo = settings.getLong(SettingsKeys.PortfolioDataEnd, Long.MIN_VALUE);
			}
			
			if(dateFrom == Long.MAX_VALUE || dateTo == Long.MIN_VALUE) {
				return 0;
			}
			
			int hours = (int)((dateTo - dateFrom) / MILLIS_IN_HOUR);
			// Protect against invalid input
			if(hours <= 0) {
				return 0;
			}

			boolean[] tradeHours = new boolean[hours];
			
			for(int a=0; a<ordersList.size(); a++) {
				Order order = ordersList.get(a);
				if(!order.isFilledOrder()) continue;		//skip canceled orders
				
				int orderHours = Math.max(1, (int)((order.CloseTime - order.OpenTime) / MILLIS_IN_HOUR));
				int startIndex = (int)((order.OpenTime - dateFrom) / MILLIS_IN_HOUR);

				if(startIndex >= 0 && orderHours >= 0 && (startIndex + orderHours) <= tradeHours.length) {
					for(int i=startIndex; i<startIndex + orderHours; i++) {
						tradeHours[i] = true;
					}
				}
			}
			
			double hoursWithTrades = 0;

			for (boolean tradeHour : tradeHours) {
				hoursWithTrades += tradeHour ? 1 : 0;
			}
			
			return round2(hoursWithTrades / tradeHours.length * 100);
			
		} catch(Exception e) {
			Log.error("Exception ", e);
			return 0;
		}
	}	
	
}