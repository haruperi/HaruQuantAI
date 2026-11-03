/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.backtest.TradingOptionsModifier;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.exception.StrategyStoppedException;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.IEngineLogListener;
import com.strategyquant.tradinglib.optimization.INewResultListener;
import com.strategyquant.tradinglib.optimization.IStepsListener;
import com.strategyquant.tradinglib.optimization.NotEnoughSpaceException;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.StrategyParamData;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.io.File;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationEngineBase {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationEngineBase");
    protected final String lastSettingsXml;
    protected SettingsMap settings;
    protected OptimizationSettings optimizationSettings;
    protected OptimizationParams parameters;
    protected String taskName;
    protected StopPauseEngine progressEngine;
    private int status = 0;
    protected IFitnessFunction fitnessFunction;
    private INewResultListener newResultListener = null;
    private IEngineLogListener engineLogListener = null;
    private IStepsListener stepsListener = null;
    public int generationNumber = 0;
    protected long totalDays;
    protected int actualStep;
    protected StatsComputer customStatsComputer = null;
    protected StatsComputer fitnessStatsComputer = null;
    protected String source;
    protected ILastEventListener lastEventListener;
    private final ReentrantLock lock = new ReentrantLock();

    public OptimizationEngineBase(String string, StopPauseEngine stopPauseEngine, String string2, ILastEventListener iLastEventListener, String string3) {
        this.taskName = string;
        this.progressEngine = stopPauseEngine;
        this.source = string2;
        this.lastEventListener = iLastEventListener;
        this.lastSettingsXml = string3;
    }

    public void initialize(SettingsMap settingsMap) throws Exception {
        this.settings = settingsMap;
        this.optimizationSettings = (OptimizationSettings)settingsMap.get("OptimizationSettings");
        if (this.optimizationSettings.optimizationType == 2) {
            this.optimizationSettings.optimizationType = 1;
        }
        this.parameters = this.optimizationSettings.parameters;
        this.fitnessFunction = (IFitnessFunction)settingsMap.get("FitnessFunction");
        if (!this.fitnessFunction.getClass().getSimpleName().equals("FitnessMethodStrategyResult")) {
            String string = "<Rankings type=\"never\">\r\n          <FitnessCriteria method=\"ComputeFromStrategyResult\">\r\n            <Settings>\r\n              <Ranking type=\"ReturnDDRatio\" />\r\n            </Settings>\r\n          </FitnessCriteria>\r\n          </Rankings>";
            Element element = XMLUtil.stringToElement((String)string);
            this.fitnessFunction = ProjectConfigHelper.getFitnessFunction(element);
        }
        this.actualStep = 0;
    }

    protected void initOptimization() {
        ChartSetups chartSetups = (ChartSetups)this.settings.get("ChartSetups");
        this.totalDays = SQTime.getDaysBetween((long)chartSetups.getMainSetup().getMainChart().getHistoryFrom(), (long)chartSetups.getMainSetup().getMainChart().getHistoryTo());
    }

    public void increaseStep() {
        this.increaseStep(1);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void increaseStep(int n) {
        OptimizationEngineBase optimizationEngineBase = this;
        synchronized (optimizationEngineBase) {
            this.actualStep += n;
            if (this.stepsListener != null) {
                this.stepsListener.step(this.actualStep);
            }
        }
    }

    protected short[] prepareIndexesArray(int n) {
        short[] sArray = new short[n];
        for (int i = 0; i < sArray.length; ++i) {
            sArray[i] = -1;
        }
        return sArray;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addResultToDatabank(ResultsGroup resultsGroup) throws Exception {
        block9: {
            boolean bl = this.lock.tryLock(20L, TimeUnit.SECONDS);
            if (bl) {
                try {
                    if (this.newResultListener == null) break block9;
                    try {
                        Object object;
                        Element element = resultsGroup.getStrategyXml();
                        if (element != null) {
                            object = StrategyBase.createXmlStrategy(element);
                            ((StrategyBase)object).transformToNumbers();
                            resultsGroup.portfolio().addStrategyXml(((StrategyBase)object).getStrategyXml());
                        }
                        if (this.settings.containsKey("LogicalVein") && (object = this.settings.getString("LogicalVein")) != null && !((String)object).isEmpty()) {
                            resultsGroup.portfolio().set("LogicalVein", object);
                        }
                    }
                    catch (Exception exception) {
                        if (!exception.getMessage().contains("ResultsMap is empty, this ResultsGroup was destroyed before!")) {
                            throw exception;
                        }
                    }
                }
                finally {
                    this.lock.unlock();
                }
            }
        }
        this.newResultListener.newResult(resultsGroup);
    }

    private void copyStatsFromFirstResultToPortfolio(ResultsGroup resultsGroup) throws Exception {
        String[] stringArray;
        String string = resultsGroup.getMainResultKey();
        Result result = resultsGroup.subResult(string);
        Result result2 = resultsGroup.portfolio();
        for (String string2 : stringArray = result.getAllKeys()) {
            if (result2.containsKey(string2)) continue;
            result2.set(string2, result.get(string2));
        }
    }

    protected MarketData getMarketData() {
        try {
            SettingsMap settingsMap = this.cloneBacktestSettings(0L, 0L);
            settingsMap.set("StrategyName", (Object)"StrToGetData");
            settingsMap.set("MainResultKey", (Object)"StrToGetData");
            settingsMap.set("ResultGroupName", (Object)"StrToGetData");
            StrategyBase strategyBase = (StrategyBase)this.settings.get("StrategyObject");
            settingsMap.set("StrategyObject", (Object)strategyBase);
            BacktestSettings backtestSettings = new BacktestSettings(settingsMap);
            ChartSetups chartSetups = (ChartSetups)this.settings.get("ChartSetups");
            ChartSetup chartSetup = chartSetups.getMainSetup();
            BacktestEngine backtestEngine = new BacktestEngine(TraderSimulators.getSimulator(chartSetup));
            backtestEngine.setSingleThreaded(true);
            backtestEngine.addSetup(backtestSettings.getSettingsMap(chartSetup));
            MarketData marketData = backtestEngine.getMarketData();
            return marketData;
        }
        catch (Exception exception) {
            exception.printStackTrace();
            return null;
        }
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
        TradingOptions tradingOptions = (TradingOptions)settingsMap.get("TradingOptions");
        Element element2 = (Element)this.settings.get("StrategyLastSettings");
        TradingOptionsModifier.modifyTradingOptions(tradingOptions, element, element2);
        boolean bl = this.optimizationSettings.periodType == 30;
        BacktestSettings backtestSettings = new BacktestSettings(settingsMap);
        backtestSettings.removeEndOfTestOrders = bl;
        BacktestRunner backtestRunner = new BacktestRunner(backtestSettings, this.progressEngine, null, false, this.lastEventListener, this.lastSettingsXml);
        BacktestResult backtestResult = backtestRunner.execute();
        ResultsGroup resultsGroup = backtestResult.getResult();
        if (resultsGroup == null) {
            if (backtestResult.getDismissalReason() == 10002) {
                throw new StrategyStoppedException("Stopped");
            }
            throw new Exception(L.t((String)"No results for backtest! Reason: %s", (Object[])new Object[]{backtestResult.getDismissalMessage()}));
        }
        resultsGroup.specialValues().setString("OptimizationParameters", string3);
        resultsGroup.specialValues().set("OptimizationParametersArray", (Object)sArray);
        if (element2 != null) {
            resultsGroup.setLastSettings(XMLUtil.elementToString((Element)element2));
        }
        double d = this.computeFitness(resultsGroup);
        resultsGroup.portfolio().setFitness((byte)127, d);
        return resultsGroup;
    }

    protected double computeFitness(ResultsGroup resultsGroup) throws Exception {
        return this.computeFitness(resultsGroup, (byte)0, (byte)10);
    }

    private double computeFitness(ResultsGroup resultsGroup, byte by, byte by2) throws Exception {
        double d = this.fitnessFunction.computeFitness(resultsGroup, by, by2);
        resultsGroup.portfolio().setFitness(by2, d);
        if (by == 0 && by2 == 127) {
            Log.debug("Fitness computed to: " + d);
        }
        return d;
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

    protected void checkEnoughDiskSize(int n, long l) throws NotEnoughSpaceException {
        int n2 = (int)((float)(n * 12) * 1.5f);
        long l2 = l * (long)n2;
        File file = new File(MainApp.getDataPath());
        long l3 = file.getUsableSpace();
        Log.debug("Free space : " + l3 / 1024L / 1024L + " MB");
        l3 = l3 / 1024L / 1024L;
        l2 = l2 / 1024L / 1024L;
        if (l2 > l3) {
            throw new NotEnoughSpaceException(2, "There is not enough space on disc to store simulation temporary files. Approximately " + l2 + " MB is required, while only " + l3 + " MB is available!\nPlease free some disc space or decrease number of tests.");
        }
    }

    public boolean isPaused() {
        return this.status == 2;
    }

    public boolean isStopped() {
        return this.status == 4;
    }

    public void setStatus(int n) {
        this.status = n;
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

    public void printLog(String string) {
        if (this.engineLogListener != null) {
            this.engineLogListener.processMessage(string);
        }
    }

    public int getGenerationNumber() {
        return this.generationNumber;
    }

    protected StopPauseEngine getStopPauseEngine() {
        return this.progressEngine;
    }
}

