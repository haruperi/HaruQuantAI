/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.ProjectFeeds;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.channels.IProjectChannel;
import com.strategyquant.tradinglib.project.websocket.channels.ProjectChannels;
import java.util.ArrayList;
import java.util.HashMap;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectDataPublisher
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(ProjectDataPublisher.class);
    public static final String PROJECT_DATA = "projectData";
    public static final String CHANNELS_DATA = "channels";
    public static final int ERROR_TYPE_GENERAL = 10;
    public static final int ERROR_TYPE_FATAL = 50;
    private SQProject project;
    private DataToSend data = new DataToSend("projectData");
    private JSONObject dataObj = new JSONObject();
    private HashMap<String, Object> lastChannelData = new HashMap();

    public ProjectDataPublisher(SQProject sQProject) {
        this.project = sQProject;
        this.data.setDataObject(this.dataObj);
    }

    @Override
    public DataToSend getData() {
        try {
            if (this.hasNewData()) {
                return this.data;
            }
        }
        catch (Exception exception) {
            Log.error("Project data publisher error: ", (Throwable)exception);
            this.project.printToLog("Project data publisher error - " + exception.getMessage());
        }
        return null;
    }

    @Override
    public void resetLastData() {
        this.lastChannelData.clear();
    }

    public void resetLastData(String string) {
        this.lastChannelData.remove(string);
    }

    private boolean hasNewData() {
        boolean bl = false;
        this.dataObj.put("name", (Object)this.project.getName());
        this.dataObj.remove(CHANNELS_DATA);
        JSONArray jSONArray = null;
        ArrayList<IProjectChannel> arrayList = ProjectChannels.getChannels();
        if (arrayList == null || arrayList.size() == 0) {
            return false;
        }
        boolean bl2 = false;
        for (IProjectChannel iProjectChannel : arrayList) {
            String string = iProjectChannel.getChannelName();
            if (!ProjectFeeds.isSubscribed(this.project.getName(), string)) continue;
            try {
                Object object = iProjectChannel.getData(this.project);
                if (object == null || !this.dataChanged(string, object)) continue;
                JSONObject jSONObject = new JSONObject();
                jSONObject.put("name", (Object)string);
                jSONObject.put("data", object);
                if (jSONArray == null) {
                    jSONArray = new JSONArray();
                }
                jSONArray.put((Object)jSONObject);
                bl = true;
                this.lastChannelData.put(string, object);
            }
            catch (Exception exception) {
                Log.error(String.format("Error while getting data from '%s-%s'. Exc.", this.project.getName(), string), (Throwable)exception);
            }
        }
        if (bl) {
            this.dataObj.put(CHANNELS_DATA, jSONArray);
        }
        return bl;
    }

    private boolean dataChanged(String string, Object object) {
        Object object2 = this.lastChannelData.get(string);
        if (object2 == null) {
            return true;
        }
        if (object instanceof JSONObject && object2 instanceof JSONObject) {
            return !((JSONObject)object).similar((Object)((JSONObject)object2));
        }
        if (object instanceof JSONArray && object2 instanceof JSONArray) {
            return !((JSONArray)object).similar((Object)((JSONArray)object2));
        }
        if (object instanceof String && object2 instanceof String) {
            return !object.equals(object2);
        }
        return true;
    }
}

