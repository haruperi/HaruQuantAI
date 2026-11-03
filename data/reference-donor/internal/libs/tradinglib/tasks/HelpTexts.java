/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.tasks;

import java.util.HashMap;

public class HelpTexts {
    private static HashMap<String, String> helps = new HashMap();

    public static void add(String string, String string2) {
        helps.put(string, string2);
    }

    public static String get(String string) {
        return helps.get(string);
    }

    public static HashMap<String, String> getAll() {
        return helps;
    }
}

