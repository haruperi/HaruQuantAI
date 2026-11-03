/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.correlation.DatabankCorrelationFilter
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Databank.impl.FilterByCorrelation;

import com.strategyquant.tradinglib.correlation.DatabankCorrelationFilter;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankFilterByCorrelationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DatabankFilterByCorrelationServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "filter": {
                return this.onFilter(args);
            }
        }
        return DatabankFilterByCorrelationServlet.apiErrorJSON((String)("Execution failed. Unknown command '" + command + "'."), null);
    }

    private String onFilter(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String databankName = this.tryGetParam(args, "databankName")[0];
            int period = Integer.parseInt(this.tryGetParam(args, "period")[0]);
            double maxCorrelation = Double.parseDouble(this.tryGetParam(args, "maxCorrelation")[0]);
            int removedCount = DatabankCorrelationFilter.filter((String)projectName, (String)databankName, (int)period, (double)maxCorrelation).size();
            response.put("success", (Object)("Strategies filtered, " + removedCount + " strategies removed."));
            return response.toString();
        }
        catch (Exception e) {
            Log.error("Error while filtering strategies by correlation", (Throwable)e);
            response.put("error", (Object)("Filtering failed - " + e.getMessage()));
            return response.toString();
        }
    }
}

