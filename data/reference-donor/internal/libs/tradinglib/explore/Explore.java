/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap
 *  it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 */
package com.strategyquant.tradinglib.explore;

import it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;

public class Explore {
    private Object2ObjectOpenHashMap<String, Long2ObjectAVLTreeMap<double[]>> data = new Object2ObjectOpenHashMap();
    private ObjectArrayList<String> columns;

    public Explore(ObjectArrayList<String> objectArrayList) {
        this.columns = objectArrayList;
    }

    public ObjectArrayList<String> getColumns() {
        return this.columns;
    }

    public void add(String string, long l, int n, double d) {
        Long2ObjectAVLTreeMap long2ObjectAVLTreeMap;
        if (!this.data.containsKey((Object)string)) {
            this.data.put((Object)string, (Object)new Long2ObjectAVLTreeMap());
        }
        if (!(long2ObjectAVLTreeMap = (Long2ObjectAVLTreeMap)this.data.get((Object)string)).containsKey(l)) {
            long2ObjectAVLTreeMap.put(l, (Object)new double[this.columns.size()]);
        }
        double[] dArray = (double[])long2ObjectAVLTreeMap.get(l);
        dArray[n] = d;
    }

    public Object2ObjectOpenHashMap<String, Long2ObjectAVLTreeMap<double[]>> getData() {
        return this.data;
    }

    public Long2ObjectAVLTreeMap<double[]> getSymbolData(String string) {
        return (Long2ObjectAVLTreeMap)this.data.get((Object)string);
    }

    public double getColumnValue(String string, long l, int n) {
        return ((double[])((Long2ObjectAVLTreeMap)this.data.get((Object)string)).get(l))[n];
    }
}

