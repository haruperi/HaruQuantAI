/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.random.MersenneTwisterRng
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.MonteCarloManipulation
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.MCResultsComputer
 *  com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.optimization.MetricForFitness
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.results.SymbolsMap
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessResults
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.random.MersenneTwisterRng;
import com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MonteCarloManipulation;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.MCResultsComputer;
import com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
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
public class MonteCarloManipulationPlugin
extends MonteCarloCrossCheckMethod
implements IServletPlugin {
    private ServletContextHandler dataContext;
    private final int[] originalStatsKeys = new int[]{"TotalTradingDays".hashCode(), "TotalTradingMonths".hashCode(), "TotalTradingYears".hashCode()};
    private int numberOfSimulations;
    private boolean useFullSample;

    public ICrossCheck clone(SettingsMap settings) {
        MonteCarloManipulationPlugin crossCheck = new MonteCarloManipulationPlugin();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        crossCheck.numberOfSimulations = this.numberOfSimulations;
        crossCheck.useFullSample = this.useFullSample;
        return crossCheck;
    }

    public String getName() {
        return NameMCManipulation;
    }

    public String getShortName() {
        return L.tsq((String)"MC trades");
    }

    public String getDescription() {
        return L.tsq((String)"This cross check uses Monte Carlo method to perform various simulations of resulting equity curve by manipulating the order of the trades.<br/>It allows you to quickly assess how much the good results are dependent on order of the trades.");
    }

    public String getSettingName() {
        return "MonteCarloManipulation";
    }

    public int getType() {
        return 0;
    }

    public int getPreferredPosition() {
        return 230;
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/monteCarloManipulation/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new MonteCarloManipulationServlet()), "/*");
        }
        return this.dataContext;
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
        this.settings.set("MonteCarloManipulation", (Object)ProjectConfigHelper.getMonteCarloManipulationMethods((Element)elMethodSettings.getChild("Methods")));
        this.readConditions(elSettings);
        this.numberOfSimulations = (Integer)this.settings.get("RTNumberOfSimulations");
        this.useFullSample = (Boolean)this.settings.get("MCUseFullSample");
    }

    public boolean runTest(ResultsGroup rg, int index, double globalATR, GridJob gridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        int m;
        ArrayList methods = (ArrayList)this.settings.get("MonteCarloManipulation");
        this.numberOfSimulations = (Integer)this.settings.get("RTNumberOfSimulations");
        this.useFullSample = (Boolean)this.settings.get("MCUseFullSample");
        String mainResultKey = rg.getMainResultKey();
        SymbolsMap symbolsMap = rg.symbols();
        MersenneTwisterRng rng = new MersenneTwisterRng();
        Result result = rg.subResult(mainResultKey);
        ArrayList<RobustnessResults> simulationResults = new ArrayList<RobustnessResults>();
        SettingsMap settings = result.getSettings();
        OrdersList orders = rg.orders();
        OrdersList ordersClone = orders.filterWithClone(mainResultKey, (byte)0, this.useFullSample ? (byte)127 : 10);
        this.getOrCreateOriginalOrders(result, ordersClone, mainResultKey, settings, symbolsMap);
        OrdersList ordersSimulation = new OrdersList("MC orders simulation");
        for (int s = 0; s < this.numberOfSimulations; ++s) {
            this.initializeSimulatedOrders(ordersSimulation, ordersClone);
            for (m = 0; m < methods.size(); ++m) {
                ((MonteCarloManipulation)methods.get(m)).modifyTrades((IRandomGenerator)rng, ordersSimulation);
            }
            RobustnessResults rr = MCResultsComputer.computeResults((OrdersList)ordersSimulation, (SettingsMap)settings, (SymbolsMap)symbolsMap, (Result)result);
            if (rr.getOrdersValues().size() < 2) {
                Log.debug("MC manipulation job returned empty result");
                continue;
            }
            simulationResults.add(rr);
            result.addMCSimulation(this.getSettingName(), rr);
            if (this.backtestProgressListener == null) continue;
            this.backtestProgressListener.increaseProgressStep();
        }
        settings.removeIgnoredKeys(this.originalStatsKeys);
        result.set(this.getSettingName() + "_NumberOfSimulations", (Object)this.numberOfSimulations);
        String[] methodsStr = new String[methods.size()];
        for (m = 0; m < methods.size(); ++m) {
            methodsStr[m] = ((MonteCarloManipulation)methods.get(m)).printFormatedName();
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

    private void initializeSimulatedOrders(OrdersList ordersSimulation, OrdersList ordersClone) {
        int diff;
        int i;
        int ordersToCopy = Math.min(ordersSimulation.size(), ordersClone.size());
        for (i = 0; i < ordersToCopy; ++i) {
            ordersSimulation.get(i).setFromOrder(ordersClone.get(i));
        }
        if (ordersSimulation.size() < ordersClone.size()) {
            for (i = ordersToCopy; i < ordersClone.size(); ++i) {
                ordersSimulation.add(new Order(ordersClone.get(i)));
            }
        }
        if ((diff = ordersSimulation.size() - ordersClone.size()) > 0) {
            for (int i2 = 0; i2 < diff; ++i2) {
                ordersSimulation.remove(ordersSimulation.size() - 1);
            }
        }
    }

    public int getNumberOfSimulations() {
        return this.numberOfSimulations;
    }

    public boolean doesRetest() {
        return false;
    }

    public boolean doesForEverySetup() {
        return false;
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
        settings = settings + "\n";
        ArrayList methods = ProjectConfigHelper.getMonteCarloManipulationMethods((Element)settingsEl.getChild("Methods"));
        for (int i = 0; i < methods.size(); ++i) {
            MonteCarloManipulation method = (MonteCarloManipulation)methods.get(i);
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
        return 10030;
    }
}

