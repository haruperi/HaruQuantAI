/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.backtest.TradingOptionsModifier;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.IStrategyModifier;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import java.io.Serializable;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationTestJob
extends GridJob<BacktestResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationTestJob");
    private double initialCapital;
    private ChartSetups chartSetups;
    private Element elStrategy;
    private Element lastSettings;
    private MoneyManagementMethod moneyManagementMethod;
    private RiskManagementMethod riskManagementMethod;
    private int testPrecision;
    private IStrategyModifier strategyModifier;
    private String optimizationParams;
    private String resultGroupName;
    private short[] optimizationParamIndexes;
    private IFitnessFunction fitnessFunction;
    private TradingOptions tradingOptions;
    private double slippage;
    private double minDistance;
    private CommissionsMethod commission;
    private SwapMethod swap;
    private ATM atm;
    private String mainResultKey;
    private StopPauseEngine parentStopPauseEngine;
    private final int periodType;

    public OptimizationTestJob(String string, Map<String, Serializable> map, StopPauseEngine stopPauseEngine, int n) {
        super(string, 1, map);
        this.initialCapital = (Double)map.get("MoneyManagement.InitialCapital");
        this.testPrecision = (Integer)map.get("TestPrecision");
        this.chartSetups = (ChartSetups)map.get("ChartSetups");
        this.slippage = (Double)map.get("Slippage");
        this.minDistance = (Double)map.get("MinDistance");
        this.commission = (CommissionsMethod)map.get("Commission");
        this.swap = (SwapMethod)map.get("Swap");
        this.elStrategy = (Element)map.get("StrategyXml");
        this.lastSettings = (Element)map.get("StrategyLastSettings");
        this.strategyModifier = (IStrategyModifier)map.get("StrategyModifier");
        this.optimizationParams = (String)((Object)map.get("OptimizationParams"));
        this.optimizationParamIndexes = (short[])map.get("OptimizationParamIndexes");
        this.moneyManagementMethod = (MoneyManagementMethod)map.get("MoneyManagement.Method");
        this.riskManagementMethod = (RiskManagementMethod)map.get("RiskManagement");
        this.resultGroupName = (String)((Object)map.get("ResultGroupName"));
        this.mainResultKey = (String)((Object)map.get("MainResultKey"));
        this.fitnessFunction = (IFitnessFunction)map.get("FitnessFunction");
        this.tradingOptions = (TradingOptions)map.get("TradingOptions");
        this.atm = (ATM)map.get("ATM");
        this.lastSettings = this.lastSettings != null ? this.lastSettings.clone() : null;
        this.periodType = n;
        try {
            TradingOptionsModifier.modifyTradingOptions(this.tradingOptions, this.elStrategy, this.lastSettings);
        }
        catch (Exception exception) {
            Log.error("Cannot modify trading options", (Throwable)exception);
        }
        this.parentStopPauseEngine = stopPauseEngine;
    }

    public BacktestResult call() throws Exception {
        DurationStats durationStats = new DurationStats();
        try {
            long l = System.currentTimeMillis();
            ResultsGroup resultsGroup = this.backtestStrategy(this.elStrategy, (ChartSetup)this.chartSetups.get(0));
            durationStats.addDuration(DurationStats.MainTest, System.currentTimeMillis() - l);
            resultsGroup.setName(this.resultGroupName);
            return new BacktestResult(resultsGroup, durationStats);
        }
        catch (TradingException tradingException) {
            if (tradingException instanceof BadStrategyException) {
                BadStrategyException badStrategyException = (BadStrategyException)tradingException;
                int n = badStrategyException.getReason();
                if (n == 32) {
                    return new BacktestResult(L.t((String)"dismissed, too many open trades", (Object[])new Object[]{n}), n, durationStats);
                }
                return new BacktestResult(L.t((String)"dismissed", (Object[])new Object[0]) + String.format(" (%d)", n), n, durationStats);
            }
            return new BacktestResult(L.t((String)"Exception in backtest", (Object[])new Object[0]) + ": " + tradingException.getMessage(), 10001, durationStats);
        }
    }

    private ResultsGroup backtestStrategy(Element element, ChartSetup chartSetup) throws Exception {
        ResultsGroup resultsGroup;
        String string = null;
        if (this.lastSettings != null) {
            string = XMLUtil.elementToString((Element)this.lastSettings);
        }
        if (chartSetup.getBacktestEngine() == 1316847364 || chartSetup.getBacktestEngine() == -1816889229) {
            String string2;
            StockpickerBacktestEngine stockpickerBacktestEngine = new StockpickerBacktestEngine();
            stockpickerBacktestEngine.setStopPauseEngine(this.parentStopPauseEngine);
            if (chartSetup.getBacktestEngine() == -1816889229) {
                string2 = chartSetup.getMainChart().getSymbol();
                String string3 = StockpickerBacktestEngine.createBasketName(string2);
                chartSetup = chartSetup.getClone(string3);
            }
            string2 = this.getBacktestSettings(element, chartSetup);
            stockpickerBacktestEngine.addSetup((SettingsMap)string2);
            stockpickerBacktestEngine.addStrategyXml(element);
            stockpickerBacktestEngine.setLastSettings(string);
            resultsGroup = stockpickerBacktestEngine.runBacktest(this.resultGroupName);
        } else {
            BacktestEngine backtestEngine = new BacktestEngine(TraderSimulators.getSimulator(chartSetup));
            backtestEngine.setStopPauseEngine(this.parentStopPauseEngine);
            SettingsMap settingsMap = this.getBacktestSettings(element, chartSetup);
            backtestEngine.addSetup(settingsMap);
            boolean bl = this.periodType == 30;
            resultsGroup = backtestEngine.runBacktest(this.resultGroupName, this.mainResultKey, false, bl).getResults();
        }
        resultsGroup.specialValues().setString("OptimizationParameters", this.optimizationParams);
        resultsGroup.specialValues().set("OptimizationParametersArray", (Object)this.optimizationParamIndexes);
        if (string != null) {
            resultsGroup.setLastSettings(string);
        }
        int n = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
        this.computeFitness(resultsGroup);
        return resultsGroup;
    }

    private void computeFitness(ResultsGroup resultsGroup) throws Exception {
        this.computeFitness(resultsGroup, (byte)0, (byte)127);
        this.computeFitness(resultsGroup, (byte)0, (byte)10);
        this.computeFitness(resultsGroup, (byte)0, (byte)20);
    }

    private void computeFitness(ResultsGroup resultsGroup, byte by, byte by2) throws Exception {
        double d = this.fitnessFunction.computeFitness(resultsGroup, by, by2);
        d = this.periodType == 30 ? this.fitnessFunction.computeFitness(resultsGroup, by, by2, false) : this.fitnessFunction.computeFitness(resultsGroup, by, by2);
        resultsGroup.portfolio().setFitness(by2, d);
    }

    private SettingsMap getBacktestSettings(Element element, ChartSetup chartSetup) throws Exception {
        SettingsMap settingsMap = new SettingsMap();
        settingsMap.set("BacktestChart", (Object)chartSetup);
        settingsMap.set("Slippage", (Object)this.slippage);
        settingsMap.set("MinDistance", (Object)this.minDistance);
        settingsMap.set("Commission", (Object)this.commission);
        settingsMap.set("Swap", (Object)this.swap);
        settingsMap.set("MoneyManagement.InitialCapital", (Object)this.initialCapital);
        settingsMap.set("MoneyManagement.Method", (Object)this.moneyManagementMethod);
        settingsMap.set("RiskManagement", (Object)this.riskManagementMethod);
        settingsMap.set("StrategyObject", (Object)StrategyBase.createXmlStrategy(element));
        settingsMap.set("ResultGroupName", (Object)this.resultGroupName);
        settingsMap.set("TradingOptions", (Object)this.tradingOptions);
        settingsMap.set("ATM", (Object)this.atm);
        settingsMap.set("TestPrecision", (Object)this.testPrecision);
        return settingsMap;
    }

    public void messageReceived(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 4) {
            this.destroy();
        }
    }
}

