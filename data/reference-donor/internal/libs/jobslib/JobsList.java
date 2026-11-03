/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.jobslib;

import com.strategyquant.jobslib.SQJob;
import java.util.ArrayList;

public class JobsList {
    private ArrayList<SQJob> list = new ArrayList();

    public void add(SQJob sQJob) {
        this.list.add(sQJob);
    }

    public void remove(SQJob sQJob) {
        this.list.remove(sQJob);
    }

    public int size() {
        return this.list.size();
    }
}

