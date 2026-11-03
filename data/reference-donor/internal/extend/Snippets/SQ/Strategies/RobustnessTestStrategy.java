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
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.event.ITradingEvent;
import com.strategyquant.tradinglib.event.ITradingEventListener;

public class RobustnessTestStrategy extends Strategy implements ITradingEventListener {

	private ILiveOrder order = null;
	private byte tradeType = OrderTypes.Buy;
	
	public int ExitAfterBars = 5;

	//----------------------------------------------------

	public RobustnessTestStrategy() {
	}

	//----------------------------------------------------

	@Override
	public void Initialize() throws Exception {
		setUpdateEventType(UpdateEventTypes.BarOpen);
	}

	//----------------------------------------------------

	@Override
	public void OnBarUpdate() throws Exception {
		if(order != null && order.getBarsInTrade() > ExitAfterBars) {
			order.Close(OrderCloseTypes.Deleted);
			order = null;
		}

		if(order == null) {
			tradeType = (tradeType == OrderTypes.Buy ? OrderTypes.Sell : OrderTypes.Buy);

			order = Trader.Open(tradeType, Symbol).setMagicNumber(0).SendAsync(this);

		} else {
			order.setSL(1.234).setPT(1.234).Send();
		}
	}

	//----------------------------------------------------

	@Override
	public void OnEvent(ITradingEvent event) throws Exception {
		// global event method, it is called every time
		//Log.debug("Global event ");
	}

	//----------------------------------------------------

	@Override
	public void OnTradingEvent(ITradingEvent event) throws Exception {
		// custom event method, called from SendAsync()
		//Log.debug("Local event ");
	}

}
