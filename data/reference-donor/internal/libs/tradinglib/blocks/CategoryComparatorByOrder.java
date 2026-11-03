/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.tradinglib.blocks.BlockCategoryInfo;
import java.util.Comparator;

public class CategoryComparatorByOrder
implements Comparator<BlockCategoryInfo> {
    @Override
    public int compare(BlockCategoryInfo blockCategoryInfo, BlockCategoryInfo blockCategoryInfo2) {
        if (blockCategoryInfo.categoryOrder > blockCategoryInfo2.categoryOrder) {
            return 1;
        }
        if (blockCategoryInfo.categoryOrder < blockCategoryInfo2.categoryOrder) {
            return -1;
        }
        return 0;
    }
}

