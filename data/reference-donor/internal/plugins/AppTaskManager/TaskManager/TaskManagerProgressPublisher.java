/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher
 *  com.strategyquant.tradinglib.project.websocket.WebSocketPublisher
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.App.impl.TaskManager;

import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

public class TaskManagerProgressPublisher
extends SynchronizedWebSocketPublisher {
    private JSONArray projectsStats = new JSONArray();
    private DataToSend data = new DataToSend("customProjectStats", this.projectsStats);
    private String lastData;

    public TaskManagerProgressPublisher() {
        SQWebSocketManager.getInstance().addAppPublisher("TASKMANAGER", (WebSocketPublisher)this);
    }

    public DataToSend getData() {
        List projects = ProjectEngine.list();
        for (int i = this.projectsStats.length() - 1; i >= 0; --i) {
            this.projectsStats.remove(i);
        }
        for (SQProject project : projects) {
            if (project.isAppProject()) continue;
            JSONObject projectStatus = project.getInfo();
            projectStatus.put("activeTask", (Object)project.getActiveTaskName());
            projectStatus.put("runningStatus", project.getRunningStatus());
            JSONArray tasksIterations = new JSONArray();
            projectStatus.put("tasksIterations", (Object)tasksIterations);
            try {
                for (int t = 0; t < project.getTasksHashes().size(); ++t) {
                    try {
                        ISQTask task = project.getTaskByHash(project.getTasksHashes().getInt(t));
                        tasksIterations.put((Object)new JSONObject().put("taskName", (Object)task.getCustomName()).put("iterations", task.getNumberOfRuns()));
                        continue;
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            this.projectsStats.put((Object)projectStatus);
        }
        if (this.lastData == null || !this.projectsStats.toString().equals(this.lastData)) {
            this.lastData = this.projectsStats.toString();
            return this.data;
        }
        return null;
    }

    public void resetLastData() {
        this.lastData = null;
    }
}

