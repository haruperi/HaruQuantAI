/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.results.IResultPlugin;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataItemsGenerator {
    private static final Logger Log = LoggerFactory.getLogger(DataItemsGenerator.class);

    /*
     * WARNING - void declaration
     */
    public static void get(JSONObject jSONObject, ResultsGroup resultsGroup) throws Exception {
        Object object;
        List<String> list = resultsGroup.getResultKeys();
        if (list == null) {
            throw new Exception("Cannot get ResultsGroup keys");
        }
        WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
        JSONArray jSONArray = new JSONArray();
        for (String object2 : list) {
            if (object2.startsWith("WF:") && walkForwardMatrixResult != null) continue;
            jSONArray.put((Object)object2);
        }
        if (walkForwardMatrixResult != null) {
            if (walkForwardMatrixResult.isMatrix()) {
                for (int i = walkForwardMatrixResult.start2; i <= walkForwardMatrixResult.stop2; i += walkForwardMatrixResult.increment2) {
                    void var6_9;
                    int j = walkForwardMatrixResult.start1;
                    while (var6_9 <= walkForwardMatrixResult.stop1) {
                        Object object2 = walkForwardMatrixResult.getWFResult((int)var6_9, i);
                        jSONArray.put((Object)((WalkForwardResult)object2).getResultKeyName());
                        var6_9 += walkForwardMatrixResult.increment1;
                    }
                }
            } else {
                object = walkForwardMatrixResult.getResultList().get(0);
                jSONArray.put((Object)((WalkForwardResult)object).getResultKeyName());
            }
        }
        jSONObject.put("dataItems", (Object)jSONArray);
        object = new JSONArray();
        for (Object object2 : SQPluginManager.getPlugins(IResultPlugin.class)) {
            try {
                if (object2.containsResult(resultsGroup)) {
                    continue;
                }
            }
            catch (Exception exception) {
                Log.error("Error while checking if strategy contains result '" + object2.getClass().getSimpleName() + "'. Exc.", (Throwable)exception);
            }
            object.put((Object)object2.getKey());
        }
        jSONObject.put("noResultItems", object);
        jSONObject.put("isPortfolio", resultsGroup.isPortfolio());
        jSONObject.put("resultInfo", (Object)DataItemsGenerator.getResultInfo(resultsGroup));
        jSONObject.put("isStockpicker", resultsGroup.isStockpickerStrategy());
        jSONObject.put("resultTypes", (Object)DataItemsGenerator.getResultTypes(resultsGroup));
    }

    private static JSONArray getResultTypes(ResultsGroup resultsGroup) throws Exception {
        JSONArray jSONArray = new JSONArray();
        byte[] byArray = SampleTypes.list();
        for (int i = 0; i < byArray.length; ++i) {
            if (resultsGroup.mainResult().statsOrNull((byte)0, (byte)10, byArray[i]) == null) continue;
            jSONArray.put((int)byArray[i]);
        }
        return jSONArray;
    }

    public static String getResultInfo(ResultsGroup resultsGroup) {
        try {
            SettingsMap settingsMap = resultsGroup.specialValues();
            String string = resultsGroup.mainResult().getString(SpecialValues.Symbol, "N/A");
            String string2 = resultsGroup.mainResult().getString(SpecialValues.Timeframe, "N/A");
            String string3 = SQTime.toString((long)settingsMap.getLong(SpecialValues.HistoryFrom), (String)"yyyy.MM.dd");
            String string4 = SQTime.toString((long)settingsMap.getLong(SpecialValues.HistoryTo), (String)"yyyy.MM.dd");
            return string + ", " + string2 + ", " + string3 + " - " + string4;
        }
        catch (Exception exception) {
            return "N/A";
        }
    }
}

