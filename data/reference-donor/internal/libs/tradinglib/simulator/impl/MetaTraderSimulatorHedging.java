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
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class MetaTraderSimulatorHedging
extends AbstractTradingSimulator {
    public static final Logger Log = LoggerFactory.getLogger((String)"MetaTraderSimulator");
    public static final Logger BacktestLog = LoggerFactory.getLogger((String)"BacktestLog");
    private static final long DAY_SECONDS = 86400000L;
    protected MarketPriceHolder marketPriceHolder = new MarketPriceHolder();
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
    private boolean orderErrorDetailedMessage = false;
    protected String marketOpenSessionString;
    protected Session marketOpenSession = null;

    public MetaTraderSimulatorHedging() {
        super(new ReservedBarsType(1, 100, 1001), (ITickSimulator)new DefaultTickSimulator());
    }

    @Override
    protected abstract double getSLPTFilledPrice(double var1, double var3);

    protected abstract boolean checkPriceLevelCorrectness(int var1, double var2, double var4);

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
        this.liveOrders = new LiveOrderObj[300];
        this.liveOrdersCount = 0;
        this.closedTrades = new OrdersList("ClosedTrades");
        this.dailyEquityValues = new Long2FloatRBTreeMap();
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
            this.closedTrades = null;
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
        if (this.lastSymbolHash != this.tradingSymbolHash) {
            return;
        }
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
        if (this.liveOrdersCount > 0) {
            this.accountEquity = -1.0;
            TickEvent tickEvent = this.marketPriceHolder.getCurrentTick(this.lastSymbolHash);
            if (this.IsMarketOpen()) {
                this.checkSLPT(tickEvent, this.lastSymbolHash, d, d2);
                this.checkStopLimitOrders(tickEvent, this.lastSymbolHash);
            }
            if (this.computeDailyStats) {
                this.updateMAE_MFE();
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
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj.isPendingOrder() || liveOrderObj.isClosedOrder()) continue;
            double d = liveOrderObj.isLong() ? this.tickData.getBid() - liveOrderObj.getOpenPrice() : liveOrderObj.getOpenPrice() - this.tickData.getAsk();
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

    protected void checkSLPT(TickEvent tickEvent, int n, double d, double d2) {
        boolean bl = false;
        int n2 = this.liveOrdersCount;
        for (int i = n2 - 1; i >= 0; --i) {
            byte by;
            double d3;
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.isPendingOrder()) continue;
            liveOrderObj.setTickData(this.tickData.getAsk(), this.tickData.getBid());
            double d4 = liveOrderObj.getSL();
            double d5 = liveOrderObj.getPT();
            if (d4 == 0.0 && d5 == 0.0) continue;
            if (d4 > d2 && d4 < d && d5 > d2 && d5 < d) {
                liveOrderObj.setAmbiguous();
                ++this.ambiguousTrades;
            }
            if (d4 > 0.0 && (d3 = this.priceLevelReached(tickEvent, n, by = liveOrderObj.getOrderTypeFromSLPT(-1), d4)) > 0.0) {
                this.closeOrder(liveOrderObj, this.getRealisticSLPTFilledPrice(d3, d4, tickEvent, by), (byte)2);
                this.removeOpenTradeNoFix(i);
                bl = true;
                continue;
            }
            if (!(d5 > 0.0) || !((d3 = this.priceLevelReached(tickEvent, n, by = liveOrderObj.getOrderTypeFromSLPT(1), d5)) > 0.0)) continue;
            this.closeOrder(liveOrderObj, this.getRealisticSLPTFilledPrice(d3, d5, tickEvent, by), (byte)3);
            this.removeOpenTradeNoFix(i);
            bl = true;
        }
        if (bl) {
            this.fixRemovedElements();
        }
    }

    protected void checkStopLimitOrders(TickEvent tickEvent, int n) {
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.isMarketOrder()) continue;
            byte by = liveOrderObj.getOrderType();
            double d = this.priceLevelReached(tickEvent, n, liveOrderObj.getOrderType(), liveOrderObj.getOpenPrice());
            if (!(d > 0.0)) continue;
            liveOrderObj.setOpenTime(this.tickData.getTime());
            if (this.fillAtRealAskBidPrice()) {
                liveOrderObj.setOpenPrice(d);
            }
            liveOrderObj.fillOrder(this.tickData);
            if (this.thereWasAGap(by, tickEvent)) {
                Log.debug("GAP detected - prev Close:{}, new Open: {}, realistic fill for MT4 set", (Object)this.closingPrice, (Object)tickEvent.getBid());
                liveOrderObj.setOpenPrice(MetaTraderSimulatorHedging.getPriceByType(by, this.tickData.getBid(), this.tickData.getAsk()));
            }
            liveOrderObj.setLastAction((byte)1);
            liveOrderObj.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj));
        }
        if (tickEvent.isBarClose()) {
            this.isNewBar = true;
            this.closingPrice = tickEvent.getBid();
        } else if (this.isNewBar) {
            this.isNewBar = false;
        }
    }

    protected void closeOrder(LiveOrderObj liveOrderObj, double d, byte by) {
        this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
        liveOrderObj.setCloseTime(this.tickData.getTime());
        liveOrderObj.setClosePrice(liveOrderObj.getClosePriceWithSlippage(this.slippage, d, by));
        liveOrderObj.setLastAction((byte)2);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setOrderStatus((byte)3);
        if (by == 2) {
            byte by2 = liveOrderObj.getSLType();
            if (by2 != -1 && (by2 == 20 || by2 == 21)) {
                liveOrderObj.setCloseType(by2);
            } else {
                liveOrderObj.setCloseType(by);
            }
        } else {
            liveOrderObj.setCloseType(by);
        }
        liveOrderObj.setCommSwap(this.getCommissionSwap(liveOrderObj));
        this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
        this.accountEquity = -1.0;
        this.fixMAEMFEByRealPrice(liveOrderObj);
        liveOrderObj.transformMAE_MFE();
        if (this.storePendingOrders || !liveOrderObj.isPendingOrder()) {
            this.closedTrades.add(liveOrderObj);
        }
    }

    @Override
    public ILiveOrder orderClose(StrategyBase strategyBase, ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) {
        LiveOrderObj liveOrderObj = (LiveOrderObj)iLiveOrder;
        this.removeOpenTrade(liveOrderObj);
        this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
        if (OrderTypes.isMarketOrder(liveOrderObj.getOrderType())) {
            double d = liveOrderObj.getPriceByType(OrderTypes.getOppositeType(liveOrderObj.getOrderType()), this.tickData.getBid(), this.tickData.getAsk(), this.slippage);
            liveOrderObj.setClosePrice(d);
        } else {
            liveOrderObj.setClosePrice(liveOrderObj.getOpenPrice());
        }
        liveOrderObj.setCloseTime(this.tickData.getTime());
        liveOrderObj.setLastAction((byte)2);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setOrderStatus((byte)3);
        liveOrderObj.setCloseType(by);
        liveOrderObj.setCommSwap(this.getCommissionSwap(liveOrderObj));
        this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
        this.accountEquity = -1.0;
        this.fixMAEMFEByRealPrice(liveOrderObj);
        liveOrderObj.transformMAE_MFE();
        if (this.storePendingOrders || !liveOrderObj.isPendingOrder()) {
            this.closedTrades.add(liveOrderObj);
        }
        return liveOrderObj;
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
            n2 = 2;
        }
        liveOrderObj.setLastAction((byte)1);
        liveOrderObj.setError(0, null);
        liveOrderObj.setOrderId(this.orderId++);
        liveOrderObj.setWorkingStatus((byte)-30);
        this.addOpenTrade(liveOrderObj);
        this.sendEvent(strategyBase, iTradingEventListener, n2, iLiveOrder);
        return iLiveOrder;
    }

    protected void addOpenTrade(LiveOrderObj liveOrderObj) throws TradingException {
        if (this.liveOrdersCount >= this.liveOrders.length - 1) {
            throw new BadStrategyException(32);
        }
        this.liveOrders[this.liveOrdersCount++] = liveOrderObj;
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
                if (this.orderErrorDetailedMessage) {
                    liveOrderObj.setError(6, "Incorrect price level. Open price: " + d3 + ", price level: " + d);
                } else {
                    liveOrderObj.setError(6, null);
                }
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d, false)) {
                if (this.orderErrorDetailedMessage) {
                    liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                } else {
                    liveOrderObj.setError(6, null);
                }
                return false;
            }
            d3 = d;
        }
        if (liveOrderObj.getSL() != -9.9999999E7) {
            d = liveOrderObj.getSL();
            by = liveOrderObj.getOrderTypeFromSLPT(-1);
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                if (this.orderErrorDetailedMessage) {
                    liveOrderObj.setError(6, "Incorrect stop level. Open price: " + d3 + ", price level: " + d);
                } else {
                    liveOrderObj.setError(6, null);
                }
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d, true)) {
                if (this.orderErrorDetailedMessage) {
                    liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                } else {
                    liveOrderObj.setError(6, null);
                }
                return false;
            }
        }
        if (liveOrderObj.getPT() != -9.9999999E7) {
            d = liveOrderObj.getPT();
            by = liveOrderObj.getOrderTypeFromSLPT(1);
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                if (this.orderErrorDetailedMessage) {
                    liveOrderObj.setError(6, "Incorrect stop level. Open price: " + d3 + ", price level: " + d);
                } else {
                    liveOrderObj.setError(6, null);
                }
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d, true)) {
                if (this.orderErrorDetailedMessage) {
                    liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                } else {
                    liveOrderObj.setError(6, null);
                }
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

    private boolean checkPriceLevelDistance(int n, double d, double d2, boolean bl) {
        if (this.chartData == null || this.chartData.getSymbolHash() != n) {
            this.chartData = this.marketPriceHolder.getChartData(n);
            this.chartDataMinDistance = this.chartData.getMinDistance() * this.chartData.getInstrumentInfo().tickSize;
            this.chartDataDecimals = this.chartData.getInstrumentInfo().decimals;
        }
        double d3 = Math.abs(d2 - d);
        if (bl && d3 == 0.0) {
            return false;
        }
        return SQUtils.compare((double)d3, (double)this.chartDataMinDistance, (int)this.chartDataDecimals) >= 0;
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
        if (liveOrderObj.isPendingOrder()) {
            return 0.0;
        }
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
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
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
        }
        return iLiveOrder;
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
            if (!this.checkPriceLevelDistance(n, d2, d, true)) {
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
            if (!this.checkPriceLevelDistance(n, d2, d, true)) {
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
            this.fixMAEMFEByRealPrice(liveOrderObj);
            liveOrderObj.transformMAE_MFE();
            this.closedTrades.add(liveOrderObj);
            f = (float)((double)f + liveOrderObj.getPL());
            this.removeOpenTradeNoFix(i);
        }
        this.liveOrdersCount = 0;
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
        for (int i = this.liveOrdersCount - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            liveOrderObj.evaluateActionListeners(n, strategyBase);
        }
    }

    @Override
    public boolean supportsDuplicateTrades() {
        return true;
    }
}

