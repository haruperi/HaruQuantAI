/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.blocks.random.ItemRandomValueRanges;
import com.strategyquant.tradinglib.blocks.random.ReplacementChartConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameter;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameters;
import com.strategyquant.tradinglib.generator.GenerateException;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ReplacementParameterGroups
extends ArrayList<ReplacementParameters> {
    public static final Logger Log = LoggerFactory.getLogger((String)"ReplacementParameter");
    private int cummulativeWeight = 0;
    private int minShift = Integer.MIN_VALUE;
    private int maxShift = Integer.MIN_VALUE;
    private int minPeriod = Integer.MIN_VALUE;
    private int maxPeriod = Integer.MIN_VALUE;

    @Override
    public boolean add(ReplacementParameters replacementParameters) {
        this.cummulativeWeight += replacementParameters.weight;
        if (replacementParameters.generationType == 1) {
            this.recognizeMinMaxShiftPeriod(replacementParameters);
        }
        return super.add(replacementParameters);
    }

    private void recognizeMinMaxShiftPeriod(ReplacementParameters replacementParameters) {
        for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
            if (replacementParameter.blockParam.key.contains("#Period") && replacementParameter.generation == 2) {
                this.minPeriod = (int)replacementParameter.blockParam.minValue;
                this.maxPeriod = (int)replacementParameter.blockParam.maxValue;
                continue;
            }
            if (!replacementParameter.blockParam.key.contains("#Shift") || replacementParameter.generation != 2) continue;
            this.minShift = (int)replacementParameter.blockParam.minValue;
            this.maxShift = (int)replacementParameter.blockParam.maxValue;
        }
    }

    public ReplacementParameters chooseRandomly(IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        if (this.size() == 1) {
            return (ReplacementParameters)this.get(0);
        }
        int n = 100;
        while (n > 0) {
            --n;
            int n2 = iRandomGenerator.nextInt(this.cummulativeWeight);
            int n3 = 0;
            for (ReplacementParameters replacementParameters : this) {
                if (n2 >= (n3 += replacementParameters.weight) || n > 1 && (!this.checkParamPeriodShiftRangesMatch(replacementParameters, replacementChartConfig) || !this.checkRandomValueAndGeneration(replacementParameters, itemRandomValueRanges))) continue;
                return replacementParameters;
            }
        }
        throw new GenerateException("No replacement parameters group found, cummWeight: " + this.cummulativeWeight);
    }

    private boolean checkRandomValueAndGeneration(ReplacementParameters replacementParameters, ItemRandomValueRanges itemRandomValueRanges) {
        if (itemRandomValueRanges == null || replacementParameters.parameters == null) {
            return true;
        }
        for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
            String string = itemRandomValueRanges.getForParam(replacementParameter.blockParam.key);
            if (string == null || replacementParameter.generation != 1) continue;
            return false;
        }
        return true;
    }

    private boolean checkParamPeriodShiftRangesMatch(ReplacementParameters replacementParameters, ReplacementChartConfig replacementChartConfig) {
        if (this.minPeriod == Integer.MIN_VALUE && this.maxPeriod == Integer.MIN_VALUE && this.minShift == Integer.MIN_VALUE && this.maxShift == Integer.MIN_VALUE) {
            return true;
        }
        for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
            int n;
            if (replacementParameter.blockParam.key.contains("#Period") && replacementParameter.generation == 1) {
                if (this.minPeriod != Integer.MIN_VALUE) {
                    n = this.minPeriod;
                    if (this.minPeriod == -1000003) {
                        n = replacementChartConfig.minPeriod;
                    }
                    if (replacementParameter.blockParam.iDefaultValue < n) {
                        return false;
                    }
                }
                if (this.maxPeriod == Integer.MIN_VALUE) continue;
                n = this.maxPeriod;
                if (this.maxPeriod == -1000004) {
                    n = replacementChartConfig.maxPeriod;
                }
                if (replacementParameter.blockParam.iDefaultValue <= n) continue;
                return false;
            }
            if (!replacementParameter.blockParam.key.contains("#Shift") || replacementParameter.generation != 2) continue;
            if (this.minShift != Integer.MIN_VALUE) {
                n = this.minShift;
                if (this.minShift == -1000001) {
                    n = replacementChartConfig.minShift;
                }
                if (replacementParameter.blockParam.iDefaultValue < n) {
                    return false;
                }
            }
            if (this.maxShift == Integer.MIN_VALUE) continue;
            n = this.maxShift;
            if (this.maxShift == -1000002) {
                n = replacementChartConfig.maxShift;
            }
            if (replacementParameter.blockParam.iDefaultValue <= n) continue;
            return false;
        }
        return true;
    }

    public ReplacementParameter getChartParam() {
        ReplacementParameters replacementParameters = (ReplacementParameters)this.get(0);
        if (replacementParameters != null) {
            return replacementParameters.getChartParam();
        }
        return null;
    }
}

