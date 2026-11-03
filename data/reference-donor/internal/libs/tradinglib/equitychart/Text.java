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

public class Text {
    public String text;
    public String color;
    public String font;
    public int x;
    public int y;

    public Text(String string, String string2, String string3, int n, int n2) {
        this.text = string;
        this.color = string2;
        this.font = string3;
        this.x = n;
        this.y = n2;
    }

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("text", (Object)this.text);
        jSONObject.put("color", (Object)this.color);
        jSONObject.put("font", (Object)this.font);
        jSONObject.put("x", this.x);
        jSONObject.put("y", this.y);
        return jSONObject;
    }

    public void fillJSON(JsonCreator jsonCreator) {
        jsonCreator.put("text", (Object)this.text, true);
        jsonCreator.put("color", (Object)this.color, true);
        jsonCreator.put("font", (Object)this.font, true);
        jsonCreator.put("x", (Object)this.x, true);
        jsonCreator.put("y", (Object)this.y, false);
    }
}

