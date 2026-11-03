/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.doubles.DoubleArrayList
 *  it.unimi.dsi.fastutil.ints.Int2DoubleMap$Entry
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.doubles.DoubleArrayList;
import it.unimi.dsi.fastutil.ints.Int2DoubleMap;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.IOException;
import java.io.ObjectInput;
import java.io.ObjectOutput;
import java.util.Collections;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SysParamPermutationsTable {
    private static final Logger Log = LoggerFactory.getLogger(SysParamPermutationsTable.class);
    private Int2DoubleOpenHashMap mapMedians = new Int2DoubleOpenHashMap();
    private Int2DoubleOpenHashMap mapOrigValues = new Int2DoubleOpenHashMap();

    public SysParamPermutationsTable(OptimizationProfile optimizationProfile) {
        List list = DatabankColumns.get().getAvailableClasses();
        ObjectArrayList<OptimizationTestResult> objectArrayList = optimizationProfile.getOptimizations();
        OptimizationTestResult optimizationTestResult = optimizationProfile.getOriginalResult();
        for (int i = 0; i < list.size(); ++i) {
            DatabankColumn databankColumn = (DatabankColumn)list.get(i);
            String string = databankColumn.getClass().getSimpleName();
            try {
                double d = this.getMedian(databankColumn, objectArrayList);
                double d2 = optimizationTestResult == null ? 0.0 : databankColumn.getNumericValue(optimizationTestResult.stats);
                int n = SQUtils.betterHashCode((String)string);
                this.mapMedians.put(n, d);
                this.mapOrigValues.put(n, d2);
                continue;
            }
            catch (Exception exception) {
                Log.info("Error computing Sys Param Profile table", (Throwable)exception);
            }
        }
    }

    public SysParamPermutationsTable(ObjectInput objectInput) throws IOException {
        double d;
        int n;
        int n2;
        int n3 = objectInput.readInt();
        for (n2 = 0; n2 < n3; ++n2) {
            n = objectInput.readInt();
            d = objectInput.readDouble();
            this.mapMedians.put(n, d);
        }
        n3 = objectInput.readInt();
        for (n2 = 0; n2 < n3; ++n2) {
            n = objectInput.readInt();
            d = objectInput.readDouble();
            this.mapOrigValues.put(n, d);
        }
    }

    public void serialize(ObjectOutput objectOutput) throws IOException {
        objectOutput.writeInt(this.mapMedians.size());
        for (Int2DoubleMap.Entry entry : this.mapMedians.int2DoubleEntrySet()) {
            objectOutput.writeInt(entry.getIntKey());
            objectOutput.writeDouble(entry.getDoubleValue());
        }
        objectOutput.writeInt(this.mapOrigValues.size());
        for (Int2DoubleMap.Entry entry : this.mapOrigValues.int2DoubleEntrySet()) {
            objectOutput.writeInt(entry.getIntKey());
            objectOutput.writeDouble(entry.getDoubleValue());
        }
    }

    private double getMedian(DatabankColumn databankColumn, ObjectArrayList<OptimizationTestResult> objectArrayList) throws Exception {
        DoubleArrayList doubleArrayList = new DoubleArrayList();
        for (int i = 0; i < objectArrayList.size(); ++i) {
            OptimizationTestResult optimizationTestResult = (OptimizationTestResult)objectArrayList.get(i);
            double d = databankColumn.getNumericValue(optimizationTestResult.stats);
            doubleArrayList.add(d);
        }
        Collections.sort(doubleArrayList);
        if (doubleArrayList.size() == 0) {
            return 0.0;
        }
        return doubleArrayList.getDouble(doubleArrayList.size() / 2);
    }

    public double getMedian(String string) {
        int n = SQUtils.betterHashCode((String)string);
        return this.mapMedians.containsKey(n) ? this.mapMedians.get(n) : 0.0;
    }

    public double getOrigValue(String string) {
        int n = SQUtils.betterHashCode((String)string);
        return this.mapOrigValues.containsKey(n) ? this.mapOrigValues.get(n) : 0.0;
    }
}

