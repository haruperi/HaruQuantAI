/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.utils.JsonCreator;
import org.json.JSONObject;

public class Marker {
    public String color = "red";
    public long x;
    public int thickness = 1;

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("color", (Object)this.color);
        jSONObject.put("x", this.x);
        jSONObject.put("thickness", this.thickness);
        return jSONObject;
    }

    public void fillJSON(JsonCreator jsonCreator) {
        jsonCreator.put("color", (Object)this.color, true);
        jsonCreator.put("x", (Object)this.x, true);
        jsonCreator.put("thickness", (Object)this.thickness, false);
    }
}

