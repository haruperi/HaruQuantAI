/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.tradinglib.EngineChart
 *  com.strategyquant.tradinglib.GeneticInfo
 *  com.strategyquant.tradinglib.MemoryCleaner
 *  com.strategyquant.tradinglib.enginecharts.EngineChartsList
 *  com.strategyquant.tradinglib.gp.GPFitnessEvolutionData
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.TaskStats
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Engine.impl.Panel;

import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.plugin.Engine.impl.Panel.EngineDb;
import com.strategyquant.tradinglib.EngineChart;
import com.strategyquant.tradinglib.GeneticInfo;
import com.strategyquant.tradinglib.MemoryCleaner;
import com.strategyquant.tradinglib.enginecharts.EngineChartsList;
import com.strategyquant.tradinglib.gp.GPFitnessEvolutionData;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.TaskStats;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EngineServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(EngineServlet.class);

    public EngineServlet() {
        try {
            EngineDb.init(SQStructure.PLUGINS_DIR + "EnginePanel");
            this.generate();
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
        }
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getTypes": {
                return this.onGetTypes(args);
            }
            case "saveSelection": {
                return this.onSaveSelection(args);
            }
            case "getInfo": {
                return this.onGetInfo(args);
            }
            case "clearLog": {
                return this.onClearLog(args);
            }
            case "cleanupMemory": {
                return this.onCleanupMemory(args);
            }
            case "loadSettings": {
                return this.onLoadSettings(args);
            }
            case "saveSettings": {
                return this.onSaveSettings(args);
            }
            case "loadTextLog": {
                return this.onLoadTextLog(args);
            }
            case "loadVisualLog": {
                return this.onLoadVisualLog(args);
            }
            case "getFitnessEvolutionStats": {
                return this.onGetFitnessEvolutionStats(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onGetFitnessEvolutionStats(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        int islands = 0;
        try {
            GPFitnessEvolutionData[] islandsEvoData;
            SQProject project = ProjectEngine.get((String)"BUILDER");
            GeneticInfo geneticInfo = project.getGeneticInfo();
            if (geneticInfo.isGeneticBuild() && (islandsEvoData = geneticInfo.getIslandsEvoData()) != null) {
                islands = islandsEvoData.length;
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        response.put("islands", islands);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onLoadTextLog(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "projectName")[0];
        JSONObject response = new JSONObject();
        SQProject project = ProjectEngine.get((String)projectName);
        response.put("text", (Object)project.printGlobalLog());
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onLoadVisualLog(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "projectName")[0];
        String type = this.tryGetParam(args, "type")[0];
        JSONObject response = new JSONObject();
        JSONArray tasksArray = new JSONArray();
        SQProject project = ProjectEngine.get((String)projectName);
        for (int t = 0; t < project.getTasksHashes().size(); ++t) {
            try {
                int taskHash = project.getTasksHashes().getInt(t);
                ISQTask task = project.getTaskByHash(taskHash);
                JSONObject item = new JSONObject().put("title", (Object)(task.getIndex() + ". " + task.getTitle())).put("type", (Object)task.getType()).put("iterations", task.getNumberOfRuns());
                TaskStats taskStats = project.getTaskStats(taskHash);
                if (taskStats != null) {
                    item.put("stats", (Object)taskStats.getStatsJSONArray());
                }
                tasksArray.put((Object)item);
                continue;
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
        response.put("tasks", (Object)tasksArray);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onLoadSettings(Map<String, String[]> args) throws Exception {
        String product = this.tryGetParam(args, "product")[0];
        JSONObject response = new JSONObject();
        boolean deleteLogOnStart = false;
        try {
            deleteLogOnStart = Boolean.parseBoolean(EngineDb.getSetting(product + "_deleteLogOnStart", "false"));
        }
        catch (Exception exception) {
            // empty catch block
        }
        response.put("deleteLogOnStart", deleteLogOnStart);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onSaveSettings(Map<String, String[]> args) throws Exception {
        String product = this.tryGetParam(args, "product")[0];
        String deleteLogOnStart = this.tryGetParam(args, "deleteLogOnStart")[0];
        JSONObject response = new JSONObject();
        EngineDb.setSetting(product + "_deleteLogOnStart", deleteLogOnStart);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onGetTypes(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "projectName")[0];
        if (!projectName.equals("TaskManager")) {
            ProjectEngine.get((String)projectName).publisher.resetLastData("engine-channel");
        }
        JSONObject response = new JSONObject();
        JSONArray types = new JSONArray();
        for (EngineChart chart : EngineChartsList.getInstance().getAvailableClasses()) {
            JSONObject item = new JSONObject();
            item.put("type", (Object)chart.getClassName());
            item.put("name", (Object)chart.toString());
            types.put((Object)item);
        }
        response.put("types", (Object)types);
        response.put("settings", (Object)this.getSettings(projectName));
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private JSONArray getSettings(String projectName) throws Exception {
        JSONArray types = new JSONArray();
        types.put((Object)EngineDb.getSetting(this.getKey(projectName, 0), "DatabankFitnessIS"));
        types.put((Object)EngineDb.getSetting(this.getKey(projectName, 1), "HeapMemoryChart"));
        types.put((Object)EngineDb.getSetting(this.getKey(projectName, 2), "OffHeapMemoryChart"));
        types.put((Object)EngineDb.getSetting(this.getKey(projectName, 3), "OffHeapMemoryInfoChart"));
        types.put((Object)EngineDb.getSetting(this.getKey(projectName, 4), "AcceptedStrategiesPerHour"));
        types.put((Object)EngineDb.getSetting(this.getKey(projectName, 5), "AverageStrategiesPerHourChart"));
        return types;
    }

    private String getKey(String projectName, int number) {
        return projectName + "_chart" + number;
    }

    private String onSaveSelection(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "projectName")[0];
        String type = this.tryGetParam(args, "type")[0];
        int number = Integer.parseInt(this.tryGetParam(args, "number")[0]);
        JSONObject response = new JSONObject();
        EngineChartsList.getInstance().findClassByName(type);
        ProjectEngine.get((String)projectName);
        EngineDb.setSetting(this.getKey(projectName, number), type);
        this.generateCharts();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onGetInfo(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(args, "projectName")[0];
        ProjectEngine.get((String)projectName).publisher.resetLastData("engine-channel");
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onCleanupMemory(Map<String, String[]> args) throws Exception {
        String result = MemoryCleaner.cleanNow();
        JSONObject response = new JSONObject();
        response.put("success", (Object)result);
        return response.toString();
    }

    private String onClearLog(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(args, "projectName")[0];
        ProjectEngine.get((String)projectName).log.clear();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private void generate() {
        new Thread(){

            @Override
            public void run() {
                while (true) {
                    try {
                        while (true) {
                            EngineServlet.this.generateCharts();
                            Thread.sleep(5000L);
                        }
                    }
                    catch (Exception exception) {
                        continue;
                    }
                    break;
                }
            }
        }.start();
    }

    private void generateCharts() {
        for (SQProject project : ProjectEngine.list()) {
            project.engineCharts.generate();
        }
        ArrayList globalCharts = EngineChartsList.getInstance().globalCharts;
        for (int i = 0; i < globalCharts.size(); ++i) {
            EngineChart chart = (EngineChart)globalCharts.get(i);
            chart.addNextValue();
        }
    }
}

