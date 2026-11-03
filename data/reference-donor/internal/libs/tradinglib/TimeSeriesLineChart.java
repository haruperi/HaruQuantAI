/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.TimeSeries;
import com.strategyquant.tradinglib.charts.AbstractXYChart;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import com.strategyquant.tradinglib.equitychart.ChartOptimalizer;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TimeSeriesLineChart
extends AbstractXYChart {
    public static final Logger Log = LoggerFactory.getLogger(TimeSeriesLineChart.class);
    private ArrayList<TimeSeries> seriesCollection = new ArrayList();
    public static final int PointsCount = 1000;
    public static final int OptimPointsCount = 20;

    public TimeSeriesLineChart() {
        super("line");
        this.xAxisType = "time";
        this.xAxisTickformat = "HH:mm";
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
        JSONArray jSONArray2 = new JSONArray();
        for (int i = 0; i < this.seriesCollection.size(); ++i) {
            Object object;
            TimeSeries timeSeries = this.seriesCollection.get(i);
            JSONObject jSONObject3 = new JSONObject();
            JSONArray jSONArray3 = new JSONArray();
            int n = timeSeries.values.size();
            if (n > 20) {
                long[] lArray = new long[n];
                object = new double[n];
                for (int j = 0; j < n; ++j) {
                    lArray[j] = ((XYValue)timeSeries.values.get((int)j)).x;
                    object[j] = ((XYValue)timeSeries.values.get((int)j)).y;
                }
                ChartOptimalizer.OptimizerResult optimizerResult = new ChartOptimalizer().optimalize(false, lArray, (double[])object, null, null, 20);
                for (int j = 0; j < optimizerResult.size(); ++j) {
                    if (optimizerResult.xVals[j] == 0L) continue;
                    jSONArray3.put((Object)new JSONObject().put("x", optimizerResult.xVals[j]).put("y", (Object)SQUtils.d2((double)optimizerResult.yVals[j])));
                }
            } else {
                for (int j = 0; j < n; ++j) {
                    object = (XYValue)timeSeries.values.get(j);
                    jSONArray3.put((Object)new JSONObject().put("x", object.x).put("y", (Object)SQUtils.d2((double)object.y)));
                }
            }
            if (timeSeries.color != null) {
                jSONObject3.put("borderColor", (Object)timeSeries.color);
            }
            jSONArray2.put((Object)timeSeries.name);
            jSONObject3.put("borderWidth", 0.5);
            jSONObject3.put("label", (Object)timeSeries.name);
            jSONObject3.put("data", (Object)jSONArray3);
            jSONObject3.put("fill", false);
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

