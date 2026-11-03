/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.tradinglib.talib.TALibCustomIndicator;

public class TALibCustomIndicatorsList
extends CustomClasses<TALibCustomIndicator> {
    private static TALibCustomIndicatorsList instance;

    public static TALibCustomIndicatorsList getInstance() {
        if (instance == null) {
            instance = new TALibCustomIndicatorsList();
        }
        return instance;
    }

    private TALibCustomIndicatorsList() {
        this.setDirName("TALibIndicators");
        this.setExpectedClassType(TALibCustomIndicator.class);
        this.loadAvailableClasses();
    }
}

