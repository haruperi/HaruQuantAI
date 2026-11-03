/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.backtestrunner;

import com.strategyquant.lib.L;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class DurationStats {
    public static final String MainTest = L.t((String)"Main test", (Object[])new Object[]{true});
    private HashMap<String, Double> map = new HashMap();
    private ArrayList<String> keysInOrder = new ArrayList();

    public void addDuration(String string, long l) {
        double d = (double)l / 1000.0;
        this.keysInOrder.add(string);
        this.map.put(string, d);
    }

    public HashMap<String, Double> getMap() {
        return this.map;
    }

    public List<String> getKeys() {
        return this.keysInOrder;
    }
}

