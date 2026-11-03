/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

public abstract class DefaultCol {
    private String name;
    private String code;

    public DefaultCol(String string, String string2) {
        this.name = string;
        this.code = string2;
    }

    public String getName() {
        return this.name;
    }

    public String getCode() {
        return this.code;
    }

    public String getClassName() {
        return this.getClass().getSimpleName();
    }

    public abstract int getType();

    public abstract int getDataType();
}

