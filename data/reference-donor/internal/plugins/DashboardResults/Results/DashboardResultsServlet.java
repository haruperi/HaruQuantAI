/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Dashboard.impl.Results;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DashboardResultsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DashboardResultsServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(args);
            }
            case "getSettings": {
                return this.onGetSettings(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = parameterMap.get("projectName")[0].toString();
        byte sampleType = Byte.parseByte(this.tryGetParam(parameterMap, "sampleType")[0]);
        SQProject project = ProjectEngine.get((String)projectName);
        project.bestResults.setSampleType(sampleType);
        project.bestResults.resetLastData();
        project.publisher.resetLastData("best-results-channel");
        MainApp.settings().set("DRST_" + projectName, sampleType + "");
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onGetSettings(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = parameterMap.get("projectName")[0].toString();
        String st = MainApp.settings().get("DRST_" + projectName);
        int sampleType = st != null ? (int)Byte.parseByte(st) : 127;
        response.put("sampleType", sampleType);
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

