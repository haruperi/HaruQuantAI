/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.fitnessfunction;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import java.io.Serializable;
import java.util.ArrayList;
import org.jdom2.Element;

public interface IFitnessFunction
extends ISQPlugin,
Serializable {
    public static final String ComputeFromStrategyResult = "ComputeFromStrategyResult";

    public double computeFitness(ResultsGroup var1, byte var2, byte var3) throws Exception;

    public double computeFitness(ResultsGroup var1, byte var2, byte var3, boolean var4) throws Exception;

    public String getFitnessKey();

    public String getFitnessName();

    public void initFitnessFromXml(Element var1);

    public byte getFitnessType() throws Exception;

    public String getFitnessDatabankColumnName();

    public ArrayList<DatabankColumn> getUsedStatValues() throws Exception;

    public String printWeightedGoals() throws Exception;

    public ArrayList<MetricForFitness> getMetricsForFitness();

    public double getMetricValue(ResultsGroup var1, byte var2, byte var3, String var4) throws Exception;

    public IFitnessFunction clone();
}

