/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.ailib.tools.MCPTools
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.algocloud.AlgoCloudImport
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Servlet.impl.AlgoCloud;

import com.strategyquant.ailib.tools.MCPTools;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.algocloud.AlgoCloudImport;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONObject;

public class AlgoCloudServlet
extends HttpJSONServlet {
    private static final String LOCK = "AlgoCloudServletImport";
    private final IResultsGroupProvider rgProvider;

    public AlgoCloudServlet(IResultsGroupProvider rgProvider) {
        this.rgProvider = rgProvider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "import": {
                return this.onImport(args);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    private String onImport(Map<String, String[]> args) throws Exception {
        JSONObject result;
        String strategyXML = AlgoCloudServlet.paramValue(args, "strategyXML");
        String lastSettingsXML = AlgoCloudServlet.paramValue(args, "lastSettingsXML");
        String strategyName = AlgoCloudServlet.paramValue(args, "strategyName");
        if (strategyXML == null || strategyXML.trim().isEmpty()) {
            JSONObject source;
            String file = AlgoCloudServlet.paramValue(args, "file");
            String project = AlgoCloudServlet.paramValue(args, "project");
            String databank = AlgoCloudServlet.paramValue(args, "databank");
            String strategy = AlgoCloudServlet.paramValue(args, "strategy");
            String backtestID = AlgoCloudServlet.paramValue(args, "backtestID");
            if (AlgoCloudServlet.notEmpty(file) || AlgoCloudServlet.notEmpty(strategy)) {
                source = MCPTools.strategySource((String)file, (String)project, (String)databank, (String)strategy);
            } else if (AlgoCloudServlet.notEmpty(backtestID)) {
                source = this.fromResultsGroup(args);
            } else {
                return AlgoCloudServlet.apiErrorJSONNoLog((String)L.t((String)"There is no strategy to open in AlgoCloud.", (Object[])new Object[0]), null);
            }
            if (source.has("error")) {
                return AlgoCloudServlet.apiErrorJSONNoLog((String)source.getString("error"), null);
            }
            strategyXML = source.getString("strategyXML");
            if (lastSettingsXML == null) {
                lastSettingsXML = source.optString("lastSettingsXML", null);
            }
            if (strategyName == null) {
                strategyName = source.optString("fileName", null);
            }
        }
        if ((result = AlgoCloudImport.run((String)strategyXML, (String)lastSettingsXML, (String)strategyName)).has("error")) {
            return AlgoCloudServlet.apiErrorJSONNoLog((String)result.getString("error"), null);
        }
        return result.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private JSONObject fromResultsGroup(Map<String, String[]> args) throws Exception {
        Map rgParams = this.getRgParams(this.getParameters(null, args));
        ResultsGroup rg = this.rgProvider.get(rgParams, LOCK);
        if (rg == null) {
            return new JSONObject().put("error", (Object)L.t((String)"The backtest result was not found.", (Object[])new Object[0]));
        }
        try {
            Element el = rg.portfolio().getStrategyXml();
            if (el == null) {
                JSONObject jSONObject = new JSONObject().put("error", (Object)L.t((String)"The result contains no strategy.", (Object[])new Object[0]));
                return jSONObject;
            }
            JSONObject out = new JSONObject();
            out.put("strategyXML", (Object)XMLUtil.elementToString((Element)el.clone()));
            out.put("fileName", (Object)rg.getName());
            String lastSettings = rg.getLastSettings();
            if (lastSettings != null && !lastSettings.isEmpty()) {
                out.put("lastSettingsXML", (Object)lastSettings);
            }
            JSONObject jSONObject = out;
            return jSONObject;
        }
        finally {
            rg.releaseLock(LOCK);
        }
    }

    private static String paramValue(Map<String, String[]> args, String name) {
        try {
            String[] values = args.get(name);
            return values == null || values.length == 0 ? null : values[0];
        }
        catch (Exception e) {
            return null;
        }
    }

    private static boolean notEmpty(String s) {
        return s != null && !s.trim().isEmpty();
    }
}

