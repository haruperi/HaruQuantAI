/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.indicatorTester;

import org.json.JSONObject;

public class IndyParameter {
    public String name;
    public String className;
    public String defaultValue;
    public String value;
    public String options;
    public String calibrationValues;

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("name", (Object)this.name);
        jSONObject.put("className", (Object)this.className);
        jSONObject.put("defaultValue", (Object)this.defaultValue);
        jSONObject.put("value", (Object)this.value);
        jSONObject.put("options", (Object)this.options);
        jSONObject.put("calibrationValues", (Object)this.calibrationValues);
        return jSONObject;
    }
}

