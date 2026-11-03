/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.AbstractTradingSimulator;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import com.strategyquant.tradinglib.strategy.MarketData;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;

public class Trader {
    private IExecutionEngine ee;
    private String name;
    private AbstractTradingSimulator tradingSimulator;
    private StrategyBase strategy;
    private SettingsMap settings;
    private MoneyManagementMethod moneyManagementMethod;
    private Order mmOrder;
    private RiskManagementMethod riskManagementMethod;
    private MarketData marketData;

    public Trader(String string, IExecutionEngine iExecutionEngine) {
        this.name = string;
        this.ee = iExecutionEngine;
        if (this.ee instanceof AbstractTradingSimulator) {
            this.tradingSimulator = (AbstractTradingSimulator)this.ee;
        }
    }

    public void setStrategy(StrategyBase strategyBase) {
        this.strategy = strategyBase;
    }

    public StrategyBase getStrategy() {
        return this.strategy;
    }

    public String getName() {
        return this.name;
    }

    public void initialize(MarketData marketData) {
        this.marketData = marketData;
        if (this.ee instanceof ITradingSimulator) {
            ((ITradingSimulator)this.ee).initialize(marketData);
        }
    }

    public void eventBarUpdated(int n) {
        if (this.tradingSimulator != null) {
            this.tradingSimulator.eventBarUpdated(n);
        }
    }

    public ILiveOrder Open(byte by, String string) throws TradingException {
        InstrumentInfo instrumentInfo;
        if (string.equals("Current")) {
            string = this.marketData.Chart((int)0).Symbol;
            instrumentInfo = this.marketData.Chart(0).getInstrumentInfo();
        } else {
            instrumentInfo = this.marketData.getInstrumentInfo(string);
        }
        return this.tradingSimulator.createLiveOrder(this, instrumentInfo, by, string);
    }

    public ILiveOrder Open(byte by, String string, double d) throws TradingException {
        InstrumentInfo instrumentInfo;
        if (string.equals("Current")) {
            string = this.marketData.Chart((int)0).Symbol;
            instrumentInfo = this.marketData.Chart(0).getInstrumentInfo();
        } else {
            instrumentInfo = this.marketData.getInstrumentInfo(string);
        }
        return this.tradingSimulator.createLiveOrder(this, instrumentInfo, by, string, d);
    }

    public ILiveOrder Buy(String string) throws TradingException {
        return this.Open((byte)1, string);
    }

    public ILiveOrder Sell(String string) throws TradingException {
        return this.Open((byte)2, string, 0.0);
    }

    public ILiveOrder BuyLimit(String string, double d) throws TradingException {
        return this.Open((byte)3, string, d);
    }

    public ILiveOrder SellLimit(String string, double d) throws TradingException {
        return this.Open((byte)1, string, d);
    }

    public ILiveOrder BuyStop(String string, double d) throws TradingException {
        return this.Open((byte)5, string, d);
    }

    public ILiveOrder SellStop(String string, double d) throws TradingException {
        return this.Open((byte)6, string, d);
    }

    public ILiveOrder BuyStopLimit(String string, double d) throws TradingException {
        return this.Open((byte)7, string, d);
    }

    public ILiveOrder SellStopLimit(String string, double d) throws TradingException {
        return this.Open((byte)8, string, d);
    }

    public ILiveOrder send(ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) throws TradingException {
        return this.send(iLiveOrder, by, (byte)0, n, iTradingEventListener);
    }

    public ILiveOrder send(ILiveOrder iLiveOrder, byte by, byte by2, int n, ITradingEventListener iTradingEventListener) throws TradingException {
        if (iLiveOrder.getWorkingStatus() == -20) {
            return iLiveOrder;
        }
        if (by == 1) {
            iLiveOrder.computeSizeIfMissing();
            return this.processOpen(iLiveOrder, by2, n, iTradingEventListener);
        }
        if (by == 3) {
            return this.processModify(iLiveOrder, by2, n, iTradingEventListener);
        }
        if (by == 2) {
            return this.processClose(iLiveOrder, by2, n, iTradingEventListener);
        }
        return iLiveOrder;
    }

    private ILiveOrder processClose(ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) throws TradingException {
        if (iLiveOrder.getWorkingStatus() == -10) {
            return iLiveOrder;
        }
        if (iLiveOrder.getWorkingStatus() == -20) {
            return iLiveOrder;
        }
        if (iLiveOrder.getPositionStatus() != 1 && iLiveOrder.getPositionStatus() != 2) {
            return iLiveOrder;
        }
        return this.ee.orderClose(this.strategy, iLiveOrder, by, n, iTradingEventListener);
    }

