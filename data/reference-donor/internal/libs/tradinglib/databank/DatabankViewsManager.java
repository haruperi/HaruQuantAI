/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import java.io.File;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankViewsManager {
    private static final Logger Log = LoggerFactory.getLogger(DatabankViewsManager.class);
    private static Map<String, DatabankTableView> views = new TreeMap<String, DatabankTableView>();
    private static final String viewsFolder = MainApp.getDataPath() + "/user/settings/views/databanks";
    private static final String fileExtension = "vw";
    private static DatabankViewsManager instance;

    public static DatabankViewsManager getInstance() {
        if (instance == null) {
            instance = new DatabankViewsManager();
        }
        return instance;
    }

    private DatabankViewsManager() {
        this.loadViews();
    }

    private void loadViews() {
        File file = new File(viewsFolder);
        if (!file.exists()) {
            file.mkdirs();
        } else {
            File[] fileArray = file.listFiles();
            if (fileArray != null) {
                for (File file2 : fileArray) {
                    try {
                        String string = SQUtils.fileToString((File)file2);
                        this._addView(string, false);
                    }
                    catch (Exception exception) {
                        Log.error("Cannot load databank view from file '" + file2.getName() + "'");
                    }
                }
            }
        }
        views.put("Default - Main data", this.createDefaultView("Default - Main data", "main"));
        views.put("Default - Portfolio", this.createDefaultView("Default - Portfolio", "portfolio"));
    }

    public Map<String, DatabankTableView> getViews() {
        return views;
    }

    public JSONArray toJSON() {
        JSONArray jSONArray = new JSONArray();
        DatabankTableView databankTableView = views.get("Default - Main data");
        JSONObject jSONObject = this.getViewObject("Default - Main data", databankTableView);
        jSONArray.put((Object)jSONObject);
        for (String string : views.keySet()) {
            if (string.equals("Default - Main data")) continue;
            databankTableView = views.get(string);
            jSONObject = this.getViewObject(string, databankTableView);
            jSONArray.put((Object)jSONObject);
        }
        return jSONArray;
    }

    public JSONObject getViewObject(String string, DatabankTableView databankTableView) {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        jSONObject.put("name", (Object)string);
        for (DatabankTableColumnEntry databankTableColumnEntry : databankTableView.columns) {
            try {
                JSONObject jSONObject2 = new JSONObject();
                jSONObject2.put("columnName", (Object)databankTableColumnEntry.tableColumn.getName());
                jSONObject2.put("class", (Object)databankTableColumnEntry.tableColumn.getClass().getSimpleName());
                jSONObject2.put("resultType", (Object)databankTableColumnEntry.resultType);
                jSONObject2.put("sampleType", (int)databankTableColumnEntry.sampleType);
                jSONObject2.put("direction", (int)databankTableColumnEntry.direction);
                jSONObject2.put("plType", (int)databankTableColumnEntry.plType);
                jSONObject2.put("confidenceLevel", databankTableColumnEntry.confidenceLevel);
                jSONObject2.put("market", databankTableColumnEntry.market);
                byte by = databankTableColumnEntry.subresult;
                jSONObject2.put("subresult", (int)by);
                jSONObject2.put("showMainResult", databankTableColumnEntry.showMainResult);
                jSONObject2.put("name", (Object)databankTableColumnEntry.getColumnEntryName());
                jSONObject2.put("width", databankTableColumnEntry.tableColumn.getWidth());
                String string2 = databankTableColumnEntry.tableColumn.getType();
                if (by == 31 || by == 32) {
                    string2 = "Decimal2Pct";
                }
                jSONObject2.put("type", (Object)string2);
                jSONArray.put((Object)jSONObject2);
            }
            catch (Exception exception) {
                Log.error("Cannot load view", (Throwable)exception);
            }
        }
        jSONObject.put("columns", (Object)jSONArray);
        return jSONObject;
    }

    public DatabankTableView getView(String string) throws Exception {
        if (views.containsKey(string)) {
            return views.get(string);
        }
        throw new Exception(L.t((String)"View with name '%s' doesn't exist.", (Object[])new Object[]{string}));
    }

    public DatabankTableView addView(String string) throws Exception {
        return this._addView(string, true);
    }

    private DatabankTableView _addView(String string, boolean bl) throws Exception {
        DatabankTableView databankTableView = this.getTableView(string);
        if (views.containsKey(databankTableView.name)) {
            throw new Exception(L.t((String)"Databank view with name '%s' already exists.", (Object[])new Object[]{databankTableView.name}));
        }
        views.put(databankTableView.name, databankTableView);
        if (bl) {
            File file = new File(this.getViewFilePath(databankTableView.name));
            SQUtils.stringToFile((File)file, (String)string);
        }
        return databankTableView;
    }

    public DatabankTableView updateView(String string) throws Exception {
        File file;
        boolean bl;
        DatabankTableView databankTableView = this.getTableView(string);
        Element element = XMLUtil.stringToElement((String)string);
        String string2 = element.getAttributeValue("originalName");
        String string3 = element.getAttributeValue("name");
        boolean bl2 = bl = string2 != null && !string2.equals(string3);
        if (bl) {
            views.remove(string2);
            file = new File(this.getViewFilePath(string2));
            file.delete();
        }
        if (!bl && !views.containsKey(databankTableView.name)) {
            throw new Exception(L.t((String)"Databank view with name '%s' doesn't exist.", (Object[])new Object[]{databankTableView.name}));
        }
        views.put(databankTableView.name, databankTableView);
        file = new File(this.getViewFilePath(databankTableView.name));
        SQUtils.stringToFile((File)file, (String)string);
        return databankTableView;
    }

    public void removeView(String string) throws Exception {
        if (views.containsKey(string)) {
            views.remove(string);
            File file = new File(this.getViewFilePath(string));
            if (!file.delete()) {
                throw new Exception(L.t((String)"Cannot delete file '%s'", (Object[])new Object[]{file.getName()}));
            }
        } else {
            throw new Exception(L.t((String)"Databank view with name '%s' doesn't exist.", (Object[])new Object[]{string}));
        }
    }

    public DatabankTableView createDefaultView(String string, String string2) {
        DatabankTableView databankTableView = new DatabankTableView();
        databankTableView.name = string;
        String[] stringArray = new String[]{"Fitness", "Symbol", "TimeFrame", "NetProfit", "MiniEquityChart", "NumberOfTrades", "PctWins", "ProfitFactor", "SharpeRatio", "RExpectancy", "AnnualPctReturn", "Stability", "Symmetry", "Drawdown", "WinLossRatio", "ReturnDDRatio", "AnnualPctReturnDDRatio", "AvgWin", "AvgLoss", "AvgBarsWin", "AvgBarsLoss", "AvgBarsInTrade", "Exposure"};
        List list = DatabankColumns.get().cloneAvailableClasses();
        block0: for (String string3 : stringArray) {
            for (DatabankColumn databankColumn : list) {
                if (!databankColumn.getClass().getSimpleName().equals(string3)) continue;
                databankTableView.columns.add(new DatabankTableColumnEntry(databankColumn, string2, 0, 10, 10));
                continue block0;
            }
        }
        block2: for (String string3 : stringArray = new String[]{"Fitness", "NetProfit", "MiniEquityChart", "NumberOfTrades", "PctWins", "ProfitFactor", "SharpeRatio", "RExpectancy", "AnnualPctReturn", "Stability", "Symmetry", "Drawdown", "WinLossRatio", "ReturnDDRatio", "AnnualPctReturnDDRatio", "AvgWin", "AvgLoss", "AvgBarsWin", "AvgBarsLoss", "AvgBarsInTrade", "Exposure"}) {
            for (DatabankColumn databankColumn : list) {
                if (!databankColumn.getClass().getSimpleName().equals(string3)) continue;
                databankTableView.columns.add(new DatabankTableColumnEntry(databankColumn, string2, 0, 10, 20));
                continue block2;
            }
        }
        return databankTableView;
    }

    private DatabankTableView getTableView(String string) throws Exception {
        DatabankTableView databankTableView = new DatabankTableView();
        Element element = XMLUtil.stringToElement((String)SQUtils.removeUTF8BOM((String)string));
        databankTableView.setFromXML(element);
        return databankTableView;
    }

    private String getViewFilePath(String string) {
        return viewsFolder + "/" + string + "." + fileExtension;
    }
}

