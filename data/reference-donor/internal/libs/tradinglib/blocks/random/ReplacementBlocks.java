/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.blocks.random.ReplacementBlock;
import com.strategyquant.tradinglib.generator.GenerateException;
import java.util.ArrayList;

public class ReplacementBlocks
extends ArrayList<ReplacementBlock> {
    private ArrayList<ReplacementBlock> blocksWithNoChildren = new ArrayList();
    private int cummulativeWeight = 0;
    private int cummulativeWeightBNC = 0;

    @Override
    public boolean add(ReplacementBlock replacementBlock) {
        this.cummulativeWeight += replacementBlock.weight;
        if (!replacementBlock.hasBlockChildren()) {
            this.cummulativeWeightBNC += replacementBlock.weight;
            this.blocksWithNoChildren.add(replacementBlock);
        }
        return super.add(replacementBlock);
    }

    public ReplacementBlock chooseRandomly(IRandomGenerator iRandomGenerator, int n) throws GenerateException {
        if (this.size() == 1) {
            return (ReplacementBlock)this.get(0);
        }
        if (n > 5 && this.blocksWithNoChildren.size() > 0) {
            return this.choose(iRandomGenerator, this.cummulativeWeightBNC, this.blocksWithNoChildren);
        }
        return this.choose(iRandomGenerator, this.cummulativeWeight, this);
    }

    private ReplacementBlock choose(IRandomGenerator iRandomGenerator, int n, ArrayList<ReplacementBlock> arrayList) throws GenerateException {
        int n2 = iRandomGenerator.nextInt(n);
        int n3 = 0;
        for (ReplacementBlock replacementBlock : arrayList) {
            if (n2 >= (n3 += replacementBlock.weight)) continue;
            return replacementBlock;
        }
        throw new GenerateException("No block found, index: " + n2 + ", cummWeight: " + n);
    }
}

