/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.RenameTool;

import com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator;
import com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RenameToolServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(RenameToolServlet.class);
    private static final String lockName = "RenameToolServlet";

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "rename": {
                return this.onRename(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onRename(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        String databankName = this.tryGetParam(parameterMap, "databankName")[0];
        String strategies = this.tryGetParam(parameterMap, "strategies")[0];
        String[] stgs = strategies.split(",");
        SQProject project = ProjectEngine.get((String)projectName);
        Databank databank = (Databank)project.getDatabanks().get((Object)databankName);
        boolean renameAll = stgs[0].equals("all");
        ArrayList allStrategies = databank.getRecordKeys();
        RenameToolSettings.load();
        for (int a = 0; a < allStrategies.size(); ++a) {
            String strategyName = (String)allStrategies.get(a);
            if (!renameAll) {
                boolean found = false;
                for (int i = 0; i < stgs.length; ++i) {
                    if (!stgs[i].equals(strategyName)) continue;
                    found = true;
                    break;
                }
                if (!found) continue;
            }
            ResultsGroup rg = null;
            ResultsGroup newRg = null;
            try {
                rg = databank.getLocked(strategyName, lockName);
                newRg = rg.clone();
            }
            catch (Exception e) {
                Log.error("Error processing strategy '" + strategyName + "'", (Throwable)e);
            }
            finally {
                if (rg != null) {
                    rg.releaseLock(lockName);
                }
            }
            databank.remove(strategyName, true, true, false, true, lockName);
            RenameToolGenerator.processStrategy(newRg);
            databank.add(newRg, true);
        }
        response.put("success", (Object)"Strategies renamed.");
        return response.toString();
    }
}

