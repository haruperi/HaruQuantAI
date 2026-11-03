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
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.ClearDatabanks;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tomas Brynda")
@Name(name="Clear databanks task plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class ClearDatabanksTask
extends AbstractTask {
    private ArrayList<String> databanksToClear;

    public ClearDatabanksTask() throws Exception {
        super(null, null);
    }

    public ClearDatabanksTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "ClearDatabanks";
    }

    public String getName() {
        return L.tsq((String)"Clear databanks");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        ClearDatabanksTask task = new ClearDatabanksTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public void start() throws Exception {
        this.project = ProjectEngine.get((String)this.projectName);
        this.databanksToClear = (ArrayList)this.settingsData.getParams().get("DatabanksToClear");
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Clearing databanks...", (Object[])new Object[0]));
        this.progressEngine.start();
        try {
            if (this.databanksToClear.contains("all")) {
                for (Databank databank : this.project.getDatabanks().list()) {
                    databank.clearRecords(true, true, String.format("'Clear databanks task' %s/%s, clear all databanks - databank %s/%s", this.projectName, this.getTitle(), this.projectName, databank.getName()));
                }
                this.progressEngine.printToLog(L.t((String)"Cleared all databanks", (Object[])new Object[0]));
            } else {
                for (int i = 0; i < this.databanksToClear.size(); ++i) {
                    Databank databank = (Databank)this.project.getDatabanks().get((Object)this.databanksToClear.get(i));
                    if (databank == null) {
                        this.progressEngine.printToLog(L.t((String)"Error: Databank %s not found", (Object[])new Object[]{this.databanksToClear.get(i)}));
                        continue;
                    }
                    databank.clearRecords(true, true, String.format("'Clear databanks task' %s/%s, clear selected databanks - databank %s/%s", this.projectName, this.getTitle(), this.projectName, databank.getName()));
                    this.progressEngine.printToLog(L.t((String)"Cleared databank '%s'", (Object[])new Object[]{databank.getName()}));
                }
            }
        }
        catch (OutOfMemoryError e) {
            this.project.onMemoryError((Error)e);
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskClearDatabanks";
    }

    public int getPreferredPosition() {
        return 10;
    }

    public String[] getSettings() {
        return new String[]{"ClearDatabanks"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        String text = this.databanksToClear.toString().replaceAll("[\\[.\\]]", "");
        log.print(L.t((String)"- Databanks cleared", (Object[])new Object[0]) + ": " + text);
        super.logTaskFinished(log);
    }
}

