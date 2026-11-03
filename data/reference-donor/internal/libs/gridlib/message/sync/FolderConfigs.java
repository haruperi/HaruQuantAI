/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.message.sync;

import com.strategyquant.gridlib.config.SingleFolderConfig;
import java.util.LinkedList;
import java.util.List;

public class FolderConfigs {
    private String dataFolderRoot;
    private List<SingleFolderConfig> folderConfig = new LinkedList<SingleFolderConfig>();

    public String getDataFolderRoot() {
        return this.dataFolderRoot;
    }

    public void setDataFolderRoot(String string) {
        this.dataFolderRoot = string;
    }

    public List<SingleFolderConfig> getFolderConfig() {
        return this.folderConfig;
    }

    public void setFolderConfig(List<SingleFolderConfig> list) {
        this.folderConfig = list;
    }
}

