/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data;

public interface BatchProgressController {
    public boolean isCancel();

    public void updateProgress(int var1, int var2, String var3) throws Exception;

    public void finished();
}

