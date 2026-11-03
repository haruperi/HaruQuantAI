/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.gp.FitnessCollectionData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TopStrategiesData {
    public static final Logger Log = LoggerFactory.getLogger(TopStrategiesData.class);
    public static int TOP_AVG_COUNT = 10;
    public static int TOP_STR_COUNT = 3;
    private double[][] topFitnesses = new double[5][TOP_AVG_COUNT];
    private double[] sumFitnesses = new double[5];
    private ResultsGroup[] topResults = new ResultsGroup[3];
    private double[] topResultsFitness = new double[3];
    private int fitnessesAdded;
    private int totalFitnessesAdded;

    public void reset() {
        int n;
        for (n = 0; n < 5; ++n) {
            for (int i = 0; i < this.topFitnesses.length; ++i) {
                this.topFitnesses[n][i] = 0.0;
                this.sumFitnesses[n] = 0.0;
            }
        }
        for (n = 0; n < this.topResults.length; ++n) {
            this.topResults[n] = null;
            this.topResultsFitness[n] = 0.0;
        }
        this.fitnessesAdded = 0;
        this.totalFitnessesAdded = 0;
    }

    public void updateWith(ResultsGroup resultsGroup) {
        this.updateFitnessWith(0, this.getFitness(resultsGroup, (byte)10), this.fitnessesAdded);
        this.updateFitnessWith(1, this.getFitness(resultsGroup, (byte)11), this.fitnessesAdded);
        this.updateFitnessWith(2, this.getFitness(resultsGroup, (byte)40), this.fitnessesAdded);
        this.updateFitnessWith(3, this.getFitness(resultsGroup, (byte)20), this.fitnessesAdded);
        boolean bl = this.updateFitnessWith(4, this.getFitness(resultsGroup, (byte)127), this.fitnessesAdded);
        if (this.fitnessesAdded < this.topFitnesses.length) {
            ++this.fitnessesAdded;
        }
        ++this.totalFitnessesAdded;
        if (bl) {
            this.updateTopStrategiesWith(resultsGroup, this.getFitness(resultsGroup, (byte)127));
        }
    }

    private boolean updateFitnessWith(int n, double d, int n2) {
        int n3 = n;
        this.sumFitnesses[n3] = this.sumFitnesses[n3] + d;
        if (n2 < this.topFitnesses.length) {
            this.topFitnesses[n][n2] = d;
            return true;
        }
        int n4 = 0;
        double d2 = Double.MAX_VALUE;
        for (int i = 0; i < this.topFitnesses.length; ++i) {
            if (!(this.topFitnesses[n][i] < d2)) continue;
            d2 = this.topFitnesses[n][i];
            n4 = i;
        }
        if (this.topFitnesses[n][n4] < d) {
            this.topFitnesses[n][n4] = d;
            return true;
        }
        return false;
    }

    private void updateTopStrategiesWith(ResultsGroup resultsGroup, double d) {
        double d2;
        int n;
        boolean bl = false;
        for (n = 0; n < this.topResults.length; ++n) {
            if (this.topResults[n] != null) continue;
            this.topResults[n] = resultsGroup;
            this.topResultsFitness[n] = d;
            bl = true;
            break;
        }
        if (!bl && d > (d2 = this.topResultsFitness[this.topResults.length - 1])) {
            this.topResults[this.topResults.length - 1] = resultsGroup;
            this.topResultsFitness[this.topResults.length - 1] = d;
        }
        for (n = this.topResults.length - 1; n > 0; --n) {
            if (this.topResults[n] == null || !(this.topResultsFitness[n] > this.topResultsFitness[n - 1])) continue;
            ResultsGroup resultsGroup2 = this.topResults[n];
            this.topResults[n] = this.topResults[n - 1];
            this.topResults[n - 1] = resultsGroup2;
            double d3 = this.topResultsFitness[n];
            this.topResultsFitness[n] = this.topResultsFitness[n - 1];
            this.topResultsFitness[n - 1] = d3;
        }
    }

    public ResultsGroup[] getTopResults() {
        return this.topResults;
    }

    private double getFitness(ResultsGroup resultsGroup, byte by) {
        try {
            double d = resultsGroup.portfolio().getFitness(by);
            return d > 0.0 ? d : 0.0;
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            return 0.0;
        }
    }

    public void updateDatabankFitnesses(FitnessCollectionData fitnessCollectionData) {
        this.getFitnesses(0, this.topFitnesses[0], fitnessCollectionData);
        this.getFitnesses(1, this.topFitnesses[1], fitnessCollectionData);
        this.getFitnesses(2, this.topFitnesses[2], fitnessCollectionData);
        this.getFitnesses(3, this.topFitnesses[3], fitnessCollectionData);
        this.getFitnesses(4, this.topFitnesses[4], fitnessCollectionData);
    }

    private void getFitnesses(int n, double[] dArray, FitnessCollectionData fitnessCollectionData) {
        if (this.fitnessesAdded == 0) {
            switch (n) {
                case 0: {
                    fitnessCollectionData.bestFitnessIS = 0.0;
                    fitnessCollectionData.topAvgFitnessIS = 0.0;
                    fitnessCollectionData.avgFitnessIS = 0.0;
                    break;
                }
                case 1: {
                    fitnessCollectionData.bestFitnessIST = 0.0;
                    fitnessCollectionData.topAvgFitnessIST = 0.0;
                    fitnessCollectionData.avgFitnessIST = 0.0;
                    break;
                }
                case 2: {
                    fitnessCollectionData.bestFitnessISV = 0.0;
                    fitnessCollectionData.topAvgFitnessISV = 0.0;
                    fitnessCollectionData.avgFitnessISV = 0.0;
                    break;
                }
                case 3: {
                    fitnessCollectionData.bestFitnessOOS = 0.0;
                    fitnessCollectionData.topAvgFitnessOOS = 0.0;
                    fitnessCollectionData.avgFitnessOOS = 0.0;
                    break;
                }
                case 4: {
                    fitnessCollectionData.bestFitnessFS = 0.0;
                    fitnessCollectionData.topAvgFitnessFS = 0.0;
                    fitnessCollectionData.avgFitnessFS = 0.0;
                }
            }
            return;
        }
        double d = 0.0;
        double d2 = -1.0;
        for (int i = 0; i < this.fitnessesAdded; ++i) {
            d += dArray[i];
            if (!(dArray[i] > d2)) continue;
            d2 = dArray[i];
        }
        switch (n) {
            case 0: {
                fitnessCollectionData.bestFitnessIS = d2;
                fitnessCollectionData.topAvgFitnessIS = d / (double)this.fitnessesAdded;
                fitnessCollectionData.avgFitnessIS = this.sumFitnesses[0] / (double)this.totalFitnessesAdded;
                break;
            }
            case 1: {
                fitnessCollectionData.bestFitnessIST = d2;
                fitnessCollectionData.topAvgFitnessIST = d / (double)this.fitnessesAdded;
                fitnessCollectionData.avgFitnessIST = this.sumFitnesses[1] / (double)this.totalFitnessesAdded;
                break;
            }
            case 2: {
                fitnessCollectionData.bestFitnessISV = d2;
                fitnessCollectionData.topAvgFitnessISV = d / (double)this.fitnessesAdded;
                fitnessCollectionData.avgFitnessISV = this.sumFitnesses[2] / (double)this.totalFitnessesAdded;
                break;
            }
            case 3: {
                fitnessCollectionData.bestFitnessOOS = d2;
                fitnessCollectionData.topAvgFitnessOOS = d / (double)this.fitnessesAdded;
                fitnessCollectionData.avgFitnessOOS = this.sumFitnesses[3] / (double)this.totalFitnessesAdded;
                break;
            }
            case 4: {
                fitnessCollectionData.bestFitnessFS = d2;
                fitnessCollectionData.topAvgFitnessFS = d / (double)this.fitnessesAdded;
                fitnessCollectionData.avgFitnessFS = this.sumFitnesses[4] / (double)this.totalFitnessesAdded;
            }
        }
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder("\nTOP STRS\n");
        for (int i = 0; i < this.topResults.length; ++i) {
            if (this.topResults[i] == null) continue;
            stringBuilder.append("#");
            stringBuilder.append(i);
            stringBuilder.append(this.topResults[i].getName());
            stringBuilder.append(" - ");
            stringBuilder.append(SQUtils.round2((double)this.topResultsFitness[i]));
            stringBuilder.append("\n");
        }
        stringBuilder.append("-----------------------------------");
        return stringBuilder.toString();
    }
}

