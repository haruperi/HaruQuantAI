/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.random.MersenneTwisterRng
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.dataseries.HeapDoubleValuesList;
import com.strategyquant.datalib.dataseries.IDoubleValuesList;
import com.strategyquant.lib.random.MersenneTwisterRng;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.atomic.AtomicInteger;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DoubleListCache {
    public static final Logger Log = LoggerFactory.getLogger((String)"DoubleListCache");
    private static final ObjectArrayList<IDoubleValuesList> cache = new ObjectArrayList();
    protected static final MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
    protected static final int MEGABYTE = 0x100000;
    private static boolean tooBigCacheMemory = false;
    private static boolean tooMuchMemoryUsed = false;
    private static long lastUsedTime = 0L;
    private static long lastClearedTime = 0L;
    private static int maxCacheSize = 0;
    private static long totalGet = 0L;
    private static long totalClear = 0L;
    private static long totalAllocated = 0L;
    private static long totalDeallocated = 0L;
    private static long totalGetFromCache = 0L;
    private static long totalReturnedToCache = 0L;
    private static long maxElementsInCache = 0L;
    private static int totalObjectsCreated = 0;
    private static final AtomicInteger objectsWaitingForAllocation = new AtomicInteger(0);
    private static final MersenneTwisterRng rng = new MersenneTwisterRng();
    private static long maxJavaMemory;
    private static int timerCount;

    public DoubleListCache() {
        TimerTask timerTask = new TimerTask(){

            @Override
            public void run() {
                DoubleListCache.printStats();
            }
        };
        Timer timer = new Timer("Timer");
        long l = 20000L;
        long l2 = 5000L;
        timer.scheduleAtFixedRate(timerTask, l, l2);
        maxJavaMemory = memoryBean.getHeapMemoryUsage().getMax() / 0x100000L;
        maxCacheSize = (int)(maxJavaMemory / 1026L) * 100;
        Log.debug("Max memory detected: {} MB, max cache size set to: {}", (Object)maxJavaMemory, (Object)maxCacheSize);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected static void printStats() {
        ObjectArrayList<IDoubleValuesList> objectArrayList = cache;
        synchronized (objectArrayList) {
            long l = 0L;
            if (lastUsedTime > 0L) {
                long l2 = (System.currentTimeMillis() - lastUsedTime) / 1000L;
                long l3 = (System.currentTimeMillis() - lastClearedTime) / 1000L;
                if (cache.size() > 0) {
                    int n = 0;
                    if (l2 > 300L) {
                        n = (int)((double)cache.size() * 0.2);
                    } else if (l3 > 300L && tooMuchMemoryUsed) {
                        n = (int)((double)cache.size() * 0.1);
                    }
                    if (n > 5) {
                        for (int i = 0; i < n; ++i) {
                            IDoubleValuesList iDoubleValuesList = (IDoubleValuesList)cache.pop();
                            iDoubleValuesList.release();
                        }
                    }
                }
            }
            tooMuchMemoryUsed = false;
            MemoryUsage memoryUsage = memoryBean.getHeapMemoryUsage();
            double d = memoryUsage.getUsed() / 0x100000L;
            double d2 = memoryUsage.getCommitted() / 0x100000L;
            double d3 = d / d2;
            double d4 = d2 / (double)maxJavaMemory;
            if (d3 > 0.75 && d4 > 0.8) {
                tooMuchMemoryUsed = true;
            }
            tooBigCacheMemory = false;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void resetStats() {
        ObjectArrayList<IDoubleValuesList> objectArrayList = cache;
        synchronized (objectArrayList) {
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void clear(IDoubleValuesList iDoubleValuesList) {
        ObjectArrayList<IDoubleValuesList> objectArrayList = cache;
        synchronized (objectArrayList) {
            ++totalClear;
            boolean bl = false;
            String string = "";
            if (cache.size() < maxCacheSize && !tooBigCacheMemory && !tooMuchMemoryUsed) {
                bl = true;
            } else {
                if (cache.size() >= maxCacheSize) {
                    string = "max cache size";
                }
                if (tooBigCacheMemory) {
                    string = "tooBigCacheMemory";
                }
                if (tooMuchMemoryUsed) {
                    string = "tooMuchMemoryUsed";
                }
            }
            String string2 = "";
            if (bl) {
                iDoubleValuesList.clear();
                ++totalReturnedToCache;
                cache.push((Object)iDoubleValuesList);
                maxElementsInCache = Math.max((long)cache.size(), maxElementsInCache);
            } else {
                ++totalDeallocated;
                iDoubleValuesList.release();
            }
        }
    }

    public static IDoubleValuesList get(int n) {
        ++totalGet;
        String string = "";
        IDoubleValuesList iDoubleValuesList = DoubleListCache.getFromCache();
        if (iDoubleValuesList != null) {
            ++totalGetFromCache;
            return iDoubleValuesList;
        }
        ++totalAllocated;
        string = "";
        iDoubleValuesList = new HeapDoubleValuesList(n);
        return iDoubleValuesList;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static IDoubleValuesList getFromCache() {
        ObjectArrayList<IDoubleValuesList> objectArrayList = cache;
        synchronized (objectArrayList) {
            if (!cache.isEmpty()) {
                lastUsedTime = System.currentTimeMillis();
                IDoubleValuesList iDoubleValuesList = (IDoubleValuesList)cache.pop();
                return iDoubleValuesList;
            }
        }
        return null;
    }

    public static int getWaitingForAllocationObjects() {
        return objectsWaitingForAllocation.get();
    }

    static {
        timerCount = 0;
    }
}