    private ILiveOrder processModify(ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) throws TradingException {
        if (iLiveOrder.getWorkingStatus() == -10) {
            return iLiveOrder;
        }
        if (!iLiveOrder.isModified()) {
            return ((LiveOrderObj)iLiveOrder).setError(4, "You cannot call Modify when you don't set new SL or PT !");
        }
        return this.ee.orderModify(this.strategy, iLiveOrder, n, iTradingEventListener);
    }

    private ILiveOrder processOpen(ILiveOrder iLiveOrder, byte by, int n, ITradingEventListener iTradingEventListener) throws TradingException {
        int n2 = 100;
        byte by2 = iLiveOrder.getOrderType();
        if (iLiveOrder.getSize() == 0.0 && by2 != 100 && by2 != 102 && by2 != 101 && by2 != 103) {
            return ((LiveOrderObj)iLiveOrder).setError(3, "Order has a zero size!");
        }
        if (this.ee.getOpenOrdersCount(false) > n2) {
            return ((LiveOrderObj)iLiveOrder).setError(7, String.format("Order refused - there are too many open orders, maximum number of open orders allowed is %d", n2));
        }
        if (iLiveOrder.getWorkingStatus() != -10) {
            return ((LiveOrderObj)iLiveOrder).setError(2, "You are using Send() on an order that was already placed or is no longer active!");
        }
        if (!this.getStrategy().isTradestationEngine() && !OrderTypes.isMarketOrder(iLiveOrder.getOrderType()) && iLiveOrder.getOpenPrice() < 0.0) {
            return ((LiveOrderObj)iLiveOrder).setError(3, "Pending order doesn't have price filled!");
        }
        if (iLiveOrder.isRefused()) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)iLiveOrder;
            liveOrderObj.setWorkingStatus((byte)-40);
            this.ee.reuseOpenOrder(liveOrderObj);
            return liveOrderObj;
        }
        return this.ee.orderOpen(this.strategy, iLiveOrder, n, iTradingEventListener);
    }

    private void checkRiskManagement(ILiveOrder iLiveOrder) {
        if (this.riskManagementMethod != null) {
            this.riskManagementMethod.verifyOrder(this, iLiveOrder);
        }
    }

    public ILiveOrder refuseOrder(ILiveOrder iLiveOrder, String string) {
        if (iLiveOrder.getWorkingStatus() == -10) {
            return ((LiveOrderObj)iLiveOrder).setError(5, string);
        }
        return iLiveOrder;
    }

    public OrdersList getHistoryOrders() {
        return this.ee.getHistoryOrders();
    }

    public Long2FloatRBTreeMap getWorstDailyEquity() {
        return this.ee.getWorstDailyEquity();
    }

    public int getHistoryOrdersCount() {
        return this.ee.getHistoryOrdersCount();
    }

    public Order getHistoryOrder(int n) {
        return this.ee.getHistoryOrder(n);
    }

    public double getAccountBalance() {
        return this.ee.getAccountBalance();
    }

    public double getAccountEquity() {
        return this.ee.getAccountEquity();
    }

    public double getInitialBalance() {
        return this.ee.getInitialBalance();
    }

    public String getStrategyName() {
        return this.strategy.getStrategyName();
    }

    public String getSetupName() {
        return this.strategy.getSetupName();
    }

    public void setSettings(SettingsMap settingsMap) {
        this.settings = settingsMap;
        if (settingsMap.containsKey("MoneyManagement.Method")) {
            this.moneyManagementMethod = (MoneyManagementMethod)settingsMap.get("MoneyManagement.Method");
            this.riskManagementMethod = (RiskManagementMethod)settingsMap.get("RiskManagement");
        }
    }

    public MoneyManagementMethod getMoneyManagementMethod() {
        return this.moneyManagementMethod;
    }

    public int getOpenOrdersCount(boolean bl) {
        return this.ee.getOpenOrdersCount(bl);
    }

    public ILiveOrder getOpenOrder(int n, boolean bl) {
        return this.ee.getOpenOrder(n, bl);
    }

    public void destroy() {
        if (this.ee != null && this.ee instanceof ITradingSimulator) {
            ((ITradingSimulator)this.ee).destroy();
            this.ee = null;
        }
    }

    public boolean fillAtRealAskBidPrice() {
        return this.ee.fillAtRealAskBidPrice();
    }

    public int getAmbiguousTrades() {
        return this.ee.getAmbiguousTrades();
    }

    public void evaluateActionListeners(int n, StrategyBase strategyBase) throws TradingException {
        this.ee.evaluateActionListeners(n, strategyBase);
    }

    public boolean supportsDuplicateTrades() {
        return this.ee.supportsDuplicateTrades();
    }

    public boolean IsMarketOpen() {
        return this.ee.IsMarketOpen();
    }
}

