/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib;

import java.io.Serializable;

public class FileInfo
implements Serializable {
    private static final long serialVersionUID = 1L;
    private byte[] data;

    public FileInfo() {
    }

    public FileInfo(byte[] byArray) {
        this.data = byArray;
    }

    public byte[] getData() {
        return this.data;
    }

    public void setData(byte[] byArray) {
        this.data = byArray;
    }
}

