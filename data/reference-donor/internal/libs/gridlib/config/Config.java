/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.config;

import com.strategyquant.gridlib.message.sync.FolderConfigs;

public class Config {
    private boolean useJavaSerialization = true;
    private boolean useAffinity = true;
    private boolean compressData = true;
    private String coreUsage = "-1";
    private String nodeId;
    private int finishedJobsInDesc = 10;
    private String serverLocation;
    private FolderConfigs folderConfigs = new FolderConfigs();
    private String[] foldersWithJars;
    private boolean adjustTopSizeOfCores;

    public Config() {
    }

    public Config(String string) {
        this();
        this.serverLocation = string;
    }

    public int getFinishedJobsInDesc() {
        return this.finishedJobsInDesc;
    }

    public void setFinishedJobsInDesc(int n) {
        this.finishedJobsInDesc = n;
    }

    public String getServerLocation() {
        return this.serverLocation;
    }

    public void setUseJavaSerialization(boolean bl) {
        this.useJavaSerialization = bl;
    }

    public boolean isUseJavaSerialization() {
        return this.useJavaSerialization;
    }

    public void setServerLocation(String string) {
        this.serverLocation = string;
    }

    public String[] getFoldersWithJars() {
        return this.foldersWithJars;
    }

    public void setFoldersWithJars(String[] stringArray) {
        this.foldersWithJars = stringArray;
    }

    public FolderConfigs getFolderConfigs() {
        return this.folderConfigs;
    }

    public void setFolderConfigs(FolderConfigs folderConfigs) {
        this.folderConfigs = folderConfigs;
    }

    public boolean isCompressData() {
        return this.compressData;
    }

    public void setCompressData(boolean bl) {
        this.compressData = bl;
    }

    public String getCoreUsage() {
        return this.coreUsage;
    }

    public void setCoreUsage(String string) {
        this.coreUsage = string;
    }

    public boolean isUseAffinity() {
        return this.useAffinity;
    }

    public void setUseAffinity(boolean bl) {
        this.useAffinity = bl;
    }

    public String getNodeId() {
        return this.nodeId;
    }

    public void setNodeId(String string) {
        this.nodeId = string;
    }

    public boolean isAdjustTopSizeOfCores() {
        return this.adjustTopSizeOfCores;
    }

    public void setAdjustTopSizeOfCores(boolean bl) {
        this.adjustTopSizeOfCores = bl;
    }
}

