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
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.DeleteFile;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Delete file")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class DeleteFileTask
extends AbstractTask {
    private String logMessage;
    private String file;

    public DeleteFileTask() throws Exception {
        super(null, null);
    }

    public DeleteFileTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "DeleteFile";
    }

    public String getName() {
        return L.tsq((String)"Delete file");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        DeleteFileTask task = new DeleteFileTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() {
        this.file = (String)this.settingsData.getParams().get("File");
    }

    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Deleting file...", (Object[])new Object[0]));
        this.progressEngine.start();
        try {
            File f = new File(this.file);
            if (!f.exists()) {
                throw new Exception(L.t((String)"File '%s' not found.", (Object[])new Object[]{f.getName()}));
            }
            if (!f.delete()) {
                throw new Exception(L.t((String)"File '%s' cannot be deleted.", (Object[])new Object[]{f.getName()}));
            }
            this.progressEngine.printToLog(L.t((String)"File '%s' deleted.", (Object[])new Object[]{f.getName()}));
            this.logMessage = L.t((String)"File '%s' deleted.", (Object[])new Object[]{f.getName()});
        }
        catch (Exception ex) {
            Log.error("Error while loading strategies. Exc.", (Throwable)ex);
            this.progressEngine.printToLog(ex.getMessage());
            this.logMessage = ex.getMessage();
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskDeleteFile";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public String[] getSettings() {
        return new String[]{"DeleteFile"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        log.print(this.logMessage);
    }
}

