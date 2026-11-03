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

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;

public class CCIReverse extends Strategy {
	
	@Override
	public void Initialize() throws Exception {
		//setUpdateEventType(UpdateEventTypes.BarTick);
		//setUpdateEventType(UpdateEventTypes.BarOpen);
	}

	@Override
	public void OnBarUpdate() throws Exception {
		if(UpdateEventType != UpdateEventTypes.BarOpen) {
			return;
		}

		ChartData chartData = MarketData.Chart(0);
		
		double cciValue = Indicators.CCI(Open, 20).Value.get(0);

		if(cciValue > 0) {
			closeOppositeOrder(1234, OrderTypes.Sell);
			
			Trader.Buy(Symbol).setMagicNumber(1234).Send();
		}
		
		if(cciValue < 0) {
			closeOppositeOrder(1234, OrderTypes.Buy);
			
			Trader.Sell(Symbol).setMagicNumber(1234).Send();
			
			Trader.getAccountBalance();
		}
	}

	private void closeOppositeOrder(int magicNumber, byte orderType) throws TradingException {
		
		for(int i=0; i<Trader.getOpenOrdersCount(true); i++) {
			ILiveOrder order = Trader.getOpenOrder(i, true);
			
			if(order.getMagicNumber() == magicNumber && order.getOrderType() == orderType) {
				order.Close(OrderCloseTypes.Reversed);
			}
		}
	}
}