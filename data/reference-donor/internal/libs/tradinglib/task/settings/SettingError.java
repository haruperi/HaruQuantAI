/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.task.settings;

public class SettingError {
    public String settingName;
    public String fieldName;
    public String errorMsg;

    public SettingError(String string, String string2, String string3) {
        this.settingName = string;
        this.fieldName = string2;
        this.errorMsg = string3;
    }
}

