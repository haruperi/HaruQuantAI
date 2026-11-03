/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.optimization.BadOptimizationParamsException;
import com.strategyquant.tradinglib.optimization.NonexistingVariableException;
import com.strategyquant.tradinglib.optimization.OptimizationException;
import com.strategyquant.tradinglib.optimization.Parameter;
import java.util.ArrayList;

public class OptimizationParams
extends ArrayList<Parameter> {
    public static final String TXT_MISCONFIGURATION_NOPARAMS = "Misconfiguration - no parameter was chosen to be optimized";
    ArrayList<Parameter> usedParams = null;

    public Parameter addParam(String string, byte by, boolean bl, double d, double d2, double d3, double d4) {
        Parameter parameter = new Parameter(string, by, bl, d, d2, d3, d4);
        this.add(parameter);
        this.usedParams = null;
        return parameter;
    }

    public void addParam(Parameter parameter) {
        this.add(parameter);
        this.usedParams = null;
    }

    public long getTotalCombinations() {
        long l = 1L;
        for (int i = 0; i < this.size(); ++i) {
            Parameter parameter = (Parameter)this.get(i);
            if (!parameter.use) continue;
            l *= (long)parameter.getCombinationsCount();
        }
        if (l <= 0L) {
            l = 1000000L;
        }
        return l;
    }

    public double getValue(int n, String string) throws NonexistingVariableException, OptimizationException {
        for (int i = 0; i < this.size(); ++i) {
            Parameter parameter = (Parameter)this.get(i);
            if (!parameter.getName().equals(string)) continue;
            return parameter.getValueByIndex(n);
        }
        throw new NonexistingVariableException(String.format("Variable '%s' doesn't exist!", string));
    }

    public int verify() throws BadOptimizationParamsException {
        long l = 1L;
        int n = 0;
        for (int i = 0; i < this.size(); ++i) {
            Parameter parameter = (Parameter)this.get(i);
            if (parameter.use) {
                ++n;
            }
            if (parameter.type != 2 && (parameter.start < parameter.stop ? parameter.start + parameter.step < parameter.start : parameter.start + parameter.step > parameter.start)) {
                throw new BadOptimizationParamsException(String.format("Misconfiguration of values for '%s'. Start: %f, Stop: %f, Step: %f", parameter.name, parameter.start, parameter.stop, parameter.step));
            }
            if (parameter.getCombinationsCount() > 1000) {
                throw new BadOptimizationParamsException(String.format("Misconfiguration (too many steps) of values for '%s'. Start: %f, Stop: %f, Step: %f", parameter.name, parameter.start, parameter.stop, parameter.step));
            }
            l *= (long)parameter.getCombinationsCount();
        }
        if (n == 0) {
            // empty if block
        }
        return n;
    }

    public int getUsedCount() {
        int n = 0;
        for (int i = 0; i < this.size(); ++i) {
            Parameter parameter = (Parameter)this.get(i);
            if (!parameter.use) continue;
            ++n;
        }
        return n;
    }

    public void prepareTestParameters(long l, short[] sArray) {
        int n;
        long l2 = this.getTotalCombinations();
        if (l >= l2) {
            l = l2 - 1L;
        }
        for (int i = 0; i < sArray.length; ++i) {
            sArray[i] = 0;
        }
        long l3 = l;
        for (int i = sArray.length - 1; i >= 0 && l3 > 0L; l3 -= (long)(sArray[i] * n), --i) {
            n = this.getPositionCoef(i);
            double d = (double)l3 / (double)n;
            if (!(d > 0.0)) continue;
            sArray[i] = (short)d;
        }
    }

    private int getPositionCoef(int n) {
        int n2;
        int n3 = 1;
        if (this.usedParams == null) {
            this.usedParams = new ArrayList();
            for (n2 = 0; n2 < this.size(); ++n2) {
                if (!((Parameter)this.get((int)n2)).use) continue;
                this.usedParams.add((Parameter)this.get(n2));
            }
        }
        n2 = 0;
        for (int i = 0; i < n; ++i) {
            n3 *= this.usedParams.get(i).getCombinationsCount();
            ++n2;
        }
        return n3;
    }

    @Override
    public OptimizationParams clone() {
        OptimizationParams optimizationParams = new OptimizationParams();
        for (int i = 0; i < this.size(); ++i) {
            optimizationParams.add(((Parameter)this.get(i)).clone());
        }
        return optimizationParams;
    }
}

