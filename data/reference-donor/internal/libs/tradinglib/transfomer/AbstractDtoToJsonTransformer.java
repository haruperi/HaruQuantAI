/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 */
package com.strategyquant.tradinglib.transfomer;

import java.util.List;
import org.json.JSONArray;

public abstract class AbstractDtoToJsonTransformer<T> {
    public JSONArray toJson(List<T> list) {
        JSONArray jSONArray = new JSONArray();
        for (T t : list) {
            jSONArray.put(this.objectToJson(t));
        }
        return jSONArray;
    }

    protected abstract Object objectToJson(T var1);
}

