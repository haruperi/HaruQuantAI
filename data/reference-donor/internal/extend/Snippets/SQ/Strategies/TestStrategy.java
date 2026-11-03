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
package SQ.Strategies;

import SQ.Internal.Strategy;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TimeframeManager;

public class TestStrategy extends Strategy {

	@Override
	public void Initialize() throws Exception {
		// adding chart to the trading setup
		MarketData.addChart(TimeframeManager.TF_H4);
		MarketData.addChart("Symbol x1", TimeframeManager.TF_H4);
		MarketData.addChart("Connection 1", "Symbol x1", TimeframeManager.TF_H4);
	}

	@Override
	public void OnBarUpdate() throws Exception {
		//----------------------
		// Getting OHLC values
		//----------------------
		// four ways of getting value of open price of the main chart
		double o01 = Open(0);
		double o02 = Open.get(0);
		double o03 = MarketData.Chart(0).Open(0);
		double o04 = MarketData.Chart(0).Open.get(0);

		// three ways of getting value of open price of second chart
		double o11 = Open(1, 0);
		double o12 = MarketData.Chart(1).Open(0);
		double o13 = MarketData.Chart(1).Open.get(0);

		String symbol = MarketData.Chart(1).Symbol;

		// getting data series of Open on first chart
		DataSeries ds1 = Open;
		DataSeries ds2 = MarketData.Chart(0).Open;

		// getting data series of Open on second chart
		DataSeries ds3 = MarketData.Chart(1).Open;
		
		
		//----------------------
		// Recognizing which chart was updated
		//----------------------
		int updatedIndex = UpdatedChart;
		boolean ChartXUpdated = MarketData.Chart(2).isUpdated();
		
		// recognize if multiple charts were updated by this tick 
		if(MultipleChartsUpdated) {
			throw new Exception("MultipleChartsUpdated - this shouldn't happen here!");
		}
		
	}

}
