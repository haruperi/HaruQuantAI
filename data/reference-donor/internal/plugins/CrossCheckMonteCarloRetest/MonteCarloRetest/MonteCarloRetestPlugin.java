/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.MonteCarloRetest
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.optimization.MetricForFitness
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.results.SymbolsMap
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessResults
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.simplegrid.SimpleGridEngine
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest;

import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MCJobResult;
import com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MCRetestJob;
import com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MonteCarloRetest;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import jakarta.servlet.Servlet;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;

@PluginImplementation
public class MonteCarloRetestPlugin
extends MonteCarloCrossCheckMethod
implements IServletPlugin {
    private ServletContextHandler dataContext;
    private int numberOfSimulations;
    private int lastIndex;
    private boolean useFullSample;
    private int backtestPrecision;

    public ICrossCheck clone(SettingsMap settings) {
        MonteCarloRetestPlugin crossCheck = new MonteCarloRetestPlugin();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        crossCheck.numberOfSimulations = this.numberOfSimulations;
        crossCheck.useFullSample = this.useFullSample;
        crossCheck.backtestPrecision = this.backtestPrecision;
        return crossCheck;
    }

    public String getName() {
        return NameMCRetest;
    }

    public String getShortName() {
        return L.tsq((String)"MC retest");
    }

    public String getDescription() {
        return L.tsq((String)"This cross check uses Monte Carlo methods that perform simulations that require retesting the strategy - using different spread, parameters or history data.<br/>Note that it is slow, strategy will have to be retested multiple times, depending on your number of simulations.");
    }

    public String getSettingName() {
        return "MonteCarloRetest";
    }

    public int getType() {
        return 1;
    }

    public int getPreferredPosition() {
        return 240;
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/monteCarloRetest/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new MonteCarloRetestServlet()), "/*");
        }
        return this.dataContext;
    }

    public int getNumberOfSimulations() {
        return this.numberOfSimulations;
    }

    public boolean doesRetest() {
        return true;
    }

    public boolean doesForEverySetup() {
        return false;
    }

    public void fixSettings(Element elSettings) {
        super.fixSettings(elSettings);
        Element elMethodSettings = elSettings.getChild("Settings");
        XMLUtil.tryAddElement((Element)elMethodSettings, (String)"Methods");
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        this.fixSettings(elSettings);
        Element elMethodSettings = elSettings.getChild("Settings");
        this.settings.set("MCUseFullSample", (Object)XMLUtil.getNodeBooleanValue((Element)elMethodSettings, (String)"MCUseFullSample", (boolean)false));
        this.settings.set("RTNumberOfSimulations", (Object)XMLUtil.getNodeIntValue((Element)elMethodSettings, (String)"NumberOfSimulations", (int)10));
        this.settings.set("MonteCarloManipulation", (Object)ProjectConfigHelper.getMonteCarloRetestMethods((Element)elMethodSettings.getChild("Methods")));
        this.settings.set("MCBacktestPrecision", (Object)XMLUtil.getNodeIntValue((Element)elMethodSettings, (String)"MCBacktestPrecision", (int)-1));
        this.readConditions(elSettings);
        this.numberOfSimulations = (Integer)this.settings.get("RTNumberOfSimulations");
        this.useFullSample = (Boolean)this.settings.get("MCUseFullSample");
        this.backtestPrecision = (Integer)this.settings.get("MCBacktestPrecision");
    }

    public boolean runTest(ResultsGroup rg, int index, double globalATR, GridJob parentGridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        this.numberOfSimulations = (Integer)this.settings.get("RTNumberOfSimulations");
        this.useFullSample = (Boolean)this.settings.get("MCUseFullSample");
        this.backtestPrecision = (Integer)this.settings.get("MCBacktestPrecision");
        String mainResultKey = rg.getMainResultKey();
        SymbolsMap symbolsMap = rg.symbols();
        Result result = null;
        OrdersList orders = rg.orders();
        result = rg.subResult(mainResultKey);
        SettingsMap resultSettings = result.getSettings();
        int mainBacktestPrecision = resultSettings.getInt("BacktestPrecision", 1);
        OrdersList ordersClone = orders.filterWithClone(mainResultKey, (byte)0, this.useFullSample ? (byte)127 : 10);
        this.getOrCreateOriginalOrders(result, ordersClone, mainResultKey, resultSettings, symbolsMap);
        ArrayList<RobustnessResults> simulationResults = this.runOnGrid(resultSettings, mainBacktestPrecision, result, symbolsMap, globalATR, strategyName, parentGridJob, lastEventListener, singleThreaded, this.useFullSample, this.backtestPrecision);
        result.set(this.getSettingName() + "_NumberOfSimulations", (Object)this.numberOfSimulations);
        ArrayList methods = (ArrayList)this.settings.get("MonteCarloManipulation");
        String[] methodsStr = new String[methods.size()];
        for (int m = 0; m < methods.size(); ++m) {
            methodsStr[m] = ((MonteCarloRetest)methods.get(m)).printFormatedName();
        }
        result.set(this.getSettingName() + "_Methods", (Object)methodsStr);
        String symbol = rg.subResult(rg.getMainResultKey()).getString(SpecialValues.Symbol);
        String tf = rg.subResult(rg.getMainResultKey()).getString(SpecialValues.Timeframe);
        String dateFrom = SQTime.toUIDateString((long)rg.specialValues().getLong(SpecialValues.HistoryFrom));
        String dateTo = SQTime.toUIDateString((long)rg.specialValues().getLong(SpecialValues.HistoryTo));
        result.set(this.getSettingName() + "_Symbol", (Object)symbol);
        result.set(this.getSettingName() + "_TimeFrame", (Object)tf);
        result.set(this.getSettingName() + "_DateRange", (Object)(dateFrom + " - " + dateTo));
        this.computeConfidenceLevels(result, simulationResults);
        return this.checkConditions(rg, index);
    }

    private ArrayList<RobustnessResults> runOnGrid(final SettingsMap resultSettings, final int mainBacktestPrecision, final Result result, final SymbolsMap symbolsMap, final double globalATR, final String strategyName, GridJob parentGridJob, final ILastEventListener lastEventListener, boolean singleThreaded, final boolean useFullSample, final int backtestPrecision) throws Exception {
        final ArrayList<RobustnessResults> simulationResults = new ArrayList<RobustnessResults>();
        this.lastIndex = 0;
        SimpleGridEngine<MCRetestJob, MCJobResult> gridEngine = new SimpleGridEngine<MCRetestJob, MCJobResult>(this, this.stopPauseEngine, parentGridJob, singleThreaded){
            final /* synthetic */ MonteCarloRetestPlugin this$0;
            {
                this.this$0 = this$0;
                super(arg0, arg1, arg2);
            }

            protected ArrayList<MCRetestJob> createJobsBatch(int jobsToCreate, GridClient gridClient) throws Exception {
                return this.this$0.createBatch(strategyName, jobsToCreate, gridClient, this.this$0.numberOfSimulations, resultSettings, this.this$0.settings, lastEventListener, mainBacktestPrecision, globalATR, symbolsMap, useFullSample, backtestPrecision);
            }

            protected void processResult(MCJobResult mcJobResult, JobDetails jobDetails) throws Exception {
                this.this$0.processMCResult(mcJobResult, jobDetails, simulationResults, result);
            }

            protected void onError(String errorMsg, Exception exception) {
                Log.error("MC Error {}, Exception ", (Object)errorMsg, (Object)exception);
            }
        };
        gridEngine.start();
        gridEngine.unregisterListeners();
        return simulationResults;
    }

    protected void processMCResult(MCJobResult mcJobResult, JobDetails jobDetails, ArrayList<RobustnessResults> simulationResults, Result result) {
        String taskName = jobDetails.getJobID();
        String mcJobError = mcJobResult.getDismissalMessage();
        if (mcJobError != null) {
            Log.error(String.format("MC retest job %s dismissed, error: %s", taskName, mcJobError));
            return;
        }
        if (jobDetails.isSuccess()) {
            RobustnessResults rr = mcJobResult.getRR();
            if (rr != null && rr.getOrdersValues().size() > 1) {
                simulationResults.add(rr);
                result.addMCSimulation(this.getSettingName(), rr);
            } else {
                Log.debug("MC retest job returned empty result");
            }
        } else {
            jobDetails.getException();
            Log.error(String.format("Optimization %s failed, error: %s", taskName, jobDetails.getException()));
        }
    }

    protected ArrayList<MCRetestJob> createBatch(String strategyName, int jobsToCreate, GridClient gridClient, long totalCombinations, SettingsMap resultSettings, SettingsMap mcSettings, ILastEventListener lastEventListener, int mainBacktestPrecision, double globalATR, SymbolsMap symbolsMap, boolean useFullSample, int backtestPrecision) throws Exception {
        ArrayList<MCRetestJob> jobsGroup = new ArrayList<MCRetestJob>();
        int jobsAdded = 0;
        for (long i = (long)this.lastIndex; i < (long)(this.lastIndex + jobsToCreate) && i < totalCombinations; ++i) {
            String simStrategyName = String.format("%s MC %d", strategyName, i);
            MCRetestJob job = new MCRetestJob(i, strategyName, simStrategyName, MonteCarloRetestPlugin.getJobSettings(resultSettings, mcSettings, useFullSample, backtestPrecision), this.stopPauseEngine, lastEventListener, mainBacktestPrecision, globalATR, symbolsMap);
            jobsGroup.add(job);
            ++jobsAdded;
        }
        this.lastIndex += jobsAdded;
        if (jobsGroup.size() == 0) {
            return null;
        }
        return jobsGroup;
    }

    private static Map<String, Serializable> getJobSettings(SettingsMap resultSettings, SettingsMap mcSettings, boolean useFullSample, int backtestPrecision) {
        HashMap<String, Serializable> params = new HashMap<String, Serializable>();
        params.put("resultSettings", (Serializable)resultSettings);
        params.put("mcSettings", (Serializable)mcSettings);
        params.put("useFullSample", Boolean.valueOf(useFullSample));
        params.put("backtestPrecision", Integer.valueOf(backtestPrecision));
        return params;
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
        String settings = "";
        settings = L.t((String)"Number of simulations: %s", (Object[])new Object[]{XMLUtil.getNodeIntValue((Element)settingsEl, (String)"NumberOfSimulations", (int)10)});
        settings = settings + "," + L.t((String)"Use Full sample: %s", (Object[])new Object[]{XMLUtil.getNodeBooleanValue((Element)settingsEl, (String)"MCUseFullSample", (boolean)false)});
        int backtestPrecision = XMLUtil.getNodeIntValue((Element)settingsEl, (String)"MCBacktestPrecision", (int)-1);
        settings = backtestPrecision == -1 ? settings + "," + L.t((String)"Backtest precision: %s", (Object[])new Object[]{"Same as main chart"}) : settings + "," + L.t((String)"Backtest precision: %s", (Object[])new Object[]{Precisions.toString((int)backtestPrecision)});
        settings = settings + "\n";
        ArrayList methods = ProjectConfigHelper.getMonteCarloRetestMethods((Element)settingsEl.getChild("Methods"));
        for (int i = 0; i < methods.size(); ++i) {
            MonteCarloRetest method = (MonteCarloRetest)methods.get(i);
            settings = settings + method.printFormatedName();
            settings = settings + "\n";
        }
        settings = settings + "\n";
        Element conditionsEl = elMethod.getChild("AcceptanceSettings").getChild("Conditions");
        ArrayList conditions = ProjectConfigHelper.getConditions((Element)conditionsEl);
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = (Condition)conditions.get(i);
            if (!condition.isUsed()) continue;
            settings = settings + condition.toString();
            settings = settings + "\n";
        }
        return settings;
    }

    public String printWeightedGoals() throws Exception {
        return null;
    }

    public ArrayList<MetricForFitness> getMetricsForFitness() {
        return null;
    }

    public double getMetricValue(ResultsGroup results, byte direction, byte sampleType, String databankColumnName) throws Exception {
        return 0.0;
    }

    public int getBadStrategyReason() {
        return 10031;
    }

    public boolean doesCreateSubjobs() {
        return true;
    }
}

