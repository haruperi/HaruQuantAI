/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.sync.updater;

import java.util.LinkedList;

public class HandleHashResult {
    private boolean needUpdate;
    private LinkedList<String> filesToUpdate;

    public HandleHashResult(boolean bl, LinkedList<String> linkedList) {
        this.needUpdate = bl;
        this.filesToUpdate = linkedList;
    }

    public boolean isNeedUpdate() {
        return this.needUpdate;
    }

    public LinkedList<String> getFilesToUpdate() {
        return this.filesToUpdate;
    }
}

