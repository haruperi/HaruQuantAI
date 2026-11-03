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
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder;

import com.strategyquant.lib.L;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tomas Brynda")
@Name(name="AutomaticPortfolioBuilder Task plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class AutomaticPortfolioBuilderTask
extends AbstractTask {
    private String projectLogMessage = "";

    public AutomaticPortfolioBuilderTask() throws Exception {
        super(null, null);
    }

    public AutomaticPortfolioBuilderTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "AutomaticPortfolioBuilder";
    }

    public String getName() {
        return L.tsq((String)"Automatic Portfolio Builder");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        AutomaticPortfolioBuilderTask task = new AutomaticPortfolioBuilderTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public void start() throws Exception {
        this.project = ProjectEngine.get((String)this.projectName);
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting PortfolioMaster...", (Object[])new Object[0]));
        this.progressEngine.start();
        try {
            this.checkSpecialTrialLimitation();
            PortfolioMasterSettings settings = (PortfolioMasterSettings)this.settingsData.getParams().get("AutomaticPortfolioBuilder");
            AutomaticPortfolioBuilder pb = new AutomaticPortfolioBuilder();
            pb.start(this.project, this.progressEngine, settings);
        }
        catch (OutOfMemoryError e) {
            this.project.onMemoryError((Error)e);
        }
        this.progressEngine.finish();
    }

    private void printToLog(String text) {
        this.projectLogMessage = this.projectLogMessage + text + "\n";
    }

    private void printToBothLogs(String text) {
        this.progressEngine.printToLog(text);
        this.projectLogMessage = this.projectLogMessage + "- " + text + "\n";
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskAutomaticPortfolioBuilder";
    }

    public int getPreferredPosition() {
        return 3;
    }

    public String[] getSettings() {
        return new String[]{"AutomaticPortfolioBuilder", "Databanks"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        if (!this.projectLogMessage.isEmpty()) {
            log.print(this.projectLogMessage, false);
        }
        super.logTaskFinished(log);
        log.print(this.logMessage);
    }
}

