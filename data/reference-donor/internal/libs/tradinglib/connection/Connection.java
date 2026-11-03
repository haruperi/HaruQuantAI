/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ValuesMap
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.connection;

import com.strategyquant.lib.ValuesMap;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.connection.IDataFeed;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import org.json.JSONObject;

public abstract class Connection {
    protected final ConnectionManager connectionManager;
    protected final String connectionName;
    protected final IConnectionPlugin connectionPlugin;
    protected final int hashCode;
    private IDataFeed dataFeed;
    private IExecutionEngine executionEngine;
    protected ValuesMap connParams;
    private String connectionType;

    public Connection(ConnectionManager connectionManager, String string, IConnectionPlugin iConnectionPlugin, ValuesMap valuesMap) {
        this.connectionManager = connectionManager;
        this.connectionName = string;
        this.connectionPlugin = iConnectionPlugin;
        this.hashCode = string.hashCode();
        this.connParams = valuesMap;
        this.initializeEngines();
        if (this.dataFeed == null && this.executionEngine == null) {
            throw new IllegalArgumentException("Connection must implement at least one of the interfaces: DataFeed or ExecutionEngine !");
        }
        this.connectionType = null;
        if (this.dataFeed != null) {
            this.connectionType = "DataFeed";
        }
        if (this.executionEngine != null) {
            this.connectionType = this.connectionType + (this.connectionType != null ? " & " : "") + "Execution";
        }
    }

    public String toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("ConnectionName", (Object)this.connectionName);
        jSONObject.put("ConnectionPlugin", (Object)this.connectionPlugin.getPluginName());
        jSONObject.put("ConnectionParams", (Object)this.connParams.toJSON());
        return jSONObject.toString();
    }

    protected void setExecutionEngine(IExecutionEngine iExecutionEngine) {
        this.executionEngine = iExecutionEngine;
    }

    protected void setDataFeed(IDataFeed iDataFeed) {
        this.dataFeed = iDataFeed;
    }

    public String getConnectionName() {
        return this.connectionName;
    }

    public int getConnectionHash() {
        return this.hashCode;
    }

    public String getPluginName() {
        return this.connectionPlugin.getPluginName();
    }

    public ValuesMap getConnectionParams() {
        return this.connParams;
    }

    public void setConnectionParams(ValuesMap valuesMap) {
        this.connParams = valuesMap;
    }

    public IExecutionEngine getExecutionEngine() {
        return this.executionEngine;
    }

    public boolean isExecutionEngine() {
        return this.executionEngine != null;
    }

    public IDataFeed getDataFeed() {
        return this.dataFeed;
    }

    public boolean isDataFeed() {
        return this.dataFeed != null;
    }

    public String getType() {
        return this.connectionType;
    }

    public abstract void initializeEngines();

    public abstract String getStatus();

    public abstract void connect() throws Exception;

    public abstract boolean isConnected();

    public abstract void disconnect() throws Exception;
}

