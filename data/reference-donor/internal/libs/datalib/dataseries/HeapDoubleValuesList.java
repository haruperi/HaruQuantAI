/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.dataseries.IDoubleValuesList;
import com.strategyquant.datalib.dataseries.SQDoubleArrayList;

public class HeapDoubleValuesList
implements IDoubleValuesList {
    private SQDoubleArrayList values = null;

    public HeapDoubleValuesList(int n) {
        this.values = new SQDoubleArrayList(n);
    }

    @Override
    public double getDouble(int n) {
        return this.values.getDouble(n);
    }

    @Override
    public int size() {
        return this.values.elementsCount;
    }

    @Override
    public void setDouble(int n, double d) {
        this.values.set(n, d);
    }

    @Override
    public void addDouble(double d) {
        this.values.add(d);
    }

    @Override
    public void clear() {
        this.values.clear();
    }

    @Override
    public long getCapacity() {
        return this.values.getCapacity();
    }

    @Override
    public void release() {
        this.values.release();
    }

    @Override
    public void addDoubleValues(int n, double d) {
        this.values.addValues(n, d);
    }
}

