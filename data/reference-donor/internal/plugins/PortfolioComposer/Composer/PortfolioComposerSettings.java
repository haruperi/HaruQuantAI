/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import com.strategyquant.tradinglib.ResultsGroup;
import java.io.Serializable;
import java.util.ArrayList;

public class PortfolioComposerSettings
implements Serializable {
    public PortfolioSelectionType PortfolioSelectionType = com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings$PortfolioSelectionType.SharpeRatio;
    public boolean dateRangeLimited = false;
    public long startDay = 0L;
    public long endDay = 0L;
    public double initialCapital = 0.0;
    public int leverage = 1;
    public int decimals;
    public int maxSimulations = 100;
    public double confidenceLevel = 0.95;
    public double RiskFreeRate = 0.7;
    public ArrayList<ResultsGroup> strategies = new ArrayList();
    public ArrayList<Double> weights = new ArrayList();

    public void setSelectionTypeByString(String selectionType) throws Exception {
        switch (selectionType) {
            case "SharpRatio": {
                this.PortfolioSelectionType = com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings$PortfolioSelectionType.SharpeRatio;
                break;
            }
            case "ReturnDrawdownRatio": {
                this.PortfolioSelectionType = com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings$PortfolioSelectionType.ReturnDrawdownRatio;
                break;
            }
            case "CAGRMaxDrawdownRatio": {
                this.PortfolioSelectionType = com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings$PortfolioSelectionType.CAGRMaxDrawdownRatio;
                break;
            }
            case "CAGRMeanDrawdownRatio": {
                this.PortfolioSelectionType = com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings$PortfolioSelectionType.CAGRMeanDrawdownRatio;
                break;
            }
            case "NetProfit": {
                this.PortfolioSelectionType = com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings$PortfolioSelectionType.NetProfit;
                break;
            }
            default: {
                throw new Exception("Invalid PortfolioSelectionType: " + selectionType);
            }
        }
    }

    public int getDecimalsByFitness() {
        switch (this.PortfolioSelectionType.ordinal()) {
            case 0: {
                return 3;
            }
            case 2: 
            case 3: {
                return 2;
            }
        }
        return 0;
    }

    public static enum PortfolioSelectionType {
        SharpeRatio,
        ReturnDrawdownRatio,
        CAGRMaxDrawdownRatio,
        CAGRMeanDrawdownRatio,
        NetProfit;

    }
}

