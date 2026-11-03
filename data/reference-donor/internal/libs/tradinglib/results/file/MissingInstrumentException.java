/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.results.file;

public class MissingInstrumentException
extends Exception {
    private String symbol;

    public MissingInstrumentException(String string) {
        super("Instrument for symbol '" + string + "' cannot be recognized by InstrumentManager!\nAdd instrument alias to Instrument manager to load this strategy.");
        this.symbol = string;
    }

    public String getSymbol() {
        return this.symbol;
    }
}

