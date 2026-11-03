/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.Negater;
import com.strategyquant.tradinglib.StrategyBase;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NegatersList
extends ObjectArrayList<Negater> {
    public static final Logger Log = LoggerFactory.getLogger((String)"NegatersList");

    public IBlock negate(IBlock iBlock, StrategyBase strategyBase) throws BlockDefinitionException {
        int n;
        int n2;
        try {
            n2 = Blocks.getBlockType(iBlock);
            n = Blocks.getReturnType(iBlock);
        }
        catch (Exception exception) {
            throw new BlockDefinitionException("Cannot get block type!", exception);
        }
        for (int i = 0; i < this.size(); ++i) {
            IBlock iBlock2;
            Negater negater = (Negater)this.get(i);
            Log.debug("- Using negater : " + negater.getClass().getSimpleName() + " for block " + iBlock.getClass().getSimpleName());
            try {
                iBlock2 = negater.negate(this, iBlock, n2, n, strategyBase);
            }
            catch (BlockDefinitionException blockDefinitionException) {
                Log.info(" - Negater " + negater.getClass().getSimpleName() + " exception, continuing.", (Throwable)blockDefinitionException);
                return null;
            }
            if (iBlock2 == null) continue;
            return iBlock2;
        }
        throw new BlockDefinitionException("No Negater worked for block '" + iBlock.getClass().getSimpleName() + "'");
    }
}

