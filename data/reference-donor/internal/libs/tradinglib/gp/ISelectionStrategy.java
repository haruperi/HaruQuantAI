/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.util.List;

public interface ISelectionStrategy<T extends IGPNode> {
    public <T extends IGPNode> List<T> select(List<T> var1, boolean var2, int var3, IRandomGenerator var4, List<T> var5);
}

