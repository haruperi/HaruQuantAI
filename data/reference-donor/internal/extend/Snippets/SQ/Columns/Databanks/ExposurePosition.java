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

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.parameters.StockpickerOptions;
import com.strategyquant.tradinglib.simulator.Engines;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ExposurePosition extends DatabankColumn {
	public static final Logger Log = LoggerFactory.getLogger("Exposure Position (Stockpicker engine)");

	static final long MILLIS_IN_HOUR = 3600L * 1000L;

	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------

	public ExposurePosition() {
		super(L.tsq("Exposure Position"), Decimal2Pct, ValueTypes.Minimize, 0, 0, 100);

		setTooltip(L.tsq("Exposure Position = # bars in all positions / total # bars in the sample.\nSpecial version for Stockpicker engine considering also # of open positions form max."));

		// restrict Exposure computation only for money PL Type (we'll not compute separate Exposure for % or pips results, it is as same as for money)
		setPLTypeRestrictions(PlTypes.Money);
		setDependencies("Exposure");
	}

	//------------------------------------------------------------------------

	@SuppressWarnings("java:S3776") // Cognitive Complexity of methods should not be too high
	@Override
	public double compute(SQStats stats, StatsTypeCombination combination, OrdersList ordersList, SettingsMap settings, SQStats statsLong, SQStats statsShort) throws Exception {

		if(!isStockpickerEngine(settings)) {
			return stats.getDouble("Exposure");
		}

		int maxOpenPositions = getMaxOpenPositions(combination, settings);

		try {
			ChartSetup chartSetup = (ChartSetup) settings.get(SettingsKeys.BacktestChart);
			if(chartSetup == null) {
				//if (Log.isWarnEnabled()) Log.warn("Chart setup is undefined");
				return 0;
			}

			ChartDef mainChart = chartSetup.getMainChart();
			if(mainChart == null) {
				//if (Log.isWarnEnabled()) Log.warn("Main chart is undefined");
				return 0;
			}

			long dateFrom = mainChart.getHistoryFrom();
			long dateTo = mainChart.getHistoryTo();

			int hours = (int)((dateTo - dateFrom) / MILLIS_IN_HOUR);
			// Protect against invalid input
			if(hours <= 0) {
				return 0;
			}

			int[] tradeHoursPositions = new int[hours];

			for(int a=0; a<ordersList.size(); a++) {
				Order order = ordersList.get(a);
				if(!order.isFilledOrder()) continue;		//skip canceled orders

				int orderHours = Math.max(1, (int)((order.CloseTime - order.OpenTime) / MILLIS_IN_HOUR));
				int startIndex = (int)((order.OpenTime - dateFrom) / MILLIS_IN_HOUR);

				if(startIndex >= 0 && orderHours >= 0 && (startIndex + orderHours) <= tradeHoursPositions.length) {
					for(int i=startIndex; i<startIndex + orderHours; i++) {
						tradeHoursPositions[i]++;
					}
				}
			}

			double maxPossiblePositions = tradeHoursPositions.length*(maxOpenPositions);
			double realPositions = 0;

			for (int tradeHour : tradeHoursPositions) {
				realPositions += tradeHour;
			}

			return round2(realPositions / maxPossiblePositions * 100d);

		} catch(Exception e) {
			Log.error("Exception ", e);
			return 0;
		}
	}

	//------------------------------------------------------------------------

	private boolean isStockpickerEngine(SettingsMap settings) {
		ChartSetup chartSetup = (ChartSetup) settings.get(SettingsKeys.BacktestChart);
		if(chartSetup == null || chartSetup.getBacktestEngine() != Engines.Stockpicker) {
			return false;
		}

		return true;
	}

	//------------------------------------------------------------------------

	private int getMaxOpenPositions(StatsTypeCombination combination, SettingsMap settings) {
		int maxPositions = 0;

		TradingOptions to = (TradingOptions) settings.get(SettingsKeys.TradingOptions);
		if(to != null) {
			for(TradingOption o : to) {
				if(o instanceof StockpickerOptions) {
					if(combination.getDirection() == Directions.Both || combination.getDirection() == Directions.Long) {
						maxPositions += ((StockpickerOptions) o).PickerMaxOpenPositionsLong;
					}
	
					if(combination.getDirection() == Directions.Both || combination.getDirection() == Directions.Short) {
						maxPositions += ((StockpickerOptions) o).PickerMaxOpenPositionsShort;
					}
				}
			}
		}

		if(maxPositions == 0) {
			maxPositions = 1;
		}

		return maxPositions;
	}

}