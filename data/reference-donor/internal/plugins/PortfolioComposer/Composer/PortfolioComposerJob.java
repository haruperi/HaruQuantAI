/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.tradinglib.ResultsGroup
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposer;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings;
import com.strategyquant.tradinglib.ResultsGroup;
import java.io.Serializable;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioComposerJob
extends GridJob<ResultsGroup> {
    public static final Logger Log = LoggerFactory.getLogger(PortfolioComposerJob.class);
    private String portfolioName;
    private Map<String, Serializable> params;
    private PortfolioComposer composer = new PortfolioComposer();
    private PortfolioComposerSettings settings;
    private Double[] weights;

    public PortfolioComposerJob(String jobID, Map<String, Serializable> params) throws Exception {
        super(jobID, 1, params);
        this.portfolioName = (String)((Object)params.get("StrategyName"));
        this.settings = (PortfolioComposerSettings)params.get("OptimizationSettings");
        this.settings = (PortfolioComposerSettings)params.get("OptimizationSettings");
        this.weights = (Double[])params.get("Weights");
    }

    public ResultsGroup call() throws Exception {
        ResultsGroup rg = this.composer.recalculate(this.portfolioName, this.settings, this.weights);
        return rg;
    }

    public void messageReceived(GridMessage message) {
        if (message.getMessageID() == 4) {
            this.composer.stop();
        }
    }
}

