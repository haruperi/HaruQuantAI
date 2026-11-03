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
import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.event.ITradingEvent;
import com.strategyquant.tradinglib.event.ITradingEventListener;

public class CompleteStrategySample extends Strategy {
	
	@Override
	public void Initialize() throws Exception {
		// we can check / set if we want to call onBarUpdate on open, on every tick or on close
		int et = getEventType();
		setUpdateEventType(UpdateEventTypes.BarOpen);
		//setEventType(EventType.OnClose);
		//setEventType(EventType.OnTick);
	}

	@Override
	public void OnBarUpdate() throws Exception {

		Log.debug("Tick processed!");
		
		if(false) StopStrategy();
		
		int i = UpdatedChart;
		boolean b = MultipleChartsUpdated;
		int t = UpdateEventType;
		
		int bars = Bars();
		
		long time = MarketData.Chart(0).Time(0);
		String symbol = MarketData.Chart(0).Symbol;
		String connection = MarketData.Chart(0).Connection;
		String timeframe = MarketData.Chart(0).Timeframe;

		int et = MarketData.Chart(0).EventType;
		
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
/*
 		LiveOrder position;
 		
		position = Trader.Buy(Symbol).setSize(Size);
		position = Trader.Sell(Symbol).setSize(Size);
		position = Trader.BuyLimit(Symbol, Price).setSize(Size);
		position = Trader.SellLimit(Symbol, Price).setSize(Size);
		position = Trader.BuyStop(Symbol, Price).setSize(Size);
		position = Trader.SellStop(Symbol, Price).setSize(Size);

		position.Close();
		position.CloseAsync();
		position.CloseAsync(new TradingEventListener() {
			@Override
			public void onTradingEvent(TradingEvent event) {
				// TODO Auto-generated method stub
				
			}});
		
		position.setSL(123.66).Send();
		
		Trader.Buy(Symbol).setSize(Size).setSL(123.45).setPT(12345).setMagicNumber(0).setComment("Some comment").setExpiration(SQTimeC.toLong(2016, 12, 12, 12, 12, 12)).setMaxSlippage(0.3).Send();

		position = Trade.Open(TradeType.Buy, Symbol, Size, Price, StopLoss, ProfitTarget, Comment);
		position = Trade.Open(TradeType.Buy, Symbol, Size);
		position = Trade.OpenAsync(TradeType.Buy, Symbol, Size, Price, StopLoss, ProfitTarget, Comment);

		position = Trade.Buy(Symbol, Size, Price, StopLoss, ProfitTarget, Comment);
		position = Trade.BuyAsync(Symbol, Size, Price, StopLoss, ProfitTarget, Comment);
		position = Trade.Sell(Symbol, Size, Price, StopLoss, ProfitTarget, Comment);
		position = Trade.SellAsync(Symbol, Size, Price, StopLoss, ProfitTarget, Comment);

		OrdersList historyOrders = Trader.GetHistoryTrades();
		//position = Trade.getPosition(TradeType.Buy, Symbol, Comment);
		
		
		boolean b;
		
		b = position.isSuccessful();
		
		for(int i=0; i<Trader.GetOpenOrdersCount(); i++) {
			LiveOrder pos = Trader.GetOpenOrder(i);

			//b = pos.isPendingOrder();
			//Price = pos.getOpenPrice();
			//Price = pos.getClosePrice();
			
		}
*/		
	}
}
