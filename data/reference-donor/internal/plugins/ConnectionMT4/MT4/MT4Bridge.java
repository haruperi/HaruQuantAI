/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.jfx.Broker
 *  com.jfx.ErrUnknownSymbol
 *  com.jfx.MarketInfo
 *  com.jfx.SelectionPool
 *  com.jfx.SelectionType
 *  com.jfx.Timeframe
 *  com.jfx.TradeOperation
 *  com.jfx.strategy.NJ4XInvalidUserNameOrPasswordException
 *  com.jfx.strategy.NJ4XMaxNumberOfTerminalsExceededException
 *  com.jfx.strategy.NJ4XNoConnectionToServerException
 *  com.jfx.strategy.OrderInfo
 *  com.jfx.strategy.Strategy
 *  com.jfx.strategy.StrategyRunner
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.IDataBuffer
 *  com.strategyquant.tradinglib.connection.ConnectionManager
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.MT4;

import com.jfx.Broker;
import com.jfx.ErrUnknownSymbol;
import com.jfx.MarketInfo;
import com.jfx.SelectionPool;
import com.jfx.SelectionType;
import com.jfx.Timeframe;
import com.jfx.TradeOperation;
import com.jfx.strategy.NJ4XInvalidUserNameOrPasswordException;
import com.jfx.strategy.NJ4XMaxNumberOfTerminalsExceededException;
import com.jfx.strategy.NJ4XNoConnectionToServerException;
import com.jfx.strategy.OrderInfo;
import com.jfx.strategy.Strategy;
import com.jfx.strategy.StrategyRunner;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT4Bridge
extends Strategy {
    private static final Logger Log = LoggerFactory.getLogger(MT4Bridge.class);
    private final int coordinationInterval = 200;
    private ArrayList<Long> activeOrders = new ArrayList();
    private ArrayList<Boolean> orderClosed = new ArrayList();
    private HashMap<String, Integer> activeSymbols = new HashMap();
    private ConnectionManager connectionManager;
    private String connectionName;
    private int connectionHash;
    private double PL;
    private double balance;
    private int openOrders;
    private String status;
    private boolean disconnectBridge = false;
    private boolean coordinationCalled = false;

    public MT4Bridge(ConnectionManager manager, String connectionName, int connectionHash) {
        this.connectionManager = manager;
        this.connectionName = connectionName;
        this.connectionHash = connectionHash;
        this.status = "Disconnected";
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void registerSymbol(String newSymbol) throws Exception {
        Log.info("Registering symbol \"" + newSymbol + "\"...");
        if (this.isConnected()) {
            HashMap<String, Integer> hashMap = this.activeSymbols;
            synchronized (hashMap) {
                for (String symbol : this.activeSymbols.keySet()) {
                    if (symbol.compareTo(newSymbol) != 0) continue;
                    Log.warn("Symbol \"" + newSymbol + "\" is already registered");
                    return;
                }
                this.activeSymbols.put(newSymbol, newSymbol.hashCode());
            }
        } else {
            throw new Exception("Connection is not active yet. Cannot register symbol.");
        }
    }

    public long buyNow(String symbol, double volume) throws Exception {
        Log.info("Executing BUY NOW order. Symbol: \"" + symbol + "\", volume: " + volume);
        long expTime = System.currentTimeMillis() + 60000L;
        Date expiration = new Date(expTime);
        long ticket = this.sendOrder(symbol, TradeOperation.OP_BUY, volume, 10, 0, 0, "Buy now order", 0, expiration);
        return ticket;
    }

    public long sellNow(String symbol, double volume) throws Exception {
        Log.info("Executing SELL NOW order. Symbol: \"" + symbol + "\", volume: " + volume);
        long expTime = System.currentTimeMillis() + 60000L;
        Date expiration = new Date(expTime);
        long ticket = this.sendOrder(symbol, TradeOperation.OP_SELL, volume, 10, 0, 0, "Sell now order", 0, expiration);
        return ticket;
    }

    public long sendOrder(String symbol, TradeOperation operation, double volume, int slippage, int stopLossPointsCount, int takeProfitPointsCount, String comment, int magicNumber, Date expiration) throws Exception {
        double buyPrice;
        Log.info("Sending order. Symbol: \"" + symbol + "\", operation: " + operation.toString() + "volume: " + volume + ", slippage: " + slippage + ", stop loss: " + stopLossPointsCount + ", take profit: " + takeProfitPointsCount + ", comment: \"" + comment + "\", expiration: " + expiration);
        double point = this.marketInfo(symbol, MarketInfo.MODE_POINT);
        double stopLoss = 0.0;
        double takeProfit = 0.0;
        if (operation == TradeOperation.OP_BUY) {
            buyPrice = this.marketInfo(symbol, MarketInfo.MODE_ASK);
            if (stopLossPointsCount > 0) {
                stopLoss = buyPrice - (double)stopLossPointsCount * point;
            }
            if (takeProfitPointsCount > 0) {
                takeProfit = buyPrice + (double)takeProfitPointsCount * point;
            }
        } else {
            buyPrice = this.marketInfo(symbol, MarketInfo.MODE_BID);
            if (stopLossPointsCount > 0) {
                stopLoss = buyPrice + (double)stopLossPointsCount * point;
            }
            if (takeProfitPointsCount > 0) {
                takeProfit = buyPrice - (double)takeProfitPointsCount * point;
            }
        }
        long ticket = this.orderSend(symbol, operation, volume, buyPrice, slippage, stopLoss, takeProfit, comment, magicNumber, expiration);
        this.activeOrders.add(ticket);
        this.orderClosed.add(false);
        this.fireOrderAddEvent(ticket, operation.toString(), symbol, volume, buyPrice);
        return ticket;
    }

    public long sendOrder(String symbol, TradeOperation operation, double volume, int slippage, double stopLoss, double takeProfit, String comment, int magicNumber, Date expiration) throws Exception {
        Log.info("Sending order. Symbol: \"" + symbol + "\", operation: " + operation.toString() + "volume: " + volume + ", slippage: " + slippage + ", stop loss: " + stopLoss + ", take profit: " + takeProfit + ", comment: \"" + comment + "\", expiration: " + expiration);
        double point = this.marketInfo(symbol, MarketInfo.MODE_POINT);
        double buyPrice = operation == TradeOperation.OP_BUY ? this.marketInfo(symbol, MarketInfo.MODE_ASK) : this.marketInfo(symbol, MarketInfo.MODE_BID);
        long ticket = this.orderSend(symbol, operation, volume, buyPrice, slippage, stopLoss, takeProfit, comment, magicNumber, expiration);
        this.activeOrders.add(ticket);
        this.orderClosed.add(false);
        this.fireOrderAddEvent(ticket, operation.toString(), symbol, volume, buyPrice);
        return ticket;
    }

    public void closeOrder(long ticket) throws Exception {
        Log.info("Closing order with ticket number: " + ticket);
        OrderInfo info = this.orderGet(ticket, SelectionType.SELECT_BY_TICKET, SelectionPool.MODE_TRADES);
        double closePrice = info.getType() == TradeOperation.OP_BUY ? this.marketInfo(info.getSymbol(), MarketInfo.MODE_BID) : this.marketInfo(info.getSymbol(), MarketInfo.MODE_ASK);
        this.orderClose(ticket, info.getLots(), closePrice, 10, 0L);
    }

    public void modifyOrder(long ticket, double price, double stopLoss, double takeProfit, Date expiration) throws Exception {
        Log.info("Modifying order with ticket number: " + ticket + ". Stop loss: " + stopLoss + ", take profit: " + takeProfit);
        this.orderModify(ticket, price, stopLoss, takeProfit, expiration, 0L);
    }

    public void addActiveOrders() {
        Log.info("Adding active orders...");
        int ordersCount = this.ordersTotal();
        for (int i = 0; i < ordersCount; ++i) {
            if (!this.orderSelect(i, SelectionType.SELECT_BY_POS, SelectionPool.MODE_TRADES)) continue;
            try {
                int typeInt = this.orderType();
                String type = typeInt == 0 ? "BUY" : "SELL";
                Log.info(String.format("Ticket no.: #%d, Type: %s, Symbol: %s, Price open: %f, Price close: %f, Profit: %f", this.orderTicketNumber(), type, this.orderSymbol(), this.orderOpenPrice(), this.orderClosePrice(), this.orderProfit()));
                this.activeOrders.add(this.orderTicketNumber());
                this.orderClosed.add(false);
                this.fireOrderAddEvent(this.orderTicketNumber(), type, this.orderSymbol(), this.orderLots(), this.orderOpenPrice());
                continue;
            }
            catch (Exception e) {
                Log.error("Error while adding order.", (Throwable)e);
            }
        }
    }

    public void dumpActiveOrders() throws Exception {
        Log.info("--- Active orders: --------------------------------------------------------");
        int ordersCount = this.ordersTotal();
        for (int i = 0; i < ordersCount; ++i) {
            if (!this.orderSelect(i, SelectionType.SELECT_BY_POS, SelectionPool.MODE_TRADES)) continue;
            int typeInt = this.orderType();
            String type = typeInt == 0 ? "BUY" : "SELL";
            Log.info(String.format("Ticket no.: #%d, Type: %s, Symbol: %s, Price open: %f, Price close: %f, Profit: %f", this.orderTicketNumber(), type, this.orderSymbol(), this.orderOpenPrice(), this.orderClosePrice(), this.orderProfit()));
        }
        Log.info("---------------------------------------------------------------------------");
    }

    private void updateOrdersInfo() {
        int ordersCount = this.ordersTotal();
        boolean[] ordersProcessed = new boolean[this.activeOrders.size()];
        if (ordersCount != this.openOrders) {
            this.openOrders = ordersCount;
            this.fireOpenOrdersChangedEvent();
        }
        block2: for (int i = 0; i < ordersCount; ++i) {
            try {
                if (!this.orderSelect(i, SelectionType.SELECT_BY_POS, SelectionPool.MODE_TRADES)) continue;
                for (int a = 0; a < this.activeOrders.size(); ++a) {
                    if (this.activeOrders.get(a).longValue() != this.orderTicketNumber()) continue;
                    ordersProcessed[a] = true;
                    this.fireOrderChangedEvent(this.orderTicketNumber(), "active", this.orderClosePrice(), this.orderProfit());
                    continue block2;
                }
                continue;
            }
            catch (Exception ex) {
                Log.error("Error getting order info", (Throwable)ex);
            }
        }
        for (int b = 0; b < ordersProcessed.length; ++b) {
            if (ordersProcessed[b] || this.orderClosed.get(b).booleanValue()) continue;
            this.fireOrderClosedEvent(this.activeOrders.get(b));
            this.orderClosed.set(b, true);
        }
    }

    public void getHistoryBars(String symbol, int count) {
        for (int i = 0; i < count; ++i) {
            try {
                double high = this.iHigh(symbol, Timeframe.PERIOD_M1, i);
                Log.debug("Symbol: " + symbol + ", shift: " + i + ", high: " + high);
                continue;
            }
            catch (Exception ex) {
                Log.error("Cannot load history bar no." + i + ".", (Throwable)ex);
            }
        }
    }

    public void init(String symbol, int period, StrategyRunner strategyRunner) {
        if (!this.disconnectBridge) {
            try {
                Log.info("Initializing MT4Bridge...");
                super.init(symbol, period, strategyRunner);
            }
            catch (ErrUnknownSymbol e) {
                e.printStackTrace();
            }
            catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public void deinit() {
        Log.info("Deinitializing MT4Bridge...");
        super.deinit();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void coordinate() {
        block13: {
            try {
                double curBalance;
                IDataBuffer dataBuffer = this.connectionManager.getDataBuffer();
                TickEvent tick = new TickEvent();
                if (!this.coordinationCalled && !this.disconnectBridge) {
                    this.coordinationCalled = true;
                    this.setStatus("Connected");
                }
                HashMap<String, Integer> hashMap = this.activeSymbols;
                synchronized (hashMap) {
                    for (String symbol : this.activeSymbols.keySet()) {
                        try {
                            double bidPrice = this.marketInfo(symbol, MarketInfo.MODE_BID);
                            double askPrice = this.marketInfo(symbol, MarketInfo.MODE_ASK);
                            tick.setSymbolHash(this.activeSymbols.get(symbol).intValue());
                            tick.setConnectionHash(this.connectionHash);
                            tick.setAsk(askPrice);
                            tick.setBid(bidPrice);
                            tick.setIsSet(true);
                            dataBuffer.put(tick);
                            Log.debug(this.connectionName + " > " + symbol + " price: " + bidPrice);
                        }
                        catch (ErrUnknownSymbol e) {
                            Log.error("Symbol \"" + symbol + "\" not recognized. Deleting from the list of symbols...", (Throwable)e);
                            this.activeSymbols.remove(symbol);
                        }
                    }
                }
                this.updateOrdersInfo();
                double curPL = this.accountProfit();
                if (curPL != this.PL) {
                    this.PL = curPL;
                    this.firePLChangedEvent();
                }
                if ((curBalance = this.accountBalance()) != this.balance) {
                    this.balance = curBalance;
                    this.fireAccountBalanceChangedEvent();
                }
            }
            catch (Exception ex) {
                if (this.disconnectBridge) break block13;
                Log.error("Error occurred during coordination.", (Throwable)ex);
                try {
                    this.disconnect();
                    this.status = "Disconnected";
                    this.fireStateChangedEvent();
                }
                catch (Exception e) {
                    Log.error("Unable to remove terminal \"" + this.connectionName + "\"");
                }
                this.fireConnectionErrorEvent(ex);
            }
        }
    }

    public synchronized void connect(String termServerHost, int termServerPort, Broker mt4Server, String mt4User, String mt4Password, String symbol, boolean asynchOrderOperations) throws NJ4XInvalidUserNameOrPasswordException, NJ4XMaxNumberOfTerminalsExceededException, NJ4XNoConnectionToServerException, IOException {
        super.connect(termServerHost, termServerPort, mt4Server, mt4User, mt4Password, symbol, asynchOrderOperations);
        this.disconnectBridge = false;
        this.coordinationCalled = false;
    }

    public void disconnectBridge() {
        try {
            this.disconnect();
        }
        catch (IOException e) {
            Log.error("Error during disconnecting.", (Throwable)e);
        }
        this.disconnectBridge = true;
    }

    public void disconnect() throws IOException {
        super.disconnect();
        this.coordinationCalled = false;
        this.status = "Disconnected";
        this.fireStateChangedEvent();
    }

    public long coordinationIntervalMillis() {
        return 200L;
    }

    public boolean isConnected() {
        return !this.disconnectBridge && super.isConnected() && this.coordinationCalled;
    }

    public boolean isDisconnectedByUser() {
        return this.disconnectBridge;
    }

    private void firePLChangedEvent() {
        this.connectionManager.firePLChangedEvent(this.connectionName, this.PL);
    }

    private void fireAccountBalanceChangedEvent() {
        this.connectionManager.fireAccountBalanceChangedEvent(this.connectionName, this.balance);
    }

    private void fireOpenOrdersChangedEvent() {
        this.connectionManager.fireOpenOrdersChangedEvent(this.connectionName, this.openOrders);
    }

    private void fireOrderAddEvent(long ticket, String type, String symbol, double lots, double openPrice) {
        this.connectionManager.fireOrderAddEvent(ticket, type, symbol, lots, openPrice);
    }

    private void fireOrderClosedEvent(long ticket) {
        this.connectionManager.fireOrderClosedEvent(ticket);
    }

    private void fireOrderChangedEvent(long ticket, String status, double closePrice, double pl) {
        this.connectionManager.fireOrderChangedEvent(ticket, status, closePrice, pl);
    }

    private void fireStateChangedEvent() {
        this.connectionManager.fireStateChangedEvent(this.connectionName, this.status);
    }

    private void fireConnectionErrorEvent(Exception ex) {
        this.connectionManager.fireConnectionErrorEvent(this.connectionName, ex);
    }

    public String getConnectionState() {
        return this.status;
    }

    public int getOpenOrdersCount() {
        return this.openOrders;
    }

    public double getTotalPL() {
        return this.PL;
    }

    public double getAccountBalance() {
        return this.balance;
    }

    public String getStatus() {
        return this.status;
    }

    public void setStatus(String status) {
        if (this.status.compareTo(status) != 0) {
            this.status = status;
            this.fireStateChangedEvent();
        }
    }
}

