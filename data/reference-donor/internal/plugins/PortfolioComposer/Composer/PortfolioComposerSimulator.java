/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.simplegrid.SimpleGridEngine
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposer;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerChart;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerJob;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerResultsSender;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import java.io.Serializable;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioComposerSimulator {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioComposerSimulator.class);
    private SQProject project;
    private PortfolioComposerSettings settings;
    private PortfolioComposerResultsSender sender;
    private boolean autocomputation;
    private int numberOfSimulations;
    private double jobCounter = 0.0;
    private int lastIndex;
    private StopPauseEngine stopPauseEngine;
    public ArrayList<Double[]> weightCombinations;

    public void start(SQProject project, PortfolioComposerSettings settings, PortfolioComposerResultsSender sender, StopPauseEngine stopPauseEngine, boolean autocomputation) {
        this.project = project;
        this.settings = settings;
        this.sender = sender;
        this.stopPauseEngine = stopPauseEngine;
        this.autocomputation = autocomputation;
        this._start();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _start() {
        try {
            this.stopPauseEngine.start();
            ResultsGroup result = null;
            if (this.autocomputation) {
                this.updateUIProgress(1, L.t((String)"Preparing simulations, please wait...", (Object[])new Object[0]));
                this.weightCombinations = this.calculateWeightCombinations();
                this.numberOfSimulations = this.weightCombinations.size();
                ArrayList<ResultsGroup> simulationResults = this.runOnGrid(false);
                result = this.selectOptimalPortfolio(simulationResults);
                simulationResults.clear();
            } else {
                this.updateUIProgress(50, L.t((String)"Calculating portfolio, please wait...", (Object[])new Object[0]));
                String strategyName = "Portfolio-" + System.currentTimeMillis();
                PortfolioComposer composer = new PortfolioComposer();
                result = composer.recalculate(strategyName, this.settings, this.settings.weights.toArray(new Double[this.settings.weights.size()]));
            }
            this.addBestPortfolioToDatabank(result);
            this.updateUI(result);
        }
        catch (Exception e) {
            Log.error("Error while computing portfolio.", (Throwable)e);
            this.updateUI("Error while computing portfolio. " + e.getMessage());
        }
        finally {
            this.stopPauseEngine.finish();
        }
    }

    private ArrayList<Double[]> calculateWeightCombinations() {
        ArrayList<Double[]> weights = new ArrayList<Double[]>();
        SecureRandom secureRandom = new SecureRandom();
        int seedSize = 20;
        byte[] seed = secureRandom.generateSeed(seedSize);
        secureRandom.setSeed(seed);
        int stepSize = 1;
        int maxStep = 100 / stepSize;
        int minWeight = 1;
        int baseAllocation = 0;
        if (minWeight * this.settings.weights.size() < 80) {
            baseAllocation = minWeight * this.settings.weights.size();
        } else {
            minWeight = 0;
        }
        for (int simulation = 0; simulation < this.settings.maxSimulations; ++simulation) {
            int i;
            Double[] weightCombination = new Double[this.settings.weights.size()];
            int remainingStep = maxStep - baseAllocation / stepSize;
            for (i = 0; i < weightCombination.length; ++i) {
                weightCombination[i] = minWeight;
            }
            i = 0;
            while (i < this.settings.weights.size() - 1) {
                int maxAvailableStep = Math.max(0, remainingStep);
                int randomStep = secureRandom.nextInt(maxAvailableStep + 1);
                Double[] doubleArray = weightCombination;
                int n = i++;
                Double.valueOf(doubleArray[n] + (double)(randomStep * stepSize));
                remainingStep -= randomStep;
            }
            Double[] doubleArray = weightCombination;
            int n = this.settings.weights.size() - 1;
            Double.valueOf(doubleArray[n] + (double)(remainingStep * stepSize));
            weights.add(weightCombination);
        }
        return weights;
    }

    private ArrayList<ResultsGroup> runOnGrid(boolean singleThreaded) throws Exception {
        final ArrayList<ResultsGroup> simulationResults = new ArrayList<ResultsGroup>();
        this.lastIndex = 0;
        this.jobCounter = 0.0;
        SimpleGridEngine<PortfolioComposerJob, ResultsGroup> gridEngine = new SimpleGridEngine<PortfolioComposerJob, ResultsGroup>(this, this.stopPauseEngine, null, singleThreaded){
            final /* synthetic */ PortfolioComposerSimulator this$0;
            {
                this.this$0 = this$0;
                super(arg0, arg1, arg2);
            }

            protected ArrayList<PortfolioComposerJob> createJobsBatch(int jobsToCreate, GridClient gridClient) throws Exception {
                return this.this$0.createBatch(jobsToCreate, gridClient, this.this$0.numberOfSimulations);
            }

            protected void processResult(ResultsGroup rg, JobDetails jobDetails) throws Exception {
                this.this$0.processJobResult(rg, jobDetails, simulationResults);
            }

            protected void onError(String errorMsg, Exception exception) {
                Log.error("PortfolioSimulation Error {}, Exception ", (Object)errorMsg, (Object)exception);
            }
        };
        gridEngine.start();
        gridEngine.unregisterListeners();
        return simulationResults;
    }

    private ResultsGroup selectOptimalPortfolio(ArrayList<ResultsGroup> simulationResults) {
        int numberOfTrades;
        String PortfolioResultKey;
        double SharpeRatio;
        int i1;
        Log.info(String.format("Select the best portfolio from %d.", simulationResults.size()));
        this.numberOfSimulations = 0;
        for (int i12 = 0; i12 < simulationResults.size(); ++i12) {
            double StdDeviation = Double.valueOf(simulationResults.get(i12).specialValues().getString(SpecialValues.PortfolioComposerStdDeviation, null)) * 100.0;
            if (StdDeviation == 0.0) continue;
            ++this.numberOfSimulations;
        }
        PortfolioComposerChart chartData = new PortfolioComposerChart(this.numberOfSimulations);
        chartData.labelMinimumRiskPortfolio = "Minimum Risk Portfolio";
        chartData.labelOptimalPortfolio = "Optimal Portfolio";
        int BestPortfolio = -1;
        int MinimumRiskPortfolio = -1;
        chartData.decimals = this.settings.getDecimalsByFitness();
        double MinimumStdDevPortofolio = Double.MAX_VALUE;
        double AverageStdDevPortofolio = 0.0;
        int simulationNum = 0;
        for (int i13 = 0; i13 < simulationResults.size(); ++i13) {
            double StdDeviation = Double.valueOf(simulationResults.get(i13).specialValues().getString(SpecialValues.PortfolioComposerStdDeviation, null)) * 100.0;
            if (StdDeviation == 0.0) continue;
            AverageStdDevPortofolio += StdDeviation;
            double PortfolioReturns = Double.valueOf(simulationResults.get(i13).specialValues().getString(SpecialValues.PortfolioComposerDailyExpectedReturnPct, null)) * 100.0;
            chartData.weights[simulationNum] = "";
            String weights1 = simulationResults.get(i13).specialValues().getString(SpecialValues.PortfolioComposerWeights, null);
            weights1 = weights1.replaceAll("[\\[\\]]", "");
            String[] values = weights1.split(",");
            for (int i2 = 0; i2 < values.length; ++i2) {
                double value1 = Double.parseDouble(values[i2].trim());
                if (i2 < this.weightCombinations.get(i13).length - 1) {
                    int n = simulationNum;
                    chartData.weights[n] = chartData.weights[n] + SQUtils.d2String((double)value1, (int)0) + ",";
                    continue;
                }
                int n = simulationNum;
                chartData.weights[n] = chartData.weights[n] + SQUtils.d2String((double)value1, (int)0);
            }
            if (StdDeviation < MinimumStdDevPortofolio) {
                MinimumStdDevPortofolio = StdDeviation;
                MinimumRiskPortfolio = simulationNum;
            }
            ++simulationNum;
        }
        AverageStdDevPortofolio = simulationNum > 0 ? (AverageStdDevPortofolio /= (double)simulationNum) : 100.0;
        PortfolioComposerSettings.PortfolioSelectionType cfr_ignored_0 = this.settings.PortfolioSelectionType;
        if (this.settings.PortfolioSelectionType == PortfolioComposerSettings.PortfolioSelectionType.SharpeRatio) {
            chartData.labelTitle = "Minimum Variance Frontier";
            chartData.labelX = "Standard Deviation of Daily Returns";
            chartData.labelY = "Expected Daily Returns";
            double BestSharpeRatio = -999999.0;
            simulationNum = 0;
            for (i1 = 0; i1 < simulationResults.size(); ++i1) {
                SharpeRatio = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerSharpeRatio, null));
                if (SharpeRatio == -1.0) continue;
                double StdDeviation = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerStdDeviation, null)) * 100.0;
                double PortfolioReturns = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerDailyExpectedReturnPct, null)) * 100.0;
                BigDecimal bdStdDeviation = new BigDecimal(StdDeviation).setScale(4, RoundingMode.HALF_UP);
                BigDecimal bdPortfolioReturns = new BigDecimal(PortfolioReturns).setScale(4, RoundingMode.HALF_UP);
                chartData.x[simulationNum] = bdStdDeviation.doubleValue();
                chartData.y[simulationNum] = bdPortfolioReturns.doubleValue();
                if (SharpeRatio > BestSharpeRatio && StdDeviation <= AverageStdDevPortofolio) {
                    BestSharpeRatio = SharpeRatio;
                    BestPortfolio = i1;
                    chartData.bestX = bdStdDeviation.doubleValue();
                    chartData.bestY = bdPortfolioReturns.doubleValue();
                }
                if (i1 == MinimumRiskPortfolio) {
                    chartData.MinimumRiskPortofolioX = bdStdDeviation.doubleValue();
                    chartData.MinimumRiskPortofolioY = bdPortfolioReturns.doubleValue();
                }
                ++simulationNum;
            }
        }
        PortfolioComposerSettings.PortfolioSelectionType cfr_ignored_1 = this.settings.PortfolioSelectionType;
        if (this.settings.PortfolioSelectionType == PortfolioComposerSettings.PortfolioSelectionType.ReturnDrawdownRatio) {
            chartData.labelTitle = "Return vs Drawdown";
            chartData.labelX = "Net Profit $";
            chartData.labelY = "Drawdown $";
            double BestReturn_DD = -9999999.0;
            simulationNum = 0;
            for (i1 = 0; i1 < simulationResults.size(); ++i1) {
                SharpeRatio = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerSharpeRatio, null));
                if (SharpeRatio == -1.0) continue;
                try {
                    PortfolioResultKey = "Portfolio";
                    SQStats Stats1 = simulationResults.get(i1).subResult(PortfolioResultKey).statsOrNull((byte)0, (byte)10, (byte)127);
                    double netProfit = Stats1.getDouble("NetProfit");
                    double DD = Math.abs(Stats1.getDouble("Drawdown"));
                    numberOfTrades = Stats1.getInt("NumberOfTrades");
                    netProfit = (double)Math.round(netProfit * 100.0) / 100.0;
                    DD = (double)Math.round(DD * 100.0) / 100.0;
                    chartData.x[simulationNum] = netProfit;
                    chartData.y[simulationNum] = DD;
                    if (numberOfTrades < 10) continue;
                    if (DD == 0.0) {
                        if (netProfit == 0.0) continue;
                        if (BestReturn_DD < 10.0) {
                            BestReturn_DD = 10.0;
                        }
                    }
                    if (SQUtils.safeDivide((double)netProfit, (double)DD) > BestReturn_DD) {
                        BestReturn_DD = SQUtils.round2((double)SQUtils.safeDivide((double)netProfit, (double)DD));
                        BestPortfolio = i1;
                        chartData.bestX = netProfit;
                        chartData.bestY = DD;
                    }
                    if (i1 == MinimumRiskPortfolio) {
                        chartData.MinimumRiskPortofolioX = netProfit;
                        chartData.MinimumRiskPortofolioY = DD;
                    }
                }
                catch (Exception e) {
                    Log.error("Exc.", (Throwable)e);
                }
                ++simulationNum;
            }
        }
        PortfolioComposerSettings.PortfolioSelectionType cfr_ignored_2 = this.settings.PortfolioSelectionType;
        if (this.settings.PortfolioSelectionType == PortfolioComposerSettings.PortfolioSelectionType.CAGRMaxDrawdownRatio) {
            chartData.labelTitle = "Compound Annual Growth Rate vs Drawdown";
            chartData.labelX = "CAGR %";
            chartData.labelY = "Max Drawdown %";
            double BestCAGR_MaxDD = -9999999.0;
            simulationNum = 0;
            for (i1 = 0; i1 < simulationResults.size(); ++i1) {
                SharpeRatio = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerSharpeRatio, null));
                if (SharpeRatio == -1.0) continue;
                try {
                    PortfolioResultKey = "Portfolio";
                    SQStats Stats1 = simulationResults.get(i1).subResult(PortfolioResultKey).statsOrNull((byte)0, (byte)10, (byte)127);
                    double CAGR = Stats1.getDouble("CAGR");
                    double DDPct = Stats1.getDouble("DrawdownPct");
                    numberOfTrades = Stats1.getInt("NumberOfTrades");
                    CAGR = (double)Math.round(CAGR * 100.0) / 100.0;
                    DDPct = (double)Math.round(DDPct * 100.0) / 100.0;
                    chartData.x[simulationNum] = CAGR;
                    chartData.y[simulationNum] = DDPct;
                    if (numberOfTrades < 10) continue;
                    if (DDPct == 0.0) {
                        if (CAGR == 0.0) continue;
                        if (BestCAGR_MaxDD < 10.0) {
                            BestCAGR_MaxDD = 10.0;
                        }
                    }
                    if (SQUtils.safeDivide((double)CAGR, (double)DDPct) > BestCAGR_MaxDD) {
                        BestCAGR_MaxDD = SQUtils.round2((double)SQUtils.safeDivide((double)CAGR, (double)DDPct));
                        BestPortfolio = i1;
                        chartData.bestX = CAGR;
                        chartData.bestY = DDPct;
                    }
                    if (i1 == MinimumRiskPortfolio) {
                        chartData.MinimumRiskPortofolioX = CAGR;
                        chartData.MinimumRiskPortofolioY = DDPct;
                    }
                }
                catch (Exception e) {
                    Log.error("Exc.", (Throwable)e);
                }
                ++simulationNum;
            }
        }
        PortfolioComposerSettings.PortfolioSelectionType cfr_ignored_3 = this.settings.PortfolioSelectionType;
        if (this.settings.PortfolioSelectionType == PortfolioComposerSettings.PortfolioSelectionType.CAGRMeanDrawdownRatio) {
            chartData.labelTitle = "Compound Annual Growth Rate vs Average Drawdown";
            chartData.labelX = "CAGR %";
            chartData.labelY = "Avg Drawdown %";
            double BestCAGR_MeanDD = -9999999.0;
            simulationNum = 0;
            for (i1 = 0; i1 < simulationResults.size(); ++i1) {
                SharpeRatio = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerSharpeRatio, null));
                if (SharpeRatio == -1.0) continue;
                try {
                    PortfolioResultKey = "Portfolio";
                    SQStats Stats1 = simulationResults.get(i1).subResult(PortfolioResultKey).statsOrNull((byte)0, (byte)10, (byte)127);
                    double CAGR = Stats1.getDouble("CAGR");
                    double AvgDD = Math.abs(Stats1.getDouble("AvgPctDrawdown"));
                    numberOfTrades = Stats1.getInt("NumberOfTrades");
                    CAGR = (double)Math.round(CAGR * 100.0) / 100.0;
                    AvgDD = (double)Math.round(AvgDD * 100.0) / 100.0;
                    chartData.x[simulationNum] = CAGR;
                    chartData.y[simulationNum] = AvgDD;
                    if (numberOfTrades < 10) continue;
                    if (AvgDD == 0.0) {
                        if (CAGR == 0.0) continue;
                        if (BestCAGR_MeanDD < 10.0) {
                            BestCAGR_MeanDD = 10.0;
                        }
                    }
                    if (SQUtils.safeDivide((double)CAGR, (double)AvgDD) > BestCAGR_MeanDD) {
                        BestCAGR_MeanDD = SQUtils.round2((double)SQUtils.safeDivide((double)CAGR, (double)AvgDD));
                        BestPortfolio = i1;
                        chartData.bestX = CAGR;
                        chartData.bestY = AvgDD;
                    }
                    if (i1 == MinimumRiskPortfolio) {
                        chartData.MinimumRiskPortofolioX = CAGR;
                        chartData.MinimumRiskPortofolioY = AvgDD;
                    }
                }
                catch (Exception e) {
                    Log.error("Exc.", (Throwable)e);
                }
                ++simulationNum;
            }
        }
        PortfolioComposerSettings.PortfolioSelectionType cfr_ignored_4 = this.settings.PortfolioSelectionType;
        if (this.settings.PortfolioSelectionType == PortfolioComposerSettings.PortfolioSelectionType.NetProfit) {
            chartData.labelTitle = "Return vs Drawdown";
            chartData.labelX = "Net Profit $";
            chartData.labelY = "Drawdown $";
            double BestNetProfit = -9999999.0;
            simulationNum = 0;
            for (i1 = 0; i1 < simulationResults.size(); ++i1) {
                SharpeRatio = Double.valueOf(simulationResults.get(i1).specialValues().getString(SpecialValues.PortfolioComposerSharpeRatio, null));
                if (SharpeRatio == -1.0) continue;
                try {
                    PortfolioResultKey = "Portfolio";
                    SQStats Stats1 = simulationResults.get(i1).subResult(PortfolioResultKey).statsOrNull((byte)0, (byte)10, (byte)127);
                    double netProfit = Stats1.getDouble("NetProfit");
                    double DD = Math.abs(Stats1.getDouble("Drawdown"));
                    netProfit = (double)Math.round(netProfit * 100.0) / 100.0;
                    DD = (double)Math.round(DD * 100.0) / 100.0;
                    chartData.x[simulationNum] = netProfit;
                    chartData.y[simulationNum] = DD;
                    if (netProfit > BestNetProfit) {
                        BestNetProfit = netProfit;
                        BestPortfolio = i1;
                        chartData.bestX = netProfit;
                        chartData.bestY = DD;
                    }
                    if (i1 == MinimumRiskPortfolio) {
                        chartData.MinimumRiskPortofolioX = netProfit;
                        chartData.MinimumRiskPortofolioY = DD;
                    }
                }
                catch (Exception e) {
                    Log.error("Exc.", (Throwable)e);
                }
                ++simulationNum;
            }
        }
        if (BestPortfolio == -1) {
            BestPortfolio = 0;
            chartData.bestX = 0.0;
            chartData.bestY = 0.0;
        }
        ResultsGroup rg = simulationResults.get(BestPortfolio);
        rg.specialValues().set(SpecialValues.PortfolioComposerChart, (Object)chartData.toJsonString());
        return rg;
    }

    protected void processJobResult(ResultsGroup rg, JobDetails jobDetails, ArrayList<ResultsGroup> simulationResults) {
        String taskName = jobDetails.getJobID();
        if (jobDetails.isSuccess()) {
            simulationResults.add(rg);
        } else {
            jobDetails.getException();
            Log.error(String.format("Simulation %s failed, error: %s", taskName, jobDetails.getException()));
        }
        this.jobCounter += 1.0;
        int pct = Double.valueOf(this.jobCounter / (double)this.numberOfSimulations * 100.0).intValue();
        this.updateUIProgress(pct, L.t((String)"Finished simulation %d/%d", (Object[])new Object[]{(int)this.jobCounter, this.numberOfSimulations}));
    }

    protected ArrayList<PortfolioComposerJob> createBatch(int jobsToCreate, GridClient gridClient, long totalCombinations) throws Exception {
        ArrayList<PortfolioComposerJob> jobsGroup = new ArrayList<PortfolioComposerJob>();
        int jobsAdded = 0;
        for (int i = this.lastIndex; i < this.lastIndex + jobsToCreate && (long)i < totalCombinations; ++i) {
            if (this.stopPauseEngine.isStopped()) {
                throw new TaskStoppedException();
            }
            String strategyName = String.format("Portfolio-%d", i);
            PortfolioComposerJob job = new PortfolioComposerJob("portfolio-composer-simulation-" + i, this.getJobParams(i, strategyName));
            jobsGroup.add(job);
            ++jobsAdded;
        }
        this.lastIndex += jobsAdded;
        if (jobsGroup.size() == 0) {
            return null;
        }
        return jobsGroup;
    }

    private Map<String, Serializable> getJobParams(int simulationNumber, String strategyName) {
        HashMap<String, Serializable> params = new HashMap<String, Serializable>();
        params.put("StrategyName", (Serializable)((Object)strategyName));
        params.put("OptimizationSettings", this.settings);
        params.put("Weights", (Serializable)this.weightCombinations.get(simulationNumber));
        return params;
    }

    private void addBestPortfolioToDatabank(ResultsGroup result) throws Exception {
        try {
            Databank databankOutput = (Databank)this.project.getDatabanks().get((Object)"Portfolios");
            if (databankOutput == null) {
                this.project.getDatabanks().add("Portfolios");
            }
            databankOutput = (Databank)this.project.getDatabanks().get((Object)"Portfolios");
            databankOutput.clearRecords(true, true, "PortfolioComposer output");
            databankOutput.add(result, false);
        }
        catch (Exception e) {
            throw new Exception("Failed to add the best portfolio to the output databank.", e);
        }
    }

    private void updateUIProgress(int pct, String message) {
        this.sender.progress(pct, message);
    }

    private void updateUI(String error) {
        this.updateUI(null, error);
    }

    private void updateUI(ResultsGroup result) {
        this.updateUI(result, null);
    }

    private void updateUI(ResultsGroup result, String error) {
        JSONObject data = new JSONObject();
        if (result != null) {
            data.put("strategyName", (Object)result.getName());
            data.put("weights", (Object)result.specialValues().getString(SpecialValues.PortfolioComposerWeights, null));
        }
        if (error != null) {
            data.put("error", (Object)error);
        }
        data.put("progress", 100);
        this.sender.sendData(data);
    }
}

