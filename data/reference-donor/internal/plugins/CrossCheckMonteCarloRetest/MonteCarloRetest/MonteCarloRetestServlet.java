/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.MonteCarloRetest
 *  com.strategyquant.tradinglib.PrecachedRequest
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckMethod
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.montecarlo.retest.MonteCarloRetestList
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.MonteCarloRetest;
import com.strategyquant.tradinglib.PrecachedRequest;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.montecarlo.retest.MonteCarloRetestList;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MonteCarloRetestServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(MonteCarloRetestServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList();
            }
            case "fitnessList": {
                return this.onFitnessList();
            }
            case "fitnessGetConfidenceLevels": {
                return this.onFitnessGetConfidenceLevels();
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    @PrecachedRequest(relativeURL="/monteCarloRetest/list")
    private String onList() throws Exception {
        JSONObject response = new JSONObject();
        JSONArray data = new JSONArray();
        List methods = MonteCarloRetestList.get().getAvailableClasses();
        for (int i = 0; i < methods.size(); ++i) {
            MonteCarloRetest method = (MonteCarloRetest)methods.get(i);
            JSONObject row = new JSONObject();
            JSONArray rowData = new JSONArray();
            rowData.put(false);
            rowData.put((Object)method.printFormatedName());
            JSONObject methodObj = new JSONObject();
            methodObj.put("display", (Object)method.getFormatedName());
            methodObj.put("config", (Object)XMLUtil.elementToString((Element)method.getXML()));
            row.put("userdata", (Object)methodObj);
            row.put("id", (Object)method.getClass().getSimpleName());
            row.put("data", (Object)rowData);
            data.put((Object)row);
        }
        response.put("rows", (Object)data);
        response.put("success", (Object)L.t((String)"RT methods listed.", (Object[])new Object[0]));
        return response.toString();
    }

    @PrecachedRequest(relativeURL="/monteCarloRetest/fitnessGetConfidenceLevels")
    private String onFitnessGetConfidenceLevels() throws Exception {
        JSONObject response = new JSONObject();
        JSONArray levels = new JSONArray();
        for (int level : CrossCheckMethod.ConfidenceLevels) {
            levels.put(level);
        }
        response.put("levels", (Object)levels);
        response.put("success", (Object)L.t((String)"Levels listed.", (Object[])new Object[0]));
        return response.toString();
    }

    @PrecachedRequest(relativeURL="/monteCarloRetest/fitnessList")
    private String onFitnessList() throws Exception {
        JSONObject response = new JSONObject();
        JSONArray items = new JSONArray();
        items.put((Object)new JSONObject().put("name", (Object)"Net Profit (Return)").put("key", (Object)"NetProfit"));
        items.put((Object)new JSONObject().put("name", (Object)"Return / Drawdown ratio").put("key", (Object)"ReturnDDRatio"));
        items.put((Object)new JSONObject().put("name", (Object)"Drawdown").put("key", (Object)"Drawdown"));
        items.put((Object)new JSONObject().put("name", (Object)"R Expectancy").put("key", (Object)"RExpectancy"));
        items.put((Object)new JSONObject().put("name", (Object)"Annual % Return").put("key", (Object)"AnnualPctReturn"));
        JSONArray options = new JSONArray();
        List columns = DatabankColumns.get().getAvailableClasses();
        for (int i = 0; i < columns.size(); ++i) {
            DatabankColumn c = (DatabankColumn)columns.get(i);
            JSONObject item = new JSONObject();
            item.put("name", (Object)c.getName());
            item.put("key", (Object)c.getClass().getSimpleName());
            options.put((Object)item);
        }
        items.put((Object)new JSONObject().put("name", (Object)"Other").put("key", (Object)"Other").put("options", (Object)options));
        response.put("types", (Object)items);
        response.put("success", (Object)L.t((String)"Listed.", (Object[])new Object[0]));
        return response.toString();
    }
}

