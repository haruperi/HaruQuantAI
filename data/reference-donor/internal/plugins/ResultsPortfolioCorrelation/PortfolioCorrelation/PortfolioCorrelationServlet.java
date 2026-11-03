/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.correlation.CorrelationTypes
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation;

import com.strategyquant.lib.L;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationInterruptException;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationResultsSender;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation.PortfolioCorrelationComputer;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingTradesComputer;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.correlation.CorrelationTypes;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioCorrelationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioCorrelationServlet.class);
    private static final String LOCK_PORTFCORRELSERVLET = "PortfolioCorrelationServlet";
    private PortfolioCorrelationResultsSender sender = new PortfolioCorrelationResultsSender();
    private PortfolioCorrelationComputer correlationComputer = new PortfolioCorrelationComputer();
    private OverlappingTradesComputer overlappingTradesComputer = new OverlappingTradesComputer();
    private static IResultsGroupProvider rgProvider;
    private boolean running = false;

    public PortfolioCorrelationServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "compute": {
                return this.onCompute(parameterMap);
            }
            case "stop": {
                return this.onStop(parameterMap);
            }
            case "correlation": {
                return this.onCorrelation(parameterMap);
            }
            case "correlationSave": {
                return this.onCorrelationSave(parameterMap);
            }
            case "overlapping": {
                return this.onOverlapping(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onCorrelation(Map<String, String[]> parameterMap) {
        int count;
        int posStart;
        try {
            posStart = Integer.parseInt(parameterMap.get("posStart")[0]);
        }
        catch (Exception ex) {
            posStart = 0;
        }
        try {
            count = Integer.parseInt(parameterMap.get("count")[0]);
        }
        catch (Exception ex) {
            count = 100;
        }
        String symbol1 = parameterMap.get("symbol1")[0].toString();
        String symbol2 = parameterMap.get("symbol2")[0].toString();
        return this.correlationComputer.list(symbol1, symbol2, posStart, count);
    }

    private String onCorrelationSave(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String path = parameterMap.get("path")[0];
        this.correlationComputer.saveToCsv(path);
        response.put("success", (Object)L.t((String)"Correlation matrix saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onOverlapping(Map<String, String[]> parameterMap) {
        int count;
        int posStart;
        try {
            posStart = Integer.parseInt(parameterMap.get("posStart")[0]);
        }
        catch (Exception ex) {
            posStart = 0;
        }
        try {
            count = Integer.parseInt(parameterMap.get("count")[0]);
        }
        catch (Exception ex) {
            count = 100;
        }
        String symbol1 = parameterMap.get("symbol1")[0].toString();
        String symbol2 = parameterMap.get("symbol2")[0].toString();
        return this.overlappingTradesComputer.list(symbol1, symbol2, posStart, count);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onCompute(Map<String, String[]> parameterMap) throws Exception {
        ResultsGroup rg;
        this.checkParamExists(parameterMap, new String[]{"period", "type", "allowNegativeCorrelation", "addEmptyPeriods"});
        if (this.running) {
            throw new Exception(L.t((String)"Computing Portfolio correlation is already running. Cannot start another process.", (Object[])new Object[0]));
        }
        final int _period = Integer.parseInt(parameterMap.get("period")[0]);
        String _type = parameterMap.get("type")[0].toString();
        final Boolean _allowNegativeCorrelation = Boolean.parseBoolean(parameterMap.get("allowNegativeCorrelation")[0]);
        final Boolean _addEmptyPeriods = Boolean.parseBoolean(parameterMap.get("addEmptyPeriods")[0]);
        ResultsGroup resultsGroup = rgProvider.get(parameterMap, LOCK_PORTFCORRELSERVLET);
        try {
            rg = resultsGroup.clone();
        }
        finally {
            resultsGroup.releaseLock(LOCK_PORTFCORRELSERVLET);
        }
        JSONObject response = new JSONObject();
        final CorrelationType type = (CorrelationType)CorrelationTypes.getInstance().findClassByName(_type);
        new Thread(this){
            final /* synthetic */ PortfolioCorrelationServlet this$0;
            {
                this.this$0 = this$0;
            }

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            @Override
            public void run() {
                JSONObject data = new JSONObject();
                this.this$0.running = true;
                try {
                    long end;
                    long start = System.currentTimeMillis();
                    JSONObject correlationData = this.this$0.correlationComputer.compute(rg, _period, type, _allowNegativeCorrelation, _addEmptyPeriods, this.this$0.sender);
                    start = end = System.currentTimeMillis();
                    JSONObject overlappingData = this.this$0.overlappingTradesComputer.compute(rg, this.this$0.sender);
                    end = System.currentTimeMillis();
                    data.put("correlation", (Object)correlationData);
                    data.put("overlapping", (Object)overlappingData);
                }
                catch (PortfolioCorrelationInterruptException e) {
                    data.put("error", (Object)"Stopped");
                    this.this$0.correlationComputer.clear();
                    this.this$0.overlappingTradesComputer.clear();
                }
                catch (Exception e) {
                    Log.error("Error while computing portfolio correlation.", (Throwable)e);
                    data.put("error", (Object)("Error while computing portfolio correlation. " + e.getMessage()));
                }
                finally {
                    this.this$0.running = false;
                    data.put("progress", 100);
                    this.this$0.sender.sendData(data);
                }
            }
        }.start();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onStop(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        this.correlationComputer.stop();
        this.overlappingTradesComputer.stop();
        System.gc();
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

