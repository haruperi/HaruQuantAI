/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.sync.guard;

import java.io.IOException;
import javax.jms.JMSException;

public interface IFolderGuard {
    public String getFolder();

    public void updateHash() throws IOException, JMSException;

    public void close() throws JMSException;
}

