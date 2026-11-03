/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.datalib.metatrader4;

import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;

public class Mt4SymbolProperties {
    private Map<String, String> values = new HashMap<String, String>();

    public String getStrValue(String string) {
        String string2 = this.values.get(string.toLowerCase());
        if (string2 != null) {
            return string2;
        }
        throw new IllegalStateException("record with key:" + string + " was not found");
    }

    public boolean exists(String string) {
        return this.values.get(string) != null;
    }

    public int getIntValue(String string) {
        return Integer.parseInt(this.getStrValue(string));
    }

    public double getDoubleValue(String string) {
        return Double.parseDouble(this.getStrValue(string));
    }

    public void put(String string, String string2) {
        this.values.put(string, string2);
    }

    public void parse(String string) {
        String[] stringArray;
        for (String string2 : stringArray = string.split("\\|")) {
            String[] stringArray2 = string2.split("=");
            if (stringArray2.length != 2) continue;
            this.put(stringArray2[0], stringArray2[1]);
        }
        this.checkParams();
    }

    private void checkParams() {
        if (this.getDoubleValue("lot_step") == 0.0) {
            this.put("lot_step", "0.01");
        }
    }

    public JSONArray toJSON() {
        JSONArray jSONArray = new JSONArray();
        for (String string : this.values.keySet()) {
            String string2 = this.values.get(string);
            jSONArray.put((Object)new JSONObject().put(string, (Object)string2));
        }
        return jSONArray;
    }

    public String toString() {
        String string = "";
        int n = 0;
        for (String string2 : this.values.keySet()) {
            String string3 = this.values.get(string2);
            string = string + (n > 0 ? "|" + string2 + "=" + string3 : string2 + "=" + string3);
            ++n;
        }
        return string;
    }
}

