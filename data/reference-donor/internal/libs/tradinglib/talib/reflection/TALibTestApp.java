/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.strategyquant.tradinglib.talib.reflection.TALibFunction;
import com.strategyquant.tradinglib.talib.reflection.TALibFunctions;

public class TALibTestApp {
    public static void main(String[] stringArray) {
        TALibFunction[] tALibFunctionArray;
        for (TALibFunction tALibFunction : tALibFunctionArray = TALibFunctions.getTALibFunctions()) {
            System.out.println(tALibFunction.toString());
        }
    }
}

