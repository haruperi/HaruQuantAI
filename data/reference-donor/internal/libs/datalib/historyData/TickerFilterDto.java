/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.historyData;

public class TickerFilterDto {
    private String[] names;
    private Long marketId;
    private boolean searchInTicker;
    private boolean searchInName;
    private boolean exactMatch;
    private boolean onlyContFutures;

    public Long getMarketId() {
        return this.marketId;
    }

    public void setMarketId(Long l) {
        this.marketId = l;
    }

    public String[] getNames() {
        return this.names;
    }

    public void setNames(String[] stringArray) {
        this.names = stringArray;
    }

    public boolean isSearchInTicker() {
        return this.searchInTicker;
    }

    public void setSearchInTicker(boolean bl) {
        this.searchInTicker = bl;
    }

    public boolean isSearchInName() {
        return this.searchInName;
    }

    public void setSearchInName(boolean bl) {
        this.searchInName = bl;
    }

    public boolean isOnlyContFutures() {
        return this.onlyContFutures;
    }

    public void setOnlyContFutures(boolean bl) {
        this.onlyContFutures = bl;
    }

    public boolean isExactMatch() {
        return this.exactMatch;
    }

    public void setExactMatch(boolean bl) {
        this.exactMatch = bl;
    }
}

