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
package SQ.ExitMethods;

import com.strategyquant.datalib.*;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.simulator.Engines;

@ClassConfig(name="Stop Loss")
@SortOrder(100)
public class StopLoss extends ExitMethod {

	@Parameter(category="Basic", showIfDefault=false)
	@Editor(type=Editors.Formula, formulaName="SLPT")
	@ExitType(ExitTypes.StopLoss)
	public IFormula StopLoss;

	private boolean debugTrailingStops = false;

	/** True when the entry block that owns this stop also carries a TrailingStop with a real formula.
	 *  It decides whether a fill-anchored stop may be left alone after the fill - see setForOrder.
	 *
	 *  <p>Written on EVERY entry by the block that wires the two together, never only raised: the answer
	 *  belongs to the block configuration of the moment, and a flag that is only ever set to true
	 *  outlives it.</p> */
	public boolean strategyTrailsThisStop = false;

	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------

	@Override
	public void setForOrder(ILiveOrder order, StrategyBase strategy) throws TradingException {
		if(order.isFilled()) {
			// A fill-anchored stop is already final: the level was resolved against the FILL price from
			// the distance computed on the creation bar, which is what the exported strategy's
			// Ticks-mode SetStopLoss does. Recomputing the formula here would replace it with a level
			// evaluated at the FILL bar, one frame newer, and move the stop off the level the platform
			// holds.
			//
			// No engine test is needed for that: a fill distance is written only where exits are
			// resolved at the fill - the simulator under its own hook, and the entry block for the
			// market fallback - and LiveOrderObj.init clears it, so anywhere else it is NOT_DEFINED and
			// this branch cannot fire.
			//
			// NOT when this strategy also trails: a trailed stop needs the call, because the trail is
			// what writes its level from then on.
			//
			// The TARGET deliberately has no counterpart to this: the exported strategy re-issues its
			// profit target from the formula after the fill, so ProfitTarget re-evaluating is what
			// matches the platform. The asymmetry is intended - do not make the two symmetrical.
			if(!strategyTrailsThisStop && order.getSLFillDistance() != Order.NOT_DEFINED) {
				return;
			}

			setOrderSLValue(order, strategy);
		}
		else {
			// An engine that attaches the initial exits to the ENTRY is answering for its platform: the
			// exported code gives a MARKET entry its stop before it submits the order, so the stop is
			// live from the fill and the entry bar's own range can take the trade out. Without the level
			// on the order the simulator materializes no exit order at all and the stop first appears on
			// the NEXT bar, so this side could not exit inside the entry bar while the platform does.
			// NinjaTrader is such an engine (SetStopLoss before the entry); TS/MC ask the same of the
			// UseInitialSLPT option, which is the second term below.
			//
			// PENDING entries are deliberately not symmetrical with that: the exported
			// EnterAtStop/EnterAtLimit submit WITHOUT pre-set levels and arm SL/PT one bar after the
			// fill, because this side does not exit a pending fill inside its entry bar. The export
			// side of that rule is Code/NinjaTrader/ExitMethods.inc (printPendingSLPTArm); read the
			// paragraph above as the market-entry case only.
			//
			// The engine property is read from StrategyBase, not computed here: snippets compile against
			// the SHIPPED SQAppLib jar, so a getter that is not in the installed jar yet does not resolve
			// and the whole snippet compilation fails with "cannot find symbol".
			boolean isTSMCEngine = strategy.getEngine() == Engines.Tradestation || strategy.getEngine() == Engines.MultiCharts;

			if(strategy.getAttachesInitialExitsAtEntry() || (isTSMCEngine && isInitialSLPTApplied(strategy))) {
				if(order.isMarketOrder()) {
					setInitialOrderSLValue(order, strategy);
				}
				else {
					setInitialExit(order, strategy);
				}
			}
		}
	}

	//------------------------------------------------------------------------ 
	// Metatrader

	private void setOrderSLValue(ILiveOrder order, StrategyBase strategy) throws TradingException {

		//int digits = Strategy.MarketData.getInstrumentInfo(order.getSymbol()).decimals;
		int direction = order.isLong() ? 1 : -1;

		double openPrice = order.isNettingMode() ? order.getLastOpenPrice(): order.getOpenPrice();

		double sl = StopLoss.evaluateFormula(strategy, order.getSymbol(), openPrice, -direction);
		if(sl == Order.NOT_DEFINED) return;

		sl = SQUtils.fixPrice(strategy.getInstrumentInfo().tickStep, sl);
		//sl = SQUtils.round(sl, digits);

		if(sl == openPrice) {
			// SL is same as open price, that cannot be set
			closeUnlessStopHeld(order);
			return;
		}

		sl = correctSLPT(order, sl, true);

		order.setSL(sl).Send();

		if(!order.isSuccessful()) {
			// we were not successful in setting StopLoss
			closeUnlessStopHeld(order);
		}
	}

	//------------------------------------------------------------------------

