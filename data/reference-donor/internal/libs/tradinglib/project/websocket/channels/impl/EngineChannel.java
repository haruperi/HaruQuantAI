/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.JsonCreator
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  it.unimi.dsi.fastutil.ints.IntSet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket.channels.impl;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod;
import com.strategyquant.tradinglib.project.ComplexDurationStats;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.channels.IProjectChannel;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import it.unimi.dsi.fastutil.ints.IntSet;
import java.util.ArrayList;
import java.util.HashMap;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EngineChannel
implements IProjectChannel {
    private static final Logger Log = LoggerFactory.getLogger(EngineChannel.class);
    private ProjectRunInfo projectRunInfo = new ProjectRunInfo();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public Object getData(SQProject sQProject) {
        JSONObject jSONObject = sQProject.getInfo();
        ProjectRunInfo projectRunInfo = sQProject.getTrackingInfo();
        try {
            jSONObject.put("backtestsPerformed", projectRunInfo.backtestsPerformed);
            String string = SQUtils.d2((double)(100.0 * projectRunInfo.strategiesAcceptedPct));
            String string2 = SQUtils.d2((double)(100.0 * projectRunInfo.strategiesRejectedPct));
            if (projectRunInfo.strategiesAccepted > 0L && string.equals("0.00")) {
                string = "0.01";
                string2 = "99.99";
            }
            jSONObject.put("strategiesRejected", projectRunInfo.strategiesRejected);
            jSONObject.put("strategiesRejectedPct", (Object)string2);
            jSONObject.put("strategiesAccepted", projectRunInfo.strategiesAccepted);
            jSONObject.put("strategiesAcceptedPct", (Object)string);
            jSONObject.put("strategiesPassed", projectRunInfo.strategiesPassed);
            jSONObject.put("strategiesFailed", projectRunInfo.strategiesFailed);
            jSONObject.put("jobExceptionsCount", projectRunInfo.jobExceptionsCount);
            jSONObject.put("strategiesPerHour", (Object)this.formatIntOrDouble(projectRunInfo.strategiesPerHour));
            jSONObject.put("acceptedStrategiesPerHour", (Object)this.formatIntOrDouble(projectRunInfo.acceptedStrategiesPerHour));
            jSONObject.put("step", projectRunInfo.step);
            jSONObject.put("totalJobsDone", projectRunInfo.totalJobsDone);
            jSONObject.put("totalSteps", projectRunInfo.totalSteps);
            jSONObject.put("timePerStrategy", (Object)SQUtils.formatDuration((long)projectRunInfo.timePerStrategy));
            jSONObject.put("timePerAcceptedStrategy", (Object)SQUtils.formatDuration((long)projectRunInfo.timePerAcceptedStrategy));
            jSONObject.put("totalRunningTime", (Object)SQUtils.formatDuration((long)projectRunInfo.totalProjectRunningTime));
            jSONObject.put("taskRunningTime", (Object)SQUtils.formatDuration((long)projectRunInfo.taskRunningTime));
            jSONObject.put("timeToFinish", (Object)SQUtils.formatDuration((long)projectRunInfo.timeToFinish));
            jSONObject.put("infiniteProgress", projectRunInfo.infiniteProgress);
            jSONObject.put("progressPercent", (int)projectRunInfo.progressPercent);
            jSONObject.put("error", (Object)projectRunInfo.error);
            jSONObject.put("errorType", projectRunInfo.errorType);
            jSONObject.put("errorInfo", (Object)projectRunInfo.errorInfo);
            try {
                jSONObject.put("acceptedStats", (Object)this.acceptedStats(sQProject));
            }
            catch (Exception exception) {
                Log.error("Failed to get acceptedStats. Exc.", (Throwable)exception);
            }
            try {
                jSONObject.put("dismissalStats", (Object)this.dismissalStats(sQProject));
            }
            catch (Exception exception) {
                Log.error("Failed to get dismissalStats. Exc.", (Throwable)exception);
            }
            try {
                jSONObject.put("durationStats", (Object)this.durationStats(sQProject));
            }
            catch (Exception exception) {
                Log.error("Failed to get durationStats. Exc.", (Throwable)exception);
            }
            jSONObject.put("runningStatus", sQProject.getRunningStatus());
            jSONObject.put("lastEvent", (Object)sQProject.getLastEvent());
            JSONObject jSONObject2 = jSONObject;
            return jSONObject2;
        }
        finally {
            projectRunInfo.error = null;
        }
    }

    private String formatIntOrDouble(double d) {
        if (d > 1000.0) {
            return String.format("%.0f", d);
        }
        return String.format("%.2f", d);
    }

    private String durationStats(SQProject sQProject) {
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginArray();
        HashMap<String, ComplexDurationStats> hashMap = this.projectRunInfo.getDurationStats();
        int n = 0;
        double d = 0.0;
        for (String string : hashMap.keySet()) {
            d += hashMap.get((Object)string).totalTime;
        }
        for (String string : hashMap.keySet()) {
            if (n != 0) {
                jsonCreator.separator();
            }
            ComplexDurationStats complexDurationStats = hashMap.get(string);
            jsonCreator.beginArray();
            jsonCreator.setValue((Object)string, true);
            jsonCreator.setValue((Object)complexDurationStats.count, true);
            jsonCreator.setValue((Object)(SQUtils.d2String((double)complexDurationStats.avgTime, (int)4) + " s."), true);
            jsonCreator.setValue((Object)(SQUtils.d2String((double)complexDurationStats.totalTime, (int)4) + " s."), true);
            double d2 = SQUtils.round2((double)(100.0 * (complexDurationStats.totalTime / d)));
            jsonCreator.setValue((Object)(SQUtils.d2((double)d2) + " %"), false);
            jsonCreator.endArray(false);
            ++n;
        }
        jsonCreator.endArray(false);
        return jsonCreator.toJson();
    }

    private String acceptedStats(SQProject sQProject) {
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginArray();
        sQProject.loadTrackingInfo(this.projectRunInfo, true);
        Int2IntOpenHashMap int2IntOpenHashMap = this.projectRunInfo.getAcceptedCounts();
        int n = 0;
        IntSet intSet = int2IntOpenHashMap.keySet();
        IntIterator intIterator = intSet.iterator();
        while (intIterator.hasNext()) {
            int n2 = (Integer)intIterator.next();
            String string = n2 == 0 ? "In databank" : (n2 == 10007 ? BadStrategyException.TxtLongReplacedWithBetterStrategy : (n2 == 10006 ? BadStrategyException.TxtLongReasonStrategyTooSimilar : BadStrategyException.ExplanationUnknown + ", code: " + n2));
            int n3 = int2IntOpenHashMap.get(n2);
            double d = SQUtils.round2((double)(100.0 * ((double)n3 / (double)this.projectRunInfo.strategiesAccepted)));
            if (n != 0) {
                jsonCreator.separator();
            }
            jsonCreator.beginArray();
            jsonCreator.setValue((Object)string, true);
            jsonCreator.setValue((Object)n3, true);
            jsonCreator.setValue((Object)(d + " %"), false);
            jsonCreator.endArray(false);
            ++n;
        }
        jsonCreator.endArray(false);
        return jsonCreator.toJson();
    }

    private String dismissalStats(SQProject sQProject) {
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginArray();
        sQProject.loadTrackingInfo(this.projectRunInfo, true);
        Int2IntOpenHashMap int2IntOpenHashMap = this.projectRunInfo.getDismissalCounts();
        Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap = this.projectRunInfo.getDismissalReasons();
        int n = 0;
        IntSet intSet = int2IntOpenHashMap.keySet();
        IntIterator intIterator = intSet.iterator();
        while (intIterator.hasNext()) {
            String string;
            int n2 = (Integer)intIterator.next();
            if (int2ObjectOpenHashMap.containsKey(n2)) {
                string = (String)int2ObjectOpenHashMap.get(n2);
            } else {
                block20: {
                    int n3;
                    if (n2 < 100000) {
                        string = BadStrategyException.getReasonAsString(n2);
                    } else if (n2 >= 100000 && n2 < 200000) {
                        try {
                            ISQTask iSQTask = sQProject.getLastRunningTask();
                            TaskSettingsData taskSettingsData = iSQTask.getSettingsData();
                            n3 = n2 - 100000;
                            string = L.t((String)"Initial population filter", (Object[])new Object[0]) + ": ";
                            ArrayList arrayList = (ArrayList)taskSettingsData.getParams().get("InitialGenerationConditions");
                            Condition condition = (Condition)arrayList.get(n3);
                            string = string + condition.toString();
                        }
                        catch (Exception exception) {
                            Log.debug("Cannot print initial condition, code: " + n2 + ". Exc.", (Throwable)exception);
                            string = L.t((String)"initial condition, code: %s", (Object[])new Object[]{n2});
                        }
                    } else if (n2 >= 200000 && n2 < 300000) {
                        try {
                            ISQTask iSQTask = sQProject.getLastRunningTask();
                            TaskSettingsData taskSettingsData = iSQTask.getSettingsData();
                            n3 = n2 - 200000;
                            string = L.t((String)"Global filter", (Object[])new Object[0]) + ":  ";
                            ArrayList arrayList = (ArrayList)taskSettingsData.getParams().get("Conditions");
                            Condition condition = (Condition)arrayList.get(n3);
                            string = string + condition.toString();
                        }
                        catch (Exception exception) {
                            Log.debug("Cannot print global condition, code: " + n2 + ". Exc.", (Throwable)exception);
                            string = L.t((String)"global condition, code: %s", (Object[])new Object[]{n2});
                        }
                    } else if (n2 >= 300000) {
                        try {
                            ISQTask iSQTask = sQProject.getLastRunningTask();
                            TaskSettingsData taskSettingsData = iSQTask.getSettingsData();
                            n3 = n2 - 300000;
                            int n4 = n3 / 1000;
                            int n5 = n3 - n4 * 1000;
                            ArrayList arrayList = (ArrayList)taskSettingsData.getParams().get("CrossChecks");
                            ICrossCheck iCrossCheck = (ICrossCheck)arrayList.get(n4);
                            string = L.t((String)"Cross Check filter in '%s'", (Object[])new Object[]{iCrossCheck.getName()}) + ":  ";
                            if (WalkForwardCrossCheckMethod.class.isAssignableFrom(iCrossCheck.getClass()) && !iCrossCheck.getSettingName().equals("OptProfileSysParamPermutation")) {
                                string = string + L.t((String)"Robustness score didn't pass.", (Object[])new Object[0]);
                                break block20;
                            }
                            ArrayList arrayList2 = (ArrayList)iCrossCheck.getSettings().get("Conditions");
                            Condition condition = (Condition)arrayList2.get(n5);
                            string = string + condition.toString();
                        }
                        catch (Exception exception) {
                            Log.debug("Cannot print cross check condition, code: " + n2 + ". Exc.", (Throwable)exception);
                            string = L.t((String)"cross check condition, code: %s", (Object[])new Object[]{n2});
                        }
                    } else {
                        string = BadStrategyException.ExplanationUnknown + ", code: " + n2;
                    }
                }
                if (!string.contains("code:")) {
                    sQProject.setTrackingInfoReasonToDismiss(n2, string);
                }
            }
            int n6 = int2IntOpenHashMap.get(n2);
            double d = SQUtils.round2((double)(100.0 * ((double)n6 / (double)this.projectRunInfo.strategiesRejected)));
            if (n != 0) {
                jsonCreator.separator();
            }
            jsonCreator.beginArray();
            jsonCreator.setValue((Object)string, true);
            jsonCreator.setValue((Object)n6, true);
            jsonCreator.setValue((Object)(d + " %"), false);
            jsonCreator.endArray(false);
            ++n;
        }
        jsonCreator.endArray(false);
        return jsonCreator.toJson();
    }

    @Override
    public String getChannelName() {
        return "engine-channel";
    }
}

