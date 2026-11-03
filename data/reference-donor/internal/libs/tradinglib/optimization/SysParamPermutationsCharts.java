/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.doubles.DoubleArrayList
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  it.unimi.dsi.fastutil.ints.IntSet
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.BarChart;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.doubles.DoubleArrayList;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import it.unimi.dsi.fastutil.ints.IntSet;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.IOException;
import java.io.ObjectInput;
import java.io.ObjectOutput;
import java.util.Collections;
import java.util.List;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SysParamPermutationsCharts {
    private static final Logger Log = LoggerFactory.getLogger(SysParamPermutationsCharts.class);
    private Int2ObjectOpenHashMap<JSONObject> mapCharts = new Int2ObjectOpenHashMap();

    public SysParamPermutationsCharts(OptimizationProfile optimizationProfile) {
        List list = DatabankColumns.get().getAvailableClasses();
        ObjectArrayList<OptimizationTestResult> objectArrayList = optimizationProfile.getOptimizations();
        OptimizationTestResult optimizationTestResult = optimizationProfile.getOriginalResult();
        for (int i = 0; i < list.size(); ++i) {
            DatabankColumn databankColumn = (DatabankColumn)list.get(i);
            String string = databankColumn.getClass().getSimpleName();
            try {
                JSONObject jSONObject = this.computeFor(string, objectArrayList, optimizationTestResult);
                int n = SQUtils.betterHashCode((String)string);
                this.mapCharts.put(n, (Object)jSONObject);
                continue;
            }
            catch (Exception exception) {
                Log.info("Error computing Sys Param Profile chart", (Throwable)exception);
            }
        }
    }

    public SysParamPermutationsCharts(ObjectInput objectInput) throws IOException {
        int n = objectInput.readInt();
        for (int i = 0; i < n; ++i) {
            int n2 = objectInput.readInt();
            String string = objectInput.readUTF();
            this.mapCharts.put(n2, (Object)new JSONObject(string));
        }
    }

    public void serialize(ObjectOutput objectOutput) throws IOException {
        objectOutput.writeInt(this.mapCharts.size());
        IntSet intSet = this.mapCharts.keySet();
        IntIterator intIterator = intSet.iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            objectOutput.writeInt(n);
            objectOutput.writeUTF(((JSONObject)this.mapCharts.get(n)).toString());
        }
    }

    public JSONObject get(String string) {
        int n = SQUtils.betterHashCode((String)string);
        return this.mapCharts.containsKey(n) ? (JSONObject)this.mapCharts.get(n) : null;
    }

    public JSONObject computeFor(String string, ObjectArrayList<OptimizationTestResult> objectArrayList, OptimizationTestResult optimizationTestResult) throws Exception {
        String string2;
        int n;
        int n2;
        JSONObject jSONObject = new JSONObject();
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
        double d = Double.MAX_VALUE;
        double d2 = -1.7976931348623157E308;
        DoubleArrayList doubleArrayList = new DoubleArrayList();
        for (n2 = 0; n2 < objectArrayList.size(); ++n2) {
            OptimizationTestResult optimizationTestResult2 = (OptimizationTestResult)objectArrayList.get(n2);
            double d3 = optimizationTestResult2.stats.getDouble(string);
            if (d3 > d2) {
                d2 = d3;
            }
            if (d3 < d) {
                d = d3;
            }
            doubleArrayList.add(d3);
        }
        n2 = doubleArrayList.size();
        if (n2 > 20) {
            n2 = 20;
        }
        double d4 = (d2 - d) / (double)(n2 - 1);
        int[] nArray = new int[n2];
        double[] dArray = new double[n2];
        for (n = 0; n < dArray.length; ++n) {
            dArray[n] = -99999.0;
        }
        if (doubleArrayList.size() == 0) {
            return jSONObject;
        }
        for (n = 0; n < doubleArrayList.size(); ++n) {
            double d5 = doubleArrayList.getDouble(n);
            int n3 = this.getHistogramIndex(d5, d, d2, d4, n2);
            if (n3 < 0 || n3 >= nArray.length) {
                n3 = this.getHistogramIndex(d5, d, d2, d4, n2);
            }
            int n4 = n3;
            nArray[n4] = nArray[n4] + 1;
            if (dArray[n3] != -99999.0 && !(dArray[n3] < d5)) continue;
            dArray[n3] = d5;
        }
        n = 0;
        BarChart barChart = new BarChart();
        barChart.tooltips = false;
        for (int i = 0; i < nArray.length; ++i) {
            int n5 = nArray[i];
            string2 = SQUtils.d2((double)dArray[i]);
            if (n5 > n) {
                n = n5;
            }
            barChart.addValue("Frequency", (Comparable)((Object)string2), n5);
        }
        Collections.sort(doubleArrayList);
        double d6 = doubleArrayList.getDouble(doubleArrayList.size() / 2);
        jSONObject.put("median", (Object)databankColumn.printPlValue(d6, (byte)10));
        barChart.setCategoryColor("Median", "#E8383C");
        int n6 = this.getHistogramIndex(d6, d, d2, d4, n2);
        for (int i = 0; i < nArray.length; ++i) {
            string2 = dArray[i] == -99999.0 ? "" : SQUtils.d2((double)dArray[i]);
            if (i == n6) {
                barChart.addValue("Median", (Comparable)((Object)string2), n);
                continue;
            }
            barChart.addValue("Median", (Comparable)((Object)string2), 0);
        }
        if (optimizationTestResult != null) {
            double d7 = databankColumn.getNumericValue(optimizationTestResult.stats);
            barChart.setCategoryColor("Orig. value", "#008000");
            n6 = this.getHistogramIndex(d7, d, d2, d4, n2);
            for (int i = 0; i < nArray.length; ++i) {
                string2 = dArray[i] == -99999.0 ? "" : SQUtils.d2((double)dArray[i]);
                if (i == n6) {
                    barChart.addValue("Orig. value", (Comparable)((Object)string2), n);
                    continue;
                }
                barChart.addValue("Orig. value", (Comparable)((Object)string2), 0);
            }
        }
        jSONObject.put("chart", (Object)barChart.toJSON());
        return jSONObject;
    }

    private int getHistogramIndex(double d, double d2, double d3, double d4, int n) {
        double d5 = d - d2;
        return (int)(d5 /= d4);
    }
}

