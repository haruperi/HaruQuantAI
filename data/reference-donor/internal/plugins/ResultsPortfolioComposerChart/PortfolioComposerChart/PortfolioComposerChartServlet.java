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
package com.strategyquant.plugin.Results.impl.PortfolioComposerChart;

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

public class PortfolioComposerChartServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioComposerChartServlet.class);
    private static final String LOCK_KEY = "PortfolioComposerChart";
    private static IResultsGroupProvider rgProvider;
    public ResultsGroup rg = null;

    public PortfolioComposerChartServlet(IResultsGroupProvider provider) {
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
        String text = "PortfolioComposer chart not stored.";
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = this.rg == null ? rgProvider.get(parameterMap, LOCK_KEY) : this.rg;
            String chart = (String)resultsGroup.specialValues().get(SpecialValues.PortfolioComposerChart);
            if (chart != null) {
                text = chart;
            }
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = PortfolioComposerChartServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = PortfolioComposerChartServlet.apiErrorJSON((String)L.t((String)"Getting PortfolioComposer chart failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null && this.rg == null) {
                resultsGroup.releaseLock(LOCK_KEY);
                resultsGroup = null;
                this.rg = null;
            }
        }
        response.put("chart", (Object)text);
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

