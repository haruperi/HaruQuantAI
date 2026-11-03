/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.dukascopy;

import java.util.HashMap;
import java.util.Map;

public class CdnInfo {
    private Map<String, SymbolInfo> map = new HashMap<String, SymbolInfo>();

    public SymbolInfo getSymbolInfo(String string, String string2) {
        return this.map.get(string + "_" + string2);
    }

    public void addSymbolInfo(String string, String string2, String string3, String string4) {
        if (this.map.containsKey(string)) {
            return;
        }
        this.map.put(string + "_" + string2, new SymbolInfo(string3, string4));
    }

    public static class SymbolInfo {
        private String url;
        private String format;

        public SymbolInfo(String string, String string2) {
            this.url = string;
            this.format = string2;
        }

        public String getFormat() {
            return this.format;
        }

        public String getUrl() {
            return this.url;
        }
    }
}

