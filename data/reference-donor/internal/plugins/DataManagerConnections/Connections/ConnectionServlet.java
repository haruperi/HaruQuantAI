/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.connection.ConnectionManager
 *  com.strategyquant.tradinglib.connection.ConnectionPluginManager
 *  com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.WebAppManager
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Connections;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.connection.ConnectionPluginManager;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.WebAppManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConnectionServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ConnectionServlet.class);
    private ConnectionManager connManager;
    private static ConnectionServlet instance;

    public ConnectionServlet() {
        instance = this;
    }

    public static ConnectionServlet getInstance() {
        return instance;
    }

    protected String execute(String command, Map<String, String[]> args, String method) {
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
        }
        return ConnectionServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onAdd(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String connectionPlugin = this.tryGetParam(args, "ConnectionPlugin")[0];
            String connectionName = this.tryGetParam(args, "ConnectionName")[0];
            ValuesMap connectionParams = ValuesMap.fromJSON((JSONObject)new JSONObject(this.tryGetParam(args, "ConnectionParams")[0]));
            this.connManager.createConnection(connectionName, ConnectionPluginManager.getConnectionPlugin((String)connectionPlugin), connectionParams);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getConnections(), (String[])new String[0]);
            response.put("success", (Object)L.t((String)"Connection '%d' added.", (Object[])new Object[]{connectionName}));
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON(null, (Throwable)ex);
        }
    }

    public String onList() {
        JSONObject response = new JSONObject();
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getConnections(), (String[])new String[0]);
        response.put("success", (Object)L.t((String)"Connections listed.", (Object[])new Object[0]));
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

    private String onRemove(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = this.tryGetParam(args, "ConnectionName")[0];
            if (!this.isConnectionActive(connectionName)) {
                this.connManager.removeConnection(connectionName);
                response.put("success", (Object)L.t((String)"Connection '%s' removed.", (Object[])new Object[]{connectionName}));
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getConnections(), (String[])new String[0]);
            } else {
                response.put("error", (Object)L.t((String)"Connection '%s' is active and thus cannot be removed.", (Object[])new Object[]{connectionName}));
            }
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON(null, (Throwable)ex);
        }
    }

    private String onEdit(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String connectionName = this.tryGetParam(args, "ConnectionName")[0];
            ValuesMap connectionParams = ValuesMap.fromJSON((JSONObject)new JSONObject(this.tryGetParam(args, "ConnectionParams")[0]));
            if (!this.isConnectionActive(connectionName)) {
                this.connManager.editConnection(connectionName, connectionParams);
                response.put("success", (Object)L.t((String)"Connection '%s' modified.", (Object[])new Object[]{connectionName}));
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getConnections(), (String[])new String[0]);
            } else {
                response.put("error", (Object)L.t((String)"Connection '%s' is active and thus cannot be edited.", (Object[])new Object[]{connectionName}));
            }
            return response.toString();
        }
        catch (Exception ex) {
            return ConnectionServlet.apiErrorJSON(null, (Throwable)ex);
        }
    }

    public boolean isConnectionActive(String connName) {
        String appCode = "SQTRADER";
        Map appPorts = WebAppManager.getAppPorts();
        if (appPorts.containsKey(appCode)) {
            int port = (Integer)appPorts.get(appCode);
            String url = WebAppManager.getBaseURL((int)port) + "/connections/isactive?args={'ConnectionName':'" + connName + "'}";
            String response = null;
            try {
                response = SQUtils.httpGet((String)url);
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (response != null) {
                try {
                    JSONObject responseJson = new JSONObject(response);
                    String active = responseJson.get("active").toString();
                    return active.equals("true");
                }
                catch (Exception ex) {
                    Log.error("Error reading response.", (Throwable)ex);
                }
            }
        }
        return false;
    }
}

