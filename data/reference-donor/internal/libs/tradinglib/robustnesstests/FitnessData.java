/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Variable;
import org.json.JSONArray;
import org.json.JSONObject;

public class FitnessData {
    public static final double NOT_STABLE = -1.7976931348623157E308;
    public Variable variable;
    public double originalValue;
    public double[] values;
    public double[] fitness;
    public double bestAreaStartValue;
    public double bestAreaEndValue;
    public double bestValue;
    public boolean stableAreaFound;

    protected FitnessData() {
    }

    public FitnessData(Variable variable, int n) {
        this.variable = variable;
        this.originalValue = variable.getValueAsDouble();
        this.values = new double[n];
        this.fitness = new double[n];
    }

    public void set(int n, double d, double d2) throws Exception {
        if (n < 0 || n >= this.values.length) {
            throw new Exception(L.t((String)"Index %d out of range (%d)", (Object[])new Object[]{n, this.values.length}));
        }
        this.values[n] = d;
        this.fitness[n] = d2;
    }

    public double analyze(int n, int n2) {
        this.bestValue = -1.7976931348623157E308;
        double d = -1.7976931348623157E308;
        boolean bl = n % 2 == 0;
        int n3 = n - 1;
        for (int i = n3 = Math.min(n3, this.fitness.length - 1); i < this.fitness.length; ++i) {
            int n4;
            int n5;
            double d2 = -1.7976931348623157E308;
            int n6 = i - n3;
            for (n5 = n6 = Math.max(n6, 0); n5 <= i; ++n5) {
                double d3 = this.fitness[n5];
                if (!(d3 > d2)) continue;
                d2 = d3 / 100.0 * (double)(100 - n2);
            }
            n5 = 1;
            for (n4 = n6; n4 <= i; ++n4) {
                if (!(this.fitness[n4] < d2)) continue;
                n5 = 0;
                break;
            }
            if (n5 == 0) continue;
            n4 = i - n / 2;
            if (n4 < 0) {
                n4 = 0;
            }
            double d4 = this.fitness[n4];
            if (bl && this.fitness[n4 + 1] > this.fitness[n4]) {
                d4 = this.fitness[++n4];
            }
            if (!(d4 > d)) continue;
            d = d4;
            this.bestValue = this.values[n4];
            this.bestAreaStartValue = this.values[n6];
            this.bestAreaEndValue = this.values[i];
            this.stableAreaFound = true;
        }
        return this.bestValue;
    }

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("parameterName", (Object)this.variable.getName());
        jSONObject.put("originalValue", this.originalValue);
        jSONObject.put("optimizedValue", this.stableAreaFound ? this.bestValue : this.originalValue);
        jSONObject.put("stableAreaFound", this.stableAreaFound);
        jSONObject.put("stableAreaStartValue", this.bestAreaStartValue);
        jSONObject.put("stableAreaEndValue", this.bestAreaEndValue);
        JSONArray jSONArray = new JSONArray();
        JSONArray jSONArray2 = new JSONArray();
        for (int i = 0; i < this.values.length; ++i) {
            jSONArray.put(this.values[i]);
            jSONArray2.put(this.fitness[i]);
        }
        jSONObject.put("values", (Object)jSONArray);
        jSONObject.put("fitness", (Object)jSONArray2);
        return jSONObject;
    }

    public FitnessData getClone() {
        FitnessData fitnessData = new FitnessData();
        fitnessData.variable = this.variable != null ? this.variable.getClone() : null;
        fitnessData.originalValue = this.originalValue;
        fitnessData.values = new double[this.values.length];
        System.arraycopy(this.values, 0, fitnessData.values, 0, this.values.length);
        fitnessData.fitness = new double[this.fitness.length];
        System.arraycopy(this.fitness, 0, fitnessData.fitness, 0, this.fitness.length);
        fitnessData.bestAreaStartValue = this.bestAreaStartValue;
        fitnessData.bestAreaEndValue = this.bestAreaEndValue;
        fitnessData.bestValue = this.bestValue;
        fitnessData.stableAreaFound = this.stableAreaFound;
        return fitnessData;
    }
}