	/**
	 * Closes an order whose recomputed stop loss cannot be set, unless the order already holds a stop anchored to
	 * its fill: that stop stays in place and the order stays open.
	 *
	 * @param order the order whose stop was recomputed
	 * @throws TradingException if the order cannot be closed
	 */
	public static void closeUnlessStopHeld(ILiveOrder order) throws TradingException {
		if(order.getSLFillDistance() == Order.NOT_DEFINED) {
			order.Close(OrderCloseTypes.Deleted);
		}
	}

	//------------------------------------------------------------------------
	// TradeStation Multicharts

	private void setInitialOrderSLValue(ILiveOrder order, StrategyBase strategy) throws TradingException {

		//int digits = Strategy.MarketData.getInstrumentInfo(order.getSymbol()).decimals;
		int direction = order.isLong() ? 1 : -1;

		double openPrice = order.isNettingMode() ? order.getLastOpenPrice(): order.getOpenPrice();

		// An engine that decides on the bar close anchors a direct market entry's stop to the decision
		// bar CLOSE, not to the decision tick. The order is not filled yet here, so getOpenPrice() is
		// still the decision tick - replace it with that close. See EnterAtMarket.marketEntry
		// (slptAnchor).
		if(strategy.getDecidesOnBarClose() && !order.isFilled()) {
			// Close(0) at the decision event is the completed bar - the export's Close[0]; see
			// EnterAtMarket.marketEntry.
			openPrice = strategy.MarketData.Chart(order.getSymbol()).Close(0);
		}

		double sl = StopLoss.evaluateFormula(strategy, order.getSymbol(), openPrice, -direction);
		if(sl == Order.NOT_DEFINED) return;

		sl = SQUtils.fixPrice(strategy.getInstrumentInfo().tickStep, sl);
		//sl = SQUtils.round(sl, digits);

		if(sl == openPrice) {
			// SL is same as open price, that cannot be set. Close whole order
			order.Close(OrderCloseTypes.Deleted);
			return;
		}

		sl = correctSLPT(order, sl, true);

		order.setSL(sl).Send();

		if(!order.isSuccessful()) {
			// we were not successful in setting StopLoss, close whole order
			order.Close(OrderCloseTypes.Deleted);
		}
	}

	//------------------------------------------------------------------------

	@Override
	public double computeValue(byte orderType, StrategyBase strategy, String symbol, double price) throws TradingException {
		int direction = OrderTypes.isLongOrder(orderType) ? 1 : -1;

		double sl = StopLoss.evaluateFormula(strategy, symbol, price, -direction);  
		if(sl == Order.NOT_DEFINED) return Order.NOT_DEFINED;

		sl = SQUtils.fixPrice(strategy.getInstrumentInfo().tickStep, sl);

		double tickSize = strategy.getInstrumentInfo().tickSize;

		return correctSLPT(price, sl, direction, tickSize, true);		//used to calculate SL for money management methods
	}

	//------------------------------------------------------------------------

	/**
	 * used in Tradestation. SL, PT and other exits are not tied 
	 * with the exact orders but they are placed separately.
	 * @throws TradingException
	 */
	@Override
	public boolean setExit(ILiveOrder order, StrategyBase strategy) throws TradingException {
		int direction = order.isLong() ? 1 : -1;

		if(order.getOpenPrice() == 0) {
			return false;
		}

		// This method runs on EVERY bar of an open trade, because the engines that apply exits at the
		// end of the rule delete any exit order older than one bar and it has to be re-placed.
		// Re-PLACING does not require re-COMPUTING, and re-computing makes an ATR-based level drift
		// with every bar - NinjaTrader keeps the level it was given.
		//
		// The level is read back from the order rather than from a remembered entry value on purpose:
		// TrailingStop and MoveSL2BE write to order.setSL(), so reading it back keeps them working by
		// construction, where restoring a latched initial value would undo them on every bar.
		if(!strategy.getRecomputeExitLevelsEveryBar() && order.getSL() != Order.NOT_DEFINED) {
			return placeStopOrder(order, order.getSL(), direction, strategy);
		}

		double sl = StopLoss.evaluateFormula(strategy, order.getSymbol(), order.getOpenPrice(), -direction);
		if(sl == Order.NOT_DEFINED) {
			return false;
		}

		sl = SQUtils.fixPrice(Strategy.getInstrumentInfo().tickStep, sl);

		if(debugTrailingStops) Log.info(SQTime.toDateMinuteString(Strategy.Time(0))+" - Setting SL to: {}, corrected: {}", sl, correctSLPT(order, sl, true));

		sl = correctSLPT(order, sl, true);

		// set it also here. It is not used in trading engine, but this way Trailing stop knows the actual SL
		order.setSL(sl).Send();

		return placeStopOrder(order, sl, direction, strategy);
	}

	//------------------------------------------------------------------------

