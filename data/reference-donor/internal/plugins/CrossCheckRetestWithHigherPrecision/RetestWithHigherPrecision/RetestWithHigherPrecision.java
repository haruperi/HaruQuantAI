/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.Directions
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SampleTypes
 *  com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckMethod
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.engine.BacktestEngine
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.MetricForFitness
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.simulator.impl.TraderSimulators
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import jakarta.servlet.Servlet;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;

@PluginImplementation
public class RetestWithHigherPrecision
extends CrossCheckMethod
implements IFitnessFunction,
IServletPlugin {
    private ServletContextHandler dataContext;
    private String databankColumnName = null;
    private ArrayList<Goal> weightedGoals = new ArrayList();

    public ICrossCheck clone(SettingsMap settings) {
        RetestWithHigherPrecision crossCheck = new RetestWithHigherPrecision();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        return crossCheck;
    }

    public String getName() {
        return NameHigherBacktestPrecis;
    }

    public String getShortName() {
        return L.t((String)"Higher backtest precis.", (Object[])new Object[0]);
    }

    public String getDescription() {
        return L.tsq((String)"This cross checks retests the strategy with higher test precision.<br/>It can be used if you are using the lowest 'Selected timeframe' precision in the main backtest to quickly find and evaluate the valid strategies. You can then use this cross check to retest the strategy with higher precision to see if it performs in a same way with higher precision backtesting.");
    }

    public String getSettingName() {
        return "RetestWithHigherPrecision";
    }

    public int getType() {
        return 0;
    }

    public int getPreferredPosition() {
        return 300;
    }

    public int getNumberOfSimulations() {
        return 1;
    }

    public boolean doesRetest() {
        return true;
    }

    public boolean doesForEverySetup() {
        return false;
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        this.fixSettings(elSettings);
        Element elMethodSettings = elSettings.getChild("Settings");
        Element elPrecision = elMethodSettings.getChild("Precision");
        Element elSpread = elMethodSettings.getChild("Spread");
        try {
            this.settings.set("BacktestPrecision", (Object)Integer.parseInt(elPrecision.getValue()));
        }
        catch (Exception e) {
            Log.warn("Cannot load backtest precision setting. Using default...", (Throwable)e);
            this.settings.set("BacktestPrecision", (Object)1);
        }
        try {
            if (this.settings != null && elSpread != null) {
                this.settings.set("BacktestSpread", (Object)Double.parseDouble(elSpread.getValue()));
            } else {
                this.settings.set("BacktestSpread", (Object)1);
            }
        }
        catch (Exception e) {
            Log.warn("Cannot load backtest spread setting. Using default...", (Throwable)e);
            this.settings.set("BacktestSpread", (Object)1);
        }
        this.readConditions(elSettings);
    }

    public boolean runTest(ResultsGroup rg, int index, double globalATR, GridJob gridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        int precision = (Integer)this.settings.get("BacktestPrecision");
        double spread = this.settings.getDouble("BacktestSpread", -2.0);
        OrdersList orders = rg.orders();
        String mainResultKey = rg.getMainResultKey();
        Result result = rg.subResult(mainResultKey);
        SettingsMap settings = result.getSettings();
        SettingsMap clonedSettings = this.cloneSettings(settings);
        ChartSetup chartSetup = (ChartSetup)clonedSettings.get("BacktestChart");
        chartSetup.setTestPrecision(precision);
        if (lastEventListener != null) {
            String event = L.t((String)"Running higher precision backtest for %s", (Object[])new Object[]{strategyName});
            lastEventListener.setLastEvent(event);
        }
        if (spread != -2.0) {
            ArrayList subcharts = chartSetup.getCharts();
            int mainSymbol = 0;
            for (int i = 0; i < subcharts.size(); ++i) {
                ChartDef subchart = (ChartDef)subcharts.get(i);
                if (i != 0 && subchart.getSymbolHash() != mainSymbol) continue;
                mainSymbol = chartSetup.getMainChart().getSymbolHash();
                subchart.setSpread(spread);
            }
        }
        BacktestEngine backtestEngine = new BacktestEngine(TraderSimulators.getSimulator((ChartSetup)chartSetup));
        backtestEngine.setSingleThreaded(true);
        backtestEngine.setUsePreparedData(true);
        backtestEngine.setStopPauseEngine(this.stopPauseEngine);
        backtestEngine.registerProgressListener(new IBacktestProgressListener(){

            public void setProgress(int progress) {
                RetestWithHigherPrecision.this.setJobProgress(progress);
            }

            public void increaseProgressStep() {
            }
        });
        backtestEngine.addSetup(clonedSettings);
        ResultsGroup newRg = backtestEngine.runBacktest().getResults();
        String ccSetupName = "CrossCheck_HigherPrecision";
        OrdersList ordersSimulation = newRg.orders();
        for (int i = 0; i < ordersSimulation.size(); ++i) {
            Order o = ordersSimulation.get(i);
            o.SetupName = ccSetupName;
            o.IsInPortfolio = 0;
        }
        rg.addSubresult(ccSetupName, settings);
        Result ccResult = rg.subResult(ccSetupName);
        ccResult.setSpecial(true);
        ccResult.setFrom(newRg.subResult(mainResultKey), ccSetupName);
        orders.addAll(ordersSimulation);
        if (this.backtestProgressListener != null) {
            this.backtestProgressListener.increaseProgressStep();
        }
        return this.checkConditions(rg, index);
    }

    public double getStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        if (!rg.getResultKeys().contains("CrossCheck_HigherPrecision")) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
        return column.getNumericValue(rg, "CrossCheck_HigherPrecision", direction, plType, sampleType);
    }

    public boolean hasStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        return rg.getResultKeys().contains("CrossCheck_HigherPrecision");
    }

    public String printSpecialValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        if (!rg.getResultKeys().contains("CrossCheck_HigherPrecision")) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
        return column.getValue(rg, rg.getMainResultKey(), direction, plType, sampleType);
    }

    public String getColumnTitle(String columnName, Element elColumn, Object ... params) {
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        String title = this.getColumnTitleTemplate();
        title = title.replace("#columnName#", columnName);
        title = title.replace(", #sampleType#", sampleType == 127 ? "" : ", " + SampleTypes.typeToString((byte)sampleType));
        title = title.replace(", #direction#", direction == 0 ? "" : ", " + Directions.typeToString((byte)direction));
        title = title.replace(", #plType#", plType == 10 ? "" : ", " + PlTypes.typeToString((byte)plType));
        return title;
    }

    public String getColumnTitleTemplate() {
        return "#columnName# (" + this.getShortName() + ", #sampleType#, #direction#, #plType#)";
    }

    public ChartSetups getChartSetups(ChartSetup mainChartSetup) {
        ChartSetup newCS = mainChartSetup.getClone();
        int precision = (Integer)this.settings.get("BacktestPrecision");
        newCS.setTestPrecision(precision);
        return new ChartSetups(newCS);
    }

    public boolean doesCreateSubjobs() {
        return false;
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
        int precision = Integer.parseInt(settingsEl.getChild("Precision").getValue());
        settings = L.t((String)"Backtest precision: %s", (Object[])new Object[]{Precisions.toString((int)precision)});
        settings = settings + "," + L.t((String)"Spread: %s", (Object[])new Object[]{settingsEl.getChildText("Spread")});
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

    public int getBadStrategyReason() {
        return 10036;
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/retestWithHigherPrecision/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new RetestWithHigherPrecisionServlet()), "/*");
        }
        return this.dataContext;
    }

    public double computeFitness(ResultsGroup results, byte direction, byte sampleType) throws Exception {
        return this.computeFitness(results, direction, sampleType, true);
    }

    public double computeFitness(ResultsGroup results, byte direction, byte sampleType, boolean useRatioByTrades) throws Exception {
        if (this.databankColumnName.equals("Weighted")) {
            return this.computeWeightedFitness(results, direction, sampleType);
        }
        return this.getFitnessValue(results, direction, sampleType, this.databankColumnName, 0.0, (byte)0);
    }

    private double getFitnessValue(ResultsGroup results, byte direction, byte sampleType, String databankColumnName, double target, byte valueType) throws Exception {
        double val;
        DatabankColumn c = (DatabankColumn)DatabankColumns.get().findClassByName(databankColumnName);
        double fitness = c.transformToFitnessRange(val = !results.hasResult("CrossCheck_HigherPrecision") ? c.getNumericValue(results, "Portfolio", direction, (byte)10, sampleType) : c.getNumericValue(results, "CrossCheck_HigherPrecision", direction, (byte)10, sampleType), target, valueType);
        if (fitness < 0.0) {
            fitness = 0.0;
        }
        if (fitness > 1.0) {
            fitness = 1.0;
        }
        return fitness;
    }

    private double computeWeightedFitness(ResultsGroup results, byte direction, byte sampleType) throws Exception {
        float totalWeight = 0.0f;
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            if (!this.weightedGoals.get((int)i).use) continue;
            totalWeight = (float)((double)totalWeight + this.weightedGoals.get((int)i).weight);
        }
        float weightedFitness = 0.0f;
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            Goal goal = this.weightedGoals.get(i);
            if (!goal.use) continue;
            double rankingFitness = this.getFitnessValue(results, direction, sampleType, goal.statsValueName, goal.target, goal.valueType);
            weightedFitness = (float)((double)weightedFitness + goal.weight / (double)totalWeight * rankingFitness);
        }
        return weightedFitness;
    }

    public String getFitnessKey() {
        return this.getSettingName();
    }

    public String getFitnessName() {
        return "Cross check - Higher backtest precision";
    }

    public void initFitnessFromXml(Element elSettings) {
        this.weightedGoals.clear();
        Element elRanking = elSettings.getChild("Ranking");
        this.databankColumnName = elRanking.getAttributeValue("type");
        for (Element elGoal : elRanking.getChildren("Goal")) {
            Goal goal = new Goal();
            String use = elGoal.getAttributeValue("use");
            goal.use = use.equals("true") || use.equalsIgnoreCase("1");
            goal.statsValueName = elGoal.getAttributeValue("type");
            goal.weight = XMLUtil.getDoubleAttr((Element)elGoal, (String)"weight", (double)1.0);
            goal.valueType = XMLUtil.getByteAttr((Element)elGoal, (String)"valueType", (byte)0);
            goal.target = XMLUtil.getDoubleAttr((Element)elGoal, (String)"target", (double)0.0);
            this.weightedGoals.add(goal);
        }
    }

    public byte getFitnessType() throws Exception {
        if (this.databankColumnName.equals("Weighted")) {
            return 1;
        }
        return ((DatabankColumn)DatabankColumns.get().findClassByName((String)this.databankColumnName)).valueType;
    }

    public String getFitnessDatabankColumnName() {
        return this.databankColumnName;
    }

    public ArrayList<DatabankColumn> getUsedStatValues() throws Exception {
        throw new Exception("This fitness method cannot be used in Walk-Forward!");
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

    public IFitnessFunction clone() {
        return this;
    }

    public String forEngine() {
        return "*,-SP,-SA";
    }

    private class Goal {
        public boolean use;
        public String statsValueName;
        public double weight;
        public double target;
        public byte valueType;

        private Goal() {
        }
    }
}

