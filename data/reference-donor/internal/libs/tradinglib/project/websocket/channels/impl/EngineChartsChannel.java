/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket.channels.impl;

import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.channels.IProjectChannel;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EngineChartsChannel
implements IProjectChannel {
    private static final Logger Log = LoggerFactory.getLogger(EngineChartsChannel.class);
    private String lastData = "";

    @Override
    public Object getData(SQProject sQProject) {
        JSONObject jSONObject = sQProject.engineCharts.print();
        String string = jSONObject.toString();
        if (string.hashCode() == this.lastData.hashCode()) {
            return null;
        }
        this.lastData = string;
        return jSONObject;
    }

    @Override
    public String getChannelName() {
        return "engine-charts-channel";
    }
}

