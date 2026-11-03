/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.BarChart
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.Variable
 *  com.strategyquant.tradinglib.Variables
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.robustnesstests.FitnessData
 *  com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.SequentialOptimization;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.BarChart;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.robustnesstests.FitnessData;
import com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SequentialOptimizationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SequentialOptimizationServlet.class);
    private static final String LOCK_SEQOPTSERVLET = "SequentialOptimizationServlet";
    private IResultsGroupProvider rgProvider;

    public SequentialOptimizationServlet(IResultsGroupProvider rgProvider) {
        this.rgProvider = rgProvider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(parameterMap);
            }
            case "applyParams": {
                return this.onApplyParams(parameterMap);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response;
        block6: {
            response = new JSONObject();
            ResultsGroup resultsGroup = this.rgProvider.get(parameterMap, LOCK_SEQOPTSERVLET);
            try {
                SequentialOptimizationResults results = resultsGroup.mainResult().getSequentialOptimizaionResults();
                if (results != null) {
                    JSONArray resultsArray = new JSONArray();
                    for (int a = 0; a < results.size(); ++a) {
                        FitnessData data = (FitnessData)results.get(a);
                        JSONObject result = data.toJSON();
                        result.put("chart", (Object)this.getChartData(data));
                        resultsArray.put((Object)result);
                    }
                    response.put("results", (Object)resultsArray);
                    response.put("parametersApplied", results.isApplyToStrategy());
                    response.put("passed", results.isPassed());
                    break block6;
                }
                String string = SequentialOptimizationServlet.apiErrorJSON((String)L.t((String)"Strategy doesn't contain Sequential Optimization results", (Object[])new Object[0]), null);
                return string;
            }
            finally {
                if (resultsGroup != null) {
                    resultsGroup.releaseLock(LOCK_SEQOPTSERVLET);
                    resultsGroup = null;
                }
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private JSONObject getChartData(FitnessData fitnessData) {
        BarChart chart = new BarChart();
        chart.maxXTicksLimit = 1000;
        chart.yAxisTitle = L.t((String)"Fitness", (Object[])new Object[0]);
        chart.xAxisTitle = L.t((String)"Parameter values", (Object[])new Object[0]);
        chart.tooltips = false;
        chart.disableEvents = true;
        chart.setCategoryColor("all", "blue");
        for (int x = 0; x < fitnessData.values.length; ++x) {
            double paramValue = fitnessData.values[x];
            double fitnessValue = fitnessData.fitness[x];
            if (paramValue < fitnessData.bestAreaStartValue || paramValue > fitnessData.bestAreaEndValue) {
                chart.addValue("all", (Comparable)Double.valueOf(paramValue), (Number)fitnessValue);
                continue;
            }
            if (paramValue == fitnessData.bestValue) {
                chart.addValue("all", (Comparable)Double.valueOf(paramValue), (Number)fitnessValue, "red");
                continue;
            }
            chart.addValue("all", (Comparable)Double.valueOf(paramValue), (Number)fitnessValue, "green");
        }
        return chart.toJSON();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onApplyParams(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response;
        block8: {
            response = new JSONObject();
            ResultsGroup resultsGroup = this.rgProvider.get(parameterMap, LOCK_SEQOPTSERVLET);
            try {
                SequentialOptimizationResults results = resultsGroup.mainResult().getSequentialOptimizaionResults();
                if (results != null) {
                    StrategyBase strategy = StrategyBase.createXmlStrategy((Element)resultsGroup.getStrategyXml());
                    strategy.transformToVariables(results.isSymmetricVariables(), results.getParamTypes());
                    Variables vars = strategy.variables();
                    for (int a = 0; a < results.size(); ++a) {
                        FitnessData data = (FitnessData)results.get(a);
                        if (!data.stableAreaFound) continue;
                        Variable var = vars.get(data.variable.getName());
                        if (var != null) {
                            var.setValue(data.bestValue);
                            continue;
                        }
                        String string = SequentialOptimizationServlet.apiErrorJSON((String)L.t((String)"Unable to modify variable %s - variable not found", (Object[])new Object[]{data.variable.getName()}), null);
                        return string;
                    }
                    strategy.transformToNumbers();
                    resultsGroup.mainResult().addStrategy(strategy);
                    resultsGroup.mainResult().addStrategyXml(strategy.getStrategyXml());
                    break block8;
                }
                String string = SequentialOptimizationServlet.apiErrorJSON((String)L.t((String)"Strategy doesn't contain Sequential Optimization results", (Object[])new Object[0]), null);
                return string;
            }
            finally {
                if (resultsGroup != null) {
                    resultsGroup.releaseLock(LOCK_SEQOPTSERVLET);
                    resultsGroup = null;
                }
            }
        }
        response.put("success", (Object)L.t((String)"Parameters applied to strategy", (Object[])new Object[0]));
        return response.toString();
    }
}

