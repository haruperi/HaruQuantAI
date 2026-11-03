/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.charts;

import com.strategyquant.tradinglib.AbstractChart;
import org.json.JSONArray;
import org.json.JSONObject;

public abstract class AbstractXYChart
extends AbstractChart {
    public String xAxisTitle = null;
    public String xAxisType = null;
    public String xAxisTickformat = null;
    public double xAxisRangeMin = -1.0;
    public double xAxisRangeMax = -1.0;
    public String yAxisTitle = null;
    public double yAxisRangeMin = -1.0;
    public double yAxisRangeMax = -1.0;
    public int maxXTicksLimit = -1;
    public int maxYTicksLimit = -1;
    public boolean invertIfNegative = false;
    public int fontSize = 11;
    public boolean tooltips = true;
    public boolean displayXAxesLabels = true;
    public boolean displayYAxesLabels = true;
    public boolean disableEvents = false;
    public int pointRadius = 0;

    public AbstractXYChart(String string) {
        super(string);
    }

    @Override
    public JSONObject getOptions() {
        JSONObject jSONObject = super.getOptions();
        jSONObject.put("elements", (Object)new JSONObject().put("point", (Object)new JSONObject().put("radius", this.pointRadius)));
        JSONObject jSONObject2 = new JSONObject();
        jSONObject.put("scales", (Object)jSONObject2);
        jSONObject2.put("xAxes", (Object)new JSONArray().put((Object)new JSONObject().put("display", this.displayXAxesLabels).put("scaleLabel", (Object)new JSONObject().put("display", this.xAxisTitle != null).put("labelString", (Object)this.xAxisTitle).put("fontSize", this.fontSize)).put("gridLines", (Object)new JSONObject().put("display", false))));
        jSONObject2.put("yAxes", (Object)new JSONArray().put((Object)new JSONObject().put("display", this.displayYAxesLabels).put("scaleLabel", (Object)new JSONObject().put("display", this.yAxisTitle != null).put("labelString", (Object)this.yAxisTitle).put("fontSize", this.fontSize)).put("gridLines", (Object)new JSONObject().put("display", false))));
        jSONObject2.getJSONArray("xAxes").getJSONObject(0).put("ticks", (Object)new JSONObject().put("autoSkip", true).put("fontSize", this.fontSize));
        jSONObject2.getJSONArray("yAxes").getJSONObject(0).put("ticks", (Object)new JSONObject().put("fontSize", this.fontSize));
        if (this.xAxisRangeMin != -1.0 && this.xAxisRangeMax != -1.0) {
            jSONObject2.getJSONArray("xAxes").getJSONObject(0).getJSONObject("ticks").put("min", this.xAxisRangeMin).put("max", this.xAxisRangeMax);
        }
        if (this.yAxisRangeMin != -1.0) {
            jSONObject2.getJSONArray("yAxes").getJSONObject(0).getJSONObject("ticks").put("min", this.yAxisRangeMin);
        }
        if (this.yAxisRangeMax != -1.0) {
            jSONObject2.getJSONArray("yAxes").getJSONObject(0).getJSONObject("ticks").put("max", this.yAxisRangeMax);
        }
        if (this.type.equals("bar")) {
            jSONObject2.getJSONArray("yAxes").getJSONObject(0).getJSONObject("ticks").put("beginAtZero", true);
        }
        if (this.maxXTicksLimit != -1) {
            jSONObject2.getJSONArray("xAxes").getJSONObject(0).getJSONObject("ticks").put("maxTicksLimit", this.maxXTicksLimit);
        }
        if (this.maxYTicksLimit != -1) {
            jSONObject2.getJSONArray("yAxes").getJSONObject(0).getJSONObject("ticks").put("maxTicksLimit", this.maxYTicksLimit);
        }
        if (this.xAxisType != null) {
            jSONObject2.getJSONArray("xAxes").getJSONObject(0).put("type", (Object)this.xAxisType);
            if (this.xAxisType != null && this.xAxisType.equals("time")) {
                jSONObject2.getJSONArray("xAxes").getJSONObject(0).put("time", (Object)new JSONObject().put("displayFormats", (Object)new JSONObject().put("second", (Object)this.xAxisTickformat)));
                jSONObject2.getJSONArray("xAxes").getJSONObject(0).getJSONObject("ticks").put("maxRotation", 0);
            }
        }
        if (this.type.equals("line")) {
            jSONObject2.getJSONArray("xAxes").getJSONObject(0).put("bounds", (Object)"data");
        }
        if (!this.tooltips) {
            jSONObject.put("tooltips", (Object)new JSONObject().put("enabled", false));
        }
        if (this.disableEvents) {
            jSONObject.put("events", (Object)new JSONArray());
        }
        return jSONObject;
    }

    public void invertIfNegative(boolean bl) {
        this.invertIfNegative = true;
    }
}

