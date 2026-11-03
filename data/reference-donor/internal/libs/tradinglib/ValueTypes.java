/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import org.json.JSONObject;

public class ValueTypes {
    public static final byte Maximize = 1;
    public static final byte Minimize = 2;
    public static final byte Aproximate = 3;

    public static String typeToString(byte by) {
        switch (by) {
            case 1: {
                return L.t((String)"Maximize", (Object[])new Object[0]);
            }
            case 2: {
                return L.t((String)"Minimize", (Object[])new Object[0]);
            }
            case 3: {
                return L.t((String)"Aproximate", (Object[])new Object[0]);
            }
        }
        return "?";
    }

    public static JSONObject getTypes() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("1", (Object)ValueTypes.typeToString((byte)1));
        jSONObject.put("2", (Object)ValueTypes.typeToString((byte)2));
        jSONObject.put("3", (Object)ValueTypes.typeToString((byte)3));
        return jSONObject;
    }
}

