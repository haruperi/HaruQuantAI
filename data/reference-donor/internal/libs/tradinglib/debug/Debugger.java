/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.debug;

import com.strategyquant.tradinglib.debug.DebugConsole;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Debugger {
    private static final Logger Log = LoggerFactory.getLogger(Debugger.class);

    public void debug(String string, String string2) {
        DebugConsole.log(string, string2);
    }

    public void fdebug(String string, String string2) {
        Log.info(string + " - " + string2);
    }
}

