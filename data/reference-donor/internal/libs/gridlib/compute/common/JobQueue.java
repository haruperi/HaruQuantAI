/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.compute.common;

import com.strategyquant.gridlib.compute.common.DescriptionsSerializer;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.gridlib.compute.common.PausedTasks;
import com.strategyquant.gridlib.compute.common.RingBuffer;
import com.strategyquant.gridlib.compute.common.TaskGroupMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.Serializable;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JobQueue<T extends Serializable>
implements AutoCloseable {
    private static final Logger LOGGER = LoggerFactory.getLogger(JobQueue.class);
    private static final int DEFAULT_MAX_LAST_JOB_KEPT = 150;
    private Map<Integer, JobInfo<T>> dataMap = new Int2ObjectOpenHashMap();
    private RingBuffer<JobInfo<T>> finishedDataMap;
    private Map<Integer, LinkedHashSet<Integer>> queueOfTaskForExecute = new HashMap<Integer, LinkedHashSet<Integer>>();
    private TaskGroupMap groupMap = new TaskGroupMap();
    private Set<Integer> pausedTasks = new HashSet<Integer>();
    private LinkedHashSet<Integer> notConfirmedRunningTasks = new LinkedHashSet();
    private Object lock = new Object();
    private DescriptionsSerializer serializer = new DescriptionsSerializer();

    private int getJobIdentHash(String string, String string2) {
        String string3 = string + "___" + string2;
        return string3.hashCode();
    }

    public void setFinishedJobsCount(int n) {
        this.finishedDataMap = new RingBuffer(Math.min(n, 150));
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public PausedTasks<T> pause(String string) {
        Object object = this.lock;
        synchronized (object) {
            LinkedList linkedList = new LinkedList();
            LinkedList linkedList2 = new LinkedList();
            Set<String> set = this.groupMap.getJobsForGroup(string);
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug("Pausing (waiting) group:{}. Jobs for pause:{}", (Object)string, (Object)set.size());
            }
            for (String string2 : set) {
                int n = this.getJobIdentHash(string2, string);
                if (!this.notConfirmedRunningTasks.contains(n)) {
                    if (LOGGER.isDebugEnabled()) {
                        LOGGER.debug("Pausing task: #{}({}).", (Object)string2, (Object)string);
                    }
                    this.pausedTasks.add(n);
                    JobInfo<T> jobInfo = this.dataMap.get(n);
                    if (jobInfo == null) continue;
                    this.removeFromQueue(n, ((JobInfo)jobInfo).priority);
                    linkedList.add(this.dataMap.get(n));
                    continue;
                }
                linkedList2.add(this.dataMap.get(n));
            }
            return new PausedTasks(linkedList, linkedList2);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<T> pause(String string, String string2) {
        Object object = this.lock;
        synchronized (object) {
            int n = this.getJobIdentHash(string2, string);
            JobInfo<T> jobInfo = this.dataMap.get(n);
            if (!this.notConfirmedRunningTasks.contains(n)) {
                if (LOGGER.isDebugEnabled()) {
                    LOGGER.debug("Pausing task: #{}({}).", (Object)string2, (Object)string);
                }
                this.pausedTasks.add(n);
                if (jobInfo != null) {
                    this.removeFromQueue(n, ((JobInfo)jobInfo).priority);
                }
                return null;
            }
            return jobInfo;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public List<JobInfo<T>> restore(String string) {
        Object object = this.lock;
        synchronized (object) {
            LinkedList<JobInfo<T>> linkedList = new LinkedList<JobInfo<T>>();
            Set<String> set = this.groupMap.getJobsForGroup(string);
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug("Restoring group:{}. Jobs for restore:{}", (Object)string, (Object)set.size());
            }
            for (String string2 : set) {
                int n = this.getJobIdentHash(string2, string);
                if (this.pausedTasks.remove(n)) {
                    JobInfo<T> jobInfo;
                    if (LOGGER.isDebugEnabled()) {
                        LOGGER.debug("Restoring task: #{}({}).", (Object)string2, (Object)string);
                    }
                    if ((jobInfo = this.dataMap.get(n)) == null) continue;
                    this.addToQueue(n, ((JobInfo)jobInfo).priority, false);
                    linkedList.add(this.dataMap.get(n));
                    continue;
                }
                if (!this.notConfirmedRunningTasks.contains(n)) continue;
                linkedList.add(this.dataMap.get(n));
            }
            return linkedList;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<T> restore(String string, String string2) {
        Object object = this.lock;
        synchronized (object) {
            int n = this.getJobIdentHash(string2, string);
            JobInfo<T> jobInfo = this.dataMap.get(n);
            if (this.pausedTasks.remove(n)) {
                if (LOGGER.isDebugEnabled()) {
                    LOGGER.debug("Restoring task: #{}({}).", (Object)string2, (Object)string);
                }
                if (jobInfo != null) {
                    this.addToQueue(n, ((JobInfo)jobInfo).priority, false);
                    return this.dataMap.get(n);
                }
            }
            return jobInfo;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Set<JobInfo<T>> stop(String string) {
        HashSet<JobInfo<T>> hashSet = new HashSet<JobInfo<T>>();
        Object object = this.lock;
        synchronized (object) {
            HashSet<String> hashSet2 = new HashSet<String>();
            hashSet2.addAll(this.groupMap.getJobsForGroup(string));
            for (String string2 : hashSet2) {
                int n = this.getJobIdentHash(string2, string);
                JobInfo<T> jobInfo = this.dataMap.get(n);
                if (jobInfo == null) continue;
                hashSet.add(jobInfo);
                if (!((JobInfo)jobInfo).executed) {
                    this.dataMap.remove(n);
                    this.removeFromQueue(n, ((JobInfo)jobInfo).priority);
                    this.groupMap.remove(string2, string);
                    ((JobInfo)jobInfo).success = true;
                    ((JobInfo)jobInfo).message = "stopped";
                    continue;
                }
                ((JobInfo)jobInfo).message = "stopping";
            }
            return hashSet;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<T> stop(String string, String string2) {
        Object object = this.lock;
        synchronized (object) {
            int n = this.getJobIdentHash(string2, string);
            JobInfo<T> jobInfo = this.dataMap.get(n);
            if (jobInfo != null) {
                if (!((JobInfo)jobInfo).executed) {
                    this.dataMap.remove(n);
                    this.removeFromQueue(n, ((JobInfo)jobInfo).priority);
                    ((JobInfo)jobInfo).success = true;
                    ((JobInfo)jobInfo).message = "stopped";
                } else {
                    ((JobInfo)jobInfo).message = "stopping";
                }
                return jobInfo;
            }
            return null;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean isEmpty() {
        Object object = this.lock;
        synchronized (object) {
            return this.queueOfTaskForExecute.isEmpty();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<T> tryToTakeNotFinishedTask(TimeEvaluator timeEvaluator) {
        Object object = this.lock;
        synchronized (object) {
            long l;
            if (this.notConfirmedRunningTasks.isEmpty()) {
                return null;
            }
            Integer n = (Integer)this.notConfirmedRunningTasks.iterator().next();
            JobInfo<T> jobInfo = this.dataMap.get(n);
            if (jobInfo == null) {
                this.notConfirmedRunningTasks.remove(n);
                return null;
            }
            long l2 = System.currentTimeMillis() - ((JobInfo)jobInfo).executeTime;
            if (l2 < (l = timeEvaluator.getTimeForWaitForTask(((JobInfo)jobInfo).jobGroupId))) {
                return null;
            }
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug("Resending task #{}.", (Object)n);
            }
            this.notConfirmedRunningTasks.remove(n);
            return jobInfo;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void add(String string, String string2, int n, boolean bl, T t, ExecuteOptions executeOptions) {
        int n2 = this.getJobIdentHash(string, string2);
        Object object = this.lock;
        synchronized (object) {
            if (this.dataMap.containsKey(n2)) {
                throw new IllegalArgumentException(String.format("Job: %s(%s) already in queue.", string, string2));
            }
            JobInfo jobInfo = new JobInfo();
            jobInfo.data = t;
            jobInfo.id = string;
            jobInfo.jobGroupId = string2;
            jobInfo.blocking = bl;
            jobInfo.priority = this.normalizePriority(n);
            jobInfo.setCreationTime(System.currentTimeMillis());
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug("Adding task to JobQueue: {}({})", (Object)string, (Object)string2);
            }
            this.dataMap.put(n2, jobInfo);
            this.groupMap.add(string, string2, executeOptions);
            this.addToQueue(n2, n, false);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void updateProgress(String string, String string2, int n) {
        Object object = this.lock;
        synchronized (object) {
            int n2 = this.getJobIdentHash(string, string2);
            JobInfo<T> jobInfo = this.dataMap.get(n2);
            if (jobInfo != null) {
                ((JobInfo)jobInfo).progress = n;
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void computing(String string, String string2) {
        int n = this.getJobIdentHash(string, string2);
        Object object = this.lock;
        synchronized (object) {
            JobInfo<T> jobInfo = this.dataMap.get(n);
            ((JobInfo)jobInfo).executed = true;
            ((JobInfo)jobInfo).executeTime = System.currentTimeMillis();
            this.notConfirmedRunningTasks.add(n);
            this.removeFromQueue(n, ((JobInfo)jobInfo).priority);
            this.groupMap.executed(string2);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public long computed(String string, String string2, boolean bl, String string3) {
        Object object = this.lock;
        synchronized (object) {
            int n = this.getJobIdentHash(string, string2);
            this.notConfirmedRunningTasks.remove(n);
            this.groupMap.remove(string, string2);
            JobInfo<T> jobInfo = this.dataMap.remove(n);
            if (jobInfo == null) {
                return 0L;
            }
            ((JobInfo)jobInfo).data = null;
            ((JobInfo)jobInfo).success = bl;
            ((JobInfo)jobInfo).message = string3;
            if (this.finishedDataMap != null) {
                this.finishedDataMap.add(jobInfo);
            }
            ((JobInfo)jobInfo).finishTime = System.currentTimeMillis();
            long l = ((JobInfo)jobInfo).finishTime - ((JobInfo)jobInfo).executeTime;
            ((JobInfo)jobInfo).duration = l;
            ((JobInfo)jobInfo).durationWithWait = ((JobInfo)jobInfo).finishTime - ((JobInfo)jobInfo).creationTime;
            return l;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<T> getNext(boolean bl, boolean bl2) {
        Object object = this.lock;
        synchronized (object) {
            JobInfo<T> jobInfo = null;
            if (bl) {
                jobInfo = this.getSuitableJob(false);
            }
            if (jobInfo == null) {
                Boolean bl3 = null;
                if (!bl2) {
                    bl3 = false;
                }
                jobInfo = this.getSuitableJob(bl3);
            }
            return jobInfo;
        }
    }

    private boolean canExecuteTaskDueGroupLimitation(JobInfo<T> jobInfo) {
        ExecuteOptions executeOptions = this.groupMap.getOptions(jobInfo.getJobGroupId());
        if (executeOptions == null || executeOptions.getMaxRunningCount() < 1) {
            return true;
        }
        int n = this.groupMap.getRunningCount(jobInfo.getJobGroupId());
        if (n < executeOptions.getMaxRunningCount()) {
            return true;
        }
        if (LOGGER.isDebugEnabled()) {
            LOGGER.debug("Can't run the job " + jobInfo.getId() + " - number of jobs in the the group " + jobInfo.getJobGroupId() + " is limited to:" + executeOptions.getMaxRunningCount());
        }
        return false;
    }

    private int normalizePriority(int n) {
        if (n < 0) {
            return 0;
        }
        if (n > 9) {
            return 9;
        }
        return n;
    }

    private JobInfo<T> getSuitableJob(Boolean bl) {
        JobInfo<T> jobInfo = null;
        for (int i = 9; i >= 0; --i) {
            LinkedHashSet<Integer> linkedHashSet = this.queueOfTaskForExecute.get(i);
            if (linkedHashSet == null || (jobInfo = this.searchForTask(linkedHashSet)) == null) continue;
            return jobInfo;
        }
        return null;
    }

    private void removeFromQueue(int n, int n2) {
        this.queueOfTaskForExecute.get(n2).remove(n);
    }

    private JobInfo<T> searchForTask(Collection<Integer> collection) {
        for (Integer n : collection) {
            JobInfo<T> jobInfo = this.dataMap.get(n);
            if (!this.canExecuteTaskDueGroupLimitation(jobInfo)) continue;
            return jobInfo;
        }
        return null;
    }

    private void addToQueue(int n, int n2, boolean bl) {
        LinkedHashSet<Integer> linkedHashSet = this.queueOfTaskForExecute.get(n2);
        if (linkedHashSet == null) {
            linkedHashSet = new LinkedHashSet();
            this.queueOfTaskForExecute.put(n2, linkedHashSet);
        }
        linkedHashSet.add(n);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<T> getJobInfo(String string, String string2) {
        Object object = this.lock;
        synchronized (object) {
            int n = this.getJobIdentHash(string, string2);
            return this.dataMap.get(n);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Set<JobInfo<T>> getRunningTasks() {
        HashSet<JobInfo<T>> hashSet = new HashSet<JobInfo<T>>();
        Object object = this.lock;
        synchronized (object) {
            for (Integer n : this.notConfirmedRunningTasks) {
                hashSet.add(this.dataMap.get(n));
            }
        }
        return hashSet;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void close() {
        Object object = this.lock;
        synchronized (object) {
            this.dataMap.clear();
            this.finishedDataMap.clear();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String getJsonDescriptions() {
        Object object = this.lock;
        synchronized (object) {
            return this.serializer.getJson(this.queueOfTaskForExecute, this.notConfirmedRunningTasks, this.dataMap, this.finishedDataMap);
        }
    }

    public void setGroupRestrictions(String string, int n) {
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void check() {
        Object object = this.lock;
        synchronized (object) {
            for (int i = 9; i >= 0; --i) {
                LinkedHashSet<Integer> linkedHashSet = this.queueOfTaskForExecute.get(i);
                if (linkedHashSet == null) continue;
                Iterator iterator = linkedHashSet.iterator();
                while (iterator.hasNext()) {
                    int n = (Integer)iterator.next();
                    if (this.dataMap.get(n) != null) continue;
                    throw new IllegalStateException("Job in queue lost its data!");
                }
            }
            Iterator iterator = this.notConfirmedRunningTasks.iterator();
            while (iterator.hasNext()) {
                int n = (Integer)iterator.next();
                if (this.dataMap.get(n) != null) continue;
                throw new IllegalStateException("Not configrmed job in queue lost its data!");
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JobInfo<?> setJobWaiting(String string, String string2, boolean bl) {
        int n = this.getJobIdentHash(string, string2);
        Object object = this.lock;
        synchronized (object) {
            JobInfo<T> jobInfo = this.dataMap.get(n);
            if (jobInfo != null) {
                jobInfo.waiting = bl;
            }
            return jobInfo;
        }
    }

    public static class JobInfo<T extends Serializable>
    implements Serializable {
        private static final long serialVersionUID = 1L;
        private boolean executed;
        private String id;
        private String jobGroupId;
        private long creationTime;
        private long executeTime;
        private long finishTime;
        private long duration;
        private long durationWithWait;
        private boolean blocking;
        private T data;
        private int progress = -1;
        private boolean success;
        private String message;
        private int priority;
        public volatile boolean waiting = false;

        public boolean isWaiting() {
            return this.waiting;
        }

        public long getFinishTime() {
            return this.finishTime;
        }

        public long getDurationWithWait() {
            return this.durationWithWait;
        }

        public boolean isSuccess() {
            return this.success;
        }

        public String getMessage() {
            return this.message;
        }

        public boolean isBlocking() {
            return this.blocking;
        }

        public String getJobGroupId() {
            return this.jobGroupId;
        }

        public boolean isExecuted() {
            return this.executed;
        }

        public String getId() {
            return this.id;
        }

        public T getData() {
            return this.data;
        }

        public void setData(T t) {
            this.data = t;
        }

        public int getProgress() {
            return this.progress;
        }

        public void setProgress(int n) {
            this.progress = n;
        }

        public long getCreationTime() {
            return this.creationTime;
        }

        public void setCreationTime(long l) {
            this.creationTime = l;
        }

        public long getDuration() {
            return this.duration;
        }

        public void setDuration(long l) {
            this.duration = l;
        }

        public long getExecuteTime() {
            return this.executeTime;
        }

        public String toString() {
            return this.id + " (" + this.jobGroupId + ")";
        }
    }

    public static interface TimeEvaluator {
        public long getTimeForWaitForTask(String var1);
    }
}

