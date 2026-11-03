/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.optimization.OptimizationIndexes;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.Parameter;
import org.jdom2.Element;

public class OptimizationIndexesFactory
extends AbstractFactory<OptimizationIndexes> {
    private OptimizationParams parameters;

    public OptimizationIndexesFactory(OptimizationParams optimizationParams) {
        this.parameters = optimizationParams;
    }

    @Override
    public OptimizationIndexes generateRandomCandidate(IRandomGenerator iRandomGenerator) throws Exception {
        int n = this.parameters.getUsedCount();
        short[] sArray = new short[n];
        int n2 = 0;
        for (int i = 0; i < this.parameters.size(); ++i) {
            Parameter parameter = (Parameter)this.parameters.get(i);
            if (!parameter.isUsed()) continue;
            sArray[n2] = (short)iRandomGenerator.nextInt(((Parameter)this.parameters.get(i)).getCombinationsCount());
            ++n2;
        }
        return new OptimizationIndexes(sArray);
    }

    @Override
    public AbstractFactory<OptimizationIndexes> clone() {
        return new OptimizationIndexesFactory(this.parameters);
    }

    @Override
    public void destroy() {
    }

    @Override
    public Element mutateATM(Element element, IRandomGenerator iRandomGenerator) throws Exception {
        return null;
    }
}

