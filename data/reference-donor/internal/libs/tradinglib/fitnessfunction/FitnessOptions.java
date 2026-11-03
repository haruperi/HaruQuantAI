/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.fitnessfunction;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ValueTypes;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

public class FitnessOptions {
    public static String list() {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Net Profit (Return)")).put("key", (Object)"NetProfit"));
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Return / Drawdown ratio")).put("key", (Object)"ReturnDDRatio"));
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"R Expectancy (Van Tharp)")).put("key", (Object)"RExpectancy"));
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Annual Return % / Max DD %")).put("key", (Object)"AnnualPctReturnDDRatio"));
        JSONArray jSONArray2 = new JSONArray();
        List list = DatabankColumns.get().getAvailableClasses();
        for (int i = 0; i < list.size(); ++i) {
            DatabankColumn databankColumn = (DatabankColumn)list.get(i);
            if (databankColumn.getType().equals("Text") || databankColumn.getClassName().equals("Fitness")) continue;
            JSONArray jSONArray3 = new JSONArray();
            jSONArray3.put((Object)databankColumn.getName());
            jSONArray3.put((Object)("{{selectWidget options='" + ValueTypes.getTypes().toString() + "' value='" + databankColumn.getValueType() + "'}}"));
            jSONArray3.put((Object)"{{spinnerWidget value='1' min='0'}}");
            jSONArray3.put((Object)("{{spinnerWidget value='" + databankColumn.getTarget() + "' min='0'}}"));
            JSONObject jSONObject2 = new JSONObject();
            jSONObject2.put("id", (Object)("r" + i));
            jSONObject2.put("data", (Object)jSONArray3);
            jSONObject2.put("userdata", (Object)new JSONObject().put("key", (Object)databankColumn.getClass().getSimpleName()).put("type", (int)databankColumn.getValueType()).put("target", databankColumn.getTarget()));
            jSONArray2.put((Object)jSONObject2);
        }
        jSONArray.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Weighted Fitness (multiple goals)")).put("key", (Object)"Weighted").put("rows", (Object)jSONArray2));
        jSONObject.put("types", (Object)jSONArray);
        jSONObject.put("success", (Object)L.t((String)"Listed.", (Object[])new Object[0]));
        return jSONObject.toString();
    }
}

