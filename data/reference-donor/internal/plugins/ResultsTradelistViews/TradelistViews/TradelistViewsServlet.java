/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.TradelistColumn
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.tradelist.TradelistColumnsList
 *  com.strategyquant.tradinglib.tradelist.TradelistTableView
 *  com.strategyquant.tradinglib.tradelist.TradelistViewsManager
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.TradelistViews;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.TradelistColumn;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.tradelist.TradelistColumnsList;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import com.strategyquant.tradinglib.tradelist.TradelistViewsManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradelistViewsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(TradelistViewsServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "getColumns": {
                return this.onGetColumns();
            }
            case "getViews": {
                return this.onGetViews();
            }
            case "addView": {
                return this.onAddView(args);
            }
            case "updateView": {
                return this.onUpdateView(args);
            }
            case "removeView": {
                return this.onRemoveView(args);
            }
            case "changeView": {
                return this.onChangeView(args);
            }
        }
        return TradelistViewsServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onGetColumns() {
        JSONObject response = new JSONObject();
        response.put("columns", (Object)this.getColumns());
        response.put("success", (Object)L.t((String)"Columns listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetViews() {
        JSONObject response = new JSONObject();
        response.put("tradelistViews", (Object)WSDataObjects.getTradelistViews().getDataArray());
        response.put("success", (Object)L.t((String)"Views listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray getColumns() {
        JSONArray columnsArray = new JSONArray();
        List columns = TradelistColumnsList.get().getAvailableClasses();
        for (TradelistColumn column : columns) {
            JSONObject columnObj = new JSONObject();
            columnObj.put("name", (Object)column.getName());
            columnObj.put("class", (Object)column.getClass().getSimpleName());
            columnObj.put("type", (Object)column.getType());
            columnObj.put("fontBold", column.isFontBold());
            columnsArray.put((Object)columnObj);
        }
        return columnsArray;
    }

    private void sendWSUpdate() {
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getTradelistViews(), (String[])new String[]{"SQUANT", "BUILDER", "OPTIMIZER", "RETESTER", "TASKMANAGER", "RESULTS"});
    }

    private String onAddView(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(args, "viewXML")[0];
            TradelistTableView tradelistView = TradelistViewsManager.getInstance().addView(xmlConfig, true);
            if (tradelistView != null && tradelistView.name.equals(tradelistView.name)) {
                MainApp.settings().set("tradelistView", tradelistView.name);
            }
            this.sendWSUpdate();
        }
        catch (Exception e) {
            return TradelistViewsServlet.apiErrorJSON((String)L.t((String)"Cannot add view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"View added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateView(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(args, "viewXML")[0];
            TradelistTableView updatedView = TradelistViewsManager.getInstance().updateView(xmlConfig);
            TradelistTableView tradelistView = TradelistViewsManager.getInstance().getSelectedTradelistView();
            if (tradelistView != null && updatedView.name.equals(tradelistView.name)) {
                MainApp.settings().set("tradelistView", updatedView.name);
            }
            this.sendWSUpdate();
        }
        catch (Exception e) {
            return TradelistViewsServlet.apiErrorJSON((String)L.t((String)"Cannot update tradelist view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Tradelist view updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveView(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            TradelistViewsManager.getInstance().removeView(name);
            TradelistTableView tradelistView = TradelistViewsManager.getInstance().getSelectedTradelistView();
            String currentView = tradelistView.name;
            if (currentView.equals(name)) {
                TradelistTableView view = TradelistViewsManager.getInstance().getView("Default");
                MainApp.settings().set("tradelistView", view.name);
            }
            this.sendWSUpdate();
        }
        catch (Exception e) {
            return TradelistViewsServlet.apiErrorJSON((String)L.t((String)"Error while removing view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"View removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onChangeView(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        String viewName = null;
        try {
            viewName = this.tryGetParam(args, "viewName")[0];
            TradelistTableView view = TradelistViewsManager.getInstance().getView(viewName);
            MainApp.settings().set("tradelistView", view.name);
        }
        catch (Exception e) {
            return TradelistViewsServlet.apiErrorJSON((String)L.t((String)"Error while changing view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Tradelist view changed to '%s'.", (Object[])new Object[]{viewName}));
        return response.toString();
    }
}

