/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.IDataBuffer
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.tradinglib.ILiveOrder
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.connection.Connection
 *  com.strategyquant.tradinglib.connection.ConnectionManager
 *  com.strategyquant.tradinglib.connection.HistoryData
 *  com.strategyquant.tradinglib.connection.IDataFeed
 *  com.strategyquant.tradinglib.event.ITradingEventListener
 *  com.strategyquant.tradinglib.execution.IExecutionEngine
 *  com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin
 *  com.strategyquant.tradinglib.strategy.LiveOrderObj
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.Test;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.connection.HistoryData;
import com.strategyquant.tradinglib.connection.IDataFeed;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TestConnection
extends Connection
implements IDataFeed,
IExecutionEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"TestConnection");
    private HashMap<String, Integer> symbolsMap = new HashMap();

    public TestConnection(IConnectionPlugin connectionPlugin, ConnectionManager connectionManager, String connectionName, ValuesMap connParams) throws Exception {
        super(connectionManager, connectionName, connectionPlugin, connParams);
    }

    public void initializeEngines() {
        this.setDataFeed(this);
        this.setExecutionEngine(this);
    }

    public void connect() throws Exception {
    }

    public void disconnect() throws Exception {
    }

    public void registerSymbol(String symbol) {
        if (!this.checkSymbolIsSupported(symbol)) {
            return;
        }
        if (this.symbolsMap.containsKey(symbol)) {
            return;
        }
        this.symbolsMap.put(symbol, symbol.hashCode());
        this.startSendingTestData(symbol.hashCode());
    }

    public boolean checkSymbolIsSupported(String symbol) {
        String[] supportedSymbols = (String[])this.connParams.get("TestSymbols");
        for (int i = 0; i < supportedSymbols.length; ++i) {
            if (!supportedSymbols[i].equals(symbol)) continue;
            return true;
        }
        return false;
    }

    private void startSendingTestData(final int symbolHash) {
        final IDataBuffer dataBuffer = this.connectionManager.getDataBuffer();
        final TickEvent tick = new TickEvent();
        new Thread(this){
            private int count = 0;
            final /* synthetic */ TestConnection this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                while (true) {
                    ++this.count;
                    tick.setSymbolHash(symbolHash);
                    tick.setConnectionHash(this.this$0.getConnectionHash());
                    tick.setAsk((double)this.count);
                    tick.setBid((double)this.count);
                    tick.setIsSet(true);
                    dataBuffer.put(tick);
                    try {
                        Thread.sleep(500L);
                        continue;
                    }
                    catch (InterruptedException e) {
                        e.printStackTrace();
                        continue;
                    }
                    break;
                }
            }
        }.start();
    }

    public boolean isConnected() {
        return true;
    }

    public String getStatus() {
        return "Connected";
    }

    public HistoryData getHistoryData(ChartDef chart, int type, long fromTime, long toTime) {
        return null;
    }

    public void initialize() {
    }

    public ILiveOrder orderOpen(StrategyBase strategy, ILiveOrder order, int syncType, ITradingEventListener orderEventListener) {
        return null;
    }

    public ILiveOrder orderClose(StrategyBase strategy, ILiveOrder order, byte additionalFlag, int syncType, ITradingEventListener orderEventListener) {
        return null;
    }

    public ILiveOrder orderModify(StrategyBase strategy, ILiveOrder order, int syncType, ITradingEventListener orderEventListener) {
        return null;
    }

    public int getOpenOrdersCount(boolean includeClosingTrades) {
        return 0;
    }

    public double getAccountBalance() {
        return 0.0;
    }

    public double getTotalPL() {
        return 0.0;
    }

    public String getMainCurrency() {
        return null;
    }

    public OrdersList getHistoryOrders() {
        return null;
    }

    public ILiveOrder getOpenOrder(int index, boolean includeClosingTrades) {
        return null;
    }

    public double getAccountEquity() {
        return 0.0;
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

