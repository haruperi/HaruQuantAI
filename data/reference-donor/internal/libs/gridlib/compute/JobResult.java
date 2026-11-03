/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute;

import java.io.Serializable;

public class JobResult<T extends Serializable>
implements Serializable {
    private static final long serialVersionUID = 1L;
    private boolean success;
    private boolean stopped;
    private T data;
    private long duration;
    private String errorMessage;

    public T getData() {
        return this.data;
    }

    public void setData(T t) {
        this.data = t;
    }

    public boolean isSuccess() {
        return this.success;
    }

    public void setSuccess(boolean bl) {
        this.success = bl;
    }

    public long getDuration() {
        return this.duration;
    }

    public void setDuration(long l) {
        this.duration = l;
    }

    public String getErrorMessage() {
        return this.errorMessage;
    }

    public void setErrorMessage(String string) {
        this.errorMessage = string;
    }

    public boolean isStopped() {
        return this.stopped;
    }

    public void setStopped(boolean bl) {
        this.stopped = bl;
    }
}

