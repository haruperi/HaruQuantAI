/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.bestresults;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.databank.IDatabankListener;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.bestresults.BestResultMiniChart;
import com.strategyquant.tradinglib.project.bestresults.BestResultOverview;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BestResults
implements IDatabankListener {
    public static final Logger Log = LoggerFactory.getLogger((String)"BestResults");
    private BestResultOverview overview = null;
    private BestResultMiniChart chart = null;
    public byte sampleType = (byte)127;
    private SQProject project = null;
    private Databank databank = null;
    private boolean changed = true;
    private boolean disabled = false;
    private final Lock lock = new ReentrantLock();
    private JSONArray cachedBestResultsArray = null;
    private int cachedBestResultsHash = 0;

    public BestResults(SQProject sQProject) {
        this.project = sQProject;
        this.chart = new BestResultMiniChart();
        this.overview = new BestResultOverview();
    }

    public void setSampleType(byte by) {
        this.sampleType = by;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JSONArray print() {
        try {
            this.lock.lock();
            if (this.disabled) {
                JSONArray jSONArray = null;
                return jSONArray;
            }
            if (this.databank == null && this.project.containsDatabank()) {
                this.databank = this.project.getResultsDatabank();
                this.databank.addListener(this);
            }
            if (this.databank == null || !this.changed) {
                JSONArray jSONArray = null;
                return jSONArray;
            }
            JSONArray jSONArray = new JSONArray();
            ResultsGroup[] resultsGroupArray = this.databank.getTopResults();
            int n = this.computeHash(resultsGroupArray);
            if (n == this.cachedBestResultsHash && this.cachedBestResultsArray != null) {
                this.changed = false;
                JSONArray jSONArray2 = this.cachedBestResultsArray;
                return jSONArray2;
            }
            for (int i = 0; i < 3; ++i) {
                JSONObject jSONObject = new JSONObject();
                ResultsGroup resultsGroup = null;
                try {
                    resultsGroup = resultsGroupArray[i];
                }
                catch (Exception exception) {
                    // empty catch block
                }
                jSONObject.put("ranking", i);
                if (resultsGroup == null) {
                    jSONObject.put("strategy", (Object)"");
                } else {
                    jSONObject.put("strategy", (Object)resultsGroup.getName());
                    jSONObject.put("overview", (Object)this.overview.print(resultsGroup, this.sampleType));
                    jSONObject.put("chart", (Object)this.chart.print(resultsGroup, this.sampleType));
                }
                jSONArray.put((Object)jSONObject);
            }
            this.cachedBestResultsArray = jSONArray;
            this.cachedBestResultsHash = n;
            this.changed = false;
            JSONArray jSONArray3 = jSONArray;
            return jSONArray3;
        }
        finally {
            this.lock.unlock();
        }
    }

    private int computeHash(ResultsGroup[] resultsGroupArray) {
        int n = 0;
        for (int i = 0; i < resultsGroupArray.length; ++i) {
            ResultsGroup resultsGroup = null;
            try {
                resultsGroup = resultsGroupArray[i];
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (resultsGroup == null) continue;
            n += SQUtils.betterHashCode((String)resultsGroup.getName());
            n += this.getStatsValue(resultsGroup, (byte)11, "NetProfit");
            n += this.getStatsValue(resultsGroup, (byte)40, "NetProfit");
            n += this.getStatsValue(resultsGroup, (byte)20, "NetProfit");
        }
        return n;
    }

    private int getStatsValue(ResultsGroup resultsGroup, byte by, String string) {
        try {
            SQStats sQStats = resultsGroup.portfolio().statsOrNull((byte)0, (byte)10, (byte)20);
            if (sQStats == null) {
                return 0;
            }
            return (int)sQStats.getDouble(string, 0.0);
        }
        catch (Exception exception) {
            Log.error("Cannot get top result stats", (Throwable)exception);
            return 0;
        }
    }

    @Override
    public void databankChanged(Databank databank) {
        this.changed = true;
    }

    public boolean hasChanged() {
        return this.changed;
    }

    public void resetLastData() {
        this.changed = true;
        this.cachedBestResultsHash = 0;
        this.cachedBestResultsArray = null;
    }

    public void enable() {
        this.disabled = false;
    }

    public void disable() {
        this.disabled = true;
    }
}

