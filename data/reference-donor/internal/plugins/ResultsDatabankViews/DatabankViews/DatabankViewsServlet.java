/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.databank.DatabankViewsManager
 *  com.strategyquant.tradinglib.databank.RecentColumns
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.DatabankViews;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.databank.DatabankViewsManager;
import com.strategyquant.tradinglib.databank.RecentColumns;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankViewsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DatabankViewsServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "getColumns": {
                return this.onGetColumns();
            }
            case "updateRecentColumns": {
                return this.onUpdateRecentColumns(args);
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
        return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onGetColumns() {
        JSONObject response = new JSONObject();
        JSONArray columnsArray = new JSONArray();
        JSONArray recentColumnsArray = new JSONArray();
        List columns = DatabankColumns.get().getAvailableClasses();
        for (Object column : columns) {
            JSONObject columnObj = new JSONObject();
            columnObj.put("name", (Object)column.getName());
            columnObj.put("class", (Object)column.getClass().getSimpleName());
            columnObj.put("type", (Object)column.getType());
            columnsArray.put((Object)columnObj);
        }
        for (Object column : RecentColumns.getRecentCols()) {
            recentColumnsArray.put(column);
        }
        response.put("columns", (Object)columnsArray);
        response.put("recentColumns", (Object)recentColumnsArray);
        response.put("success", (Object)L.t((String)"Columns listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateRecentColumns(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        JSONArray recentColumnsArray = new JSONArray();
        try {
            String lastUsedCols = this.tryGetParam(parameterMap, "lastUsedCols")[0];
            RecentColumns.updateRecentCols((String[])lastUsedCols.split(";"));
            for (String column : RecentColumns.getRecentCols()) {
                recentColumnsArray.put((Object)column);
            }
        }
        catch (Exception e) {
            return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Cannot update recent columns.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("recentColumns", (Object)recentColumnsArray);
        response.put("success", (Object)L.t((String)"Recent columns updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetViews() {
        JSONObject response = new JSONObject();
        response.put("databankViews", (Object)DatabankViewsManager.getInstance().toJSON());
        response.put("success", (Object)L.t((String)"Databank views broadcasted", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddView(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(parameterMap, "viewXML")[0];
            DatabankTableView newView = DatabankViewsManager.getInstance().addView(xmlConfig);
            try {
                String projectName = this.tryGetParam(parameterMap, "project")[0];
                String databankName = this.tryGetParam(parameterMap, "databank")[0];
                Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
                databank.setView(newView);
            }
            catch (Exception exception) {
                // empty catch block
            }
            this.sendDataUpdate();
        }
        catch (Exception e) {
            return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Cannot add view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"View added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateView(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(parameterMap, "viewXML")[0];
            DatabankTableView updatedView = DatabankViewsManager.getInstance().updateView(xmlConfig);
            for (SQProject project : ProjectEngine.list()) {
                for (Databank databank : project.getDatabanks().list()) {
                    if (!databank.getView().name.equals(updatedView.name)) continue;
                    databank.setView(updatedView);
                }
            }
            this.sendDataUpdate();
        }
        catch (Exception e) {
            return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Cannot update view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"View updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveView(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(parameterMap, "name")[0];
            for (SQProject project : ProjectEngine.list()) {
                for (Databank databank : project.getDatabanks().list()) {
                    if (!databank.getView().name.equals(name)) continue;
                    return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Cannot remove view '%s', because it is still used by some databanks.", (Object[])new Object[]{name}), null);
                }
            }
            DatabankViewsManager.getInstance().removeView(name);
            this.sendDataUpdate();
        }
        catch (Exception e) {
            return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Error while removing view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"View removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onChangeView(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        String dbName = null;
        String viewName = null;
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            dbName = this.tryGetParam(parameterMap, "databankName")[0];
            viewName = this.tryGetParam(parameterMap, "viewName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            Databank databank = (Databank)project.getDatabanks().get((Object)dbName);
            DatabankTableView view = DatabankViewsManager.getInstance().getView(viewName);
            databank.setView(view);
        }
        catch (Exception e) {
            return DatabankViewsServlet.apiErrorJSON((String)L.t((String)"Error while changing view.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"View for databank '%s' changed to '%s'.", (Object[])new Object[]{dbName, viewName}));
        return response.toString();
    }

    private void sendDataUpdate() {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getDatabankViews(), (String[])new String[]{"SQUANT"});
        }
        catch (Exception e) {
            Log.error("Cannot send websocket data update. ", (Throwable)e);
        }
    }
}

