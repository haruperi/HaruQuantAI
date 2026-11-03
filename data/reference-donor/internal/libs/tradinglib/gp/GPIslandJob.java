/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.IRandomGenerator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.GPGenerationalEngine;
import com.strategyquant.tradinglib.gp.GPSettings;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GPIslandJob<T extends IGPNode>
extends GridJob<Integer> {
    private static final long serialVersionUID = -2179402133615108244L;
    private static final Logger Log = LoggerFactory.getLogger((String)"GPIslandJob");
    private GPSettings<T> gpSettings;
    private int islandIndex;
    private GPGenerationalEngine<T> engine;
    private String gpGroupID;
    private IRandomGenerator rng;
    private ArrayList<T> initialPopulation;
    private GridJob parentGridJob;
    private String source;

    public GPIslandJob(String string, Map<String, Serializable> map, GridJob gridJob) {
        super(string, 0, map);
        long l = (Long)map.get("IslandRandomSeed");
        GPSettings gPSettings = (GPSettings)map.get("GPSettings");
        this.initialPopulation = (ArrayList)map.get("GPInitialPopulation");
        this.rng = gPSettings.rng.clone(l);
        this.gpSettings = gPSettings.clone(this.rng);
        this.gpGroupID = (String)((Object)map.get("GPGroupID"));
        this.islandIndex = (Integer)map.get("IslandIndex");
        this.source = (String)((Object)map.get("GPSource"));
        this.parentGridJob = gridJob;
    }

    public static String createJobID(int n, GridJob gridJob, String string) {
        if (gridJob != null) {
            String string2 = gridJob.getJobId();
            return String.format("%s-%s_%d", string2, string, n);
        }
        return String.format("%s_%d", string, n);
    }

    public Integer call() throws Exception {
        Log.debug("Island Job started");
        try {
            this.engine = new GPGenerationalEngine<T>(this, this.gpSettings, this.gpGroupID, this.getJobId(), this.source, this.islandIndex, this.initialPopulation, this.parentGridJob);
            this.engine.evolve();
        }
        finally {
            Log.debug("Island Job finished");
            if (this.gpSettings.factory != null) {
                this.gpSettings.factory.destroy();
            }
        }
        return null;
    }

    public void messageReceived(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 2) {
            if (this.engine != null) {
                this.engine.pause();
            }
        } else if (gridMessage.getMessageID() == 3) {
            if (this.engine != null) {
                this.engine.restart();
            }
        } else if (gridMessage.getMessageID() == 4) {
            if (this.engine != null) {
                this.engine.stop();
            }
        } else if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID().equals("GBIslandExchange")) {
            List list = (List)((Object)gridMessage.getData());
            this.engine.addToInbox(list);
        }
    }

    public void destroy() {
        Log.debug(String.format("Job %s destroyed", this.getJobId()));
        if (this.engine != null) {
            this.engine.stop();
            this.engine.destroy();
        }
    }
}

