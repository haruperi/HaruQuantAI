/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.topology;

import java.io.Serializable;

public class NodeInfo
implements Serializable {
    private static final long serialVersionUID = 1L;
    private String ip;
    private Long id;
    private int totalCores;
    private int usedCores;
    private Long age;
    private Long lastHeartBeat;
    private int runningThreads;
    private String osVersion;
    private double totalMemory;
    private double usedMemory;
    private int cpuUsage;

    public String getIp() {
        return this.ip;
    }

    public void setIp(String string) {
        this.ip = string;
    }

    public Long getAge() {
        return this.age;
    }

    public void setAge(Long l) {
        this.age = l;
    }

    public int getRunningThreads() {
        return this.runningThreads;
    }

    public void setRunningThreads(int n) {
        this.runningThreads = n;
    }

    public String getOsVersion() {
        return this.osVersion;
    }

    public void setOsVersion(String string) {
        this.osVersion = string;
    }

    public double getTotalMemory() {
        return this.totalMemory;
    }

    public void setTotalMemory(double d) {
        this.totalMemory = d;
    }

    public int getCpuUsage() {
        return this.cpuUsage;
    }

    public void setCpuUsage(int n) {
        this.cpuUsage = n;
    }

    public Long getLastHeartBeat() {
        return this.lastHeartBeat;
    }

    public void setLastHeartBeat(Long l) {
        this.lastHeartBeat = l;
    }

    public double getUsedMemory() {
        return this.usedMemory;
    }

    public void setUsedMemory(double d) {
        this.usedMemory = d;
    }

    public int getTotalCores() {
        return this.totalCores;
    }

    public void setTotalCores(int n) {
        this.totalCores = n;
    }

    public int getUsedCores() {
        return this.usedCores;
    }

    public void setUsedCores(int n) {
        this.usedCores = n;
    }

    public Long getId() {
        return this.id;
    }

    public void setId(Long l) {
        this.id = l;
    }
}

