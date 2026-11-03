/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.gp.GPEvolutionMessage;
import com.strategyquant.tradinglib.gp.GPEvolutionPopulationMessage;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.io.Serializable;

public interface IGPEvolutionMessagesListener<T extends IGPNode> {
    public void newCandidate(T var1);

    public void evolutionMessage(GPEvolutionMessage var1);

    public void lastPopulation(GPEvolutionPopulationMessage var1);

    public void evolutionException(Serializable var1);
}

