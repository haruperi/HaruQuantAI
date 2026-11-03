/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.tradinglib.backtest.BacktestDataCache;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MemoryCleaner {
    public static final Logger Log = LoggerFactory.getLogger(MemoryCleaner.class);
    public static final int NEVER = 0;
    public static final int EVERY_10_SECONDS = 10000;
    public static final int EVERY_20_SECONDS = 20000;
    public static final int EVERY_30_SECONDS = 30000;
    public static final int EVERY_45_SECONDS = 40000;
    public static final int EVERY_MINUTE = 60000;
    public static final int EVERY_2_MINUTES = 120000;
    public static final int EVERY_5_MINUTES = 300000;
    public static final int EVERY_10_MINUTES = 600000;
    public static final int EVERY_15_MINUTES = 900000;
    public static final int EVERY_30_MINUTES = 1800000;
    public static final int EVERY_HOUR = 3600000;
    private static final int memoryUsageActivationLimit = 80;
    private static final int autoCleaningInterval = 60000;
    private static Thread manualCleaningThread = null;
    private static long lastCleanTime = 0L;

    public static void init() {
        boolean bl = Boolean.parseBoolean(MainApp.settings().get("memoryCleanup", "false"));
        int n = Integer.parseInt(MainApp.settings().get("memoryCleanupInterval", "0"));
        MemoryCleaner.startAutomaticCleaningInterval();
        if (bl) {
            try {
                MemoryCleaner.checkType(n);
                MemoryCleaner.startManualCleaningInterval(n);
            }
            catch (Exception exception) {
                Log.error("Cannot setup memory cleanup interval", (Throwable)exception);
            }
        }
    }

    public static String cleanNow() {
        long l;
        System.gc();
        lastCleanTime = System.currentTimeMillis();
        Log.debug("Memory cleaned");
        long l2 = SQGrid.getGridClient().countAllJobs(null);
        String string = l2 == 0L ? ((l = BacktestDataCache.getInstance().freeCache()) == 0L ? "Started Java memory cleanup.<br/>No other offheap cached data found." : "Started Java memory cleanup.<br/>Cleaned also " + SQUtils.formatBytesToHumanFormat((long)l) + " from cached offheap data.") : "Started Java memory cleanup.<br/>No cached offheap data memory was freed because there are some jobs running.";
        return string;
    }

    public static void checkType(int n) throws Exception {
        switch (n) {
            case 0: 
            case 10000: 
            case 20000: 
            case 30000: 
            case 40000: 
            case 60000: 
            case 120000: 
            case 300000: 
            case 600000: 
            case 900000: 
            case 1800000: 
            case 3600000: {
                return;
            }
        }
        throw new Exception(L.t((String)"Unknown cleaning period %d.", (Object[])new Object[]{n}));
    }

    private static void startManualCleaningInterval(final int n) {
        if (manualCleaningThread != null && manualCleaningThread.isAlive()) {
            manualCleaningThread.interrupt();
        }
        if (n == 0) {
            return;
        }
        manualCleaningThread = new Thread(){

            @Override
            public void run() {
                while (true) {
                    try {
                        Thread.sleep(n);
                    }
                    catch (InterruptedException interruptedException) {
                        break;
                    }
                    if (!MainApp.AppLoaded) continue;
                    if (MainApp.isExiting()) break;
                    MemoryCleaner.cleanNow();
                }
            }
        };
        manualCleaningThread.start();
    }

    private static void startAutomaticCleaningInterval() {
        new Thread(){

            @Override
            public void run() {
                while (true) {
                    long l;
                    try {
                        Thread.sleep(60000L);
                    }
                    catch (InterruptedException interruptedException) {
                        Log.error("Automatic memory cleaning thread interrupted", (Throwable)interruptedException);
                        break;
                    }
                    if (MainApp.isExiting()) break;
                    if (MemoryUsageChecker.getCurrentUsage() < 80.0 || (l = System.currentTimeMillis()) - lastCleanTime < 60000L) continue;
                    MemoryCleaner.cleanNow();
                }
            }
        }.start();
    }
}

