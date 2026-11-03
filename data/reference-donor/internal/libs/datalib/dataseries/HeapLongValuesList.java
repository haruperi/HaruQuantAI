/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.longs.LongArrayList
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.dataseries.ILongValuesList;
import it.unimi.dsi.fastutil.longs.LongArrayList;

public class HeapLongValuesList
implements ILongValuesList {
    private LongArrayList values = null;

    public HeapLongValuesList(int n) {
        this.values = new LongArrayList(n);
    }

    @Override
    public long getLong(int n) {
        return this.values.getLong(n);
    }

    @Override
    public int size() {
        return this.values.size();
    }

    @Override
    public void setLong(int n, long l) {
        this.values.set(n, l);
    }

    @Override
    public void addLong(long l) {
        this.values.add(l);
    }

    @Override
    public void clear() {
        this.values.clear();
    }
}

