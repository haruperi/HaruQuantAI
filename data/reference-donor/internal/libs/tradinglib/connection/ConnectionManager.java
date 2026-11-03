/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.IDataBuffer
 *  com.strategyquant.datalib.data.impl.ConcurrentDataBuffer
 *  com.strategyquant.lib.ValuesMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.connection;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.IDataBuffer;
import com.strategyquant.datalib.data.impl.ConcurrentDataBuffer;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionsFileManager;
import com.strategyquant.tradinglib.connection.IConnectionListener;
import com.strategyquant.tradinglib.connection.IDataFeed;
import com.strategyquant.tradinglib.order.IOrderListener;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import java.util.ArrayList;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConnectionManager {
    public static final Logger Log = LoggerFactory.getLogger(ConnectionManager.class);
    public static final String CONNECTION_HISTORY = "History";
    public static final String STATUS_DISCONNECTED = "Disconnected";
    public static final String STATUS_CONNECTING = "Connecting";
    public static final String STATUS_CONNECTED = "Connected";
    public static final String STATUS_CONNECTION_FAILED = "Connection failed";
    private HashMap<Integer, Connection> connections = new HashMap();
    private HashMap<String, Integer> connectionHashCodes = new HashMap();
    private ArrayList<IConnectionListener> connectionListeners = new ArrayList();
    private ArrayList<IOrderListener> orderListeners = new ArrayList();
    IDataBuffer dataBuffer = null;

    public ConnectionManager() {
        this(200);
    }

    public ConnectionManager(int n) {
        this.dataBuffer = new ConcurrentDataBuffer(n);
    }

    public synchronized Connection createConnection(String string, IConnectionPlugin iConnectionPlugin, ValuesMap valuesMap) throws Exception {
        for (String object : this.connectionHashCodes.keySet()) {
            if (object.compareTo(string) != 0) continue;
            throw new Exception("Cannot create connection. Connection with name \"" + string + "\" already exists!");
        }
        Connection connection = iConnectionPlugin.createConnection(this, string, valuesMap);
        this.addConnection(string, connection);
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionAdd(string, iConnectionPlugin.getPluginName(), connection.getType(), 0, 0.0, 0.0, connection.getStatus());
            }
        }
        return connection;
    }

    public synchronized Connection getConnection(String string) throws DataException {
        if (!this.connectionHashCodes.containsKey(string)) {
            throw new DataException(1, "Connection with name '" + string + "' doesn't exist!");
        }
        return this.connections.get(this.connectionHashCodes.get(string));
    }

    public synchronized ArrayList<Connection> getAllConnections() {
        ArrayList<Connection> arrayList = new ArrayList<Connection>();
        for (int n : this.connections.keySet()) {
            arrayList.add(this.connections.get(n));
        }
        return arrayList;
    }

    public void addConnection(String string, Connection connection) {
        int n = connection.getConnectionHash();
        this.connectionHashCodes.put(string, n);
        this.connections.put(n, connection);
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionAdd(string, connection.getPluginName(), connection.getType(), 0, 0.0, 0.0, connection.getStatus());
            }
        }
    }

    public synchronized void editConnection(String string, ValuesMap valuesMap) throws Exception {
        Connection connection = this.connections.get(this.connectionHashCodes.get(string));
        if (connection.isConnected()) {
            connection.disconnect();
        }
        connection.setConnectionParams(valuesMap);
        ConnectionsFileManager.saveConnections();
    }

    public synchronized void removeConnection(String string) throws Exception {
        Connection connection = this.connections.get(this.connectionHashCodes.get(string));
        connection.disconnect();
        this.connections.remove(this.connectionHashCodes.get(string));
        this.connectionHashCodes.remove(string);
        ConnectionsFileManager.saveConnections();
        this.fireConnectionRemovedEvent(string);
    }

    public void registerConnectionAndSymbol(ChartDef chartDef) throws Exception {
        if (chartDef.isRegistered()) {
            return;
        }
        String string = chartDef.getConnectionName();
        Connection connection = this.getConnection(string);
        IDataFeed iDataFeed = connection.getDataFeed();
        if (iDataFeed == null) {
            throw new Exception("Connection is not a Data Feed, cannot register symbols !");
        }
        String string2 = chartDef.getSymbol();
        if (!iDataFeed.checkSymbolIsSupported(string2)) {
            throw new DataException(2, "Symbol '" + string2 + "' is not supported for connection '" + string + "'!");
        }
        iDataFeed.registerSymbol(string2);
        chartDef.setRegistered();
    }

    public void closeAllConnections() {
        for (int n : this.connections.keySet()) {
            try {
                this.connections.get(n).disconnect();
            }
            catch (Exception exception) {
                Log.error("Exception thrown while closing connections.", (Throwable)exception);
            }
        }
    }

    public IDataBuffer getDataBuffer() {
        return this.dataBuffer;
    }

    public void registerConnectionAndSymbol() {
    }

    public synchronized boolean hasConnection(String string) {
        return this.connectionHashCodes.containsKey(string);
    }

    public void addConnectionListener(IConnectionListener iConnectionListener) {
        this.connectionListeners.add(iConnectionListener);
    }

    public void removeConnectionListener(IConnectionListener iConnectionListener) {
        this.connectionListeners.remove(iConnectionListener);
    }

    public void addOrderListener(IOrderListener iOrderListener) {
        this.orderListeners.add(iOrderListener);
    }

    public void removeOrderListener(IOrderListener iOrderListener) {
        this.orderListeners.remove(iOrderListener);
    }

    public void fireStateChangedEvent(String string, String string2) {
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionStateChange(string, string2);
            }
        }
    }

    public void fireConnectionErrorEvent(String string, Exception exception) {
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionError(string, exception);
            }
        }
    }

    public void fireConnectionRemovedEvent(String string) {
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionRemove(string);
            }
        }
    }

    public void firePLChangedEvent(String string, double d) {
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionPLChange(string, d);
            }
        }
    }

    public void fireAccountBalanceChangedEvent(String string, double d) {
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionAccountBalanceChange(string, d);
            }
        }
    }

    public void fireOpenOrdersChangedEvent(String string, int n) {
        if (!this.connectionListeners.isEmpty()) {
            for (IConnectionListener iConnectionListener : this.connectionListeners) {
                iConnectionListener.onConnectionOpenOrdersChange(string, n);
            }
        }
    }

    public void fireOrderAddEvent(long l, String string, String string2, double d, double d2) {
        if (!this.orderListeners.isEmpty()) {
            for (IOrderListener iOrderListener : this.orderListeners) {
                iOrderListener.onOrderAdd(l, string, string2, d, d2);
            }
        }
    }

    public void fireOrderClosedEvent(long l) {
        if (!this.orderListeners.isEmpty()) {
            for (IOrderListener iOrderListener : this.orderListeners) {
                iOrderListener.onOrderClosed(l);
            }
        }
    }

    public void fireOrderChangedEvent(long l, String string, double d, double d2) {
        if (!this.orderListeners.isEmpty()) {
            for (IOrderListener iOrderListener : this.orderListeners) {
                iOrderListener.onOrderChanged(l, string, d, d2);
            }
        }
    }
}

