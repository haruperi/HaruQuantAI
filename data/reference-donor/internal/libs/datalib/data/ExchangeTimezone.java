/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data;

import java.util.HashMap;
import java.util.Map;

public class ExchangeTimezone {
    private static final String DEFAULT = "America/New_York";
    private static ExchangeTimezone instance = new ExchangeTimezone();
    private Map<String, String> map = new HashMap<String, String>();

    public static ExchangeTimezone get() {
        return instance;
    }

    private ExchangeTimezone() {
        this.map.put("AMEX", DEFAULT);
        this.map.put("ASX", "Australia/Sydney");
        this.map.put("CNSX", "America/Toronto");
        this.map.put("NASDAQ", DEFAULT);
        this.map.put("NYSE", DEFAULT);
        this.map.put("OTHEROTC", DEFAULT);
        this.map.put("TSX", "America/Toronto");
        this.map.put("TSX-V", "America/Toronto");
        this.map.put("CBOT", "America/Chicago");
        this.map.put("CME", "America/Chicago");
        this.map.put("COMEX", DEFAULT);
        this.map.put("ICEUS", DEFAULT);
        this.map.put("KCBT", "America/Chicago");
        this.map.put("NYMEX", DEFAULT);
        this.map.put("SMALL", "America/Chicago");
    }

    public String getTimezone(String string) {
        String string2 = this.map.get(string);
        return string2 != null ? string2 : DEFAULT;
    }
}

