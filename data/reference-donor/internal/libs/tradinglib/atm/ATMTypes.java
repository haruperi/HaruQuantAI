/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.atm;

import com.strategyquant.tradinglib.task.settings.buildmode.JSONAble;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ATMTypes
extends JSONAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"ATMTypes");
    public static final int DONT_USE = 0;
    public static final int FROM_STRATEGY = 1;
    public static final int FROM_CONFIG = 2;
    public static final int GENERATE = 3;
    public static final int TYPE_FIXED_PIPS = 1;
    public static final int TYPE_ATR_BASED = 2;

    public static int recognize(String string, int n) {
        if (string == null || string.equals("")) {
            return n;
        }
        try {
            int n2 = Integer.parseInt(string);
            switch (n2) {
                case 0: 
                case 1: 
                case 2: 
                case 3: {
                    return n2;
                }
            }
            Log.error("Unrecognized atm type: {}. Using default value", (Object)string);
        }
        catch (Exception exception) {
            Log.info("Cannot convert value'{}' to int!", (Object)string);
        }
        return n;
    }
}

