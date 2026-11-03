/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.RobustnessTests;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import java.util.ArrayList;
import java.util.HashMap;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RiskOfRuins {
    private static final Logger Log = LoggerFactory.getLogger(RiskOfRuins.class);

    public JSONArray print(Result result, String methodName, int level, DatabankTableView view) {
        JSONArray rows = new JSONArray();
        HashMap riskOfRuins = (HashMap)result.get(String.format(methodName + "_RiskOfRuins%d", level));
        if (riskOfRuins == null) {
            return rows;
        }
        SettingsMap settings = result.getSettings();
        double initialCapital = settings.getDouble("InitialDeposit", 10000.0);
        int i = 0;
        for (double initialCapitalVariant : MonteCarloCrossCheckMethod.InitialCapitalVariants) {
            rows.put((Object)this.writeStats(i, initialCapitalVariant, initialCapital, (SQStats)riskOfRuins.get(initialCapitalVariant), view));
            ++i;
        }
        return rows;
    }

    private JSONObject writeStats(int row, double initialCapitalVariant, double initialCapital, SQStats stats, DatabankTableView view) {
        JSONObject obj = new JSONObject();
        JSONArray data = new JSONArray();
        data.put(initialCapital * initialCapitalVariant);
        data.put((Object)(SQUtils.d2((double)stats.getDouble("RiskOfRuin")) + " %"));
        data.put((Object)(SQUtils.d2((double)stats.getDouble("ProfitProbability")) + " %"));
        ArrayList columns = view.columns;
        for (int i = 0; i < columns.size(); ++i) {
            DatabankColumn column = ((DatabankTableColumnEntry)columns.get((int)i)).tableColumn;
            try {
                String formattedValue = column.printValue(stats);
                data.put((Object)formattedValue);
                continue;
            }
            catch (Exception e) {
                Log.error("RT column value couldn't be printed.", (Throwable)e);
                data.put((Object)"N/A");
            }
        }
        obj.put("id", (Object)("r" + row));
        obj.put("data", (Object)data);
        return obj;
    }
}

