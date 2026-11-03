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

import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;

/**
 * strategy that opens trade every 30 minutes, it should be used to test that backtest in SQTrader matches real trading in MT4.
 * @author maros
 *
 */
public class LiveTestStrategy1 extends Strategy {
	
	ILiveOrder order = null;
	
	//----------------------------------------------------
	
	@Override
	public void Initialize() throws Exception {
		setUpdateEventType(UpdateEventTypes.BarOpen);
	}

	//----------------------------------------------------
	
	@Override
	public void OnBarUpdate() throws Exception {
		
		if(order != null && order.getBarsInTrade() >=4) {
			// close trade after 4 bars
			order.Close(OrderCloseTypes.Manual);
			order = null;
		}
		
		if(order == null) {
			byte tradeType = 0;
			
			// open buy order on full hour or sell order on half hour
			SQTimeOld timeNow = new SQTimeOld(this.Time(0));
			if(timeNow.getMinute() == 0) {
				tradeType = OrderTypes.Buy;
			} else if(timeNow.getMinute() == 30) {
				tradeType = OrderTypes.Sell;
			}
			
			if(tradeType != 0) {
				order = Trader.Open(tradeType, Symbol, 1).setMagicNumber(0).setComment("LiveTestStrategy1").Send();
			}
		}
	}
	
}
