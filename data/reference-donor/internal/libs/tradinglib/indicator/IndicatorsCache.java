/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.longs.LongIterator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.indicator;

import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.indicator.IndicatorBase;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongIterator;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorsCache {
    private static final Logger Log = LoggerFactory.getLogger(IndicatorsCache.class);
    private Long2ObjectOpenHashMap<IndicatorBase> cache = new Long2ObjectOpenHashMap(10);

    public boolean containsKey(long l) {
        return this.cache.containsKey(l);
    }

    public IndicatorBase put(long l, IndicatorBase indicatorBase) {
        return (IndicatorBase)this.cache.put(l, (Object)indicatorBase);
    }

    public IndicatorBase get(long l) {
        return (IndicatorBase)this.cache.get(l);
    }

    public void destroy() {
        for (IndicatorBase indicatorBase : this.cache.values()) {
            try {
                indicatorBase.Deinitialize();
            }
            catch (Exception exception) {
                Log.error("Error during Deinitialization of indicator", (Throwable)exception);
            }
            indicatorBase.destroy();
        }
        this.cache.clear();
    }

    public ArrayList<IndicatorBase> getIndicatorsForThisData(ChartData chartData) {
        ArrayList<IndicatorBase> arrayList = new ArrayList<IndicatorBase>();
        LongIterator longIterator = this.cache.keySet().iterator();
        while (longIterator.hasNext()) {
            long l = (Long)longIterator.next();
            IndicatorBase indicatorBase = (IndicatorBase)this.cache.get(l);
            if (!indicatorBase.checkUsesData(chartData)) continue;
            indicatorBase.setName(indicatorBase.getPseudoName());
            arrayList.add(indicatorBase);
        }
        return arrayList;
    }
}

