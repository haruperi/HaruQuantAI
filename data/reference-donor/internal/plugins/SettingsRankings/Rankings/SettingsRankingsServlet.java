/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Rankings;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SettingsRankingsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SettingsRankingsServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getDefaultWFConditions": {
                return this.onGetDefaultWFConditions(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONArray getFitnessMethods() throws Exception {
        JSONArray methods = new JSONArray();
        for (IFitnessFunction plugin : SQPluginManager.getPlugins(IFitnessFunction.class)) {
            if (plugin.getFitnessKey().equals("ComputeFromWFResult")) continue;
            methods.put((Object)new JSONObject().put("value", (Object)plugin.getFitnessKey()).put("name", (Object)plugin.getFitnessName()).put("crosscheck", ICrossCheck.class.isAssignableFrom(plugin.getClass())));
        }
        return methods;
    }

    private String onGetDefaultWFConditions(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"conditions", "action"});
        String conditions = args.get("conditions")[0].toString();
        String action = args.get("action")[0].toString();
        JSONObject response = new JSONObject();
        Element conditionsEl = null;
        if (action.equals("replace")) {
            conditionsEl = XMLUtil.fileToXmlElement((File)new File(SQPaths.wfDefaultConditionsPath));
        } else {
            conditionsEl = XMLUtil.stringToElement((String)conditions);
            Element defConditionsEl = XMLUtil.fileToXmlElement((File)new File(SQPaths.wfDefaultConditionsPath));
            for (Element conditionEl : defConditionsEl.getChildren("Condition")) {
                conditionsEl.addContent((Content)conditionEl.clone());
            }
        }
        response.put("conditions", (Object)XMLUtil.elementToString((Element)conditionsEl));
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

