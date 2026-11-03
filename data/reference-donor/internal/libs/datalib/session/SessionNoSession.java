/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.session;

import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionStatus;

public class SessionNoSession
extends Session {
    SessionNoSession() {
        super("No Session", null);
    }

    public void checkTimeIsInSession(long l, SessionStatus sessionStatus) {
        sessionStatus.isInSession = true;
    }
}

