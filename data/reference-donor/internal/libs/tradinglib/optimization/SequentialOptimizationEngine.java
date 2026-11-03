/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.optimization.IEngineLogListener;
import com.strategyquant.tradinglib.optimization.INewResultListener;
import com.strategyquant.tradinglib.optimization.ISequentialOptimizationCompleteListener;
import com.strategyquant.tradinglib.optimization.IStepsListener;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.SequentialOptimizationJob;
import com.strategyquant.tradinglib.optimization.SequentialOptimizationSettings;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.robustnesstests.FitnessData;
import com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SequentialOptimizationEngine {
    private static final Logger Log = LoggerFactory.getLogger((String)"SequentialOptimizationEngine");
    private final String lastSettingsXml;
    private SequentialOptimizationSettings settings;
    private StopPauseEngine stopPauseEngine;
    private String dismissalMessage = null;
    private ILastEventListener lastEventListener;
    private String jobGroupID;
    private INewResultListener newResultListener = null;
    private IEngineLogListener engineLogListener = null;
    private IStepsListener stepsListener = null;
    private StrategyBase strategy = null;
    private String strategyName;
    private SettingsMap backtestSettings;
    private String lastSettingsXML;
    private ArrayList<Variable> variablesToOptimize;
    private ArrayList<Parameter> optimizationParams;
    private HashMap<Double, ResultsGroup> lastResults;
    private ArrayList<String> parameterNames;
    private ArrayList<Double> parameterValues;
    private int totalCount = 0;
    private int step = 0;

    public SequentialOptimizationEngine(SequentialOptimizationSettings sequentialOptimizationSettings, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener, String string) {
        this.settings = sequentialOptimizationSettings;
        this.stopPauseEngine = stopPauseEngine;
        this.lastEventListener = iLastEventListener;
        this.lastResults = new HashMap();
        this.parameterNames = new ArrayList();
        this.parameterValues = new ArrayList();
        this.variablesToOptimize = new ArrayList();
        this.optimizationParams = new ArrayList();
        this.lastSettingsXml = string;
    }

    public void initialize(String string, Element element, SettingsMap settingsMap) throws Exception {
        int n;
        this.strategyName = string;
        this.backtestSettings = settingsMap;
        this.strategy = StrategyBase.createXmlStrategy(element);
        this.strategy.transformToVariables(this.settings.symmetry, this.settings.paramTypes);
        Variables variables = this.strategy.variables();
        variables.sortByName();
        this.variablesToOptimize.clear();
        this.optimizationParams.clear();
        if (this.settings.manualParams != null) {
            for (n = 0; n < this.settings.manualParams.size(); ++n) {
                Parameter parameter = (Parameter)this.settings.manualParams.get(n);
                if (!parameter.use || !this.shouldOptimizeParameter(parameter.getType(), parameter.getName())) continue;
                Variable variable = variables.get(parameter.getName());
                if (variable == null) {
                    Log.error("Variable with name " + parameter.getName() + " not found. This should not happen!");
                    continue;
                }
                this.variablesToOptimize.add(variable);
                this.optimizationParams.add(parameter);
                this.parameterNames.add(variable.getName());
                this.parameterValues.add(parameter.original);
            }
        } else {
            for (n = 0; n < variables.size(); ++n) {
                Variable variable = (Variable)variables.get(n);
                if (!this.shouldOptimizeParameter(variable.getInternalType(), variable.getName())) continue;
                this.optimizationParams.add(null);
                this.variablesToOptimize.add(variable);
                this.parameterNames.add(variable.getName());
                this.parameterValues.add(variable.getValueAsDouble());
            }
        }
        try {
            Element element2 = (Element)settingsMap.get("StrategyLastSettings");
            this.lastSettingsXML = element2 != null ? XMLUtil.elementToString((Element)element2) : null;
        }
        catch (Exception exception) {
            Log.error("Cannot read last settings", (Throwable)exception);
        }
    }

    public boolean optimize(boolean bl, boolean bl2, GridJob gridJob, ISequentialOptimizationCompleteListener iSequentialOptimizationCompleteListener) throws Exception {
        Object object;
        Object object2;
        Object object3;
        if (this.variablesToOptimize.size() == 0) {
            this.dismissalMessage = L.t((String)"No parameters to optimize", (Object[])new Object[0]);
            iSequentialOptimizationCompleteListener.onFinish(false, this.strategy, null, null);
            return false;
        }
        this.totalCount = 0;
        int n = 0;
        this.step = 0;
        SequentialOptimizationResults sequentialOptimizationResults = new SequentialOptimizationResults(this.settings.paramTypes, this.settings.symmetry, false);
        if (bl) {
            object3 = null;
            try {
                object3 = (String)this.backtestSettings.get("StrategyNote");
            }
            catch (Exception exception) {
                // empty catch block
            }
            object2 = new BacktestRunner(new BacktestSettings(this.backtestSettings), this.stopPauseEngine, null, false, this.lastEventListener, this.lastSettingsXml);
            BacktestResult backtestResult = ((BacktestRunner)object2).execute();
            if (backtestResult != null && (object = backtestResult.getResult()) != null) {
                ((ResultsGroup)object).specialValues().set(SpecialValues.Note, object3);
                ((ResultsGroup)object).specialValues().setString("OptimizationParameters", this.getOptimizationParameters(-1, 0.0));
                ((ResultsGroup)object).setLastSettings(this.lastSettingsXML);
                if (this.newResultListener != null) {
                    ((ResultsGroup)object).setName(this.strategyName);
                    this.newResultListener.newResult((ResultsGroup)object);
                }
            }
        }
        object3 = null;
        object2 = this.strategy.clone();
        for (int i = 0; i < this.variablesToOptimize.size(); ++i) {
            object = this.variablesToOptimize.get(i);
            FitnessData fitnessData = this.optimizeParameter(this.strategyName, (StrategyBase)object2, (Variable)object, this.optimizationParams.get(i), this.backtestSettings, gridJob, bl2);
            double d = fitnessData.analyze(this.settings.stableAreaCount, this.settings.stabilityRangePct);
            sequentialOptimizationResults.add(fitnessData);
            if (d != -1.7976931348623157E308) {
                ((Variable)object).setValue(d);
                this.parameterValues.set(this.totalCount, d);
                object3 = this.lastResults.get(d);
                Variables variables = ((StrategyBase)object2).variables();
                ((StrategyBase)object2).variables().setValue(((Variable)object).getName(), d);
            } else {
                ++n;
            }
            ++this.totalCount;
            this.lastResults.clear();
        }
        if (n <= (int)(0.01 * (double)this.totalCount * (double)(100 - this.settings.pctToPass))) {
            if (this.settings.applyToStrategy) {
                this.strategy.transformToNumbers();
                sequentialOptimizationResults.setApplyToStrategy(true);
            }
            sequentialOptimizationResults.setPassed(true);
            if (object3 != null) {
                object3 = ((ResultsGroup)object3).clone();
                ((ResultsGroup)object3).specialValues().setString(SpecialValues.FiltersResultFailedReason, SpecialValues.FiltersResultPassed);
                iSequentialOptimizationCompleteListener.onFinish(true, this.strategy, sequentialOptimizationResults, (ResultsGroup)object3);
            }
            return true;
        }
        sequentialOptimizationResults.setPassed(false);
        this.dismissalMessage = L.t((String)"Too many unstable parameters - %d of %d (treshold %d%%)", (Object[])new Object[]{n, this.totalCount, this.settings.pctToPass});
        iSequentialOptimizationCompleteListener.onFinish(false, this.strategy, sequentialOptimizationResults, null);
        return false;
    }

    private boolean shouldOptimizeParameter(byte by, String string) {
        return (by == 1 || by == 4) && !string.startsWith("Magic");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private FitnessData optimizeParameter(String string, StrategyBase strategyBase, Variable variable, Parameter parameter, SettingsMap settingsMap, GridJob gridJob, boolean bl) throws Exception {
        this.stopPauseEngine.checkPaused();
        this.stopPauseEngine.printToLog(L.t((String)"Sequential optimization: %s - Optimizing parameter %s...", (Object[])new Object[]{string, variable.getName()}));
        ArrayList<SequentialOptimizationJob> arrayList = this.createJobs(string, strategyBase, variable, parameter, settingsMap, gridJob);
        final FitnessData fitnessData = new FitnessData(variable, arrayList.size());
        if (bl) {
            for (int i = 0; i < arrayList.size(); ++i) {
                SequentialOptimizationJob sequentialOptimizationJob = arrayList.get(i);
                this.stopPauseEngine.checkPaused();
                if (this.stopPauseEngine.isStopped()) {
                    return fitnessData;
                }
                JobDetails jobDetails = new JobDetails(sequentialOptimizationJob.getJobId());
                BacktestResult backtestResult = null;
                try {
                    long l = System.currentTimeMillis();
                    backtestResult = sequentialOptimizationJob.call();
                    long l2 = System.currentTimeMillis() - l;
                    jobDetails.setDuration(l2);
                    this.processResult(backtestResult, sequentialOptimizationJob.getJobId(), fitnessData);
                    continue;
                }
                catch (TradingException tradingException) {
                    Log.error("Trading exception during optimization", (Throwable)tradingException);
                    continue;
                }
                catch (Throwable throwable) {
                    jobDetails.setException(SQUtils.getStackTrace((Throwable)throwable));
                    Log.error("Error while running sequential optimization job #{}", (Object)i, (Object)throwable);
                    continue;
                }
                finally {
                    if (sequentialOptimizationJob != null) {
                        sequentialOptimizationJob.destroy();
                    }
                }
            }
        } else {
            this.jobGroupID = UUID.randomUUID().toString();
            final GridClient gridClient = SQGrid.getGridClient();
            gridClient.executeOnGrid(this.jobGroupID, arrayList);
            gridClient.registerMessageListener(this.jobGroupID, new IGridMessageListener(){
                final /* synthetic */ SequentialOptimizationEngine this$0;
                {
                    this.this$0 = sequentialOptimizationEngine;
                }

                public void messageReceived(GridMessage gridMessage) {
                    try {
                        if (SQProject.isMemoryProtectionUsed()) {
                            MemoryUsageChecker.checkAvailableMemory();
                        }
                        if (gridMessage.getMessageID() == 1) {
                            BacktestResult backtestResult = (BacktestResult)gridMessage.getData();
                            this.this$0.processResult(backtestResult, gridMessage.getJobDetails().getJobID(), fitnessData);
                            String string = gridMessage.getJobDetails().getException();
                            if (string != null && !string.isEmpty()) {
                                Log.error("Job exception: " + string);
                            }
                        }
                    }
                    catch (OutOfMemoryError outOfMemoryError) {
                        gridClient.stop(this.this$0.jobGroupID);
                    }
                }
            });
            gridClient.waitForFinish((Object)this, null, null, this.jobGroupID);
        }
        return fitnessData;
    }

    private void processResult(BacktestResult backtestResult, String string, FitnessData fitnessData) {
        ResultsGroup resultsGroup = backtestResult.getResult();
        try {
            String[] stringArray = this.getJobIDData(string);
            int n = Integer.parseInt(stringArray[0]);
            double d = Double.parseDouble(stringArray[1]);
            if (resultsGroup != null) {
                try {
                    fitnessData.set(n, d, resultsGroup.getFitness());
                    resultsGroup.setLastSettings(this.lastSettingsXML);
                    if (this.newResultListener != null) {
                        resultsGroup.setName(this.strategyName + " - Opt. " + this.totalCount + "." + n);
                        resultsGroup.specialValues().setString("OptimizationParameters", this.getOptimizationParameters(this.totalCount, d));
                        this.newResultListener.newResult(resultsGroup);
                    }
                    if (this.stepsListener != null) {
                        this.stepsListener.step(++this.step);
                    }
                    this.lastResults.put(d, resultsGroup);
                }
                catch (Exception exception) {
                    Log.error("Sequential Optimization error", (Throwable)exception);
                }
            } else {
                Log.debug("Sequential Optimization backtest result is null. DismissalMessage: " + backtestResult.getDismissalMessage());
                fitnessData.set(n, d, 0.0);
            }
        }
        catch (Exception exception) {
            Log.error("Unable to get job details from job id", (Throwable)exception);
        }
    }

    private ArrayList<SequentialOptimizationJob> createJobs(String string, StrategyBase strategyBase, Variable variable, Parameter parameter, SettingsMap settingsMap, GridJob gridJob) throws Exception {
        ArrayList<SequentialOptimizationJob> arrayList = new ArrayList<SequentialOptimizationJob>();
        try {
            double[] dArray = this.getCombinations(variable, parameter, variable.getInternalType() == 1);
            for (int i = 0; i < dArray.length; ++i) {
                double d = dArray[i];
                Map<String, Serializable> map = this.updateBacktestSettings(settingsMap, string, strategyBase, variable, d);
                String string2 = this.getJobID(string, variable.getName(), i, d);
                SequentialOptimizationJob sequentialOptimizationJob = new SequentialOptimizationJob(string2, map, this.stopPauseEngine, this.lastEventListener, string, variable.getName(), d, this.lastSettingsXml);
                if (gridJob != null) {
                    sequentialOptimizationJob.setPriority(gridJob.getPriority() + 1);
                }
                arrayList.add(sequentialOptimizationJob);
            }
        }
        catch (Exception exception) {
            this.stopPauseEngine.printToLog(string + ": " + L.t((String)"Sequential Optimization job preparation error", (Object[])new Object[0]) + " - " + exception.getMessage());
            Log.error("Error while preparing Sequential Optimization jobs for strategy" + string, (Throwable)exception);
            throw exception;
        }
        return arrayList;
    }

    private String getJobID(String string, String string2, int n, double d) {
        return string + "_SequentialOpt." + string2 + "_" + n + "/" + d;
    }

    private String[] getJobIDData(String string) throws Exception {
        try {
            int n = string.lastIndexOf("_");
            String string2 = string.substring(n + 1);
            return string2.split("/");
        }
        catch (Exception exception) {
            throw new Exception("Unable to parse data from jobID", exception);
        }
    }

    private String getOptimizationParameters(int n, double d) {
        String string = "";
        for (int i = 0; i < this.parameterNames.size(); ++i) {
            string = string + "," + this.parameterNames.get(i) + "=" + (i == n ? d : this.parameterValues.get(i));
        }
        return string.substring(1);
    }

    private double[] getCombinations(Variable variable, Parameter parameter, boolean bl) {
        double d;
        int n;
        double d2 = variable.getValueAsDouble();
        double d3 = variable.getParamType() != null && "ParamTypePeriod".equals(variable.getParamType()) ? 2.0 : 0.0;
        boolean bl2 = parameter != null;
        double d4 = bl2 ? parameter.start : (1.0 - 0.01 * (double)this.settings.distributionDown) * d2;
        d4 = bl ? (double)SQUtils.round((double)d4).intValue() : d4;
        double d5 = bl2 ? parameter.stop : (1.0 + 0.01 * (double)this.settings.distributionUp) * d2;
        d5 = bl ? (double)SQUtils.round((double)d5).intValue() : d5;
        double d6 = bl2 ? parameter.step : (1.0 * d5 - d4) / (double)(this.settings.steps - 1);
        d6 = bl ? Math.max(1.0, d6) : d6;
        int n2 = this.getStepDecimals(d6);
        if (d6 == 0.0) {
            d6 = 1.0;
        }
        ArrayList<Double> arrayList = new ArrayList<Double>();
        if (bl2) {
            this.settings.steps = 1000000;
        }
        for (n = 0; n < this.settings.steps; ++n) {
            d = d4 + d6 * (double)n;
            d = Math.max(bl ? (double)((int)d) : SQUtils.round((double)d, (int)n2), d3);
            if (!arrayList.contains(d)) {
                arrayList.add(d);
            }
            if (d >= d5) break;
        }
        if (!bl2 && arrayList.size() < this.settings.steps) {
            int n3 = n = d4 <= d3 ? 1 : 0;
            while (arrayList.size() < this.settings.steps) {
                if (n == 0) {
                    d = Math.max(d4 - d6, d3);
                    double d7 = d = bl ? (double)((int)d) : SQUtils.round((double)d, (int)n2);
                    if (!arrayList.contains(d)) {
                        arrayList.add(0, d);
                    }
                    d4 = d;
                    n = d <= d3 ? 1 : 0;
                }
                d = d5 + d6;
                d5 = d = bl ? (double)((int)d) : SQUtils.round((double)d, (int)n2);
                if (arrayList.contains(d)) continue;
                arrayList.add(d);
            }
        }
        double[] dArray = new double[arrayList.size()];
        for (int i = 0; i < arrayList.size(); ++i) {
            dArray[i] = (Double)arrayList.get(i);
        }
        return dArray;
    }

    protected Map<String, Serializable> updateBacktestSettings(SettingsMap settingsMap, String string, StrategyBase strategyBase, Variable variable, double d) throws Exception {
        StrategyBase strategyBase2 = strategyBase.clone();
        this.copyModifiedVariables(strategyBase, strategyBase2);
        Variables variables = strategyBase2.variables();
        variables.get(variable.getName()).setValue(variable.getInternalType() == 1 ? (double)((int)d) : d);
        strategyBase2.transformToNumbers();
        settingsMap.set("StrategyObject", (Object)strategyBase2);
        settingsMap.set("StrategyXml", (Object)strategyBase2.getStrategyXml());
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        String[] stringArray = settingsMap.getAllKeys();
        for (int i = 0; i < stringArray.length; ++i) {
            if (stringArray[i].equals("TradingOptions")) {
                TradingOptions tradingOptions = new TradingOptions();
                tradingOptions.addAll(0, (ArrayList)settingsMap.get(stringArray[i]));
                hashMap.put("TradingOptions", tradingOptions.getClone());
                continue;
            }
            hashMap.put(stringArray[i], (Serializable)settingsMap.get(stringArray[i]));
        }
        return hashMap;
    }

    private void copyModifiedVariables(StrategyBase strategyBase, StrategyBase strategyBase2) {
        Variables variables = strategyBase.variables();
        Variables variables2 = strategyBase2.variables();
        for (Variable variable : variables) {
            Variable variable2 = variables2.get(variable.getName());
            if (variable2 == null || variable.getInternalType() != 1 && variable.getInternalType() != 4) continue;
            double d = variable.getValueAsDouble();
            variable2.setValue(variable.getInternalType() == 1 ? (double)((int)d) : d);
        }
    }

    public String getDismissalMessage() {
        return this.dismissalMessage;
    }

    public void setNewResultListener(INewResultListener iNewResultListener) {
        this.newResultListener = iNewResultListener;
    }

    public void setLogListener(IEngineLogListener iEngineLogListener) {
        this.engineLogListener = iEngineLogListener;
    }

    public void setStepsListener(IStepsListener iStepsListener) {
        this.stepsListener = iStepsListener;
    }

    public int getTotalStepsCount() {
        int n = 0;
        for (int i = 0; i < this.variablesToOptimize.size(); ++i) {
            Variable variable = this.variablesToOptimize.get(i);
            Parameter parameter = this.optimizationParams.get(i);
            double[] dArray = this.getCombinations(variable, parameter, variable.getInternalType() == 1);
            n += dArray.length;
        }
        return n;
    }

    public int getStepDecimals(double d) {
        if (d == 0.0) {
            return 0;
        }
        d = Math.abs(d);
        int n = 0;
        while (d < 1.0) {
            d *= 10.0;
            ++n;
        }
        return n;
    }
}

