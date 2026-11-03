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
package SQ.Blocks.Order.Open;

import java.util.ArrayList;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.ATMExit;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.BuildingBlock;
import com.strategyquant.tradinglib.CategoryOrder;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.Editors;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.ExitTypes;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.IActionEventListener;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.Required;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.SortOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.exits.None;
import com.strategyquant.tradinglib.atm.exits.TrailingStop;
import com.strategyquant.tradinglib.simulator.Engines;
import SQ.ExitMethods.StopLoss;
import SQ.Functions.OrderFunctions;
import SQ.Internal.ActionBlock;
import SQ.Internal.MMFormulaBlock;

@BuildingBlock(name="(MKT) Enter at market", display="EnterAtMarket", returnType=ReturnTypes.Order)
@Help("Opens order at current market price")
@SortOrder(100)
@CategoryOrder(100)
public class EnterAtMarket extends ActionBlock {

	private static final int MaxDistanceFromMarketHash = "MaxDistanceFromMarket.MaxDistanceFromMarket".hashCode();
	private static final int MaxDistanceFromMarketPctHash = "MaxDistanceFromMarket.MaxDistancePct".hashCode();
	
	// Basic parameters
	@Parameter(defaultValue="Any", category="Basic", showIfDefault=false)
	@Editor(type=Editors.SelectionSymbolsWithAny)
	public String Symbol;
	
	@Parameter(defaultValue="1", category="Basic")
	@Editor(type=Editors.Selection, values="Long=1,Short=-1")
	public int Direction;

	@Parameter(category="Basic")
	@Editor(type=Editors.Formula, formulaName="Size")
	@Required
	public IFormula Size;

	// Other parameters
	@Parameter(defaultValue="MagicNumber", category="Order identification", showIfDefault=false)
	@Help("Magic number is used to identify this trade, it should be unique for every trade you open.")
	@Editor(type=Editors.SelectionVariables)
	public int MagicNumber;

	@Parameter(defaultValue="", category="Order identification", showIfDefault=false)
	public String Comment;
	
	@Parameter(defaultValue="false", category="Order identification", showIfDefault=false)
	@Help("If set to true, it will allow to place multiple trades with the same Magic Number")
	public boolean AllowDuplicateTrades;
	
	public ExitMethod[] ExitMethods;

	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	
	@Override
	public void OnAction() throws TradingException {
		sqNtSnapshotWorkingEntries();
		marketEntry();
	}

	//------------------------------------------------------------------------

	/**
	 * Whether an opposite-direction pending entry is WORKING at this moment on the NinjaTrader side.
	 *
	 * <p>The export skips its market fallback in that state, because a market entry that fills while
	 * an opposite entry order is working receives no protective orders at all from the Managed
	 * approach - see sqOppositeEntryWorking in SQ.inc. The backtest has to skip the same
	 * entries or it reports trades the exported strategy will not take.</p>
	 *
	 * <p>A pending queued on THIS bar does not count. The export does not submit where the rule
	 * decides: it queues, and sqFlushPendingEntries submits after the last rule, so a fallback firing
	 * in any rule sees no order from this bar at all. This side places immediately, so the same-bar
	 * case has to be excluded here by hand.</p>
	 */
	protected boolean sqNtOppositeEntryWorking() throws TradingException {
		StrategyBase.EntryBarState atOpen = Strategy.entryBarState;

		// No snapshot on this bar means no entry action has run on it, so nothing of this bar's has
		// replaced anything either. Every caller takes one first - see sqNtSnapshotWorkingEntries.
		if(atOpen.snapshotBarTime != Strategy.Time(0)) {
			return false;
		}

		// this block asks about the OPPOSITE of its own direction
		return Direction > 0 ? atOpen.shortWorkingAtOpen : atOpen.longWorkingAtOpen;
	}

	//------------------------------------------------------------------------

	/**
	 * Records which directions had a working pending ENTRY when this bar opened, once per bar and
	 * before any rule replaces one.
	 *
	 * <p>Called at the very top of the action, which is the last moment the bar's starting state can
	 * still be seen: the entry rule that runs first closes the pending it is about to re-place.</p>
	 *
	 * <p>This is the state the EXPORT reasons about. NinjaTrader carries one entry order per signal
	 * name across bars and amends its level, so an order placed bars ago is still working when a rule
	 * asks. This side closes its pending and places a new one every bar, so by the time a rule asks,
	 * the only pending present is the one this bar just queued - which the export has not submitted
	 * yet. Reading the live orders therefore answers a different question than the export's.</p>
	 */
	protected void sqNtSnapshotWorkingEntries() throws TradingException {
		if(Strategy.getEngine() != Engines.NinjaTrader) {
			return;
		}

		StrategyBase.EntryBarState atOpen = Strategy.entryBarState;
		if(atOpen.snapshotBarTime == Strategy.Time(0)) {
			return;
		}

		boolean longWorking = false;
		boolean shortWorking = false;

		for(int i=0; i<Strategy.Trader.getOpenOrdersCount(false); i++) {
			ILiveOrder order = Strategy.Trader.getOpenOrder(i, false);

			if(!order.isPendingOrder() || !order.getStrategyName().equals(Strategy.getStrategyName())) {
				continue;
			}

			if(order.getDirection() > 0) {
				longWorking = true;
			}
			else {
				shortWorking = true;
			}
		}

		// A pending the exported strategy parked on the previous bar is still working there: the
		// amend that parks it keeps it working through this bar's rules too - see sqNtRecordPark.
		long previousBar = Strategy.Time(1);
		longWorking |= atOpen.longParkedBarTime == previousBar;
		shortWorking |= atOpen.shortParkedBarTime == previousBar;

		atOpen.longWorkingAtOpen = longWorking;
		atOpen.shortWorkingAtOpen = shortWorking;
		atOpen.snapshotBarTime = Strategy.Time(0);
	}

