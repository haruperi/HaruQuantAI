/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.indicators;

public class SParameter {
    public String name;
    public String type;
    public String value;
    public int index;

    public SParameter(String string, String string2, String string3, int n) {
        this.name = string;
        this.type = string2;
        this.value = string3;
        this.index = n;
        this.adjustParameterData();
    }

    private void adjustParameterData() {
        if (this.type.contains("bool")) {
            this.type = "boolean";
        }
        if (this.value == null) {
            this.value = "0";
            if (this.type.equals("string")) {
                this.value = "";
            }
            if (this.type.contains("bool")) {
                this.value = "false";
            }
            if (this.type.equals("color")) {
                this.value = "Red";
            }
        } else if (this.type.contains("bool")) {
            this.value = this.value.toLowerCase();
        }
    }

    public String toString() {
        return "name: " + this.name + ", type: " + this.type + ", value: " + this.value + ", index: " + this.index;
    }
}

