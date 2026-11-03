/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.model.IdName
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.model.IdName;
import com.strategyquant.tradinglib.transfomer.AbstractDtoToJsonTransformer;
import org.json.JSONObject;

public class MarketDtoToJsonTransformer
extends AbstractDtoToJsonTransformer<IdName> {
    protected JSONObject objectToJson(IdName idName) {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("id", (Object)idName.getId());
        jSONObject.put("name", (Object)idName.getName());
        return jSONObject;
    }
}

