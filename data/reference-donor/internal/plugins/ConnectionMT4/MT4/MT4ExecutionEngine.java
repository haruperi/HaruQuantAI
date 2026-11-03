/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.tradinglib.ILiveOrder
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.event.ITradingEvent
 *  com.strategyquant.tradinglib.event.ITradingEventListener
 *  com.strategyquant.tradinglib.event.TradingEventObj
 *  com.strategyquant.tradinglib.event.TradingEventsArray
 *  com.strategyquant.tradinglib.execution.IExecutionEngine
 *  com.strategyquant.tradinglib.strategy.LiveOrderObj
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.MT4;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge;
import com.strategyquant.plugin.Connection.impl.MT4.MT4Connection;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.event.ITradingEvent;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import com.strategyquant.tradinglib.event.TradingEventObj;
import com.strategyquant.tradinglib.event.TradingEventsArray;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT4ExecutionEngine
implements IExecutionEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"MT4ExecutionEngine");
    private MT4Connection mt4Connection;
    private MT4Bridge mt4Bridge;
    private TradingEventsArray tradingEventsArray = new TradingEventsArray();

    public MT4ExecutionEngine(MT4Connection mt4Connection, MT4Bridge mt4Bridge) {
        this.mt4Connection = mt4Connection;
        this.mt4Bridge = mt4Bridge;
    }

    public void initialize() {
    }

    public ILiveOrder orderOpen(StrategyBase strategy, ILiveOrder order, int syncType, ITradingEventListener orderEventListener) {
        LiveOrderObj orderObj = (LiveOrderObj)order;
        orderObj.setWorkingStatus((byte)-20);
        if (syncType == 0) {
            orderObj.setWorkingStatus((byte)-30);
            this.sendEvent(strategy, orderEventListener, 1, order);
            return order;
        }
        this.sendEvent(strategy, orderEventListener, 2, order);
        return order;
    }

    public ILiveOrder orderClose(StrategyBase strategy, ILiveOrder order, byte additionalFlag, int syncType, ITradingEventListener orderEventListener) {
        return null;
    }

    public ILiveOrder orderModify(StrategyBase strategy, ILiveOrder order, int syncType, ITradingEventListener orderEventListener) {
        return null;
    }

    private void sendEvent(StrategyBase strategy, ITradingEventListener orderEventListener, int eventType, ILiveOrder order) {
        TradingEventObj event = this.tradingEventsArray.getAvailableEventObject();
        event.setEventType(eventType);
        event.setOrder(order);
        try {
            strategy.OnEvent((ITradingEvent)event);
        }
        catch (Exception e) {
            Log.error("Exception during strategy.onEvent()", (Throwable)e);
        }
        if (orderEventListener != null) {
            try {
                orderEventListener.OnTradingEvent((ITradingEvent)event);
            }
            catch (Exception e) {
                Log.error("Exception during OrderEventListener.onTradingEvent()", (Throwable)e);
            }
        }
        event.releaseEvent();
    }

    public int getOpenOrdersCount(boolean includeClosingTrades) {
        return 0;
    }

    public double getAccountBalance() {
        return 0.0;
    }

    public double getAccountEquity() {
        return 0.0;
    }

    public double getTotalPL() {
        return 0.0;
    }

    public String getMainCurrency() {
        return "USD";
    }

    public OrdersList getHistoryOrders() {
        return null;
    }

    public ILiveOrder getOpenOrder(int index, boolean includeClosingTrades) {
        return null;
    }

    public double getInitialBalance() {
        return 0.0;
    }

    public TickEvent getTickData() {
        return null;
    }

    public int getHistoryOrdersCount() {
        return 0;
    }

    public Order getHistoryOrder(int index) {
        return null;
    }

    public boolean fillAtRealAskBidPrice() {
        return false;
    }

    public Long2FloatRBTreeMap getWorstDailyEquity() {
        return null;
    }

    public int getAmbiguousTrades() {
        return 0;
    }

    public void reuseOpenOrder(LiveOrderObj orderObj) {
    }

    public void evaluateActionListeners(int updateEventType, StrategyBase strategyBase) {
    }

    public boolean supportsDuplicateTrades() {
        return true;
    }

    public boolean IsMarketOpen() {
        return true;
    }
}

