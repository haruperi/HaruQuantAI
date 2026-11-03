/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.client;

import java.io.Serializable;

public class JobDetails
implements Serializable {
    private String id;
    private long duration;
    private String exception;

    public JobDetails(String string) {
        this.id = string;
    }

    public String getJobID() {
        return this.id;
    }

    public String getException() {
        return this.exception;
    }

    public void setException(String string) {
        this.exception = string;
    }

    public long getDuration() {
        return this.duration;
    }

    public void setDuration(long l) {
        this.duration = l;
    }

    public boolean isSuccess() {
        return this.exception == null;
    }
}

