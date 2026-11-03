/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.HideDatabankChoice
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.MetricForFitness
 *  com.strategyquant.tradinglib.results.stats.StatsComputer
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.FitnessMethod.impl.StrategyResult;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.HideDatabankChoice;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import jakarta.servlet.Servlet;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tamas Takacs")
@Name(name="Fitness Function StrategyResult plugin")
@Category(name="FitnessFunction")
@License(text="")
@ShortDesc(text="Short description")
@HideDatabankChoice
@PluginImplementation
public class FitnessMethodStrategyResult
implements IFitnessFunction,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(FitnessMethodStrategyResult.class);
    private ServletContextHandler dataContext;
    private String databankColumnName = null;
    private ArrayList<Goal> weightedGoals = new ArrayList();

    public FitnessMethodStrategyResult() {
    }

    public FitnessMethodStrategyResult(String databankColumnName) {
        this.databankColumnName = databankColumnName;
    }

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODEAlgoWizardStandalone";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public double computeFitness(ResultsGroup results, byte direction, byte sampleType) throws Exception {
        return this.computeFitness(results, direction, sampleType, true);
    }

    public double computeFitness(ResultsGroup results, byte direction, byte sampleType, boolean useRatioByTrades) throws Exception {
        if (this.databankColumnName.equals("Weighted")) {
            double fitness = this.computeWeightedFitness(results, direction, sampleType, useRatioByTrades);
            if (fitness == 0.0) {
                return this.getFitnessValue(results, direction, sampleType, "NetProfit", 0.0, (byte)0, useRatioByTrades);
            }
            return fitness;
        }
        return this.getFitnessValue(results, direction, sampleType, this.databankColumnName, 0.0, (byte)0, useRatioByTrades);
    }

    private double getFitnessValue(ResultsGroup results, byte direction, byte sampleType, String databankColumnName, double target, byte valueType, boolean useRatioByTrades) throws Exception {
        double val;
        DatabankColumn c = (DatabankColumn)DatabankColumns.get().findClassByName(databankColumnName);
        double fitness = c.transformToFitnessRange(val = c.getNumericValue(results, results.getMainResultKey(), direction, (byte)10, sampleType), target, valueType);
        if (fitness < 0.0) {
            fitness = 0.0;
        }
        if (fitness > 1.0) {
            fitness = 1.0;
        }
        if (!useRatioByTrades) {
            return fitness;
        }
        SQStats stats = results.mainResult().statsOrNull((byte)0, (byte)10, sampleType);
        int trades = 0;
        if (stats != null) {
            trades = stats.getInt("NumberOfTrades");
        }
        if (trades < 20) {
            fitness *= 0.3;
        } else if (trades < 30) {
            fitness *= 0.4;
        } else if (trades < 50) {
            fitness *= 0.6;
        } else if (trades < 70) {
            fitness *= 0.8;
        } else if (trades < 100) {
            fitness *= 0.85;
        } else if (trades < 150) {
            fitness *= 0.9;
        }
        return fitness;
    }

    private double computeWeightedFitness(ResultsGroup results, byte direction, byte sampleType, boolean useRatioByTrades) throws Exception {
        float totalWeight = 0.0f;
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            if (!this.weightedGoals.get((int)i).use) continue;
            totalWeight = (float)((double)totalWeight + this.weightedGoals.get((int)i).weight);
        }
        float weightedFitness = 0.0f;
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            Goal goal = this.weightedGoals.get(i);
            if (!goal.use) continue;
            double rankingFitness = this.getFitnessValue(results, direction, sampleType, goal.statsValueName, goal.target, goal.valueType, useRatioByTrades);
            weightedFitness = (float)((double)weightedFitness + goal.weight / (double)totalWeight * rankingFitness);
        }
        return weightedFitness;
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
            try {
                if (!goal.use) continue;
                DatabankColumn c = (DatabankColumn)DatabankColumns.get().findClassByName(goal.statsValueName);
                this.weightedGoals.add(goal);
            }
            catch (Exception e) {
                Log.error("Ranking Criterium SKIPPED. Reason: ", (Throwable)e);
            }
        }
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/fitnessMethodStrategyResult/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new FitnessMethodStrategyResultServlet()), "/*");
        }
        return this.dataContext;
    }

    public byte getFitnessType() throws Exception {
        if (this.databankColumnName.equals("Weighted")) {
            return 1;
        }
        return ((DatabankColumn)DatabankColumns.get().findClassByName((String)this.databankColumnName)).valueType;
    }

    public String getFitnessKey() {
        return "ComputeFromStrategyResult";
    }

    public String getFitnessName() {
        return L.tsq((String)"Main data backtest");
    }

    public String getFitnessDatabankColumnName() {
        return this.databankColumnName;
    }

    public ArrayList<DatabankColumn> getUsedStatValues() throws NonexistingCustomClassException {
        ArrayList<DatabankColumn> columnsUsed = new ArrayList<DatabankColumn>();
        if (!this.databankColumnName.equals("Weighted")) {
            columnsUsed.add((DatabankColumn)DatabankColumns.get().findClassByName(this.databankColumnName));
        } else {
            for (int i = 0; i < this.weightedGoals.size(); ++i) {
                Goal goal = this.weightedGoals.get(i);
                if (!goal.use) continue;
                columnsUsed.add((DatabankColumn)DatabankColumns.get().findClassByName(goal.statsValueName));
            }
        }
        return StatsComputer.getAllDependentStatValues(columnsUsed);
    }

    public String printWeightedGoals() {
        String goals = "";
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            Goal goal = this.weightedGoals.get(i);
            if (!goal.use) continue;
            goals = goals + this.weightedGoals.get((int)i).statsValueName;
            if (i >= this.weightedGoals.size() - 1) continue;
            goals = goals + ", ";
        }
        return goals;
    }

    public ArrayList<MetricForFitness> getMetricsForFitness() {
        ArrayList<MetricForFitness> metrics = new ArrayList<MetricForFitness>();
        if (this.databankColumnName.equals("Weighted")) {
            for (int i = 0; i < this.weightedGoals.size(); ++i) {
                Goal goal = this.weightedGoals.get(i);
                if (!goal.use) continue;
                MetricForFitness m = new MetricForFitness();
                m.metric = this.weightedGoals.get((int)i).statsValueName;
                m.weight = this.weightedGoals.get((int)i).weight;
                m.valueType = this.weightedGoals.get((int)i).valueType;
                m.target = this.weightedGoals.get((int)i).target;
                metrics.add(m);
            }
        } else {
            MetricForFitness m = new MetricForFitness();
            m.metric = this.databankColumnName;
            m.weight = 1.0;
            m.valueType = 1;
            m.target = 0.0;
            metrics.add(m);
        }
        return metrics;
    }

    public double getMetricValue(ResultsGroup results, byte direction, byte sampleType, String databankColumnName) throws Exception {
        DatabankColumn c = (DatabankColumn)DatabankColumns.get().findClassByName(databankColumnName);
        double val = c.getNumericValue(results, results.getMainResultKey(), direction, (byte)10, sampleType);
        return val;
    }

    public IFitnessFunction clone() {
        FitnessMethodStrategyResult obj = new FitnessMethodStrategyResult();
        obj.dataContext = this.dataContext;
        obj.databankColumnName = this.databankColumnName;
        obj.weightedGoals = this.cloneGoals();
        return obj;
    }

    private ArrayList<Goal> cloneGoals() {
        ArrayList<Goal> newWeightedGoals = new ArrayList<Goal>();
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            Goal g = this.weightedGoals.get(i);
            Goal gNew = new Goal();
            gNew.valueType = g.valueType;
            gNew.use = g.use;
            gNew.statsValueName = g.statsValueName;
            gNew.weight = g.weight;
            gNew.target = g.target;
            newWeightedGoals.add(gNew);
        }
        return newWeightedGoals;
    }

    private class Goal {
        public byte valueType;
        public boolean use;
        public String statsValueName;
        public double weight;
        public double target;

        private Goal() {
        }
    }
}

