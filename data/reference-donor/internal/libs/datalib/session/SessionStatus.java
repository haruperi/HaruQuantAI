/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.session;

import java.io.Serializable;

public class SessionStatus
implements Serializable {
    public boolean isInSession;
    public long sessionStartTime = Long.MIN_VALUE;
    public long sessionEndTime = Long.MIN_VALUE;
}

