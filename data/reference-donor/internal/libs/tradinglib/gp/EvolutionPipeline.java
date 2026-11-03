/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

public class EvolutionPipeline<T extends IGPNode>
implements IEvolutionaryOperator<T>,
Serializable {
    private final List<IEvolutionaryOperator<T>> pipeline;

    public EvolutionPipeline(List<IEvolutionaryOperator<T>> list) {
        if (list.isEmpty()) {
            throw new IllegalArgumentException("Pipeline must contain at least one operator.");
        }
        this.pipeline = new ArrayList<IEvolutionaryOperator<T>>(list);
    }

    @Override
    public List<T> apply(List<T> list, IRandomGenerator iRandomGenerator, AbstractFactory<T> abstractFactory, int n, int n2) throws Exception {
        List<T> list2 = list;
        for (IEvolutionaryOperator<T> iEvolutionaryOperator : this.pipeline) {
            list2 = iEvolutionaryOperator.apply(list2, iRandomGenerator, abstractFactory, n, n2);
        }
        int n3 = list2.size();
        for (int i = 0; i < list2.size(); ++i) {
            IGPNode iGPNode = (IGPNode)list2.get(i);
            GPIDs gPIDs = iGPNode.getGPIDs();
            if (gPIDs.nodeIndex >= 0) continue;
            gPIDs.nodeIndex = n3++;
        }
        return list2;
    }
}

