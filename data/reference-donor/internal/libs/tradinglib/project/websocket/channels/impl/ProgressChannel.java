/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.websocket.channels.impl;

import com.strategyquant.tradinglib.project.ProjectProgressInfo;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.channels.IProjectChannel;
import org.json.JSONObject;

public class ProgressChannel
implements IProjectChannel {
    @Override
    public Object getData(SQProject sQProject) {
        JSONObject jSONObject = null;
        ProjectProgressInfo projectProgressInfo = sQProject.getProgress().get();
        if (projectProgressInfo != null) {
            jSONObject = new JSONObject();
            jSONObject.put("action", (Object)projectProgressInfo.action);
            jSONObject.put("percent", projectProgressInfo.percent);
            jSONObject.put("info", (Object)projectProgressInfo.info);
            if (projectProgressInfo.hasExtra) {
                jSONObject.put(projectProgressInfo.extraName, (Object)projectProgressInfo.extraValue);
            }
            if (projectProgressInfo.error != null) {
                jSONObject.put("error", (Object)projectProgressInfo.error);
            }
        }
        return jSONObject;
    }

    @Override
    public String getChannelName() {
        return "progress-channel";
    }
}

