/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.websocket.channels.impl;

import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.channels.IProjectChannel;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

public class DatabankChannel
implements IProjectChannel {
    @Override
    public Object getData(SQProject sQProject) {
        ArrayList<Databank> arrayList = sQProject.getDatabanks().list();
        JSONArray jSONArray = null;
        for (int i = 0; i < arrayList.size(); ++i) {
            Databank databank = arrayList.get(i);
            JSONArray jSONArray2 = databank.getChanges();
            if (jSONArray2 == null) continue;
            if (jSONArray == null) {
                jSONArray = new JSONArray();
            }
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("name", (Object)databank.getName());
            jSONObject.put("records", databank.size());
            jSONObject.put("changes", (Object)jSONArray2);
            jSONArray.put((Object)jSONObject);
        }
        return jSONArray;
    }

    @Override
    public String getChannelName() {
        return "databanks-channel";
    }
}

