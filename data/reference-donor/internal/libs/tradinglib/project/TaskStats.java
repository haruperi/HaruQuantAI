/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.project.TaskStat;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;

public class TaskStats {
    private static int MAX_ORDERS = 999999;
    public HashMap<String, TaskStat> stats = new HashMap();

    private TaskStat getStat(String string) {
        return this.getStat(string, MAX_ORDERS);
    }

    private TaskStat getStat(String string, int n) {
        TaskStat taskStat = this.stats.get(string);
        if (taskStat == null) {
            taskStat = new TaskStat();
            taskStat.action = string;
            taskStat.count = 0L;
            taskStat.order = n;
            this.stats.put(string, taskStat);
        }
        return taskStat;
    }

    public void increaseStat(String string, String string2, long l) {
        this.increaseStat(string, string2, l, MAX_ORDERS);
    }

    public void increaseStat(String string, String string2, long l, int n) {
        this.increaseStat(string, string2, l, n, "");
    }

    public void increaseStat(String string, String string2, long l, int n, String string3) {
        TaskStat taskStat = this.getStat(string2, n);
        taskStat.action = string2;
        taskStat.count += l;
        taskStat.display = string;
        taskStat.percentageCompareAction = string3;
    }

    public void setStat(String string, String string2, long l, String string3) {
        this.setStat(string, string2, l, MAX_ORDERS, string3);
    }

    public void setStat(String string, String string2, long l, int n, String string3) {
        TaskStat taskStat = this.getStat(string2, n);
        taskStat.action = string2;
        taskStat.count = l;
        taskStat.display = string;
        taskStat.percentageCompareAction = string3;
    }

    public JSONArray getStatsJSONArray() {
        JSONArray jSONArray = new JSONArray();
        for (Map.Entry<String, TaskStat> entry : this.stats.entrySet()) {
            String string = entry.getKey();
            TaskStat taskStat = entry.getValue();
            jSONArray.put((Object)taskStat.getJSONObject());
        }
        return jSONArray;
    }
}

