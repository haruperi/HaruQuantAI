/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.Stockpicker;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockpickerServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(StockpickerServlet.class);
    private static final String LOCK_STOCKPICKERSERVLET = "StockpickerServlet";
    private static IResultsGroupProvider rgProvider;
    public ResultsGroup rg = null;

    public StockpickerServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[0]);
        String text = "Stockpicker log not stored.";
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = this.rg == null ? rgProvider.get(parameterMap, LOCK_STOCKPICKERSERVLET) : this.rg;
            String log = (String)resultsGroup.specialValues().get(SpecialValues.StockpickerLog);
            if (log != null) {
                text = log;
            }
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = StockpickerServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = StockpickerServlet.apiErrorJSON((String)L.t((String)"Getting stockpicker detailed log failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null && this.rg == null) {
                resultsGroup.releaseLock(LOCK_STOCKPICKERSERVLET);
                resultsGroup = null;
                this.rg = null;
            }
        }
        response.put("text", (Object)text);
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

