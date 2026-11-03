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
import java.util.ArrayList;
import java.util.HashMap;
import org.json.JSONArray;
import org.json.JSONObject;

public class BarChart
extends AbstractXYChart {
    protected ArrayList<CategoryValue> values = new ArrayList();
    protected ArrayList<String> categories = new ArrayList();
    protected HashMap<String, String> categoryColors = new HashMap();
    protected HashMap<Comparable, String> individualColors = new HashMap();

    public BarChart() {
        super("bar");
    }

    public void addValue(String string, Comparable comparable, Number number) {
        CategoryValue categoryValue = new CategoryValue(string, comparable, number);
        this.values.add(categoryValue);
        if (!this.categories.contains(string)) {
            this.categories.add(string);
        }
    }

    public void addValue(String string, Comparable comparable, Number number, String string2) {
        CategoryValue categoryValue = new CategoryValue(string, comparable, number);
        this.values.add(categoryValue);
        if (!this.categories.contains(string)) {
            this.categories.add(string);
        }
        this.individualColors.put(comparable, string2);
    }

    public void setCategoryColor(String string, String string2) {
        this.categoryColors.put(string, string2);
    }

    @Override
    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        JSONObject jSONObject2 = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        JSONArray jSONArray2 = new JSONArray();
        for (int i = 0; i < this.categories.size(); ++i) {
            String string = this.categories.get(i);
            JSONObject jSONObject3 = new JSONObject();
            JSONArray jSONArray3 = new JSONArray();
            JSONArray jSONArray4 = new JSONArray();
            jSONArray2 = new JSONArray();
            for (int j = 0; j < this.values.size(); ++j) {
                CategoryValue categoryValue = this.values.get(j);
                if (!categoryValue.name.equals(string)) continue;
                jSONArray2.put((Object)categoryValue.x);
                jSONArray3.put((Object)SQUtils.d2((Number)categoryValue.y));
                if (this.individualColors.containsKey(categoryValue.x)) {
                    jSONArray4.put((Object)this.individualColors.get(categoryValue.x));
                    continue;
                }
                if (this.categoryColors.containsKey(string)) {
                    jSONArray4.put((Object)this.categoryColors.get(string));
                    continue;
                }
                if (this.invertIfNegative) {
                    jSONArray4.put((Object)(categoryValue.y.doubleValue() >= 0.0 ? "#008000" : "#E8383C"));
                    continue;
                }
                jSONArray4.put((Object)"#383CE8");
            }
            jSONObject3.put("backgroundColor", (Object)jSONArray4);
            jSONObject3.put("label", (Object)string);
            jSONObject3.put("data", (Object)jSONArray3);
            jSONArray.put((Object)jSONObject3);
        }
        jSONObject2.put("labels", (Object)jSONArray2);
        jSONObject2.put("datasets", (Object)jSONArray);
        jSONObject.put("data", (Object)jSONObject2);
        jSONObject.put("options", (Object)this.getOptions());
        jSONObject.put("type", (Object)this.type);
        return jSONObject;
    }

    public class CategoryValue {
        public String name;
        public Comparable x;
        public Number y;

        public CategoryValue(String string, Comparable comparable, Number number) {
            this.name = string;
            this.x = comparable;
            this.y = number;
        }
    }
}

