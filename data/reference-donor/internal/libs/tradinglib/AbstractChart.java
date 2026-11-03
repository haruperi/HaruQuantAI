/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib;

import org.json.JSONObject;

public abstract class AbstractChart {
    public String type = null;
    public String title = null;
    public boolean showLegend = false;
    public boolean xAxisTicksDurationInMS = false;
    public boolean yAxisTicksMemory = false;
    public boolean categoryAxis = false;

    public AbstractChart(String string) {
        this.type = string;
    }

    public abstract JSONObject toJSON();

    public JSONObject getOptions() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("xAxisTicksDurationInMS", this.xAxisTicksDurationInMS);
        jSONObject.put("yAxisTicksMemory", this.yAxisTicksMemory);
        jSONObject.put("animation", false);
        jSONObject.put("title", (Object)new JSONObject().put("display", this.title != null).put("text", (Object)this.title));
        jSONObject.put("legend", (Object)new JSONObject().put("display", this.showLegend).put("position", (Object)"bottom").put("labels", (Object)new JSONObject().put("fontSize", 10).put("boxWidth", 15)));
        jSONObject.put("responsive", true);
        jSONObject.put("maintainAspectRatio", false);
        return jSONObject;
    }
}

