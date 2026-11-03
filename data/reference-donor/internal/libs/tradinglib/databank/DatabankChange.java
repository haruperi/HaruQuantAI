/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.databank;

import org.json.JSONArray;
import org.json.JSONObject;

public class DatabankChange {
    public static final String ADD = "add";
    public static final String REMOVE = "remove";
    public static final String UPDATE = "update";
    public static final String RESET = "reset";
    public static final String CLEARALL = "clearAll";
    public static final String CONST_REFRESH_GRID = "refreshGrid";
    String type = "";
    String id;
    Object[] data = new Object[500];
    String extraValue;
    long time;

    public void update(String string, String string2, Object[] objectArray) {
        this.type = string;
        this.id = string2;
        this.time = System.currentTimeMillis();
        for (int i = 0; i < this.data.length; ++i) {
            this.data[i] = objectArray == null || i >= objectArray.length ? null : objectArray[i];
        }
    }

    public DatabankChange setExtraValue(String string) {
        this.extraValue = string;
        return this;
    }

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("type", (Object)this.type);
        jSONObject.put("id", (Object)this.id);
        jSONObject.put("time", this.time);
        jSONObject.put("extraValue", (Object)this.extraValue);
        JSONArray jSONArray = new JSONArray();
        if (this.data != null) {
            Object object;
            for (int i = 0; i < this.data.length && (object = this.data[i]) != null; ++i) {
                try {
                    jSONArray.put((Object)object.toString());
                    continue;
                }
                catch (Exception exception) {
                    jSONArray.put((Object)"N/A");
                }
            }
        }
        jSONObject.put("data", (Object)jSONArray);
        return jSONObject;
    }
}

