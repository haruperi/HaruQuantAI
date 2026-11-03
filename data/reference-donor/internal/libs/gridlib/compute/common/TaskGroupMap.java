/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 */
package com.strategyquant.gridlib.compute.common;

import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class TaskGroupMap {
    private Map<Integer, Set<String>> groupMap = new Int2ObjectOpenHashMap();
    private Map<Integer, ExecuteOptions> groupLimits = new Int2ObjectOpenHashMap();
    private Map<Integer, Integer> runningInGroups = new Int2IntOpenHashMap();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Set<String> getJobsForGroup(String string) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            int n = string.hashCode();
            Set<String> set = this.groupMap.get(n);
            if (set == null) {
                set = new HashSet<String>();
                this.groupMap.put(n, set);
            }
            return set;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void add(String string, String string2, ExecuteOptions executeOptions) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            this.getJobsForGroup(string2).add(string);
            this.groupLimits.put(string2.hashCode(), executeOptions);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean remove(String string, String string2) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            this.finished(string2);
            Set<String> set = this.getJobsForGroup(string2);
            if (set == null) {
                return false;
            }
            set.remove(string);
            if (set.isEmpty()) {
                this.removeGroup(string2);
                return true;
            }
            return false;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ExecuteOptions getOptions(String string) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            int n = string.hashCode();
            return this.groupLimits.get(n);
        }
    }

    private void removeGroup(String string) {
        int n = string.hashCode();
        this.groupMap.remove(n);
        this.groupLimits.remove(n);
        this.runningInGroups.remove(n);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public int getRunningCount(String string) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            Integer n = this.runningInGroups.get(string.hashCode());
            return n == null ? 0 : n;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void executed(String string) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            int n = string.hashCode();
            Integer n2 = this.runningInGroups.get(n);
            this.runningInGroups.put(string.hashCode(), n2 == null ? 1 : n2 + 1);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void finished(String string) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            int n = string.hashCode();
            Integer n2 = this.runningInGroups.get(n);
            this.runningInGroups.put(string.hashCode(), n2 == null ? 0 : n2 - 1);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean hasTasks(String string) {
        Map<Integer, Set<String>> map = this.groupMap;
        synchronized (map) {
            return this.getRunningCount(string) > 0;
        }
    }
}

