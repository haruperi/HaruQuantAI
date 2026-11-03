/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

public class MassImportDataInfo {
    private String timezone;
    private int barType;
    private String path;
    private String format;
    private OverwriteStrategy overwriteStrategy;
    private String instrument;
    private String connection;
    private String postfix;
    private String dateFormat;
    private boolean createStockGroup;
    private String timeframe;

    public String getPath() {
        return this.path;
    }

    public void setPath(String string) {
        this.path = string;
    }

    public String getFormat() {
        return this.format;
    }

    public void setFormat(String string) {
        this.format = string;
    }

    public OverwriteStrategy getOverwriteStrategy() {
        return this.overwriteStrategy;
    }

    public void setOverwriteStrategy(OverwriteStrategy overwriteStrategy) {
        this.overwriteStrategy = overwriteStrategy;
    }

    public int getBarType() {
        return this.barType;
    }

    public void setBarType(int n) {
        this.barType = n;
    }

    public String getInstrument() {
        return this.instrument;
    }

    public void setInstrument(String string) {
        this.instrument = string;
    }

    public String getTimezone() {
        return this.timezone;
    }

    public void setTimezone(String string) {
        this.timezone = string;
    }

    public String getConnection() {
        return this.connection;
    }

    public void setConnection(String string) {
        this.connection = string;
    }

    public String getPostfix() {
        return this.postfix;
    }

    public void setPostfix(String string) {
        this.postfix = string;
    }

    public boolean isCreateStockGroup() {
        return this.createStockGroup;
    }

    public void setCreateStockGroup(boolean bl) {
        this.createStockGroup = bl;
    }

    public String getDateFormat() {
        return this.dateFormat;
    }

    public void setDateFormat(String string) {
        this.dateFormat = string;
    }

    public String getTimeframe() {
        return this.timeframe;
    }

    public void setTimeframe(String string) {
        this.timeframe = string;
    }

    public static enum OverwriteStrategy {
        overwrite,
        skip,
        create;

    }
}

