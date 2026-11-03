/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.lib.utils.ISQCloneable;
import java.io.Serializable;

public class SymbolInfo
implements Serializable,
ISQCloneable<SymbolInfo> {
    private String symbolName;
    private int symbolHash;
    private String instrumentName;
    private InstrumentInfo instrumentInfo;

    public SymbolInfo(String string, String string2, InstrumentInfo instrumentInfo) {
        this.symbolName = string;
        this.symbolHash = string.hashCode();
        this.instrumentName = string2;
        this.instrumentInfo = instrumentInfo;
    }

    public String Symbol() {
        return this.symbolName;
    }

    public String Instrument() {
        return this.instrumentName;
    }

    public InstrumentInfo InstrumentInfo() {
        return this.instrumentInfo;
    }

    public SymbolInfo getClone() throws Exception {
        SymbolInfo symbolInfo = new SymbolInfo(this.symbolName, this.instrumentName, this.instrumentInfo);
        return symbolInfo;
    }
}

