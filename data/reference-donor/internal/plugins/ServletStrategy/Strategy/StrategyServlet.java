/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.engine.TradingEngine
 *  com.strategyquant.tradinglib.engine.TradingSetup
 *  com.strategyquant.tradinglib.engine.TradingSetupStatus
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.Strategy;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.lib.L;
import com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.engine.TradingEngine;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.engine.TradingSetupStatus;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(StrategyServlet.class);
    private TradingEngine tradingEngine = TradingEngine.getLiveEngine();
    private static StrategyServlet instance;

    public StrategyServlet() {
        instance = this;
    }

    public static StrategyServlet getInstance() {
        return instance;
    }

    protected String execute(String command, JSONObject args) {
        switch (command) {
            case "add": {
                return this.onAdd(args);
            }
            case "start": {
                return this.onStart(args);
            }
            case "stop": {
                return this.onStop(args);
            }
            case "remove": {
                return this.onRemove(args);
            }
            case "list": {
                return this.onList();
            }
        }
        return StrategyServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onAdd(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            Object connNameObj = args.get("ConnectionName");
            if (connNameObj != null) {
                String connName = connNameObj.toString();
                MyStrategy strategy = new MyStrategy();
                ChartSetup chartSetup1 = new ChartSetup(connName, "EURUSD", "H1", 1, 100L, "No Session");
                this.tradingEngine.addSetup(chartSetup1, null, (StrategyBase)strategy, new String[]{connName});
                response.put("success", (Object)L.t((String)"Strategy added.", (Object[])new Object[0]));
                return response.toString();
            }
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot add strategy. Connection name not specified.", (Object[])new Object[0]), null);
        }
        catch (Exception ex) {
            return StrategyServlet.apiErrorJSON(null, (Throwable)ex);
        }
    }

    public String onList() {
        JSONObject response = new JSONObject();
        JSONArray allConns = new JSONArray();
        for (TradingSetup tradingSetup : this.tradingEngine.getTradingSetups()) {
            JSONObject connJSON = new JSONObject();
            connJSON.put("SetupID", tradingSetup.getSetupId());
            connJSON.put("StrategyName", (Object)tradingSetup.getStrategy().getStrategyName());
            connJSON.put("ConnectionName", (Object)((ChartDef)tradingSetup.getChartSetup().getCharts().get(0)).getConnectionName());
            connJSON.put("Symbol", (Object)((ChartDef)tradingSetup.getChartSetup().getCharts().get(0)).getSymbol());
            connJSON.put("Status", (Object)TradingSetupStatus.toString((int)tradingSetup.getStatus()));
            allConns.put((Object)connJSON);
        }
        response.put("strategies", (Object)allConns);
        response.put("success", (Object)L.t((String)"Found %d trading setups.", (Object[])new Object[]{this.tradingEngine.getTradingSetups().size()}));
        return response.toString();
    }

    private String onRemove(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            Object setupIDObj = args.get("SetupID");
            if (setupIDObj != null) {
                int setupID = Integer.parseInt(String.valueOf(setupIDObj));
                this.tradingEngine.remove(this.tradingEngine.getSetupById(setupID));
                response.put("success", (Object)L.t((String)"Trading setup with ID '%s' removed.", (Object[])new Object[]{setupID}));
                return response.toString();
            }
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot remove trading setup. Setup ID not specified.", (Object[])new Object[0]), null);
        }
        catch (Exception ex) {
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot remove trading setup.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onStart(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            Object setupIDObj = args.get("SetupID");
            if (setupIDObj != null) {
                int setupID = Integer.parseInt(String.valueOf(setupIDObj));
                if (this.tradingEngine.getSetupById(setupID).getStatus() != 1) {
                    this.tradingEngine.getSetupById(setupID).start(false);
                    response.put("success", (Object)L.t((String)"Trading setup with ID '%s' started.", (Object[])new Object[]{setupID}));
                    return response.toString();
                }
                return StrategyServlet.apiErrorJSON((String)L.t((String)"Trading setup with ID '%s' is already running.", (Object[])new Object[]{setupID}), null);
            }
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot start trading setup. Setup ID not specified.", (Object[])new Object[0]), null);
        }
        catch (Exception ex) {
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot start setup.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onStop(JSONObject args) {
        JSONObject response = new JSONObject();
        try {
            Object setupIDObj = args.get("SetupID");
            if (setupIDObj != null) {
                int setupID = (Integer)setupIDObj;
                if (this.tradingEngine.getSetupById(setupID).getStatus() == 1) {
                    this.tradingEngine.getSetupById(setupID).stop();
                    response.put("success", (Object)L.t((String)"Trading setup with ID '%s' stopped.", (Object[])new Object[]{setupID}));
                    return response.toString();
                }
                return StrategyServlet.apiErrorJSON((String)L.t((String)"Trading setup with ID '%s' is not running.", (Object[])new Object[]{setupID}), null);
            }
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot stop trading setup. Setup ID not specified.", (Object[])new Object[0]), null);
        }
        catch (Exception ex) {
            return StrategyServlet.apiErrorJSON((String)L.t((String)"Cannot stop setup.", (Object[])new Object[0]), (Throwable)ex);
        }
    }
}

