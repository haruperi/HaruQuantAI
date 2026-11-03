/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.dataseries;

import java.util.Arrays;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQDoubleArrayList {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQDoubleArrayList");
    public static final int DEFAULT_CAPACITY = 5000;
    private static final Object EMPTY = new double[0];
    public double[] buffer;
    public int elementsCount;

    public SQDoubleArrayList() {
        this(5000);
    }

    public SQDoubleArrayList(int n) {
        this.ensureBufferSpace(n);
    }

    public void add(double d) {
        this.ensureBufferSpace(1);
        this.buffer[this.elementsCount++] = d;
    }

    public double getDouble(int n) {
        assert (n >= 0 && n < this.elementsCount) : "Index out of bounds.";
        return this.buffer[n];
    }

    public double set(int n, double d) {
        assert (n >= 0 && n < this.elementsCount) : "Index out of bounds.";
        double d2 = this.buffer[n];
        this.buffer[n] = d;
        return d2;
    }

    public void ensureCapacity(int n) {
        if (n > this.buffer.length) {
            this.ensureBufferSpace(n - this.elementsCount);
        }
    }

    protected void ensureBufferSpace(int n) {
        int n2;
        int n3 = n2 = this.buffer == null ? 0 : this.buffer.length;
        if (n2 < this.elementsCount + n) {
            int n4 = (int)((double)(this.elementsCount + n) * 1.3);
            double[] dArray = new double[n4];
            if (n2 > 0) {
                System.arraycopy(this.buffer, 0, dArray, 0, this.buffer.length);
            }
            this.buffer = dArray;
        }
    }

    public void clear() {
        Arrays.fill(this.buffer, 0, this.elementsCount, 0.0);
        this.elementsCount = 0;
    }

    public void release() {
        this.buffer = (double[])EMPTY;
        this.elementsCount = 0;
    }

    public long getCapacity() {
        return this.buffer.length;
    }

    public void addValues(int n, double d) {
        this.ensureBufferSpace(n);
        Arrays.fill(this.buffer, this.elementsCount, this.elementsCount + n, d);
        this.elementsCount += n;
    }
}

