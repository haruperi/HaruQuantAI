/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.benchmark;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.backtest.BacktestDataCache;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.robustnesstests.RobustnessTestMethod;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BenchmarkJob2
extends GridJob<ResultsGroup> {
    public static final Logger Log = LoggerFactory.getLogger((String)"BenchmarkJob");
    private int initialCapital;
    private OutOfSample outOfSample;
    private ChartSetups chartSetups;
    private String strategyName;
    private ArrayList<TradingOption> tradingOptions;
    private Element elStrategy;
    private MoneyManagementMethod moneyManagementMethod;
    private RiskManagementMethod riskManagementMethod;
    private IFitnessFunction fitnessFunction;
    private boolean useRobustnessTests;
    private ArrayList<RobustnessTestMethod> rtMethods;
    private int rtNumberOfSimulations;
    private boolean rtForEverySetup;
    private SettingsMap backtestSettings = null;
    private ObjectArrayList<VersatileData> bigArray;

    public BenchmarkJob2(String string, Map<String, Serializable> map) {
        super(string, 1, map);
        this.strategyName = (String)((Object)map.get("StrategyName"));
        this.elStrategy = (Element)map.get("StrategyXml");
        this.moneyManagementMethod = (MoneyManagementMethod)map.get("MoneyManagement.Method");
        this.riskManagementMethod = (RiskManagementMethod)map.get("RiskManagement");
        this.fitnessFunction = (IFitnessFunction)map.get("FitnessFunction");
        this.tradingOptions = (ArrayList)map.get("TradingOptions");
        this.initialCapital = (Integer)map.get("MoneyManagement.InitialCapital");
        this.outOfSample = (OutOfSample)map.get("OutOfSample");
        this.chartSetups = (ChartSetups)map.get("ChartSetups");
        this.useRobustnessTests = (Boolean)map.get("UseRobustnessTests");
        this.rtMethods = (ArrayList)map.get("RTMethods");
        this.rtNumberOfSimulations = (Integer)map.get("RTNumberOfSimulations");
        this.rtForEverySetup = (Boolean)map.get("RTForEverySetup");
        this.bigArray = (ObjectArrayList)map.get("BigArray");
    }

    public ResultsGroup call() throws Exception {
        long l = System.currentTimeMillis();
        BacktestEngine backtestEngine = new BacktestEngine(TraderSimulators.getSimulator(this.chartSetups.getMainSetup()));
        this.backtestSettings = this.getBacktestSettings(this.elStrategy, this.chartSetups.getMainSetup());
        backtestEngine.addSetup(this.backtestSettings);
        boolean bl = false;
        VersatileData versatileData = new VersatileData();
        BacktestDataCache backtestDataCache = BacktestDataCache.getInstance();
        ArrayList<ChartDef> arrayList = this.getAllBacktestChartDefs();
        throw new Exception(L.t((String)"Need to implement this below!", (Object[])new Object[0]));
    }

    public ArrayList<ChartDef> getAllBacktestChartDefs() throws Exception {
        ArrayList<ChartDef> arrayList = new ArrayList<ChartDef>();
        ArrayList<ChartDef> arrayList2 = this.chartSetups.getMainSetup().getCharts();
        for (int i = 0; i < arrayList2.size(); ++i) {
            ChartDef chartDef = arrayList2.get(i);
            arrayList.add(new ChartDef(chartDef));
        }
        return arrayList;
    }

    private SettingsMap getBacktestSettings(Element element, ChartSetup chartSetup) throws Exception {
        SettingsMap settingsMap = new SettingsMap();
        settingsMap.set("ChartSetups", (Object)this.chartSetups);
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

    public Integer call2() throws Exception {
        long l = System.currentTimeMillis();
        int n = 0;
        for (int i = 0; i < 90000; ++i) {
            for (int j = 0; j < 30000; ++j) {
                n += i + j;
            }
        }
        long l2 = System.currentTimeMillis();
        Log.info(String.format("CALL TOOK: %d ms", l2 - l));
        return n;
    }
}

