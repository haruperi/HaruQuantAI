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
 *  com.strategyquant.lib.utils.SQUUID
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.SQUUID;
import com.strategyquant.tradinglib.gp.GPEvolutionMessage;
import com.strategyquant.tradinglib.gp.GPEvolutionPopulationMessage;
import com.strategyquant.tradinglib.gp.GPGenerationalEngine;
import com.strategyquant.tradinglib.gp.GPIslandJob;
import com.strategyquant.tradinglib.gp.GPSettings;
import com.strategyquant.tradinglib.gp.IGPEvolutionMessagesListener;
import com.strategyquant.tradinglib.gp.IGPFinishedListener;
import com.strategyquant.tradinglib.gp.IGPNode;
import com.strategyquant.tradinglib.gp.IStopConditionsChecker;
import com.strategyquant.tradinglib.project.IProgressStatusListener;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GPEngine<T extends IGPNode>
implements IProgressStatusListener,
IGridMessageListener {
    private static final Logger Log = LoggerFactory.getLogger((String)"GPIslandsEngine");
    private GPSettings<T> gpSettings;
    private String gpGroupID;
    private GridClient gridClient;
    private IGPEvolutionMessagesListener<T> evolutionMessagesListener;
    private ArrayList<String> islandJobIds = new ArrayList();
    private StopPauseEngine stopPauseEngine;
    private int runningStatus = 0;
    private IGPFinishedListener gpFinishedListener;
    private ArrayList<T> initialPopulation = null;
    private GridJob parentGridJob;
    private GPIslandJob<T> singleThreadedIsland;
    private IStopConditionsChecker stopConditionsChecker;
    private String source;

    public GPEngine(GPSettings<T> gPSettings, StopPauseEngine stopPauseEngine, ArrayList<T> arrayList, GridJob gridJob, String string) {
        this(gPSettings, stopPauseEngine, arrayList, gridJob, string, null);
    }

    public GPEngine(GPSettings<T> gPSettings, StopPauseEngine stopPauseEngine, ArrayList<T> arrayList, GridJob gridJob, String string, IStopConditionsChecker iStopConditionsChecker) {
        this.gpSettings = gPSettings;
        this.stopPauseEngine = stopPauseEngine;
        this.initialPopulation = arrayList;
        this.parentGridJob = gridJob;
        this.stopConditionsChecker = iStopConditionsChecker;
        this.source = string;
        this.gpGroupID = SQUUID.randomUUID().substring(0, 6);
        this.checkSettings();
        this.gridClient = SQGrid.getGridClient();
        this.gridClient.registerMessageListener(this.gpGroupID, (IGridMessageListener)this);
        stopPauseEngine.registerStatusListener(this);
    }

    @Override
    public void onStatusChanged(int n) {
        if (n == 4 || n == 3 || n == 50) {
            if (this.singleThreadedIsland != null) {
                this.singleThreadedIsland.messageReceived(new GridMessage(4));
            } else {
                this.gridClient.stop(this.gpGroupID);
            }
            this.stopPauseEngine.unregisterStatusListener(this);
        } else if (n == 2) {
            if (this.runningStatus == 1) {
                this.runningStatus = n;
                if (this.singleThreadedIsland != null) {
                    this.singleThreadedIsland.messageReceived(new GridMessage(2));
                } else {
                    this.gridClient.pause(this.gpGroupID);
                }
            }
        } else if (n == 1 && this.runningStatus == 2) {
            this.runningStatus = n;
            if (this.singleThreadedIsland != null) {
                this.singleThreadedIsland.messageReceived(new GridMessage(3));
            } else {
                this.gridClient.restart(this.gpGroupID);
            }
        }
    }

    public void start() throws Exception {
        if (this.runningStatus == 0) {
            this.runningStatus = 1;
            if (this.gpSettings.singleThreaded && this.gpSettings.numberOfIslands != 1) {
                throw new Exception("Single threaded mode cannot be used if number of islands is bigger than 1!");
            }
            if (this.stopPauseEngine instanceof ProgressEngine) {
                // empty if block
            }
            ArrayList arrayList = new ArrayList();
            for (int i = 0; i < this.gpSettings.numberOfIslands; ++i) {
                Map<String, Serializable> map = this.getIslandParams(i);
                String string = GPIslandJob.createJobID(i, this.parentGridJob, this.source);
                this.islandJobIds.add(string);
                GPIslandJob gPIslandJob = new GPIslandJob(string, map, this.parentGridJob);
                arrayList.add(gPIslandJob);
            }
            Log.debug(L.t((String)"Created %d island jobs", (Object[])new Object[]{arrayList.size()}));
            if (this.gpSettings.singleThreaded) {
                if (arrayList.size() != 1) {
                    throw new Exception("Single threaded mode - incorrect number of island jobs: " + arrayList.size());
                }
                this.singleThreadedIsland = (GPIslandJob)((Object)arrayList.get(0));
                this.singleThreadedIsland.call();
                this.runningStatus = 3;
                if (this.gpFinishedListener != null) {
                    this.gpFinishedListener.finished(1);
                }
                this.gridClient.stop(this.gpGroupID);
                this.gridClient.removeMessageListener(this.gpGroupID);
            } else {
                this.gridClient.executeOnGrid(this.gpGroupID, arrayList);
            }
        }
    }

    protected void processMessage(GridMessage gridMessage) {
        JobDetails jobDetails = gridMessage.getJobDetails();
        if (jobDetails != null && jobDetails.getException() != null && jobDetails.getException().contains("OutOfMemoryError") && this.gpFinishedListener != null && this.gridClient.countAllJobs(this.gpGroupID) > 0L) {
            this.gpFinishedListener.finished(3);
            return;
        }
        if (gridMessage.getMessageID() == 1) {
            if (this.gridClient.countAllJobs(this.gpGroupID) == 1L) {
                Log.debug("GP Engine finished");
                if (jobDetails != null && jobDetails.getException() != null && this.stopPauseEngine instanceof ProgressEngine) {
                    ((ProgressEngine)this.stopPauseEngine).printToLog(L.t((String)"Genetic engine finished with exception %s", (Object[])new Object[]{jobDetails.getException()}));
                }
                this.runningStatus = 3;
                if (this.gpFinishedListener != null) {
                    this.gpFinishedListener.finished(1);
                }
                this.gridClient.stop(this.gpGroupID);
                this.gridClient.removeMessageListener(this.gpGroupID);
            }
        } else if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID().equals("GPEvaluatedCandidate")) {
            if (this.evolutionMessagesListener != null) {
                IGPNode iGPNode = (IGPNode)gridMessage.getData();
                this.evolutionMessagesListener.newCandidate(iGPNode);
            }
        } else if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID().equals("GPEvolutionStatus")) {
            if (this.evolutionMessagesListener != null) {
                GPEvolutionMessage gPEvolutionMessage = (GPEvolutionMessage)gridMessage.getData();
                this.evolutionMessagesListener.evolutionMessage(gPEvolutionMessage);
            }
        } else if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID().equals("GPException")) {
            if (this.evolutionMessagesListener != null) {
                this.evolutionMessagesListener.evolutionException(gridMessage.getData());
            }
        } else if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID().equals("GPLastPopulation") && this.evolutionMessagesListener != null) {
            GPEvolutionPopulationMessage gPEvolutionPopulationMessage = (GPEvolutionPopulationMessage)gridMessage.getData();
            this.evolutionMessagesListener.lastPopulation(gPEvolutionPopulationMessage);
        }
    }

    private Map<String, Serializable> getIslandParams(int n) {
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        hashMap.put("GPSettings", this.gpSettings);
        hashMap.put("GPGroupID", (Serializable)((Object)this.gpGroupID));
        hashMap.put("IslandIndex", Integer.valueOf(n));
        hashMap.put("GPSource", (Serializable)((Object)this.source));
        if (this.initialPopulation != null) {
            hashMap.put("GPInitialPopulation", (ArrayList)this.initialPopulation.clone());
        } else {
            hashMap.put("GPInitialPopulation", null);
        }
        hashMap.put("IslandRandomSeed", Long.valueOf((long)n + this.gpSettings.rng.nextLong()));
        return hashMap;
    }

    private void checkSettings() {
        if (this.gpSettings.numberOfIslands == 0) {
            this.gpSettings.numberOfIslands = 1;
        }
    }

    public void setEvolutionMessagesListener(IGPEvolutionMessagesListener<T> iGPEvolutionMessagesListener) {
        this.evolutionMessagesListener = iGPEvolutionMessagesListener;
    }

    public void broadcastMessage(String string, Serializable serializable) throws Exception {
        if (Log.isDebugEnabled()) {
            Log.debug("Broadcasting message {}, data {}", (Object)string, (Object)serializable);
        }
        for (int i = 0; i < this.islandJobIds.size(); ++i) {
            String string2 = GPGenerationalEngine.getEvaluationGroupID(this.gpGroupID, this.islandJobIds.get(i));
            GridMessage gridMessage = new GridMessage(5, string, serializable);
            this.gridClient.sendMessage(string2, null, gridMessage);
        }
    }

    public void broadcastNewThresholdFitness(double d) throws Exception {
        this.broadcastMessage("GPThresholdFitness", Double.valueOf(d));
    }

    public void setFinishListener(IGPFinishedListener iGPFinishedListener) {
        this.gpFinishedListener = iGPFinishedListener;
    }

    public boolean isFinished() {
        return this.runningStatus == 3;
    }

    public void destroy() {
        this.unregisterListeners();
        this.gpFinishedListener = null;
        this.evolutionMessagesListener = null;
    }

    public void unregisterListeners() {
        if (this.gridClient != null) {
            this.gridClient.removeMessageListener(this.gpGroupID);
        }
        if (this.stopPauseEngine != null) {
            this.stopPauseEngine.unregisterStatusListener(this);
        }
    }

    public void messageReceived(GridMessage gridMessage) {
        this.processMessage(gridMessage);
    }
}

