/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.GeneticInfo;
import com.strategyquant.tradinglib.TimeSeries;
import com.strategyquant.tradinglib.TimeSeriesLineChart;
import com.strategyquant.tradinglib.XYLineChart;
import com.strategyquant.tradinglib.charts.linechart.series.XYSeries;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import com.strategyquant.tradinglib.gp.FitnessCollectionData;
import com.strategyquant.tradinglib.gp.GPFitnessEvolutionData;
import com.strategyquant.tradinglib.project.SQProject;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FitnessEvolution {
    public static final Logger Log = LoggerFactory.getLogger(FitnessEvolution.class);
    private SQProject project;
    private DatabankChart[] databankCharts = new DatabankChart[3];
    private IslandCharts[] islandCharts = null;
    private boolean geneticBuild;

    public FitnessEvolution(SQProject sQProject) {
        this.project = sQProject;
        this.databankCharts[0] = new DatabankChart(L.tsq((String)"In Sample Training"));
        this.databankCharts[1] = new DatabankChart(L.tsq((String)"In Sample Validation"));
        this.databankCharts[2] = new DatabankChart(L.tsq((String)"Out of sample"));
    }

    public boolean isGeneticBuild() {
        return this.geneticBuild;
    }

    public JSONObject print() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("geneticBuild", this.geneticBuild);
        if (this.isGeneticBuild()) {
            GeneticInfo geneticInfo = this.project.getGeneticInfo();
            GPFitnessEvolutionData[] gPFitnessEvolutionDataArray = geneticInfo.getIslandsEvoData();
            JSONArray jSONArray = new JSONArray();
            for (int i = 0; i < gPFitnessEvolutionDataArray.length && i != 30; ++i) {
                if (gPFitnessEvolutionDataArray[i] == null) continue;
                JSONObject jSONObject2 = new JSONObject().put("generation", gPFitnessEvolutionDataArray[i].generation).put("population", gPFitnessEvolutionDataArray[i].populationSize);
                if (i < this.islandCharts.length) {
                    jSONObject2.put("chart", (Object)new JSONArray().put((Object)this.islandCharts[i].fitness[0].toJSON()).put((Object)this.islandCharts[i].fitness[1].toJSON()).put((Object)this.islandCharts[i].fitness[2].toJSON()));
                }
                jSONArray.put((Object)jSONObject2);
            }
            jSONObject.put("islands", (Object)jSONArray);
        }
        jSONObject.put("databank", (Object)new JSONArray().put((Object)this.databankCharts[0].toJSON()).put((Object)this.databankCharts[1].toJSON()).put((Object)this.databankCharts[2].toJSON()));
        return jSONObject;
    }

    public synchronized void addNextIslansEvodData(GPFitnessEvolutionData[] gPFitnessEvolutionDataArray, boolean bl) {
        GPFitnessEvolutionData gPFitnessEvolutionData;
        for (int i = 0; i < gPFitnessEvolutionDataArray.length && (gPFitnessEvolutionData = gPFitnessEvolutionDataArray[i]) != null && i < this.islandCharts.length; ++i) {
            FitnessCollectionData[] fitnessCollectionDataArray = gPFitnessEvolutionData.generationData;
            IslandCharts islandCharts = this.islandCharts[gPFitnessEvolutionData.islandIndex];
            int n = 0;
            if (islandCharts.lastGenerationIndex == gPFitnessEvolutionDataArray[i].generation) continue;
            if (islandCharts.lastGenerationIndex < gPFitnessEvolutionDataArray[i].generation) {
                n = islandCharts.lastGenerationIndex;
            }
            if (n < 0) {
                n = 0;
            }
            for (int j = n; j < gPFitnessEvolutionDataArray[i].generation + 1; ++j) {
                String string = j + "";
                if (fitnessCollectionDataArray[j] == null) break;
                if (islandCharts.fitness[0].bestSeries.values.size() > 0 && ((XYValue)islandCharts.fitness[0].bestSeries.values.get((int)(islandCharts.fitness[0].bestSeries.values.size() - 1))).xLabel.equals(string)) continue;
                islandCharts.fitness[0].bestSeries.addValue(j, fitnessCollectionDataArray[j].bestFitnessIST, string);
                islandCharts.fitness[0].topAvgSeries.addValue(j, fitnessCollectionDataArray[j].topAvgFitnessIST, string);
                islandCharts.fitness[0].avgSeries.addValue(j, fitnessCollectionDataArray[j].avgFitnessIST, string);
                islandCharts.fitness[1].bestSeries.addValue(j, fitnessCollectionDataArray[j].bestFitnessISV, string);
                islandCharts.fitness[1].topAvgSeries.addValue(j, fitnessCollectionDataArray[j].topAvgFitnessISV, string);
                islandCharts.fitness[1].avgSeries.addValue(j, fitnessCollectionDataArray[j].avgFitnessISV, string);
                islandCharts.fitness[2].bestSeries.addValue(j, fitnessCollectionDataArray[j].bestFitnessOOS, string);
                islandCharts.fitness[2].topAvgSeries.addValue(j, fitnessCollectionDataArray[j].topAvgFitnessOOS, string);
                islandCharts.fitness[2].avgSeries.addValue(j, fitnessCollectionDataArray[j].avgFitnessOOS, string);
            }
            islandCharts.lastGenerationIndex = gPFitnessEvolutionDataArray[i].generation;
        }
    }

    public void addNextValue() {
        try {
            Databank databank = this.project.getResultsDatabank();
            if (databank == null) {
                return;
            }
            if (!this.project.isRunning()) {
                return;
            }
            this.addValueFromDatabank(databank);
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
    }

    private void addValueFromDatabank(Databank databank) {
        FitnessCollectionData fitnessCollectionData = databank.getFitnessData();
        long l = System.currentTimeMillis();
        if (fitnessCollectionData.bestFitnessIST != 0.0 || fitnessCollectionData.topAvgFitnessIST != 0.0 || fitnessCollectionData.avgFitnessIST != 0.0) {
            this.databankCharts[0].bestSeries.addValue(l, fitnessCollectionData.bestFitnessIST);
            this.databankCharts[0].topAvgSeries.addValue(l, fitnessCollectionData.topAvgFitnessIST);
            this.databankCharts[0].avgSeries.addValue(l, fitnessCollectionData.avgFitnessIST);
        } else if (fitnessCollectionData.bestFitnessISV == 0.0) {
            this.databankCharts[0].bestSeries.addValue(l, fitnessCollectionData.bestFitnessIS);
            this.databankCharts[0].topAvgSeries.addValue(l, fitnessCollectionData.topAvgFitnessIS);
            this.databankCharts[0].avgSeries.addValue(l, fitnessCollectionData.avgFitnessIS);
        } else {
            this.databankCharts[0].bestSeries.addValue(l, 0.0);
            this.databankCharts[0].topAvgSeries.addValue(l, 0.0);
            this.databankCharts[0].avgSeries.addValue(l, 0.0);
        }
        this.databankCharts[1].bestSeries.addValue(l, fitnessCollectionData.bestFitnessISV);
        this.databankCharts[1].topAvgSeries.addValue(l, fitnessCollectionData.topAvgFitnessISV);
        this.databankCharts[1].avgSeries.addValue(l, fitnessCollectionData.avgFitnessISV);
        this.databankCharts[2].bestSeries.addValue(l, fitnessCollectionData.bestFitnessOOS);
        this.databankCharts[2].topAvgSeries.addValue(l, fitnessCollectionData.topAvgFitnessOOS);
        this.databankCharts[2].avgSeries.addValue(l, fitnessCollectionData.avgFitnessOOS);
    }

    public void reset(boolean bl, int n) {
        this.geneticBuild = bl;
        if (n > 20) {
            n = 20;
        }
        if (bl) {
            this.islandCharts = new IslandCharts[n];
            for (int i = 0; i < n; ++i) {
                this.islandCharts[i] = new IslandCharts();
                this.islandCharts[i].fitness[0] = new IslandChart("In Sample Training");
                this.islandCharts[i].fitness[1] = new IslandChart("In Sample Validation");
                this.islandCharts[i].fitness[2] = new IslandChart("Out of sample");
            }
        } else {
            this.islandCharts = null;
        }
    }

    private class DatabankChart {
        public TimeSeriesLineChart chart = new TimeSeriesLineChart();
        public TimeSeries bestSeries = null;
        public TimeSeries topAvgSeries = null;
        public TimeSeries avgSeries = null;

        public DatabankChart(String string) {
            this.chart.title = string;
            this.chart.yAxisRangeMin = 0.0;
            this.chart.yAxisRangeMax = 1.0;
            this.chart.maxXTicksLimit = 4;
            this.chart.showLegend = true;
            this.bestSeries = new TimeSeries(L.t((String)"Top Strategy", (Object[])new Object[0]), 1000);
            this.bestSeries.color = "#008000";
            this.chart.addSeries(this.bestSeries);
            this.topAvgSeries = new TimeSeries(L.t((String)"Top Ten Avg", (Object[])new Object[0]), 1000);
            this.topAvgSeries.color = "#383CE8";
            this.chart.addSeries(this.topAvgSeries);
            this.avgSeries = new TimeSeries(L.t((String)"All Avg", (Object[])new Object[0]), 1000);
            this.avgSeries.color = "#E8383C";
            this.chart.addSeries(this.avgSeries);
        }

        public JSONObject toJSON() {
            return this.chart.toJSON();
        }
    }

    private class IslandCharts {
        public int lastGenerationIndex = -1;
        public IslandChart[] fitness = new IslandChart[3];

        private IslandCharts() {
        }
    }

    private class IslandChart {
        public XYLineChart chart = new XYLineChart();
        public XYSeries bestSeries = null;
        public XYSeries topAvgSeries = null;
        public XYSeries avgSeries = null;

        public IslandChart(String string) {
            this.chart.title = string;
            this.chart.yAxisRangeMin = 0.0;
            this.chart.yAxisRangeMax = 1.0;
            this.chart.pointRadius = 3;
            this.chart.showLegend = true;
            this.chart.categoryAxis = true;
            this.bestSeries = new XYSeries(L.tsq((String)"Top Strategy"), 30);
            this.bestSeries.color = "#008000";
            this.chart.addSeries(this.bestSeries);
            this.topAvgSeries = new XYSeries(L.tsq((String)"Top 10 Avg"), 30);
            this.topAvgSeries.color = "#383CE8";
            this.chart.addSeries(this.topAvgSeries);
            this.avgSeries = new XYSeries(L.tsq((String)"All Avg"), 30);
            this.avgSeries.color = "#E8383C";
            this.chart.addSeries(this.avgSeries);
        }

        public JSONObject toJSON() {
            JSONObject jSONObject = this.chart.toJSON();
            JSONArray jSONArray = new JSONArray();
            for (int i = 0; i < this.chart.getSeries((int)0).values.size(); ++i) {
                if (!((XYValue)this.chart.getSeries((int)0).values.get((int)i)).xLabel.equals("0")) continue;
                jSONArray.put(i);
            }
            if (jSONArray.length() > 0) {
                jSONObject.put("lineAtIndex", (Object)jSONArray);
            }
            return jSONObject;
        }
    }
}

