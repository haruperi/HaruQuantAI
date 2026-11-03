/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data;

import java.util.HashMap;
import java.util.Map;

public class StockGroupUpdateErrorManager {
    private static final StockGroupUpdateErrorManager instance = new StockGroupUpdateErrorManager();
    private Map<String, String> errors;

    public static StockGroupUpdateErrorManager getInstance() {
        return instance;
    }

    public synchronized void start() {
        if (this.errors == null) {
            this.errors = new HashMap<String, String>();
        }
    }

    public synchronized void logError(String string, String string2) {
        if (this.errors != null) {
            this.errors.put(string, string2);
        }
    }

    public synchronized Map<String, String> finished() {
        Map<String, String> map = this.errors;
        this.errors = null;
        return map;
    }
}

