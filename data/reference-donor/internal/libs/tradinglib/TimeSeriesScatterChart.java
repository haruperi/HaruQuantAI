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
import com.strategyquant.tradinglib.AbstractChart;
import com.strategyquant.tradinglib.TimeSeries;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

public class TimeSeriesScatterChart
extends AbstractChart {
    private ArrayList<TimeSeries> seriesCollection = new ArrayList();

    public TimeSeriesScatterChart() {
        super("scatter");
    }

    public void addSeries(TimeSeries timeSeries) {
        this.seriesCollection.add(timeSeries);
    }

    public TimeSeries getSeries(int n) {
        return this.seriesCollection.get(n);
    }

    public ArrayList<TimeSeries> getSeriesCollection() {
        return this.seriesCollection;
    }

    @Override
    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        JSONObject jSONObject2 = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        for (int i = 0; i < this.seriesCollection.size(); ++i) {
            TimeSeries timeSeries = this.seriesCollection.get(i);
            JSONObject jSONObject3 = new JSONObject();
            JSONArray jSONArray2 = new JSONArray();
            for (int j = 0; j < timeSeries.values.size(); ++j) {
                XYValue xYValue = (XYValue)timeSeries.values.get(j);
                JSONObject jSONObject4 = new JSONObject().put("x", xYValue.x).put("y", (Object)SQUtils.d2((double)xYValue.y));
                jSONArray2.put((Object)jSONObject4);
            }
            if (timeSeries.color != null) {
                jSONObject3.put("borderColor", (Object)timeSeries.color);
                jSONObject3.put("backgroundColor", (Object)timeSeries.color);
            }
            jSONObject3.put("borderWidth", 0.5);
            jSONObject3.put("label", (Object)timeSeries.name);
            jSONObject3.put("data", (Object)jSONArray2);
            jSONObject3.put("fill", (Object)"start");
            jSONObject3.put("lineTension", 0);
            jSONArray.put((Object)jSONObject3);
        }
        jSONObject2.put("datasets", (Object)jSONArray);
        jSONObject.put("data", (Object)jSONObject2);
        jSONObject.put("options", (Object)this.getOptions());
        jSONObject.put("type", (Object)this.type);
        return jSONObject;
    }
}

