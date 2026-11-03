/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractCrossover<T extends IGPNode>
implements IEvolutionaryOperator<T> {
    public static final Logger Log = LoggerFactory.getLogger((String)"AbstractCrossover");
    private final int crossoverPoints;
    private final double crossoverProbability;

    protected AbstractCrossover(int n) {
        this(n, 1.0);
    }

    protected AbstractCrossover(int n, double d) {
        this.crossoverPoints = n;
        this.crossoverProbability = d;
        if (n <= 0) {
            throw new IllegalArgumentException("Number of cross-over points must be positive.");
        }
    }

    @Override
    public List<T> apply(List<T> list, IRandomGenerator iRandomGenerator, AbstractFactory<T> abstractFactory, int n, int n2) {
        ArrayList<T> arrayList = new ArrayList<T>(list);
        Collections.shuffle(arrayList, iRandomGenerator.getRandom());
        ArrayList<IGPNode> arrayList2 = new ArrayList<IGPNode>(list.size());
        Iterator iterator = arrayList.iterator();
        while (iterator.hasNext()) {
            IGPNode iGPNode = (IGPNode)iterator.next();
            if (iterator.hasNext()) {
                IGPNode iGPNode2 = (IGPNode)iterator.next();
                int n3 = iRandomGenerator.probability(this.crossoverProbability) ? (this.crossoverPoints == 1 ? 1 : 1 + iRandomGenerator.nextInt(this.crossoverPoints)) : 0;
                if (n3 > 0) {
                    arrayList2.addAll(this.mate(iGPNode, iGPNode2, n3, iRandomGenerator, n, n2));
                    continue;
                }
                arrayList2.add(iGPNode);
                arrayList2.add(iGPNode2);
                continue;
            }
            arrayList2.add(iGPNode);
        }
        return arrayList2;
    }

    protected abstract List<T> mate(T var1, T var2, int var3, IRandomGenerator var4, int var5, int var6);
}

