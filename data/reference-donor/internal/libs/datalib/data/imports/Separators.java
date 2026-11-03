/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.datalib.data.imports;

import org.json.JSONArray;
import org.json.JSONObject;

public class Separators {
    public static final String TYPE_COMMA = "COMMA";
    public static final String VALUE_COMMA = ",";
    public static final String TYPE_SEMICOLON = "SEMICOLON";
    public static final String VALUE_SEMICOLON = ";";
    public static final String TYPE_TAB = "TAB";
    public static final String VALUE_TAB = "\t";
    public static final String TYPE_SPACE = "SPACE";
    public static final String VALUE_SPACE = " ";
    private static final String[] types = new String[]{"COMMA", "SEMICOLON", "TAB", "SPACE"};
    private static final String[] values = new String[]{",", ";", "\t", " "};

    public static String[] listTypes() {
        return types;
    }

    public static String[] listValues() {
        return values;
    }

    public static String getValue(String string) {
        for (int i = 0; i < types.length; ++i) {
            if (!types[i].equals(string)) continue;
            return values[i];
        }
        return string;
    }

    public static String getType(String string) {
        for (int i = 0; i < values.length; ++i) {
            if (!values[i].equals(string)) continue;
            return types[i];
        }
        return string;
    }

    public static JSONArray toJSON() {
        JSONArray jSONArray = new JSONArray();
        for (int i = 0; i < types.length; ++i) {
            jSONArray.put((Object)new JSONObject().put("type", (Object)types[i]).put("value", (Object)values[i]));
        }
        return jSONArray;
    }
}

