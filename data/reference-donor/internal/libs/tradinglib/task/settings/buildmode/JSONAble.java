/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.task.settings.buildmode;

import java.lang.reflect.Field;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class JSONAble {
    private static final Logger Log = LoggerFactory.getLogger(JSONAble.class);

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        for (Field field : this.getClass().getDeclaredFields()) {
            try {
                jSONObject.put(this.getCamelName(field.getName()), field.get(this));
            }
            catch (Exception exception) {
                Log.error("Cannot get value of field '" + field.getName() + "' of class '" + this.getClass().getName() + "'");
            }
        }
        return jSONObject;
    }

    private String getCamelName(String string) {
        String[] stringArray = string.split("_");
        String string2 = "";
        for (int i = 0; i < stringArray.length; ++i) {
            String string3 = stringArray[i];
            if (i == 0) {
                string2 = string2 + string3.toLowerCase();
                continue;
            }
            string2 = string2 + string3.toUpperCase().substring(0, 1);
            string2 = string2 + string3.toLowerCase().substring(1);
        }
        return string2;
    }
}

