/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.charts.AbstractXYChart;
import com.strategyquant.tradinglib.charts.linechart.series.XYSeries;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

public class XYLineChart
extends AbstractXYChart {
    private ArrayList<XYSeries> seriesCollection = new ArrayList();

    public XYLineChart() {
        super("line");
    }

    public void addSeries(XYSeries xYSeries) {
        this.seriesCollection.add(xYSeries);
    }

    public XYSeries getSeries(int n) {
        return this.seriesCollection.get(n);
    }

    @Override
    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        JSONObject jSONObject2 = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        JSONArray jSONArray2 = new JSONArray();
        for (int i = 0; i < this.seriesCollection.size(); ++i) {
            XYSeries xYSeries = this.seriesCollection.get(i);
            JSONObject jSONObject3 = new JSONObject();
            JSONArray jSONArray3 = new JSONArray();
            for (int j = 0; j < xYSeries.values.size(); ++j) {
                XYValue xYValue = (XYValue)xYSeries.values.get(j);
                if (this.categoryAxis) {
                    jSONArray3.put((Object)SQUtils.d2((double)xYValue.y));
                    if (i != 0) continue;
                    jSONArray2.put((Object)xYValue.xLabel);
                    continue;
                }
                JSONObject jSONObject4 = new JSONObject().put("x", xYValue.x).put("y", (Object)SQUtils.d2((double)xYValue.y));
                jSONArray3.put((Object)jSONObject4);
            }
            if (xYSeries.color != null) {
                jSONObject3.put("borderColor", (Object)xYSeries.color);
            }
            jSONObject3.put("borderWidth", 0.5);
            jSONObject3.put("label", (Object)xYSeries.name);
            jSONObject3.put("data", (Object)jSONArray3);
            jSONObject3.put("fill", false);
            jSONObject3.put("lineTension", 0);
            jSONArray.put((Object)jSONObject3);
        }
        if (this.categoryAxis) {
            jSONObject2.put("labels", (Object)jSONArray2);
        }
        jSONObject2.put("datasets", (Object)jSONArray);
        jSONObject.put("data", (Object)jSONObject2);
        jSONObject.put("options", (Object)this.getOptions());
        jSONObject.put("type", (Object)this.type);
        return jSONObject;
    }
}

