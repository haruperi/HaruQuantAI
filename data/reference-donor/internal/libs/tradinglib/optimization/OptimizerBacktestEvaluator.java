/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.backtest.TradingOptionsModifier;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IFitnessEvaluator;
import com.strategyquant.tradinglib.optimization.OptimizationIndexes;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.StrategyParamData;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.io.Serializable;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizerBacktestEvaluator
implements IFitnessEvaluator<OptimizationIndexes> {
    private static final Logger Log = LoggerFactory.getLogger((String)"OptimizerBacktestEvaluator");
    private BacktestSettings backtestSettings;
    private BacktestRunner backtestRunner;
    private StopPauseEngine parentStopPauseEngine;
    private OptimizationSettings optimizationSettings;
    private ILastEventListener lastEventListener;
    private final String lastSettingsXml;

    public OptimizerBacktestEvaluator(BacktestSettings backtestSettings, OptimizationSettings optimizationSettings, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener, String string) {
        this.backtestSettings = backtestSettings;
        this.parentStopPauseEngine = stopPauseEngine;
        this.optimizationSettings = optimizationSettings;
        this.lastEventListener = iLastEventListener;
        this.lastSettingsXml = string;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public OptimizationIndexes evaluateCandidate(OptimizationIndexes optimizationIndexes, int n, GridJob gridJob, boolean bl) {
        ResultsGroup resultsGroup;
        Element element;
        String string;
        Serializable serializable;
        String string2;
        block14: {
            BacktestResult backtestResult;
            block13: {
                GPIDs gPIDs = optimizationIndexes.getGPIDs();
                string2 = String.format("%s - Optimization %d.%d.%d", this.backtestSettings.strategyName, gPIDs.islandIndex, gPIDs.generationIndex, gPIDs.nodeIndex);
                Log.debug("--- Job {} started", (Object)string2);
                serializable = StrategyBase.createXmlStrategy(this.backtestSettings.elStrategy, "temp");
                StrategyParamData strategyParamData = StrategyBase.createStrategyVariation((StrategyBase)serializable, this.optimizationSettings, this.optimizationSettings.transformToFullIndexes(optimizationIndexes.getIndexes()));
                StrategyBase strategyBase = strategyParamData.getStrategy();
                string = strategyParamData.getParams();
                Element element2 = strategyBase.getStrategyXml();
                element = this.backtestSettings.lastSettings != null ? this.backtestSettings.lastSettings.clone() : null;
                try {
                    TradingOptionsModifier.modifyTradingOptions(this.backtestSettings.tradingOptions, element2, element);
                }
                catch (Exception exception) {
                    Log.error("Cannot modify trading options", (Throwable)exception);
                }
                this.backtestRunner = new BacktestRunner(this.backtestSettings, this.parentStopPauseEngine, gridJob, false, this.lastEventListener, this.lastSettingsXml);
                this.backtestRunner.setStrategyName(string2);
                this.backtestRunner.setStrategy(element2);
                backtestResult = this.backtestRunner.execute(n);
                int n2 = backtestResult.getDismissalReason();
                String string3 = backtestResult.getDismissalMessage();
                if (string3 == null) break block13;
                optimizationIndexes.setError(n2, string3, null);
                OptimizationIndexes optimizationIndexes2 = optimizationIndexes;
                return optimizationIndexes2;
            }
            resultsGroup = backtestResult.getResult();
            if (resultsGroup != null) break block14;
            optimizationIndexes.setError(10001, "No dismissal message, but ResultsGroup was null in BacktestResult", null);
            Log.error("No dismissal message, but ResultsGroup was null in BacktestResult");
            OptimizationIndexes optimizationIndexes3 = optimizationIndexes;
            return optimizationIndexes3;
        }
        try {
            double d = resultsGroup.portfolio().getFitness((byte)10);
            resultsGroup.specialValues().setString("OptimizationParameters", string);
            resultsGroup.specialValues().set("OptimizationParametersArray", (Object)optimizationIndexes.getIndexes());
            if (element != null) {
                resultsGroup.setLastSettings(XMLUtil.elementToString((Element)element));
            }
            optimizationIndexes.setFitness(d, (byte)0);
            optimizationIndexes.setResult(resultsGroup);
            OptimizationIndexes optimizationIndexes4 = optimizationIndexes;
            return optimizationIndexes4;
        }
        catch (Exception exception) {
            string2 = exception.getMessage();
            if (string2 == null) {
                Log.info("Exception in optimizer backtest", (Throwable)exception);
                optimizationIndexes.setError(10001, String.format("Exception in backtest: NullPointerException", exception.getMessage()), exception);
            } else if (!(string2.contains("Index out of range") || string2.contains("Undefined type:") || string2.contains("Invalid MA type used") || string2.contains("Invalid PriceField value") || string2.contains("Invalid Signal Strength"))) {
                Log.info("Exception in optimizer backtest " + string2, (Throwable)exception);
                optimizationIndexes.setError(10001, String.format("Exception in backtest: %s", exception.getMessage()), exception);
            } else {
                optimizationIndexes.setError(10013, String.format("Exception in backtest: %s", exception.getMessage()), exception);
            }
            serializable = optimizationIndexes;
            return serializable;
        }
    }

    public OptimizerBacktestEvaluator getClone() throws Exception {
        OptimizerBacktestEvaluator optimizerBacktestEvaluator = new OptimizerBacktestEvaluator(this.backtestSettings.getClone(), this.optimizationSettings, this.parentStopPauseEngine, this.lastEventListener, this.lastSettingsXml);
        return optimizerBacktestEvaluator;
    }

    @Override
    public void destroy() {
        if (this.backtestRunner != null) {
            this.backtestRunner.stop();
        }
    }

    @Override
    public void stop() {
    }
}

