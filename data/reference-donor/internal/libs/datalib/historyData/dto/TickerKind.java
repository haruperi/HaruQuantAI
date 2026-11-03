/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.historyData.dto;

public enum TickerKind {
    FUTURES(1L, "futures"),
    STOCK(2L, "equities");

    private Long id;
    private String forDownload;

    private TickerKind(Long l, String string2) {
        this.id = l;
        this.forDownload = string2;
    }

    public Long getId() {
        return this.id;
    }

    public static TickerKind tryEvalTickerFromName(String string) {
        for (int i = 0; i < string.length(); ++i) {
            char c = string.charAt(i);
            if (!Character.isDigit(c)) continue;
            return FUTURES;
        }
        return STOCK;
    }

    public static TickerKind forId(Long l) {
        for (TickerKind tickerKind : TickerKind.values()) {
            if (!tickerKind.getId().equals(l)) continue;
            return tickerKind;
        }
        return null;
    }

    public String forDownload() {
        return this.forDownload;
    }
}

