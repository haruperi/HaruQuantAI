/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 */
package com.strategyquant.tradinglib.execution;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;

public interface IExecutionEngine {
    public void initialize();

    public ILiveOrder orderOpen(StrategyBase var1, ILiveOrder var2, int var3, ITradingEventListener var4) throws TradingException;

    public ILiveOrder orderClose(StrategyBase var1, ILiveOrder var2, byte var3, int var4, ITradingEventListener var5) throws TradingException;

    public ILiveOrder orderModify(StrategyBase var1, ILiveOrder var2, int var3, ITradingEventListener var4) throws TradingException;

    public OrdersList getHistoryOrders();

    public int getOpenOrdersCount(boolean var1);

    public ILiveOrder getOpenOrder(int var1, boolean var2);

    public int getHistoryOrdersCount();

    public Order getHistoryOrder(int var1);

    public double getAccountBalance();

    public double getAccountEquity();

    public double getInitialBalance();

    public double getTotalPL();

    public String getMainCurrency();

    public TickEvent getTickData();

    public boolean fillAtRealAskBidPrice();

    public Long2FloatRBTreeMap getWorstDailyEquity();

    public int getAmbiguousTrades();

    public void reuseOpenOrder(LiveOrderObj var1);

    public void evaluateActionListeners(int var1, StrategyBase var2) throws TradingException;

    public boolean supportsDuplicateTrades();

    public boolean IsMarketOpen();
}

