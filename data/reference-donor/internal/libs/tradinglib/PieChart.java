/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.AbstractChart;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

public class PieChart
extends AbstractChart {
    private ArrayList<Section> sections = new ArrayList();

    public PieChart() {
        super("pie");
    }

    public void addValue(String string, Number number, String string2) {
        Section section = new Section(string, number, string2);
        this.sections.add(section);
    }

    public Section getSectionByLabel(String string) {
        for (int i = 0; i < this.sections.size(); ++i) {
            Section section = this.sections.get(i);
            if (!section.label.equals(string)) continue;
            return section;
        }
        return null;
    }

    @Override
    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        JSONObject jSONObject2 = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        JSONArray jSONArray2 = new JSONArray();
        JSONArray jSONArray3 = new JSONArray();
        JSONArray jSONArray4 = new JSONArray();
        JSONObject jSONObject3 = new JSONObject();
        for (int i = 0; i < this.sections.size(); ++i) {
            Section section = this.sections.get(i);
            jSONArray2.put((Object)section.value);
            jSONArray3.put((Object)section.label);
            jSONArray4.put((Object)section.color);
        }
        jSONObject3.put("label", (Object)"");
        jSONObject3.put("backgroundColor", (Object)jSONArray4);
        jSONObject3.put("data", (Object)jSONArray2);
        jSONArray.put((Object)jSONObject3);
        jSONObject2.put("labels", (Object)jSONArray3);
        jSONObject2.put("datasets", (Object)jSONArray);
        jSONObject.put("data", (Object)jSONObject2);
        jSONObject.put("options", (Object)this.getOptions());
        jSONObject.put("type", (Object)this.type);
        return jSONObject;
    }

    private class Section {
        public String label;
        public Number value;
        public String color;

        public Section(String string, Number number, String string2) {
            this.label = string;
            this.value = number;
            this.color = string2;
        }
    }
}

