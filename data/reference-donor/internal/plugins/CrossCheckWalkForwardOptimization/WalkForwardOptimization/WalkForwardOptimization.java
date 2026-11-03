/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.Variables
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.OptimizationConst
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.OptimizationConst;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@PluginImplementation
public class WalkForwardOptimization
extends WalkForwardCrossCheckMethod {
    public static final Logger Log = LoggerFactory.getLogger((String)"WalkForwardOptimizationCrossCheck");
    private int distributionUp = 30;
    private int distributionDown = 30;
    private int maxSteps = 10;
    private ValuesMap paramTypesWFO = new ValuesMap();

    public WalkForwardOptimization() {
        super("WalkForwardOptimization_CrossCheck");
    }

    public String getName() {
        return NameWFOptimization;
    }

    public String getShortName() {
        return L.tsq((String)"WF optim.");
    }

    public String getDescription() {
        return L.tsq((String)"This cross check performs Walk-Forward Optimization of the strategy using the settings below.<br/>Be aware that WF optimization is very slow, it requires repeated backtests of the strategy in different time ranges and using different parameter values.");
    }

    public int getPreferredPosition() {
        return 270;
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        this.fixSettings(elSettings);
        Element elTaskSettings = elSettings.getParentElement().getParentElement();
        this.elRankings = elTaskSettings.getChild("Rankings");
        Element elCCSettings = elSettings.getChild("Settings");
        if (elCCSettings == null) {
            throw new Exception(L.t((String)"Missing Settings element in Crosscheck config", (Object[])new Object[0]));
        }
        Element elWalkForward = elCCSettings.getChild("WalkForward");
        if (elWalkForward == null) {
            throw new Exception(L.t((String)"Missing WalkForward element in Crosscheck config", (Object[])new Object[0]));
        }
        this.optimizationSettings.optimizationType = XMLUtil.getIntAttr((Element)elWalkForward, (String)"type", (int)1);
        this.optimizationSettings.periodType = XMLUtil.getIntAttr((Element)elWalkForward, (String)"period", (int)10);
        this.optimizationSettings.floating = XMLUtil.getIntAttr((Element)elWalkForward, (String)"optimization", (int)15) == 15;
        this.distributionUp = XMLUtil.getIntAttr((Element)elWalkForward, (String)"distributionUp", (int)30);
        this.distributionDown = XMLUtil.getIntAttr((Element)elWalkForward, (String)"distributionDown", (int)30);
        this.maxSteps = XMLUtil.getIntAttr((Element)elWalkForward, (String)"maxSteps", (int)10);
        Element elParam1 = elWalkForward.getChild("Param1");
        Element elParam2 = elWalkForward.getChild("Param2");
        this.optimizationSettings.param1Start = XMLUtil.getIntAttr((Element)elParam1, (String)"value", (int)20);
        this.optimizationSettings.param2Start = XMLUtil.getIntAttr((Element)elParam2, (String)"value", (int)10);
        this.optimizationSettings.maxOptimizationBacktests = XMLUtil.getNodeIntValue((Element)elCCSettings, (String)"MaxTests", (int)100);
        this.optimizationSettings.singleThreaded = true;
        Element whatToParametrizeElem = elCCSettings.getChild("WhatToParametrize");
        this.readWhatToParametrize(whatToParametrizeElem);
        this.paramTypesWFO = this.paramTypes.clone();
        Element elAcceptanceSettings = elSettings.getChild("AcceptanceSettings");
        if (elAcceptanceSettings == null) {
            throw new Exception(L.t((String)"Missing AcceptanceSettings element in Crosscheck config", (Object[])new Object[0]));
        }
        try {
            Element elConditions;
            this.optimizationSettings.elConditions = elConditions = XMLUtil.tryAddElement((Element)elAcceptanceSettings, (String)"Conditions");
            this.optimizationSettings.conditions = ProjectConfigHelper.getConditions((Element)elConditions);
            this.optimizationSettings.thresholdPct = XMLUtil.getIntAttr((Element)elConditions, (String)"thresholdPct", (int)10);
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Cannot read conditions of Crosscheck method '%s'", (Object[])new Object[]{this.getName()}), e);
        }
    }

    protected SettingsMap prepareSettings(String name, SettingsMap mainSettings, Element strategyXml, boolean singleThreaded) throws Exception {
        try {
            SettingsMap newSettings = this.cloneSettings(mainSettings);
            ChartSetups chartSetups = new ChartSetups();
            chartSetups.add((Object)((ChartSetup)newSettings.get("BacktestChart")));
            newSettings.set("ChartSetups", (Object)chartSetups);
            newSettings.set("TestPrecision", mainSettings.get("BacktestPrecision"));
            newSettings.set("StrategyXml", (Object)strategyXml);
            StrategyBase strategy = StrategyBase.createXmlStrategy((Element)strategyXml);
            strategy.transformToVariables(this.paramSymmetry, this.paramTypesWFO);
            Variables vars = strategy.variables();
            vars.sortByName();
            newSettings.set("StrategyObject", (Object)strategy);
            newSettings.set("StrategyName", (Object)name);
            this.optimizationSettings.parameters = this.initializeParams(strategy, this.distributionUp, this.distributionDown, this.maxSteps);
            this.optimizationSettings.optimizationMethod = 0;
            this.optimizationSettings.type = 2;
            this.optimizationSettings.singleThreaded = singleThreaded;
            newSettings.set("OptimizationSettings", (Object)this.optimizationSettings.clone());
            IFitnessFunction ff = ProjectConfigHelper.getFitnessFunction((Element)this.elRankings);
            newSettings.set("FitnessFunction", (Object)ff);
            newSettings.set("Slippage", mainSettings.get("Slippage"));
            newSettings.set("MinDistance", mainSettings.get("MinDistance"));
            newSettings.set("Commission", mainSettings.get("Commission"));
            newSettings.set("Swap", mainSettings.get("Swap"));
            return newSettings;
        }
        catch (Exception e) {
            Log.error(SQUtils.getStackTrace((Throwable)e));
            throw new Exception("Error while preparing settings - " + e.getMessage());
        }
    }

    public boolean runTest(ResultsGroup rg, int index, double globalATR, GridJob parentGridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        this.checkSpecialTrialLimitation();
        return super.runTest(rg, index, globalATR, parentGridJob, singleThreaded, lastEventListener, strategyName);
    }

    public ICrossCheck clone(SettingsMap settings) {
        WalkForwardOptimization crossCheck = new WalkForwardOptimization();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        crossCheck.elRankings = this.elRankings;
        crossCheck.optimizationSettings = this.optimizationSettings.clone();
        crossCheck.distributionUp = this.distributionUp;
        crossCheck.distributionDown = this.distributionDown;
        crossCheck.maxSteps = this.maxSteps;
        crossCheck.paramTypesWFO = this.paramTypes.clone();
        return crossCheck;
    }

    public ChartSetups getChartSetups(ChartSetup mainChartSetup) {
        return null;
    }

    public String printSettings(Element elMethod) throws Exception {
        if (elMethod == null) {
            throw new NullPointerException();
        }
        if (!XMLUtil.elementIs((Element)elMethod, (String)"use")) {
            return "Not used";
        }
        Element settingsEl = elMethod.getChild("Settings");
        Element elWalkForward = settingsEl.getChild("WalkForward");
        int periodType = XMLUtil.getIntAttr((Element)elWalkForward, (String)"period", (int)10);
        String settings = "";
        settings = OptimizationConst.wfTypeToString((int)XMLUtil.getIntAttr((Element)elWalkForward, (String)"type", (int)1));
        settings = settings + "," + OptimizationConst.getPeriodTypeAsString((int)periodType);
        settings = settings + "," + (XMLUtil.getIntAttr((Element)elWalkForward, (String)"optimization", (int)15) == 15 ? "Floating" : "Fixed");
        settings = settings + "\n";
        settings = settings + OptimizationConst.printWFByPeriodType((int)periodType, (int)XMLUtil.getIntAttr((Element)elWalkForward.getChild("Param2"), (String)"value", (int)10), (int)XMLUtil.getIntAttr((Element)elWalkForward.getChild("Param1"), (String)"value", (int)20));
        settings = settings + "\n";
        settings = settings + L.t((String)"Optimize Periods: %s", (Object[])new Object[]{XMLUtil.getNodeBooleanValue((Element)settingsEl, (String)"OptimizePeriods", (boolean)false) ? "Yes" : "No"});
        settings = settings + "," + L.t((String)"Optimize Exit Types: %s", (Object[])new Object[]{XMLUtil.getNodeBooleanValue((Element)settingsEl, (String)"OptimizeExitTypes", (boolean)false) ? "Yes" : "No"});
        settings = settings + "," + L.t((String)"Max Tests: %s", (Object[])new Object[]{XMLUtil.getNodeIntValue((Element)settingsEl, (String)"MaxTests", (int)100)});
        settings = settings + "\n\n";
        Element elAcceptanceSettings = elMethod.getChild("AcceptanceSettings");
        settings = settings + L.t((String)"ThresholdPct: %s", (Object[])new Object[]{XMLUtil.getIntAttr((Element)elAcceptanceSettings, (String)"thresholdPct", (int)10)});
        settings = settings + "\n";
        Element conditionsEl = elAcceptanceSettings.getChild("Conditions");
        ArrayList conditions = ProjectConfigHelper.getConditions((Element)conditionsEl);
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = (Condition)conditions.get(i);
            if (!condition.isUsed()) continue;
            settings = settings + condition.toString();
            settings = settings + "\n";
        }
        return settings;
    }

    public int getBadStrategyReason() {
        return 10035;
    }

    public boolean disabledForSpecialTrial() {
        return true;
    }
}

