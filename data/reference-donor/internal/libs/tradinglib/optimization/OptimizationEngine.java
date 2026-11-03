/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.BadOptimizationParamsException;
import com.strategyquant.tradinglib.optimization.OptimizationEngineWF;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationEngine
extends OptimizationEngineWF {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationEngine");

    public OptimizationEngine(String string, StopPauseEngine stopPauseEngine, GridJob gridJob, String string2, ILastEventListener iLastEventListener) {
        this(string, stopPauseEngine, gridJob, string2, iLastEventListener, null);
    }

    public OptimizationEngine(String string, StopPauseEngine stopPauseEngine, GridJob gridJob, String string2, ILastEventListener iLastEventListener, String string3) {
        super(string, stopPauseEngine, gridJob, string2, iLastEventListener, string3);
    }

    public void optimize() throws Exception {
        if (this.settings == null) {
            throw new Exception("OptimizationEngine was not initialized!");
        }
        int n = this.verifySettings();
        this.initOptimization();
        this.actualStep = 0;
        this.optimizationProfile = new OptimizationProfile();
        if (n == 0 || this.optimizationSettings.type == 1) {
            this.printLog(L.t((String)"Running simple optimization on %s", (Object[])new Object[]{this.settings.getString("StrategyName")}));
            this.printLog(L.t((String)"Testing original strategy", (Object[])new Object[0]));
            this.optimizeSimple(false);
        } else {
            int n2 = 0;
            if (this.optimizationSettings.optimizationType == 0 || this.optimizationSettings.optimizationType == 1) {
                n2 = this.optimizeSimple(true);
            }
            if (n2 > 0) {
                if (n2 < 50) {
                    n2 = 50000;
                }
                this.customStatsComputer = new StatsComputer();
                ArrayList<DatabankColumn> arrayList = this.recognizeStatValues();
                this.fitnessStatsComputer = new StatsComputer(arrayList);
                if (this.wfoSimulationEngine != null) {
                    this.wfoSimulationEngine.sortVariants();
                }
                if (this.optimizationSettings.type == 2) {
                    this.optimizeWF(null, this.optimizationSettings.periodType, 2, this.optimizationSettings.param1Start, this.optimizationSettings.param2Start, 0, null, false);
                } else if (this.optimizationSettings.type == 3) {
                    this.optimizeMultiWF();
                }
            }
        }
        this.clearOptimizationProfile();
    }

    private ArrayList<DatabankColumn> recognizeStatValues() throws Exception {
        ArrayList<DatabankColumn> arrayList = this.fitnessFunction.getUsedStatValues();
        for (DatabankColumn databankColumn : DatabankColumns.get().getAvailableClasses()) {
            if (databankColumn.getClassName().equals("NumberOfTrades") || databankColumn.getClassName().equals("Drawdown")) {
                this.addToStatValues(arrayList, databankColumn);
            }
            if (this.optimizationSettings.periodType != 30 || !databankColumn.getClassName().equals("DrawdownPct")) continue;
            this.addToStatValues(arrayList, databankColumn);
        }
        StatsComputer.createDependencyGraph(arrayList);
        return arrayList;
    }

    private void addToStatValues(ArrayList<DatabankColumn> arrayList, DatabankColumn databankColumn) {
        String string = databankColumn.getClassName();
        for (int i = 0; i < arrayList.size(); ++i) {
            if (!arrayList.get(i).getClassName().equals(string)) continue;
            return;
        }
        arrayList.add(databankColumn);
    }

    private int verifySettings() throws BadOptimizationParamsException {
        int n = this.parameters.verify();
        this.optimizationSettings.verify();
        return n;
    }

    private int optimizeSimple(boolean bl) throws Exception {
        return this.runSimpleOptimization(0, 0L, 0L, this.optimizationSettings.type, bl);
    }
}

