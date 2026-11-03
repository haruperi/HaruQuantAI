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
import com.strategyquant.tradinglib.equitychart.SubChartDataset;
import com.strategyquant.tradinglib.equitychart.Zoom;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

public class SubChart {
    public String key;
    public String name = "";
    public int weight = 10;
    public boolean hideYValues = false;
    public boolean hideYTitle = false;
    public String titlePosition = null;
    public boolean forceStartYFromZero = false;
    public ArrayList<SubChartDataset> datasets = new ArrayList();

    public SubChart(String string) {
        this.key = string;
    }

    public void addDataset(SubChartDataset subChartDataset) {
        this.datasets.add(subChartDataset);
    }

    public JSONObject toJSON(Zoom zoom, boolean bl) {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        for (int i = 0; i < this.datasets.size(); ++i) {
            SubChartDataset subChartDataset = this.datasets.get(i);
            jSONArray.put((Object)subChartDataset.toJSON(zoom, bl));
        }
        jSONObject.put("title", (Object)this.name);
        jSONObject.put("weight", this.weight);
        jSONObject.put("hideYValues", this.hideYValues);
        jSONObject.put("hideYTitle", this.hideYTitle);
        jSONObject.put("datasets", (Object)jSONArray);
        jSONObject.put("forceStartYFromZero", this.forceStartYFromZero);
        if (this.titlePosition != null) {
            jSONObject.put("titlePosition", (Object)this.titlePosition);
        }
        return jSONObject;
    }

    public void fillJSON(JsonCreator jsonCreator, Zoom zoom, boolean bl) {
        jsonCreator.put("title", (Object)this.name, true);
        jsonCreator.put("weight", (Object)this.weight, true);
        jsonCreator.put("hideYValues", (Object)this.hideYValues, true);
        jsonCreator.put("hideYTitle", (Object)this.hideYTitle, true);
        jsonCreator.put("forceStartYFromZero", (Object)this.forceStartYFromZero, true);
        if (this.titlePosition != null) {
            jsonCreator.put("titlePosition", (Object)this.titlePosition, true);
        }
        jsonCreator.putBeginArray("datasets");
        for (int i = 0; i < this.datasets.size(); ++i) {
            SubChartDataset subChartDataset = this.datasets.get(i);
            jsonCreator.beginObject();
            subChartDataset.fillJSON(jsonCreator, zoom, bl);
            jsonCreator.endObject(i < this.datasets.size() - 1);
        }
        jsonCreator.endArray(false);
    }
}

