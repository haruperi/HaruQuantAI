/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.jfx.TradeOperation
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.tradinglib.connection.Connection
 *  com.strategyquant.tradinglib.connection.ConnectionManager
 *  com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.MT4;

import com.jfx.TradeOperation;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge;
import com.strategyquant.plugin.Connection.impl.MT4.MT4DataFeed;
import com.strategyquant.plugin.Connection.impl.MT4.MT4ExecutionEngine;
import com.strategyquant.plugin.Connection.impl.MT4.MT4TerminalManager;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import java.util.ArrayList;
import java.util.Date;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT4Connection
extends Connection {
    public static final Logger Log = LoggerFactory.getLogger((String)"MT4Connection");
    private MT4Bridge mt4Bridge;
    private Thread connStateCheckThread;
    private boolean endConnStateCheck = false;

    public MT4Connection(IConnectionPlugin connectionPlugin, ConnectionManager connectionManager, String connectionName, ValuesMap connParams) throws Exception {
        super(connectionManager, connectionName, connectionPlugin, connParams);
        this.checkConnection(connectionManager, connParams);
    }

    public void initializeEngines() {
        this.mt4Bridge = new MT4Bridge(this.connectionManager, this.connectionName, this.getConnectionHash());
        this.setDataFeed(new MT4DataFeed(this, this.mt4Bridge));
        this.setExecutionEngine(new MT4ExecutionEngine(this, this.mt4Bridge));
    }

    private void checkConnection(ConnectionManager connectionManager, ValuesMap connParams) throws Exception {
        ArrayList connections = connectionManager.getAllConnections();
        Object curUsername = connParams.get("username");
        Object curBrokerIP = connParams.get("brokerIP");
        if (curUsername == null) {
            throw new Exception("Cannot create connection. Parameter \"username\" not found!");
        }
        if (curBrokerIP == null) {
            throw new Exception("Cannot create connection. Parameter \"brokerIP\" not found!");
        }
        for (Connection conn : connections) {
            Object username = conn.getConnectionParams().get("username");
            Object brokerIP = conn.getConnectionParams().get("brokerIP");
            if (username == null || brokerIP == null || username.toString().compareTo(curUsername.toString()) != 0 || brokerIP.toString().compareTo(curBrokerIP.toString()) != 0) continue;
            throw new Exception("Cannot create connection. Connection to user account \"" + username + "\" and broker IP " + curBrokerIP + " already exists!");
        }
    }

    public void connect() throws Exception {
        if (!this.mt4Bridge.isConnected() && this.mt4Bridge.getStatus().compareTo("Disconnected") == 0) {
            String user = this.connParams.get("username").toString();
            String password = this.connParams.get("password").toString();
            String brokerIP = this.connParams.get("brokerIP").toString();
            boolean hide = false;
            if (this.connParams.get("hide") != null) {
                hide = Boolean.parseBoolean(this.connParams.get("hide").toString());
            }
            boolean minimized = false;
            if (this.connParams.get("minimize") != null) {
                minimized = Boolean.parseBoolean(this.connParams.get("minimize").toString());
            }
            boolean connectOnStart = false;
            if (this.connParams.get("connectOnStart") != null) {
                connectOnStart = Boolean.parseBoolean(this.connParams.get("connectOnStart").toString());
            }
            this.mt4Bridge.setStatus("Connecting");
            try {
                MT4TerminalManager.createTerminal(user, password, brokerIP, this.connectionName, this.mt4Bridge, hide, minimized, connectOnStart);
            }
            catch (Exception e) {
                this.mt4Bridge.setStatus("Connection failed");
                throw e;
            }
            this.startConnectionStateCheck();
        } else {
            Log.error("Cannot connect. Connection \"" + this.connectionName + "\" is already active.");
        }
    }

    private void startConnectionStateCheck() {
        if (this.connStateCheckThread != null && this.connStateCheckThread.isAlive()) {
            this.endConnStateCheck = true;
            this.connStateCheckThread.interrupt();
            try {
                this.connStateCheckThread.join();
            }
            catch (InterruptedException e) {
                e.printStackTrace();
            }
            this.endConnStateCheck = false;
        }
        this.connStateCheckThread = new Thread(){

            @Override
            public void run() {
                try {
                    1.sleep(20000L);
                }
                catch (InterruptedException e) {
                    e.printStackTrace();
                }
                if (MT4Connection.this.endConnStateCheck) {
                    return;
                }
                if (!MT4Connection.this.mt4Bridge.isConnected() && MT4Connection.this.mt4Bridge.getStatus().compareTo("Disconnected") != 0) {
                    MT4Connection.this.mt4Bridge.setStatus("Connection failed");
                }
            }
        };
        this.connStateCheckThread.start();
    }

    public void disconnect() throws Exception {
        Log.info("Disconnecting MT4 Connection \"" + this.connectionName + "\"");
        this.mt4Bridge.disconnectBridge();
        this.mt4Bridge.setStatus("Disconnected");
        Object connOnStart = this.connParams.get("connectOnStart");
        if (connOnStart == null || !Boolean.parseBoolean(connOnStart.toString())) {
            MT4TerminalManager.removeTerminal(this.connectionName);
        } else {
            MT4TerminalManager.killTerminalProcess(this.connectionName);
        }
    }

    public boolean isConnected() {
        return this.mt4Bridge.isConnected();
    }

    public String getStatus() {
        return this.mt4Bridge.getConnectionState();
    }

    public long buyNow(String symbol, double volume) throws Exception {
        return this.mt4Bridge.buyNow(symbol, volume);
    }

    public long sellNow(String symbol, double volume) throws Exception {
        return this.mt4Bridge.sellNow(symbol, volume);
    }

    public long sendOrder(String symbol, String operation, double volume, int slippage, int stopLossPointsCount, int takeProfitPointsCount, String comment, int magicNumber, Date expiration) throws Exception {
        if (operation.compareTo("BUY") == 0) {
            return this.mt4Bridge.sendOrder(symbol, TradeOperation.OP_BUY, volume, slippage, stopLossPointsCount, takeProfitPointsCount, comment, magicNumber, expiration);
        }
        if (operation.compareTo("SELL") == 0) {
            return this.mt4Bridge.sendOrder(symbol, TradeOperation.OP_SELL, volume, slippage, stopLossPointsCount, takeProfitPointsCount, comment, magicNumber, expiration);
        }
        throw new Exception("Unrecognized operation \"" + operation + "\". Expected \"BUY\" or \"SELL\".");
    }

    public long sendOrder(String symbol, String operation, double volume, int slippage, double stopLoss, double takeProfit, String comment, int magicNumber, Date expiration) throws Exception {
        if (operation.compareTo("BUY") == 0) {
            return this.mt4Bridge.sendOrder(symbol, TradeOperation.OP_BUY, volume, slippage, stopLoss, takeProfit, comment, magicNumber, expiration);
        }
        if (operation.compareTo("SELL") == 0) {
            return this.mt4Bridge.sendOrder(symbol, TradeOperation.OP_SELL, volume, slippage, stopLoss, takeProfit, comment, magicNumber, expiration);
        }
        throw new Exception("Unrecognized operation \"" + operation + "\". Expected \"BUY\" or \"SELL\".");
    }

    public void modifyOrder(long ticket, double price, double stopLoss, double takeProfit, Date expiration) throws Exception {
        this.mt4Bridge.modifyOrder(ticket, price, stopLoss, takeProfit, expiration);
    }

    public void closeOrder(long ticket) throws Exception {
        this.mt4Bridge.closeOrder(ticket);
    }

    public String getConnectionName() {
        return this.connectionName;
    }
}

