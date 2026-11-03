/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

public class ProjectConditionField {
    public static final String DATABANK = "databank";
    public static final String NUMBER = "number";
    public static final String DURATION = "duration";
    public static final String COMPARATOR = "comparator";
    private String type;
    private String name;
    private String defaultValue;

    public ProjectConditionField(String string, String string2, String string3) {
        this.type = string;
        this.name = string2;
        this.defaultValue = string3;
    }

    public String getType() {
        return this.type;
    }

    public String getName() {
        return this.name;
    }

    public String getDefaultValue() {
        return this.defaultValue;
    }
}

