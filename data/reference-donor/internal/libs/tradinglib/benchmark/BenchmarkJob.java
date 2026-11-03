/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.SettingsMap
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.benchmark;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.simulator.impl.MetaTrader4Simulator;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BenchmarkJob
extends GridJob<ResultsGroup> {
    public static final Logger Log = LoggerFactory.getLogger((String)"BenchmarkJob");
    private double initialCapital;
    private OutOfSample outOfSample;
    private ChartSetups chartSetups;
    private ArrayList<TradingOption> tradingOptions;
    private Element elStrategy;
    private MoneyManagementMethod moneyManagementMethod;
    private RiskManagementMethod riskManagementMethod;
    private SettingsMap backtestSettings = null;

    public BenchmarkJob(String string, Map<String, Serializable> map) {
        super(string, 1, map);
        this.elStrategy = (Element)map.get("StrategyXml");
        this.moneyManagementMethod = (MoneyManagementMethod)map.get("MoneyManagement.Method");
        this.riskManagementMethod = (RiskManagementMethod)map.get("RiskManagement");
        this.tradingOptions = (ArrayList)map.get("TradingOptions");
        this.initialCapital = (Double)map.get("MoneyManagement.InitialCapital");
        this.outOfSample = (OutOfSample)map.get("OutOfSample");
        this.chartSetups = (ChartSetups)map.get("ChartSetups");
    }

    public ResultsGroup call() throws Exception {
        long l = System.currentTimeMillis();
        ResultsGroup resultsGroup = this.backtestStrategy(this.elStrategy, this.chartSetups.getMainSetup());
        int n = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
        long l2 = System.currentTimeMillis();
        return resultsGroup;
    }

    private ResultsGroup backtestStrategy(Element element, ChartSetup chartSetup) throws Exception {
        MetaTrader4Simulator metaTrader4Simulator = new MetaTrader4Simulator();
        metaTrader4Simulator.setTestPrecision(chartSetup.getTestPrecision());
        BacktestEngine backtestEngine = new BacktestEngine(metaTrader4Simulator);
        this.backtestSettings = this.getBacktestSettings(element, chartSetup);
        backtestEngine.addSetup(this.backtestSettings);
        ResultsGroup resultsGroup = backtestEngine.runBacktest().getResults();
        return resultsGroup;
    }

    private SettingsMap getBacktestSettings(Element element, ChartSetup chartSetup) throws Exception {
        SettingsMap settingsMap = new SettingsMap();
        settingsMap.set("ChartSetups", (Object)this.chartSetups);
        settingsMap.set("BacktestChart", (Object)chartSetup);
        settingsMap.set("MoneyManagement.InitialCapital", (Object)this.initialCapital);
        settingsMap.set("OutOfSample", (Object)this.outOfSample);
        settingsMap.set("MoneyManagement.Method", (Object)this.moneyManagementMethod);
        settingsMap.set("RiskManagement", (Object)this.riskManagementMethod);
        settingsMap.set("StrategyObject", (Object)StrategyBase.createXmlStrategy(element));
        for (TradingOption tradingOption : this.tradingOptions) {
            String string = tradingOption.getClass().getSimpleName();
            List<String> list = tradingOption.getParametersList();
            for (String string2 : list) {
                String string3 = list.size() > 1 || !string.equals(string2) ? String.format("%s.%s", string, string2) : string2;
                settingsMap.set(string3, tradingOption.getParameterValue(string2));
            }
        }
        return settingsMap;
    }

    public void messageReceived(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 4) {
            this.destroy();
        }
    }
}

