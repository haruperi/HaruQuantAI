/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.DataSource.impl.Dukascopy;

public class DukasExport {
    private long dateFrom;
    private long dateTo;
    private String targetFolder;
    private String symbol;
    private String filenamePrefix;

    public long getDateFrom() {
        return this.dateFrom;
    }

    public void setDateFrom(long dateFrom) {
        this.dateFrom = dateFrom;
    }

    public long getDateTo() {
        return this.dateTo;
    }

    public void setDateTo(long dateTo) {
        this.dateTo = dateTo;
    }

    public String getTargetFolder() {
        return this.targetFolder;
    }

    public void setTargetFolder(String targetFolder) {
        this.targetFolder = targetFolder;
    }

    public String getSymbol() {
        return this.symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public String getFilenamePrefix() {
        return this.filenamePrefix;
    }

    public void setFilenamePrefix(String filenamePrefix) {
        this.filenamePrefix = filenamePrefix;
    }
}

