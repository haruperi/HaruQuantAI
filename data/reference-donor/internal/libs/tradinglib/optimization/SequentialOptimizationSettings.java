/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ValuesMap
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.ValuesMap;
import com.strategyquant.tradinglib.optimization.OptimizationParams;

public class SequentialOptimizationSettings {
    public int distributionUp;
    public int distributionDown;
    public int steps;
    public boolean applyToStrategy;
    public ValuesMap paramTypes;
    public boolean symmetry;
    public OptimizationParams manualParams;
    public int pctToPass;
    public int stableAreaCount;
    public int stabilityRangePct;

    public SequentialOptimizationSettings clone() {
        SequentialOptimizationSettings sequentialOptimizationSettings = new SequentialOptimizationSettings();
        sequentialOptimizationSettings.distributionUp = this.distributionUp;
        sequentialOptimizationSettings.distributionDown = this.distributionDown;
        sequentialOptimizationSettings.steps = this.steps;
        sequentialOptimizationSettings.paramTypes = this.paramTypes != null ? this.paramTypes.clone() : null;
        sequentialOptimizationSettings.symmetry = this.symmetry;
        sequentialOptimizationSettings.manualParams = this.manualParams != null ? this.manualParams.clone() : null;
        sequentialOptimizationSettings.applyToStrategy = this.applyToStrategy;
        sequentialOptimizationSettings.pctToPass = this.pctToPass;
        sequentialOptimizationSettings.stableAreaCount = this.stableAreaCount;
        sequentialOptimizationSettings.stabilityRangePct = this.stabilityRangePct;
        return sequentialOptimizationSettings;
    }
}

