/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.app.MainApp
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.connection;

import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.connection.ConnectionPluginManager;
import com.strategyquant.tradinglib.engine.TradingEngine;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConnectionsFileManager {
    public static final Logger Log = LoggerFactory.getLogger((String)"ConnectionFileManager");
    private static final String connectionsFileName = "connections.txt";
    private static final String connectionsFilePath = MainApp.getDataPath() + "user/data/" + "connections.txt";

    public static void saveConnections() {
        Log.info("Saving connections to " + connectionsFilePath);
        ConnectionManager connectionManager = TradingEngine.getLiveEngine().getConnectionManager();
        try (PrintWriter printWriter = new PrintWriter(new FileWriter(connectionsFilePath, false));){
            for (Connection connection : connectionManager.getAllConnections()) {
                printWriter.write(connection.toJSON() + "\n");
            }
        }
        catch (IOException iOException) {
            Log.error("Error while saving connections to the connections file.", (Throwable)iOException);
        }
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public static void loadConnections() {
        Log.info("Loading connections from " + connectionsFilePath);
        ConnectionManager connectionManager = TradingEngine.getLiveEngine().getConnectionManager();
        try (BufferedReader bufferedReader = new BufferedReader(new FileReader(connectionsFilePath));){
            String string;
            while ((string = bufferedReader.readLine()) != null) {
                try {
                    JSONObject jSONObject = new JSONObject(string);
                    String string2 = jSONObject.get("ConnectionName").toString();
                    String string3 = jSONObject.get("ConnectionPlugin").toString();
                    ValuesMap valuesMap = ValuesMap.fromJSON((JSONObject)jSONObject.getJSONObject("ConnectionParams"));
                    Connection connection = connectionManager.createConnection(string2, ConnectionPluginManager.getConnectionPlugin(string3), valuesMap);
                    if (valuesMap.get("connectOnStart") == null || !valuesMap.get("connectOnStart").toString().equals("true")) continue;
                    connection.connect();
                }
                catch (Exception exception) {
                    Log.error("Cannot initialize the connection.", (Throwable)exception);
                }
            }
            return;
        }
        catch (Exception exception) {
            Log.error("Error while initializing auto-connect connections...", (Throwable)exception);
        }
    }
}

