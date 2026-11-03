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
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.CreatePortfolio;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Create portfolio plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class CreatePortfolio
extends AbstractTask {
    private Databank databankSource = null;
    private Databank databankTarget = null;
    private int maxStrategies = 100;
    private int strategies;
    private String logMessage;

    public CreatePortfolio() throws Exception {
        super(null, null);
    }

    public CreatePortfolio(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    private void init() {
        this.strategies = 0;
        this.logMessage = null;
        this.databankSource = (Databank)this.settingsData.getParams().get("DatabankSource");
        this.databankTarget = (Databank)this.settingsData.getParams().get("DatabankTarget");
        this.maxStrategies = (Integer)this.settingsData.getParams().get("MaxStrategies");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting...", (Object[])new Object[0]));
        this.progressEngine.start();
        ArrayList sourceResults = this.databankSource.getRecords();
        ArrayList<ResultsGroup> results = new ArrayList<ResultsGroup>();
        try {
            for (int i = sourceResults.size() - 1; i >= 0 && results.size() != this.maxStrategies; --i) {
                ResultsGroup rg = this.databankSource.getLocked(((ResultsGroup)sourceResults.get(i)).getName(), "CreatePortfolioTask");
                results.add(rg);
                ++this.strategies;
            }
            if (sourceResults.isEmpty()) {
                this.logMessage = L.t((String)"Portfolio cannot be created because databank '%s' is empty.", (Object[])new Object[]{this.databankSource.getName()});
                this.progressEngine.printToLog(L.t((String)"Portfolio not created: databank '%s' is empty.", (Object[])new Object[]{this.databankSource.getName()}));
            } else if (results.size() < 2) {
                this.logMessage = L.t((String)"Portfolio cannot be created because databank '%s' contains only one strategy.", (Object[])new Object[]{this.databankSource.getName()});
                this.progressEngine.printToLog(L.t((String)"Portfolio not created: databank '%s' contains only one strategy.", (Object[])new Object[]{this.databankSource.getName()}));
            } else {
                ResultsGroup portfolio = ResultsGroup.merge(results, (String[])new String[]{"AdditionalMarket", "CrossCheck_"}, null);
                portfolio.createPortfolioResult();
                this.databankTarget.add(portfolio, true);
                this.databankTarget.updateBestResults(portfolio);
                this.progressEngine.printToLog(L.t((String)"Portfolio created from %d strategies.", (Object[])new Object[]{this.strategies}));
            }
        }
        finally {
            for (ResultsGroup rg : results) {
                rg.releaseLock("CreatePortfolioTask");
            }
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskCreatePortfolio";
    }

    public int getPreferredPosition() {
        return 10;
    }

    public String getType() {
        return "CreatePortfolio";
    }

    public String getName() {
        return L.tsq((String)"Create portfolio");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        CreatePortfolio task = new CreatePortfolio(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public String[] getSettings() {
        return new String[]{"CreatePortfolio"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return this.databankTarget;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        if (this.logMessage == null) {
            log.print(L.t((String)"Portfolio created from %d strategies from source databank '%s' saved to target databank '%s'.", (Object[])new Object[]{this.strategies, this.databankSource.getName(), this.databankTarget.getName()}));
        } else {
            log.print(this.logMessage);
        }
    }
}