	/**
	 * Places the stop order for an open trade at a level that has already been computed.
	 *
	 * <p>Factored out of {@link #setExit} so that re-placing an existing level and computing a fresh one
	 * go through exactly the same code. The bar-close engines re-place the exit order on every bar - the
	 * simulator deletes any older than one - and re-evaluating the formula to do so would make
	 * ATR-based levels drift.</p>
	 *
	 * @param order the open order the stop belongs to
	 * @param sl the price level, already fixed to the tick step and corrected
	 * @param direction 1 for a long trade, -1 for a short one
	 * @param strategy the running strategy
	 * @return true - the stop was handled for this order, whether or not an exit order was needed
	 * @throws TradingException if the exit order cannot be placed
	 */
	private boolean placeStopOrder(ILiveOrder order, double sl, int direction, StrategyBase strategy)
			throws TradingException {
		if(!shouldApplySLPTToOrder(order, strategy)) {
			return true;
		}

		// An engine that keeps ONE protective stop per position places it once per bar, after every exit
		// method has had its say - the level that counts is the last one written. Placing here would use
		// the level as it stands BEFORE the trailing stop runs, since this method comes first in the
		// exit-method list. Returning false hands the placement to the single call at the end of
		// EnterAtMarket.OnApplyExits, which carries the submission guard. NinjaTrader is such an engine:
		// SetStopLoss amends the one order rather than adding a second.
		if(strategy.getKeepsOneProtectiveStop()) {
			return false;
		}

		byte orderType = (direction < 0 ? OrderTypes.BuyToCoverStop : OrderTypes.SellToCoverStop);

		ILiveOrder slOrder = Strategy.Trader.Open(orderType, order.getSymbol(), sl)
				.setComment("ExitSL")
				.setMagicNumber(order.getMagicNumber())
				.setEntryOrderId(order.getOrderId())
				.Send();

		return true;
	}

	public boolean setInitialExit(ILiveOrder order, StrategyBase strategy) throws TradingException {
		int direction = order.isLong() ? 1 : -1;

//		if(order.getOpenPrice() == 0) {
//			return false;
//		}

		double sl = StopLoss.evaluateFormula(strategy, order.getSymbol(), 0, 1);
		if(sl == Order.NOT_DEFINED || sl <= 0) {
			return false;
		}

		// Called with openPrice 0, so what comes back here is a DISTANCE - unlike setExit above, which
		// passes the open price and gets a price level. The distinction decides how a half tick breaks.
		// A formula that returns an absolute level (a price read from a block) gives the same value
		// whatever price it is handed, so it is recognised by that: its distance is the level's distance
		// from the order price, and it is anchored to the fill like any other.
		double orderPrice = order.getOpenPrice();
		if(orderPrice > 0 && StopLoss.evaluateFormula(strategy, order.getSymbol(), orderPrice, 1) == sl) {
			sl = Math.abs(orderPrice - sl);
			if(sl <= 0) {
				return false;
			}
		}
		sl = fixInitialStopDistance(strategy, order, sl);

		if(debugTrailingStops) Log.info(SQTime.toDateMinuteString(Strategy.Time(0))+" - Setting SL to: {}, corrected: {}", sl, correctSLPT(order, sl, true));

		sl = correctSLPT(order, sl, true);

		order.setSL(sl).Send();

		if(!shouldApplySLPTToOrder(order, strategy)) {
			return true;
		}

		byte orderType = (direction < 0 ? OrderTypes.BuyToCoverStop : OrderTypes.SellToCoverStop);

		ILiveOrder slOrder = Strategy.Trader.Open(orderType, order.getSymbol(), sl)
				.setComment("ExitSL")
				.setMagicNumber(order.getMagicNumber())
				.setEntryOrderId(order.getOrderId())
				.Send();

		return true;
	}

	//------------------------------------------------------------------------

	// Snaps an initial stop-loss DISTANCE to the tick grid the way an engine that resolves it into a
	// PRICE would snap the price it ends up as.
	//
	// On such an engine the resulting price is rounded to the tick grid with ties going UP in both
	// directions - not half-even. This side rounds the DISTANCE, and SQUtils.fixPrice does it with
	// Math.round, whose tie also goes up - that is, always AWAY from the entry. For a short the stop sits
	// above the entry, so both rules move the level the same way and agree. For a long they are
	// opposites: away from the entry is DOWN in price, so an exact half tick lands one tick below where
	// such an engine puts it.
	//
	// Only the long branch changes, and only where the engine says so. The entry price is itself on the
	// tick grid, so a tie in price space is exactly a tie in distance space and the mapping is direction
	// alone - no fill price is needed, which matters because this runs while the entry is still pending.
	private double fixInitialStopDistance(StrategyBase strategy, ILiveOrder order, double distance) {
		double tickStep = Strategy.getInstrumentInfo().tickStep;

		if(!strategy.getRoundsStopTiesUpInPrice() || !order.isLong() || tickStep <= 0) {
			return SQUtils.fixPrice(tickStep, distance);
		}

		// Math.ceil(t - 0.5) leaves every non-tie where Math.round would put it and sends the exact
		// half to the LOWER tick count, which is the higher price - where such an engine puts a long's
		// stop.
		double ticks = Math.ceil((distance / tickStep) - 0.5);
		return SQUtils.fixPrice(tickStep, ticks * tickStep);
	}

	//------------------------------------------------------------------------

	@Override
	public IBlock clone(boolean includingParameters, StrategyBase strategy) throws BlockDefinitionException {
		return this; //no need to clone
	}

}