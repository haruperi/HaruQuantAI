/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.config;

public class SingleFolderConfig {
    private String folder;
    private boolean solidFolder;

    public SingleFolderConfig() {
    }

    public SingleFolderConfig(String string, boolean bl) {
        this.folder = string;
        this.solidFolder = bl;
    }

    public String getFolder() {
        return this.folder;
    }

    public boolean isSolidFolder() {
        return this.solidFolder;
    }

    public void setFolder(String string) {
        this.folder = string;
    }

    public void setSolidFolder(boolean bl) {
        this.solidFolder = bl;
    }
}

