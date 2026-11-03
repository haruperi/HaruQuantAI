/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessResults
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.RobustnessTests;

import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import java.util.ArrayList;
import java.util.HashMap;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConfidenceLevels {
    private static final Logger Log = LoggerFactory.getLogger(ConfidenceLevels.class);

    public JSONArray print(ResultsGroup rg, Result result, String methodName, DatabankTableView view) {
        JSONArray rows = new JSONArray();
        HashMap statsForConfidenceLevels = (HashMap)result.get(methodName + "_ConfidenceLevelsStats");
        if (statsForConfidenceLevels == null) {
            return rows;
        }
        RobustnessResults rr = (RobustnessResults)result.get("RobustnessOriginalResults");
        if (rr != null) {
            rows.put((Object)this.writeStats(0, rr.getOriginalStats(), view, rg));
            rows.put((Object)this.writeStats(50, (SQStats)statsForConfidenceLevels.get(50), view, rg));
            rows.put((Object)this.writeStats(60, (SQStats)statsForConfidenceLevels.get(60), view, rg));
            rows.put((Object)this.writeStats(70, (SQStats)statsForConfidenceLevels.get(70), view, rg));
            rows.put((Object)this.writeStats(80, (SQStats)statsForConfidenceLevels.get(80), view, rg));
            rows.put((Object)this.writeStats(90, (SQStats)statsForConfidenceLevels.get(90), view, rg));
            rows.put((Object)this.writeStats(92, (SQStats)statsForConfidenceLevels.get(92), view, rg));
            rows.put((Object)this.writeStats(95, (SQStats)statsForConfidenceLevels.get(95), view, rg));
            rows.put((Object)this.writeStats(97, (SQStats)statsForConfidenceLevels.get(97), view, rg));
            rows.put((Object)this.writeStats(98, (SQStats)statsForConfidenceLevels.get(98), view, rg));
            rows.put((Object)this.writeStats(99, (SQStats)statsForConfidenceLevels.get(99), view, rg));
            rows.put((Object)this.writeStats(100, (SQStats)statsForConfidenceLevels.get(100), view, rg));
        }
        return rows;
    }

    private JSONObject writeStats(int level, SQStats stats, DatabankTableView view, ResultsGroup rg) {
        JSONObject obj = new JSONObject();
        JSONArray data = new JSONArray();
        data.put((Object)(level == 0 ? "Original" : level + " %"));
        ArrayList columns = view.columns;
        for (int i = 0; i < columns.size(); ++i) {
            DatabankColumn column = ((DatabankTableColumnEntry)columns.get((int)i)).tableColumn;
            try {
                String formattedValue = column.printHtmlFormatedValue(stats);
                data.put((Object)formattedValue);
                continue;
            }
            catch (Exception e) {
                Log.error("RT column value couldn't be printed.", (Throwable)e);
                data.put((Object)"N/A");
            }
        }
        obj.put("id", (Object)("r" + level));
        obj.put("data", (Object)data);
        return obj;
    }
}

