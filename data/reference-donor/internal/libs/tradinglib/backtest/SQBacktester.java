/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtest.IBacktester;
import com.strategyquant.tradinglib.backtest.ResultsPanelData;
import com.strategyquant.tradinglib.backtest.SQBacktesterJob;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.StampedLock;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQBacktester
implements IBacktester {
    private static final Logger Log = LoggerFactory.getLogger(SQBacktester.class);
    private static StampedLock lock = new StampedLock();
    private static final int lockTimeout = 2;
    private static long stamp = 0L;
    private static SQBacktester instance;
    private static HashMap<String, String> jobToBacktestMap;
    private static HashMap<String, ResultsGroup> resultsMap;
    private static String serverUrl;
    private static int serverPort;
    private GridClient gridClient;
    private String jobGroupID;
    private long jobCount = 0L;
    private Thread timeoutThread;
    DataToSend dataProgress = new DataToSend("backtestProgress", new JSONObject());
    DataToSend dataMessage = new DataToSend("backtestMessage", new JSONObject());

    private SQBacktester() {
        this.jobGroupID = UUID.randomUUID().toString();
        this.gridClient = SQGrid.getGridClient();
        this.gridClient.registerMessageListener(this.jobGroupID, new IGridMessageListener(){

            public void messageReceived(GridMessage gridMessage) {
                SQBacktester.this.processMessage(gridMessage);
            }
        });
    }

    public static SQBacktester get() {
        if (instance == null) {
            instance = new SQBacktester();
        }
        return instance;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void run(String string, ChartSetup chartSetup, Map<String, Serializable> map) throws Exception {
        long l = lock.writeLock();
        try {
            this.dataProgress.setDataObject(new JSONObject());
            this.dataProgress.getDataObject().put("backtestID", (Object)string);
            this.dataProgress.getDataObject().put("percent", 0);
            String string2 = String.format(map.get("StrategyName") + "_%d", this.jobCount++);
            jobToBacktestMap.put(string2, string);
            this.gridClient.executeOnGrid(this.jobGroupID, (GridJob)new SQBacktesterJob(string2, map, new JobLastEventListener(string)));
        }
        finally {
            lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected synchronized void processMessage(GridMessage gridMessage) {
        long l = lock.writeLock();
        try {
            String string;
            JobDetails jobDetails = gridMessage.getJobDetails();
            String string2 = string = jobDetails != null ? jobDetails.getJobID() : gridMessage.getCustomID();
            if (!jobToBacktestMap.containsKey(string)) {
                Log.error("Unrecognized backtest by jobID " + string);
                return;
            }
            String string3 = jobToBacktestMap.get(string);
            this.dataProgress.setDataObject(new JSONObject());
            this.dataProgress.getDataObject().put("backtestID", (Object)string3);
            if (gridMessage.getMessageID() == 6) {
                int n = (Integer)gridMessage.getData();
                this.dataProgress.getDataObject().put("percent", n);
                SQWebSocketManager.addToDataQueue(this.dataProgress, "AlgoWizard");
            } else if (gridMessage.getMessageID() == 1) {
                jobDetails = gridMessage.getJobDetails();
                if (this.timeoutThread != null && this.timeoutThread.isAlive()) {
                    this.timeoutThread.interrupt();
                }
                if (jobDetails.isSuccess()) {
                    BacktestResult backtestResult = (BacktestResult)gridMessage.getData();
                    try {
                        ResultsGroup resultsGroup = backtestResult.getResult();
                        if (resultsGroup == null) {
                            throw new Exception(backtestResult.getDismissalMessage());
                        }
                        resultsMap.put(string3, resultsGroup.clone());
                        ResultsPanelData.load(resultsGroup, this.dataProgress.getDataObject(), new JSONObject());
                        this.dataProgress.getDataObject().put("percent", 100);
                        this.dataProgress.getDataObject().put("nodeURL", (Object)(serverUrl + ":" + serverPort));
                        SQWebSocketManager.addToDataQueue(this.dataProgress, "AlgoWizard");
                    }
                    catch (Exception exception) {
                        Log.error("Backtest failed", (Throwable)exception);
                        this.dataProgress.getDataObject().put("error", (Object)(exception.getMessage() != null ? exception.getMessage() : "null"));
                        SQWebSocketManager.addToDataQueue(this.dataProgress, "AlgoWizard");
                    }
                } else {
                    Log.error("Backtest failed", (Object)jobDetails.getException());
                    this.dataProgress.getDataObject().put("error", (Object)SQBacktester.getFirstLine(jobDetails.getException()));
                    SQWebSocketManager.addToDataQueue(this.dataProgress, "AlgoWizard");
                }
            }
        }
        catch (Exception exception) {
            Log.error("Exception while processing message", (Throwable)exception);
        }
        finally {
            lock.unlock(l);
        }
    }

    private static String getFirstLine(String string) {
        return string == null ? "NullPointer - see log" : string.split("\n")[0];
    }

    @Override
    public void stop(String string) throws Exception {
        SQBacktester.lock();
        try {
            Log.info("Stopping backtest with id " + string + "...");
            String string2 = this.findJobIDByBacktestID(string);
            if (string2 == null) {
                throw new Exception(L.t((String)"Job not found for backtestID %s", (Object[])new Object[]{string}));
            }
            this.gridClient.sendMessage(this.jobGroupID, string2, new GridMessage(5, "StopBacktest"));
        }
        finally {
            lock.unlock(stamp);
        }
    }

    private String findJobIDByBacktestID(String string) {
        for (Map.Entry<String, String> entry : jobToBacktestMap.entrySet()) {
            if (!entry.getValue().equals(string)) continue;
            return entry.getKey();
        }
        return null;
    }

    private static void lock() throws Exception {
        stamp = lock.tryWriteLock(2L, TimeUnit.SECONDS);
        if (stamp == 0L) {
            throw new Exception(L.t((String)"Cannot acquire lock. Stamp is 0", (Object[])new Object[0]));
        }
    }

    public static ResultsGroup getResultsGroup(String string) throws Exception {
        if (string == null) {
            throw new Exception(L.t((String)"backtestID cannot be null.", (Object[])new Object[0]));
        }
        if (string.trim().isEmpty()) {
            throw new Exception(L.t((String)"backtestID is not set.", (Object[])new Object[0]));
        }
        if (!resultsMap.containsKey(string)) {
            throw new Exception(L.t((String)"Backtest not found for id %s", (Object[])new Object[]{string}));
        }
        return resultsMap.get(string);
    }

    @Override
    public void setServerInfo(String string, int n) {
        serverUrl = string;
        serverPort = n;
    }

    static {
        jobToBacktestMap = new HashMap();
        resultsMap = new HashMap();
        serverUrl = "http://localhost";
        serverPort = 8080;
    }

    private class JobLastEventListener
    implements ILastEventListener {
        private String backtestID;

        public JobLastEventListener(String string) {
            this.backtestID = string;
        }

        @Override
        public void setLastEvent(String string) {
            SQBacktester.this.dataMessage.setDataObject(new JSONObject());
            SQBacktester.this.dataMessage.getDataObject().put("backtestID", (Object)this.backtestID);
            SQBacktester.this.dataMessage.getDataObject().put("message", (Object)string);
            SQWebSocketManager.addToDataQueue(SQBacktester.this.dataMessage, "AlgoWizard");
        }
    }
}