	//------------------------------------------------------------------------

	/**
	 * Records that the exported strategy PARKS this block's direction on this bar.
	 *
	 * <p>A market entry beside a pending of its own direction that has been working since an earlier bar
	 * cannot go in under that pending's signal name, so the export amends the pending to a price the
	 * market cannot reach and enters under the F-suffixed name - the pending blocks' market fallback and,
	 * where the direction also has a pending block, the market entry blocks. The amend keeps the parked
	 * order working through the next bar's rules as well, where it blocks the other direction: the
	 * fallback guard (sqNtOppositeEntryWorking) and the simulator's refusal of an opposite pending. The
	 * pending on this side has been replaced or has expired by then, so the park is recorded here and
	 * read by both. It does not count as a pending entry of the strategy - the export does not count it
	 * either.</p>
	 *
	 * <p>Called right before the market order is submitted, when a pending of the direction was working
	 * when the bar opened - the condition the export parks under.</p>
	 *
	 * @throws TradingException if the bar time cannot be read
	 */
	protected void sqNtRecordPark() throws TradingException {
		if(Strategy.getEngine() != Engines.NinjaTrader) {
			return;
		}

		StrategyBase.EntryBarState atOpen = Strategy.entryBarState;
		if(atOpen.snapshotBarTime != Strategy.Time(0)) {
			return;
		}

		if(Direction > 0 && atOpen.longWorkingAtOpen) {
			atOpen.longParkedBarTime = Strategy.Time(0);
		}
		else if(Direction < 0 && atOpen.shortWorkingAtOpen) {
			atOpen.shortParkedBarTime = Strategy.Time(0);
		}
	}

	//------------------------------------------------------------------------

	/**
	 * The market-entry body of {@link #OnAction}, callable from subclasses. The pending entry
	 * blocks need it on the NinjaTrader engine: the exported strategy falls back to a MARKET
	 * entry when its pending level is already through the close, and this is the exact counterpart
	 * of that fallback - Java has no super.super, so the body is factored out instead.
	 */
	protected void marketEntry() throws TradingException {
		if((!AllowDuplicateTrades || !engineSupportsDuplicateTrades()) && checkLiveOrderExists(0, true) != null) {
			// market is not flat and duplicate trades are not allowed
			return;
		}

		if(Strategy != null && Strategy.Trader != null && !Strategy.Trader.IsMarketOpen()) {
			// market is not open (MT5 feature since Build 140)
			return;
		}
/*
		String ss = SQTime.toDateMinuteString(Strategy.Time(0));
		if(ss.contains("2022.04.12 13:00")) {
			int a = 1;
			int b = a;
		}
*/
		// open trade
		byte orderType = (Direction > 0 ? OrderTypes.Buy : OrderTypes.Sell);

		// The price the SL/PT formulas are anchored to: the decision price - Ask for a long, Bid for a
		// short, or the completed bar's close on an engine that decides on the bar close
		// (StrategyBase.decisionAsk / decisionBid).
		double slptAnchor = Direction > 0 ? Strategy.decisionAsk(Symbol, 0) : Strategy.decisionBid(Symbol, 0);

		double sl = computeSL(orderType, slptAnchor);
		double size = computeSize(orderType, 0, sl);

		if(sl == slptAnchor) {
			return;
		}

		sqNtRecordPark();

		ATM atm = Strategy.getATM();

		if(atm != null && atm.isApplicable(Strategy, size, sl, orderType)) {
			double pt = computePT(orderType, slptAnchor);

			openATMOrder(atm, -1, size, sl, pt, orderType, 0);
		
		} else {
			openNormalOrder(-1, size, sl, orderType, 0);
		}
	}

	//------------------------------------------------------------------------

