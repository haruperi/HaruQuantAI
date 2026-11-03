/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.blocks;

public class BlockCategoryInfo {
    public int categoryNameHash;
    public int categoryOrder;
    public String categoryName;

    public BlockCategoryInfo(String string, int n) {
        this.categoryName = string;
        this.categoryNameHash = string.hashCode();
        this.categoryOrder = n;
    }
}

