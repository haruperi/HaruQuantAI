/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.project.ProjectEngine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQLogger {
    public static final Logger Log = LoggerFactory.getLogger(SQLogger.class);

    public static void log(String string, String string2) {
        if (string.equals("WalkForwardOptimization_CrossCheck") || string.equals("WalkForwardMatrix_CrossCheck")) {
            return;
        }
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            return;
        }
        try {
            String string3 = SQTime.getLogTime((boolean)false, (boolean)false);
            StringBuilder stringBuilder = new StringBuilder(string3);
            stringBuilder.append(" ");
            stringBuilder.append(string2);
            stringBuilder.append("\n");
            ProjectEngine.get((String)string).log.add(stringBuilder.toString());
        }
        catch (Exception exception) {
            Log.error("Error while writing log. Exc.", (Throwable)exception);
        }
    }
}

