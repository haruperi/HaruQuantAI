/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  it.unimi.dsi.fastutil.ints.IntSet
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod;
import com.strategyquant.tradinglib.project.ComplexDurationStats;
import com.strategyquant.tradinglib.project.TaskStat;
import com.strategyquant.tradinglib.project.TaskStats;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import it.unimi.dsi.fastutil.ints.IntSet;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectGlobalLog {
    private static final Logger Log = LoggerFactory.getLogger(ProjectGlobalLog.class);
    private PrintWriter out = null;
    private File file;
    private Int2ObjectOpenHashMap<TaskStats> stats = new Int2ObjectOpenHashMap();

    public ProjectGlobalLog(String string) throws Exception {
        this.createLogFile(string);
    }

    private void createLogFile(String string) throws Exception {
        String string2 = string + "log/global_log_" + SQTime.toString((long)System.currentTimeMillis(), (DateTimeFormatter)DateTimeFormat.forPattern((String)"yyyyMMdd")) + "_" + SQTime.toString((long)System.currentTimeMillis(), (DateTimeFormatter)DateTimeFormat.forPattern((String)"HHmmss")) + ".log";
        this.file = new File(string2);
        this.file.getParentFile().mkdirs();
        Log.info("Creating project log at '{}'", (Object)string2);
        this.out = new PrintWriter(new FileWriter(this.file, StandardCharsets.UTF_8, false));
        this.print(L.t((String)"Project", (Object[])new Object[0]) + ": " + this.file.getParentFile().getParentFile().getName());
        this.print(L.t((String)"Log file", (Object[])new Object[0]) + ": /" + this.file.getName());
    }

    public void print(String string, boolean bl) {
        if (string == null) {
            return;
        }
        if (this.out == null) {
            return;
        }
        this.out.write(string);
        if (bl) {
            this.out.write("\n");
        }
    }

    public void print(String string) {
        if (this.out == null) {
            return;
        }
        if (string == null) {
            return;
        }
        this.out.write(string + "\n");
    }

    public void printSeparator() {
        this.print("--------------------------------------------------------------------------------------------------------------------------");
    }

    public void printDoubleSeparator() {
        this.print("================================================================================");
    }

    public void printEmptyLine() {
        this.print("");
    }

    public String load() throws Exception {
        if (this.out != null) {
            this.out.flush();
        }
        return SQUtils.fileToString((File)this.file);
    }

    public void close() {
        if (this.out == null) {
            return;
        }
        this.out.flush();
        this.out.close();
        this.out = null;
    }

    public void addDurationStats(ProjectRunInfo projectRunInfo) {
        this.printEmptyLine();
        this.print(L.t((String)"Time per strategy details", (Object[])new Object[0]) + ":");
        HashMap<String, ComplexDurationStats> hashMap = projectRunInfo.getDurationStats();
        double d = 0.0;
        for (String string : hashMap.keySet()) {
            d += hashMap.get((Object)string).totalTime;
        }
        for (String string : hashMap.keySet()) {
            ComplexDurationStats complexDurationStats = hashMap.get(string);
            this.print(string + ": Count: " + complexDurationStats.count + ", Avg. time: " + SQUtils.d2String((double)complexDurationStats.avgTime, (int)4) + " s., Total time: " + SQUtils.d2String((double)complexDurationStats.totalTime, (int)4) + " s., % of all: " + SQUtils.d2((double)SQUtils.round2((double)(100.0 * (complexDurationStats.totalTime / d)))) + " %");
        }
    }

    public void addAcceptedStats(ProjectRunInfo projectRunInfo, ISQTask iSQTask) {
        this.printEmptyLine();
        if (iSQTask.getType().equals("Build")) {
            this.print(L.t((String)"Accepted details", (Object[])new Object[0]) + ":");
        } else {
            this.print(L.t((String)"Passed details", (Object[])new Object[0]) + ":");
        }
        Int2IntOpenHashMap int2IntOpenHashMap = projectRunInfo.getAcceptedCounts();
        IntSet intSet = int2IntOpenHashMap.keySet();
        IntIterator intIterator = intSet.iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            String string = n == 0 ? "In databank" : (n == 10007 ? BadStrategyException.TxtLongReplacedWithBetterStrategy : (n == 10006 ? BadStrategyException.TxtLongReasonStrategyTooSimilar : BadStrategyException.ExplanationUnknown + ", code: " + n));
            int n2 = int2IntOpenHashMap.get(n);
            double d = SQUtils.round2((double)(100.0 * ((double)n2 / (double)projectRunInfo.strategiesAccepted)));
            this.print(string + ", Count: " + n2 + ", % of all: " + d + " %");
        }
    }

    public void addDismissalStats(ProjectRunInfo projectRunInfo, ISQTask iSQTask) {
        this.printEmptyLine();
        if (iSQTask.getType().equals("Build")) {
            this.print(L.t((String)"Rejected details", (Object[])new Object[0]) + ":");
        } else {
            this.print(L.t((String)"Failed details", (Object[])new Object[0]) + ":");
        }
        Int2IntOpenHashMap int2IntOpenHashMap = projectRunInfo.getDismissalCounts();
        Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap = projectRunInfo.getDismissalReasons();
        IntSet intSet = int2IntOpenHashMap.keySet();
        IntIterator intIterator = intSet.iterator();
        while (intIterator.hasNext()) {
            String string;
            int n;
            block20: {
                n = (Integer)intIterator.next();
                if (int2ObjectOpenHashMap.containsKey(n)) {
                    string = (String)int2ObjectOpenHashMap.get(n);
                } else if (n < 100000) {
                    string = BadStrategyException.getReasonAsString(n);
                } else if (n >= 100000 && n < 200000) {
                    try {
                        TaskSettingsData taskSettingsData = iSQTask.getSettingsData();
                        int n2 = n - 100000;
                        string = L.t((String)"Initial population filter", (Object[])new Object[0]) + ": ";
                        ArrayList arrayList = (ArrayList)taskSettingsData.getParams().get("InitialGenerationConditions");
                        Condition condition = (Condition)arrayList.get(n2);
                        string = string + condition.toString();
                    }
                    catch (Exception exception) {
                        string = L.t((String)"initial condition, code: %s", (Object[])new Object[]{n});
                    }
                } else if (n >= 200000 && n < 300000) {
                    try {
                        TaskSettingsData taskSettingsData = iSQTask.getSettingsData();
                        int n3 = n - 200000;
                        string = L.t((String)"Global filter", (Object[])new Object[0]) + ":  ";
                        ArrayList arrayList = (ArrayList)taskSettingsData.getParams().get("Conditions");
                        Condition condition = (Condition)arrayList.get(n3);
                        string = string + condition.toString();
                    }
                    catch (Exception exception) {
                        string = L.t((String)"global condition, code: %s", (Object[])new Object[]{n});
                    }
                } else if (n >= 300000) {
                    try {
                        TaskSettingsData taskSettingsData = iSQTask.getSettingsData();
                        int n4 = n - 300000;
                        int n5 = n4 / 1000;
                        int n6 = n4 - n5 * 1000;
                        ArrayList arrayList = (ArrayList)taskSettingsData.getParams().get("CrossChecks");
                        ICrossCheck iCrossCheck = (ICrossCheck)arrayList.get(n5);
                        string = L.t((String)"Cross Check filter in '%s'", (Object[])new Object[]{iCrossCheck.getName()}) + ":  ";
                        if (WalkForwardCrossCheckMethod.class.isAssignableFrom(iCrossCheck.getClass()) && !iCrossCheck.getSettingName().equals("OptProfileSysParamPermutation")) {
                            string = string + L.t((String)"Robustness score didn't pass.", (Object[])new Object[0]);
                            break block20;
                        }
                        ArrayList arrayList2 = (ArrayList)iCrossCheck.getSettings().get("Conditions");
                        Condition condition = (Condition)arrayList2.get(n6);
                        string = string + condition.toString();
                    }
                    catch (Exception exception) {
                        string = L.t((String)"cross check condition, code: %s", (Object[])new Object[]{n});
                    }
                } else {
                    string = BadStrategyException.ExplanationUnknown + ", code: " + n;
                }
            }
            int n7 = int2IntOpenHashMap.get(n);
            double d = SQUtils.round2((double)(100.0 * ((double)n7 / (double)projectRunInfo.strategiesRejected)));
            this.print(string + ", Count: " + n7 + ", % of all: " + d + " %");
        }
    }

    public TaskStats getTaskStats(int n) {
        TaskStats taskStats = (TaskStats)this.stats.get(n);
        if (taskStats == null) {
            taskStats = new TaskStats();
            this.stats.put(n, (Object)taskStats);
        }
        return taskStats;
    }

    public void increaseStats(int n, String string, long l, String string2, long l2) {
        TaskStats taskStats = this.getTaskStats(n);
        taskStats.increaseStat(TaskStat.BAR, string, l, 1);
        taskStats.increaseStat(TaskStat.BAR, string2, l2, 2, string);
    }

    public void increaseStats(String string, int n, String string2, long l, int n2) {
        TaskStats taskStats = this.getTaskStats(n);
        taskStats.increaseStat(string, string2, l, n2);
    }

    public void setStats(String string, int n, String string2, long l, int n2, String string3) {
        TaskStats taskStats = this.getTaskStats(n);
        taskStats.setStat(string, string2, l, n2, string3);
    }
}

