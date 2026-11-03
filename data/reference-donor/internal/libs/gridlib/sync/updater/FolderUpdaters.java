/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.sync.updater;

import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.sync.FolderGuardFactory;
import com.strategyquant.gridlib.sync.updater.IFolderUpdatedListener;
import com.strategyquant.gridlib.sync.updater.IFolderUpdater;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;
import javax.jms.JMSException;

public class FolderUpdaters
implements AutoCloseable {
    private List<IFolderUpdater> updaters = new LinkedList<IFolderUpdater>();
    private String path;
    private List<IFolderUpdatedListener> listeners = new LinkedList<IFolderUpdatedListener>();
    private FolderUpdatedListener listener = new FolderUpdatedListener();
    private JmsConnectionInfo connection;

    public FolderUpdaters(String string, JmsConnectionInfo jmsConnectionInfo) throws JMSException {
        this.path = string;
        this.connection = jmsConnectionInfo;
    }

    public void createUpdater(String string, boolean bl) throws IOException, JMSException {
        IFolderUpdater iFolderUpdater = FolderGuardFactory.getUpdater(string, this.path + "/" + string, bl, this.connection);
        iFolderUpdater.addFolderUpdatedListener(this.listener);
        this.updaters.add(iFolderUpdater);
    }

    public void addFolderUpdatedListener(IFolderUpdatedListener iFolderUpdatedListener) {
        this.listeners.add(iFolderUpdatedListener);
    }

    @Override
    public void close() throws Exception {
        for (IFolderUpdater iFolderUpdater : this.updaters) {
            iFolderUpdater.close();
        }
    }

    public boolean isDirty() {
        for (IFolderUpdater iFolderUpdater : this.updaters) {
            if (!iFolderUpdater.isDirty()) continue;
            return true;
        }
        return false;
    }

    private class FolderUpdatedListener
    implements IFolderUpdatedListener {
        private FolderUpdatedListener() {
        }

        @Override
        public void onUpdated() {
            if (!FolderUpdaters.this.isDirty()) {
                for (IFolderUpdatedListener iFolderUpdatedListener : FolderUpdaters.this.listeners) {
                    iFolderUpdatedListener.onUpdated();
                }
            }
        }
    }
}

