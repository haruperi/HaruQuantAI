/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.WhatToBuild;

import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WhatToBuildServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(WhatToBuildServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "listFiles": {
                return this.onListFiles();
            }
            case "getTemplateConfig": {
                return this.onGetTemplateConfig(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onListFiles() throws Exception {
        JSONObject response = new JSONObject();
        try {
            response.put("strategyFiles", (Object)this.loadFilesFromFolder(SQPaths.strategiesDirPath));
            response.put("strategyTemplateFiles", (Object)this.loadFilesFromFolder(SQPaths.strategyTemplatesDirPath));
        }
        catch (Exception e) {
            return WhatToBuildServlet.apiErrorJSON((String)L.t((String)"Cannot list config files.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Config files listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray loadFilesFromFolder(String path) {
        JSONArray array = new JSONArray();
        File folder = new File(path);
        if (folder.exists()) {
            for (File file : folder.listFiles()) {
                array.put((Object)file.getName());
            }
        } else {
            folder.mkdirs();
        }
        return array;
    }

    private String onGetTemplateConfig(Map<String, String[]> params) throws Exception {
        JSONObject response = new JSONObject();
        JSONArray chartSettings = new JSONArray();
        String fileName = this.tryGetParam(params, "fileName")[0];
        File templateFile = new File(fileName = (fileName = fileName.replaceAll(Pattern.quote("\\"), "/")).contains("/") ? fileName : SQPaths.strategyTemplatesDirPath + "/" + fileName);
        if (!templateFile.exists()) {
            return WhatToBuildServlet.apiErrorJSON((String)L.t((String)"Selected template file doesn't exist", (Object[])new Object[0]), null);
        }
        boolean reload = false;
        try {
            reload = Boolean.parseBoolean(this.tryGetParam(params, "reload")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            Element settings = null;
            if (SQUtils.getExtension((String)fileName).toLowerCase().equals("sqw")) {
                settings = XMLUtil.fileToXmlElement((File)templateFile);
                if (settings == null) {
                    throw new Exception(L.t((String)"Portfolio settings not found in the template file.", (Object[])new Object[0]));
                }
            } else {
                ResultsGroup rg = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{fileName});
                settings = rg.getStrategyXml();
                response.put("lastSettings", (Object)rg.getLastSettings());
            }
            Element elStrategy = XMLUtil.getChildElem((Element)settings, (String)"Strategy");
            Element elDatas = XMLUtil.getChildElem((Element)elStrategy, (String)"Datas");
            List children = elDatas.getChildren("data");
            for (int i = 0; i < children.size(); ++i) {
                Element elData = (Element)children.get(i);
                JSONObject chartSetting = new JSONObject();
                chartSetting.put("name", (Object)XMLUtil.getNodeValue((Element)elData, (String)"chart"));
                chartSetting.put("symbol", (Object)XMLUtil.getNodeValue((Element)elData, (String)"symbol"));
                String timeframe = XMLUtil.getNodeValue((Element)elData, (String)"timeFrame");
                try {
                    TimeframeManager.getMillis((String)timeframe);
                }
                catch (Exception e) {
                    timeframe = TimeframeManager.translateSQ3TFToString((int)Integer.parseInt(timeframe));
                }
                chartSetting.put("timeframe", (Object)timeframe);
                chartSettings.put((Object)chartSetting);
            }
        }
        catch (Exception e) {
            return WhatToBuildServlet.apiErrorJSON((String)L.t((String)"Cannot load template chart data settings.", (Object[])new Object[0]), (Throwable)e);
        }
        if (reload) {
            response.put("strategyTemplateFiles", (Object)this.loadFilesFromFolder(SQPaths.strategyTemplatesDirPath));
        }
        response.put("chartSettings", (Object)chartSettings);
        response.put("success", (Object)L.t((String)"Template chart data returned.", (Object[])new Object[0]));
        return response.toString();
    }
}

