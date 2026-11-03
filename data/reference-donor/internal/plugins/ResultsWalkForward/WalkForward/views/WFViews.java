/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.WalkForward.views;

import com.strategyquant.lib.L;
import com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WFViews {
    private static final Logger Log = LoggerFactory.getLogger(WFViews.class);
    private WFViewsManager manager;

    public WFViews(String viewsFolder) {
        this.manager = new WFViewsManager(viewsFolder);
    }

    public String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "viewsGetColumns": {
                return this.onGetColumns();
            }
            case "viewsGetViews": {
                return this.onGetViews();
            }
            case "viewsAddView": {
                return this.onAddView(args);
            }
            case "viewsUpdateView": {
                return this.onUpdateView(args);
            }
            case "viewsRemoveView": {
                return this.onRemoveView(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onGetColumns() {
        JSONObject response = new JSONObject();
        JSONArray columnsArray = new JSONArray();
        List columns = DatabankColumns.get().getAvailableClasses();
        for (DatabankColumn column : columns) {
            JSONObject columnObj = new JSONObject();
            columnObj.put("name", (Object)column.getName());
            columnObj.put("class", (Object)column.getClass().getSimpleName());
            columnsArray.put((Object)columnObj);
        }
        response.put("columns", (Object)columnsArray);
        response.put("success", (Object)L.t((String)"Columns listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetViews() throws Exception {
        JSONObject response = new JSONObject();
        JSONArray viewsArray = new JSONArray();
        try {
            for (String name : this.manager.getViews().keySet()) {
                JSONObject viewObj = new JSONObject();
                JSONArray columnsArray = new JSONArray();
                DatabankTableView view = this.manager.getView(name);
                viewObj.put("name", (Object)name);
                for (DatabankTableColumnEntry columnEntry : view.columns) {
                    if (columnEntry.tableColumn == null) continue;
                    try {
                        JSONObject columnObj = new JSONObject();
                        columnObj.put("entryName", (Object)columnEntry.tableColumn.getName());
                        columnObj.put("columnName", (Object)columnEntry.tableColumn.getName());
                        columnObj.put("sampleType", (int)columnEntry.sampleType);
                        columnObj.put("class", (Object)columnEntry.tableColumn.getClass().getSimpleName());
                        columnObj.put("width", columnEntry.tableColumn.getWidth());
                        columnObj.put("type", (Object)columnEntry.tableColumn.getType());
                        columnsArray.put((Object)columnObj);
                    }
                    catch (Exception e) {
                        Log.error("Cannot load view", (Throwable)e);
                    }
                }
                viewObj.put("columns", (Object)columnsArray);
                viewsArray.put((Object)viewObj);
            }
            response.put("views", (Object)viewsArray);
        }
        catch (Exception e) {
            throw new Exception("Cannot get list of views.", e);
        }
        response.put("success", (Object)L.t((String)"Views listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddView(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(args, "viewXML")[0];
            this.manager.addView(xmlConfig);
        }
        catch (Exception e) {
            throw new Exception("Cannot add view.", e);
        }
        response.put("success", (Object)L.t((String)"View added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateView(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(args, "viewXML")[0];
            this.manager.updateView(xmlConfig);
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Cannot update the view.", (Object[])new Object[0]), e);
        }
        response.put("success", (Object)L.t((String)"View updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveView(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            this.manager.removeView(name);
        }
        catch (Exception e) {
            throw new Exception("Error while removing view.", e);
        }
        response.put("success", (Object)L.t((String)"View removed.", (Object[])new Object[0]));
        return response.toString();
    }

    protected String[] tryGetParam(Map<String, String[]> params, String parameter) throws Exception {
        if (!params.containsKey(parameter)) {
            throw new Exception("Parameter '" + parameter + "' is missing.");
        }
        return params.get(parameter);
    }

    public DatabankTableView getViewByName(String name) throws Exception {
        return this.manager.getView(name);
    }
}

