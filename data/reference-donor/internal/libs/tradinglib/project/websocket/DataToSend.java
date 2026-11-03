/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.websocket;

import org.json.JSONArray;
import org.json.JSONObject;

public class DataToSend {
    private String name;
    private JSONObject dataObject;
    private JSONArray dataArray;

    public DataToSend() {
    }

    public DataToSend(String string) {
        this.name = string;
    }

    public DataToSend(String string, JSONObject jSONObject) {
        this.name = string;
        this.dataObject = jSONObject;
    }

    public DataToSend(String string, JSONArray jSONArray) {
        this.name = string;
        this.dataArray = jSONArray;
    }

    public JSONObject getDataObject() {
        return this.dataObject;
    }

    public void setDataObject(JSONObject jSONObject) {
        this.dataObject = jSONObject;
    }

    public JSONArray getDataArray() {
        return this.dataArray;
    }

    public void setDataObject(JSONArray jSONArray) {
        this.dataArray = jSONArray;
    }

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }
}

