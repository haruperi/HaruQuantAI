/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.dataseries.HeapLongValuesList;
import com.strategyquant.datalib.dataseries.ILongValuesList;
import java.util.Timer;
import java.util.TimerTask;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LongListCache {
    public static final Logger Log = LoggerFactory.getLogger((String)"LongListCache");
    private static final ILongValuesList[] cache = new ILongValuesList[100];
    private static int initedTotal = 0;
    private static int fromCache = 0;
    private static int clearedTotal = 0;
    private static int clearedToCache = 0;
    private static int maxInCache = 0;
    private static int notSavedToCache = 0;

    public LongListCache() {
        TimerTask timerTask = new TimerTask(){

            @Override
            public void run() {
                LongListCache.printStats();
            }
        };
        Timer timer = new Timer("Timer");
        long l = 3000L;
        long l2 = 3000L;
        timer.scheduleAtFixedRate(timerTask, l, l2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected static void printStats() {
        ILongValuesList[] iLongValuesListArray = cache;
        synchronized (cache) {
            int n = LongListCache.computeInCache();
            Log.info("initedTotal: {}, from cache: {}, clearedTotal: {}, clearedToCache: {}, notSavedToCache: {}, in cache: {}, max in cache: {}", new Object[]{initedTotal, fromCache, clearedTotal, clearedToCache, notSavedToCache, n, maxInCache});
            // ** MonitorExit[var0] (shouldn't be in output)
            return;
        }
    }

    private static int computeInCache() {
        int n = 0;
        for (int i = 0; i < cache.length; ++i) {
            if (cache[i] == null) continue;
            ++n;
        }
        return n;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void resetStats() {
        ILongValuesList[] iLongValuesListArray = cache;
        synchronized (cache) {
            initedTotal = 0;
            fromCache = 0;
            clearedTotal = 0;
            clearedToCache = 0;
            notSavedToCache = 0;
            // ** MonitorExit[var0] (shouldn't be in output)
            return;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void clear(ILongValuesList iLongValuesList) {
        iLongValuesList.clear();
        ++clearedTotal;
        ILongValuesList[] iLongValuesListArray = cache;
        synchronized (cache) {
            for (int i = 0; i < cache.length; ++i) {
                if (cache[i] != null) continue;
                ++clearedToCache;
                LongListCache.cache[i] = iLongValuesList;
                break;
            }
            // ** MonitorExit[var1_1] (shouldn't be in output)
            return;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static ILongValuesList get(int n) {
        ++initedTotal;
        ILongValuesList[] iLongValuesListArray = cache;
        synchronized (cache) {
            for (int i = 0; i < cache.length; ++i) {
                if (cache[i] == null) continue;
                ILongValuesList iLongValuesList = cache[i];
                LongListCache.cache[i] = null;
                ++fromCache;
                // ** MonitorExit[var2_1] (shouldn't be in output)
                return iLongValuesList;
            }
            // ** MonitorExit[var2_1] (shouldn't be in output)
            HeapLongValuesList heapLongValuesList = new HeapLongValuesList(n);
            return heapLongValuesList;
        }
    }
}

