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
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Task.impl.WaitFor;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONObject;

@Author(name="Tamas Takacs")
@Name(name="Wait for user/file")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class WaitForTask
extends AbstractTask {
    private String logMessage;
    private String file;
    private String action;

    public WaitForTask() throws Exception {
        super(null, null);
    }

    public WaitForTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "WaitFor";
    }

    public String getName() {
        return L.tsq((String)"Wait for user/file");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        WaitForTask task = new WaitForTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() {
        this.file = (String)this.settingsData.getParams().get("File");
        this.action = (String)this.settingsData.getParams().get("ActionType");
    }

    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.start();
        this.logMessage = null;
        boolean paused = false;
        if (this.action.equals("user")) {
            paused = true;
            this.logMessage = L.t((String)"Project is paused, waiting for your action.", (Object[])new Object[0]);
            JSONObject data = new JSONObject();
            data.put("projectName", (Object)this.projectName);
            data.put("taskName", (Object)this.customName);
            data.put("projectPaused", true);
            DataToSend dataToSend = new DataToSend("customProjectNotification", data);
            SQWebSocketManager.addToDataQueue((DataToSend)dataToSend, (String[])new String[]{"SQUANT"});
        } else {
            final File f = new File(this.file);
            if (f.exists()) {
                this.logMessage = L.t((String)"File '%s' exists. Project continues with the next task.", (Object[])new Object[]{f.getName()});
            } else {
                paused = true;
                this.logMessage = L.t((String)"Project is paused, waiting for file '%s'.", (Object[])new Object[]{f.getName()});
                new Thread(this){
                    final /* synthetic */ WaitForTask this$0;
                    {
                        this.this$0 = this$0;
                    }

                    @Override
                    public void run() {
                        while (true) {
                            try {
                                Thread.sleep(1000L);
                            }
                            catch (Exception exception) {
                                // empty catch block
                            }
                            try {
                                if (!f.exists()) continue;
                                String message = L.t((String)"File '%s' exists.", (Object[])new Object[]{f.getName()});
                                this.this$0.logMessage = this.this$0.logMessage + ("\n" + message);
                                this.this$0.progressEngine.printToLog(message);
                                this.this$0.progressEngine.resume();
                                return;
                            }
                            catch (Exception e) {
                                AbstractTask.Log.error("Exc.", (Throwable)e);
                                continue;
                            }
                            break;
                        }
                    }
                }.start();
            }
        }
        this.progressEngine.printToLog(this.logMessage);
        if (paused) {
            this.progressEngine.pause();
            this.progressEngine.checkPaused();
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskWaitFor";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public String[] getSettings() {
        return new String[]{"WaitFor"};
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

