/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.backtestrunner;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.correlation.FitPortfolio;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;

public class BacktestSettings
implements ISQCloneable {
    public double initialCapital;
    public MoneyManagementMethod moneyManagementMethod;
    public boolean moneyManagementMethodUseFromStrategy;
    public RiskManagementMethod riskManagementMethod;
    public IFitnessFunction fitnessFunction;
    public ArrayList<Condition> rankingConditions;
    public ArrayList<Condition> initialGenerationConditions;
    public TradingOptions tradingOptions;
    public ChartSetups chartSetups;
    public OutOfSample outOfSample;
    public boolean useCrossChecks;
    public ArrayList<ICrossCheck> crossChecks;
    public boolean evaluateAllCrossChecks = false;
    public boolean forceRunCrossChecks = false;
    public double slippage;
    public double minDistance;
    public CommissionsMethod commission;
    public SwapMethod swap;
    public String strategyName;
    public Element elStrategy;
    public Element lastSettings;
    public int dismissBadStrategies = 0;
    public StrategyBase strategyObject;
    public String mainResultKey;
    public boolean deleteFailedStrategies = false;
    public boolean isRetester = false;
    public boolean singleThreadedOptimizations = true;
    public List<ResultsGroup> mergedStrategies = null;
    public long dateGenerated;
    public boolean warningsBadStrategies = false;
    public ATM atm;
    public FitPortfolio fitPortfolio;
    public boolean isAlgoWizard = false;
    public boolean removeEndOfTestOrders = false;
    public String userID = null;
    public String groupSymbols = null;
    public String brokerSymbols = null;

    public BacktestSettings() {
    }

    public BacktestSettings(Map<String, Serializable> map) throws Exception {
        this.strategyName = (String)((Object)map.get("StrategyName"));
        this.mainResultKey = (String)((Object)map.get("MainResultKey"));
        this.elStrategy = (Element)map.get("StrategyXml");
        this.lastSettings = (Element)map.get("StrategyLastSettings");
        this.moneyManagementMethod = (MoneyManagementMethod)map.get("MoneyManagement.Method");
        if (this.moneyManagementMethod != null) {
            this.moneyManagementMethod = this.moneyManagementMethod.getClone();
        }
        this.moneyManagementMethodUseFromStrategy = SettingsMap.getBool((Object)map.get("MoneyManagement.UseFromStrategy"), (boolean)false);
        this.riskManagementMethod = (RiskManagementMethod)map.get("RiskManagement");
        if (this.riskManagementMethod != null) {
            this.riskManagementMethod = this.riskManagementMethod.getClone();
        }
        this.fitnessFunction = (IFitnessFunction)map.get("FitnessFunction");
        this.tradingOptions = (TradingOptions)map.get("TradingOptions");
        this.atm = (ATM)map.get("ATM");
        this.initialCapital = (Double)map.get("MoneyManagement.InitialCapital");
        this.outOfSample = (OutOfSample)map.get("OutOfSample");
        this.chartSetups = (ChartSetups)map.get("ChartSetups");
        this.useCrossChecks = SettingsMap.getBool((Object)map.get("UseRobustnessTests"), (boolean)false);
        this.crossChecks = (ArrayList)map.get("CrossChecks");
        this.slippage = SettingsMap.getDouble((Object)map.get("Slippage"), (double)0.0);
        this.minDistance = SettingsMap.getDouble((Object)map.get("MinDistance"), (double)0.0);
        this.commission = (CommissionsMethod)map.get("Commission");
        this.swap = (SwapMethod)map.get("Swap");
        this.rankingConditions = (ArrayList)map.get("Conditions");
        this.dismissBadStrategies = SettingsMap.getInt((Object)map.get("DismissBadStrategies"), (int)0);
        this.warningsBadStrategies = SettingsMap.getBool((Object)map.get("StrategyDismissWarnings"), (boolean)false);
        this.strategyObject = (StrategyBase)map.get("StrategyObject");
        this.evaluateAllCrossChecks = SettingsMap.getBool((Object)map.get("CrossChecks.EvaluateAll"), (boolean)false);
        this.deleteFailedStrategies = SettingsMap.getBool((Object)map.get("DeleteFailedStrategies"), (boolean)false);
        this.forceRunCrossChecks = SettingsMap.getBool((Object)map.get("ForceRunCrossChecks"), (boolean)false);
        this.isRetester = SettingsMap.getBool((Object)map.get("IsRetester"), (boolean)false);
        this.singleThreadedOptimizations = SettingsMap.getBool((Object)map.get("SingleThreadedOptimizations"), (boolean)true);
        this.mergedStrategies = (List)((Object)map.get("PortfolioMergedStrategies"));
        this.dateGenerated = SettingsMap.getLong((Object)map.get("DateGenerated"), (long)-1L);
        this.fitPortfolio = (FitPortfolio)map.get("FitPortfolio");
        this.isAlgoWizard = SettingsMap.getBool((Object)map.get("IsAlgoWizard"), (boolean)false);
        this.userID = (String)((Object)map.get("UserID"));
        this.brokerSymbols = (String)((Object)map.get("BrokerSymbols"));
    }

    public BacktestSettings(SettingsMap settingsMap) throws Exception {
        this.strategyName = (String)settingsMap.get("StrategyName");
        this.mainResultKey = (String)settingsMap.get("MainResultKey");
        this.elStrategy = (Element)settingsMap.get("StrategyXml");
        this.lastSettings = (Element)settingsMap.get("StrategyLastSettings");
        this.strategyObject = (StrategyBase)settingsMap.get("StrategyObject");
        this.moneyManagementMethod = (MoneyManagementMethod)settingsMap.get("MoneyManagement.Method");
        if (this.moneyManagementMethod != null) {
            this.moneyManagementMethod = this.moneyManagementMethod.getClone();
        }
        this.moneyManagementMethodUseFromStrategy = SettingsMap.getBool((Object)settingsMap.get("MoneyManagement.UseFromStrategy"), (boolean)false);
        this.riskManagementMethod = (RiskManagementMethod)settingsMap.get("RiskManagement");
        if (this.riskManagementMethod != null) {
            this.riskManagementMethod = this.riskManagementMethod.getClone();
        }
        this.fitnessFunction = (IFitnessFunction)settingsMap.get("FitnessFunction");
        this.tradingOptions = (TradingOptions)settingsMap.get("TradingOptions");
        this.atm = (ATM)settingsMap.get("ATM");
        this.initialCapital = (Double)settingsMap.get("MoneyManagement.InitialCapital");
        this.outOfSample = (OutOfSample)settingsMap.get("OutOfSample");
        if (!settingsMap.containsKey("ChartSetups")) {
            throw new Exception(L.t((String)"Settings don't have ChartSetups defined", (Object[])new Object[0]));
        }
        this.chartSetups = (ChartSetups)settingsMap.get("ChartSetups");
        this.useCrossChecks = (Boolean)settingsMap.get("UseRobustnessTests", (Object)false);
        this.crossChecks = (ArrayList)settingsMap.get("CrossChecks");
        this.slippage = (Double)settingsMap.get("Slippage");
        this.minDistance = (Double)settingsMap.get("MinDistance");
        this.commission = (CommissionsMethod)settingsMap.get("Commission");
        this.swap = (SwapMethod)settingsMap.get("Swap");
        this.rankingConditions = (ArrayList)settingsMap.get("Conditions", null);
        this.dismissBadStrategies = (Integer)settingsMap.get("DismissBadStrategies", (Object)0);
        this.warningsBadStrategies = SettingsMap.getBool((Object)settingsMap.get("StrategyDismissWarnings"), (boolean)false);
        this.evaluateAllCrossChecks = SettingsMap.getBool((Object)settingsMap.get("CrossChecks.EvaluateAll"), (boolean)false);
        this.deleteFailedStrategies = SettingsMap.getBool((Object)settingsMap.get("DeleteFailedStrategies"), (boolean)false);
        this.forceRunCrossChecks = SettingsMap.getBool((Object)settingsMap.get("ForceRunCrossChecks"), (boolean)false);
        this.isRetester = SettingsMap.getBool((Object)settingsMap.get("IsRetester"), (boolean)false);
        this.singleThreadedOptimizations = SettingsMap.getBool((Object)settingsMap.get("SingleThreadedOptimizations"), (boolean)true);
        this.mergedStrategies = (List)settingsMap.get("PortfolioMergedStrategies");
        this.dateGenerated = settingsMap.getLong("DateGenerated", -1L);
        this.fitPortfolio = (FitPortfolio)settingsMap.get("FitPortfolio");
        this.isAlgoWizard = SettingsMap.getBool((Object)settingsMap.get("IsAlgoWizard"), (boolean)false);
        this.userID = (String)settingsMap.get("UserID");
        this.brokerSymbols = (String)settingsMap.get("BrokerSymbols");
    }

    public BacktestSettings getClone() throws Exception {
        BacktestSettings backtestSettings = new BacktestSettings();
        backtestSettings.initialCapital = this.initialCapital;
        backtestSettings.moneyManagementMethod = this.moneyManagementMethod != null ? this.moneyManagementMethod.getClone() : null;
        backtestSettings.moneyManagementMethodUseFromStrategy = this.moneyManagementMethodUseFromStrategy;
        backtestSettings.riskManagementMethod = this.riskManagementMethod != null ? this.riskManagementMethod.getClone() : null;
        backtestSettings.fitnessFunction = this.fitnessFunction;
        backtestSettings.tradingOptions = this.tradingOptions != null ? this.tradingOptions.getClone() : null;
        backtestSettings.atm = this.atm != null ? this.atm.getClone() : null;
        backtestSettings.rankingConditions = this.cloneConditions(this.rankingConditions);
        backtestSettings.initialGenerationConditions = this.cloneConditions(this.initialGenerationConditions);
        backtestSettings.dismissBadStrategies = this.dismissBadStrategies;
        backtestSettings.warningsBadStrategies = this.warningsBadStrategies;
        backtestSettings.outOfSample = this.outOfSample;
        backtestSettings.chartSetups = this.chartSetups;
        backtestSettings.useCrossChecks = this.useCrossChecks;
        if (this.useCrossChecks) {
            backtestSettings.crossChecks = ProjectConfigHelper.cloneCrossChecks(this.crossChecks);
        }
        backtestSettings.slippage = this.slippage;
        backtestSettings.minDistance = this.minDistance;
        backtestSettings.commission = this.commission;
        backtestSettings.swap = this.swap;
        backtestSettings.elStrategy = this.elStrategy;
        backtestSettings.lastSettings = this.lastSettings != null ? this.lastSettings.clone() : null;
        backtestSettings.strategyName = this.strategyName;
        backtestSettings.mainResultKey = this.mainResultKey;
        backtestSettings.isRetester = this.isRetester;
        backtestSettings.singleThreadedOptimizations = this.singleThreadedOptimizations;
        backtestSettings.mergedStrategies = this.mergedStrategies;
        backtestSettings.dateGenerated = this.dateGenerated;
        backtestSettings.fitPortfolio = this.fitPortfolio != null ? this.fitPortfolio.getClone() : null;
        backtestSettings.isAlgoWizard = this.isAlgoWizard;
        backtestSettings.removeEndOfTestOrders = this.removeEndOfTestOrders;
        backtestSettings.userID = this.userID;
        backtestSettings.groupSymbols = this.groupSymbols;
        backtestSettings.brokerSymbols = this.brokerSymbols;
        return backtestSettings;
    }

    private ArrayList<Condition> cloneConditions(ArrayList<Condition> arrayList) throws Exception {
        if (arrayList == null) {
            return null;
        }
        ArrayList<Condition> arrayList2 = new ArrayList<Condition>();
        for (Condition condition : arrayList) {
            arrayList2.add(condition.getClone());
        }
        return arrayList2;
    }

    public SettingsMap getSettingsMap(ChartSetup chartSetup) throws Exception {
        SettingsMap settingsMap = new SettingsMap();
        settingsMap.set("BacktestChart", (Object)chartSetup);
        settingsMap.set("MoneyManagement.InitialCapital", (Object)this.initialCapital);
        settingsMap.set("OutOfSample", (Object)this.outOfSample);
        settingsMap.set("MoneyManagement.Method", (Object)this.moneyManagementMethod);
        settingsMap.set("MoneyManagement.UseFromStrategy", (Object)this.moneyManagementMethodUseFromStrategy);
        settingsMap.set("RiskManagement", (Object)this.riskManagementMethod);
        if (this.strategyObject == null) {
            settingsMap.set("StrategyObject", (Object)StrategyBase.createXmlStrategy(this.elStrategy.clone(), this.strategyName));
        } else {
            settingsMap.set("StrategyObject", (Object)this.strategyObject);
        }
        settingsMap.set("Slippage", (Object)this.slippage);
        settingsMap.set("MinDistance", (Object)this.minDistance);
        settingsMap.set("Commission", (Object)this.commission);
        settingsMap.set("Swap", (Object)this.swap);
        settingsMap.set("StrategyName", (Object)this.strategyName);
        settingsMap.set("MainResultKey", (Object)this.mainResultKey);
        long l = chartSetup.getMainChart().getHistoryFrom() + (long)((double)(chartSetup.getMainChart().getHistoryTo() - chartSetup.getMainChart().getHistoryFrom()) * 0.4);
        settingsMap.set("StrategyCheckDate", (Object)l);
        settingsMap.set("DismissBadStrategies", (Object)this.dismissBadStrategies);
        settingsMap.set("StrategyDismissWarnings", (Object)this.warningsBadStrategies);
        settingsMap.set("IsRetester", (Object)this.isRetester);
        settingsMap.set("IsAlgoWizard", (Object)this.isAlgoWizard);
        settingsMap.set("UserID", (Object)this.userID);
        settingsMap.set("SingleThreadedOptimizations", (Object)this.singleThreadedOptimizations);
        if (this.tradingOptions != null) {
            settingsMap.set("TradingOptions", (Object)this.tradingOptions);
        }
        if (this.atm != null) {
            settingsMap.set("ATM", (Object)this.atm);
        }
        if (this.fitPortfolio != null) {
            settingsMap.set("FitPortfolio", (Object)this.fitPortfolio);
        }
        settingsMap.set("BrokerSymbols", (Object)this.brokerSymbols);
        return settingsMap;
    }
}

