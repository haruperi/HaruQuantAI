/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.EmailSender
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
package com.strategyquant.plugin.Task.impl.Notification;

import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.EmailSender;
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
import java.io.Serializable;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONObject;

@Author(name="Tamas Takacs")
@Name(name="NotificationTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class NotificationTask
extends AbstractTask {
    private String type;
    private String email;
    private boolean pause;
    private String smtpServer;
    private int smtpPort;
    private String smtpUsername;
    private String smtpPassword;
    private String smtpEmailFrom;
    private boolean smtpSSL;
    private String logMessage;

    public NotificationTask() throws Exception {
        super(null, null);
    }

    public NotificationTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "Notification";
    }

    public String getName() {
        return L.tsq((String)"Notification");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        NotificationTask task = new NotificationTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() {
        this.type = (String)this.settingsData.getParams().get("Type");
        this.email = (String)this.settingsData.getParams().get("Email");
        this.pause = (Boolean)this.settingsData.getParams().get("PauseProject");
        if (this.type.toLowerCase().equals("email")) {
            this.smtpServer = (String)this.settingsData.getParams().get("SMTPServer");
            this.smtpPort = (Integer)this.settingsData.getParams().get("SMTPPort");
            this.smtpUsername = (String)this.settingsData.getParams().get("SMTPUsername");
            this.smtpPassword = (String)this.settingsData.getParams().get("SMTPPassword");
            this.smtpEmailFrom = (String)this.settingsData.getParams().get("SMTPEmailFrom");
            this.smtpSSL = (Boolean)((Serializable)this.settingsData.getParams().get("SMTPUseSSL"));
        }
    }

    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Processing notification...", (Object[])new Object[0]));
        this.progressEngine.start();
        this.logMessage = null;
        String text = L.t((String)"Task notification for project %s", (Object[])new Object[]{this.projectName});
        if (this.pause) {
            text = text + "\n\n" + L.t((String)"Note - Project is paused, waiting for your action.", (Object[])new Object[0]) + "\n" + L.t((String)"Please don't reply to this email, it is not watched!", (Object[])new Object[0]) + "\n";
        }
        if (this.type.toLowerCase().equals("email")) {
            try {
                EmailSender.sendTo((String)this.smtpServer, (int)this.smtpPort, (String)this.smtpUsername, (String)this.smtpPassword, (String)L.t((String)"SQ Task notification for project %s", (Object[])new Object[]{this.projectName}), (String)text, (String)this.smtpEmailFrom, (String)this.email, (boolean)this.smtpSSL);
                this.logMessage = L.t((String)"Task notification was successfully sent.", (Object[])new Object[0]);
                this.progressEngine.printToLog(this.logMessage);
            }
            catch (Exception e) {
                Log.error("Exc.", (Throwable)e);
                this.logMessage = L.t((String)"Task notification could not be sent. Please check your SMTP settings.", (Object[])new Object[0]);
                this.progressEngine.printToLog(this.logMessage);
            }
        } else if (this.type.toLowerCase().equals("popup")) {
            JSONObject data = new JSONObject();
            data.put("projectName", (Object)this.projectName);
            data.put("taskName", (Object)this.customName);
            data.put("projectPaused", this.pause);
            DataToSend dataToSend = new DataToSend("customProjectNotification", data);
            SQWebSocketManager.addToDataQueue((DataToSend)dataToSend, (String[])new String[]{"SQUANT"});
        }
        if (this.pause) {
            String message = L.t((String)"Project is paused, waiting for your action.", (Object[])new Object[0]);
            this.logMessage = this.logMessage + "\n" + message;
            this.progressEngine.printToLog(message);
            this.progressEngine.pause();
            this.progressEngine.checkPaused();
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskNotification";
    }

    public int getPreferredPosition() {
        return 5;
    }

    public String[] getSettings() {
        return new String[]{"Notification"};
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

