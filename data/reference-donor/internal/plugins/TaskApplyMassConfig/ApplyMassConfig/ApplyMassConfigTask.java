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
 *  com.strategyquant.tradinglib.applyMassConfig.ApplyMassConfig
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.ApplyMassConfig;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.applyMassConfig.ApplyMassConfig;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tomas Brynda")
@Name(name="ApplyMassConfigTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Apply mass config")
@PluginImplementation
public class ApplyMassConfigTask
extends AbstractTask {
    private ApplyMassConfig applyMassConfig;

    public ApplyMassConfigTask() throws Exception {
        super(null, null);
    }

    public ApplyMassConfigTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "ApplyMassConfig";
    }

    public String getName() {
        return L.tsq((String)"Apply mass config");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        ApplyMassConfigTask task = new ApplyMassConfigTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public void start() throws Exception {
        this.applyMassConfig = (ApplyMassConfig)this.settingsData.getParams().get("ApplyMassConfig");
        this.project = ProjectEngine.get((String)this.projectName);
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Applying mass config...", (Object[])new Object[0]));
        this.progressEngine.start();
        this.applyMassConfig.applyChangesToTasks(this.project, this.progressEngine);
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskApplyMassConfig";
    }

    public int getPreferredPosition() {
        return 3;
    }

    public String[] getSettings() {
        return new String[]{"ApplyMassConfig"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }
}

