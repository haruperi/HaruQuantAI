/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.databank;

import org.json.JSONObject;

public class DatabankColumnTypes {
    public static final byte GENERAL = 0;
    public static final byte ORIGINAL = 10;
    public static final byte WF = 30;
    public static final byte WF_STABILITY = 31;
    public static final byte WF_SCORE = 32;
    public static final byte WF_SPECIAL = 33;
    public static final String WF_TEXT = "WF";
    public static final String WF_STABILITY_TEXT = "WF Stability of";
    public static final String WF_SCORE_TEXT = "WF Score of";
    public static final String WF_SPECIAL_TEXT = "WF Special - ";
    public static final String CATEGORY_ORIGINAL = "Original";
    public static final String CATEGORY_RT = "RT";
    public static final String CATEGORY_WF = "WF";

    public static JSONObject toJSONObject() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("general", (Object)new JSONObject().put("value", 0).put("category", (Object)"General").put("dataType", (Object)"default"));
        jSONObject.put("original", (Object)new JSONObject().put("value", 10).put("category", (Object)CATEGORY_ORIGINAL).put("dataType", (Object)"default"));
        jSONObject.put("wf", (Object)new JSONObject().put("value", 30).put("category", (Object)"WF").put("dataType", (Object)"default"));
        jSONObject.put("wfStability", (Object)new JSONObject().put("value", 31).put("category", (Object)"WF Stability").put("dataType", (Object)"Decimal2Pct"));
        jSONObject.put("wfScore", (Object)new JSONObject().put("value", 32).put("category", (Object)"WF Score").put("dataType", (Object)"Decimal2Pct"));
        jSONObject.put("wfSpecial", (Object)new JSONObject().put("value", 33).put("category", (Object)"WF Special").put("dataType", (Object)"default"));
        return jSONObject;
    }

    public static String typeToString(byte by) {
        switch (by) {
            case 0: {
                return "General";
            }
            case 10: {
                return CATEGORY_ORIGINAL;
            }
            case 30: {
                return "WF";
            }
            case 31: {
                return WF_STABILITY_TEXT;
            }
            case 32: {
                return WF_SCORE_TEXT;
            }
            case 33: {
                return WF_SPECIAL_TEXT;
            }
        }
        return "?";
    }
}

