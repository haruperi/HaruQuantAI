/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.random.MersenneTwisterRng
 *  com.strategyquant.tradinglib.BadStrategyException
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.MonteCarloRetest
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.backtestrunner.DurationStats
 *  com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener
 *  com.strategyquant.tradinglib.crosscheck.MCResultsComputer
 *  com.strategyquant.tradinglib.engine.BacktestEngine
 *  com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine
 *  com.strategyquant.tradinglib.options.TradingOptions
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SymbolsMap
 *  com.strategyquant.tradinglib.robustnesstests.DataModifierCallback
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessResults
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.tradinglib.simulator.ITradingSimulator
 *  com.strategyquant.tradinglib.simulator.impl.TraderSimulators
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.random.MersenneTwisterRng;
import com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MCJobResult;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MonteCarloRetest;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.crosscheck.MCResultsComputer;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.robustnesstests.DataModifierCallback;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MCRetestJob
extends GridJob<MCJobResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"MCRetestJob");
    private ILastEventListener lastEventListener;
    private long index;
    private String strategyName;
    private StopPauseEngine parentStopPauseEngine;
    private SettingsMap resultSettings;
    private SettingsMap mcSettings;
    private int mainBacktestPrecision;
    private double globalATR;
    private SymbolsMap symbolsMap;
    private boolean useFullSample;
    private int backtestPrecision;

    public MCRetestJob(long index, String strategyName, String jobID, Map<String, Serializable> jobSettings, StopPauseEngine parentStopPauseEngine, ILastEventListener lastEventListener, int mainBacktestPrecision, double globalATR, SymbolsMap symbolsMap) {
        super(jobID, 1, jobSettings);
        this.lastEventListener = lastEventListener;
        this.index = index;
        this.strategyName = strategyName;
        this.parentStopPauseEngine = parentStopPauseEngine;
        this.resultSettings = (SettingsMap)jobSettings.get("resultSettings");
        this.mcSettings = (SettingsMap)jobSettings.get("mcSettings");
        this.mainBacktestPrecision = mainBacktestPrecision;
        this.useFullSample = (Boolean)jobSettings.get("useFullSample");
        this.backtestPrecision = (Integer)jobSettings.get("backtestPrecision");
        this.globalATR = globalATR;
        this.symbolsMap = symbolsMap;
    }

    public MCJobResult call() throws Exception {
        DurationStats durationStats = new DurationStats();
        long start = System.currentTimeMillis();
        try {
            if (this.lastEventListener != null) {
                String event = L.t((String)"Running MC simulation %d for %s", (Object[])new Object[]{this.index, this.strategyName});
                this.lastEventListener.setLastEvent(event);
            }
            ArrayList availableMethods = (ArrayList)this.mcSettings.get("MonteCarloManipulation");
            ArrayList<MonteCarloRetest> methods = new ArrayList<MonteCarloRetest>();
            for (MonteCarloRetest mc : availableMethods) {
                methods.add(mc.getClone());
            }
            SettingsMap clonedSettings = this.cloneSettings(this.resultSettings);
            ChartSetup chartSetup = (ChartSetup)clonedSettings.get("BacktestChart");
            if (this.backtestPrecision == -1) {
                chartSetup.setTestPrecision(this.mainBacktestPrecision);
            } else {
                chartSetup.setTestPrecision(this.backtestPrecision);
            }
            StockpickerBacktestEngine backtestEngine = null;
            if (chartSetup.getBacktestEngine() == 1316847364 || chartSetup.getBacktestEngine() == -1816889229) {
                backtestEngine = new StockpickerBacktestEngine();
            } else {
                boolean usePreparedData;
                ITradingSimulator simulator = TraderSimulators.getSimulator((ChartSetup)chartSetup);
                backtestEngine = new BacktestEngine(simulator);
                boolean bl = usePreparedData = !this.isRandomizeHistoryUsed(chartSetup, methods);
                if (Engines.isTradestationEngine((int)simulator.getEngineId())) {
                    usePreparedData = true;
                }
                backtestEngine.setUsePreparedData(usePreparedData);
            }
            backtestEngine.setSingleThreaded(true);
            backtestEngine.setStopPauseEngine(this.parentStopPauseEngine);
            long seed = System.currentTimeMillis() + 109L * this.index;
            MersenneTwisterRng rng = new MersenneTwisterRng(seed);
            backtestEngine.registerProgressListener(new IBacktestProgressListener(){

                public void setProgress(int progress) {
                }

                public void increaseProgressStep() {
                }
            });
            for (final MonteCarloRetest method : methods) {
                if (this.parentStopPauseEngine.isStopped()) break;
                if (method.getType() == 1) {
                    method.modifySettings((IRandomGenerator)rng, clonedSettings);
                    continue;
                }
                if (method.getType() != 2) continue;
                method.initSettings(clonedSettings);
                backtestEngine.setDataModifierCallback(new DataModifierCallback(){
                    final /* synthetic */ IRandomGenerator val$rng;
                    final /* synthetic */ MCRetestJob this$0;
                    {
                        this.val$rng = iRandomGenerator;
                        this.this$0 = this$0;
                    }

                    public void modifyData(TickEvent tickEvent) {
                        method.modifyData(this.val$rng, tickEvent, this.this$0.globalATR);
                    }

                    public void modifyOHLCData(VersatileData data) {
                        method.modifyOHLCData(this.val$rng, data, this.this$0.globalATR);
                    }

                    public void modifyData(TickEvent tickEvent, double atr) {
                        method.modifyData(this.val$rng, tickEvent, atr);
                    }
                });
            }
            backtestEngine.addSetup(clonedSettings);
            ResultsGroup newRg = backtestEngine.runBacktest().getResults();
            OrdersList ordersSimulation = newRg.orders();
            if (!this.useFullSample) {
                ordersSimulation = this.filterInSampleOnly(ordersSimulation, clonedSettings);
            }
            RobustnessResults rr = MCResultsComputer.computeResults((OrdersList)ordersSimulation, (SettingsMap)clonedSettings, (SymbolsMap)this.symbolsMap, null);
            durationStats.addDuration(DurationStats.MainTest, System.currentTimeMillis() - start);
            return new MCJobResult(rr, durationStats);
        }
        catch (Exception e) {
            if (e instanceof BadStrategyException) {
                BadStrategyException be = (BadStrategyException)e;
                if (!e.getMessage().contains("Automatic filter") && !e.getMessage().contains(L.t((String)"Automatic filter", (Object[])new Object[0]))) {
                    Log.error(String.format("Exception in Cross check - %s : ", this.getJobId(), BadStrategyException.getReasonAsString((int)be.getReason())), (Throwable)e);
                    return new MCJobResult(L.t((String)"Automatic filter", (Object[])new Object[0]), 10004, durationStats);
                }
            }
            return new MCJobResult(L.t((String)"Exception in backtest: %s", (Object[])new Object[]{e.getMessage()}), 10004, durationStats);
        }
    }

    private boolean isRandomizeHistoryUsed(ChartSetup chartSetup, ArrayList<MonteCarloRetest> methods) {
        if (chartSetup.getMainChart().getSymbolInfo().dataType != 2) {
            for (MonteCarloRetest method : methods) {
                if (method.getType() != 2) continue;
                return true;
            }
        }
        return false;
    }

    private OrdersList filterInSampleOnly(OrdersList ordersSimulation, SettingsMap clonedSettings) {
        OrdersList newOL = ordersSimulation.filterWithClone("*", (byte)0, (byte)10);
        ordersSimulation.clear();
        return newOL;
    }

    protected SettingsMap cloneSettings(SettingsMap settings) throws CloneNotSupportedException {
        SettingsMap copy = new SettingsMap();
        String[] keys = settings.getAllKeys();
        for (int i = 0; i < keys.length; ++i) {
            Object valueCopy = this.cloneValue(keys[i], settings.get(keys[i]));
            copy.set(keys[i], valueCopy);
        }
        copy.set("StrategyCheckDate", (Object)-1L);
        return copy;
    }

    private Object cloneValue(String key, Object value) throws CloneNotSupportedException {
        if (key.equals("TradingOptions")) {
            return ((TradingOptions)value).getClone();
        }
        if (key.equals("StoreChartData")) {
            return false;
        }
        if (value instanceof StrategyBase) {
            return ((StrategyBase)value).clone();
        }
        if (key.equals("BacktestChart")) {
            return ((ChartSetup)value).getClone();
        }
        return value;
    }
}

