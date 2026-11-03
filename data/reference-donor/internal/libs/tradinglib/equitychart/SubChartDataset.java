/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.equitychart.ChartDataset;
import com.strategyquant.tradinglib.equitychart.ChartOptimalizer;
import com.strategyquant.tradinglib.equitychart.Zoom;
import org.json.JSONArray;
import org.json.JSONObject;

public class SubChartDataset
extends ChartDataset {
    private String name;

    public SubChartDataset(String string, int n) {
        super(string, n);
    }

    @Override
    public JSONObject toJSON(Zoom zoom, boolean bl) {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        JSONArray jSONArray2 = new JSONArray();
        ChartOptimalizer.OptimizerResult optimizerResult = new ChartOptimalizer().optimalize(bl, this.xVals, this.yVals, zoom.getMin(this.xVals), zoom.getMax(this.xVals), zoom.width);
        for (int i = 0; i < optimizerResult.size(); ++i) {
            jSONArray.put(bl ? this.formatTime(optimizerResult.xVals[i]) : Long.valueOf(optimizerResult.xVals[i]));
            jSONArray2.put(this.d(optimizerResult.yVals[i]));
        }
        jSONObject.put("title", (Object)this.name);
        jSONObject.put("type", (Object)this.type);
        jSONObject.put("color", (Object)this.color);
        jSONObject.put("thickness", this.thickness);
        jSONObject.put("xVals", (Object)jSONArray);
        jSONObject.put("yVals", (Object)jSONArray2);
        return jSONObject;
    }

    @Override
    public void fillJSON(JsonCreator jsonCreator, Zoom zoom, boolean bl) {
        int n;
        jsonCreator.put("title", (Object)this.name, true);
        jsonCreator.put("type", (Object)this.type, true);
        jsonCreator.put("color", (Object)this.color, true);
        if (this.colorDark != null) {
            jsonCreator.put("color_dark", (Object)this.color, true);
        }
        jsonCreator.put("thickness", (Object)this.thickness, true);
        ChartOptimalizer.OptimizerResult optimizerResult = new ChartOptimalizer().optimalize(bl, this.xVals, this.yVals, zoom.getMin(this.xVals), zoom.getMax(this.xVals), zoom.width);
        jsonCreator.putBeginArray("xVals");
        for (n = 0; n < optimizerResult.size(); ++n) {
            jsonCreator.setValue(bl ? this.formatTime(optimizerResult.xVals[n]) : Long.valueOf(optimizerResult.xVals[n]), n < optimizerResult.size() - 1);
        }
        jsonCreator.endArray(true);
        jsonCreator.putBeginArray("yVals");
        for (n = 0; n < optimizerResult.size(); ++n) {
            jsonCreator.setValue((Object)this.d(optimizerResult.yVals[n]), n < optimizerResult.size() - 1);
        }
        jsonCreator.endArray(false);
    }

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }
}

