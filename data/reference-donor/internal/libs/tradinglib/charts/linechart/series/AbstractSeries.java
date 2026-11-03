/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.charts.linechart.series;

import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import java.util.ArrayList;

public abstract class AbstractSeries {
    public ArrayList<XYValue> values = new ArrayList<XYValue>(){

        @Override
        public boolean add(XYValue xYValue) {
            super.add(xYValue);
            if (AbstractSeries.this.capacity > 0 && AbstractSeries.this.values.size() > AbstractSeries.this.capacity) {
                this.remove(0);
            }
            return true;
        }
    };
    public String name = null;
    public int capacity = -1;
    public String color = null;

    public AbstractSeries(String string) {
        this.name = string;
    }

    public AbstractSeries(String string, int n) {
        this.name = string;
        this.capacity = n;
    }

    public void clear() {
        this.values.clear();
    }
}

