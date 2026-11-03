/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.log.StockpickerLog;
import com.strategyquant.tradinglib.engine.stockpicker.constants.PickerEodTypes;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import com.strategyquant.tradinglib.swap.SwapCalculator;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockBroker {
    public static final Logger Log = LoggerFactory.getLogger(StockBroker.class);
    private int orderId = 1;
    private ObjectArrayList<LiveOrderObj> liveOrders;
    private OrdersList closedTrades;
    private long lastDayStartTime = -1L;
    private long nextDayStartTime = -1L;
    private double worstDailyEquity;
    private Long2FloatRBTreeMap dailyEquityValues;
    private double peakEquity;
    private double maxDailyDrawdown;
    private double maxDailyPctDrawdown;
    private Long2FloatRBTreeMap maxDailyDDValues;
    private Long2FloatRBTreeMap maxDailyDDPctValues;
    public double maxOpenDrawdown = 0.0;
    public double maxOpenDrawdownPct = 0.0;
    private ObjectArrayList<String> tradedSymbols = new ObjectArrayList();
    private double initialCapital;
    private double accountBalance;
    private double accountEquity;
    private Trader dummyTradeController;
    private TickEvent currentTick = new TickEvent();
    StockpickerLog verboseLog;
    protected int ambiguousTrades;
    private double prevClosePrice;
    private double slippage;
    private CommissionsMethod commission;
    private SwapMethod swap;
    private double LimitOver = 0.0;
    private boolean AllowBetterLimitFill = false;
    public ObjectArrayList<LiveOrderObj> statsOpenedPositions;
    public ObjectArrayList<LiveOrderObj> statsClosedPositions;
    public ObjectArrayList<LiveOrderObj> statsCanceledOrders;
    public static int TickBeforeBarOpen = 1;
    public static int TickOnBarOpen = 2;
    public static int TickOnBarClose = 3;

    public StockBroker(Trader trader) {
        this(trader, null);
    }

    public StockBroker(Trader trader, StockpickerLog stockpickerLog) {
        this.dummyTradeController = trader;
        this.verboseLog = stockpickerLog;
        this.liveOrders = new ObjectArrayList();
        this.closedTrades = new OrdersList("ClosedTrades");
        this.dailyEquityValues = new Long2FloatRBTreeMap();
        this.maxDailyDDValues = new Long2FloatRBTreeMap();
        this.maxDailyDDPctValues = new Long2FloatRBTreeMap();
        this.statsOpenedPositions = new ObjectArrayList();
        this.statsClosedPositions = new ObjectArrayList();
        this.statsCanceledOrders = new ObjectArrayList();
    }

    public void resetStats() {
        this.statsOpenedPositions.clear();
        this.statsClosedPositions.clear();
        this.statsCanceledOrders.clear();
    }

    public int openPosCount(int n) {
        int n2 = 0;
        for (int i = 0; i < this.liveOrders.size(); ++i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (n == 1 && OrderTypes.isLongOrder(liveOrderObj.getOrderType())) {
                ++n2;
            }
            if (n != -1 || !OrderTypes.isShortOrder(liveOrderObj.getOrderType())) continue;
            ++n2;
        }
        return n2;
    }

    public int openPosCount(boolean bl) {
        int n = 0;
        for (int i = 0; i < this.liveOrders.size(); ++i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (!bl && liveOrderObj.getPositionStatus() == 1) {
                ++n;
            }
            if (!bl || liveOrderObj.getPositionStatus() == 1) continue;
            ++n;
        }
        return n;
    }

    public double getAccountBalance() {
        return this.accountBalance;
    }

    public double getAccountEquity() {
        return this.accountEquity;
    }

    public void printOpenTrades(StringBuilder stringBuilder, boolean bl) {
        for (int i = 0; i < this.liveOrders.size(); ++i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (!bl && liveOrderObj.getPositionStatus() == 1) {
                stringBuilder.append(liveOrderObj.getSymbol());
                stringBuilder.append(", ");
            }
            if (!bl || liveOrderObj.getPositionStatus() == 1) continue;
            stringBuilder.append(liveOrderObj.getSymbol());
            stringBuilder.append(", ");
        }
    }

    public String printOpenTrades(boolean bl) {
        StringBuilder stringBuilder = new StringBuilder();
        this.printOpenTrades(stringBuilder, bl);
        return stringBuilder.toString();
    }

    public ObjectArrayList<LiveOrderObj> getOpenPositions() {
        return this.liveOrders;
    }

    public LiveOrderObj open(byte by, String string, double d, double d2, double d3, double d4, int n, int n2, int n3, byte by2, boolean bl, boolean bl2) throws TradingException {
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string, (boolean)true);
        InstrumentInfo instrumentInfo = dataInfo.symbolInfo;
        LiveOrderObj liveOrderObj = new LiveOrderObj(this.dummyTradeController, instrumentInfo, by, string);
        liveOrderObj.setTickData(this.currentTick.getAsk(), this.currentTick.getBid());
        liveOrderObj.setSize(d);
        liveOrderObj.setOpenTime(this.currentTick.getTime());
        liveOrderObj.setOriginalOpenTime(liveOrderObj.getOpenTime());
        if (OrderTypes.isMarketOrder(by)) {
            liveOrderObj.setOpenPrice(liveOrderObj.getPriceByType(by, this.currentTick.getBid(), this.currentTick.getAsk(), this.slippage));
            liveOrderObj.setOrderStatus((byte)1);
            liveOrderObj.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj));
            this.statsOpenedPositions.add((Object)liveOrderObj);
        } else {
            liveOrderObj.setOpenPrice(d2);
            liveOrderObj.setOrderStatus((byte)2);
            liveOrderObj.setBarsValid(n2);
        }
        liveOrderObj.setOriginalOpenPrice(liveOrderObj.getOpenPrice());
        liveOrderObj.setLastAction((byte)1);
        liveOrderObj.setError(0, null);
        liveOrderObj.setOrderId(this.orderId++);
        liveOrderObj.setSL(d3);
        liveOrderObj.setPT(d4);
        liveOrderObj.setSLPTValidFrom(n);
        liveOrderObj.setExitAfterBars(n3);
        liveOrderObj.setEOD(by2);
        liveOrderObj.setWorkingStatus((byte)-30);
        if (!this.checkOrder(liveOrderObj)) {
            StringBuilder stringBuilder = new StringBuilder("Order refused with id: ");
            stringBuilder.append(liveOrderObj.getOrderId());
            stringBuilder.append(", ");
            this.orderToString(stringBuilder, liveOrderObj);
            stringBuilder.append(". Reason: ");
            stringBuilder.append(liveOrderObj.getErrorMessage());
            this.VerboseLog(stringBuilder.toString());
            return null;
        }
        this.liveOrders.add((Object)liveOrderObj);
        StringBuilder stringBuilder = new StringBuilder("Order placed with id: ");
        stringBuilder.append(liveOrderObj.getOrderId());
        stringBuilder.append(", ");
        this.orderToString(stringBuilder, liveOrderObj);
        this.VerboseLog(stringBuilder.toString());
        return liveOrderObj;
    }

    public void orderToString(StringBuilder stringBuilder, LiveOrderObj liveOrderObj) {
        stringBuilder.append(liveOrderObj.getSymbol());
        stringBuilder.append(", Type=");
        stringBuilder.append(OrderTypes.toString(liveOrderObj.getOrderType()));
        stringBuilder.append(", Size=");
        stringBuilder.append(SQUtils.d2((double)liveOrderObj.getSize()));
        stringBuilder.append(", OpenTime=");
        stringBuilder.append(SQTime.toDateMinuteString((long)liveOrderObj.getOpenTime()));
        stringBuilder.append(", OpenPrice=");
        stringBuilder.append(SQUtils.d2((double)liveOrderObj.getOpenPrice()));
        stringBuilder.append(", CloseTime=");
        stringBuilder.append(liveOrderObj.getCloseTime() > 0L ? SQTime.toDateMinuteString((long)liveOrderObj.getCloseTime()) : "");
        stringBuilder.append(", ClosePrice=");
        stringBuilder.append(liveOrderObj.getClosePrice() > 0.0 ? SQUtils.d2((double)liveOrderObj.getClosePrice()) : "");
        stringBuilder.append("[Exits: ExitEOD=");
        stringBuilder.append(PickerEodTypes.toString(liveOrderObj.getEOD()));
        stringBuilder.append(", BarsValid=");
        stringBuilder.append(liveOrderObj.getBarsValid());
        stringBuilder.append(", ExitAfterBars=");
        stringBuilder.append(liveOrderObj.getExitAfterBars());
        stringBuilder.append(", SL=");
        stringBuilder.append(liveOrderObj.getSL() != -9.9999999E7 ? SQUtils.d2((double)liveOrderObj.getSL()) : "");
        stringBuilder.append(", PT=");
        stringBuilder.append(liveOrderObj.getSL() != -9.9999999E7 ? SQUtils.d2((double)liveOrderObj.getPT()) : "");
        stringBuilder.append("],");
    }

    public String orderToString(LiveOrderObj liveOrderObj) {
        StringBuilder stringBuilder = new StringBuilder("Symbol=");
        this.orderToString(stringBuilder, liveOrderObj);
        return stringBuilder.toString();
    }

    private boolean checkOrder(LiveOrderObj liveOrderObj) {
        double d;
        double d2;
        int n = liveOrderObj.getSymbolHash();
        byte by = liveOrderObj.getOrderType();
        double d3 = d2 = LiveOrderObj.getPriceByType(by, this.currentTick.getBid(), this.currentTick.getAsk());
        if (liveOrderObj.isPendingOrder()) {
            d = liveOrderObj.getOpenPrice();
            if (!this.checkPriceLevelCorrectness(by, d3, d)) {
                if ((by == 3 || by == 4) && this.AllowBetterLimitFill) {
                    d = d2;
                } else {
                    liveOrderObj.setError(6, "Incorrect price level. Open price: " + d3 + ", price level: " + d);
                    return false;
                }
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

    private boolean checkPriceLevelDistance(int n, double d, double d2) {
        return true;
    }

    public void onStart(double d, double d2, CommissionsMethod commissionsMethod, SwapMethod swapMethod, double d3, boolean bl) {
        this.initialCapital = d;
        this.peakEquity = this.accountEquity = (this.accountBalance = d);
        this.slippage = d2;
        this.commission = commissionsMethod;
        this.swap = swapMethod;
        this.LimitOver = d3;
        this.AllowBetterLimitFill = bl;
        this.liveOrders.clear();
        this.closedTrades.clear();
    }

    public void onTick(TickEvent tickEvent, double d, double d2, double d3, byte by, byte by2, int n) throws TradingException {
        this.currentTick.set(tickEvent);
        this.prevClosePrice = d;
        this.updateLastPrice(this.currentTick, this.currentTick.getSymbolHash());
        this.updateDailyEquity();
        if (this.currentTick.isBarOpen() && (by2 == 15 || by2 == 5)) {
            if (n == TickOnBarOpen) {
                this.increaseBarsInTrade(this.currentTick.getSymbolHash());
            }
            this.checkBarsValid(this.currentTick, this.currentTick.getSymbolHash());
            this.checkExitAfterBars(this.currentTick, this.currentTick.getSymbolHash(), by, by2);
        }
        if (d2 > 0.0 && d3 > 0.0) {
            this.checkStopLimitOrders(this.currentTick, this.currentTick.getSymbolHash(), d2, d3);
            this.checkSLPT(this.currentTick, this.currentTick.getSymbolHash(), d2, d3);
        }
        if (this.currentTick.isBarClose() && by2 == 10) {
            this.increaseBarsInTrade(this.currentTick.getSymbolHash());
            this.checkBarsValid(this.currentTick, this.currentTick.getSymbolHash());
            this.checkExitAfterBars(this.currentTick, this.currentTick.getSymbolHash(), by, by2);
        }
        if (this.currentTick.isBarClose()) {
            this.checkEOD(this.currentTick, this.currentTick.getSymbolHash(), by, by2);
        }
        this.updateMAE_MFE(this.currentTick.getSymbolHash(), d2, d3);
    }

    private void updateLastPrice(TickEvent tickEvent, int n) {
        int n2 = this.liveOrders.size();
        for (int i = n2 - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n) continue;
            liveOrderObj.lastPrice = liveOrderObj.isLong() ? tickEvent.getAsk() : tickEvent.getBid();
            liveOrderObj.setTickData(this.currentTick.getAsk(), this.currentTick.getBid());
        }
    }

    private void checkExitAfterBars(TickEvent tickEvent, int n, byte by, byte by2) {
        int n2 = this.liveOrders.size();
        for (int i = n2 - 1; i >= 0; --i) {
            int n3;
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.getPositionStatus() != 1 || (n3 = liveOrderObj.getExitAfterBars()) <= 0) continue;
            if (by == by2 && (OrderTypes.isMarketOrder(liveOrderObj.getOriginalOrderType()) || tickEvent.getTime() == liveOrderObj.getOriginalOpenTime())) {
                ++n3;
            }
            if (liveOrderObj.getBarsInTrade() < n3) continue;
            this.closeOrder(liveOrderObj, -1.0, (byte)19);
        }
    }

    private void checkEOD(TickEvent tickEvent, int n, byte by, byte by2) {
        int n2 = this.liveOrders.size();
        for (int i = n2 - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.getPositionStatus() != 1 || by == by2 && tickEvent.getTime() == liveOrderObj.getOpenTime() && (OrderTypes.isMarketOrder(liveOrderObj.getOriginalOrderType()) || tickEvent.getTime() == liveOrderObj.getOriginalOpenTime()) || liveOrderObj.getEOD() != 5) continue;
            this.closeOrder(liveOrderObj, -1.0, (byte)5);
        }
    }

    public void setCurrentTick(TickEvent tickEvent) {
        this.currentTick.set(tickEvent);
    }

    private void updateDayStartTimes(long l) {
        this.lastDayStartTime = SQTime.getDateInMs((long)l);
        this.nextDayStartTime = this.lastDayStartTime + 86400000L;
    }

    private void updateDailyEquity() {
        long l = this.currentTick.getTime();
        if (this.lastDayStartTime == -1L) {
            this.updateDayStartTimes(l);
        } else if (l >= this.nextDayStartTime) {
            this.dailyEquityValues.addTo(this.lastDayStartTime, (float)this.worstDailyEquity);
            this.maxDailyDDValues.addTo(this.lastDayStartTime, (float)this.maxDailyDrawdown);
            this.maxDailyDDPctValues.addTo(this.lastDayStartTime, (float)this.maxDailyPctDrawdown);
            this.maxOpenDrawdown = Math.min(this.maxDailyDrawdown, this.maxOpenDrawdown);
            this.maxOpenDrawdownPct = Math.min(this.maxDailyPctDrawdown, this.maxOpenDrawdownPct);
            this.updateDayStartTimes(l);
        } else {
            return;
        }
        this.worstDailyEquity = this.liveOrders.size() > 0 ? 3.4028234663852886E38 : this.accountBalance - this.initialCapital;
        this.maxDailyDrawdown = 3.4028234663852886E38;
        this.maxDailyPctDrawdown = 3.4028234663852886E38;
    }

    private void updateMAE_MFE(int n, double d, double d2) {
        double d3 = this.accountBalance;
        for (int i = 0; i < this.liveOrders.size(); ++i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.isPendingOrder() || liveOrderObj.isClosedOrder()) continue;
            if (liveOrderObj.getSymbolHash() == n && d > 0.0 && d2 > 0.0) {
                double d4;
                double d5;
                if (liveOrderObj.isLong()) {
                    d5 = (d - liveOrderObj.getOpenPrice()) / liveOrderObj.getInstrumentInfo().tickSize;
                    d4 = (liveOrderObj.getOpenPrice() - d2) / liveOrderObj.getInstrumentInfo().tickSize;
                } else {
                    d5 = (liveOrderObj.getOpenPrice() - d2) / liveOrderObj.getInstrumentInfo().tickSize;
                    d4 = (d - liveOrderObj.getOpenPrice()) / liveOrderObj.getInstrumentInfo().tickSize;
                }
                if (liveOrderObj.getMFE() == 0.0f || d5 > (double)liveOrderObj.getMFE()) {
                    liveOrderObj.setMFE((float)d5);
                }
                if (liveOrderObj.getMAE() == 0.0f || d4 > (double)liveOrderObj.getMAE()) {
                    liveOrderObj.setMAE((float)d4);
                }
            }
            d3 += liveOrderObj.getPL() - liveOrderObj.getCommSwap();
        }
        this.accountEquity = d3;
        this.worstDailyEquity = Math.min(d3 - this.initialCapital, this.worstDailyEquity);
        double d6 = StockBroker.specialSubtraction(this.peakEquity, d3);
        double d7 = this.getPercentageDD(d6, this.peakEquity);
        this.maxDailyDrawdown = Math.min(d6, this.maxDailyDrawdown);
        this.maxDailyPctDrawdown = Math.min(d7, this.maxDailyPctDrawdown);
        if (this.accountEquity > this.peakEquity) {
            this.peakEquity = this.accountEquity;
        }
    }

    private void checkSLPT(TickEvent tickEvent, int n, double d, double d2) {
        boolean bl = false;
        int n2 = this.liveOrders.size();
        for (int i = n2 - 1; i >= 0; --i) {
            byte by;
            double d3;
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.isPendingOrder()) continue;
            double d4 = liveOrderObj.getSL();
            double d5 = liveOrderObj.getPT();
            if (d4 == 0.0 && d5 == 0.0 || liveOrderObj.getSLPTValidFrom() > 0 && tickEvent.getTime() == liveOrderObj.getOpenTime()) continue;
            if (d4 > d2 && d4 < d && d5 > d2 && d5 < d) {
                liveOrderObj.setAmbiguous();
                ++this.ambiguousTrades;
            }
            if (d4 > 0.0 && (d3 = this.priceLevelReached(tickEvent, d, d2, n, by = liveOrderObj.getOrderTypeFromSLPT(-1), d4, liveOrderObj.getInstrumentInfo().tickSize)) > 0.0) {
                d3 = this.fixByHighLow(d3, d, d2);
                this.closeOrder(liveOrderObj, this.getRealisticSLPTFilledPrice(d3, d4, by), (byte)2);
                continue;
            }
            if (!(d5 > 0.0) || !((d3 = this.priceLevelReached(tickEvent, d, d2, n, by = liveOrderObj.getOrderTypeFromSLPT(1), d5, liveOrderObj.getInstrumentInfo().tickSize)) > 0.0)) continue;
            d3 = this.fixByHighLow(d3, d, d2);
            this.closeOrder(liveOrderObj, this.getRealisticSLPTFilledPrice(d3, d5, by), (byte)3);
        }
    }

    protected double getRealisticSLPTFilledPrice(double d, double d2, int n) {
        double d3;
        if (this.currentTick.isBarOpen() && this.prevClosePrice > 0.0 && (d3 = this.currentTick.getBid()) != this.prevClosePrice) {
            if (n == 5 || n == 6) {
                Log.debug("GAP detected - prev Close:{}, new Open: {}, realistic fill set", (Object)this.prevClosePrice, (Object)d3);
                return LiveOrderObj.getPriceByType(n, this.currentTick.getBid(), this.currentTick.getAsk());
            }
            if (n == 3 || n == 4) {
                Log.debug("GAP detected for Limit - prev Close:{}, new Open: {}, realistic fill set", (Object)this.prevClosePrice, (Object)d3);
                double d4 = LiveOrderObj.getPriceByType(n, this.currentTick.getBid(), this.currentTick.getAsk());
                double d5 = this.getSLPTFilledPrice(d, d2);
                if (n == 3) {
                    return Math.min(d4, d5);
                }
                if (n == 4) {
                    return Math.max(d4, d5);
                }
            }
        }
        return this.getSLPTFilledPrice(d, d2);
    }

    private double getSLPTFilledPrice(double d, double d2) {
        return d;
    }

    public void onClose() {
        int n = this.liveOrders.size();
        for (int i = n - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            this.closeOrder(liveOrderObj, liveOrderObj.lastPrice, (byte)4);
        }
    }

    public OrdersList getHistoryOrders() {
        return this.closedTrades;
    }

    public void close(String string, byte by, byte by2) {
        int n = this.liveOrders.size();
        for (int i = n - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (by == 1 && !OrderTypes.isLongOrder(liveOrderObj.getOrderType()) || by == -1 && !OrderTypes.isShortOrder(liveOrderObj.getOrderType()) || !liveOrderObj.getSymbol().equals(string)) continue;
            this.closeOrder(liveOrderObj, -1.0, by2);
            break;
        }
    }

    private void closeOrder(LiveOrderObj liveOrderObj, double d, byte by) {
        double d2 = d >= 0.0 ? liveOrderObj.getPriceByType(OrderTypes.getOppositeType(liveOrderObj.getOrderType()), d, d, by == 3 ? 0.0 : this.slippage) : liveOrderObj.getPriceByType(OrderTypes.getOppositeType(liveOrderObj.getOrderType()), this.currentTick.getBid(), this.currentTick.getAsk(), by == 3 ? 0.0 : this.slippage);
        liveOrderObj.setCloseTime(this.currentTick.getTime());
        liveOrderObj.setClosePrice(d2);
        liveOrderObj.setLastAction((byte)2);
        liveOrderObj.setWorkingStatus((byte)-30);
        liveOrderObj.setOrderStatus((byte)3);
        liveOrderObj.setCloseType(by);
        if (!liveOrderObj.isPendingOrder()) {
            liveOrderObj.setCommSwap(this.getCommissionSwap(liveOrderObj));
        }
        this.accountBalance += liveOrderObj.getPL();
        StringBuilder stringBuilder = new StringBuilder("Order closed [");
        stringBuilder.append(OrderCloseTypes.toString(by));
        stringBuilder.append("] with id: ");
        stringBuilder.append(liveOrderObj.getOrderId());
        stringBuilder.append(", ");
        this.orderToString(stringBuilder, liveOrderObj);
        this.VerboseLog(stringBuilder.toString());
        this.closedTrades.add(liveOrderObj);
        this.liveOrders.remove((Object)liveOrderObj);
        if (liveOrderObj.isPendingOrder()) {
            this.statsCanceledOrders.add((Object)liveOrderObj);
        } else {
            this.statsClosedPositions.add((Object)liveOrderObj);
        }
        this.regTradedSymbol(liveOrderObj.getSymbol());
    }

    private void checkBarsValid(TickEvent tickEvent, int n) throws TradingException {
        int n2 = this.liveOrders.size();
        for (int i = n2 - 1; i >= 0; --i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n || !liveOrderObj.isPendingOrder() || liveOrderObj.isClosedOrder() || liveOrderObj.getBarsValid() <= 0 || liveOrderObj.getBarsInTrade() < liveOrderObj.getBarsValid()) continue;
            this.closeOrder(liveOrderObj, -1.0, (byte)6);
        }
    }

    protected boolean checkPriceLevelCorrectness(int n, double d, double d2) {
        return !(n == 5 ? d >= d2 : (n == 6 ? d <= d2 : (n == 3 ? d <= d2 : n == 4 && d >= d2)));
    }

    protected void checkStopLimitOrders(TickEvent tickEvent, int n, double d, double d2) {
        for (int i = 0; i < this.liveOrders.size(); ++i) {
            double d3;
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n || liveOrderObj.isMarketOrder() || !((d3 = this.priceLevelReached(tickEvent, d, d2, n, liveOrderObj.getOrderType(), liveOrderObj.getOpenPrice(), liveOrderObj.getInstrumentInfo().tickSize)) > 0.0)) continue;
            d3 = this.fixByHighLow(d3, d, d2);
            if (OrderTypes.isStopOrder(liveOrderObj.getOrderType()) || OrderTypes.isLimitOrder(liveOrderObj.getOrderType())) {
                liveOrderObj.setOpenPrice(liveOrderObj.getPriceByType(liveOrderObj.getOrderType(), d3, d3, this.slippage));
            } else {
                liveOrderObj.setOpenPrice(d3);
            }
            this.VerboseLog("Order filled with id " + liveOrderObj.getOrderId() + ", symbol=" + liveOrderObj.getSymbol() + " reached: " + SQUtils.d2((double)d3) + " at " + SQTime.toFullDateMinuteString((long)tickEvent.getTime()));
            liveOrderObj.setOpenTime(tickEvent.getTime());
            liveOrderObj.fillOrder(tickEvent);
            liveOrderObj.setLastAction((byte)1);
            liveOrderObj.setCommSwap(this.computeCommissionsOnOpen(liveOrderObj));
            this.statsOpenedPositions.add((Object)liveOrderObj);
        }
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

    protected double priceLevelReached(TickEvent tickEvent, double d, double d2, int n, int n2, double d3, double d4) {
        if (this.currentTick.getTime() == -1L) {
            return 0.0;
        }
        if (n2 == 6) {
            if (d2 <= d3) {
                if (tickEvent.isBarOpen() && this.currentTick.getBid() <= d3) {
                    return this.currentTick.getBid();
                }
                return d3;
            }
        } else if (n2 == 5) {
            if (d >= d3) {
                if (tickEvent.isBarOpen() && this.currentTick.getAsk() >= d3) {
                    return this.currentTick.getAsk();
                }
                return d3;
            }
        } else if (n2 == 4) {
            if (d >= d3 * (1.0 + this.LimitOver / 100.0)) {
                if (tickEvent.isBarOpen() && this.currentTick.getBid() >= d3) {
                    return this.currentTick.getBid();
                }
                return d3;
            }
        } else if (n2 == 3 && d2 <= d3 * (1.0 - this.LimitOver / 100.0)) {
            if (tickEvent.isBarOpen() && this.currentTick.getAsk() <= d3) {
                return this.currentTick.getAsk();
            }
            return d3;
        }
        return 0.0;
    }

    private void increaseBarsInTrade(int n) {
        for (int i = 0; i < this.liveOrders.size(); ++i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)this.liveOrders.get(i);
            if (liveOrderObj.getSymbolHash() != n) continue;
            liveOrderObj.increaseBarsInTrade();
        }
    }

    private void regTradedSymbol(String string) {
        if (!this.tradedSymbols.contains((Object)string)) {
            this.tradedSymbols.add((Object)string);
        }
    }

    public ObjectArrayList<String> getTradedSymbols() {
        return this.tradedSymbols;
    }

    public void VerboseLog(String string) {
        if (this.verboseLog == null) {
            Log.debug(string);
        } else {
            this.verboseLog.print(string);
        }
    }

    protected double computeCommissionsOnOpen(LiveOrderObj liveOrderObj) {
        if (this.commission != null) {
            try {
                return -this.commission.computeCommissionsOnOpen(liveOrderObj, liveOrderObj.getInstrumentInfo().tickSize, liveOrderObj.getInstrumentInfo().pointValue);
            }
            catch (Exception exception) {
                Log.error("Exception computing commissions", (Throwable)exception);
            }
        }
        return 0.0;
    }

    private double getCommissionSwap(LiveOrderObj liveOrderObj) {
        double d = liveOrderObj.getCommSwap();
        if (this.commission != null) {
            try {
                d -= this.commission.computeCommissionsOnClose(liveOrderObj, liveOrderObj.getInstrumentInfo().tickSize, liveOrderObj.getInstrumentInfo().pointValue);
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

    public Long2FloatRBTreeMap getWorstDailyEquity() {
        return this.dailyEquityValues;
    }

    public Long2FloatRBTreeMap getMaxDailyDDValues() {
        return this.maxDailyDDValues;
    }

    public Long2FloatRBTreeMap getMaxDailyDDPctValues() {
        return this.maxDailyDDPctValues;
    }

    private static double specialSubtraction(double d, double d2) {
        double d3 = d - d2;
        if (d3 < 0.0) {
            d3 = 0.0;
        }
        return -1.0 * d3;
    }

    private double getPercentageDD(double d, double d2) {
        if (d2 <= 0.0 || d > d2) {
            return -1.0;
        }
        return d / (d2 / 100.0);
    }

    public double getMaxOpenDrawdown() {
        return this.maxOpenDrawdown;
    }

    public double getMaxOpenDrawdownPct() {
        return this.maxOpenDrawdownPct;
    }
}