	protected void openATMOrder(ATM atm, double openPrice, double fullSize, double sl, double pt, byte orderType, int barsValid) throws TradingException {
		ExitMethod slExit = getStopLossExit();
		double sizeSoFar = 0;
		
		if(Strategy.getEngine() == Engines.MetaTrader4 || Strategy.getEngine() == Engines.MetaTrader5Hedged) {
			for(int i=0; i<atm.getExitsCount(); i++) {
				ATMExit atmExit = tryCloneATMExit(atm.getExit(i));
			
				boolean isLastExit = (i == atm.getExitsCount()-1);
				double size = atmExit.computeSize(fullSize, sizeSoFar, isLastExit);
				
				if(size > 0) {
					ILiveOrder order = Strategy.Trader.Open(orderType, Symbol, openPrice)
							.setSize(size)
							.setMagicNumber(MagicNumber)
							.setComment(Comment)
							.Send();
	
					sizeSoFar += order.getSize();
					
					if(order.isSuccessful()) {
						handleBarsValid(order, barsValid);
						
						// add standard SL
						if(slExit != null && !order.isClosedOrder()) {
							slExit.setForOrder(order, Strategy);
						}
						
						// add ATM exit
						atmExit.setForOrder(order, Strategy, sl, pt);
					}
				}
			}
		}
		else {
			ILiveOrder order = Strategy.Trader.Open(orderType, Symbol, openPrice)
					.setSize(fullSize)
					.setMagicNumber(MagicNumber)
					.setComment(Comment)
					.Send();

			if(order.isSuccessful()) {
				handleBarsValid(order, barsValid);
				
				// add standard SL
				if(slExit != null && !order.isClosedOrder()) {
					slExit.setForOrder(order, Strategy);
				}
				
				for(byte i=0; i<atm.getExitsCount(); i++) {
					ATMExit atmExit = tryCloneATMExit(atm.getExit(i));
					boolean isLastExit = (i == atm.getExitsCount() - 1);
					double size = atmExit.computeSize(fullSize, sizeSoFar, isLastExit);
					
					if(size > 0) {
						sizeSoFar += Strategy.getEngine() == Engines.MetaTrader5Netted ? openNewATMNettingOrder(order, atmExit, size, sl, pt, i) : openNewTSATMOrder(order, atmExit, size, sl, pt, i);
					}
				}
			}
		}
	}

	//------------------------------------------------------------------------

