/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.StrategyParamData;
import com.strategyquant.tradinglib.optimization.WFSimulationJobResult;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.util.RngUtils;
import com.strategyquant.tradinglib.wfo.WFOSimulationEngine;
import com.strategyquant.tradinglib.wfo.WFVariant;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WFSimulationJob
extends GridJob<WFSimulationJobResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"WFSimulationJob");
    private ILastEventListener lastEventListener;
    private StopPauseEngine parentStopPauseEngine;
    private WalkForwardPeriod period;
    private String resultName;
    private boolean lastPeriod;
    private IFitnessFunction fitnessFunction;
    private SettingsMap settings;
    private OptimizationSettings optimizationSettings;
    private StatsComputer fitnessStatsComputer;
    private WFOSimulationEngine wfoSimulationEngine;
    private int index;
    private final String mainResultKey;

    public WFSimulationJob(String string, Map<String, Serializable> map, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener, String string2, boolean bl, IFitnessFunction iFitnessFunction, SettingsMap settingsMap, OptimizationSettings optimizationSettings, StatsComputer statsComputer, WFOSimulationEngine wFOSimulationEngine, WalkForwardPeriod walkForwardPeriod, int n, String string3) {
        super(string, 1, map);
        this.lastEventListener = iLastEventListener;
        this.parentStopPauseEngine = stopPauseEngine;
        this.period = walkForwardPeriod;
        this.resultName = string2;
        this.lastPeriod = bl;
        this.fitnessFunction = iFitnessFunction;
        this.settings = settingsMap;
        this.optimizationSettings = optimizationSettings;
        this.fitnessStatsComputer = statsComputer;
        this.wfoSimulationEngine = wFOSimulationEngine;
        this.index = n;
        this.mainResultKey = string3;
    }

    public WFSimulationJobResult call() throws Exception {
        DurationStats durationStats = new DurationStats();
        long l = System.currentTimeMillis();
        try {
            Object object;
            long l2 = Long.MAX_VALUE;
            if (this.period.runFrom < l2) {
                l2 = this.period.runFrom;
            }
            if (this.lastEventListener != null) {
                object = L.t((String)"Computing period %d for %s", (Object[])new Object[]{this.index, this.resultName});
                this.lastEventListener.setLastEvent((String)object);
            }
            object = new OrdersList("performSimulatedWFOptimization " + this.index);
            ResultsGroup resultsGroup = this.runSimpleSimulatedOptimization(this.index, this.period.optimizeFrom, this.period.optimizeTo);
            if (this.index == 0 && resultsGroup != null) {
                ((OrdersList)object).addAll(resultsGroup.orders());
            }
            if (this.parentStopPauseEngine.isStopped()) {
                if (resultsGroup != null) {
                    resultsGroup.clear();
                }
                return null;
            }
            ResultsGroup resultsGroup2 = null;
            this.period.optimizationStatData = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getClone();
            if (!this.lastPeriod) {
                boolean bl = true;
                short[] sArray = (short[])resultsGroup.specialValues().get("OptimizationParametersArray");
                resultsGroup2 = bl ? (this.optimizationSettings.optimizationType == 1 ? this.testStrategy(sArray, "WF Simulation", "Run strategy " + this.index, this.period.runFrom, this.period.runTo) : this.runSimpleSimulationRun(resultsGroup, "Run strategy " + this.index, this.period.runFrom, this.period.runTo)) : this.createEmptyCandidate(resultsGroup, this.fitnessStatsComputer, "Run strategy " + this.index, this.period.runFrom, this.period.runTo);
                this.period.runStatData = resultsGroup2.portfolio().stats((byte)0, (byte)10, (byte)127).getClone();
                ((OrdersList)object).addAll(resultsGroup2.orders());
                resultsGroup2.clear();
            }
            this.period.testParameters = resultsGroup.specialValues().getString("OptimizationParameters");
            resultsGroup.clear();
            durationStats.addDuration(DurationStats.MainTest, System.currentTimeMillis() - l);
            return new WFSimulationJobResult((OrdersList)object, this.index, durationStats);
        }
        catch (Exception exception) {
            if (exception instanceof BadStrategyException) {
                BadStrategyException badStrategyException = (BadStrategyException)((Object)exception);
                if (!exception.getMessage().contains("Automatic filter") && !exception.getMessage().contains(L.t((String)"Automatic filter", (Object[])new Object[]{true}))) {
                    Log.error(String.format("Exception in Cross check - %s : ", this.getJobId(), BadStrategyException.getReasonAsString(badStrategyException.getReason())), (Throwable)exception);
                    return new WFSimulationJobResult(L.t((String)"Automatic filter", (Object[])new Object[]{true}), 10004, durationStats);
                }
            } else {
                Log.error(String.format("Exception in Cross check - %s : ", this.getJobId()), (Throwable)exception);
            }
            return new WFSimulationJobResult(String.format("Exception in backtest: %s", exception.getMessage()), 10004, durationStats);
        }
    }

    private ResultsGroup createEmptyCandidate(ResultsGroup resultsGroup, StatsComputer statsComputer, String string, long l, long l2) throws Exception {
        ArrayList<WFVariant> arrayList = this.wfoSimulationEngine.getVariants();
        String string2 = "";
        int n = (Integer)resultsGroup.specialValues().get("OptVariantIndex", (Object)-1);
        if (n < 0) {
            throw new Exception("Best variant index not found!");
        }
        WFVariant wFVariant = arrayList.get(n);
        ResultsGroup resultsGroup2 = new ResultsGroup("Variant " + wFVariant.paramsFile);
        resultsGroup2.addSubresult(string, this.settings.clone());
        ChartSetups chartSetups = (ChartSetups)this.settings.get("ChartSetups");
        for (ChartDef object2 : chartSetups.getMainSetup().getCharts()) {
            resultsGroup2.symbols().add(object2.getSymbol(), object2.getSymbolInfo().instrument, object2.getSymbolInfo());
            resultsGroup2.addResultSymbol(string, object2.getSymbol());
        }
        SettingsMap settingsMap = resultsGroup2.portfolio().getSettings();
        settingsMap.setIfNotExists("MoneyManagement.InitialCapital", (Object)20000.0);
        Result result = resultsGroup2.subResult(string);
        SettingsMap settingsMap2 = result.getSettings();
        settingsMap2.set("PortfolioDataStart", (Object)l);
        settingsMap2.set("PortfolioDataEnd", (Object)l2);
        WFOSimulationEngine.computeStatsRequiredForFitness(statsComputer, string, result, resultsGroup2.orders(), resultsGroup2.symbols());
        resultsGroup2.specialValues().set("OptimizationParameters", (Object)wFVariant.params);
        resultsGroup2.specialValues().set("OptimizationParametersArray", (Object)wFVariant.indexes);
        return resultsGroup2;
    }

    protected ResultsGroup runSimpleSimulatedOptimization(int n, long l, long l2) throws Exception {
        if (this.shouldOptimizeByIndex()) {
            return this.runSimpleSimulatedOptimizationIndexFitness(n, l, l2);
        }
        return this.runSimpleSimulatedOptimizationNormalFitness(n, l, l2);
    }

    private boolean shouldOptimizeByIndex() throws Exception {
        boolean bl = (Boolean)this.settings.get("UseFitnessByIndex", (Object)false);
        return bl;
    }

    protected ResultsGroup runSimpleSimulatedOptimizationIndexFitness(int n, long l, long l2) throws Exception {
        int n2;
        Object object;
        ArrayList<WFVariant> arrayList = this.wfoSimulationEngine.getVariants();
        ArrayList<ResultsGroup> arrayList2 = new ArrayList<ResultsGroup>();
        if (n == 1 && Log.isDebugEnabled()) {
            String string = SQTime.toDateMinuteString((long)l);
            object = SQTime.toDateMinuteString((long)l2);
            Log.debug("Optimize from {} to {}", (Object)string, object);
        }
        for (n2 = 0; n2 < arrayList.size(); ++n2) {
            object = arrayList.get(n2);
            if (this.parentStopPauseEngine.isStopped()) {
                this.clearCandidates(arrayList2);
                return null;
            }
            ResultsGroup resultsGroup = this.wfoSimulationEngine.simulateTestCandidate(this.fitnessStatsComputer, (WFVariant)object, l, l2, this.cloneBacktestSettings(l, l2));
            if (resultsGroup == null) continue;
            resultsGroup.specialValues().set("OptVariantIndex", (Object)n2);
            arrayList2.add(resultsGroup);
        }
        if (arrayList2.size() == 0) {
            throw new Exception(L.t((String)"Optimization not successful, please check log for more information!", (Object[])new Object[]{true}));
        }
        n2 = 0;
        object = this.findBestCandidate(arrayList2, this.fitnessFunction, l);
        if (object == null) {
            throw new Exception(L.t((String)"Optimization not successful (reason 2), please check log for more information!", (Object[])new Object[]{true}));
        }
        int n3 = ((ResultsGroup)object).specialValues().getInt("OptVariantIndex");
        String string = arrayList.get((int)n3).params;
        Log.debug("Best candiate params: {}", (Object)string);
        if (object == null) {
            throw new Exception(L.t((String)"Optimization not successful, please check log for more information!", (Object[])new Object[]{true}));
        }
        SettingsMap settingsMap = ((ResultsGroup)object).subResult("Setup 1").getSettings();
        settingsMap.set("PortfolioDataStart", (Object)l);
        settingsMap.set("PortfolioDataEnd", (Object)l2);
        ((ResultsGroup)object).computeAllStats();
        return object;
    }

    private ResultsGroup findBestCandidate(ArrayList<ResultsGroup> arrayList, IFitnessFunction iFitnessFunction, long l) throws Exception {
        Object object;
        Serializable serializable;
        for (int i = 0; i < arrayList.size(); ++i) {
            serializable = arrayList.get(i);
            serializable.specialValues().set("OptIndexFitness", (Object)0.0);
        }
        ArrayList<MetricForFitness> arrayList2 = iFitnessFunction.getMetricsForFitness();
        serializable = new ArrayList<ResultsGroup>(arrayList);
        for (int i = 0; i < arrayList2.size(); ++i) {
            object = arrayList2.get(i);
            RngUtils.setIndexByMetric((ArrayList<ResultsGroup>)serializable, (MetricForFitness)object, iFitnessFunction);
        }
        object = null;
        double d = Double.MAX_VALUE;
        double d2 = 0.0;
        String string = null;
        StringBuffer stringBuffer = null;
        ArrayList<String> arrayList3 = null;
        if (this.optimizationSettings.debugWFFitnessPath != null) {
            stringBuffer = new StringBuffer();
            arrayList3 = RngUtils.printStrategyResultsHeader(stringBuffer, true, iFitnessFunction);
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            String string2;
            boolean bl;
            ResultsGroup resultsGroup = arrayList.get(i);
            if (this.parentStopPauseEngine.isStopped()) {
                if (object != null) {
                    ((ResultsGroup)object).clear();
                }
                return null;
            }
            double d3 = resultsGroup.specialValues().getDouble("OptIndexFitness");
            if (this.optimizationSettings.debugWFFitnessPath != null) {
                RngUtils.debugWFLogCandidate(stringBuffer, this.resultName, resultsGroup, arrayList3);
            }
            if (bl = this.isBetterCandidateFitnessIndex(resultsGroup, d3, d, d2, string, string2 = resultsGroup.specialValues().getString("OptimizationParameters", null))) {
                if (object != null) {
                    ((ResultsGroup)object).clear();
                }
                d = d3;
                d2 = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)10).getInt("NumberOfTrades");
                string = string2;
                object = resultsGroup;
                ((ResultsGroup)object).specialValues().set("OptVariantIndex", (Object)i);
                continue;
            }
            resultsGroup.clear();
        }
        if (this.optimizationSettings.debugWFFitnessPath != null) {
            RngUtils.debugWFLogWriteFile(this.optimizationSettings, this.mainResultKey, this.resultName, stringBuffer, this.period);
        }
        return object;
    }

    private boolean isBetterCandidateFitnessIndex(ResultsGroup resultsGroup, double d, double d2, double d3, String string, String string2) throws Exception {
        if (d2 == Double.MAX_VALUE) {
            return true;
        }
        return d < d2;
    }

    private boolean isVariantSmaller(String string, String string2) {
        if (string2 == null) {
            return true;
        }
        String[] stringArray = string.split(",");
        String[] stringArray2 = string2.split(",");
        if (stringArray.length == 0 || stringArray.length != stringArray2.length) {
            return true;
        }
        for (int i = 0; i < stringArray.length; ++i) {
            double d;
            String[] stringArray3 = stringArray[i].split("=");
            String[] stringArray4 = stringArray2[i].split("=");
            if (stringArray3.length == 0 || stringArray3.length != stringArray4.length) {
                return true;
            }
            if (!stringArray3[0].equals(stringArray4[0])) {
                return true;
            }
            double d2 = Double.parseDouble(stringArray3[1]);
            if (d2 < (d = Double.parseDouble(stringArray4[1]))) {
                return true;
            }
            if (!(d2 > d)) continue;
            return false;
        }
        return false;
    }

    private void clearCandidates(ArrayList<ResultsGroup> arrayList) {
        for (int i = 0; i < arrayList.size(); ++i) {
            ResultsGroup resultsGroup = arrayList.get(i);
            if (resultsGroup == null) continue;
            resultsGroup.clear();
        }
    }

    protected ResultsGroup runSimpleSimulatedOptimizationNormalFitness(int n, long l, long l2) throws Exception {
        Object object;
        ResultsGroup resultsGroup = null;
        double d = -1.0;
        double d2 = 0.0;
        Object object2 = null;
        ArrayList<WFVariant> arrayList = this.wfoSimulationEngine.getVariants();
        String string = "";
        if (n == 1 && Log.isDebugEnabled()) {
            String string2 = SQTime.toDateMinuteString((long)l);
            object = SQTime.toDateMinuteString((long)l2);
            Log.debug("Optimize from {} to {}", (Object)string2, object);
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            object = arrayList.get(i);
            if (this.parentStopPauseEngine.isStopped()) {
                if (resultsGroup != null) {
                    resultsGroup.clear();
                }
                return null;
            }
            ResultsGroup resultsGroup2 = this.wfoSimulationEngine.simulateTestCandidate(this.fitnessStatsComputer, (WFVariant)object, l, l2, this.cloneBacktestSettings(l, l2));
            if (resultsGroup2 == null) continue;
            double d3 = this.computeFitness(resultsGroup2);
            boolean bl = this.isBetterCandidate(resultsGroup2, d3, d, d2, (WFVariant)object2, (WFVariant)object);
            if (bl) {
                if (resultsGroup != null) {
                    resultsGroup.clear();
                }
                d = d3;
                d2 = resultsGroup2.portfolio().stats((byte)0, (byte)10, (byte)10).getInt("NumberOfTrades");
                object2 = object;
                resultsGroup = resultsGroup2;
                string = arrayList.get((int)i).params;
                resultsGroup.specialValues().set("OptVariantIndex", (Object)i);
                continue;
            }
            resultsGroup2.clear();
        }
        if (resultsGroup == null) {
            throw new Exception(L.t((String)"Optimization not successful, please check log for more information!", (Object[])new Object[]{true}));
        }
        SettingsMap settingsMap = resultsGroup.subResult("Setup 1").getSettings();
        settingsMap.set("PortfolioDataStart", (Object)l);
        settingsMap.set("PortfolioDataEnd", (Object)l2);
        resultsGroup.computeAllStats();
        return resultsGroup;
    }

    private boolean isBetterCandidate(ResultsGroup resultsGroup, double d, double d2, double d3, WFVariant wFVariant, WFVariant wFVariant2) throws Exception {
        if (d2 == -1.0) {
            return true;
        }
        return d > d2;
    }

    private boolean isVariantSmaller(WFVariant wFVariant, WFVariant wFVariant2) {
        if (wFVariant2 == null) {
            return true;
        }
        String[] stringArray = wFVariant.params.split(",");
        String[] stringArray2 = wFVariant2.params.split(",");
        if (stringArray.length == 0 || stringArray.length != stringArray2.length) {
            return true;
        }
        for (int i = 0; i < stringArray.length; ++i) {
            double d;
            String[] stringArray3 = stringArray[i].split("=");
            String[] stringArray4 = stringArray2[i].split("=");
            if (stringArray3.length == 0 || stringArray3.length != stringArray4.length) {
                return true;
            }
            if (!stringArray3[0].equals(stringArray4[0])) {
                return true;
            }
            double d2 = Double.parseDouble(stringArray3[1]);
            if (d2 < (d = Double.parseDouble(stringArray4[1]))) {
                return true;
            }
            if (!(d2 > d)) continue;
            return false;
        }
        return false;
    }

    protected double computeFitness(ResultsGroup resultsGroup) throws Exception {
        return this.computeFitness(resultsGroup, (byte)0, (byte)10);
    }

    private double computeFitness(ResultsGroup resultsGroup, byte by, byte by2) throws Exception {
        double d = this.wfoSimulationEngine.isPeriodTypeBars() ? this.fitnessFunction.computeFitness(resultsGroup, by, by2, false) : this.fitnessFunction.computeFitness(resultsGroup, by, by2);
        resultsGroup.portfolio().setFitness(by2, d);
        if (by == 0 && by2 == 127) {
            Log.debug("Fitness computed to: " + d);
        }
        return d;
    }

    public ResultsGroup testStrategy(short[] sArray, String string, String string2, long l, long l2) throws Exception {
        long l3 = System.currentTimeMillis();
        SettingsMap settingsMap = this.cloneBacktestSettings(l, l2);
        settingsMap.set("StrategyName", (Object)string);
        settingsMap.set("MainResultKey", (Object)string2);
        settingsMap.set("ResultGroupName", (Object)string);
        StrategyBase strategyBase = (StrategyBase)this.settings.get("StrategyObject");
        StrategyParamData strategyParamData = StrategyBase.createStrategyVariation(strategyBase, this.optimizationSettings, this.optimizationSettings.transformToFullIndexes(sArray));
        StrategyBase strategyBase2 = strategyParamData.getStrategy();
        String string3 = strategyParamData.getParams();
        Element element = strategyBase2.getStrategyXml();
        settingsMap.set("StrategyObject", (Object)StrategyBase.createXmlStrategy(element));
        BacktestRunner backtestRunner = new BacktestRunner(new BacktestSettings(settingsMap), this.parentStopPauseEngine, null, false, this.lastEventListener, null);
        BacktestResult backtestResult = backtestRunner.execute();
        ResultsGroup resultsGroup = backtestResult.getResult();
        if (resultsGroup == null) {
            throw new Exception(String.format("No results for backtest! Reason: %s", backtestResult.getDismissalMessage()));
        }
        resultsGroup.specialValues().setString("OptimizationParameters", string3);
        resultsGroup.specialValues().set("OptimizationParametersArray", (Object)sArray);
        double d = this.computeFitness(resultsGroup);
        resultsGroup.portfolio().setFitness((byte)127, d);
        return resultsGroup;
    }

    protected SettingsMap cloneBacktestSettings(long l, long l2) throws Exception {
        SettingsMap settingsMap = new SettingsMap();
        settingsMap.set("ChartSetups", (Object)((ChartSetups)this.settings.get("ChartSetups")).getClone(l, l2));
        settingsMap.set("MoneyManagement.InitialCapital", (Object)this.settings.getDouble("MoneyManagement.InitialCapital"));
        settingsMap.set("TestPrecision", (Object)this.settings.getInt("TestPrecision"));
        settingsMap.set("Slippage", (Object)this.settings.getDouble("Slippage"));
        settingsMap.set("MinDistance", (Object)this.settings.getDouble("MinDistance"));
        settingsMap.set("Commission", (Object)((CommissionsMethod)this.settings.get("Commission")));
        settingsMap.set("Swap", (Object)((SwapMethod)this.settings.get("Swap")));
        settingsMap.set("FitnessFunction", this.settings.get("FitnessFunction"));
        settingsMap.set("MoneyManagement.Method", this.settings.get("MoneyManagement.Method"));
        settingsMap.set("RiskManagement", this.settings.get("RiskManagement"));
        TradingOptions tradingOptions = ((TradingOptions)this.settings.get("TradingOptions")).getClone();
        settingsMap.set("TradingOptions", (Object)tradingOptions);
        ATM aTM = (ATM)this.settings.get("ATM");
        if (aTM != null) {
            settingsMap.set("ATM", (Object)aTM.getClone());
        }
        return settingsMap;
    }

    private ResultsGroup runSimpleSimulationRun(ResultsGroup resultsGroup, String string, long l, long l2) throws Exception {
        double d = -1.0;
        ArrayList<WFVariant> arrayList = this.wfoSimulationEngine.getVariants();
        String string2 = "";
        int n = (Integer)resultsGroup.specialValues().get("OptVariantIndex", (Object)-1);
        if (n < 0) {
            throw new Exception("Best variant index not found!");
        }
        ResultsGroup resultsGroup2 = this.wfoSimulationEngine.simulateTestCandidate(this.fitnessStatsComputer, arrayList.get(n), l, l2, this.cloneBacktestSettings(l, l2));
        if (resultsGroup2 == null) {
            throw new Exception("Candidate is null!");
        }
        double d2 = this.computeFitness(resultsGroup2);
        SettingsMap settingsMap = resultsGroup2.subResult("Setup 1").getSettings();
        settingsMap.set("PortfolioDataStart", (Object)l);
        settingsMap.set("PortfolioDataEnd", (Object)l2);
        resultsGroup2.computeAllStats();
        return resultsGroup2;
    }
}

