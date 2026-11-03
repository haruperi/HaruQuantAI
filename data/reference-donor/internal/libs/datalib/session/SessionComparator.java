/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.session;

import com.strategyquant.datalib.session.Session;
import java.util.Comparator;

public class SessionComparator
implements Comparator<Session> {
    @Override
    public int compare(Session session, Session session2) {
        if ("No Session".equals(session.getSessionName()) && session.getSessionName().equals(session2.getSessionName())) {
            return 0;
        }
        return "No Session".equals(session.getSessionName()) ? -1 : ("No Session".equals(session2.getSessionName()) ? 1 : session.getSessionName().compareTo(session2.getSessionName()));
    }
}

