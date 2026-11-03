/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.indicatorTester.CalibrationRangesInfo;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

public class CalibrationInfo {
    public String key;
    public String name;
    public ArrayList<CalibrationRangesInfo> ranges = new ArrayList();

    public CalibrationInfo(String string) {
        this.key = string;
    }

    public void addRange(String string, String string2, double d, double d2) {
        this.ranges.add(new CalibrationRangesInfo(string, string2, d, d2));
    }

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("key", (Object)this.key);
        jSONObject.put("name", (Object)this.name);
        JSONArray jSONArray = new JSONArray();
        for (int i = 0; i < this.ranges.size(); ++i) {
            CalibrationRangesInfo calibrationRangesInfo = this.ranges.get(i);
            jSONArray.put((Object)calibrationRangesInfo.toJSON());
        }
        jSONObject.put("ranges", (Object)jSONArray);
        return jSONObject;
    }
}

