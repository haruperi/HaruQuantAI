/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.benchmark;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.project.ProgressEngine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BenchmarkProgressEngine
extends ProgressEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"ProgressTracker");

    public BenchmarkProgressEngine() {
        super("Benchmark");
    }

    @Override
    public void setProgress(long l) {
        int n = SQUtils.round((double)(100.0 * ((double)l / (double)this.maxProgress)));
        super.setProgress(n);
    }
}

