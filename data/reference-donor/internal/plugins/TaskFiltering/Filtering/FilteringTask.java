/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.conditions.ConditionsChecker
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.Filtering;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Filter strategies plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class FilteringTask
extends AbstractTask {
    private static final String LOCK_FILTERINGTASK = "FilteringTask";
    private int actionType;
    private int conditionsType;
    private ArrayList<Condition> conditions;
    private Databank databankSource = null;
    private Databank databankTarget = null;
    private String dismissReason;
    private int totalResults;
    private int totalPassed = 0;
    private int maxStrategies = 0;
    private ConditionsChecker conditionsChecker = new ConditionsChecker();

    public FilteringTask() throws Exception {
        super(null, null);
    }

    public FilteringTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "Filtering";
    }

    public String getName() {
        return L.tsq((String)"Filter strategies");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        FilteringTask task = new FilteringTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public void start() throws Exception {
        this.project = ProjectEngine.get((String)this.projectName);
        this.databankSource = (Databank)this.settingsData.getParams().get("DatabankSource");
        this.databankTarget = (Databank)this.settingsData.getParams().get("DatabankTarget");
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting strategies filtering...", (Object[])new Object[0]));
        this.progressEngine.start();
        if (this.databankTarget != null) {
            this.setDatabankFilter(this.databankTarget, false);
        }
        this.actionType = (Integer)this.settingsData.getParams().get("ActionType");
        this.conditionsType = (Integer)this.settingsData.getParams().get("ConditionsType");
        this.conditions = (ArrayList)this.settingsData.getParams().get("Conditions");
        this.maxStrategies = (Integer)this.settingsData.getParams().get("MaxStrategiesFilter");
        ArrayList results = this.databankSource.getRecords();
        this.totalPassed = 0;
        this.totalResults = results.size();
        for (int i = results.size() - 1; i >= 0; --i) {
            ResultsGroup strategy = (ResultsGroup)results.get(i);
            String strategyName = strategy.getName();
            try {
                boolean passed = false;
                if (this.maxStrategies > 0 && this.totalPassed >= this.maxStrategies) break;
                if (this.conditionsPass(strategy)) {
                    ++this.totalPassed;
                    passed = true;
                    switch (this.actionType) {
                        case 0: {
                            this.databankSource.remove(strategyName, true, true, true, true, LOCK_FILTERINGTASK);
                            this.progressEngine.printToLogDebug(L.t((String)"%s, deleted: %s", (Object[])new Object[]{strategyName, this.dismissReason}));
                            break;
                        }
                        case 1: {
                            ResultsGroup strategyCloned = strategy.clone();
                            this.databankTarget.add(strategyCloned, true);
                            this.progressEngine.printToLogDebug(L.t((String)"%s, copied: %s", (Object[])new Object[]{strategyName, this.dismissReason}));
                            break;
                        }
                        case 2: {
                            ResultsGroup strategyCloned = strategy.clone();
                            this.databankTarget.add(strategyCloned, true);
                            this.databankSource.remove(strategyName, true, true, true, false, LOCK_FILTERINGTASK);
                            this.progressEngine.printToLogDebug(L.t((String)"%s, moved: %s", (Object[])new Object[]{strategyName, this.dismissReason}));
                        }
                    }
                }
                this.increaseGlobalStats(passed);
                this.progressEngine.checkPaused();
                if (!this.progressEngine.isStopped()) continue;
            }
            catch (OutOfMemoryError e) {
                this.project.onMemoryError((Error)e);
            }
            break;
        }
        if (this.actionType == 0) {
            this.databankSource.updateBestResults();
        } else {
            this.databankTarget.updateBestResults();
        }
        this.progressEngine.finish();
    }

    private void increaseGlobalStats(boolean passed) {
        String action = this.actionTypeToText();
        this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Input", (Object[])new Object[0]), 1L, action, passed ? 1L : 0L);
    }

    private boolean conditionsPass(ResultsGroup rg) {
        if (this.conditionsType == 2 || this.conditionsType == 3) {
            SettingsMap map = rg.specialValues();
            if (this.conditionsType == 2) {
                if (map.containsKey(SpecialValues.FiltersResultFailedReason) && map.getString(SpecialValues.FiltersResultFailedReason).equals(SpecialValues.FiltersResultPassed)) {
                    this.dismissReason = L.t((String)"Filter result = Passed", (Object[])new Object[0]);
                    return true;
                }
                return false;
            }
            if (this.conditionsType == 3) {
                if (map.containsKey(SpecialValues.FiltersResultFailedReason) && map.getString(SpecialValues.FiltersResultFailedReason).equals(SpecialValues.FiltersResultPassed)) {
                    return false;
                }
                this.dismissReason = L.t((String)"Filter result = Failed", (Object[])new Object[0]);
                return true;
            }
        }
        if (this.conditions == null || this.conditions.isEmpty()) {
            this.dismissReason = L.t((String)"No conditions", (Object[])new Object[0]);
            return true;
        }
        String dismissReason = this.checkConditions(rg);
        if (this.conditionsType == 0 && dismissReason == null) {
            this.dismissReason = L.t((String)"fit the conditions", (Object[])new Object[0]);
            return true;
        }
        if (this.conditionsType == 1 && dismissReason != null) {
            this.dismissReason = L.t((String)"not fit %s", (Object[])new Object[]{dismissReason});
            return true;
        }
        return false;
    }

    private String checkConditions(ResultsGroup rg) {
        for (Condition condition : this.conditions) {
            try {
                boolean met;
                if (!condition.isUsed() || (met = this.conditionsChecker.check(rg, condition))) continue;
                return this.conditionsChecker.dismissalMessage;
            }
            catch (Exception e) {
                this.progressEngine.printToLog(L.t((String)"Error while evaluating conditions: %s", (Object[])new Object[]{e.getMessage()}));
                Log.error("Error while evaluating condition: ", (Throwable)e);
            }
        }
        return null;
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskFiltering";
    }

    public int getPreferredPosition() {
        return 3;
    }

    public String[] getSettings() {
        return new String[]{"Filtering"};
    }

    protected Databank[] getUsedDatabanks() {
        return new Databank[]{this.databankSource, this.databankTarget};
    }

    protected Databank getOutputDatabank() {
        return this.databankTarget;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        String action = this.actionTypeToText();
        log.print(action + ": " + this.totalPassed);
        if (this.progressEngine != null) {
            this.progressEngine.printToLogDebug(action + ": " + this.totalPassed);
        }
    }

    private String actionTypeToText() {
        if (this.actionType == 0) {
            return L.t((String)"Deleted", (Object[])new Object[0]);
        }
        if (this.actionType == 1) {
            return L.t((String)"Copied", (Object[])new Object[0]);
        }
        if (this.actionType == 2) {
            return L.t((String)"Moved", (Object[])new Object[0]);
        }
        return "NA";
    }
}

