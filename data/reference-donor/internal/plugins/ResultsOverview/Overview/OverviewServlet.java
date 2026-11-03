/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.OverviewTemplate
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StatsTypeCombination
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.overview.OverviewJsonBuilder
 *  com.strategyquant.tradinglib.results.overview.OverviewTemplates
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.Overview;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.OverviewTemplate;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.overview.OverviewJsonBuilder;
import com.strategyquant.tradinglib.results.overview.OverviewTemplates;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OverviewServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(OverviewServlet.class);
    private static final String LOCK_OVERVIEWSERVLET = "OverviewServlet";
    private static IResultsGroupProvider rgProvider;

    public OverviewServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "ac": {
                return this.onAC(args);
            }
            case "getOverviewContent": {
                return this.onGetOverviewContent(args);
            }
        }
        return OverviewServlet.apiErrorJSON((String)(L.t((String)"Execution failed. Unknown command", (Object[])new Object[0]) + " '" + command + "'."), null);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetOverviewContent(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        String htmlContents = null;
        ResultsGroup report = null;
        String resultKey = "Portfolio";
        byte direction = 0;
        byte sampleType = 127;
        String templateName = "SQDefaultWithPortfolio";
        try {
            resultKey = this.tryGetParam(parameterMap, "resultKey")[0];
            direction = Byte.parseByte(this.tryGetParam(parameterMap, "direction")[0]);
            sampleType = Byte.parseByte(this.tryGetParam(parameterMap, "sampleType")[0]);
            templateName = this.tryGetParam(parameterMap, "template")[0];
            report = rgProvider.get(parameterMap, LOCK_OVERVIEWSERVLET);
            OverviewTemplate template = (OverviewTemplate)OverviewTemplates.getInstance().findClassByName(templateName);
            htmlContents = template.drawValues(report, resultKey, new StatsTypeCombination(direction, 10, sampleType));
        }
        catch (Exception ex) {
            response.put("error", (Object)("Cannot get overview content - " + ex.getMessage()));
            String string = response.toString();
            return string;
        }
        finally {
            if (report != null) {
                report.releaseLock(LOCK_OVERVIEWSERVLET);
            }
        }
        if (htmlContents == null) {
            return OverviewServlet.apiErrorJSON((String)L.t((String)"Cannot get overview content.", (Object[])new Object[0]), null);
        }
        response.put("overviewHtml", (Object)htmlContents);
        response.put("success", (Object)L.t((String)"Html code generated.", (Object[])new Object[0]));
        return response.toString();
    }

    public JSONArray getTemplates() throws Exception {
        JSONArray templates = new JSONArray();
        for (OverviewTemplate plugin : OverviewTemplates.getInstance().getAvailableClasses()) {
            if (plugin.getClass().getSimpleName().equals("AWSharedDefault")) continue;
            templates.put((Object)new JSONObject().put("value", (Object)plugin.getClass().getSimpleName()).put("name", (Object)plugin.getName()));
        }
        return templates;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onAC(Map<String, String[]> parameterMap) {
        ResultsGroup report = null;
        try {
            String resultKey = this.tryGetParam(parameterMap, "resultKey")[0];
            byte direction = Byte.parseByte(this.tryGetParam(parameterMap, "direction")[0]);
            byte sampleType = Byte.parseByte(this.tryGetParam(parameterMap, "sampleType")[0]);
            report = rgProvider.get(parameterMap, LOCK_OVERVIEWSERVLET);
            StatsTypeCombination combination = new StatsTypeCombination(direction, 10, sampleType);
            String string = OverviewJsonBuilder.build((ResultsGroup)report, (String)resultKey, (StatsTypeCombination)combination).toString();
            return string;
        }
        catch (Exception ex) {
            String string = new JSONObject().put("error", (Object)("Cannot get overview stats - " + ex.getMessage())).toString();
            return string;
        }
        finally {
            if (report != null) {
                report.releaseLock(LOCK_OVERVIEWSERVLET);
            }
        }
    }
}

