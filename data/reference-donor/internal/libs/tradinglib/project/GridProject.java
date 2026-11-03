/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.RunningStatus
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.RunningStatus;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.project.Databanks;
import com.strategyquant.tradinglib.project.IProject;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQLogger;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class GridProject
implements IProject {
    private static final Logger Log = LoggerFactory.getLogger(GridProject.class);
    protected Databanks databanks;
    private boolean stopped = false;
    private boolean paused = false;
    private boolean feedFinished = false;
    private long lastProcessedIndex;
    private int runningStatus = 0;
    private String projectName = null;
    protected Thread taskGrid = null;
    private long lastSentProgress = 0L;
    protected GridClient gridClient;
    private int progressType = 1;
    private long progressValue = 0L;
    private long progressMax = 0L;

    public GridProject(String string) throws Exception {
        this.projectName = string;
        this.databanks = new Databanks(string);
        this.lastProcessedIndex = 0L;
        this.gridClient = SQGrid.getGridClient();
    }

    @Override
    public Databanks getDatabanks() {
        return this.databanks;
    }

    @Override
    public Element getConfig() throws Exception {
        return ProjectEngine.get(this.projectName).getConfig();
    }

    public abstract void projectStart() throws Exception;

    @Override
    public void start() throws Exception {
        try {
            this.setRunningStatus(1);
            this.initStart();
            this.taskGrid = new Thread(){

                @Override
                public void run() {
                    try {
                        GridProject.this.projectStart();
                    }
                    catch (Exception exception) {
                        Log.error("Exc.", (Throwable)exception);
                        GridProject.this.changeProjectStatus(50, GridProject.this.getExceptionString(exception));
                    }
                }
            };
            this.taskGrid.start();
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            this.changeProjectStatus(50, this.getExceptionString(exception));
            throw exception;
        }
    }

    private String getExceptionString(Exception exception) {
        String string = SQUtils.stackTraceToString((Throwable)exception);
        return string.length() > 500 ? string.substring(0, 500) : string;
    }

    private void initStart() throws Exception {
        this.stopped = false;
        this.paused = false;
        this.feedFinished = false;
        if (this.taskGrid != null && this.taskGrid.isAlive()) {
            throw new Exception(L.t((String)"Project '%s' is already running.", (Object[])new Object[]{this.projectName}));
        }
    }

    public boolean isStopped() {
        return this.stopped;
    }

    public boolean isPaused() {
        return this.paused;
    }

    @Override
    public void stop() {
        this.printLog("Stopping...");
        this.stopped = true;
        this.printLog("Stopped");
        this.lastProcessedIndex = 0L;
        this.progressValue = 0L;
    }

    @Override
    public void pause() {
        this.printLog("Pausing...");
        this.paused = true;
        this.setRunningStatus(2);
    }

    @Override
    public void resume() throws Exception {
        this.start();
    }

    protected long getLastProcessedIndex() {
        return this.lastProcessedIndex;
    }

    protected void setLastProcessedIndex(long l) {
        this.lastProcessedIndex = l;
    }

    protected void setProgressType(int n) {
        this.progressType = n;
        this.sendProgressInfo();
    }

    protected void setProgressMax(long l) {
        this.progressMax = l;
        this.sendProgressInfo();
    }

    protected void increaseProgress() {
        ++this.progressValue;
        this.sendProgressInfo();
    }

    private void sendProgressInfo() {
        boolean bl;
        long l = (long)((double)this.progressValue / (double)this.progressMax * 100.0);
        boolean bl2 = bl = this.progressType == 0;
        if (bl) {
            l = 100L;
        } else if (this.lastSentProgress == l) {
            return;
        }
        this.lastSentProgress = l;
    }

    @Override
    public int getRunningStatus() {
        return this.runningStatus;
    }

    @Override
    public void setRunningStatus(int n) {
        this.changeProjectStatus(n, null);
    }

    private void changeProjectStatus(int n, String string) {
        this.runningStatus = n;
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("projectName", (Object)this.projectName);
        jSONObject.put("status", n);
        if (n == 50) {
            this.printLog("Running error: " + string);
            this.stop();
        }
        Log.info("Project status changed to " + RunningStatus.printStatus((int)n));
    }

    protected void printLog(String string) {
        SQLogger.log(this.projectName, string);
        Log.info(string);
    }

    @Override
    public String getName() {
        return this.projectName;
    }

    public String getProduct() {
        return "SQUANTTESTAPP";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }
}

