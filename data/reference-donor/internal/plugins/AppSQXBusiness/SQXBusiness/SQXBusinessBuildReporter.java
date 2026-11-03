/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  com.strategyquant.lib.sqxbusiness.BuildData
 *  com.strategyquant.lib.sqxbusiness.MQLMarketBuildResult
 *  com.strategyquant.lib.sqxbusiness.MQLMarketConst
 *  com.strategyquant.lib.sqxbusiness.MQLMarketLoggable
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  org.json.JSONArray
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.lib.sqxbusiness.BuildData;
import com.strategyquant.lib.sqxbusiness.MQLMarketBuildResult;
import com.strategyquant.lib.sqxbusiness.MQLMarketConst;
import com.strategyquant.lib.sqxbusiness.MQLMarketLoggable;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.locks.StampedLock;
import org.json.JSONArray;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQXBusinessBuildReporter
implements IGridMessageListener,
MQLMarketLoggable {
    private static final Logger Log = LoggerFactory.getLogger(SQXBusinessBuildReporter.class);
    private static final DataToSend wsData = new DataToSend("buildUpdates");
    private static SQXBusinessBuildReporter instance;
    private static ArrayList<String> allGroupIDs;
    private static HashMap<String, HashMap<String, BuildData>> allBuilds;
    private static StampedLock groupIDsLock;
    private static StampedLock buildsLock;

    private SQXBusinessBuildReporter() {
        new Thread(){

            @Override
            public void run() {
                while (true) {
                    try {
                        1.sleep(1000L);
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    SQXBusinessBuildReporter.this.sendWSUpdates();
                }
            }
        }.start();
    }

    public static SQXBusinessBuildReporter get() {
        if (instance == null) {
            instance = new SQXBusinessBuildReporter();
        }
        return instance;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void messageReceived(GridMessage message) {
        block32: {
            long stamp;
            try {
                if (SQProject.isMemoryProtectionUsed()) {
                    MemoryUsageChecker.checkAvailableMemory();
                }
            }
            catch (OutOfMemoryError e) {
                Log.error("Out of memory error occurred. Stopping all jobs...");
                stamp = groupIDsLock.readLock();
                try {
                    for (int a = 0; a < allGroupIDs.size(); ++a) {
                        String jobGroupID = allGroupIDs.get(a);
                        Log.info("Stopping jobGroupID " + jobGroupID + "...");
                        SQGrid.getGridClient().stop(jobGroupID);
                    }
                }
                finally {
                    groupIDsLock.unlock(stamp);
                }
            }
            JobDetails jobDetails = message.getJobDetails();
            if (message.getMessageID() == 1) {
                try {
                    if (jobDetails.isSuccess()) {
                        MQLMarketBuildResult result = (MQLMarketBuildResult)message.getData();
                        long stamp2 = buildsLock.writeLock();
                        try {
                            BuildData data = SQXBusinessBuildReporter.getBuildData(jobDetails.getJobID());
                            if (result.exception != null) {
                                data.addLogLine("Compilation failed - " + result.exception.getMessage());
                                data.status = 5;
                                data.changed = true;
                            } else {
                                data.addLogLine("Compilation done");
                                data.status = 2;
                                data.changed = true;
                            }
                            break block32;
                        }
                        finally {
                            buildsLock.unlock(stamp2);
                        }
                    }
                    stamp = buildsLock.writeLock();
                    try {
                        BuildData data = SQXBusinessBuildReporter.getBuildData(jobDetails.getJobID());
                        data.addLogLine("Compilation failed - " + jobDetails.getException());
                        data.status = 5;
                        data.changed = true;
                    }
                    finally {
                        buildsLock.unlock(stamp);
                    }
                }
                catch (Exception e) {
                    Log.error("Error while processing job message", (Throwable)e);
                }
            } else {
                if (message.getMessageID() == 4) {
                    stamp = buildsLock.writeLock();
                    try {
                        BuildData data = SQXBusinessBuildReporter.getBuildData(jobDetails.getJobID());
                        data.addLogLine("Compilation stopped");
                        data.status = 3;
                        data.changed = true;
                    }
                    finally {
                        buildsLock.unlock(stamp);
                    }
                }
                if (message.getMessageID() == 2) {
                    stamp = buildsLock.writeLock();
                    try {
                        BuildData data = SQXBusinessBuildReporter.getBuildData(jobDetails.getJobID());
                        data.addLogLine("Compilation paused");
                        data.status = 4;
                        data.changed = true;
                    }
                    finally {
                        buildsLock.unlock(stamp);
                    }
                }
                if (message.getMessageID() == 3) {
                    stamp = buildsLock.writeLock();
                    try {
                        BuildData data = SQXBusinessBuildReporter.getBuildData((String)((Object)message.getData()));
                        data.addLogLine("Compilation resumed");
                        data.status = 1;
                        data.changed = true;
                    }
                    finally {
                        buildsLock.unlock(stamp);
                    }
                }
            }
        }
    }

    public static void registerMessageListener(String jobGroupID) {
        long stamp = groupIDsLock.writeLock();
        try {
            if (!allGroupIDs.contains(jobGroupID)) {
                allGroupIDs.add(jobGroupID);
            }
        }
        finally {
            groupIDsLock.unlock(stamp);
        }
        SQGrid.getGridClient().registerMessageListener(jobGroupID, (IGridMessageListener)SQXBusinessBuildReporter.get());
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void addNewBuildData(String projectName, String jobGroupID, String jobID, String outputName, boolean isMT5) {
        long stamp = buildsLock.writeLock();
        try {
            if (!allBuilds.containsKey(projectName)) {
                allBuilds.put(projectName, new HashMap());
            }
            allBuilds.get(projectName).put(jobID, new BuildData(projectName, jobGroupID, jobID, outputName, isMT5));
        }
        catch (Exception e) {
            Log.error("Cannot add build data. ProjectName: " + projectName + ", jobID: " + jobID, (Throwable)e);
        }
        finally {
            buildsLock.unlock(stamp);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void printToLog(String jobID, String message) {
        String projectName = MQLMarketConst.getProjectNameFromJobID((String)jobID);
        long stamp = buildsLock.writeLock();
        try {
            BuildData data = allBuilds.get(projectName).get(jobID);
            data.addLogLine(message);
        }
        catch (Exception e) {
            Log.error("Cannot add message to log. ProjectName: " + projectName + ", jobID: " + jobID, (Throwable)e);
        }
        finally {
            buildsLock.unlock(stamp);
        }
    }

    public static void clearLog(String jobID) {
        String projectName = MQLMarketConst.getProjectNameFromJobID((String)jobID);
        long stamp = buildsLock.writeLock();
        try {
            BuildData data = allBuilds.get(projectName).get(jobID);
            data.clearLog();
        }
        catch (Exception e) {
            Log.error("Cannot clear build log. ProjectName: " + projectName + ", jobID: " + jobID, (Throwable)e);
            throw e;
        }
        finally {
            buildsLock.unlock(stamp);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void setStatus(String jobID, int status) {
        String projectName = MQLMarketConst.getProjectNameFromJobID((String)jobID);
        long stamp = buildsLock.writeLock();
        try {
            BuildData data = allBuilds.get(projectName).get(jobID);
            data.status = status;
            data.changed = true;
        }
        catch (Exception e) {
            Log.error("Cannot set build status. ProjectName: " + projectName + ", jobID: " + jobID, (Throwable)e);
        }
        finally {
            buildsLock.unlock(stamp);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static JSONArray getBuildReports() {
        long stamp = buildsLock.writeLock();
        try {
            JSONArray array = new JSONArray();
            for (String projectName : allBuilds.keySet()) {
                HashMap<String, BuildData> jobsData = allBuilds.get(projectName);
                for (String jobID : jobsData.keySet()) {
                    BuildData data = jobsData.get(jobID);
                    if (data.changed) {
                        array.put((Object)data.toJSON());
                    }
                    data.changed = false;
                }
            }
            JSONArray jSONArray = array;
            return jSONArray;
        }
        catch (Exception e) {
            Log.error("Cannot get build reports", (Throwable)e);
            JSONArray jSONArray = null;
            return jSONArray;
        }
        finally {
            buildsLock.unlock(stamp);
        }
    }

    private static BuildData getBuildData(String jobID) {
        String projectName = MQLMarketConst.getProjectNameFromJobID((String)jobID);
        return allBuilds.get(projectName).get(jobID);
    }

    private void sendWSUpdates() {
        JSONArray reports = SQXBusinessBuildReporter.getBuildReports();
        if (reports.length() == 0) {
            return;
        }
        wsData.setDataObject(reports);
        SQWebSocketManager.addToDataQueue((DataToSend)wsData, (String[])new String[]{"SQXBUSINESS"});
    }

    public void _printToLog(String jobID, String message) {
        SQXBusinessBuildReporter.printToLog(jobID, message);
    }

    static {
        allGroupIDs = new ArrayList();
        allBuilds = new HashMap();
        groupIDsLock = new StampedLock();
        buildsLock = new StampedLock();
    }
}

