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
package com.strategyquant.plugin.Databank.impl.Rename;

import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class DatabankRenameServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DatabankRenameServlet.class);

    DatabankRenameServlet() {
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "rename": {
                return this.onRename(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onRename(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "databankName", "strategies"});
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParamValue(args, "projectName");
        String databankName = this.tryGetParamValue(args, "databankName");
        String strategies = this.getParam(args, "strategies", "all");
        SQProject project = ProjectEngine.get((String)projectName);
        if (!ProjectEngine.projectExists((String)projectName)) {
            throw new Exception("Project '" + projectName + "' doesn't exist.");
        }
        if (!project.getDatabanks().containsKey((Object)databankName)) {
            throw new Exception("Databank '" + databankName + "' doesn't exist.");
        }
        Databank databank = (Databank)project.getDatabanks().get((Object)databankName);
        String[] stgs = strategies.split(",");
        if (stgs.length == 1 && stgs[0].equals("all")) {
            stgs = new String[databank.size()];
            databank.getRecordKeys().toArray(stgs);
        }
        String name = null;
        String prefix = "";
        String postfix = "";
        if (stgs.length == 1) {
            name = this.tryGetParamValue(args, "name");
        } else {
            try {
                prefix = this.tryGetParamValue(args, "prefix");
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                postfix = this.tryGetParamValue(args, "postfix");
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
        String lockName = "RenameStrategies";
        String actionName = "RenameStrategies";
        double count = 0.0;
        project.publisher.resetLastData("progress-channel");
        project.getProgress().update(actionName, 0.0, null);
        for (int i = 0; i < stgs.length; ++i) {
            String strategyName = stgs[i];
            ResultsGroup rg = null;
            try {
                rg = databank.getLocked(strategyName, lockName);
                ResultsGroup newRg = rg.clone();
                if (stgs.length == 1) {
                    newRg.setName(name);
                } else {
                    newRg.setName(prefix + newRg.getName() + postfix);
                }
                databank.remove(strategyName, true, true, false, true, lockName);
                databank.add(newRg, true);
                continue;
            }
            catch (Exception e) {
                Log.error("Error while renaming strategy '" + strategyName + "'", (Throwable)e);
                continue;
            }
            finally {
                if (rg != null) {
                    rg.releaseLock(lockName);
                }
                int percent = (int)((count += 1.0) / (double)stgs.length * 100.0);
                project.getProgress().update("RenameStrategies", (double)percent, null);
            }
        }
        project.getProgress().update(actionName, 100.0, null);
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

