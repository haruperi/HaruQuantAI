/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.simulator;

import com.strategyquant.lib.L;
import org.json.JSONArray;
import org.json.JSONObject;

public class Engines {
    private String[] langs = new String[]{L.tsq((String)"MetaTrader4"), L.tsq((String)"MetaTrader5 (netted)"), L.tsq((String)"MetaTrader5 (hedged)"), L.tsq((String)"Tradestation"), L.tsq((String)"MultiCharts"), L.tsq((String)"JForex")};
    public static final String MetaTrader4Name = "MetaTrader4";
    public static final int MetaTrader4 = -659455871;
    public static final String MetaTrader5NettedName = "MetaTrader5 (netted)";
    public static final int MetaTrader5Netted = 1441180233;
    public static final String MetaTrader5HedgedName = "MetaTrader5 (hedged)";
    public static final int MetaTrader5Hedged = 395961824;
    public static final String TradestationName = "Tradestation";
    public static final int Tradestation = 56756755;
    public static final String MultiChartsName = "MultiCharts";
    public static final int MultiCharts = 938213070;
    public static final String JForexName = "JForex";
    public static final int JForex = 1949519549;
    public static final String StockpickerName = "Stockpicker";
    public static final int Stockpicker = 1316847364;
    public static final String StockpickerSingleAssetName = "Single-asset cloud strategy";
    public static final int StockpickerSingleAsset = -1816889229;

    public static JSONArray toJSON() {
        JSONArray jSONArray = new JSONArray().put((Object)MetaTrader4Name).put((Object)MetaTrader5NettedName).put((Object)MetaTrader5HedgedName).put((Object)TradestationName).put((Object)MultiChartsName).put((Object)JForexName);
        jSONArray.put((Object)StockpickerName);
        jSONArray.put((Object)StockpickerSingleAssetName);
        return jSONArray;
    }

    public static JSONObject toJSONKeys() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put(StockpickerName, (Object)"SP");
        jSONObject.put(StockpickerSingleAssetName, (Object)"SA");
        jSONObject.put(MetaTrader4Name, (Object)"MT4");
        jSONObject.put(MetaTrader5NettedName, (Object)"MT5");
        jSONObject.put(MetaTrader5HedgedName, (Object)"MT5");
        jSONObject.put(TradestationName, (Object)"TS");
        jSONObject.put(MultiChartsName, (Object)"MC");
        jSONObject.put(JForexName, (Object)"JF");
        return jSONObject;
    }

    public static String getEngineKey(String string) {
        if (string == null) {
            return null;
        }
        switch (string) {
            case "MetaTrader4": {
                return "MT4";
            }
            case "MetaTrader5 (hedged)": {
                return "MT5";
            }
            case "MetaTrader5 (netted)": {
                return "MT5";
            }
            case "Tradestation": {
                return "TS";
            }
            case "MultiCharts": {
                return "MC";
            }
            case "JForex": {
                return "JF";
            }
            case "Stockpicker": {
                return "SP";
            }
            case "Single-asset cloud strategy": {
                return "SA";
            }
        }
        return null;
    }

    public static int getEngine(String string) {
        if (string == null) {
            return -1;
        }
        switch (string) {
            case "MetaTrader4": {
                return -659455871;
            }
            case "MetaTrader5 (hedged)": {
                return 395961824;
            }
            case "MetaTrader5 (netted)": {
                return 1441180233;
            }
            case "Tradestation": {
                return 56756755;
            }
            case "MultiCharts": {
                return 938213070;
            }
            case "JForex": {
                return 1949519549;
            }
            case "Stockpicker": {
                return 1316847364;
            }
            case "Single-asset cloud strategy": {
                return -1816889229;
            }
        }
        return -1;
    }

    public static String getEngineName(int n) {
        switch (n) {
            case -659455871: {
                return MetaTrader4Name;
            }
            case 395961824: {
                return MetaTrader5HedgedName;
            }
            case 1441180233: {
                return MetaTrader5NettedName;
            }
            case 56756755: {
                return TradestationName;
            }
            case 938213070: {
                return MultiChartsName;
            }
            case 1949519549: {
                return JForexName;
            }
            case 1316847364: {
                return StockpickerName;
            }
            case -1816889229: {
                return StockpickerSingleAssetName;
            }
        }
        return null;
    }

    public static JSONArray list() {
        JSONArray jSONArray = new JSONArray();
        jSONArray.put((Object)new JSONObject().put("name", (Object)MetaTrader4Name).put("value", (Object)MetaTrader4Name));
        jSONArray.put((Object)new JSONObject().put("name", (Object)MetaTrader5NettedName).put("value", (Object)MetaTrader5NettedName));
        jSONArray.put((Object)new JSONObject().put("name", (Object)MetaTrader5HedgedName).put("value", (Object)MetaTrader5HedgedName));
        jSONArray.put((Object)new JSONObject().put("name", (Object)TradestationName).put("value", (Object)TradestationName));
        jSONArray.put((Object)new JSONObject().put("name", (Object)MultiChartsName).put("value", (Object)MultiChartsName));
        jSONArray.put((Object)new JSONObject().put("name", (Object)JForexName).put("value", (Object)JForexName));
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"AlgoCloud Stockpicker")).put("value", (Object)StockpickerName));
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"AlgoCloud Single-asset")).put("value", (Object)StockpickerSingleAssetName));
        return jSONArray;
    }

    public static boolean isTradestationEngine(int n) {
        return n == 56756755 || n == 938213070;
    }

    public static boolean isAWCloudEngine(int n) {
        return n == 1316847364 || n == -1816889229;
    }

    public static boolean isStandardEngine(int n) {
        return !Engines.isAWCloudEngine(n);
    }
}

