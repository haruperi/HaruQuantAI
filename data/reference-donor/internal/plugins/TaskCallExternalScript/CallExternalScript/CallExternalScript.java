/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
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
package com.strategyquant.plugin.Task.impl.CallExternalScript;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
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
import java.util.Timer;
import java.util.TimerTask;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Call external script")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class CallExternalScript
extends AbstractTask {
    private String file;
    private String params;
    private String type;
    private long runTime;

    public CallExternalScript() throws Exception {
        super(null, null);
    }

    public CallExternalScript(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "CallExternalScript";
    }

    public String getName() {
        return L.tsq((String)"Call external script");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        CallExternalScript task = new CallExternalScript(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() {
        this.file = (String)this.settingsData.getParams().get("File");
        this.params = (String)this.settingsData.getParams().get("Params");
        this.type = (String)this.settingsData.getParams().get("Type");
        this.runTime = (Long)this.settingsData.getParams().get("MaxBuildRunTime");
    }

    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.start();
        File f = new File(this.file);
        if (f.exists()) {
            this.printLog(String.format("Executing script '%s'", f.getName()));
            String command = this.file;
            if (this.params != null && !this.params.isBlank()) {
                command = command + " " + this.params;
            }
            Process proc = Runtime.getRuntime().exec(command);
            if (this.type.equals("time")) {
                this.printLog(L.t((String)"Project is paused, waiting for %s", (Object[])new Object[]{SQTime.formatDateTime((long)(this.runTime / 1000L))}));
                Timer timer = new Timer();
                timer.schedule(new TimerTask(){

                    @Override
                    public void run() {
                        CallExternalScript.this.progressEngine.resume();
                    }
                }, this.runTime);
                this.progressEngine.pause();
                this.progressEngine.checkPaused();
            } else {
                this.printLog(L.t((String)"Project is paused, waiting for script.", (Object[])new Object[0]));
                proc.waitFor();
                this.printLog(L.t((String)"Script done.", (Object[])new Object[0]));
                this.progressEngine.resume();
            }
        } else {
            this.printLog(String.format("Script '%s' doesn't exist.", f.getName()));
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskCallExternalScript";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public String[] getSettings() {
        return new String[]{"CallExternalScript"};
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

