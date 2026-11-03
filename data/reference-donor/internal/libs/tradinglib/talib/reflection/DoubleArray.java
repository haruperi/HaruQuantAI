/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.strategyquant.tradinglib.engine.stockpicker.data.BarData;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.ArrayList;

public class DoubleArray {
    private ArrayList<double[]> arrays = new ArrayList();
    private Integer[] columns;

    public DoubleArray(ObjectArrayList<BarData> objectArrayList, Integer ... integerArray) {
        this.columns = integerArray;
        int n = objectArrayList.size();
        for (int i = 0; i < integerArray.length; ++i) {
            this.arrays.add(new double[n]);
        }
    }

    public double[] get(int n) {
        int n2 = 0;
        Integer[] integerArray = this.columns;
        int n3 = integerArray.length;
        for (int i = 0; i < n3; ++i) {
            int n4 = integerArray[i];
            if (n4 == n) {
                return this.arrays.get(n2);
            }
            ++n2;
        }
        return null;
    }

    public double[] getByIndex(int n) {
        return this.arrays.get(n);
    }
}

