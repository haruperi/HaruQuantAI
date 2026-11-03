/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.ticksimulator.DefaultTickSimulator
 *  com.strategyquant.datalib.ticksimulator.ITickSimulator
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.ticksimulator.DefaultTickSimulator;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import com.strategyquant.tradinglib.event.TradingEventObj;
import com.strategyquant.tradinglib.event.TradingEventsArray;
import com.strategyquant.tradinglib.execution.ReservedBarsType;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.parameters.MarketOpenSession;
import com.strategyquant.tradinglib.options.parameters.RealisticGapsHandling;
import com.strategyquant.tradinglib.simulator.impl.AbstractTradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.MarketPriceHolder;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.swap.SwapCalculator;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class MetaTraderSimulatorNetting
extends AbstractTradingSimulator {
    public static final Logger Log = LoggerFactory.getLogger((String)"MetaTraderSimulator");
    public static final Logger BacktestLog = LoggerFactory.getLogger((String)"BacktestLog");
    protected MarketPriceHolder marketPriceHolder = new MarketPriceHolder();
    protected Int2ObjectOpenHashMap<LiveOrderObj> openPositions;
    protected OrdersList closedTrades;
    protected Long2FloatRBTreeMap dailyEquityValues;
    private long lastDayStartTime = -1L;
    private long nextDayStartTime = -1L;
    private float worstDailyEquity;
    private int orderId = -1000;
    private String connectionName = null;
    private int connectionHash;
    private int lastSymbolHash;
    private ChartData chartData = null;
    private TradingEventsArray tradingEventsArray = new TradingEventsArray();
    private double chartDataMinDistance;
    private int chartDataDecimals;
    private float accountBalance;
    private double accountEquity;
    private float initialCapital;
    private double slippage;
    private CommissionsMethod commission;
    private SwapMethod swap;
    private boolean computeDailyStats = true;
    protected String marketOpenSessionString;
    protected Session marketOpenSession = null;

    public MetaTraderSimulatorNetting() {
        super(new ReservedBarsType(1, 100, 1001), (ITickSimulator)new DefaultTickSimulator());
    }

    @Override
    public void initSettings(SettingsMap settingsMap) throws TradingException {
        if (!settingsMap.containsKey("MoneyManagement.InitialCapital") || !(settingsMap.get("MoneyManagement.InitialCapital") instanceof Double)) {
            throw new TradingException("Setting 'TradingSetup.InitialCapital' is not set or has incorrect value! It must be double!");
        }
        this.accountBalance = this.initialCapital = (float)settingsMap.getDouble("MoneyManagement.InitialCapital");
        this.accountEquity = this.accountBalance;
        this.slippage = 0.0;
        if (settingsMap.containsKey("Slippage") && settingsMap.get("Slippage") instanceof Double || settingsMap.get("Slippage") instanceof Integer) {
            this.slippage = settingsMap.getDouble("Slippage");
        }
        if (settingsMap.containsKey("Commission") && settingsMap.get("Commission") instanceof CommissionsMethod) {
            this.commission = (CommissionsMethod)settingsMap.get("Commission");
        }
        if (settingsMap.containsKey("Swap") && settingsMap.get("Swap") instanceof SwapMethod) {
            this.swap = (SwapMethod)settingsMap.get("Swap");
        }
        boolean bl = this.storePendingOrders = !Boolean.parseBoolean(MainApp.settings().get("dontStorePendingOrders", "true"));
        if (settingsMap.containsKey("TradingOptions") && settingsMap.get("TradingOptions") instanceof TradingOptions) {
            TradingOptions tradingOptions = (TradingOptions)settingsMap.get("TradingOptions");
            for (int i = 0; i < tradingOptions.size(); ++i) {
                TradingOption tradingOption = (TradingOption)tradingOptions.get(i);
                if (tradingOption instanceof RealisticGapsHandling) {
                    this.realisticGapsHandling = ((RealisticGapsHandling)tradingOption).RealisticGapsHandling;
                }
                if (!(tradingOption instanceof MarketOpenSession)) continue;
                this.marketOpenSessionString = ((MarketOpenSession)tradingOption).MarketOpenSession;
                Session session = SessionManager.getSession((String)this.marketOpenSessionString);
                if (session == null) continue;
                this.marketOpenSession = session.clone();
            }
        }
    }

    @Override
    public void initialize(MarketData marketData) {
        this.liveOrders = new LiveOrderObj[100];
        this.openPositions = new Int2ObjectOpenHashMap();
        this.dailyEquityValues = new Long2FloatRBTreeMap();
        this.liveOrdersCount = 0;
        this.closedTrades = new OrdersList("ClosedTrades");
        this.orderId = 1;
        this.tickData = new TickEvent();
        for (int i = 0; i < marketData.getChartsCount(); ++i) {
            if (this.connectionHash != marketData.Chart(i).getConnectionHash()) continue;
            marketData.Chart(i).getMinDistance();
            this.marketPriceHolder.registerNewSymbol(marketData.Chart(i));
        }
        this.tradingSymbolHash = marketData.Chart((int)0).Symbol.hashCode();
        this.mainChartData = marketData.Chart(0);
    }

    @Override
    public void destroy() {
        if (this.closedTrades != null) {
            this.closedTrades.clear();
        }
    }

    @Override
    public void setConnection(String string) {
        this.connectionName = string;
        this.connectionHash = string.hashCode();
    }

    @Override
    public void eventNewTick(TickEvent tickEvent, double d, double d2) {
        if (tickEvent.getConnectionHash() != this.connectionHash) {
            return;
        }
        this.lastSymbolHash = tickEvent.getSymbolHash();
        TickEvent tickEvent2 = this.marketPriceHolder.setNewTick(this.lastSymbolHash, tickEvent);
        if (tickEvent2 != null) {
            this.tickData = tickEvent2;
            if (this.getTestPrecision() != 5) {
                this.processNewTick(d, d2);
            }
        }
    }

    private void processNewTick(double d, double d2) {
        if (this.computeDailyStats) {
            this.tryUpdateDailyEquity();
        }
        TickEvent tickEvent = this.marketPriceHolder.getCurrentTick(this.lastSymbolHash);
        if (this.IsMarketOpen()) {
            this.checkSLPT(tickEvent, this.lastSymbolHash, d, d2);
            if (this.liveOrdersCount > 0) {
                this.accountEquity = -1.0;
                if (this.computeDailyStats) {
                    this.updateMAE_MFE();
                }
                this.checkStopLimitOrders(tickEvent, this.lastSymbolHash);
            }
        }
    }

    private void tryUpdateDailyEquity() {
        long l = this.tickData.getTime();
        if (this.lastDayStartTime == -1L) {
            this.updateDayStartTimes(l);
        } else if (l >= this.nextDayStartTime) {
            this.dailyEquityValues.addTo(this.lastDayStartTime, this.worstDailyEquity);
            this.updateDayStartTimes(l);
        } else {
            return;
        }
        this.worstDailyEquity = this.liveOrdersCount > 0 ? Float.MAX_VALUE : this.accountBalance - this.initialCapital;
    }

    private void updateDayStartTimes(long l) {
        this.lastDayStartTime = SQTime.getDateInMs((long)l);
        this.nextDayStartTime = this.lastDayStartTime + 86400000L;
    }

    private void updateMAE_MFE() {
        float f = this.accountBalance;
        IntIterator intIterator = this.openPositions.keySet().iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            if (n != this.lastSymbolHash) continue;
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.openPositions.get(n);
            double d = liveOrderObj.isLong() ? this.tickData.getBid() - liveOrderObj.getOpenPrice() : liveOrderObj.getOpenPrice() - this.tickData.getBid();
            if ((double)liveOrderObj.getMFE() < d) {
                liveOrderObj.setMFE((float)d);
            }
            d *= -1.0;
            if ((double)liveOrderObj.getMAE() < d) {
                liveOrderObj.setMAE((float)d);
            }
            liveOrderObj.setTickData(this.tickData.getAsk(), this.tickData.getBid());
            f = (float)((double)f + liveOrderObj.getPL());
        }
        this.accountEquity = f;
        this.worstDailyEquity = Math.min(f - this.initialCapital, this.worstDailyEquity);
    }

    private void checkSLPT(TickEvent tickEvent, int n, double d, double d2) {
        LiveOrderObj liveOrderObj = (LiveOrderObj)this.openPositions.get(n);
        if (liveOrderObj != null) {
            byte by;
            double d3;
            liveOrderObj.setTickData(this.tickData.getAsk(), this.tickData.getBid());
            double d4 = liveOrderObj.getSL();
            double d5 = liveOrderObj.getPT();
            if (d4 == 0.0 && d5 == 0.0) {
                return;
            }
            if (d4 > d2 && d4 < d && d5 > d2 && d5 < d) {
                liveOrderObj.setAmbiguous();
                ++this.ambiguousTrades;
            }
            if (d4 > 0.0 && (d3 = this.priceLevelReached(tickEvent, n, by = liveOrderObj.getOrderTypeFromSLPT(-1), d4)) > 0.0) {
                this.closePosition(liveOrderObj, this.getRealisticSLPTFilledPrice(d3, d4, tickEvent, by), (byte)2);
                return;
            }
            if (d5 > 0.0 && (d3 = this.priceLevelReached(tickEvent, n, by = liveOrderObj.getOrderTypeFromSLPT(1), d5)) > 0.0) {
                this.closePosition(liveOrderObj, this.getRealisticSLPTFilledPrice(d3, d5, tickEvent, by), (byte)3);
            }
        }
    }

    private void closePosition(LiveOrderObj liveOrderObj, double d, byte by) {
        this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
        if (!liveOrderObj.isPendingOrder()) {
            liveOrderObj.setOrderId(this.orderId++);
        }
        liveOrderObj.setCloseTime(this.tickData.getTime());
        liveOrderObj.setClosePrice(liveOrderObj.getClosePriceWithSlippage(this.slippage, d, by));
        liveOrderObj.setLastAction((byte)2);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setOrderStatus((byte)3);
        liveOrderObj.setCloseType(by);
        liveOrderObj.setCommSwap(this.getCommissionSwap(liveOrderObj));
        this.fixMAEMFEByRealPrice(liveOrderObj);
        this.saveOrder(liveOrderObj, false);
        this.removeOpenTrade(liveOrderObj);
        if (!liveOrderObj.isPendingOrder()) {
            this.openPositions.remove(liveOrderObj.getSymbolHash());
            this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
        }
    }

    protected void checkStopLimitOrders(TickEvent tickEvent, int n) {
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.isMarketOrder()) continue;
            byte by = liveOrderObj.getOrderType();
            double d = this.priceLevelReached(tickEvent, n, liveOrderObj.getOrderType(), liveOrderObj.getOpenPrice());
            if (!(d > 0.0)) continue;
            liveOrderObj.fillOrder(this.tickData);
            if (this.thereWasAGap(by, tickEvent)) {
                Log.debug("GAP detected - prev Close:{}, new Open: {}, realistic fill for MT4 set", (Object)this.closingPrice, (Object)tickEvent.getBid());
                liveOrderObj.setOpenPrice(MetaTraderSimulatorNetting.getPriceByType(by, this.tickData.getBid(), this.tickData.getAsk()));
            }
            liveOrderObj.setLastAction((byte)1);
            liveOrderObj.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj));
            this.onOrderFill(liveOrderObj);
            --i;
        }
        if (tickEvent.isBarClose()) {
            this.isNewBar = true;
            this.closingPrice = tickEvent.getBid();
        } else if (this.isNewBar) {
            this.isNewBar = false;
        }
    }

    @Override
    public void eventBarUpdated(int n) {
        if (n == 2) {
            this.increaseBarsInTrade();
        }
    }

    private void increaseBarsInTrade() {
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            if (this.tickData.getTime() == this.liveOrders[i].getOpenTime()) continue;
            this.liveOrders[i].increaseBarsInTrade();
        }
    }

    @Override
    public ILiveOrder orderOpen(StrategyBase strategyBase, ILiveOrder iLiveOrder, int n, ITradingEventListener iTradingEventListener) throws TradingException {
        int n2;
        LiveOrderObj liveOrderObj = (LiveOrderObj)iLiveOrder;
        this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
        if (!this.checkOrder(liveOrderObj)) {
            this.reuseTemporaryOrder(liveOrderObj);
            return liveOrderObj;
        }
        byte by = liveOrderObj.getOrderType();
        liveOrderObj.setOrderId(this.orderId++);
        liveOrderObj.setOpenTime(this.tickData.getTime());
        liveOrderObj.setOriginalOpenTime(liveOrderObj.getOpenTime());
        liveOrderObj.setATROnOpen(this.getATR(strategyBase, liveOrderObj.getSymbol()));
        if (OrderTypes.isMarketOrder(by)) {
            liveOrderObj.setOpenPrice(liveOrderObj.getPriceByType(by, this.tickData.getBid(), this.tickData.getAsk(), this.slippage));
            liveOrderObj.setOriginalOpenPrice(liveOrderObj.getOpenPrice());
            liveOrderObj.setOrderStatus((byte)1);
            liveOrderObj.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj));
            n2 = 1;
        } else {
            liveOrderObj.setOrderStatus((byte)2);
            liveOrderObj.setLastOpenPrice(liveOrderObj.getOpenPrice());
            n2 = 2;
        }
        liveOrderObj.setLastAction((byte)1);
        liveOrderObj.setError(0, null);
        liveOrderObj.setWorkingStatus((byte)-30);
        this.addOpenTrade(liveOrderObj);
        this.sendEvent(strategyBase, iTradingEventListener, n2, iLiveOrder);
        return iLiveOrder;
    }

    @Override
    public ILiveOrder orderModify(StrategyBase strategyBase, ILiveOrder iLiveOrder, int n, ITradingEventListener iTradingEventListener) {
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj != iLiveOrder) continue;
            if (!this.checkOrderSLPT(liveOrderObj)) {
                return liveOrderObj;
            }
            liveOrderObj.setSLFromModified();
            liveOrderObj.setPTFromModified();
            return liveOrderObj;
        }
        return iLiveOrder;
    }

    @Override
    public ILiveOrder orderClose(StrategyBase strategyBase, ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) {
        LiveOrderObj liveOrderObj = (LiveOrderObj)iLiveOrder;
        double d = 0.0;
        this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
        d = OrderTypes.isMarketOrder(liveOrderObj.getOrderType()) ? liveOrderObj.getPriceByType(OrderTypes.getOppositeType(liveOrderObj.getOrderType()), this.tickData.getBid(), this.tickData.getAsk(), this.slippage) : liveOrderObj.getOpenPrice();
        liveOrderObj.setClosePrice(d);
        liveOrderObj.setCloseTime(this.tickData.getTime());
        liveOrderObj.setLastAction((byte)2);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setOrderStatus((byte)3);
        liveOrderObj.setCloseType(by);
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj2 = this.liveOrders[i];
            if (liveOrderObj2 != liveOrderObj) continue;
            this.closePosition(liveOrderObj, d, by);
            this.removeOpenTrade(liveOrderObj);
            return liveOrderObj;
        }
        return null;
    }

    protected void addOpenTrade(LiveOrderObj liveOrderObj) throws TradingException {
        if (this.liveOrdersCount >= this.liveOrders.length - 1) {
            throw new BadStrategyException(32);
        }
        this.liveOrders[this.liveOrdersCount++] = liveOrderObj;
        if (liveOrderObj.isMarketOrder()) {
            this.onOrderFill(liveOrderObj);
        }
    }

    private void onOrderFill(LiveOrderObj liveOrderObj) {
        liveOrderObj.setNettingMode(true);
        LiveOrderObj liveOrderObj2 = (LiveOrderObj)this.openPositions.get(liveOrderObj.getSymbolHash());
        if (liveOrderObj2 == null) {
            liveOrderObj.setLastOpenPrice(liveOrderObj.getOpenPrice());
            this.saveOrder(liveOrderObj, true);
            this.openPositions.put(liveOrderObj.getSymbolHash(), (Object)liveOrderObj);
        } else if (liveOrderObj.getDirection() == liveOrderObj2.getDirection()) {
            this.saveOrder(liveOrderObj, true);
            liveOrderObj.setLastOpenPrice(liveOrderObj.getOpenPrice());
            liveOrderObj.setOpenPrice((liveOrderObj2.getOpenPrice() * liveOrderObj2.getSize() + liveOrderObj.getOpenPrice() * liveOrderObj.getSize()) / (liveOrderObj2.getSize() + liveOrderObj.getSize()));
            liveOrderObj.setSize(SQUtils.round((double)(liveOrderObj2.getSize() + liveOrderObj.getSize()), (int)5));
            liveOrderObj.setCommSwap(liveOrderObj.getCommSwap() + liveOrderObj2.getCommSwap());
            for (int i = 0; i < liveOrderObj2.getBarsInTrade(); ++i) {
                liveOrderObj.increaseBarsInTrade();
            }
            this.openPositions.put(liveOrderObj.getSymbolHash(), (Object)liveOrderObj);
            this.removeOpenTrade(liveOrderObj2);
        } else {
            double d = liveOrderObj.getSize();
            double d2 = liveOrderObj2.getSize();
            double d3 = liveOrderObj.getOpenPrice();
            LiveOrderObj liveOrderObj3 = this.createLiveOrder(liveOrderObj.getTrader(), liveOrderObj.getInstrumentInfo(), liveOrderObj2.getOrderType(), liveOrderObj.getSymbol());
            liveOrderObj3.setSize(Math.min(d2, d));
            liveOrderObj3.setOriginalOpenPrice(liveOrderObj2.getOriginalOpenPrice());
            liveOrderObj3.setOpenPrice(liveOrderObj2.getOpenPrice());
            liveOrderObj3.setClosePrice(d3);
            liveOrderObj3.setTickData(this.tickData.getAsk(), this.tickData.getBid());
            liveOrderObj3.setOriginalOpenTime(liveOrderObj2.getOriginalOpenTime());
            liveOrderObj3.setOriginalOrderType(liveOrderObj2.getOriginalOrderType());
            liveOrderObj3.setOpenTime(liveOrderObj2.getOpenTime());
            liveOrderObj3.setCloseTime(liveOrderObj.getOpenTime());
            liveOrderObj3.setOrderType(liveOrderObj2.getOrderType());
            liveOrderObj3.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj));
            liveOrderObj3.setCommSwap(this.getCommissionSwap(liveOrderObj));
            liveOrderObj3.setOrderStatus((byte)3);
            this.accountBalance = (float)((double)this.accountBalance + liveOrderObj3.getPL());
            liveOrderObj3.setExitIndex(liveOrderObj.getExitIndex());
            liveOrderObj3.setATROnOpen(liveOrderObj2.getATROnOpen());
            byte by = liveOrderObj.getSLType();
            if (by != -1 && (by == 20 || by == 21)) {
                liveOrderObj3.setCloseType(by);
            } else {
                liveOrderObj3.setCloseType((byte)1);
            }
            liveOrderObj3.setComment(liveOrderObj.getComment());
            if (d > d2) {
                liveOrderObj.setWorkingStatus((byte)-10);
                liveOrderObj.setSize(SQUtils.round((double)(d - d2), (int)5));
                liveOrderObj.setWorkingStatus((byte)-30);
                this.openPositions.put(liveOrderObj.getSymbolHash(), (Object)liveOrderObj);
                this.removeOpenTrade(liveOrderObj2);
            } else if (d == d2) {
                this.openPositions.remove(liveOrderObj.getSymbolHash());
                liveOrderObj.setCloseType((byte)1);
                liveOrderObj.setCloseTime(this.tickData.getTime());
                this.removeOpenTrade(liveOrderObj2);
                this.removeOpenTrade(liveOrderObj);
            } else {
                liveOrderObj2.setWorkingStatus((byte)-10);
                liveOrderObj2.setSize(SQUtils.round((double)(d2 - d), (int)5));
                liveOrderObj2.setWorkingStatus((byte)-30);
                liveOrderObj2.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj2));
                liveOrderObj.setCloseType((byte)1);
                liveOrderObj.setCloseTime(this.tickData.getTime());
                liveOrderObj.setOrderType(liveOrderObj.isLong() ? (byte)1 : 2);
                this.removeOpenTrade(liveOrderObj);
            }
            this.saveOrder(liveOrderObj3, false);
            this.removeOpenTrade(liveOrderObj3);
        }
        try {
            liveOrderObj.evaluateActionListeners(7, null);
        }
        catch (TradingException tradingException) {
            Log.error("Error while calling Order filled action listeners", (Throwable)tradingException);
        }
    }

    private void saveOrder(LiveOrderObj liveOrderObj, boolean bl) {
        if (bl) {
            LiveOrderObj liveOrderObj2 = this.createLiveOrder(liveOrderObj.getTrader(), liveOrderObj.getInstrumentInfo(), liveOrderObj.getOrderType(), liveOrderObj.getSymbol());
            liveOrderObj2.setOrderId(liveOrderObj.getOrderId());
            liveOrderObj2.setMagicNumber(liveOrderObj.getMagicNumber());
            liveOrderObj2.setOriginalOpenTime(liveOrderObj.getOriginalOpenTime());
            liveOrderObj2.setOpenTime(liveOrderObj.getOpenTime());
            liveOrderObj2.setOriginalOpenPrice(liveOrderObj.getOriginalOpenPrice());
            liveOrderObj2.setOpenPrice(liveOrderObj.getOpenPrice());
            liveOrderObj2.setSize(liveOrderObj.getSize());
            liveOrderObj2.setCloseTime(this.tickData.getTime());
            liveOrderObj2.setClosePrice(liveOrderObj.getOpenPrice());
            liveOrderObj2.setLastAction((byte)2);
            liveOrderObj2.setWorkingStatus((byte)-30);
            liveOrderObj2.setOrderStatus((byte)3);
            liveOrderObj2.setCloseType((byte)18);
            liveOrderObj2.setATROnOpen(liveOrderObj.getATROnOpen());
            this.fixMAEMFEByRealPrice(liveOrderObj2);
            this.closedTrades.add(liveOrderObj2);
            this.removeOpenTrade(liveOrderObj2);
        } else if (this.storePendingOrders || !liveOrderObj.isPendingOrder()) {
            liveOrderObj.transformMAE_MFE();
            this.fixMAEMFEByRealPrice(liveOrderObj);
            this.closedTrades.add(liveOrderObj);
        }
    }

    private boolean checkOrder(LiveOrderObj liveOrderObj) {
        double d;
        double d2;
        int n = liveOrderObj.getSymbolHash();
        if (!this.marketPriceHolder.containsSymbol(n)) {
            String string = "Symbol '" + liveOrderObj.getSymbol() + "' is not supported in this Trade Controller";
            liveOrderObj.setError(1, string);
            return false;
        }
        byte by = liveOrderObj.getOrderType();
        double d3 = d2 = LiveOrderObj.getPriceByType(by, this.tickData.getBid(), this.tickData.getAsk());
        if (liveOrderObj.isPendingOrder()) {
            d = liveOrderObj.getOpenPrice();
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                liveOrderObj.setError(6, "Incorrect price level. Open price: " + d3 + ", price level: " + d);
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d)) {
                liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                return false;
            }
            d3 = d;
        }
        if (liveOrderObj.getSL() != -9.9999999E7) {
            d = liveOrderObj.getSL();
            by = liveOrderObj.getOrderTypeFromSLPT(-1);
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                liveOrderObj.setError(6, "Incorrect stop level. Open price: " + d3 + ", price level: " + d);
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d)) {
                liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                liveOrderObj.setSL(0.0);
                liveOrderObj.setSLFromModified();
            }
        }
        if (liveOrderObj.getPT() != -9.9999999E7) {
            d = liveOrderObj.getPT();
            by = liveOrderObj.getOrderTypeFromSLPT(1);
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                liveOrderObj.setError(6, "Incorrect stop level. Open price: " + d3 + ", price level: " + d);
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d)) {
                liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                return false;
            }
        }
        return true;
    }

    private String generatePriceLevelCorrectnessMsg(String string, int n) {
        switch (n) {
            case 5: {
                return String.format("Incorrect %s for Buy Stop order. Price must be above market price.", string);
            }
            case 6: {
                return String.format("Incorrect %s for Sell Stop order. Price must be below market price.", string);
            }
            case 3: {
                return String.format("Incorrect %s for Buy Limit order. Price must be below market price.", string);
            }
            case 4: {
                return String.format("Incorrect %s for Sell Limit order. Price must be above market price.", string);
            }
        }
        return String.format("Unknown orderType: %d", n);
    }

    protected abstract boolean checkPriceLevelCorrectness(int var1, double var2, double var4);

    private boolean checkPriceLevelDistance(int n, double d, double d2) {
        double d3;
        if (this.chartData == null || this.chartData.getSymbolHash() != n) {
            this.chartData = this.marketPriceHolder.getChartData(n);
            this.chartDataMinDistance = this.chartData.getMinDistance() * this.chartData.getInstrumentInfo().tickSize;
            this.chartDataDecimals = this.chartData.getInstrumentInfo().decimals;
        }
        return SQUtils.compare((double)(d3 = Math.abs(d2 - d)), (double)this.chartDataMinDistance, (int)this.chartDataDecimals) >= 0;
    }

    private void sendEvent(StrategyBase strategyBase, ITradingEventListener iTradingEventListener, int n, ILiveOrder iLiveOrder) {
        TradingEventObj tradingEventObj = this.tradingEventsArray.getAvailableEventObject();
        tradingEventObj.setEventType(n);
        tradingEventObj.setOrder(iLiveOrder);
        try {
            strategyBase.OnEvent(tradingEventObj);
        }
        catch (Exception exception) {
            Log.error("Exception during strategy.onEvent()", (Throwable)exception);
        }
        if (iTradingEventListener != null) {
            try {
                iTradingEventListener.OnTradingEvent(tradingEventObj);
            }
            catch (Exception exception) {
                Log.error("Exception during OrderEventListener.onTradingEvent()", (Throwable)exception);
            }
        }
        tradingEventObj.releaseEvent();
    }

    private double getCommissionSwap(LiveOrderObj liveOrderObj) {
        double d = liveOrderObj.getCommSwap();
        if (this.commission != null) {
            if (this.chartData == null || this.chartData.getSymbolHash() != liveOrderObj.getSymbolHash()) {
                this.chartData = this.marketPriceHolder.getChartData(liveOrderObj.getSymbolHash());
            }
            this.chartDataMinDistance = this.chartData.getMinDistance() * this.chartData.getInstrumentInfo().tickSize;
            this.chartDataDecimals = this.chartData.getInstrumentInfo().decimals;
            try {
                d -= this.commission.computeCommissionsOnClose(liveOrderObj, this.chartData.getInstrumentInfo().tickSize, this.chartData.getInstrumentInfo().pointValue);
            }
            catch (Exception exception) {
                Log.error("Exception computing commissions", (Throwable)exception);
            }
        }
        if (this.swap != null && this.swap.isUsed()) {
            try {
                d += SwapCalculator.calculate(liveOrderObj, this.swap);
            }
            catch (Exception exception) {
                Log.error("Exception computing swap", (Throwable)exception);
            }
        }
        return d;
    }

    protected double computeCommissionsOnOpen(LiveOrderObj liveOrderObj) {
        if (this.commission != null) {
            if (this.chartData == null || this.chartData.getSymbolHash() != liveOrderObj.getSymbolHash()) {
                this.chartData = this.marketPriceHolder.getChartData(liveOrderObj.getSymbolHash());
            }
            this.chartDataMinDistance = this.chartData.getMinDistance() * this.chartData.getInstrumentInfo().tickSize;
            this.chartDataDecimals = this.chartData.getInstrumentInfo().decimals;
            try {
                return -this.commission.computeCommissionsOnOpen(liveOrderObj, this.chartData.getInstrumentInfo().tickSize, this.chartData.getInstrumentInfo().pointValue);
            }
            catch (Exception exception) {
                Log.error("Exception computing commissions", (Throwable)exception);
            }
        }
        return 0.0;
    }

    @Override
    public OrdersList getHistoryOrders() {
        return this.closedTrades;
    }

    @Override
    public int getHistoryOrdersCount() {
        return this.closedTrades.size();
    }

    @Override
    public Order getHistoryOrder(int n) {
        if (n < 0 || n >= this.closedTrades.size()) {
            return null;
        }
        return this.closedTrades.get(n);
    }

    @Override
    public int getOpenOrdersCount(boolean bl) {
        return this.liveOrdersCount;
    }

    public ILiveOrder getOpenOrder(int n) {
        if (n < 0 || n >= this.getOpenOrdersCount(false)) {
            throw new IllegalArgumentException("Trade index is out of range!");
        }
        if (n < this.liveOrdersCount) {
            return this.liveOrders[n];
        }
        return null;
    }

    @Override
    public double getAccountBalance() {
        return this.accountBalance;
    }

    @Override
    public double getAccountEquity() {
        if (this.accountEquity == -1.0) {
            this.computeAccountEquity();
        }
        return this.accountEquity;
    }

    private void computeAccountEquity() {
        this.accountEquity = this.accountBalance;
        IntIterator intIterator = this.openPositions.keySet().iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.openPositions.get(n);
            this.accountEquity += liveOrderObj.getPL();
        }
    }

    @Override
    public double getInitialBalance() {
        return this.initialCapital;
    }

    @Override
    public double getTotalPL() {
        return 0.0;
    }

    @Override
    public String getMainCurrency() {
        return null;
    }

    private boolean checkOrderSLPT(LiveOrderObj liveOrderObj) {
        double d;
        byte by = liveOrderObj.getOrderType();
        double d2 = liveOrderObj.isPendingOrder() ? liveOrderObj.getOpenPrice() : LiveOrderObj.getClosePriceByType(by, this.tickData.getBid(), this.tickData.getAsk());
        int n = liveOrderObj.getSymbolHash();
        if (liveOrderObj.modifiedSL > 0.0) {
            d = liveOrderObj.modifiedSL;
            by = liveOrderObj.getOrderTypeFromSLPT(-1);
            if (!this.checkPriceLevelCorrectness(by, d2, d)) {
                liveOrderObj.setError(6, null);
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d2, d)) {
                liveOrderObj.setError(6, null);
                return false;
            }
        }
        if (liveOrderObj.modifiedPT > 0.0) {
            d = liveOrderObj.modifiedPT;
            by = liveOrderObj.getOrderTypeFromSLPT(1);
            if (!this.checkPriceLevelCorrectness(by, d2, d)) {
                liveOrderObj.setError(6, null);
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d2, d)) {
                liveOrderObj.setError(6, null);
                return false;
            }
        }
        return true;
    }

    @Override
    public void eventEndOfTest() {
        this.eventNoTrade();
        this.liveOrders = null;
    }

    @Override
    public void eventNoTrade() {
        float f = this.accountBalance;
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
            double d = LiveOrderObj.getPriceByType(OrderTypes.getOppositeType(liveOrderObj.getOrderType()), this.tickData.getBid(), this.tickData.getAsk());
            liveOrderObj.setCloseTime(this.tickData.getTime());
            liveOrderObj.setClosePrice(d);
            liveOrderObj.setLastAction((byte)2);
            liveOrderObj.setWorkingStatus((byte)-30);
            liveOrderObj.setOrderStatus((byte)3);
            liveOrderObj.setCloseType((byte)4);
            f = (float)((double)f + liveOrderObj.getPL());
            if (!liveOrderObj.isPendingOrder()) {
                liveOrderObj.setOrderId(this.orderId++);
            }
            this.fixMAEMFEByRealPrice(liveOrderObj);
            this.closedTrades.add(liveOrderObj);
            this.removeOpenTradeNoFix(i);
        }
        this.liveOrdersCount = 0;
        this.openPositions.clear();
        this.accountEquity = f;
    }

    @Override
    public TickEvent getTickData() {
        return this.tickData;
    }

    @Override
    public Long2FloatRBTreeMap getWorstDailyEquity() {
        return this.dailyEquityValues;
    }

    @Override
    public int getBarEventType() {
        return 2;
    }

    @Override
    public void evaluateActionListeners(int n, StrategyBase strategyBase) throws TradingException {
        IntIterator intIterator = this.openPositions.keySet().iterator();
        while (intIterator.hasNext()) {
            int n2 = (Integer)intIterator.next();
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.openPositions.get(n2);
            if (liveOrderObj == null) continue;
            liveOrderObj.evaluateActionListeners(n, strategyBase);
        }
        for (int i = this.liveOrdersCount - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj == null) continue;
            liveOrderObj.evaluateActionListeners(n, strategyBase);
        }
    }

    @Override
    public boolean supportsDuplicateTrades() {
        return true;
    }
}

