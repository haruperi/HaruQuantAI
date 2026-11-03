/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

public interface IDoubleValuesList {
    public double getDouble(int var1);

    public int size();

    public void setDouble(int var1, double var2);

    public void addDouble(double var1);

    public void clear();

    public long getCapacity();

    public void release();

    public void addDoubleValues(int var1, double var2);
}

