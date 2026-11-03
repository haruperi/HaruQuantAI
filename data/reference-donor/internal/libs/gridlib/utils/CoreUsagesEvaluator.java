/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.memory.CpuInfo
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.utils;

import com.strategyquant.lib.memory.CpuInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CoreUsagesEvaluator {
    private static final Logger LOGGER = LoggerFactory.getLogger(CoreUsagesEvaluator.class);

    public static int getCores(String string) {
        int n = CpuInfo.getAvailableProcessors();
        string = string.trim();
        try {
            int n2 = Integer.parseInt(string);
            if (n2 < 0) {
                LOGGER.debug("Using all cores but reserving:" + -n2 + " cores");
                n2 = n + n2;
            }
            n2 = CoreUsagesEvaluator.getSafeCountOFCores(n2, n);
            LOGGER.debug("Total cores available: {}, using: {}", (Object)n, (Object)n2);
            return n2;
        }
        catch (Exception exception) {
            if (string.endsWith("%")) {
                string = string.substring(0, string.length() - 1);
                try {
                    int n3 = Integer.parseInt(string);
                    double d = (double)((float)n * (float)n3) / 100.0;
                    int n4 = (int)d;
                    LOGGER.debug("Using percentage of cores:" + n3 + "%. Total cores:" + n + ". Cores for usage:" + n4);
                    n4 = CoreUsagesEvaluator.getSafeCountOFCores(n4, n);
                    LOGGER.debug("Total cores available: {}, using: {}", (Object)n, (Object)n4);
                    return n4;
                }
                catch (Exception exception2) {
                    // empty catch block
                }
            }
            LOGGER.debug("Invalid core usage pattern:" + string + ". Using all available cores-1");
            int n5 = CoreUsagesEvaluator.getSafeCountOFCores(n - 1, n);
            LOGGER.debug("Total cores available: {}, using: {}", (Object)n, (Object)n5);
            return n5;
        }
    }

    private static int getSafeCountOFCores(int n, int n2) {
        if (n < 1) {
            LOGGER.debug("Number of cores is too small. Using 1 core.");
            n = 1;
        }
        if (n > n2) {
            LOGGER.debug("Number of cores is higher than available cores. Using " + n2 + " core.");
            n = n2;
        }
        return n;
    }
}

