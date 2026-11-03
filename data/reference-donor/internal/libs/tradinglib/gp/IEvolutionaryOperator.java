/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.util.List;

public interface IEvolutionaryOperator<T extends IGPNode> {
    public List<T> apply(List<T> var1, IRandomGenerator var2, AbstractFactory<T> var3, int var4, int var5) throws Exception;
}

