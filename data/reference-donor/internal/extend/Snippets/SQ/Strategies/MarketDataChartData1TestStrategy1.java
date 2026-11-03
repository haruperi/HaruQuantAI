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

import java.util.ArrayList;

import SQ.Internal.Strategy;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.lib.utils.FullData;

public class MarketDataChartData1TestStrategy1 extends Strategy {

	public ArrayList<FullData> data = new ArrayList<FullData>();
	int count = -1;
	
	@Override
	public void Initialize() throws Exception {
		MarketData.addChart("XSymbol_1_3", TimeframeManager.TF_H1);
		MarketData.addChart("History", "XSymbol_0_1", TimeframeManager.TF_H1);
		MarketData.addChart("History", "XSymbol_0_2", TimeframeManager.TF_H1);
	}

	@Override
	public void OnBarUpdate() throws Exception {
		count++;

		Log.debug("Tick processed!");
		
		if(count >= 20) {
			Log.info("Stopping strategy here!");
			StopStrategy();
		}
		
		if(count % 4 > 0) {
			// we loaded OHLC data, so for one data record there are 4 ticks created. 
			// We skip these 3 ticks here 
			return;
		}
		
		int chartIndex = count / 4;
		
		FullData fd = new FullData();
		fd.time = MarketData.Chart(chartIndex).Time(0);
		fd.open = MarketData.Chart(chartIndex).Open(0);
		fd.symbol = MarketData.Chart(chartIndex).Symbol;
		fd.connection = MarketData.Chart(chartIndex).Connection;
		fd.timeframe = MarketData.Chart(chartIndex).Timeframe;
		
		data.add(fd);
		
		if(chartIndex < 4) return;
		
		//-----------------------
		// now verify that all the methods of getting value are the same
		
		// four ways of getting value of open price of the main chart
		double o1 = Open(0);
		double o2 = Open.get(0);
		double o3 = MarketData.Chart(0).Open(0);
		double o4 = MarketData.Chart(0).Open.get(0);

		if(o1 != o2 || o1 != o3 || o1 != o4) {
			throw new Exception("Values from Open() are not same (1)!");
		}
		
		// three ways of getting value of open price of second chart
		double o5 = Open(3, 0);
		double o6 = MarketData.Chart(3).Open(0);
		double o7 = MarketData.Chart(3).Open.get(0);

		if(o5 != o6 || o5 != o7) {
			throw new Exception("Values from Open() are not same (2)!");
		}

		// getting data series of Open on first chart
		DataSeries ds = Open;
		ds = MarketData.Chart(0).Open;
		
		// getting data series of Open on second chart
		ds = MarketData.Chart(1).Open;	
		
		//-----------------------
		// verify symbols and connections set by chart
		if(!MarketData.Chart(0).Connection.equals("XTestConn1")) throw new Exception("Error 1");
		if(!MarketData.Chart(0).Symbol.equals("XSymbol_1_1")) throw new Exception("Error 2");
		
		if(!MarketData.Chart(1).Connection.equals("XTestConn1")) throw new Exception("Error 3");
		if(!MarketData.Chart(1).Symbol.equals("XSymbol_1_2")) throw new Exception("Error 4");
		
		if(!MarketData.Chart(2).Connection.equals("XTestConn1")) throw new Exception("Error 5");
		if(!MarketData.Chart(2).Symbol.equals("XSymbol_1_3")) throw new Exception("Error 6");

		if(!MarketData.Chart(3).Connection.equals("History")) throw new Exception("Error 7");
		if(!MarketData.Chart(3).Symbol.equals("XSymbol_0_1")) throw new Exception("Error 8");

		if(!MarketData.Chart(4).Connection.equals("History")) throw new Exception("Error 9");
		if(!MarketData.Chart(4).Symbol.equals("XSymbol_0_2")) throw new Exception("Error 10");
		
	}

}		