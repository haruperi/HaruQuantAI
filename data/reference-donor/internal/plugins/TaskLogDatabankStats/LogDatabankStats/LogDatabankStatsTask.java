/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.conditions.ConditionsChecker
 *  com.strategyquant.tradinglib.conditions.IConditionValue
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.LogDatabankStats;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="LogDatabankStatsTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class LogDatabankStatsTask
extends AbstractTask {
    private String logMessage;
    private Databank databank;
    private ArrayList<Object[]> logStats;
    private ConditionsChecker conditionsChecker = new ConditionsChecker();

    public LogDatabankStatsTask() throws Exception {
        super(null, null);
    }

    public LogDatabankStatsTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "LogDatabankStats";
    }

    public String getName() {
        return L.tsq((String)"Log databank stats");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        LogDatabankStatsTask task = new LogDatabankStatsTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() throws Exception {
        this.project = ProjectEngine.get((String)this.projectName);
        this.databank = (Databank)this.settingsData.getParams().get("DatabankSource");
        this.logStats = (ArrayList)this.settingsData.getParams().get("LogStats");
    }

    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Logging databank statistics of '%s'", (Object[])new Object[]{this.databank.getName()}));
        this.progressEngine.start();
        this.logMessage = "\n";
        this.logMessage = this.logMessage + L.t((String)"Logging databank statistics of '%s'", (Object[])new Object[]{this.databank.getName()}) + "\n";
        ArrayList results = this.databank.getRecords();
        if (this.logStats.isEmpty()) {
            this.progressEngine.printToLog(L.t((String)"No log data configured", (Object[])new Object[0]));
            this.logMessage = this.logMessage + L.t((String)"No log data configured", (Object[])new Object[0]) + "\n";
        } else {
            for (int i = 0; i < this.logStats.size(); ++i) {
                try {
                    Object[] logStastsItem = this.logStats.get(i);
                    String type = (String)logStastsItem[0];
                    ArrayList conditions = (ArrayList)logStastsItem[1];
                    IConditionValue conditionValue = (IConditionValue)logStastsItem[2];
                    this.logStats(type, conditions, conditionValue, results);
                    this.progressEngine.checkPaused();
                    if (!this.progressEngine.isStopped()) continue;
                }
                catch (OutOfMemoryError e) {
                    this.project.onMemoryError((Error)e);
                }
                break;
            }
        }
        this.progressEngine.finish();
    }

    private void logStats(String type, ArrayList<Condition> conditions, IConditionValue conditionValue, ArrayList<ResultsGroup> results) throws Exception {
        double totalValue = 0.0;
        int resultsPassed = 0;
        for (int i = 0; i < results.size(); ++i) {
            ResultsGroup rg = results.get(i);
            if (!this.checkConditions(rg, conditions)) continue;
            ++resultsPassed;
            try {
                switch (type) {
                    case "sum": {
                        double statsValue = conditionValue.statsExists(new Object[]{rg}) ? conditionValue.getValue(new Object[]{rg}) : 0.0;
                        totalValue += statsValue;
                        break;
                    }
                    case "avg": {
                        double statsValue = conditionValue.statsExists(new Object[]{rg}) ? conditionValue.getValue(new Object[]{rg}) : 0.0;
                        totalValue += statsValue;
                        break;
                    }
                    case "count": {
                        totalValue += 1.0;
                    }
                }
                continue;
            }
            catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
                // empty catch block
            }
        }
        String title = "NA";
        String column = conditionValue.getTitle();
        switch (type) {
            case "sum": {
                String formatedValue = conditionValue.printFormatedValue(totalValue);
                title = L.t((String)"Sum of %s of strategies matching conditions: %s, results passed %d", (Object[])new Object[]{column, formatedValue, resultsPassed});
                break;
            }
            case "avg": {
                String formatedValue = conditionValue.printFormatedValue(totalValue / (double)resultsPassed);
                title = L.t((String)"Average of %s of strategies matching conditions: %s, results passed %d", (Object[])new Object[]{column, formatedValue, resultsPassed});
                break;
            }
            case "count": {
                double pct = totalValue / (double)results.size() * 100.0;
                title = L.t((String)"Count of strategies matching conditions: %s (%s of all)", (Object[])new Object[]{Double.valueOf(totalValue).intValue(), PlTypes.printPL((double)pct, (byte)20)});
            }
        }
        String conditionsText = "";
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = conditions.get(i);
            if (!condition.isUsed()) continue;
            conditionsText = conditionsText + "\t" + condition.toString() + "\n";
        }
        this.progressEngine.printToLog(title + "\n" + conditionsText);
        this.logMessage = this.logMessage + title + "\n" + conditionsText + "\n";
    }

    private boolean checkConditions(ResultsGroup rg, ArrayList<Condition> conditions) {
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = conditions.get(i);
            try {
                if (!condition.isUsed() || this.conditionsChecker.check(rg, condition)) continue;
                return false;
            }
            catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
                continue;
            }
            catch (Exception e) {
                this.progressEngine.printToLog(L.t((String)"Error while evaluating conditions: %s", (Object[])new Object[]{e.getMessage()}));
                Log.error("Error while evaluating condition: ", (Throwable)e);
            }
        }
        return true;
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskLogDatabankStats";
    }

    public int getPreferredPosition() {
        return 500;
    }

    public String[] getSettings() {
        return new String[]{"LogDatabankStats"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        log.print(this.logMessage, false);
        super.logTaskFinished(log);
    }
}

