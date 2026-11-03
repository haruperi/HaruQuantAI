/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute;

import java.io.Serializable;

public class ComputeResult<T extends Serializable>
implements Serializable {
    private static final long serialVersionUID = 1L;
    private T data;
    private String taskId;

    public ComputeResult() {
    }

    public ComputeResult(T t, String string) {
        this.data = t;
        this.taskId = string;
    }

    public T getData() {
        return this.data;
    }

    public void setData(T t) {
        this.data = t;
    }

    public String getTaskId() {
        return this.taskId;
    }

    public void setTaskId(String string) {
        this.taskId = string;
    }
}

