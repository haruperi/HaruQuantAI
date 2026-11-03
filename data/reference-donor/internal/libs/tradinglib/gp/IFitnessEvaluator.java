/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.io.Serializable;

public interface IFitnessEvaluator<T extends IGPNode>
extends Serializable,
ISQCloneable<IFitnessEvaluator<? super T>> {
    public T evaluateCandidate(T var1, int var2, GridJob var3, boolean var4);

    public void destroy();

    public void stop();
}

