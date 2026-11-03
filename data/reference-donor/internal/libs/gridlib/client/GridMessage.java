/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.client;

import com.strategyquant.gridlib.client.JobDetails;
import java.io.Serializable;

public class GridMessage
implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final int JobFinished = 1;
    public static final int JobPause = 2;
    public static final int JobRestart = 3;
    public static final int JobStop = 4;
    public static final int Custom = 5;
    public static final int ProgressUpdated = 6;
    private int messageID;
    private String customID;
    private Serializable data;
    private JobDetails jobDetails;

    public GridMessage() {
    }

    public GridMessage(int n) {
        this(n, null, null);
    }

    public GridMessage(int n, String string) {
        this(n, string, null);
    }

    public GridMessage(int n, String string, Serializable serializable) {
        this.messageID = n;
        this.customID = string;
        this.data = serializable;
    }

    public int getMessageID() {
        return this.messageID;
    }

    public String getCustomID() {
        return this.customID;
    }

    public Serializable getData() {
        return this.data;
    }

    public JobDetails getJobDetails() {
        return this.jobDetails;
    }

    public void setJobDetails(JobDetails jobDetails) {
        this.jobDetails = jobDetails;
    }
}

