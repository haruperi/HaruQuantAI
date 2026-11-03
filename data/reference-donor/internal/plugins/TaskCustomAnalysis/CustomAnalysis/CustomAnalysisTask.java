/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.CustomAnalysisMethod
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.CustomAnalysis;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.CustomAnalysisMethod;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="CustomAnalysisTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class CustomAnalysisTask
extends AbstractTask {
    private static final String LockCustomAnalysisTask = "CustomAnalysisTask";
    private String projectLogMessage = "";
    private CustomAnalysisInfo ca = null;
    private Databank databankSource = null;
    private Databank databankTarget = null;

    public CustomAnalysisTask() throws Exception {
        super(null, null);
    }

    public CustomAnalysisTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "CustomAnalysis";
    }

    public String getName() {
        return L.tsq((String)"Custom analysis");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        CustomAnalysisTask task = new CustomAnalysisTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() throws Exception {
        this.project = ProjectEngine.get((String)this.projectName);
        this.ca = (CustomAnalysisInfo)this.settingsData.getParams().get("CustomAnalysis");
        this.databankSource = (Databank)this.settingsData.getParams().get("DatabankSource");
        this.databankTarget = (Databank)this.settingsData.getParams().get("DatabankTarget");
    }

    public void start() throws Exception {
        this.init();
        this.projectLogMessage = "";
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting custom analysis...", (Object[])new Object[0]));
        this.progressEngine.start();
        ArrayList results = this.databankSource.getRecords();
        ArrayList<ResultsGroup> passedResults = new ArrayList<ResultsGroup>();
        for (int i = 0; i < results.size(); ++i) {
            ResultsGroup rg = (ResultsGroup)results.get(i);
            if (this.databankSource != this.databankTarget) {
                rg = rg.clone();
            }
            passedResults.add(rg);
        }
        if (this.ca.perStrategy1 != null) {
            this.runPerStrategyAnalysis(this.ca.perStrategy1, passedResults, this.ca.inputArgsPerStrategy1);
        }
        if (this.ca.fullDatabank1 != null) {
            passedResults = this.runFullDatabankAnalysis(this.ca.fullDatabank1, passedResults, this.ca.inputArgsFullDatabank1);
        }
        if (this.ca.perStrategy2 != null) {
            this.runPerStrategyAnalysis(this.ca.perStrategy2, passedResults, this.ca.inputArgsPerStrategy2);
        }
        if (this.ca.fullDatabank2 != null) {
            passedResults = this.runFullDatabankAnalysis(this.ca.fullDatabank2, passedResults, this.ca.inputArgsFullDatabank2);
        }
        Object2ObjectOpenHashMap passedMap = new Object2ObjectOpenHashMap();
        for (int i = 0; i < passedResults.size(); ++i) {
            passedMap.put((Object)passedResults.get(i).getName(), (Object)passedResults.get(i));
        }
        for (int i = results.size() - 1; i >= 0; --i) {
            ResultsGroup rg = (ResultsGroup)results.get(i);
            if (passedMap.containsKey((Object)rg.getName())) {
                if (this.databankSource.getName().equals(this.databankTarget.getName())) continue;
                this.databankTarget.add((ResultsGroup)passedMap.get((Object)rg.getName()), true);
                this.progressEngine.printToLogDebug("   - " + L.t((String)"%s, moved to : %s", (Object[])new Object[]{rg.getName(), this.databankTarget.getName()}));
                continue;
            }
            if (!this.ca.filter) continue;
            this.databankSource.remove(rg.getName(), true, true, true, true, LockCustomAnalysisTask);
            this.progressEngine.printToLogDebug("   - " + L.t((String)"%s, removed from : %s", (Object[])new Object[]{rg.getName(), this.databankSource.getName()}));
        }
        this.progressEngine.finish();
    }

    private ArrayList<ResultsGroup> runFullDatabankAnalysis(CustomAnalysisMethod method, ArrayList<ResultsGroup> results, String inputArgs) throws Exception {
        method.setProjectLog(this.projectLogMessage);
        method.setInputArgs(inputArgs);
        ArrayList passedResults = method.processDatabank(this.project.getName(), this.getTitle(), this.databankSource.getName(), results);
        this.projectLogMessage = method.getProjectLog();
        return passedResults;
    }

    private void runPerStrategyAnalysis(CustomAnalysisMethod method, ArrayList<ResultsGroup> results, String caInputArgs) throws Exception {
        for (int i = results.size() - 1; i >= 0; --i) {
            ResultsGroup rg = results.get(i);
            this.printToLog(L.t((String)"%s, running Per strategy analysis: %s", (Object[])new Object[]{rg.getName(), method.name}));
            method.setInputArgs(caInputArgs);
            if (!method.filterStrategy(this.project.getName(), this.getTitle(), this.databankSource.getName(), rg)) {
                this.printToLog("   - Failed");
                results.remove(i);
                continue;
            }
            this.printToLog("   - OK");
        }
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskCustomAnalysis";
    }

    public int getPreferredPosition() {
        return 500;
    }

    public String[] getSettings() {
        return new String[]{"CustomAnalysis", "Databanks"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    private void printToLog(String text) {
        this.projectLogMessage = this.projectLogMessage + text + "\n";
        this.progressEngine.printToLogDebug(text);
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        if (!this.projectLogMessage.isEmpty()) {
            log.print(this.projectLogMessage, false);
        }
        super.logTaskFinished(log);
    }
}

