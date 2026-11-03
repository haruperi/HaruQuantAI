/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.connection.Connection
 *  com.strategyquant.tradinglib.connection.ConnectionManager
 *  com.strategyquant.tradinglib.connection.ConnectionPluginManager
 *  com.strategyquant.tradinglib.engine.TradingEngine
 *  com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.Connection;

import com.strategyquant.lib.L;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.connection.ConnectionPluginManager;
import com.strategyquant.tradinglib.engine.TradingEngine;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConnectionServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ConnectionServlet.class);
    private ConnectionManager connManager = TradingEngine.getLiveEngine().getConnectionManager();
    private static ConnectionServlet instance;

    public ConnectionServlet() {
        instance = this;
    }

    public static ConnectionServlet getInstance() {
        return instance;
    }

    protected String execute(String command, JSONObject args) {
        switch (command) {
            case "add": {
                return this.onAdd(args);
            }
            case "edit": {
                return this.onEdit(args);
            }
            case "remove": {
                return this.onRemove(args);
            }
            case "list": {
                return this.onList();
            }
            case "listplugins": {
                return this.onListPlugins();
            }
            case "connect": {
                return this.onConnect(args);
            }
            case "disconnect": {
                return this.onDisconnect(args);
            }
            case "isactive": {
                return this.onIsActive(args);
            }
        }
        return ConnectionServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onAdd(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            String connectionPlugin = args.get("ConnectionPlugin").toString();
            String connectionName = args.get("ConnectionName").toString();
            ValuesMap connectionParams = ValuesMap.fromJSON((JSONObject)args.getJSONObject("ConnectionParams"));
            this.connManager.createConnection(connectionName, ConnectionPluginManager.getConnectionPlugin((String)connectionPlugin), connectionParams);
            response.put("success", (Object)L.t((String)"Connection '%s' added.", (Object[])new Object[]{connectionName}));
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON((String)L.t((String)"Cannot add connection.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    public String onList() {
        JSONObject response = new JSONObject();
        JSONArray allConns = new JSONArray();
        for (Connection conn : this.connManager.getAllConnections()) {
            JSONObject connJSON = new JSONObject();
            connJSON.put("ConnectionPlugin", (Object)conn.getPluginName());
            connJSON.put("ConnectionName", (Object)conn.getConnectionName());
            connJSON.put("ConnectionState", (Object)conn.getStatus());
            connJSON.put("ConnectionParams", (Object)conn.getConnectionParams().toJSON());
            connJSON.put("ConnectionType", (Object)conn.getType());
            if (conn.isExecutionEngine()) {
                connJSON.put("OpenPositions", conn.getExecutionEngine().getOpenOrdersCount(true));
                connJSON.put("AccountBalance", conn.getExecutionEngine().getAccountBalance());
                connJSON.put("AccountPL", conn.getExecutionEngine().getTotalPL());
            } else {
                connJSON.put("OpenPositions", (Object)"N/A");
                connJSON.put("AccountBalance", (Object)"N/A");
                connJSON.put("AccountPL", (Object)"N/A");
            }
            allConns.put((Object)connJSON);
        }
        response.put("connections", (Object)allConns);
        response.put("success", (Object)L.t((String)"Found %d connections.", (Object[])new Object[]{this.connManager.getAllConnections().size()}));
        return response.toString();
    }

    private String onListPlugins() {
        JSONObject response = new JSONObject();
        JSONArray allPlugins = new JSONArray();
        for (IConnectionPlugin plugin : SQPluginManager.getPlugins(IConnectionPlugin.class)) {
            JSONObject pluginJSON = new JSONObject();
            pluginJSON.put("PluginName", (Object)plugin.getPluginName());
            allPlugins.put((Object)pluginJSON);
        }
        response.put("plugins", (Object)allPlugins);
        response.put("success", (Object)L.t((String)"Found %d plugins.", (Object[])new Object[]{SQPluginManager.getPlugins(IConnectionPlugin.class).size()}));
        return response.toString();
    }

    private String onRemove(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = args.get("ConnectionName").toString();
            this.connManager.removeConnection(connectionName);
            response.put("success", (Object)L.t((String)"Connection '%s' removed.", (Object[])new Object[]{connectionName}));
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON((String)L.t((String)"Cannot remove connection.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onEdit(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = args.get("ConnectionName").toString();
            ValuesMap connectionParams = ValuesMap.fromJSON((JSONObject)args.getJSONObject("ConnectionParams"));
            this.connManager.editConnection(connectionName, connectionParams);
            response.put("success", (Object)L.t((String)"Connection '%s' modified.", (Object[])new Object[]{connectionName}));
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON((String)L.t((String)"Cannot edit connection.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onConnect(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = args.get("ConnectionName").toString();
            this.connManager.getConnection(connectionName).connect();
            response.put("success", (Object)L.t((String)"Connection '%s' connected.", (Object[])new Object[]{connectionName}));
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON((String)L.t((String)"Connection failed.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onDisconnect(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = args.get("ConnectionName").toString();
            this.connManager.getConnection(connectionName).disconnect();
            response.put("success", (Object)L.t((String)"Connection '%s' disconnected.", (Object[])new Object[]{connectionName}));
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON((String)L.t((String)"Cannot disconnect.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onIsActive(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = args.get("ConnectionName").toString();
            if (this.connManager.getConnection(connectionName).isConnected()) {
                response.put("active", (Object)"true");
            } else {
                response.put("active", (Object)"false");
            }
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON(null, (Throwable)ex);
        }
    }
}

