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
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.Variables
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.OptProfileChecksLevels
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.SysParamPermutationsTable
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.OptProfileChecksLevels;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.SysParamPermutationsTable;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import jakarta.servlet.Servlet;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;

@PluginImplementation
public class OptProfileSysParamPermutation
extends WalkForwardCrossCheckMethod
implements IServletPlugin {
    private static final String CROSSCHECK_NAME = "OptProfileSysParamPermutation_CrossCheck";
    private ServletContextHandler dataContext;
    private OptProfileChecksLevels optProfileLevels;
    private int distributionUp = 30;
    private int distributionDown = 30;
    private int maxSteps = 10;
    private ValuesMap paramTypesOPSPP = new ValuesMap();

    public OptProfileSysParamPermutation() {
        super(CROSSCHECK_NAME);
        this.optProfileLevels = new OptProfileChecksLevels();
    }

    public String getName() {
        return NameOptProfileSPP;
    }

    public String getShortName() {
        return L.tsq((String)"Opt. Profile / SPP");
    }

    public String getDescription() {
        return L.tsq((String)"This cross check performs optimization of the strategy and then evaluates its Optimization profile - see the conditions in filter.");
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/optProfileSysParamPerm/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new OptProfileSysParamPermutationServlet()), "/*");
        }
        return this.dataContext;
    }

    public String getSettingName() {
        return ((Object)((Object)this)).getClass().getSimpleName();
    }

    public int getType() {
        return 2;
    }

    public int getPreferredPosition() {
        return 260;
    }

    public int getNumberOfSimulations() {
        return 0;
    }

    public boolean doesRetest() {
        return true;
    }

    public boolean doesForEverySetup() {
        return false;
    }

    public void fixSettings(Element elSettings) {
        super.fixSettings(elSettings);
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        this.fixSettings(elSettings);
        Element elTaskSettings = elSettings.getParentElement().getParentElement();
        this.elRankings = elTaskSettings.getChild("Rankings");
        Element elMethodSettings = elSettings.getChild("Settings");
        this.optimizationSettings.maxOptimizationBacktests = XMLUtil.getNodeIntValue((Element)elMethodSettings, (String)"MaxTests", (int)100);
        this.distributionUp = XMLUtil.getNodeIntValue((Element)elMethodSettings, (String)"DistributionUp", (int)100);
        this.distributionDown = XMLUtil.getNodeIntValue((Element)elMethodSettings, (String)"DistributionDown", (int)100);
        this.maxSteps = XMLUtil.getNodeIntValue((Element)elMethodSettings, (String)"Steps", (int)25);
        Element whatToParametrizeElem = elMethodSettings.getChild("WhatToParametrize");
        this.readWhatToParametrize(whatToParametrizeElem);
        this.paramTypesOPSPP = this.paramTypes.clone();
        Element elAcceptanceSettings = elSettings.getChild("AcceptanceSettings");
        if (elAcceptanceSettings == null) {
            elAcceptanceSettings = XMLUtil.tryAddElement((Element)elSettings, (String)"AcceptanceSettings");
        }
        try {
            Element elConditions = XMLUtil.tryAddElement((Element)elAcceptanceSettings, (String)"Conditions");
            this.settings.set("Conditions", (Object)ProjectConfigHelper.getConditions((Element)elConditions));
            this.optimizationSettings.elConditions = elConditions;
            this.optimizationSettings.conditions = ProjectConfigHelper.getConditions((Element)elConditions);
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Cannot read conditions of Crosscheck method '%s'", (Object[])new Object[]{this.getName()}), e);
        }
        this.optProfileLevels.evalProfitOptCheck = XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalProfitOptCheck", (boolean)true);
        this.optProfileLevels.evalAvgProfitCheck = XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalAvgProfitCheck", (boolean)true);
        this.optProfileLevels.evalUniformDistrCheck = XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalUniformDistrCheck", (boolean)true);
        this.optProfileLevels.evalTopProfitCheck = XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalTopProfitCheck", (boolean)true);
        this.optProfileLevels.profitableOptPct = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"ProfitOptPct", (int)30);
        this.optProfileLevels.avgProfit = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"AvgProfit", (int)0);
        this.optProfileLevels.uniformDistrChanges = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"UniformDistrChanges", (int)5);
        this.optProfileLevels.stdevAvgProfit = XMLUtil.getDouble((Element)elAcceptanceSettings, (String)"StdevAvgProfit", (double)1.0);
    }

    protected SettingsMap prepareSettings(String name, SettingsMap mainSettings, Element strategyXml, boolean singleThreaded) throws Exception {
        try {
            SettingsMap newSettings = this.cloneSettings(mainSettings);
            ChartSetups chartSetups = new ChartSetups();
            chartSetups.add((Object)((ChartSetup)newSettings.get("BacktestChart")));
            newSettings.set("ChartSetups", (Object)chartSetups);
            newSettings.set("StrategyXml", (Object)strategyXml);
            StrategyBase strategy = StrategyBase.createXmlStrategy((Element)strategyXml);
            strategy.transformToVariables(this.paramSymmetry, this.paramTypesOPSPP);
            Variables vars = strategy.variables();
            vars.sortByName();
            newSettings.set("StrategyObject", (Object)strategy);
            newSettings.set("StrategyName", (Object)name);
            this.optimizationSettings.parameters = this.initializeParams(strategy, this.distributionUp, this.distributionDown, this.maxSteps);
            this.optimizationSettings.optimizationMethod = 0;
            this.optimizationSettings.type = 4;
            this.optimizationSettings.singleThreaded = singleThreaded;
            newSettings.set("OptimizationSettings", (Object)this.optimizationSettings.clone());
            IFitnessFunction ff = ProjectConfigHelper.getFitnessFunction((Element)this.elRankings);
            newSettings.set("FitnessFunction", (Object)ff);
            return newSettings;
        }
        catch (Exception e) {
            Log.error(SQUtils.getStackTrace((Throwable)e));
            throw new Exception(L.t((String)"Error while preparing settings - %s", (Object[])new Object[]{e.getMessage()}));
        }
    }

    public boolean runTest(ResultsGroup rg, int index, double globalATR, GridJob parentGridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        boolean result = super.runTest(rg, index, globalATR, parentGridJob, singleThreaded, lastEventListener, strategyName);
        if (!result) {
            return false;
        }
        return this.checkOptimizationProfileConditions(rg);
    }

    protected void processResult(ResultsGroup mainRG, ResultsGroup wfRG) {
        try {
            OptimizationProfile op1 = wfRG.getOptimizationProfile();
            OptimizationProfile op2 = mainRG.getOptimizationProfile();
            if (op2 == null && op1 != null) {
                mainRG.setOptimizationProfile(op1);
            }
            wfRG.orders().clear();
        }
        catch (Exception e) {
            Log.info("Error processing Optimization result", (Throwable)e);
        }
    }

    private boolean checkOptimizationProfileConditions(ResultsGroup rg) throws Exception {
        rg.specialValues().set("OptProfileChecksLevels", (Object)this.optProfileLevels);
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        if (optimizationProfile == null) {
            return true;
        }
        if (!optimizationProfile.evaluateChecks(this.optProfileLevels)) {
            this.dismissalReason = optimizationProfile.getDismissalReason();
            this.dismissalMessage = L.t((String)"Cross Check filter in '%s': %s", (Object[])new Object[]{this.getName(), optimizationProfile.getDismissalMessage()});
            return false;
        }
        return true;
    }

    protected boolean checkConditions(ResultsGroup strategy, int index) {
        ArrayList conditions = (ArrayList)this.settings.get("Conditions");
        if (conditions != null && conditions.size() > 0) {
            for (int i = 0; i < conditions.size(); ++i) {
                Condition condition = (Condition)conditions.get(i);
                if (!condition.isUsed()) continue;
                try {
                    boolean met = this.conditionsChecker.check(strategy, condition);
                    if (met) continue;
                    this.dismissalReason = 300000 + i + index * 1000;
                    this.dismissalMessage = L.t((String)"Cross Check filter in '%s': %s", (Object[])new Object[]{this.getName(), this.conditionsChecker.dismissalMessage});
                    return false;
                }
                catch (CrossCheckDataNotExistException met) {
                    continue;
                }
                catch (Exception e) {
                    Log.error("Error while checking condition", (Throwable)e);
                    this.dismissalReason = 10003;
                    this.dismissalMessage = L.t((String)"Cross Check filter in '%s': Error evaluating conditions: %s", (Object[])new Object[]{this.getName(), e.getMessage()});
                    return false;
                }
            }
        }
        return true;
    }

    public double getStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        if (optimizationProfile == null) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        SysParamPermutationsTable table = optimizationProfile.getSysParamPermutationsTable();
        return table.getMedian(columnName);
    }

    public boolean hasStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        return optimizationProfile != null;
    }

    public String printSpecialValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        double value = this.getStatsValue(rg, columnName, elColumn, params);
        DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
        return column.printPlValue(value, (byte)10);
    }

    public String getColumnTitle(String columnName, Element elColumn, Object ... params) {
        String title = this.getColumnTitleTemplate();
        title = title.replace("#columnName#", columnName);
        return title;
    }

    public String getColumnTitleTemplate() {
        return "#columnName# (Median)";
    }

    public ChartSetups getChartSetups(ChartSetup mainChartSetup) {
        return null;
    }

    public ICrossCheck clone(SettingsMap settings) {
        OptProfileSysParamPermutation crossCheck = new OptProfileSysParamPermutation();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        crossCheck.elRankings = this.elRankings;
        crossCheck.optimizationSettings = this.optimizationSettings.clone();
        crossCheck.optProfileLevels = this.optProfileLevels.clone();
        crossCheck.distributionUp = this.distributionUp;
        crossCheck.distributionDown = this.distributionDown;
        crossCheck.maxSteps = this.maxSteps;
        crossCheck.paramTypesOPSPP = this.paramTypes.clone();
        return crossCheck;
    }

    public String printSettings(Element elMethod) throws Exception {
        if (elMethod == null) {
            throw new NullPointerException();
        }
        if (!XMLUtil.elementIs((Element)elMethod, (String)"use")) {
            return "Not used";
        }
        Element settingsEl = elMethod.getChild("Settings");
        String settings = "";
        settings = L.t((String)"Optimize Periods: %s", (Object[])new Object[]{XMLUtil.getNodeBooleanValue((Element)settingsEl, (String)"OptimPeriods", (boolean)false) ? "Yes" : "No"});
        settings = settings + "," + L.t((String)"Optimize Exit Types: %s", (Object[])new Object[]{XMLUtil.getNodeBooleanValue((Element)settingsEl, (String)"OptimExitTypes", (boolean)false) ? "Yes" : "No"});
        settings = settings + "," + L.t((String)"Max Tests: %s", (Object[])new Object[]{XMLUtil.getNodeIntValue((Element)settingsEl, (String)"MaxTests", (int)100)});
        settings = settings + "\n\n";
        Element elAcceptanceSettings = elMethod.getChild("AcceptanceSettings");
        if (XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalProfitOptCheck", (boolean)true)) {
            settings = settings + L.t((String)"ProfitOptPct: %s", (Object[])new Object[]{XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"ProfitOptPct", (int)30)});
        }
        if (XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalAvgProfitCheck", (boolean)true)) {
            settings = settings + "," + L.t((String)"AvgProfit: %s", (Object[])new Object[]{XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"AvgProfit", (int)0)});
        }
        if (XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalUniformDistrCheck", (boolean)true)) {
            settings = settings + "," + L.t((String)"UniformDistrChanges: %s", (Object[])new Object[]{XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"UniformDistrChanges", (int)5)});
        }
        if (XMLUtil.getNodeBooleanValue((Element)elAcceptanceSettings, (String)"EvalTopProfitCheck", (boolean)true)) {
            settings = settings + "," + L.t((String)"StdevAvgProfit: %s", (Object[])new Object[]{XMLUtil.getDouble((Element)elAcceptanceSettings, (String)"StdevAvgProfit", (double)1.0)});
        }
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
        return 10032;
    }
}

