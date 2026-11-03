/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.project.ProjectProgressInfo;
import java.util.concurrent.locks.StampedLock;
import org.json.JSONObject;

public class ProjectProgress {
    private ProjectProgressInfo info = new ProjectProgressInfo();
    private StampedLock lock = new StampedLock();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void update(String string, double d, String string2) {
        long l = this.lock.writeLock();
        try {
            this.info.action = string;
            this.info.percent = (int)d;
            this.info.error = string2;
            this.info.hasExtra = false;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void update(String string, double d, String string2, String string3) {
        long l = this.lock.writeLock();
        try {
            this.info.action = string;
            this.info.percent = (int)d;
            this.info.error = string2;
            this.info.info = string3;
            this.info.hasExtra = false;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void update(String string, double d, String string2, String string3, JSONObject jSONObject) {
        long l = this.lock.writeLock();
        try {
            this.info.action = string;
            this.info.percent = (int)d;
            this.info.error = string2;
            this.info.extraName = string3;
            this.info.extraValue = jSONObject;
            this.info.hasExtra = true;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ProjectProgressInfo get() {
        long l = this.lock.readLock();
        try {
            ProjectProgressInfo projectProgressInfo = this.info;
            return projectProgressInfo;
        }
        finally {
            this.lock.unlock(l);
        }
    }
}

