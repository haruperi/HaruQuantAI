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

public class AreaFill {
    public long xFrom;
    public long xTo;
    public String color = "#999";
    public String colorDark = "#999";
    public String text = "";
    public String textColor = "black";
    public String textColorDark = "#ddd";
    public String verticalAlign = "top";
    public String borderColor = null;
    public String borderColorDark = null;
    public int borderThickness = 1;
    public boolean borderOnly = false;

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("xFrom", this.xFrom);
        jSONObject.put("xTo", this.xTo);
        jSONObject.put("color", (Object)this.color);
        jSONObject.put("text", (Object)this.text);
        jSONObject.put("textColor", (Object)this.textColor);
        jSONObject.put("textColor_dark", (Object)this.textColorDark);
        jSONObject.put("verticalAlign", (Object)this.verticalAlign);
        jSONObject.put("borderThickness", this.borderThickness);
        jSONObject.put("borderOnly", this.borderOnly);
        if (this.borderColor != null) {
            jSONObject.put("borderColor", (Object)this.borderColor);
        }
        if (this.borderColorDark != null) {
            jSONObject.put("borderColor_dark", (Object)this.borderColorDark);
        }
        return jSONObject;
    }

    public void fillJSON(JsonCreator jsonCreator) {
        jsonCreator.put("xFrom", (Object)this.xFrom, true);
        jsonCreator.put("xTo", (Object)this.xTo, true);
        jsonCreator.put("color", (Object)this.color, true);
        jsonCreator.put("color_dark", (Object)this.colorDark, true);
        jsonCreator.put("text", (Object)this.text, true);
        jsonCreator.put("textColor", (Object)this.textColor, true);
        jsonCreator.put("textColor_dark", (Object)this.textColorDark, true);
        jsonCreator.put("verticalAlign", (Object)this.verticalAlign, true);
        jsonCreator.put("borderThickness", (Object)this.borderThickness, true);
        if (this.borderColor != null) {
            jsonCreator.put("borderColor", (Object)this.borderColor, true);
        }
        if (this.borderColorDark != null) {
            jsonCreator.put("borderColor_dark", (Object)this.borderColorDark, true);
        }
        jsonCreator.put("borderOnly", (Object)this.borderOnly, false);
    }
}

