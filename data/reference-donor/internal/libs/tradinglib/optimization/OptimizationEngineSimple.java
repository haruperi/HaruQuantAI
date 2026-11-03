/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.random.MersenneTwisterRng
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.L;
import com.strategyquant.lib.random.MersenneTwisterRng;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.gp.EvolutionPipeline;
import com.strategyquant.tradinglib.gp.GPEngine;
import com.strategyquant.tradinglib.gp.GPEvolutionMessage;
import com.strategyquant.tradinglib.gp.GPEvolutionPopulationMessage;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.GPSettings;
import com.strategyquant.tradinglib.gp.IGPEvolutionMessagesListener;
import com.strategyquant.tradinglib.gp.RouletteWheelSelection;
import com.strategyquant.tradinglib.optimization.OptimizationEngineBase;
import com.strategyquant.tradinglib.optimization.OptimizationIndexes;
import com.strategyquant.tradinglib.optimization.OptimizationIndexesCrossover;
import com.strategyquant.tradinglib.optimization.OptimizationIndexesFactory;
import com.strategyquant.tradinglib.optimization.OptimizationIndexesMutation;
import com.strategyquant.tradinglib.optimization.OptimizationMethods;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestJob;
import com.strategyquant.tradinglib.optimization.OptimizerBacktestEvaluator;
import com.strategyquant.tradinglib.optimization.PopulationGenerations;
import com.strategyquant.tradinglib.optimization.StrategyParamData;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import com.strategyquant.tradinglib.wfo.WFOSimulationEngine;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationEngineSimple
extends OptimizationEngineBase {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationEngineSimple");
    private int lastIndex;
    protected WFOSimulationEngine wfoSimulationEngine;
    protected int actualStep;
    private GPEngine<OptimizationIndexes> gpEngine;
    private GridJob parentGridJob;
    protected OptimizationProfile optimizationProfile;
    protected ConditionsChecker conditionsChecker = new ConditionsChecker();

    public OptimizationEngineSimple(String string, StopPauseEngine stopPauseEngine, GridJob gridJob, String string2, ILastEventListener iLastEventListener, String string3) {
        super(string, stopPauseEngine, string2, iLastEventListener, string3);
        this.parentGridJob = gridJob;
    }

    protected int getTotalStepsForSimpleOptimization() {
        long l = this.parameters.getTotalCombinations();
        PopulationGenerations populationGenerations = OptimizationMethods.suggestPopulationGenerations(l, this.optimizationSettings.optimizationMethod, this.optimizationSettings.maxOptimizationBacktests);
        if (populationGenerations.method == 1) {
            return (int)l + 1;
        }
        return 1 + populationGenerations.generations * populationGenerations.population;
    }

    protected int runSimpleOptimization(int n, long l, long l2, int n2, boolean bl) throws Exception {
        long l3 = this.parameters.getTotalCombinations();
        PopulationGenerations populationGenerations = OptimizationMethods.suggestPopulationGenerations(l3, this.optimizationSettings.optimizationMethod, this.optimizationSettings.maxOptimizationBacktests);
        long l4 = OptimizationMethods.getTotalCombinations(l3, populationGenerations, this.optimizationSettings.maxOptimizationBacktests);
        int n3 = 0;
        this.wfoSimulationEngine = null;
        if (n == 0) {
            short[] sArray = this.prepareIndexesArray(this.parameters.getUsedCount());
            String string = this.settings.getString("StrategyName");
            this.printLog(L.t((String)"Testing original parameters", (Object[])new Object[0]));
            if (l3 == 1L || bl || !this.optimizationSettings.dontSaveOriginalStr) {
                if (l3 == 1L) {
                    string = string + "(Optimized)";
                }
                ResultsGroup resultsGroup = this.testStrategy(sArray, string, string, 0L, 0L);
                n3 = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
                if (bl) {
                    this.wfoSimulationEngine = new WFOSimulationEngine(this.optimizationSettings.periodType == 30);
                }
                this.addResultToDatabank(resultsGroup);
                this.optimizationProfile.addOriginalResult(resultsGroup);
                if (l3 == 1L) {
                    return n3;
                }
            }
            this.increaseStep();
        }
        if (l3 == 1L) {
            // empty if block
        }
        if (populationGenerations.method == 1) {
            this.printLog(L.t((String)"Brute Force method", (Object[])new Object[0]));
            this.runBruteForceOptimization(n, l, l2, n2, l3);
        } else {
            this.printLog(L.t((String)"Genetic optimization method", (Object[])new Object[0]));
            Log.debug("Population: {}, Generations: {}", (Object)populationGenerations.population, (Object)populationGenerations.generations);
            this.printLog(L.t((String)"Genetic optimization of parameters started, please wait, it might take some time...", (Object[])new Object[0]));
            this.runGeneticOptimization(populationGenerations, n, l, l2, n2, l3, l4);
        }
        return n3;
    }

    private void runGeneticOptimization(PopulationGenerations populationGenerations, int n, long l, long l2, final int n2, long l3, long l4) throws Exception {
        GPSettings<OptimizationIndexes> gPSettings = this.getGPSettings(populationGenerations);
        this.gpEngine = new GPEngine<OptimizationIndexes>(gPSettings, this.progressEngine, null, this.parentGridJob, this.source);
        this.gpEngine.setEvolutionMessagesListener(new IGPEvolutionMessagesListener<OptimizationIndexes>(){
            final /* synthetic */ OptimizationEngineSimple this$0;
            {
                this.this$0 = optimizationEngineSimple;
            }

            @Override
            public void newCandidate(OptimizationIndexes optimizationIndexes) {
                this.this$0.processNewCandidate(optimizationIndexes, this.this$0.gpEngine, n2);
            }

            @Override
            public void evolutionMessage(GPEvolutionMessage gPEvolutionMessage) {
                this.this$0.processEvolutionMessage(gPEvolutionMessage);
            }

            @Override
            public void lastPopulation(GPEvolutionPopulationMessage gPEvolutionPopulationMessage) {
            }

            @Override
            public void evolutionException(Serializable serializable) {
            }
        });
        this.gpEngine.start();
        if (!gPSettings.singleThreaded) {
            do {
                Thread.sleep(200L);
            } while (!this.gpEngine.isFinished() && !this.progressEngine.isStopped());
        }
        this.gpEngine.unregisterListeners();
    }

    private GPSettings<OptimizationIndexes> getGPSettings(PopulationGenerations populationGenerations) throws Exception {
        OptimizationIndexesFactory optimizationIndexesFactory;
        GPSettings<OptimizationIndexes> gPSettings = new GPSettings<OptimizationIndexes>();
        gPSettings.populationSize = populationGenerations.population;
        gPSettings.maxGenerations = populationGenerations.generations;
        gPSettings.elitismSize = gPSettings.populationSize <= 10 ? 1 : 2;
        gPSettings.decimationCoefficient = 0;
        gPSettings.numberOfIslands = 1;
        gPSettings.migrationRate = 0.1;
        gPSettings.migrationGenerationsModulo = 8;
        gPSettings.naturalFitness = true;
        gPSettings.printPopulationToLog = true;
        gPSettings.sendEveryCandidateEvent = true;
        gPSettings.rng = new MersenneTwisterRng();
        gPSettings.factory = optimizationIndexesFactory = new OptimizationIndexesFactory(this.parameters);
        ArrayList arrayList = new ArrayList(3);
        arrayList.add(new OptimizationIndexesCrossover(this.parameters));
        arrayList.add(new OptimizationIndexesMutation(this.parameters, 0.2));
        gPSettings.evolutionPipeline = new EvolutionPipeline(arrayList);
        gPSettings.evaluator = new OptimizerBacktestEvaluator(this.getBacktestSettings(), this.optimizationSettings, this.progressEngine, this.lastEventListener, this.lastSettingsXml);
        gPSettings.selectionStrategy = new RouletteWheelSelection();
        gPSettings.singleThreaded = this.optimizationSettings.singleThreaded;
        return gPSettings;
    }

    private BacktestSettings getBacktestSettings() throws Exception {
        BacktestSettings backtestSettings = new BacktestSettings();
        backtestSettings.initialCapital = (Double)this.settings.get("MoneyManagement.InitialCapital");
        backtestSettings.fitnessFunction = (IFitnessFunction)this.settings.get("FitnessFunction");
        backtestSettings.tradingOptions = ((TradingOptions)this.settings.get("TradingOptions")).getClone();
        backtestSettings.moneyManagementMethod = (MoneyManagementMethod)this.settings.get("MoneyManagement.Method");
        backtestSettings.riskManagementMethod = (RiskManagementMethod)this.settings.get("RiskManagement");
        ATM aTM = (ATM)this.settings.get("ATM");
        backtestSettings.atm = aTM != null ? aTM.getClone() : null;
        backtestSettings.rankingConditions = null;
        backtestSettings.dismissBadStrategies = 0;
        backtestSettings.outOfSample = null;
        backtestSettings.chartSetups = ((ChartSetups)this.settings.get("ChartSetups")).getClone(0L, 0L);
        backtestSettings.useCrossChecks = false;
        backtestSettings.crossChecks = null;
        backtestSettings.slippage = (Double)this.settings.get("Slippage");
        backtestSettings.minDistance = (Double)this.settings.get("MinDistance");
        backtestSettings.commission = (CommissionsMethod)this.settings.get("Commission");
        backtestSettings.swap = (SwapMethod)this.settings.get("Swap");
        backtestSettings.strategyName = this.settings.getString("StrategyName");
        backtestSettings.elStrategy = (Element)this.settings.get("StrategyXml");
        backtestSettings.lastSettings = (Element)this.settings.get("StrategyLastSettings");
        return backtestSettings;
    }

    protected void processNewCandidate(OptimizationIndexes optimizationIndexes, GPEngine<OptimizationIndexes> gPEngine, int n) {
        GPIDs gPIDs = optimizationIndexes.getGPIDs();
        String string = String.format("Candidate %d.%d.%d", gPIDs.islandIndex, gPIDs.generationIndex, gPIDs.nodeIndex);
        int n2 = optimizationIndexes.getDismissalReason();
        String string2 = String.format(".%2f", optimizationIndexes.getFitness((byte)0));
        String string3 = OptimizationIndexes.convertToString(optimizationIndexes.getIndexes());
        if (n2 == 0) {
            ResultsGroup resultsGroup = optimizationIndexes.getResult();
            if (resultsGroup != null) {
                try {
                    double d = resultsGroup.specialValues().getDouble(SpecialValues.BacktestDuration, 0.0);
                    this.processOptimizationResult(resultsGroup, n, d);
                }
                catch (Exception exception) {
                    exception.printStackTrace();
                    Log.error("Exception processing result", (Throwable)exception);
                }
            } else {
                Log.debug("Candidate {} doesn't have test result set!", (Object)string);
            }
        } else {
            Log.debug("Dismissed {} with fitness {} - {} : {}", new Object[]{string, string2, optimizationIndexes.getErrorMsg(), string3});
        }
    }

    protected void processEvolutionMessage(GPEvolutionMessage gPEvolutionMessage) {
        if (gPEvolutionMessage.messageType == 30) {
            this.increaseStep(gPEvolutionMessage.populationSize);
        }
    }

    private void runBruteForceOptimization(final int n, long l, long l2, final int n2, final long l3) throws Exception {
        if (n2 == 1) {
            // empty if block
        }
        this.lastIndex = 0;
        SimpleGridEngine<OptimizationTestJob, BacktestResult> simpleGridEngine = new SimpleGridEngine<OptimizationTestJob, BacktestResult>(this, this.progressEngine, this.parentGridJob, this.optimizationSettings.singleThreaded){
            final /* synthetic */ OptimizationEngineSimple this$0;
            {
                this.this$0 = optimizationEngineSimple;
                super(stopPauseEngine, gridJob, bl);
            }

            @Override
            protected ArrayList<OptimizationTestJob> createJobsBatch(int n3, GridClient gridClient) throws Exception {
                return this.this$0.createBatch(n, n3, gridClient, l3);
            }

            @Override
            protected void processResult(BacktestResult backtestResult, JobDetails jobDetails) throws Exception {
                this.this$0.processSimpleOptimizationResult(backtestResult, jobDetails, n2);
            }

            @Override
            protected void onError(String string, Exception exception) {
                this.this$0.printLog(string);
                this.this$0.progressEngine.stop();
            }
        };
        simpleGridEngine.start();
        simpleGridEngine.unregisterListeners();
    }

    protected ArrayList<OptimizationTestJob> createBatch(int n, int n2, GridClient gridClient, long l) throws Exception {
        ArrayList<OptimizationTestJob> arrayList = new ArrayList<OptimizationTestJob>();
        int n3 = 0;
        for (long i = (long)this.lastIndex; i < (long)(this.lastIndex + n2) && i < l; ++i) {
            String string = String.format("Optimized %d.%d", n, i);
            OptimizationTestJob optimizationTestJob = new OptimizationTestJob(string, this.getParams(string, i), this.progressEngine, this.optimizationSettings.periodType);
            arrayList.add(optimizationTestJob);
            ++n3;
        }
        this.lastIndex += n3;
        if (arrayList.size() == 0) {
            return null;
        }
        return arrayList;
    }

    private Map<String, Serializable> getParams(String string, long l) throws Exception {
        short[] sArray = this.prepareIndexesArray(this.parameters.getUsedCount());
        this.parameters.prepareTestParameters(l, sArray);
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        String string2 = this.settings.getString("StrategyName");
        hashMap.put("ChartSetups", ((ChartSetups)this.settings.get("ChartSetups")).getClone());
        hashMap.put("Slippage", Double.valueOf(this.settings.getDouble("Slippage")));
        hashMap.put("MinDistance", Double.valueOf(this.settings.getDouble("MinDistance")));
        hashMap.put("Commission", (CommissionsMethod)this.settings.get("Commission"));
        hashMap.put("Swap", (SwapMethod)this.settings.get("Swap"));
        hashMap.put("MoneyManagement.InitialCapital", Double.valueOf(this.settings.getDouble("MoneyManagement.InitialCapital")));
        hashMap.put("MoneyManagement.Method", (MoneyManagementMethod)this.settings.get("MoneyManagement.Method"));
        hashMap.put("RiskManagement", (RiskManagementMethod)this.settings.get("RiskManagement"));
        hashMap.put("TestPrecision", Integer.valueOf(this.settings.getInt("TestPrecision")));
        hashMap.put("ResultGroupName", (Serializable)((Object)(string2 + " - " + string)));
        hashMap.put("MainResultKey", (Serializable)((Object)string2));
        hashMap.put("FitnessFunction", this.fitnessFunction);
        hashMap.put("TradingOptions", ((TradingOptions)this.settings.get("TradingOptions")).getClone());
        ATM aTM = (ATM)this.settings.get("ATM");
        if (aTM != null) {
            hashMap.put("ATM", aTM.getClone());
        }
        StrategyBase strategyBase = (StrategyBase)this.settings.get("StrategyObject");
        StrategyParamData strategyParamData = StrategyBase.createStrategyVariation(strategyBase, this.optimizationSettings, this.optimizationSettings.transformToFullIndexes(sArray));
        StrategyBase strategyBase2 = strategyParamData.getStrategy();
        String string3 = strategyParamData.getParams();
        hashMap.put("StrategyXml", (Serializable)strategyBase2.getStrategyXml());
        hashMap.put("StrategyLastSettings", (Serializable)((Element)this.settings.get("StrategyLastSettings")));
        hashMap.remove("StrategyObject");
        hashMap.put("OptimizationParams", (Serializable)((Object)string3));
        hashMap.put("OptimizationParamIndexes", (Serializable)sArray);
        return hashMap;
    }

    protected void processSimpleOptimizationResult(BacktestResult backtestResult, JobDetails jobDetails, int n) throws Exception {
        String string = jobDetails.getJobID();
        this.increaseStep();
        if (jobDetails.isSuccess()) {
            ResultsGroup resultsGroup = backtestResult.getResult();
            if (resultsGroup != null) {
                this.processOptimizationResult(resultsGroup, n, (double)jobDetails.getDuration() / 1000.0);
            } else {
                this.printLog(L.t((String)"Optimization %s failed, error: %s", (Object[])new Object[]{string, backtestResult.getDismissalMessage()}));
            }
        } else {
            jobDetails.getException();
            this.printLog(L.t((String)"Optimization %s failed, error: %s", (Object[])new Object[]{string, jobDetails.getException()}));
        }
    }

    private void processOptimizationResult(ResultsGroup resultsGroup, int n, double d) throws Exception {
        if (n != 1 || this.wfoSimulationEngine != null) {
            this.printLog(L.t((String)"Testing %s, OK took %.3f s.", (Object[])new Object[]{resultsGroup.getName(), d}));
        }
        this.optimizationProfile.addResult(resultsGroup);
        if (resultsGroup.getOptimizationProfile() == null) {
            resultsGroup.setOptimizationProfile(this.optimizationProfile);
        }
        boolean bl = true;
        if (n == 1 && this.wfoSimulationEngine == null) {
            String string = this.checkConditions(resultsGroup);
            if (string != null) {
                this.printLog(L.t((String)"Testing %s, dismissed : %s", (Object[])new Object[]{resultsGroup.getName(), string}));
                if (this.optimizationSettings.type == 4) {
                    this.addResultToDatabank(resultsGroup);
                }
            } else {
                this.printLog(L.t((String)"Testing %s, OK took %.3f s.", (Object[])new Object[]{resultsGroup.getName(), d}));
                this.addResultToDatabank(resultsGroup);
            }
            bl = false;
        } else if (this.optimizationSettings.type == 4) {
            this.addResultToDatabank(resultsGroup);
        }
        if (this.wfoSimulationEngine != null) {
            this.wfoSimulationEngine.saveTestToFile(resultsGroup);
        }
        if (bl) {
            resultsGroup.clear();
        }
    }

    private String checkConditions(ResultsGroup resultsGroup) {
        if (this.optimizationSettings.conditions == null) {
            return null;
        }
        for (Condition condition : this.optimizationSettings.conditions) {
            try {
                boolean bl;
                if (!condition.isUsed() || (bl = this.conditionsChecker.check(resultsGroup, condition))) continue;
                return this.conditionsChecker.dismissalMessage;
            }
            catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
            }
            catch (Exception exception) {
                this.printLog(String.format("Error while evaluating conditions: %s", exception.getMessage()));
                Log.error("Error while evaluating condition: ", (Throwable)exception);
            }
        }
        return null;
    }

    protected void clearOptimizationProfile() {
        if (this.optimizationProfile != null) {
            this.optimizationProfile.compute(true, true);
            this.optimizationProfile.clearData();
        }
    }
}

