/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.SortOrder;
import java.util.Comparator;

public class BlockComparatorByOrder
implements Comparator<IBlock> {
    @Override
    public int compare(IBlock iBlock, IBlock iBlock2) {
        int n;
        int n2 = this.getOrder(iBlock);
        if (n2 > (n = this.getOrder(iBlock2))) {
            return 1;
        }
        if (n2 < n) {
            return -1;
        }
        return 0;
    }

    private int getOrder(IBlock iBlock) {
        Class<?> clazz = iBlock.getClass();
        SortOrder sortOrder = clazz.getAnnotation(SortOrder.class);
        if (sortOrder == null) {
            return 100;
        }
        return sortOrder.value();
    }
}

