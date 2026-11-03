/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.sync.updater;

import com.strategyquant.gridlib.sync.updater.IFolderUpdatedListener;
import java.io.IOException;
import javax.jms.JMSException;

public interface IFolderUpdater {
    public String getFolder();

    public void updateHash() throws IOException;

    public boolean isDirty();

    public void close() throws JMSException;

    public void addFolderUpdatedListener(IFolderUpdatedListener var1);
}

