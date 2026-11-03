/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project;

import org.json.JSONObject;

public class TaskStat {
    public static String BAR = "bar";
    public static String MILLISECONDS = "milliseconds";
    public String action;
    public String display;
    public long count;
    public int order;
    public String percentageCompareAction;

    public JSONObject getJSONObject() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("display", (Object)this.display);
        jSONObject.put("action", (Object)this.action);
        jSONObject.put("count", this.count);
        jSONObject.put("order", this.order);
        jSONObject.put("percentageCompareAction", (Object)this.percentageCompareAction);
        return jSONObject;
    }
}