	private double openNewTSATMOrder(ILiveOrder mainOrder, ATMExit atmExit, double size, double sl, double pt, byte exitIndex) throws TradingException {
		mainOrder.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
			private ILiveOrder exitOrder = null;
			private double actualSL = -1, actualPT = -1;
			private double lastTS = -1;
			private boolean filled = false;
			
			@Override
			public void OnActionEvent(StrategyBase strategy) throws TradingException {
				if(mainOrder.isClosedOrder()) {
					if(exitOrder != null) {
						exitOrder.Close(OrderCloseTypes.Deleted);
						exitOrder = null;
					}
					return;
				}
				
				if(!mainOrder.isMarketOrder()) return;
				
				//SL and PT must be calculated when order is filled. Otherwise it may use old indicator values (TradeStation fills on next bar)
				
				actualSL = computeSL(mainOrder.getOrderType(), mainOrder.getOpenPrice());
				actualPT = computePT(mainOrder.getOrderType(), mainOrder.getOpenPrice());
				
				if(atmExit.exitLevel instanceof None) {
					None noneExit = (None) atmExit.exitLevel;
					
					if(noneExit.checkExitAfterBars(mainOrder)) {
						noneExit.deactivate();
						
						Strategy.Trader.Open(mainOrder.isLong() ? OrderTypes.Sell : OrderTypes.Buy, mainOrder.getSymbol(), 0)
								.setSize(size)
								.setMagicNumber(MagicNumber)
								.setComment(Comment)
								.setExitIndex(exitIndex)
								.Send();
					}
				}
				else if(atmExit.exitLevel instanceof TrailingStop) {		
					if(filled) return;
					
					double newTrailingPrice = SQUtils.fixPrice(Strategy.getInstrumentInfo().tickStep, atmExit.exitLevel.getNettingPrice(Strategy, mainOrder, actualSL, actualPT));
					
					if(mainOrder.isLong()) {
						if(newTrailingPrice > mainOrder.getOpenPrice() && newTrailingPrice > actualSL && newTrailingPrice > lastTS) {
							//move trailing exit closer to current price
							lastTS = newTrailingPrice;
						}
					}
					else {
						if(newTrailingPrice < mainOrder.getOpenPrice() && newTrailingPrice < actualSL && (newTrailingPrice < lastTS || lastTS < 0)) {
							//move trailing exit closer to current price
							lastTS = newTrailingPrice;
						}
					}

					if(exitOrder != null) {
						if(exitWasFilled(exitOrder)) {	//Trailing stop has been hit
							filled = true;
							return;		
						}
						else {
							exitOrder.Close(OrderCloseTypes.Replaced);
						}
					}
					
					if(lastTS > 0) {
						exitOrder = Strategy.Trader.Open(Direction > 0 ? OrderTypes.SellStop : OrderTypes.BuyStop, Symbol, lastTS)
							.setSize(size)
							.setMagicNumber(MagicNumber)
							.setComment(Comment)
							.setExitIndex(exitIndex)
							.Send();

						exitOrder.registerEvent(UpdateEventTypes.OrderFilled, new IActionEventListener() {
							@Override
							public void OnActionEvent(StrategyBase Strategy) throws TradingException {
								if(exitWasFilled(exitOrder)) {
									filled = true;
								}
							}
						});
					}
				}
				else {
					if(filled) return;
					
					double exitOpenPrice = SQUtils.fixPrice(Strategy.getInstrumentInfo().tickStep, atmExit.exitLevel.getNettingPrice(Strategy, mainOrder, actualSL, actualPT));

					if(exitOpenPrice <= 0) {
						return;
					}
					
					if(exitOrder != null) {
						if(exitWasFilled(exitOrder)) return;
						else {
							exitOrder.Close(OrderCloseTypes.Deleted);
							exitOrder = null;
						}
					}
					
					exitOrder = Strategy.Trader.Open(Direction > 0 ? OrderTypes.SellLimit : OrderTypes.BuyLimit, Symbol, exitOpenPrice)
							.setSize(size)
							.setMagicNumber(MagicNumber)
							.setComment(Comment)
							.setExitIndex(exitIndex)
							.Send();
					
					if(exitOrder.isSuccessful()) {
						exitOrder.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
							@Override
							public void OnActionEvent(StrategyBase strategy) throws TradingException {
								boolean mainOrderExists = false;
								
								for(int i=Strategy.Trader.getOpenOrdersCount(false) - 1; i >= 0; i--) {
									ILiveOrder order = Strategy.Trader.getOpenOrder(i, false);
									
									if(order.getOrderId() == mainOrder.getOrderId()) {
										mainOrderExists = true;
									}
								}
								
								if(!mainOrderExists) {
									exitOrder.Close(OrderCloseTypes.Deleted);
								}
							}
						});	
						exitOrder.registerEvent(UpdateEventTypes.OrderFilled, new IActionEventListener() {
							@Override
							public void OnActionEvent(StrategyBase Strategy) throws TradingException {
								if(exitWasFilled(exitOrder)) {
									filled = true;
								}
							}
						});
					}
				}
			}
		});	
		
		return size;
	}
	
	//------------------------------------------------------------------------

	private double openNewATMNettingOrder(ILiveOrder mainOrder, ATMExit atmExit, double size, double sl, double pt, byte exitIndex) throws TradingException {
		// for None attach a BarOpen event listener and close after number of bars set
		
		if(atmExit.exitLevel instanceof None) {
			mainOrder.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
				@Override
				public void OnActionEvent(StrategyBase strategy) throws TradingException {
					if(mainOrder.isClosedOrder() || !mainOrder.isMarketOrder()) return;
					
					None noneExit = (None) atmExit.exitLevel;
					
					if(noneExit.checkExitAfterBars(mainOrder)) {
						noneExit.deactivate();
						
						ILiveOrder exitOrder = Strategy.Trader.Open(mainOrder.isLong() ? OrderTypes.Sell : OrderTypes.Buy, mainOrder.getSymbol(), 0)
								.setSize(size)
								.setMagicNumber(MagicNumber)
								.setComment(Comment)
								.setExitIndex(exitIndex)
								.Send();
					}
				}
			});	
			
			return size;
		}
		else if(atmExit.exitLevel instanceof TrailingStop) {
			mainOrder.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
				private ILiveOrder exitOrder = null;
				private double lastTS = -1;
				private boolean filled = false;
				
				@Override
				public void OnActionEvent(StrategyBase strategy) throws TradingException {
					if(filled) return;
					
					if(mainOrder.isClosedOrder()) {
						if(exitOrder != null) {
							exitOrder.Close(OrderCloseTypes.Deleted);
							exitOrder = null;
						}
						return;
					}
					
					if(mainOrder.isMarketOrder()) {
						double newTrailingPrice = SQUtils.fixPrice(Strategy.getInstrumentInfo().tickStep, atmExit.exitLevel.getNettingPrice(Strategy, mainOrder, mainOrder.getSL(), mainOrder.getPT()));
						double prevTS = lastTS;
						
						if(mainOrder.isLong()) {
							if(newTrailingPrice > mainOrder.getOpenPrice() && newTrailingPrice > mainOrder.getSL() && newTrailingPrice > lastTS) {
								//move trailing exit closer to current price
								lastTS = newTrailingPrice;
							}
						}
						else {
							if(newTrailingPrice < mainOrder.getOpenPrice() && newTrailingPrice < mainOrder.getSL() && (newTrailingPrice < lastTS || lastTS < 0)) {
								//move trailing exit closer to current price
								lastTS = newTrailingPrice;
							}
						}
						
						if(prevTS != lastTS && lastTS > 0) {
							if(exitOrder != null) {
								exitOrder.Close(OrderCloseTypes.Replaced);
							}
							
							exitOrder = Strategy.Trader.Open(Direction > 0 ? OrderTypes.SellStop : OrderTypes.BuyStop, Symbol, lastTS)
								.setSize(size)
								.setMagicNumber(MagicNumber)
								.setComment(Comment)
								.setExitIndex(exitIndex)
								.Send();
							
							exitOrder.registerEvent(UpdateEventTypes.OrderFilled, new IActionEventListener() {
								@Override
								public void OnActionEvent(StrategyBase Strategy) throws TradingException {
									if(exitWasFilled(exitOrder)) {
										filled = true;
									}
								}
							});
						}
					}
				}
			});	

			return size;
		}
		
		// for other types create limit orders
		
		double exitOpenPrice = SQUtils.fixPrice(Strategy.getInstrumentInfo().tickStep, atmExit.exitLevel.getNettingPrice(Strategy, mainOrder, sl, pt));

		if(exitOpenPrice <= 0) {
			return 0;
		}
		
		ILiveOrder exitOrder = Strategy.Trader.Open(Direction > 0 ? OrderTypes.SellLimit : OrderTypes.BuyLimit, Symbol, exitOpenPrice)
				.setSize(size)
				.setMagicNumber(MagicNumber)
				.setComment(Comment)
				.setExitIndex(exitIndex)
				.Send();
		
		if(exitOrder.isSuccessful()) {
			exitOrder.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
				@Override
				public void OnActionEvent(StrategyBase strategy) throws TradingException {
					boolean mainOrderExists = false;
					
					for(int i=Strategy.Trader.getOpenOrdersCount(false) - 1; i >= 0; i--) {
						ILiveOrder order = Strategy.Trader.getOpenOrder(i, false);
						
						if(order.getOrderId() == mainOrder.getOrderId()) {
							mainOrderExists = true;
						}
					}
					
					if(!mainOrderExists) {
						exitOrder.Close(OrderCloseTypes.Deleted);
					}
				}
			});	
			
			return size;
		}
		else return 0;
	}

	//------------------------------------------------------------------------

	private boolean exitWasFilled(ILiveOrder exitOrder) {
		return exitOrder.isMarketOrder() && exitOrder.getCloseTime() > 0;
	}
	
	//------------------------------------------------------------------------

	/** Set by the pending entry blocks around the market fallback they turn a through-the-market level
	 * into. It says only WHICH path this entry took; whether that path's protective exits are
	 * fill-anchored distances is the engine's answer, StrategyBase.getAnchorsFallbackExitsToFill().
	 * See ILiveOrder.setSLFillDistance. */
	protected boolean ntPendingFallback = false;

	protected void openNormalOrder(double openPrice, double size, double sl, byte orderType, int barsValid) throws TradingException {
		ILiveOrder order = Strategy.Trader.Open(orderType, Symbol, openPrice)
				.setSize(size)
				.setMagicNumber(MagicNumber)
				.setComment(Comment);

		// Which entry this order counts as, set BEFORE it is submitted because the admission rule reads
		// it there. A pending block's market fallback goes out under a name of its own, so on an engine
		// that limits its entries per signal name it does not take the direction's market entry away.
		order.setOpenedByPendingFallback(ntPendingFallback);

		order = order.Send();

		if(order.isSuccessful()) {
			handleBarsValid(order, barsValid);

			// An entry fallback on an engine that anchors such exits to the fill: carry the stop AND
			// target as distances - the absolute levels were computed against the decision price, and
			// re-anchoring the same distances to the fill is what the exported strategy's Ticks-mode
			// SetStopLoss/SetProfitTarget pair does. The recovery anchor must be the SAME price the
			// levels were computed from, which is why it repeats marketEntry's slptAnchor expression
			// rather than naming a price: the distance then round-trips exactly back to the formula's
			// own distance.
			if(ntPendingFallback && Strategy.getAnchorsFallbackExitsToFill()) {
				double anchor = Direction > 0 ? Strategy.decisionAsk(Symbol, 0) : Strategy.decisionBid(Symbol, 0);

				if(sl != Order.NOT_DEFINED && sl != 0) {
					order.setSLFillDistance(Math.abs(anchor - sl));
				}

				double pt = computePT(orderType, anchor);
				if(pt != Order.NOT_DEFINED && pt != 0 && pt != anchor) {
					order.setPTFillDistance(Math.abs(anchor - pt));
				}
			}

			// An engine that bounds the trail by the Stop Loss formula re-evaluates that formula every
			// bar as the trail's floor, so the TrailingStop exit method needs a reference to it - the
			// two methods have no other channel to each other. Wired here because every entry block
			// inherits this loop, and this is the only place that hands the formula over: downstream
			// TrailingStopHandler recognises the bound by having been given one at all.
			if(Strategy.getBoundsTrailByStopLossFormula()) {
				ExitMethod slExit = getStopLossExit();
				IFormula slFormula = slExit instanceof StopLoss ? ((StopLoss) slExit).StopLoss : null;
				for(ExitMethod exitMethod : ExitMethods) {
					if(exitMethod instanceof SQ.ExitMethods.TrailingStop) {
						((SQ.ExitMethods.TrailingStop) exitMethod).setStopLossFloorFormula(slFormula);
					}
				}
			}

			for(ExitMethod exitMethod : ExitMethods) {
				if(!order.isClosedOrder()) {
					if(AllowDuplicateTrades) {
						//we have to clone the exit method, otherwise it makes problems when strategy has duplicate trades enabled (problem example: Trailing Stop is set only for the first order)
						try {
							ExitMethod exitMethodCloned = (ExitMethod) exitMethod.clone(true, Strategy);
							exitMethodCloned.setForOrder(order, Strategy);
						} 
						catch (BlockDefinitionException e) {
							Log.error("Cannot clone exit method '" + exitMethod.getClass().getName() + "' for order #" + order.getOrderId(), e);
						}
					}
					else {
						exitMethod.setForOrder(order, Strategy);
					}
				}
			}

			armPendingExitsAfterFill(order, orderType);
		}
	}

	//------------------------------------------------------------------------

	/**
	 * Re-applies a PENDING entry's SL and PT one bar after the fill on an engine that arms them there,
	 * overwriting whatever the trailing stop did on that bar.
	 *
	 * <p>Such a platform submits a pending entry without levels and sets them from an arming step that
	 * runs BELOW the trail, so on the first bar the trade is open the trail moves the stop and the
	 * arming then puts it back on the entry-anchored level - the trail's move is overwritten within
	 * that same bar. Without this the runtime keeps the trailed level and exits early, on a price the
	 * exported strategy never trades at.</p>
	 *
	 * <p>Registered last, so it runs after the trailing stop's own listener - the same order the
	 * exported code has. Market entries are untouched: their levels are set before the entry.</p>
	 *
	 * @param order the freshly placed order
	 * @param orderType the order type it was placed with
	 */
	protected void armPendingExitsAfterFill(ILiveOrder order, byte orderType) throws TradingException {
		// Pending ORIGIN, not pending order type: the arming covers both names a pending entry rule can
		// produce - the pending itself and the market fallback it turns into when the level is through
		// the close. A fallback entry is armed back to the entry-anchored level after the first trail
		// move, exactly like the pending one.
		//
		// This term is NOT an engine question - a pending order type occurs on every engine - so the
		// engine's answer has to stand beside it, not replace it.
		boolean pendingOrigin = !OrderTypes.isMarketOrder(orderType) || ntPendingFallback;

		if(!Strategy.getArmsPendingExitsAfterFill() || !pendingOrigin) {
			return;
		}

		order.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
			@Override
			public void OnActionEvent(StrategyBase strategy) throws TradingException {
				// getBarsInTrade() == 0 is the first bar open after the fill - the same evaluation
				// the trailing stop makes its first move on, which is exactly when the platform's
				// arming step overwrites it.
				if(order.isClosedOrder() || !order.isMarketOrder() || order.getBarsInTrade() != 0) {
					return;
				}

				ExitMethod slExit = getStopLossExit();
				if(slExit != null) {
					slExit.setForOrder(order, Strategy);
				}

				ExitMethod ptExit = getProfitTargetExit();
				if(ptExit != null) {
					ptExit.setForOrder(order, Strategy);
				}
			}
		});
	}

	//------------------------------------------------------------------------

	protected void handleBarsValid(final ILiveOrder order, int barsValid) throws TradingException {
		if(order.isClosedOrder() || order.isMarketOrder()) return;

		if(Strategy.getEngine() == Engines.NinjaTrader) {
			// The export submits every pending entry with isLiveUntilCancelled = false, which is
			// what NinjaTrader's managed approach cancels one bar later unless the rule re-places
			// it. StrategyQuant's own expiry cannot express that - it is keyed on getBarsInTrade(),
			// which only advances once an order is FILLED, so a live pending's count stays 0 and
			// checkBarsValid never fires for any BarsValid value. Without this listener the pending
			// would live on and fill on bars where NinjaTrader has already cancelled it.
			// #BarsValid# is deliberately not consulted here - NinjaTrader's own lifetime overrides
			// it, and the export says so.
			final int[] barsSeen = new int[1];

			order.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
				@Override
				public void OnActionEvent(StrategyBase strategy) throws TradingException {
					if(order.isClosedOrder() || !order.isPendingOrder()) return;

					// the first BarOpen is the bar the order is fillable on, the second is the one
					// NinjaTrader cancels it at - and BarCloseSimulator drains closes at the START
					// of a BarOpen, before that bar's ticks can fill anything
					barsSeen[0]++;
					if(barsSeen[0] >= 2) {
						order.Close(OrderCloseTypes.Expired);
					}
				}
			});

			return;
		}

		// order is placed, now handle order validity
		if(barsValid != 0) {
			order.registerEvent(UpdateEventTypes.BarOpen, new IActionEventListener() {
				@Override
				public void OnActionEvent(StrategyBase strategy) throws TradingException {
					checkBarsValid(order, barsValid);
				}
			});
		}
	}
	

	//------------------------------------------------------------------------

	protected void checkBarsValid(ILiveOrder order, int barsValid) throws TradingException {
		if(order.isClosedOrder()) return;
		
		if(order.isPendingOrder() && order.getBarsInTrade() >= barsValid) {
			order.Close(OrderCloseTypes.Expired);
		}
	}
	
	//------------------------------------------------------------------------

	protected double computeSL(byte orderType, double orderPrice) throws TradingException {
		ExitMethod slExit = getStopLossExit();

		// Tell the Stop Loss whether this strategy also trails, BEFORE the order exists: the answer
		// decides whether its fill-anchored level survives the fill (see StopLoss.setForOrder), and
		// that runs while the order is being created. The other wiring between these two methods
		// happens after the order is open, which would be a trade too late.
		// A TrailingStop is present in ExitMethods whether or not the strategy uses one, so the
		// instance says nothing - a disabled trail carries the None formula, so the FORMULA is what
		// has to be keyed on.
		// The answer is ASSIGNED, not raised: it belongs to the block configuration this entry is being
		// placed with, and a flag that is only ever set to true keeps the first entry's answer for every
		// later one.
		if(slExit instanceof StopLoss && ExitMethods != null) {
			boolean trails = false;

			for(ExitMethod exitMethod : ExitMethods) {
				if(exitMethod instanceof SQ.ExitMethods.TrailingStop) {
					IFormula trailFormula = ((SQ.ExitMethods.TrailingStop) exitMethod).TrailingStop;

					if(trailFormula != null && !(trailFormula instanceof SQ.Formulas.RangeLevel.None)) {
						trails = true;
					}
				}
			}

			((StopLoss) slExit).strategyTrailsThisStop = trails;
		}

		if(slExit == null || orderPrice == 0) {
			// no SL
			return Order.NOT_DEFINED;
		}
		
		return SQUtils.fixPrice(Strategy.getInstrumentInfo().tickStep, slExit.computeValue(orderType, Strategy, Symbol, orderPrice));
	}
	

	//------------------------------------------------------------------------

	protected double computePT(byte orderType, double orderPrice) throws TradingException {
		ExitMethod ptExit = getProfitTargetExit();
		
		if(ptExit == null) {
			// no PT
			return Order.NOT_DEFINED;
		}

		double tickStep = Strategy.getInstrumentInfo().tickStep;
		return SQUtils.fixPrice(tickStep, ptExit.computeValue(orderType, Strategy, Symbol, orderPrice));
	}
	
	//------------------------------------------------------------------------

	public ExitMethod getStopLossExit() {
		ExitMethod slExit = null;
		
		for(ExitMethod exitMethod : ExitMethods) {
			if(exitMethod.getExitType() == ExitTypes.StopLoss) {
				slExit = exitMethod;
				break;
			}
		}
		
		return slExit;
	}
	
	//------------------------------------------------------------------------

	public ExitMethod getProfitTargetExit() {
		ExitMethod ptExit = null;
		
		for(ExitMethod exitMethod : ExitMethods) {
			if(exitMethod.getExitType() == ExitTypes.ProfitTarget) {
				ptExit = exitMethod;
				break;
			}
		}
		
		return ptExit;
	}
	
	//------------------------------------------------------------------------

	public ExitMethod getExitAfterBarsExit() {
		ExitMethod exit = null;
		
		for(ExitMethod exitMethod : ExitMethods) {
			if(exitMethod.getExitType() == ExitTypes.ExitAfterBars) {
				exit = exitMethod;
				break;
			}
		}
		
		return exit;
	}
	
	//------------------------------------------------------------------------

	public double computeSize(byte orderType, double price, double sl) throws TradingException {
		MMFormulaBlock sizeFormula = (MMFormulaBlock) Size;
		
		return sizeFormula.computeSize(Strategy, Symbol, orderType, price, sl);
	}

	//------------------------------------------------------------------------

	protected ILiveOrder checkLiveOrderExists(int direction, boolean includeClosingOrders) {
		int count = Strategy.Trader.getOpenOrdersCount(includeClosingOrders) - 1;

		// NinjaScript's Managed approach gives a strategy ONE position and knows neither magic numbers
		// nor per-order comments, so a position there is the strategy's and not a block's. Every entry
		// block the export emits is gated on Position.MarketPosition for that reason - on the position,
		// never on which entry opened it, whether the gate is the normal "== Flat" or the reversing
		// "!= Long". Keeping the magic number here would look past a position another entry block
		// holds, and the backtest would place an entry the exported strategy cannot.
		int magicNumber = MagicNumber;
		String comment = Comment;

		if(Strategy.getEngine() == Engines.NinjaTrader) {
			magicNumber = 0;
			comment = "";
		}

		for(int i=count; i >= 0; i--) {
			ILiveOrder order = Strategy.Trader.getOpenOrder(i, includeClosingOrders);

			if(OrderFunctions.identify(order, Strategy, Symbol, direction, magicNumber, comment) && order.isMarketOrder()) {
				return order;
			}
		}

		return null;
	}
	
	//------------------------------------------------------------------------

	/** 
	 * this method is called only in Tradestation engine, to handle exits (SL, PT, etc.) as same as they are handled in TS.
	 * @throws TradingException 
	 */
	public void OnApplyExits() throws TradingException {
		ArrayList<ILiveOrder> orders = getOpenOrders(Direction);
		ATM atm = Strategy.getATM();
		
		boolean slPlaced = false;
		if(orders != null) {
			for(int i=0; i<orders.size(); i++) {
				ILiveOrder order = orders.get(i);
				boolean atmUsed = atm != null && atm.isApplicable(Strategy, order.getSize(), order.getSL(), order.getOrderType());
				
				for(ExitMethod exitMethod : ExitMethods) {
					if(!atmUsed || exitMethod instanceof StopLoss) {
						if(exitMethod.setExit(order, Strategy)) {
							slPlaced = true;
						}
					}
				}
				
				if(!slPlaced && order.getSL() != Order.NOT_DEFINED) {
					// we have to set SL from order - handling if there is no SL, only for Trailing stop or Move2BE
					int direction = order.isLong() ? -1 : 1;

					// this is the path an action-set stop takes - Move SL/PT, Move to break even and
					// the trailing stop all only write order.setSL(), and with no StopLoss exit method on the
					// strategy the level becomes a real order right here. The NinjaTrader rule that governs it
					// is NOT applied at this point: the order created here is live for the whole of the next
					// bar, while the export submits the level at that bar's CLOSE and has it dropped or
					// accepted there. Comparing against the close available here would be a bar too early.
					// The rule lives in
					// BarCloseSimulator.dropActionStopsRejectedAtSubmission(), which decides this order at the
					// open of the bar it is live on and is gated to the NinjaTrader engine.
					byte orderType = (direction > 0 ? OrderTypes.BuyToCoverStop : OrderTypes.SellToCoverStop);

					ILiveOrder slOrder = Strategy.Trader.Open(orderType, order.getSymbol(), order.getSL())
							.setComment("SL")
							.setMagicNumber(order.getMagicNumber())
							.setEntryOrderId(order.getOrderId())
							.Send();
				}
			}
		}
	}

	//------------------------------------------------------------------------

	private ArrayList<ILiveOrder> getOpenOrders(int direction) {
		ArrayList<ILiveOrder> orders = null;
		
		for(int i=0; i<Strategy.Trader.getOpenOrdersCount(false); i++) {
			ILiveOrder order = Strategy.Trader.getOpenOrder(i, false);
			
			if(order.isPendingOrder()) {
				continue;
			}
			
			if(OrderFunctions.identify(order, Strategy, Symbol, direction, MagicNumber, Comment) && order.isMarketOrder()) {
				if(orders == null) {
					orders = new ArrayList<ILiveOrder>();
				}
				
				orders.add(order);
			}
		}
		
		return orders;
	}

	//------------------------------------------------------------------------

	protected boolean engineSupportsDuplicateTrades() {
		return Strategy.Trader.supportsDuplicateTrades();
	}

	//------------------------------------------------------------------------

	private ATMExit tryCloneATMExit(ATMExit exit) throws TradingException {
		ATMExit clone = exit.clone();
		if(clone == null) {
			throw new TradingException("Unable to create ATMExit object");
		}
		
		return clone;
	}

	//------------------------------------------------------------------------

	protected boolean checkOpenPriceWithinRange(double openPrice) {
		try {
			SettingsMap settings = Strategy.getSettings();
			if(settings.containsKey(MaxDistanceFromMarketHash) && settings.containsKey(MaxDistanceFromMarketPctHash) && ((boolean) settings.get(MaxDistanceFromMarketHash))) {
				double maxPctDistance = SQUtils.round2((double) settings.get(MaxDistanceFromMarketPctHash));
				double currentPrice;

				// The distance is measured from the decision price (StrategyBase.decisionAsk / decisionBid).
				currentPrice = Direction > 0 ? Strategy.decisionAsk(Symbol, 0) : Strategy.decisionBid(Symbol, 0);
				
				double distancePct = SQUtils.round2(Math.abs(currentPrice - openPrice) / currentPrice * 100);
				if(distancePct > maxPctDistance) {
					Log.debug("Order skipped - too far from market. Open price: {}, Market price: {}, Max distance: {}%", openPrice, currentPrice, maxPctDistance);
					return false;
				}
			}
		}
		catch(Throwable t) {
			Log.error("Error while checking open price max distance", t);
		}
		
		return true;
	}
}
