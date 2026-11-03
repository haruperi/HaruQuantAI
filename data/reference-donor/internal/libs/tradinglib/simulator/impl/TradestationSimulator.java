/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.ticksimulator.ITickSimulator
 *  com.strategyquant.datalib.ticksimulator.TSTickSimulator
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.datalib.ticksimulator.TSTickSimulator;
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
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import com.strategyquant.tradinglib.event.TradingEventObj;
import com.strategyquant.tradinglib.event.TradingEventsArray;
import com.strategyquant.tradinglib.execution.ReservedBarsType;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.AbstractTradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.MarketPriceHolder;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.swap.SwapCalculator;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradestationSimulator
extends AbstractTradingSimulator {
    public static final Logger Log = LoggerFactory.getLogger((String)"TradestationSimulator");
    public static final Logger BacktestLog = LoggerFactory.getLogger((String)"BacktestLog");
    private static final long DAY_SECONDS = 86400000L;
    protected MarketPriceHolder marketPriceHolder = new MarketPriceHolder();
    protected OrdersList closedTrades;
    protected Long2FloatRBTreeMap dailyEquityValues;
    private long lastDayStartTime = -1L;
    private long nextDayStartTime = -1L;
    private float worstDailyEquity;
    private int orderId = -1000;
    private int connectionHash;
    private int lastSymbolHash;
    protected TickEvent tickData;
    private ChartData chartData = null;
    private TradingEventsArray tradingEventsArray = new TradingEventsArray();
    private float accountBalance;
    private double accountEquity;
    private float initialCapital;
    private double slippage;
    private CommissionsMethod commission;
    private SwapMethod swap;
    private boolean computeDailyStats = true;
    private ObjectArrayList<LiveOrderObj> preparedTrades = new ObjectArrayList();
    private ObjectArrayList<LiveOrderObj> tradesToClose = new ObjectArrayList();
    private ObjectArrayList<LiveOrderObj> tradesToCloseOnClose = new ObjectArrayList();
    protected double lastFilledPriceThisBar;
    private long lastTickTime;
    private double lastTickPrice;
    private double lastBidPrice;
    private double lastSpread;
    protected LiveOrderObj[] exitOrders = null;
    protected int exitOrdersCount = 0;
    private String connectionName;
    protected double bouncingTicksPct = 0.1;
    protected boolean useInitialSLPT = false;
    private final String initialSLComment = "InitialSL";
    private final String initialPTComment = "InitialPT";

    public TradestationSimulator() {
        super(new ReservedBarsType(1, 0, 0), (ITickSimulator)new TSTickSimulator());
    }

    @Override
    public ITradingSimulator clone() {
        TradestationSimulator tradestationSimulator = new TradestationSimulator();
        tradestationSimulator.setTestPrecision(this.getTestPrecision());
        return tradestationSimulator;
    }

    private void processNewTick(long l, double d, double d2, BarUpdateInfo barUpdateInfo) throws TradingException {
        if (barUpdateInfo != null) {
            if (barUpdateInfo.eventType == 3) {
                return;
            }
            if (barUpdateInfo.eventType == 2) {
                this.lastFilledPriceThisBar = 0.0;
            }
        }
        if (this.computeDailyStats) {
            this.tryUpdateDailyEquity();
        }
        this.lastFilledPriceThisBar = 0.0;
        if (this.tradesToClose.size() > 0 && barUpdateInfo.eventType == 2) {
            this.closePreparedOrders(this.tradesToClose);
        }
        if (this.tradesToCloseOnClose.size() > 0) {
            this.closePreparedOrders(this.tradesToCloseOnClose);
        }
        if (this.preparedTrades.size() > 0) {
            this.openPreparedOrders();
        }
        if (this.liveOrdersCount > 0) {
            this.accountEquity = -1.0;
        }
        TickEvent tickEvent = this.marketPriceHolder.getCurrentTick(this.lastSymbolHash);
        this.lastBidPrice = tickEvent.getBid();
        this.lastSpread = tickEvent.getAsk() - tickEvent.getBid();
        double d3 = d - d2;
        while (this.liveOrdersCount != 0 || this.exitOrdersCount != 0) {
            this.checkSLPT(tickEvent, this.lastSymbolHash, l, d, d2, d3, barUpdateInfo);
            this.checkStopLimitOrders(tickEvent, this.lastSymbolHash, l, d, d2, d3, barUpdateInfo);
            double d4 = tickEvent.getBid();
            if (this.lastBidPrice == d4) break;
            tickEvent.setAsk(this.lastBidPrice);
            tickEvent.setBid(this.lastBidPrice);
        }
        if (this.liveOrdersCount > 0 && this.computeDailyStats) {
            this.updateMAE_MFE();
        }
    }

    private void printLiveOrders() {
    }

    protected boolean checkPriceLevelCorrectness(int n, double d, double d2) {
        return true;
    }

    @Override
    public boolean fillAtRealAskBidPrice() {
        return false;
    }

    protected double getSLPTFilledPrice(double d, double d2, int n) {
        if (n == 2) {
            return d;
        }
        return d2;
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
        this.storePendingOrders = !Boolean.parseBoolean(MainApp.settings().get("dontStorePendingOrders", "true"));
        this.useInitialSLPT = false;
        if (settingsMap.containsKey("TradingOptions") && settingsMap.get("TradingOptions") instanceof TradingOptions) {
            TradingOptions tradingOptions = (TradingOptions)settingsMap.get("TradingOptions");
            for (int i = 0; i < tradingOptions.size(); ++i) {
                TradingOption tradingOption = (TradingOption)tradingOptions.get(i);
                if (!tradingOption.getClass().getSimpleName().equals("UseInitialSLPT")) continue;
                try {
                    this.useInitialSLPT = (Boolean)tradingOption.getParameterValue("UseInitialSLPT");
                }
                catch (Exception exception) {
                    Log.error("Unable to read UseInitialSLPT value", (Throwable)exception);
                    this.useInitialSLPT = false;
                }
                break;
            }
        }
    }

    @Override
    public void initialize(MarketData marketData) {
        this.liveOrders = new LiveOrderObj[100];
        this.liveOrdersCount = 0;
        this.exitOrders = new LiveOrderObj[100];
        this.exitOrdersCount = 0;
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
    public void eventNewTick(TickEvent tickEvent, double d, double d2, BarUpdateInfo barUpdateInfo) throws TradingException {
        if (tickEvent.getConnectionHash() != this.connectionHash) {
            return;
        }
        this.lastSymbolHash = tickEvent.getSymbolHash();
        if (this.lastSymbolHash != this.tradingSymbolHash) {
            return;
        }
        TickEvent tickEvent2 = this.marketPriceHolder.setNewTick(this.lastSymbolHash, tickEvent);
        this.lastTickTime = tickEvent2.getTime();
        this.lastTickPrice = tickEvent2.getBid();
        if (tickEvent2 != null) {
            this.tickData = tickEvent2;
            if (this.getTestPrecision() != 5) {
                this.processNewTick(tickEvent.getTime(), d, d2, barUpdateInfo);
            }
        }
    }

    private void closePreparedOrders(ObjectArrayList<LiveOrderObj> objectArrayList) {
        if (objectArrayList.size() == 0) {
            return;
        }
        ObjectListIterator objectListIterator = objectArrayList.iterator();
        while (objectListIterator.hasNext()) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)objectListIterator.next();
            int n = liveOrderObj.getWaitingBars();
            if (n > 0) {
                liveOrderObj.setWaitingBars(n - 1);
                continue;
            }
            objectListIterator.remove();
            if (!this.removeOpenTrade(liveOrderObj)) continue;
            this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
            if (OrderTypes.isMarketOrder(liveOrderObj.getOrderType())) {
                double d = liveOrderObj.getPriceByType(OrderTypes.getOppositeType(liveOrderObj.getOrderType()), this.tickData.getBid(), this.tickData.getAsk(), 0.0);
                liveOrderObj.setClosePrice(d);
            } else {
                liveOrderObj.setClosePrice(liveOrderObj.getOpenPrice());
            }
            liveOrderObj.setCloseTime(this.tickData.getTime());
            liveOrderObj.setLastAction((byte)2);
            liveOrderObj.setWorkingStatus((byte)-30);
            liveOrderObj.setOrderStatus((byte)3);
            this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
            if (liveOrderObj.isMarketOrder()) {
                this.accountBalance = (float)((double)this.accountBalance - this.getCommSlippage(liveOrderObj));
            }
            if (!this.storePendingOrders && (liveOrderObj.isPendingOrder() || liveOrderObj.isExitOrder())) continue;
            this.fixMAEMFEByRealPrice(liveOrderObj);
            liveOrderObj.transformMAE_MFE();
            this.addToClosedTrades(liveOrderObj);
        }
    }

    private double getCommSlippage(LiveOrderObj liveOrderObj) {
        return -1.0 * this.getCommissionSwap(liveOrderObj) + this.getSlippageInMoney(liveOrderObj);
    }

    private void addToClosedTrades(LiveOrderObj liveOrderObj) {
        if (liveOrderObj.getOpenTime() != liveOrderObj.getCloseTime()) {
            liveOrderObj.increaseBarsInTrade();
        }
        liveOrderObj.setCommSwap(this.getCommissionSwap(liveOrderObj));
        liveOrderObj.setSlippageInMoney(this.getSlippageInMoney(liveOrderObj));
        this.closedTrades.add(liveOrderObj);
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
            try {
                d -= this.commission.computeCommissionsOnOpen(liveOrderObj, this.chartData.getInstrumentInfo().tickSize, this.chartData.getInstrumentInfo().pointValue);
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

    private double getSlippageInMoney(LiveOrderObj liveOrderObj) {
        if (liveOrderObj.isPendingOrder()) {
            return 0.0;
        }
        return 2.0 * this.slippage;
    }

    private void openPreparedOrders() {
        while (this.preparedTrades.size() > 0) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.preparedTrades.get(0);
            this.preparedTrades.remove(0);
            try {
                if (liveOrderObj.isMarketOrder()) {
                    this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
                    byte by = liveOrderObj.getOrderType();
                    double d = liveOrderObj.getOpenPrice();
                    liveOrderObj.setOpenTime(this.tickData.getTime());
                    liveOrderObj.setOpenPrice(liveOrderObj.getPriceByType(by, this.tickData.getBid(), this.tickData.getAsk(), 0.0));
                    liveOrderObj.setOriginalOpenPrice(liveOrderObj.getOpenPrice());
                    liveOrderObj.setWorkingStatus((byte)-30);
                    liveOrderObj.setFilled(true);
                    this.addOpenTrade(liveOrderObj);
                    this.openInitialSLOrder(liveOrderObj, d, false);
                    this.openInitialPTOrder(liveOrderObj, d, false);
                    continue;
                }
                throw new Exception("Not implemented here!");
            }
            catch (Exception exception) {
                Log.error("openPreparedOrders()", (Throwable)exception);
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

    protected void checkSLPT(TickEvent tickEvent, int n, long l, double d, double d2, double d3, BarUpdateInfo barUpdateInfo) {
        LiveOrderObj liveOrderObj = this.findExistingMarketOrder(-1, -1);
        if (liveOrderObj == null) {
            return;
        }
        boolean bl = false;
        boolean bl2 = false;
        for (int i = 0; i < this.exitOrdersCount; ++i) {
            boolean bl3;
            LiveOrderObj liveOrderObj2 = this.exitOrders[i];
            if (liveOrderObj2 == null || liveOrderObj2.getSymbolHash() != n) continue;
            if (!liveOrderObj2.isExitOrder()) {
                throw new IllegalArgumentException("This shouldn't happen");
            }
            if (liveOrderObj2.getBarsInTrade() >= 1) {
                this.removeClosingTradeNoFix(i);
                bl2 = true;
                continue;
            }
            int n2 = liveOrderObj2.getMagicNumber();
            if (n2 != 0 && n2 != liveOrderObj.getMagicNumber()) continue;
            boolean bl4 = liveOrderObj2.getOrderType() == 102 || liveOrderObj2.getOrderType() == 100;
            boolean bl5 = bl3 = liveOrderObj2.getOrderType() == 103 || liveOrderObj2.getOrderType() == 101;
            if ((!this.useInitialSLPT || !bl4 && !bl3) && liveOrderObj2.getOpenTime() < liveOrderObj.getOpenTime() || (bl4 || bl3) && liveOrderObj2.getOpenTime() < liveOrderObj.getOpenTime()) continue;
            liveOrderObj2.setTickData(this.tickData.getAsk(), this.tickData.getBid());
            double d4 = this.priceLevelReached(tickEvent, n, liveOrderObj2, barUpdateInfo);
            if (d4 == 0.0 || this.stopLimitShouldBeFilledFirst(tickEvent, n, liveOrderObj2.getOrderType(), liveOrderObj2.getOpenPrice(), barUpdateInfo) || this.otherExitStopShouldBeFilledFirst(tickEvent, i, n, liveOrderObj2.getOrderType(), liveOrderObj2.getOpenPrice(), barUpdateInfo)) continue;
            byte by = liveOrderObj2.getOrderType();
            d4 = by == 100 || by == 101 ? this.fixByHighLow(d4, d + this.lastSpread, d2 + this.lastSpread) : this.fixByHighLow(d4, d, d2);
            d4 = this.getStopLimitFillPrice(d4, liveOrderObj2);
            if (barUpdateInfo.eventType != 2) {
                this.tradestationBouncingTicks(tickEvent, this.bouncingTicksPct, d, d2, d3, n, liveOrderObj2.getOrderType(), liveOrderObj2.getInstrumentInfo(), liveOrderObj2.getOpenPrice());
            }
            this.lastFilledPriceThisBar = d4;
            this.closeOrder(liveOrderObj, d4, this.getOrderCloseType(liveOrderObj2.getOrderType()));
            this.removeOpenTrade(liveOrderObj, false);
            bl = true;
            this.removeClosingTradeNoFix(i);
            bl2 = true;
            try {
                liveOrderObj2.evaluateActionListeners(7, null);
            }
            catch (TradingException tradingException) {
                Log.error("Error while calling Order filled action listeners", (Throwable)tradingException);
            }
            break;
        }
        if (bl) {
            this.fixRemovedElements();
        }
        if (bl2) {
            this.fixRemovedClosingElements();
        }
    }

    protected boolean otherExitStopShouldBeFilledFirst(TickEvent tickEvent, int n, int n2, byte by, double d, BarUpdateInfo barUpdateInfo) {
        for (int i = 0; i < this.exitOrdersCount; ++i) {
            byte by2;
            double d2;
            LiveOrderObj liveOrderObj = this.exitOrders[i];
            if (liveOrderObj == null || i == n || liveOrderObj.getSymbolHash() != n2 || liveOrderObj.getBarsInTrade() == 1 || this.liveOrdersCount > 1 && this.findExistingMarketOrder(liveOrderObj.getMagicNumber(), i) != null || (d2 = this.priceLevelReached(tickEvent, n2, liveOrderObj, barUpdateInfo)) == 0.0 || !((by2 = liveOrderObj.getOrderType()) == 102 && by == 102 ? liveOrderObj.getOpenPrice() > d : by2 == 100 && by == 100 && liveOrderObj.getOpenPrice() < d)) continue;
            return true;
        }
        return false;
    }

    protected boolean stopLimitShouldBeFilledFirst(TickEvent tickEvent, int n, byte by, double d, BarUpdateInfo barUpdateInfo) {
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            double d2;
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj == null || liveOrderObj.getSymbolHash() != n || liveOrderObj.isMarketOrder()) continue;
            if (liveOrderObj.isExitOrder()) {
                throw new IllegalArgumentException("This shouldn't happen");
            }
            if (liveOrderObj.getBarsInTrade() == 1 || liveOrderObj.getExitIndex() < 0 && this.liveOrdersCount > 1 && this.findExistingMarketOrder(liveOrderObj.getMagicNumber(), i) != null || (d2 = this.priceLevelReached(tickEvent, n, liveOrderObj, barUpdateInfo)) == 0.0) continue;
            byte by2 = liveOrderObj.getOrderType();
            if (by2 == 6 && by == 102) {
                return liveOrderObj.getOpenPrice() > d;
            }
            if (by2 != 5 || by != 100) continue;
            return liveOrderObj.getOpenPrice() < d;
        }
        return false;
    }

    protected byte getOrderCloseType(byte by) {
        if (by == 100 || by == 102) {
            return 2;
        }
        return 3;
    }

    protected void checkStopLimitOrders(TickEvent tickEvent, int n, long l, double d, double d2, double d3, BarUpdateInfo barUpdateInfo) throws TradingException {
        LiveOrderObj liveOrderObj;
        int n2;
        boolean bl = false;
        boolean bl2 = false;
        for (n2 = 0; n2 < this.liveOrdersCount; ++n2) {
            LiveOrderObj liveOrderObj2;
            liveOrderObj = this.liveOrders[n2];
            if (liveOrderObj == null || liveOrderObj.getSymbolHash() != n || liveOrderObj.isMarketOrder()) continue;
            if (liveOrderObj.isExitOrder()) {
                throw new IllegalArgumentException("This shouldn't happen");
            }
            if (!liveOrderObj.usesATM() && liveOrderObj.getBarsInTrade() == 1) {
                this.removeOpenTradeNoFix(n2);
                bl = true;
                continue;
            }
            if (!liveOrderObj.usesATM() && this.liveOrdersCount > 1 && (liveOrderObj2 = this.findExistingMarketOrder(liveOrderObj.getMagicNumber(), n2)) != null && !OrderTypes.areOppositeOrders(liveOrderObj.getOrderType(), liveOrderObj2.getOrderType())) continue;
            double d4 = liveOrderObj.getOpenPrice();
            boolean bl3 = false;
            double d5 = this.priceLevelReached(tickEvent, n, liveOrderObj, barUpdateInfo);
            if (d5 == 0.0) continue;
            byte by = liveOrderObj.getOrderType();
            d5 = by == 5 || by == 3 ? this.fixByHighLow(d5, d + this.lastSpread, d2 + this.lastSpread) : this.fixByHighLow(d5, d, d2);
            d5 = this.getStopLimitFillPrice(d5, liveOrderObj);
            liveOrderObj.setOpenTime(this.tickData.getTime());
            liveOrderObj.setOpenPrice(d5);
            if (!liveOrderObj.usesATM() && this.closeExistingOppositeDirectionLiveOrders(n2, n, liveOrderObj)) {
                bl = true;
            }
            bl2 = bl;
            if (barUpdateInfo.eventType != 2) {
                bl3 = this.tradestationBouncingTicks(tickEvent, this.bouncingTicksPct, d, d2, d3, n, liveOrderObj.getOrderType(), liveOrderObj.getInstrumentInfo(), liveOrderObj.getOpenPrice());
            }
            this.lastFilledPriceThisBar = d5;
            liveOrderObj.fillOrder(this.tickData);
            liveOrderObj.setLastAction((byte)1);
            liveOrderObj.setFilled(true);
            if (liveOrderObj.usesATM()) {
                this.tryPairMarketOrders(liveOrderObj);
                liveOrderObj.setWorkingStatus((byte)-30);
                liveOrderObj.setOrderStatus((byte)3);
                liveOrderObj.setCloseType((byte)1);
                this.removeOpenTrade(liveOrderObj, false);
                bl = true;
            } else {
                double d6 = d5;
                LiveOrderObj liveOrderObj3 = this.checkSLPTForOrder(n, liveOrderObj, barUpdateInfo);
                if (liveOrderObj3 == null && bl3 && (liveOrderObj3 = this.checkSLPTForOrderByHighLow(n, liveOrderObj, barUpdateInfo, tickEvent.getAsk(), tickEvent.getBid())) != null) {
                    d6 = liveOrderObj3.getOpenPrice();
                }
                if (liveOrderObj3 != null) {
                    this.closeOrder(liveOrderObj, d6, this.getOrderCloseType(liveOrderObj3.getOrderType()));
                    this.removeOpenTrade(liveOrderObj, false);
                    bl = true;
                    this.removeOpenTrade(liveOrderObj3, false);
                    bl2 = true;
                }
                if (liveOrderObj3 == null) {
                    this.openInitialSLOrder(liveOrderObj, d4, true);
                    this.openInitialPTOrder(liveOrderObj, d4, true);
                }
            }
            try {
                liveOrderObj.evaluateActionListeners(7, null);
                continue;
            }
            catch (TradingException tradingException) {
                Log.error("Error while calling Order filled action listeners", (Throwable)tradingException);
            }
        }
        for (n2 = 0; n2 < this.exitOrdersCount; ++n2) {
            liveOrderObj = this.exitOrders[n2];
            if (liveOrderObj == null || liveOrderObj.getSymbolHash() != n || liveOrderObj.isMarketOrder() || liveOrderObj.usesATM() || liveOrderObj.getBarsInTrade() != 1) continue;
            this.exitOrders[n2] = null;
            bl2 = true;
        }
        if (bl) {
            this.fixRemovedElements();
        }
        if (bl2) {
            this.fixRemovedClosingElements();
        }
    }

    private boolean closeExistingOppositeDirectionLiveOrders(int n, int n2, LiveOrderObj liveOrderObj) {
        int n3 = liveOrderObj.getDirection() * -1;
        boolean bl = false;
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj2;
            if (i == n || (liveOrderObj2 = this.liveOrders[i]) == null || liveOrderObj2.getSymbolHash() != n2 || !liveOrderObj2.isMarketOrder() || liveOrderObj2.getDirection() != n3) continue;
            this.closeOrder(liveOrderObj2, liveOrderObj.getOpenPrice(), (byte)7);
            this.removeOpenTrade(liveOrderObj2, false);
            bl = true;
        }
        return bl;
    }

    protected double fixByHighLow(double d, double d2, double d3) {
        if (d < d3) {
            return d3;
        }
        if (d > d2) {
            return d2;
        }
        return d;
    }

    private LiveOrderObj checkSLPTForOrder(int n, LiveOrderObj liveOrderObj, BarUpdateInfo barUpdateInfo) {
        double d = liveOrderObj.getOpenPrice();
        int n2 = liveOrderObj.getDirection();
        for (int i = 0; i < this.exitOrdersCount; ++i) {
            int n3;
            LiveOrderObj liveOrderObj2 = this.exitOrders[i];
            if (liveOrderObj2 == null || liveOrderObj2.getSymbolHash() != n) continue;
            if (!liveOrderObj2.isExitOrder()) {
                throw new IllegalArgumentException("This shouldn't happen");
            }
            if (liveOrderObj2.getBarsInTrade() >= 1 || (n3 = liveOrderObj2.getMagicNumber()) != 0 && n3 != liveOrderObj.getMagicNumber()) continue;
            byte by = liveOrderObj2.getOrderType();
            double d2 = liveOrderObj2.getOpenPrice();
            if (liveOrderObj.getOriginalOpenTime() == liveOrderObj2.getOpenTime()) {
                double d3;
                if ((by == 102 || by == 100) && (OrderTypes.isStopOrder(liveOrderObj.getOriginalOrderType()) || OrderTypes.isLimitOrder(liveOrderObj.getOriginalOrderType()))) {
                    d3 = this.computeRealSLFromOrder(liveOrderObj, liveOrderObj2.getOpenPrice(), true);
                    liveOrderObj.setSL(d3);
                    liveOrderObj.setInitialSL(d3);
                    d2 = d3;
                    liveOrderObj2.setOpenPrice(d2);
                }
                if ((by == 103 || by == 101) && (OrderTypes.isStopOrder(liveOrderObj.getOriginalOrderType()) || OrderTypes.isLimitOrder(liveOrderObj.getOriginalOrderType()))) {
                    d3 = this.computeRealPTFromOrder(liveOrderObj, liveOrderObj2.getOpenPrice(), true);
                    liveOrderObj.setPT(d3);
                    d2 = d3;
                    liveOrderObj2.setOpenPrice(d2);
                }
            }
            if (!(n2 > 0 ? (by == 102 ? d <= d2 : by == 103 && d >= d2) : (by == 100 ? d >= d2 : by == 101 && d <= d2))) continue;
            return liveOrderObj2;
        }
        return null;
    }

    private LiveOrderObj checkSLPTForOrderByHighLow(int n, LiveOrderObj liveOrderObj, BarUpdateInfo barUpdateInfo, double d, double d2) {
        double d3 = liveOrderObj.getOpenPrice();
        int n2 = liveOrderObj.getDirection();
        for (int i = 0; i < this.exitOrdersCount; ++i) {
            int n3;
            LiveOrderObj liveOrderObj2 = this.exitOrders[i];
            if (liveOrderObj2 == null || liveOrderObj2.getSymbolHash() != n) continue;
            if (!liveOrderObj2.isExitOrder()) {
                throw new IllegalArgumentException("This shouldn't happen");
            }
            if (liveOrderObj2.getBarsInTrade() >= 1 || (n3 = liveOrderObj2.getMagicNumber()) != 0 && n3 != liveOrderObj.getMagicNumber()) continue;
            byte by = liveOrderObj2.getOrderType();
            double d4 = liveOrderObj2.getOpenPrice();
            if (liveOrderObj.getOriginalOpenTime() != liveOrderObj2.getOpenTime() || !OrderTypes.isStopOrder(liveOrderObj.getOriginalOrderType()) && !OrderTypes.isLimitOrder(liveOrderObj.getOriginalOrderType())) continue;
            d4 = liveOrderObj2.getOpenPrice();
            if (!(n2 > 0 ? (by == 102 ? d2 <= d4 : by == 103 && d >= d4) : (by == 100 ? d2 >= d4 : by == 101 && d <= d4))) continue;
            return liveOrderObj2;
        }
        return null;
    }

    protected double getStopLimitFillPrice(double d, LiveOrderObj liveOrderObj) {
        byte by = liveOrderObj.getOrderType();
        if (by == 101 || by == 103) {
            return d;
        }
        int n = liveOrderObj.getDirection();
        if (this.lastFilledPriceThisBar <= 0.0) {
            return d;
        }
        if (n > 0) {
            if ((OrderTypes.isStopOrder(by) || OrderTypes.isLimitOrder(by)) && this.lastFilledPriceThisBar > d) {
                return this.lastFilledPriceThisBar;
            }
            if (OrderTypes.isLimitOrder(by) && this.lastFilledPriceThisBar < d) {
                return this.lastFilledPriceThisBar;
            }
        } else if (n < 0) {
            if ((OrderTypes.isStopOrder(by) || OrderTypes.isLimitOrder(by)) && this.lastFilledPriceThisBar < d) {
                return this.lastFilledPriceThisBar;
            }
            if (OrderTypes.isLimitOrder(by) && this.lastFilledPriceThisBar > d) {
                return this.lastFilledPriceThisBar;
            }
        }
        return d;
    }

    protected LiveOrderObj findExistingMarketOrder(int n, int n2) {
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj;
            if (i == n2 || (liveOrderObj = this.liveOrders[i]) == null || liveOrderObj.isExitOrder() || liveOrderObj.usesATM() || !liveOrderObj.isMarketOrder() || n != -1 && liveOrderObj.getMagicNumber() != n) continue;
            return liveOrderObj;
        }
        return null;
    }

    protected void closeOrder(LiveOrderObj liveOrderObj, double d, byte by) {
        if (liveOrderObj.isExitOrder()) {
            return;
        }
        this.tickData = this.marketPriceHolder.getCurrentTick(liveOrderObj.getSymbolHash());
        liveOrderObj.setCloseTime(this.tickData.getTime());
        liveOrderObj.setClosePrice(liveOrderObj.getClosePriceWithSlippage(0.0, d, by));
        liveOrderObj.setLastAction((byte)2);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setOrderStatus((byte)3);
        liveOrderObj.setCloseType(by);
        this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
        if (liveOrderObj.isMarketOrder()) {
            this.accountBalance = (float)((double)this.accountBalance - this.getCommSlippage(liveOrderObj));
        }
        if (this.storePendingOrders || !liveOrderObj.isPendingOrder()) {
            this.fixMAEMFEByRealPrice(liveOrderObj);
            liveOrderObj.transformMAE_MFE();
            this.addToClosedTrades(liveOrderObj);
        }
    }

    @Override
    public ILiveOrder orderClose(StrategyBase strategyBase, ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) {
        LiveOrderObj liveOrderObj = (LiveOrderObj)iLiveOrder;
        if (liveOrderObj.isExitOrder()) {
            return liveOrderObj;
        }
        if (by == 5 || by == 14) {
            this.removeOpenTrade(liveOrderObj);
            liveOrderObj.setClosePrice(this.lastTickPrice);
            liveOrderObj.setCloseTime(this.lastTickTime);
            liveOrderObj.setLastAction((byte)2);
            liveOrderObj.setWorkingStatus((byte)-30);
            liveOrderObj.setOrderStatus((byte)3);
            liveOrderObj.setCloseType(by);
            this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
            if (liveOrderObj.isMarketOrder()) {
                this.accountBalance = (float)((double)this.accountBalance - this.getCommSlippage(liveOrderObj));
            }
            if (this.storePendingOrders || !liveOrderObj.isPendingOrder()) {
                this.fixMAEMFEByRealPrice(liveOrderObj);
                liveOrderObj.transformMAE_MFE();
                this.addToClosedTrades(liveOrderObj);
            }
        } else if (by == 13 || by == 16) {
            if (!this.tradesToCloseOnClose.contains((Object)liveOrderObj)) {
                liveOrderObj.setCloseType(by);
                this.tradesToCloseOnClose.add((Object)liveOrderObj);
            }
        } else {
            liveOrderObj.setCloseType(by);
            this.tradesToClose.add((Object)liveOrderObj);
        }
        return liveOrderObj;
    }

    @Override
    public void eventBarUpdated(int n) {
        if (n == 3) {
            this.increaseBarsInTrade();
        }
    }

    private void increaseBarsInTrade() {
        int n;
        for (n = 0; n < this.liveOrdersCount; ++n) {
            if (this.tickData.getTime() == this.liveOrders[n].getOpenTime()) continue;
            this.liveOrders[n].increaseBarsInTrade();
        }
        for (n = 0; n < this.exitOrdersCount; ++n) {
            if (this.tickData.getTime() == this.exitOrders[n].getOpenTime()) continue;
            this.exitOrders[n].increaseBarsInTrade();
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
            liveOrderObj.setOpenPrice(liveOrderObj.getPriceByType(by, this.tickData.getBid(), this.tickData.getAsk(), 0.0));
            liveOrderObj.setOriginalOpenPrice(liveOrderObj.getOpenPrice());
            liveOrderObj.setOrderStatus((byte)1);
            n2 = 1;
        } else {
            liveOrderObj.setOrderStatus((byte)2);
            n2 = 2;
        }
        liveOrderObj.setLastAction((byte)1);
        liveOrderObj.setError(0, null);
        liveOrderObj.setOrderId(this.orderId++);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setFilled(false);
        this.addPreparedTrade(liveOrderObj);
        this.sendEvent(strategyBase, iTradingEventListener, n2, iLiveOrder);
        return iLiveOrder;
    }

    protected void addOpenTrade(LiveOrderObj liveOrderObj) throws TradingException {
        if (liveOrderObj.usesATM()) {
            this.tryPairMarketOrders(liveOrderObj);
            liveOrderObj.setWorkingStatus((byte)-30);
            liveOrderObj.setOrderStatus((byte)3);
            liveOrderObj.setCloseType((byte)1);
            this.removeOpenTrade(liveOrderObj, true);
            return;
        }
        if (this.liveOrdersCount >= this.liveOrders.length - 1) {
            throw new BadStrategyException(32);
        }
        this.liveOrders[this.liveOrdersCount++] = liveOrderObj;
    }

    private void tryPairMarketOrders(LiveOrderObj liveOrderObj) {
        double d = liveOrderObj.getSize();
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj2 = this.liveOrders[i];
            if (liveOrderObj2 == null || !liveOrderObj2.isMarketOrder() || liveOrderObj2.usesATM() || liveOrderObj.isLong() == liveOrderObj2.isLong()) continue;
            if (liveOrderObj2.getSize() >= d) {
                liveOrderObj.setClosePrice(liveOrderObj.getOpenPrice());
                liveOrderObj.setCloseTime(liveOrderObj.getOpenTime());
                liveOrderObj.setCloseType((byte)1);
                liveOrderObj.setOriginalOpenTime(liveOrderObj2.getOriginalOpenTime());
                liveOrderObj.setOpenPrice(liveOrderObj2.getOpenPrice());
                liveOrderObj.setOpenTime(liveOrderObj2.getOpenTime());
                liveOrderObj.setOrderType(liveOrderObj2.getOrderType());
                liveOrderObj.setWorkingStatus((byte)-30);
                liveOrderObj.setOrderStatus((byte)3);
                this.fixMAEMFEByRealPrice(liveOrderObj);
                liveOrderObj.transformMAE_MFE();
                this.accountBalance = (float)((double)this.accountBalance + liveOrderObj.getPL());
                if (liveOrderObj.isMarketOrder()) {
                    this.accountBalance = (float)((double)this.accountBalance - this.getCommSlippage(liveOrderObj));
                }
                this.addToClosedTrades(liveOrderObj);
                liveOrderObj2.setSize(liveOrderObj2.getSize() - d);
                if (liveOrderObj2.getSize() == 0.0) {
                    this.removeOpenTrade(liveOrderObj2);
                }
                d = 0.0;
                break;
            }
            liveOrderObj2.setClosePrice(liveOrderObj.getOpenPrice());
            liveOrderObj2.setCloseTime(liveOrderObj.getOpenTime());
            liveOrderObj2.setCloseType((byte)1);
            liveOrderObj2.setWorkingStatus((byte)-30);
            liveOrderObj2.setOrderStatus((byte)3);
            liveOrderObj.setSize(d -= liveOrderObj2.getSize());
            if (d == 0.0) break;
        }
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    protected void addPreparedTrade(LiveOrderObj liveOrderObj) throws TradingException {
        if (liveOrderObj.isMarketOrder()) {
            this.preparedTrades.add((Object)liveOrderObj);
            try {
                liveOrderObj.evaluateActionListeners(7, null);
                return;
            }
            catch (TradingException tradingException) {
                Log.error("Error while calling Order filled action listeners", (Throwable)tradingException);
            }
            return;
        }
        if (liveOrderObj.isExitOrder()) {
            if (this.exitOrdersCount >= this.exitOrders.length - 1) throw new BadStrategyException(32);
            this.exitOrders[this.exitOrdersCount++] = liveOrderObj;
            return;
        } else {
            if (this.liveOrdersCount >= this.liveOrders.length - 1) throw new BadStrategyException(32);
            this.liveOrders[this.liveOrdersCount++] = liveOrderObj;
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
        if (liveOrderObj.getSL() != 0.0) {
            d = liveOrderObj.getSL();
            by = liveOrderObj.getOrderTypeFromSLPT(-1);
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                liveOrderObj.setError(6, "Incorrect stop level. Open price: " + d3 + ", price level: " + d);
                return false;
            }
            if (!this.checkPriceLevelDistance(n, d3, d)) {
                liveOrderObj.setError(6, "Incorrect price level distance. Open price: " + d3 + ", price level: " + d);
                return false;
            }
        }
        if (liveOrderObj.getPT() != 0.0) {
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

    private boolean checkPriceLevelDistance(int n, double d, double d2) {
        return true;
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
        LiveOrderObj liveOrderObj;
        int n2;
        for (n2 = 0; n2 < this.liveOrdersCount; ++n2) {
            liveOrderObj = this.liveOrders[n2];
            if (liveOrderObj != iLiveOrder) continue;
            if (!this.checkOrderSLPT(liveOrderObj)) {
                return liveOrderObj;
            }
            liveOrderObj.setSLFromModified();
            liveOrderObj.setPTFromModified();
            return iLiveOrder;
        }
        if (this.useInitialSLPT) {
            for (n2 = 0; n2 < this.preparedTrades.size(); ++n2) {
                liveOrderObj = (LiveOrderObj)this.preparedTrades.get(n2);
                if (liveOrderObj != iLiveOrder) continue;
                if (!this.checkOrderSLPT(liveOrderObj)) {
                    return liveOrderObj;
                }
                liveOrderObj.setSLFromModified();
                liveOrderObj.setPTFromModified();
            }
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
            if (liveOrderObj.isExitOrder()) continue;
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
            this.addToClosedTrades(liveOrderObj);
            f = (float)((double)f + liveOrderObj.getPL());
            this.removeOpenTradeNoFix(i);
        }
        this.liveOrdersCount = 0;
        this.accountEquity = f;
    }

    @Override
    public int getEngineId() {
        return 56756755;
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
        return 3;
    }

    @Override
    public void eventNewTick(TickEvent tickEvent, double d, double d2) {
    }

    @Override
    public boolean getApplyExitsAtTheEndOfRule() {
        return true;
    }

    @Override
    protected double getSLPTFilledPrice(double d, double d2) {
        throw new IllegalArgumentException("Not used in Tradestation");
    }

    @Override
    protected boolean removeOpenTrade(LiveOrderObj liveOrderObj) {
        return this.removeOpenTrade(liveOrderObj, true);
    }

    @Override
    protected boolean removeOpenTrade(LiveOrderObj liveOrderObj, boolean bl) {
        int n;
        boolean bl2 = false;
        for (n = 0; n < this.liveOrdersCount; ++n) {
            if (this.liveOrders[n] != liveOrderObj) continue;
            this.removeOpenTradeNoFix(n);
            bl2 = true;
            break;
        }
        if (bl && bl2) {
            this.fixRemovedElements();
        }
        if (!bl2) {
            for (n = 0; n < this.exitOrdersCount; ++n) {
                if (this.exitOrders[n] != liveOrderObj) continue;
                this.removeClosingTradeNoFix(n);
                bl2 = true;
                break;
            }
            if (bl && bl2) {
                this.fixRemovedClosingElements();
            }
        }
        return bl2;
    }

    protected void fixRemovedClosingElements() {
        int n = -1;
        for (int i = 0; i < this.exitOrdersCount; ++i) {
            if (this.exitOrders[i] == null) continue;
            this.exitOrders[++n] = this.exitOrders[i];
        }
        this.exitOrdersCount = n == -1 ? 0 : n + 1;
    }

    protected void removeClosingTradeNoFix(int n) {
        if (n >= 0 && n < this.exitOrdersCount) {
            this.reuseTemporaryOrder(this.exitOrders[n]);
            this.exitOrders[n] = null;
        }
    }

    @Override
    public void evaluateActionListeners(int n, StrategyBase strategyBase) throws TradingException {
        for (int i = this.liveOrdersCount - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            liveOrderObj.evaluateActionListeners(n, strategyBase);
        }
    }

    protected boolean tradestationBouncingTicks(TickEvent tickEvent, double d, double d2, double d3, double d4, int n, byte by, InstrumentInfo instrumentInfo, double d5) {
        double d6 = 0.0;
        switch (by) {
            case 6: {
                d6 = 1.0;
                break;
            }
            case 102: {
                d6 = 1.0;
                break;
            }
            case 5: {
                d6 = -1.0;
                break;
            }
            case 100: {
                d6 = -1.0;
                break;
            }
            case 4: {
                d6 = -1.0;
                break;
            }
            case 103: {
                d6 = -1.0;
                break;
            }
            case 3: {
                d6 = 1.0;
                break;
            }
            case 101: {
                d6 = 1.0;
            }
        }
        double d7 = instrumentInfo.tickStep;
        double d8 = d4 / d7;
        double d9 = d * d8;
        d9 = Math.floor(d9);
        double d10 = d9 * d7;
        double d11 = tickEvent.getBid();
        double d12 = d5 + d6 * d10;
        if (d12 < d3) {
            d12 = d3 < d11 ? d3 : d11;
        } else if (d12 > d2) {
            d12 = d2 > d11 ? d2 : d11;
        }
        if (d12 != d11) {
            tickEvent.setAsk(d12);
            tickEvent.setBid(d12);
            return true;
        }
        return false;
    }

    private double priceLevelReached(TickEvent tickEvent, int n, LiveOrderObj liveOrderObj, BarUpdateInfo barUpdateInfo) {
        if (tickEvent.getTime() == -1L) {
            return 0.0;
        }
        byte by = liveOrderObj.getOrderType();
        double d = liveOrderObj.getOpenPrice();
        if (by == 6 || by == 102) {
            if (tickEvent.getBid() <= d) {
                if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                    return tickEvent.getBid();
                }
                return d;
            }
        } else if (by == 5 || by == 100) {
            if (tickEvent.getAsk() >= d) {
                if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                    return tickEvent.getAsk();
                }
                return d;
            }
        } else if (by == 4 || by == 103) {
            if (tickEvent.getBid() >= d) {
                if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                    return tickEvent.getBid();
                }
                return d;
            }
        } else if ((by == 3 || by == 101) && tickEvent.getAsk() <= d) {
            if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                return tickEvent.getAsk();
            }
            return d;
        }
        return 0.0;
    }

    @Override
    public boolean supportsDuplicateTrades() {
        return false;
    }

    @Override
    public int getOpenOrdersCount(boolean bl) {
        if (this.liveOrdersCount == 0) {
            return 0;
        }
        int n = 0;
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj.getPositionStatus() != 1 && liveOrderObj.getPositionStatus() != 2 || !bl && this.tradesToClose.contains((Object)liveOrderObj) || !bl && this.tradesToCloseOnClose.contains((Object)liveOrderObj)) continue;
            ++n;
        }
        return n;
    }

    @Override
    public ILiveOrder getOpenOrder(int n, boolean bl) {
        if (n < 0 || n >= this.liveOrdersCount) {
            throw new IllegalArgumentException("Trade index is out of range!");
        }
        int n2 = 0;
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            LiveOrderObj liveOrderObj = this.liveOrders[i];
            if (liveOrderObj.getPositionStatus() != 1 && liveOrderObj.getPositionStatus() != 2 || !bl && this.tradesToClose.contains((Object)liveOrderObj) || !bl && this.tradesToCloseOnClose.contains((Object)liveOrderObj)) continue;
            if (n2 == n) {
                return liveOrderObj;
            }
            ++n2;
        }
        throw new IllegalArgumentException("Trade index is out of range!");
    }

    private void openInitialSLOrder(LiveOrderObj liveOrderObj, double d, boolean bl) {
        try {
            if (this.useInitialSLPT && liveOrderObj.getSL() != 0.0 && liveOrderObj.getSL() != -9.9999999E7) {
                byte by = liveOrderObj.getDirection() > 0 ? (byte)102 : 100;
                LiveOrderObj liveOrderObj2 = this.createLiveOrder(liveOrderObj.getTrader(), liveOrderObj.getInstrumentInfo(), by, liveOrderObj.getSymbol());
                double d2 = this.computeRealSLFromOrder(liveOrderObj, liveOrderObj.getSL(), bl);
                liveOrderObj2.setOpenPrice(d2);
                liveOrderObj2.setComment("InitialSL");
                this.orderOpen(liveOrderObj.getTrader().getStrategy(), liveOrderObj2, 0, null);
            }
        }
        catch (Exception exception) {
            Log.error("Opening InitialSL order failed", (Throwable)exception);
        }
    }

    private double computeRealSLFromOrder(LiveOrderObj liveOrderObj, double d, boolean bl) {
        int n = liveOrderObj.isLong() ? -1 : 1;
        double d2 = 0.0;
        d2 = bl ? (n > 0 ? liveOrderObj.getOpenPrice() + d : liveOrderObj.getOpenPrice() - d) : d;
        return d2;
    }

    private double computeRealPTFromOrder(LiveOrderObj liveOrderObj, double d, boolean bl) {
        int n = liveOrderObj.isLong() ? -1 : 1;
        double d2 = 0.0;
        d2 = bl ? (n > 0 ? liveOrderObj.getOpenPrice() - d : liveOrderObj.getOpenPrice() + d) : d;
        return d2;
    }

    private void openInitialPTOrder(LiveOrderObj liveOrderObj, double d, boolean bl) {
        try {
            if (this.useInitialSLPT && liveOrderObj.getPT() != 0.0 && liveOrderObj.getPT() != -9.9999999E7) {
                byte by = liveOrderObj.getDirection() > 0 ? (byte)103 : 101;
                LiveOrderObj liveOrderObj2 = this.createLiveOrder(liveOrderObj.getTrader(), liveOrderObj.getInstrumentInfo(), by, liveOrderObj.getSymbol());
                double d2 = this.computeRealPTFromOrder(liveOrderObj, liveOrderObj.getPT(), bl);
                liveOrderObj2.setOpenPrice(d2);
                liveOrderObj2.setComment("InitialPT");
                this.orderOpen(liveOrderObj.getTrader().getStrategy(), liveOrderObj2, 0, null);
            }
        }
        catch (Exception exception) {
            Log.error("Opening InitialPT order failed", (Throwable)exception);
        }
    }

    @Override
    public LiveOrderObj createLiveOrder(Trader trader, InstrumentInfo instrumentInfo, byte by, String string, double d) {
        d = this.fixTSStopPrice(instrumentInfo, by, d);
        return super.createLiveOrder(trader, instrumentInfo, by, string, d);
    }

    private double fixTSStopPrice(InstrumentInfo instrumentInfo, byte by, double d) {
        int n = 0;
        if (by == 5 || by == 7 || by == 100) {
            n = 1;
        } else if (by == 6 || by == 8 || by == 102) {
            n = -1;
        }
        if (n == 0) {
            return d;
        }
        if (instrumentInfo.tickStep == Math.pow(10.0, -instrumentInfo.decimals)) {
            return SQUtils.round((double)d, (int)instrumentInfo.decimals);
        }
        d = SQUtils.round((double)d, (int)instrumentInfo.decimals);
        double d2 = n == -1 ? Math.floor(d / instrumentInfo.tickStep) : Math.ceil(d / instrumentInfo.tickStep);
        d = d2 * instrumentInfo.tickStep;
        d = SQUtils.round((double)d, (int)instrumentInfo.decimals);
        return d;
    }

    @Override
    public boolean IsMarketOpen() {
        return true;
    }
}

