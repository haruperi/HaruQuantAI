/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import java.util.Comparator;

public class FitnessMetricComparator
implements Comparator<ResultsGroup> {
    private final MetricForFitness metric;
    private final IFitnessFunction fitnessFunction;

    public FitnessMetricComparator(MetricForFitness metricForFitness, IFitnessFunction iFitnessFunction) {
        this.metric = metricForFitness;
        this.fitnessFunction = iFitnessFunction;
    }

    @Override
    public int compare(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        try {
            double d = this.fitnessFunction.getMetricValue(resultsGroup, (byte)0, (byte)10, this.metric.metric);
            double d2 = this.fitnessFunction.getMetricValue(resultsGroup2, (byte)0, (byte)10, this.metric.metric);
            if (this.metric.valueType == 1) {
                if (d < d2) {
                    return 1;
                }
                if (d > d2) {
                    return -1;
                }
            } else if (this.metric.valueType == 2) {
                if (d < d2) {
                    return -1;
                }
                if (d > d2) {
                    return 1;
                }
            } else {
                if ((d = Math.abs(d - this.metric.target)) < (d2 = Math.abs(d2 - this.metric.target))) {
                    return -1;
                }
                if (d > d2) {
                    return 1;
                }
            }
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
        return 0;
    }
}

