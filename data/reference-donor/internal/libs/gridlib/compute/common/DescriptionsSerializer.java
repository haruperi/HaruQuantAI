/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.common;

import com.strategyquant.gridlib.compute.common.JobQueue;
import com.strategyquant.gridlib.compute.common.RingBuffer;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

public class DescriptionsSerializer<T> {
    private StringBuilder sb;

    public String getJson(Map<Integer, LinkedHashSet<Integer>> map, Collection<Integer> collection, Map<Integer, JobQueue.JobInfo<?>> map2, RingBuffer<JobQueue.JobInfo<?>> ringBuffer) {
        this.sb = new StringBuilder();
        this.beginObject();
        this.addJobs("running", SerializedPart.RUNNING, this.getRunning(collection, map2), map2);
        this.addSeparator();
        this.addJobs("waiting", SerializedPart.WAITING, this.getWaiting(collection, map, map2), map2);
        if (ringBuffer != null) {
            this.addSeparator();
            this.addFinishedJobs("finished", ringBuffer);
        }
        this.endObject();
        return this.sb.toString();
    }

    private List<Integer> getRunning(Collection<Integer> collection, Map<Integer, JobQueue.JobInfo<?>> map) {
        LinkedList<Integer> linkedList = new LinkedList<Integer>();
        for (Integer n : collection) {
            JobQueue.JobInfo<?> jobInfo = map.get(n);
            if (jobInfo == null || jobInfo.waiting) continue;
            linkedList.add(n);
        }
        return linkedList;
    }

    private List<Integer> getWaiting(Collection<Integer> collection, Map<Integer, LinkedHashSet<Integer>> map, Map<Integer, JobQueue.JobInfo<?>> map2) {
        LinkedList<Integer> linkedList = new LinkedList<Integer>();
        for (Serializable serializable : collection) {
            JobQueue.JobInfo<?> jobInfo = map2.get(serializable);
            if (jobInfo == null || !jobInfo.waiting) continue;
            linkedList.add((Integer)serializable);
        }
        for (int i = 9; i >= 0; --i) {
            Serializable serializable;
            serializable = map.get(i);
            if (serializable == null) continue;
            linkedList.addAll((Collection<Integer>)((Object)serializable));
        }
        return linkedList;
    }

    private void addFinishedJobs(String string, RingBuffer<JobQueue.JobInfo<?>> ringBuffer) {
        this.addAttrOnly(string);
        ArrayList arrayList = new ArrayList(ringBuffer.getSize());
        for (JobQueue.JobInfo<?> object : ringBuffer) {
            arrayList.add(object);
        }
        Collections.sort(arrayList, new Comparator<JobQueue.JobInfo>(){

            @Override
            public int compare(JobQueue.JobInfo jobInfo, JobQueue.JobInfo jobInfo2) {
                long l;
                long l2 = jobInfo.getFinishTime();
                if (l2 == (l = jobInfo2.getFinishTime())) {
                    return 0;
                }
                if (l2 > l) {
                    return -1;
                }
                return 1;
            }
        });
        this.beginArray();
        boolean bl = true;
        for (JobQueue.JobInfo jobInfo : arrayList) {
            if (!bl) {
                this.addSeparator();
            }
            this.beginObject();
            this.addCommonsJobsInfo(jobInfo);
            this.addSeparator();
            this.addAttribute("duration", jobInfo.getDuration());
            this.addSeparator();
            this.addAttribute("durationWithWait", jobInfo.getDurationWithWait());
            this.addSeparator();
            this.addAttribute("startTime", jobInfo.getExecuteTime());
            this.addSeparator();
            this.addAttribute("finishTime", jobInfo.getExecuteTime());
            this.addSeparator();
            this.addAttribute("success", jobInfo.isSuccess());
            if (!jobInfo.isSuccess()) {
                this.addSeparator();
                this.addAttribute("message", jobInfo.getMessage());
            }
            this.endObject();
            bl = false;
        }
        this.endArray();
    }

    private void addCommonsJobsInfo(JobQueue.JobInfo<?> jobInfo) {
        this.addAttribute("jobId", jobInfo.getId());
        this.addSeparator();
        this.addAttribute("jobGroupId", jobInfo.getJobGroupId());
        this.addSeparator();
        this.addAttribute("createTime", jobInfo.getCreationTime());
    }

    private void addJobs(String string, SerializedPart serializedPart, Collection<Integer> collection, Map<Integer, JobQueue.JobInfo<?>> map) {
        this.addAttrOnly(string);
        this.beginArray();
        boolean bl = true;
        for (Integer n : collection) {
            JobQueue.JobInfo<?> jobInfo = map.get(n);
            if (jobInfo == null) continue;
            if (!bl) {
                this.addSeparator();
            }
            this.beginObject();
            this.addCommonsJobsInfo(jobInfo);
            if (serializedPart == SerializedPart.RUNNING) {
                long l = System.currentTimeMillis();
                this.addSeparator();
                this.addAttribute("progress", jobInfo.getProgress());
                this.addSeparator();
                this.addAttribute("duration", l - jobInfo.getExecuteTime());
                this.addSeparator();
                this.addAttribute("durationWithWait", l - jobInfo.getCreationTime());
                this.addSeparator();
                this.addAttribute("startTime", jobInfo.getExecuteTime());
                this.addSeparator();
                this.addAttribute("waiting", jobInfo.isWaiting());
            }
            this.endObject();
            bl = false;
        }
        this.endArray();
    }

    private void beginArray() {
        this.sb.append("[");
    }

    private void endArray() {
        this.sb.append("]");
    }

    private void beginObject() {
        this.sb.append("{");
    }

    private void endObject() {
        this.sb.append("}");
    }

    private void addSeparator() {
        this.sb.append(",");
    }

    private void addAttrOnly(String string) {
        this.sb.append("\"" + string + "\":");
    }

    private void addAttribute(String string, String string2) {
        string2 = string2.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t");
        this.addAttrOnly(string);
        this.sb.append("\"" + string2 + "\"");
    }

    private void addAttribute(String string, boolean bl) {
        this.addAttrOnly(string);
        this.sb.append(bl);
    }

    private void addAttribute(String string, long l) {
        this.addAttrOnly(string);
        this.sb.append(l);
    }

    private void addAttribute(String string, int n) {
        this.addAttrOnly(string);
        this.sb.append(n);
    }

    private static enum SerializedPart {
        FINISHED,
        WAITING,
        RUNNING;

    }
}

