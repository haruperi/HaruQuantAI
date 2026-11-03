/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.optimization.OptimizationConst;
import com.strategyquant.tradinglib.optimization.OptimizationEngineSimple;
import com.strategyquant.tradinglib.optimization.WFOptJobResult;
import com.strategyquant.tradinglib.optimization.WFSimulationJob;
import com.strategyquant.tradinglib.optimization.WFSimulationJobResult;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.parameters.ReservedBars;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import com.strategyquant.tradinglib.wfo.WFVariant;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationEngineWF
extends OptimizationEngineSimple {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationEngineWF");
    private Element conditionsElem;
    private ArrayList<Condition> conditions;
    private int thresholdPct;
    private int robCombRows;
    private int robCombCols;
    private int robMinComb;
    protected int runNumber = 0;
    private boolean wfBatchCreated;

    public OptimizationEngineWF(String string, StopPauseEngine stopPauseEngine, GridJob gridJob, String string2, ILastEventListener iLastEventListener, String string3) {
        super(string, stopPauseEngine, gridJob, string2, iLastEventListener, string3);
    }

    @Override
    public void initialize(SettingsMap settingsMap) throws Exception {
        super.initialize(settingsMap);
        if (this.optimizationSettings.type != 1) {
            this.conditionsElem = this.optimizationSettings.elConditions;
            this.conditions = this.optimizationSettings.conditions;
            this.thresholdPct = this.optimizationSettings.thresholdPct;
            this.robCombRows = this.optimizationSettings.robCombRows;
            this.robCombCols = this.optimizationSettings.robCombCols;
            this.robMinComb = this.optimizationSettings.robMinComb;
        }
    }

    public int getTotalStepsCount() {
        if (this.optimizationSettings.type == 1) {
            return this.getTotalStepsForSimpleOptimization();
        }
        int n = 0;
        if (this.optimizationSettings.optimizationType == 1 || this.optimizationSettings.optimizationType == 0) {
            n = this.getTotalStepsForSimpleOptimization();
        }
        this.initOptimization();
        int n2 = n;
        if (this.optimizationSettings.type == 2) {
            n2 += this.getTotalStepsForWF(n, this.optimizationSettings.param1Start, this.optimizationSettings.param2Start);
        } else if (this.optimizationSettings.type == 3) {
            n2 += this.getTotalStepsForMultiWF(n) - 1;
        }
        return n2;
    }

    private int getTotalStepsForMultiWF(int n) {
        int n2 = 1;
        for (int i = this.optimizationSettings.param1Start; i <= this.optimizationSettings.param1Stop; i += this.optimizationSettings.param1Step) {
            for (int j = this.optimizationSettings.param2Start; j <= this.optimizationSettings.param2Stop; j += this.optimizationSettings.param2Step) {
                n2 += this.getTotalStepsForWF(n, i, j) - 1;
            }
        }
        return n2;
    }

    private int getTotalStepsForWF(int n, int n2, int n3) {
        int n4 = 1;
        ArrayList<WalkForwardPeriod> arrayList = this.computeWFPeriods(n2, n3, 0, null);
        return n4 += arrayList.size() * 2;
    }

    @Override
    protected void initOptimization() {
        ChartSetups chartSetups = (ChartSetups)this.settings.get("ChartSetups");
        this.totalDays = SQTimeOld.getDaysBetween((long)chartSetups.getMainSetup().getMainChart().getHistoryFrom(), (long)chartSetups.getMainSetup().getMainChart().getHistoryTo());
    }

    protected WalkForwardResult optimizeWF(ResultsGroup resultsGroup, int n, int n2, int n3, int n4, int n5, MarketData marketData, boolean bl) throws Exception {
        ResultsGroup resultsGroup2;
        Object object;
        Object object2;
        String string;
        Object object3;
        double d = this.settings.getDouble("MoneyManagement.InitialCapital");
        if (this.optimizationSettings.periodType == 30 && marketData == null && (n5 = this.getReservedBars()) > 0) {
            marketData = this.getMarketData();
        }
        ArrayList<WalkForwardPeriod> arrayList = this.computeWFPeriods(n3, n4, n5, marketData);
        String string2 = this.settings.getString("StrategyName");
        if (resultsGroup == null) {
            object3 = this.prepareIndexesArray(this.parameters.getUsedCount());
            string = "WF Optimization - " + string2;
            resultsGroup = this.testStrategy((short[])object3, string, string2, 0L, 0L);
            this.increaseStep();
        }
        if (this.progressEngine.isStopped()) {
            return null;
        }
        object3 = OptimizationConst.printWFByPeriodType(n, n4, n3);
        string = "Computing " + (String)object3;
        this.printLog(string);
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(string);
        }
        object3 = this.performSimulatedWFOptimization(resultsGroup, (String)object3, n2, arrayList, string2);
        String string3 = resultsGroup.subResult(resultsGroup.getMainResultKey()).getString(SpecialValues.Symbol);
        String string4 = resultsGroup.subResult(resultsGroup.getMainResultKey()).getString(SpecialValues.Timeframe);
        if (bl) {
            object2 = resultsGroup.subResult((String)object3);
            ((Result)((Object)object2)).setSettings(this.settings.clone());
            object = this.getStrName(resultsGroup);
            resultsGroup2 = new ResultsGroup((String)object + " - WFM " + n3 + "x" + n4);
            resultsGroup2.addSubresult((String)object3, ((Result)((Object)object2)).getSettings(), (Result)((Object)object2));
            resultsGroup2.orders().addAll(resultsGroup.orders().filterWithClone((String)object3, (byte)0, (byte)127));
        } else {
            resultsGroup2 = resultsGroup;
        }
        if (this.progressEngine.isStopped()) {
            return null;
        }
        object2 = new WalkForwardResult();
        ((WalkForwardResult)object2).wfPeriods = arrayList;
        ((WalkForwardResult)object2).resultName = object3;
        ((WalkForwardResult)object2).stats = resultsGroup.subResult((String)object3).stats((byte)0, (byte)10, (byte)127);
        ((WalkForwardResult)object2).statsOOS = resultsGroup.subResult((String)object3).stats((byte)0, (byte)10, (byte)20);
        ((WalkForwardResult)object2).testParams = resultsGroup.specialValues().getString("OptimizationParameters");
        if (n2 == 2) {
            object = new WalkForwardMatrixResult();
            ((WalkForwardMatrixResult)object).start1 = n3;
            ((WalkForwardMatrixResult)object).start2 = n4;
            ((WalkForwardMatrixResult)object).activeParam1 = n3;
            ((WalkForwardMatrixResult)object).activeParam2 = n4;
            ((WalkForwardMatrixResult)object).periodType = n;
            ((WalkForwardMatrixResult)object).addWFResult(n3, n4, (WalkForwardResult)object2);
            ((WalkForwardMatrixResult)object).computeRobustnessResults(resultsGroup, this.conditionsElem, this.conditions, this.thresholdPct, this.robCombRows, this.robCombCols, this.robMinComb);
            if (((WalkForwardMatrixResult)object).passed) {
                resultsGroup2.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)SpecialValues.FiltersResultPassed);
            } else {
                resultsGroup2.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)((WalkForwardMatrixResult)object).dismissalMessage);
            }
            resultsGroup2.mainResult().set("WalkForwardResult", object);
            resultsGroup2.specialValues().set("WalkForwardConditions", (Object)this.conditionsElem);
            if (bl) {
                resultsGroup2.mainResult().set("WalkForwardResult", object);
                resultsGroup2.specialValues().set("WalkForwardConditions", (Object)this.conditionsElem);
                resultsGroup2.specialValues().set(SpecialValues.Symbol, (Object)string3);
                resultsGroup2.specialValues().set(SpecialValues.Timeframe, (Object)string4);
                resultsGroup2.portfolio().addStrategyXml(resultsGroup.getStrategyXml());
            }
            resultsGroup2.symbols().add(resultsGroup.symbols());
            this.addResultToDatabank(resultsGroup2);
            this.optimizationProfile.reset();
            resultsGroup2.setOptimizationProfile(this.optimizationProfile);
        }
        this.settings.set("MoneyManagement.InitialCapital", (Object)d);
        if (bl) {
            resultsGroup2.setLastSettings(resultsGroup.getLastSettings());
        }
        return object2;
    }

    private String getStrName(ResultsGroup resultsGroup) {
        String string = resultsGroup.getName();
        int n = string.indexOf("- RA");
        if (n < 0) {
            return string;
        }
        int n2 = string.indexOf(" -", n + 2);
        if (n2 < 0) {
            return string;
        }
        String string2 = string.substring(n + 2, n2);
        return string2;
    }

    private long printTime(long l, String string) {
        long l2 = System.currentTimeMillis();
        System.out.println(string + " : " + (l2 - l));
        return l2;
    }

    private int getReservedBars() {
        TradingOptions tradingOptions = (TradingOptions)this.settings.get("TradingOptions");
        for (TradingOption tradingOption : tradingOptions) {
            if (!(tradingOption instanceof ReservedBars)) continue;
            ReservedBars reservedBars = (ReservedBars)tradingOption;
            return reservedBars.ReservedBars;
        }
        return 0;
    }

    private void processWFOptJobResult(WFOptJobResult wFOptJobResult, JobDetails jobDetails) {
    }

    protected void optimizeMultiWF() throws Exception {
        if (this.progressEngine.isStopped()) {
            return;
        }
        short[] sArray = this.prepareIndexesArray(this.parameters.getUsedCount());
        String string = this.settings.getString("StrategyName");
        String string2 = "WF Matrix - " + string;
        ResultsGroup resultsGroup = this.testStrategy(sArray, string2, string, 0L, 0L);
        if (this.progressEngine.isStopped()) {
            if (resultsGroup != null) {
                resultsGroup.clear();
            }
            return;
        }
        this.printLog("Computing Walk-Forward Matrix");
        WalkForwardMatrixResult walkForwardMatrixResult = new WalkForwardMatrixResult();
        walkForwardMatrixResult.start1 = this.optimizationSettings.param1Start;
        walkForwardMatrixResult.stop1 = this.optimizationSettings.param1Stop;
        walkForwardMatrixResult.increment1 = this.optimizationSettings.param1Step;
        walkForwardMatrixResult.start2 = this.optimizationSettings.param2Start;
        walkForwardMatrixResult.stop2 = this.optimizationSettings.param2Stop;
        walkForwardMatrixResult.increment2 = this.optimizationSettings.param2Step;
        walkForwardMatrixResult.periodType = this.optimizationSettings.periodType;
        int n = 0;
        MarketData marketData = null;
        if (this.optimizationSettings.periodType == 30 && (n = this.getReservedBars()) > 0) {
            marketData = this.getMarketData();
        }
        for (int i = walkForwardMatrixResult.start1; i <= walkForwardMatrixResult.stop1; i += walkForwardMatrixResult.increment1) {
            for (int j = walkForwardMatrixResult.start2; j <= walkForwardMatrixResult.stop2; j += walkForwardMatrixResult.increment2) {
                WalkForwardResult walkForwardResult = this.optimizeWF(resultsGroup, this.optimizationSettings.periodType, 3, i, j, n, marketData, false);
                if (this.progressEngine.isStopped()) {
                    if (resultsGroup != null) {
                        resultsGroup.clear();
                    }
                    return;
                }
                if (walkForwardResult == null) continue;
                walkForwardMatrixResult.addWFResult(i, j, walkForwardResult);
            }
        }
        walkForwardMatrixResult.computeRobustnessResults(resultsGroup, this.conditionsElem, this.conditions, this.thresholdPct, this.robCombRows, this.robCombCols, this.robMinComb);
        resultsGroup.mainResult().set("WalkForwardResult", walkForwardMatrixResult);
        if (walkForwardMatrixResult.passed) {
            resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)SpecialValues.FiltersResultPassed);
        } else {
            resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)walkForwardMatrixResult.dismissalMessage);
        }
        resultsGroup.specialValues().set("WalkForwardConditions", (Object)this.conditionsElem);
        this.optimizationProfile.reset();
        resultsGroup.setOptimizationProfile(this.optimizationProfile);
        this.addResultToDatabank(resultsGroup);
    }

    private String performSimulatedWFOptimization(ResultsGroup resultsGroup, final String string, int n, final ArrayList<WalkForwardPeriod> arrayList, final String string2) throws Exception {
        Object object;
        Object object2;
        ++this.runNumber;
        long l = Long.MAX_VALUE;
        long l2 = Long.MIN_VALUE;
        if (this.optimizationSettings.optimizationType == 1) {
            // empty if block
        }
        final ArrayList arrayList2 = new ArrayList();
        for (int i = 0; i < arrayList.size(); ++i) {
            arrayList2.add(null);
        }
        this.wfBatchCreated = false;
        SimpleGridEngine<WFSimulationJob, WFSimulationJobResult> simpleGridEngine = new SimpleGridEngine<WFSimulationJob, WFSimulationJobResult>(this, this.getStopPauseEngine(), null, this.optimizationSettings.singleThreaded){
            final /* synthetic */ OptimizationEngineWF this$0;
            {
                this.this$0 = optimizationEngineWF;
                super(stopPauseEngine, gridJob, bl);
            }

            @Override
            protected ArrayList<WFSimulationJob> createJobsBatch(int n, GridClient gridClient) throws Exception {
                return this.this$0.createWFSimBatch(gridClient, this.this$0.getStopPauseEngine(), string, arrayList, string2);
            }

            @Override
            protected void processResult(WFSimulationJobResult wFSimulationJobResult, JobDetails jobDetails) throws Exception {
                this.this$0.processWFSimJobResult(wFSimulationJobResult, jobDetails, arrayList2);
            }

            @Override
            protected void onError(String string3, Exception exception) {
                Log.error("MC Error {}, Exception ", (Object)string3, (Object)exception);
            }
        };
        simpleGridEngine.start();
        simpleGridEngine.unregisterListeners();
        resultsGroup.addSubresult(string, this.settings);
        long l3 = Long.MAX_VALUE;
        long l4 = Long.MIN_VALUE;
        OutOfSample outOfSample = new OutOfSample();
        for (int i = 0; i < arrayList.size(); ++i) {
            object2 = arrayList.get(i);
            if (object2.runFrom < l) {
                l = object2.runFrom;
            }
            if (object2.runTo > l2) {
                l2 = object2.runTo;
            }
            if (object2.runFrom < l3) {
                l3 = object2.runFrom;
            }
            if (object2.optimizeTo > l4) {
                l4 = object2.optimizeTo;
            }
            if ((object = (OrdersList)arrayList2.get(i)) == null) continue;
            for (int j = 0; j < ((OrdersList)object).size(); ++j) {
                Order order = ((OrdersList)object).get(j);
                order.IsInPortfolio = 0;
                order.SetupName = string;
                order.Ticket = j + 1;
                long l5 = this.optimizationSettings.periodType == 30 ? order.CloseTime : order.OpenTime;
                if (l5 < l) continue;
                order.SampleType = (byte)21;
            }
            resultsGroup.orders().addAll((OrdersList)object);
            ((OrdersList)object).clear();
        }
        outOfSample.addRange(l, l2, (byte)20);
        SettingsMap settingsMap = resultsGroup.subResult(string).getSettings();
        settingsMap.set("PortfolioDataStart", (Object)l3);
        settingsMap.set("PortfolioDataEnd", (Object)l4);
        object2 = (OutOfSample)settingsMap.get("OutOfSample");
        settingsMap.set("OutOfSample", (Object)outOfSample);
        resultsGroup.subResult(string).computeAllStats(resultsGroup.specialValues(), null);
        settingsMap.set("OutOfSample", object2);
        object = resultsGroup.subResult(string);
        ResultsGroup resultsGroup2 = new ResultsGroup("wfRG");
        resultsGroup2.addSubresult(string, ((Result)((Object)object)).getSettings(), (Result)((Object)object));
        double d = this.fitnessFunction.computeFitness(resultsGroup2, (byte)0, (byte)10);
        ((Result)((Object)object)).setFitness((byte)10, d);
        d = this.fitnessFunction.computeFitness(resultsGroup2, (byte)0, (byte)127);
        ((Result)((Object)object)).setFitness((byte)127, d);
        d = this.fitnessFunction.computeFitness(resultsGroup2, (byte)0, (byte)20);
        ((Result)((Object)object)).setFitness((byte)20, d);
        resultsGroup2.portfolio().setFitness((byte)127, d);
        return string;
    }

    protected ArrayList<WFSimulationJob> createWFSimBatch(GridClient gridClient, StopPauseEngine stopPauseEngine, String string, ArrayList<WalkForwardPeriod> arrayList, String string2) {
        if (this.wfBatchCreated) {
            return null;
        }
        ArrayList<WFSimulationJob> arrayList2 = new ArrayList<WFSimulationJob>();
        for (int i = 0; i < arrayList.size(); ++i) {
            WalkForwardPeriod walkForwardPeriod = arrayList.get(i);
            String string3 = String.format("%s WFO %d", string, i);
            boolean bl = i == arrayList.size() - 1;
            WFSimulationJob wFSimulationJob = new WFSimulationJob(string3, this.getWFSimJobSettings(), this.getStopPauseEngine(), this.lastEventListener, string, bl, this.fitnessFunction, this.settings, this.optimizationSettings, this.fitnessStatsComputer.getClone(), this.wfoSimulationEngine, walkForwardPeriod, i, string2);
            arrayList2.add(wFSimulationJob);
        }
        this.wfBatchCreated = true;
        if (arrayList2.size() == 0) {
            return null;
        }
        return arrayList2;
    }

    private Map<String, Serializable> getWFSimJobSettings() {
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        return hashMap;
    }

    protected void processWFSimJobResult(WFSimulationJobResult wFSimulationJobResult, JobDetails jobDetails, ArrayList<OrdersList> arrayList) {
        String string = jobDetails.getJobID();
        this.increaseStep(2);
        if (jobDetails.isSuccess()) {
            OrdersList ordersList = wFSimulationJobResult.getOrders();
            int n = wFSimulationJobResult.getIndex();
            if (ordersList != null && n >= 0 && n < arrayList.size()) {
                arrayList.set(n, ordersList);
            } else {
                Log.debug("WF Sim job returned empty orders");
            }
        } else {
            jobDetails.getException();
            Log.error(String.format("Optimization %s failed, error: %s", string, jobDetails.getException()));
        }
    }

    private String performSimulatedWFOptimizationOld(ResultsGroup resultsGroup, String string, int n, ArrayList<WalkForwardPeriod> arrayList) throws Exception {
        Object object;
        int n2;
        long l;
        ++this.runNumber;
        ResultsGroup resultsGroup2 = null;
        OrdersList ordersList = new OrdersList("performSimulatedWFOptimization");
        long l2 = Long.MAX_VALUE;
        if (this.optimizationSettings.optimizationType == 1) {
            // empty if block
        }
        long l3 = l = System.currentTimeMillis();
        for (n2 = 0; n2 < arrayList.size(); ++n2) {
            Object object2;
            object = arrayList.get(n2);
            if (((WalkForwardPeriod)object).runFrom < l2) {
                l2 = ((WalkForwardPeriod)object).runFrom;
            }
            if (this.lastEventListener != null) {
                object2 = L.t((String)"Computing period %d for %s", (Object[])new Object[]{n2, string});
                this.lastEventListener.setLastEvent((String)object2);
            }
            ResultsGroup resultsGroup3 = this.runSimpleSimulatedOptimization(n2, ((WalkForwardPeriod)object).optimizeFrom, ((WalkForwardPeriod)object).optimizeTo);
            if (n2 == 0 && resultsGroup3 != null) {
                ordersList.addAll(resultsGroup3.orders());
            }
            if (this.progressEngine.isStopped()) {
                if (resultsGroup3 != null) {
                    resultsGroup3.clear();
                }
                return null;
            }
            this.increaseStep();
            ((WalkForwardPeriod)object).optimizationStatData = resultsGroup3.portfolio().stats((byte)0, (byte)10, (byte)127).getClone();
            if (n2 == 0) {
                // empty if block
            }
            if (n2 < arrayList.size() - 1) {
                object2 = (short[])resultsGroup3.specialValues().get("OptimizationParametersArray");
                resultsGroup2 = this.optimizationSettings.optimizationType == 1 ? this.testStrategy((short[])object2, "WF Simulation", "Run strategy " + n2, ((WalkForwardPeriod)object).runFrom, ((WalkForwardPeriod)object).runTo) : this.runSimpleSimulationRun(resultsGroup3, "Run strategy " + n2, ((WalkForwardPeriod)object).runFrom, ((WalkForwardPeriod)object).runTo);
                ((WalkForwardPeriod)object).runStatData = resultsGroup2.portfolio().stats((byte)0, (byte)10, (byte)127).getClone();
                if (n2 != 0) {
                    // empty if block
                }
                ordersList.addAll(resultsGroup2.orders());
                resultsGroup2.clear();
            }
            ((WalkForwardPeriod)object).testParameters = resultsGroup3.specialValues().getString("OptimizationParameters");
            resultsGroup3.clear();
            this.increaseStep();
        }
        resultsGroup.addSubresult(string, this.settings);
        for (n2 = 0; n2 < ordersList.size(); ++n2) {
            object = ordersList.get(n2);
            ((Order)object).SetupName = string;
            ((Order)object).Ticket = n2 + 1;
            if (((Order)object).OpenTime < l2) continue;
            ((Order)object).SampleType = (byte)21;
        }
        resultsGroup.orders().addAll(ordersList);
        ordersList.clear();
        resultsGroup.subResult(string).computeAllStats(resultsGroup.specialValues(), null);
        Result result = resultsGroup.subResult(string);
        object = new ResultsGroup("wfRG");
        ((ResultsGroup)object).addSubresult(string, result.getSettings(), result);
        double d = this.fitnessFunction.computeFitness((ResultsGroup)object, (byte)0, (byte)10);
        result.setFitness((byte)10, d);
        d = this.fitnessFunction.computeFitness((ResultsGroup)object, (byte)0, (byte)127);
        result.setFitness((byte)127, d);
        d = this.fitnessFunction.computeFitness((ResultsGroup)object, (byte)0, (byte)20);
        result.setFitness((byte)20, d);
        ((ResultsGroup)object).portfolio().setFitness((byte)127, d);
        return string;
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
        resultsGroup2.computeAllStats();
        return resultsGroup2;
    }

    protected ResultsGroup runSimpleSimulatedOptimization(int n, long l, long l2) throws Exception {
        ResultsGroup resultsGroup = null;
        double d = -1.0;
        ArrayList<WFVariant> arrayList = this.wfoSimulationEngine.getVariants();
        String string = "";
        for (int i = 0; i < arrayList.size(); ++i) {
            if (this.progressEngine.isStopped()) {
                if (resultsGroup != null) {
                    resultsGroup.clear();
                }
                return null;
            }
            ResultsGroup resultsGroup2 = this.wfoSimulationEngine.simulateTestCandidate(this.fitnessStatsComputer, arrayList.get(i), l, l2, this.cloneBacktestSettings(l, l2));
            if (resultsGroup2 == null) continue;
            double d2 = this.computeFitness(resultsGroup2);
            if (d == -1.0 || d < d2) {
                if (resultsGroup != null) {
                    resultsGroup.clear();
                }
                d = d2;
                resultsGroup = resultsGroup2;
                string = arrayList.get((int)i).params;
                resultsGroup.specialValues().set("OptVariantIndex", (Object)i);
                continue;
            }
            resultsGroup2.clear();
        }
        Log.debug("Best candiate params: {}", (Object)string);
        if (resultsGroup == null) {
            throw new Exception(L.t((String)"Optimization not successful, please check log for more information!", (Object[])new Object[0]));
        }
        resultsGroup.computeAllStats();
        return resultsGroup;
    }

    protected ArrayList<WalkForwardPeriod> computeWFPeriods(int n, int n2, int n3, MarketData marketData) {
        int n4;
        int n5;
        if (this.optimizationSettings.periodType == 20 || this.optimizationSettings.periodType == 30) {
            n5 = n;
            n4 = n2;
        } else {
            double d = n2;
            double d2 = (double)n / 100.0;
            n5 = (int)((double)this.totalDays / (1.0 + d * d2));
            n4 = (int)((double)n5 * d2);
            long l = this.totalDays - (long)(n5 + (int)d * n4) - (long)((int)d + 2);
            n5 = (int)((long)n5 + l);
        }
        ArrayList<WalkForwardPeriod> arrayList = this.computeWalkForwardPeriods(n5, n4, n3, marketData);
        for (int i = 0; i < arrayList.size(); ++i) {
            WalkForwardPeriod walkForwardPeriod = arrayList.get(i);
            this.progressEngine.checkPaused();
        }
        return arrayList;
    }

    private ArrayList<WalkForwardPeriod> computeWalkForwardPeriods(int n, int n2, int n3, MarketData marketData) {
        WalkForwardPeriod walkForwardPeriod;
        SQTimeOld sQTimeOld;
        ChartSetups chartSetups = (ChartSetups)this.settings.get("ChartSetups");
        ChartSetup chartSetup = chartSetups.getMainSetup();
        int n4 = -1;
        int n5 = -1;
        if (n3 > 0 && marketData != null) {
            long l = marketData.getDateBarsFromDate(0L, n3);
            SQTimeOld sQTimeOld2 = new SQTimeOld(l);
            sQTimeOld = new SQTimeOld(SQTime.correctDayStart((long)sQTimeOld2.getMilis()));
        } else {
            sQTimeOld = new SQTimeOld(chartSetup.getMainChart().getHistoryFrom());
        }
        ArrayList<WalkForwardPeriod> arrayList = new ArrayList<WalkForwardPeriod>();
        long l = -1L;
        boolean bl = false;
        if (n3 > 0 && marketData != null) {
            --n2;
        }
        int n6 = 0;
        WalkForwardPeriod walkForwardPeriod2 = null;
        do {
            int n7;
            ++n6;
            walkForwardPeriod = new WalkForwardPeriod();
            if (n3 > 0 && marketData != null) {
                long l2;
                if (walkForwardPeriod2 == null) {
                    walkForwardPeriod.optimizeFrom = sQTimeOld.getMilis();
                    l2 = marketData.getDateBarsFromDate(walkForwardPeriod.optimizeFrom, n);
                    walkForwardPeriod.optimizeTo = SQTime.correctDayEnd((long)l2);
                    walkForwardPeriod.runFrom = SQTime.correctDayStart((long)this.addDaysReturnDate(walkForwardPeriod.optimizeTo, 1).getMilis());
                    l2 = marketData.getDateBarsFromDate(walkForwardPeriod.runFrom, n2);
                    walkForwardPeriod.runTo = SQTime.correctDayEnd((long)l2);
                } else {
                    walkForwardPeriod.runFrom = SQTime.correctDayStart((long)this.addDaysReturnDate(walkForwardPeriod2.runTo, 1).getMilis());
                    l2 = marketData.getDateBarsFromDate(walkForwardPeriod.runFrom, n2);
                    walkForwardPeriod.runTo = SQTime.correctDayEnd((long)l2);
                    walkForwardPeriod.optimizeTo = SQTime.correctDayEnd((long)this.addDaysReturnDate(walkForwardPeriod.runFrom, -1).getMilis());
                    l2 = marketData.getDateBarsFromDate(walkForwardPeriod.optimizeTo, -(n + 0));
                    walkForwardPeriod.optimizeFrom = SQTime.correctDayStart((long)l2);
                }
                n5 = SQTime.getDiffInDays((long)walkForwardPeriod.optimizeTo, (long)walkForwardPeriod.optimizeFrom) + 1;
                n4 = SQTime.getDiffInDays((long)walkForwardPeriod.runTo, (long)walkForwardPeriod.runFrom) + 1;
                walkForwardPeriod2 = walkForwardPeriod;
            } else {
                walkForwardPeriod.optimizeFrom = this.optimizationSettings.floating ? sQTimeOld.getMilis() : chartSetup.getMainChart().getHistoryFrom();
                l = l < 0L ? walkForwardPeriod.optimizeFrom : sQTimeOld.getMilis();
                walkForwardPeriod.optimizeTo = SQTime.correctDayEnd((long)this.addDaysReturnDate(l, n).getMilis());
                walkForwardPeriod.runFrom = SQTime.correctDayStart((long)this.addDaysReturnDate(walkForwardPeriod.optimizeTo, 1).getMilis());
                walkForwardPeriod.runTo = this.addDaysReturnDate(walkForwardPeriod.runFrom, n2).getMilis();
                n5 = n;
                n4 = n2;
            }
            SQTimeOld sQTimeOld3 = this.addDaysReturnDate(walkForwardPeriod.runTo, n4 + 1 + 1);
            if (sQTimeOld3.getMilis() > chartSetup.getMainChart().getHistoryTo()) {
                int n8;
                sQTimeOld3.addDays(-n4 - 1);
                n7 = SQTimeOld.getDaysBetween((long)sQTimeOld3.getMilis(), (long)chartSetup.getMainChart().getHistoryTo());
                if (n7 < 0 && (marketData == null || walkForwardPeriod2 != null && (double)n4 < (double)(n8 = SQTime.getDaysBetween((long)walkForwardPeriod2.runFrom, (long)walkForwardPeriod2.runTo)) * 0.6)) break;
                if (n7 < n4 / 3) {
                    walkForwardPeriod.runTo = chartSetup.getMainChart().getHistoryTo();
                    bl = true;
                }
            }
            if (!bl && walkForwardPeriod.runTo >= chartSetup.getMainChart().getHistoryTo()) {
                walkForwardPeriod.runTo = chartSetup.getMainChart().getHistoryTo();
                bl = true;
            }
            n7 = Math.abs(SQTime.getDaysBetween((long)chartSetup.getMainChart().getHistoryTo(), (long)walkForwardPeriod.runTo));
            if (!bl && n7 >= 0 && (double)n7 <= 0.3 * (double)n4) {
                walkForwardPeriod.runTo = chartSetup.getMainChart().getHistoryTo();
                bl = true;
            }
            if (walkForwardPeriod.runTo < walkForwardPeriod.runFrom) break;
            arrayList.add(walkForwardPeriod);
            if (n3 > 0 && marketData != null) continue;
            sQTimeOld.addDays(n2 + 1);
        } while (!bl);
        if (n3 > 0 && marketData != null) {
            walkForwardPeriod = (WalkForwardPeriod)arrayList.get(arrayList.size() - 1);
            walkForwardPeriod.runTo = chartSetup.getMainChart().getHistoryTo();
        }
        walkForwardPeriod = new WalkForwardPeriod();
        walkForwardPeriod.optimizeTo = chartSetup.getMainChart().getHistoryTo();
        walkForwardPeriod.optimizeFrom = this.optimizationSettings.floating ? this.addDaysReturnDate(walkForwardPeriod.optimizeTo, -n5 - 1).getMilis() : chartSetup.getMainChart().getHistoryFrom();
        walkForwardPeriod.runFrom = chartSetup.getMainChart().getHistoryTo();
        walkForwardPeriod.runTo = this.addDaysReturnDate(walkForwardPeriod.runFrom, n4).getMilis();
        walkForwardPeriod.futurePeriod = true;
        arrayList.add(walkForwardPeriod);
        return arrayList;
    }

    private SQTimeOld addDaysReturnDate(long l, int n) {
        SQTimeOld sQTimeOld = new SQTimeOld(l);
        sQTimeOld.addDays(n);
        return sQTimeOld;
    }
}

